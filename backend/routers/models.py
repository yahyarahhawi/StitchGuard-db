from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import backend.schemas as schemas
from backend.deps import get_db
from db.models import Model

router = APIRouter(prefix="/models", tags=["models"])


@router.get("/", response_model=List[schemas.Model])
def list_models(
    model_type: str = None,
    platform: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Model)
    
    if model_type:
        query = query.filter(Model.type == model_type)
    if platform:
        query = query.filter(Model.platform == platform)
    
    return query.offset(offset).limit(limit).all()


@router.post("/", response_model=schemas.Model, status_code=status.HTTP_201_CREATED)
def create_model(payload: schemas.ModelCreate, db: Session = Depends(get_db)):
    model = Model(**payload.dict(), created_at=datetime.utcnow())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/{model_id}", response_model=schemas.Model)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/{model_id}", response_model=schemas.Model)
def update_model(
    model_id: int,
    payload: schemas.ModelCreate,
    db: Session = Depends(get_db)
):
    model = db.query(Model).get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).get(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    db.delete(model)
    db.commit() 