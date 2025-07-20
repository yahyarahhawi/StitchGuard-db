from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import backend.schemas as schemas
from backend.deps import get_db                     # DB dependency
from db.models import Product, Model, ProductOrientation                       # SQLAlchemy ORM

router = APIRouter(prefix="/products", tags=["products"])


# ------------------------------------------------------------------ #
#  LIST all products
# ------------------------------------------------------------------ #
@router.get("/", response_model=List[schemas.Product])
def list_products(db: Session = Depends(get_db)):
    """Get all products with their orientations included"""
    from sqlalchemy.orm import joinedload
    
    return db.query(Product).options(
        joinedload(Product.orientations)
    ).all()


# ------------------------------------------------------------------ #
#  LIST all products WITH their models
# ------------------------------------------------------------------ #
@router.get("/with-models", response_model=List[schemas.ProductWithModels])
def list_products_with_models(db: Session = Depends(get_db)):
    """Get all products with their associated models and orientations included"""
    from sqlalchemy.orm import joinedload
    
    products = db.query(Product).options(
        joinedload(Product.models),
        joinedload(Product.orientations)
    ).all()
    
    # Convert to response format with backward compatibility
    result = []
    for product in products:
        product_dict = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "orientations_required": [o.orientation for o in product.orientations],  # Backward compatibility
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "models": product.models,
            "orientations": product.orientations
        }
        result.append(product_dict)
    return result


# ------------------------------------------------------------------ #
#  CREATE a new product
# ------------------------------------------------------------------ #
@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    """Create a new product with orientations"""
    # Extract orientations from payload and exclude from product creation
    orientations_list = payload.orientations
    product_data = payload.model_dump(exclude={'orientations'})
    
    # Create the product
    product = Product(**product_data)
    db.add(product)
    db.flush()  # Get the product ID without committing
    
    # Create orientations for the product
    for orientation_name in orientations_list:
        orientation = ProductOrientation(
            product_id=product.id,
            orientation=orientation_name
        )
        db.add(orientation)
    
    db.commit()
    db.refresh(product)
    return product


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
    
    # Get models using foreign key relationship
    models = db.query(Model).filter(Model.product_id == product_id).all()
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
    
    # Get models using foreign key relationship
    models = db.query(Model).filter(Model.product_id == product_id).all()
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

