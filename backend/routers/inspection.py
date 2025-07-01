from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import backend.schemas as schemas
from backend.deps import get_db
from db.models import (
    Product,
    InspectionRule,
    InspectedItem,
    Flaw,
    Order,
    User,
)

router = APIRouter(prefix="/inspection", tags=["inspection"])


# ------------------------------------------------------------------ #
#  GET /inspection/config/{product_id}
# ------------------------------------------------------------------ #
@router.get(
    "/config/{product_id}",
    response_model=schemas.InspectionConfigOut,
    status_code=status.HTTP_200_OK,
)
def get_inspection_config(product_id: int, db: Session = Depends(get_db)):
    product: Product | None = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    rules: List[InspectionRule] = (
        db.query(InspectionRule)
        .filter(InspectionRule.product_id == product_id)
        .all()
    )

    return {
        "product_id": product.id,
        "orientations_required": product.orientations_required,
        "rules": rules,
    }


# ------------------------------------------------------------------ #
#  POST /inspection/items
# ------------------------------------------------------------------ #
@router.post(
    "/items",
    response_model=schemas.InspectedItemOut,
    status_code=status.HTTP_201_CREATED,
)
def create_inspected_item(
    payload: schemas.InspectedItemCreate, db: Session = Depends(get_db)
):
    # Validate that order and sewer exist
    order = db.query(Order).get(payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    sewer = db.query(User).get(payload.sewer_id)
    if not sewer:
        raise HTTPException(status_code=404, detail="Sewer not found")
    
    # Check if serial number already exists
    existing_item = db.query(InspectedItem).filter(
        InspectedItem.serial_number == payload.serial_number
    ).first()
    if existing_item:
        raise HTTPException(
            status_code=400, 
            detail=f"Item with serial number {payload.serial_number} already exists"
        )

    item = InspectedItem(
        serial_number=payload.serial_number,
        order_id=payload.order_id,
        sewer_id=payload.sewer_id,
        status=payload.status,  # Now using status instead of passed
        front_image_url=payload.front_image_url,
        back_image_url=payload.back_image_url,
        inspected_at=payload.inspected_at or datetime.utcnow(),
    )
    db.add(item)
    db.flush()  # item.id now available

    for flaw in payload.flaws:
        db.add(
            Flaw(
                item_id=item.id,
                flaw_type=flaw.flaw_type,
                orientation=flaw.orientation,
                detected_at=flaw.detected_at or datetime.utcnow(),
            )
        )

    db.commit()
    db.refresh(item)
    return item


# ------------------------------------------------------------------ #
#  GET /inspection/items/{item_id}
# ------------------------------------------------------------------ #
@router.get(
    "/items/{item_id}",
    response_model=schemas.InspectedItemOut,
    status_code=status.HTTP_200_OK,
)
def get_inspected_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(InspectedItem).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inspected item not found")
    return item


# ------------------------------------------------------------------ #
#  GET /inspection/items (list with filters)
# ------------------------------------------------------------------ #
@router.get(
    "/items",
    response_model=List[schemas.InspectedItemOut],
    status_code=status.HTTP_200_OK,
)
def list_inspected_items(
    order_id: int = None,
    sewer_id: int = None,
    status: str = None,  # Now filter by status instead of passed
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(InspectedItem)
    
    if order_id:
        query = query.filter(InspectedItem.order_id == order_id)
    if sewer_id:
        query = query.filter(InspectedItem.sewer_id == sewer_id)
    if status:
        query = query.filter(InspectedItem.status == status)
    
    items = query.offset(offset).limit(limit).all()
    return items