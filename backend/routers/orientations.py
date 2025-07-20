from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import backend.schemas as schemas
from backend.deps import get_db
from db.models import Product, ProductOrientation

router = APIRouter(prefix="/orientations", tags=["orientations"])


# ------------------------------------------------------------------ #
#  GET orientations for a specific product
# ------------------------------------------------------------------ #
@router.get("/product/{product_id}", response_model=List[schemas.ProductOrientation])
def get_product_orientations(product_id: int, db: Session = Depends(get_db)):
    """Get all orientations for a specific product"""
    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return db.query(ProductOrientation).filter(ProductOrientation.product_id == product_id).all()


# ------------------------------------------------------------------ #
#  CREATE a new orientation for a product
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.ProductOrientation, status_code=status.HTTP_201_CREATED)
def create_product_orientation(payload: schemas.ProductOrientationCreate, db: Session = Depends(get_db)):
    """Create a new orientation for a product"""
    # Check if product exists
    product = db.query(Product).get(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if orientation already exists for this product
    existing = db.query(ProductOrientation).filter(
        ProductOrientation.product_id == payload.product_id,
        ProductOrientation.orientation == payload.orientation
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Orientation '{payload.orientation}' already exists for product {payload.product_id}"
        )
    
    # Create new orientation
    orientation = ProductOrientation(
        product_id=payload.product_id,
        orientation=payload.orientation
    )
    
    db.add(orientation)
    db.commit()
    db.refresh(orientation)
    
    return orientation


# ------------------------------------------------------------------ #
#  DELETE an orientation
# ------------------------------------------------------------------ #
@router.delete("/{orientation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_orientation(orientation_id: int, db: Session = Depends(get_db)):
    """Delete a product orientation"""
    orientation = db.query(ProductOrientation).get(orientation_id)
    if not orientation:
        raise HTTPException(status_code=404, detail="Orientation not found")
    
    db.delete(orientation)
    db.commit()


# ------------------------------------------------------------------ #
#  UPDATE an orientation
# ------------------------------------------------------------------ #
@router.put("/{orientation_id}", response_model=schemas.ProductOrientation)
def update_product_orientation(
    orientation_id: int, 
    payload: schemas.ProductOrientationBase, 
    db: Session = Depends(get_db)
):
    """Update a product orientation"""
    orientation = db.query(ProductOrientation).get(orientation_id)
    if not orientation:
        raise HTTPException(status_code=404, detail="Orientation not found")
    
    # Check for duplicate orientation for the same product
    existing = db.query(ProductOrientation).filter(
        ProductOrientation.product_id == orientation.product_id,
        ProductOrientation.orientation == payload.orientation,
        ProductOrientation.id != orientation_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Orientation '{payload.orientation}' already exists for this product"
        )
    
    # Update the orientation
    orientation.orientation = payload.orientation
    
    db.commit()
    db.refresh(orientation)
    
    return orientation