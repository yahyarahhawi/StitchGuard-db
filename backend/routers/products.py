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
    prod = Product(**payload.dict())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


# ------------------------------------------------------------------ #
#  GET MODELS for a specific product (MUST come before /{product_id})
# ------------------------------------------------------------------ #
@router.get("/{product_id}/models", response_model=List[schemas.Model])
def get_product_models(product_id: int, db: Session = Depends(get_db)):
    """
    Get all models associated with a specific product
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
#  GET one product (MUST come after specific routes)
# ------------------------------------------------------------------ #
@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    prod = db.query(Product).get(product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@router.get("/test-deploy")
def test_deploy():
    return {"message": "Deployment working", "timestamp": "$(date)"}

