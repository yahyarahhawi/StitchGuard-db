from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import backend.schemas as schemas
from backend.deps import get_db                     # DB dependency
from db.models import Product, Model                       # SQLAlchemy ORM

router = APIRouter(prefix="/products", tags=["products"])


# ------------------------------------------------------------------ #
#  LIST all products
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.Product])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


# ------------------------------------------------------------------ #
#  CREATE a new product
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    prod = Product(**payload.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


# ------------------------------------------------------------------ #
#  GET MODELS for a specific product - EXPLICIT ROUTE (RECOMMENDED)
# ------------------------------------------------------------------ #
@router.get("/by-id/{product_id}/models", response_model=List[schemas.Model])
def get_product_models_explicit(product_id: int, db: Session = Depends(get_db)):
    """
    Get all models associated with a specific product
    Using explicit route structure to avoid conflicts
    Recommended route: /api/v1/products/by-id/{product_id}/models
    """
    # Get the product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get models by IDs
    if not product.model_ids:
        return []
    
    models = db.query(Model).filter(Model.id.in_(product.model_ids)).all()
    return models


# ------------------------------------------------------------------ #
#  GET MODELS for a specific product - ORIGINAL ROUTE (FIXED ORDER)
# ------------------------------------------------------------------ #
@router.get("/{product_id}/models", response_model=List[schemas.Model])
def get_product_models_original(product_id: int, db: Session = Depends(get_db)):
    """
    Get all models associated with a specific product
    Original route structure: /api/v1/products/{product_id}/models
    MUST be placed before the general /{product_id} route
    """
    # Get the product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get models by IDs
    if not product.model_ids:
        return []
    
    models = db.query(Model).filter(Model.id.in_(product.model_ids)).all()
    return models


# ------------------------------------------------------------------ #
#  GET one product (MUST be placed AFTER specific routes)
# ------------------------------------------------------------------ #
@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.query(Product).get(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

