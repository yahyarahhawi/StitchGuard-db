from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend import schemas
from backend.deps import get_db
from db.models import User

# Updated for Supabase authentication support
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[schemas.User])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = User(**payload.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/by-auth-id/{auth_id}", response_model=schemas.User)
def get_user_by_auth_id(auth_id: str, db: Session = Depends(get_db)):
    """Get user by Supabase auth ID"""
    user = db.query(User).filter(User.auth_id == auth_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/auth-sync", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def sync_user_from_auth(payload: schemas.UserAuthSync, db: Session = Depends(get_db)):
    """Create or update user profile from Supabase auth data"""
    # Check if user already exists by auth_id
    existing_user = db.query(User).filter(User.auth_id == payload.auth_id).first()
    
    if existing_user:
        # Update existing user
        existing_user.email = payload.email
        existing_user.name = payload.name
        existing_user.role = payload.role
        existing_user.updated_at = func.now()
        db.commit()
        db.refresh(existing_user)
        return existing_user
    else:
        # Check if user exists by email (for migration of existing users)
        existing_user_by_email = db.query(User).filter(User.email == payload.email).first()
        
        if existing_user_by_email:
            # Update existing user with auth_id
            existing_user_by_email.auth_id = payload.auth_id
            existing_user_by_email.name = payload.name
            existing_user_by_email.role = payload.role
            existing_user_by_email.updated_at = func.now()
            db.commit()
            db.refresh(existing_user_by_email)
            return existing_user_by_email
        else:
            # Create new user
            new_user = User(
                auth_id=payload.auth_id,
                email=payload.email,
                name=payload.name,
                role=payload.role
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user