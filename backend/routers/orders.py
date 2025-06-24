from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

import backend.schemas as schemas
from backend.deps import get_db
from db.models import Order, User, Product, InspectedItem

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=List[schemas.Order])
def list_orders(
    supervisor_id: int = None,
    product_id: int = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Order)
    
    if supervisor_id:
        query = query.filter(Order.supervisor_id == supervisor_id)
    if product_id:
        query = query.filter(Order.product_id == product_id)
    
    return query.offset(offset).limit(limit).all()


@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    # Validate supervisor exists
    supervisor = db.query(User).get(payload.supervisor_id)
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    
    # Validate product exists
    product = db.query(Product).get(payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    order = Order(**payload.dict(), created_at=datetime.utcnow())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}", response_model=schemas.Order)
def update_order(
    order_id: int, 
    payload: schemas.OrderUpdate, 
    db: Session = Depends(get_db)
):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order has inspected items
    inspected_count = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id
    ).count()
    
    if inspected_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete order with {inspected_count} inspected items"
        )
    
    db.delete(order)
    db.commit()


@router.get("/{order_id}/stats", response_model=schemas.OrderStats)
def get_order_stats(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get inspection statistics
    total_items = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id
    ).count()
    
    passed_items = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id,
        InspectedItem.passed == True
    ).count()
    
    failed_items = total_items - passed_items
    pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0
    
    return schemas.OrderStats(
        total_orders=1,
        completed_orders=1 if order.completed >= order.quantity else 0,
        pending_orders=0 if order.completed >= order.quantity else 1,
        total_items=total_items,
        passed_items=passed_items,
        failed_items=failed_items,
        pass_rate=pass_rate
    )