from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

import backend.schemas as schemas
from backend.deps import get_db
from db.models import Order, User, Product, InspectedItem, AssignedSewer, ShippingDetail

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
    
    order = Order(**payload.model_dump(), created_at=datetime.utcnow())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/assigned-to/{user_id}", response_model=List[schemas.Order])
def get_orders_assigned_to_user(user_id: int, db: Session = Depends(get_db)):
    """Get all orders assigned to a specific user (sewer)"""
    # Verify user exists
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get orders assigned directly to this sewer
    orders = db.query(Order).filter(Order.sewer_id == user_id).all()
    
    return orders


@router.get("/assigned-to-auth/{auth_id}", response_model=List[schemas.OrderWithNames])
def get_orders_assigned_to_auth_user(auth_id: str, db: Session = Depends(get_db)):
    """Get all orders assigned to a user by their Supabase auth ID with names for UI"""
    # Find user by auth_id
    user = db.query(User).filter(User.auth_id == auth_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get orders assigned directly to this sewer with supervisor and sewer names
    orders_with_names = db.query(
        Order.id,
        Order.name,
        Order.supervisor_id,
        Order.sewer_id,
        Order.product_id,
        Order.quantity,
        Order.completed,
        Order.deadline,
        Order.created_at,
        Order.updated_at,
        User.name.label('supervisor_name')
    ).join(
        User, Order.supervisor_id == User.id
    ).filter(Order.sewer_id == user.id).all()
    
    # Convert to response format
    result = []
    for order in orders_with_names:
        # Get sewer name (we know it's the current user)
        sewer_name = user.name
        
        result.append({
            "id": order.id,
            "name": order.name,
            "supervisor_id": order.supervisor_id,
            "sewer_id": order.sewer_id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "completed": order.completed,
            "deadline": order.deadline,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "supervisor_name": order.supervisor_name,
            "sewer_name": sewer_name
        })
    
    return result


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
    
    update_data = payload.model_dump(exclude_unset=True)
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
    
    # Count PASSED and OVERRIDDEN as successful completions
    passed_items = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id,
        InspectedItem.status.in_(['PASSED', 'OVERRIDDEN'])
    ).count()
    
    failed_items = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id,
        InspectedItem.status == 'FAILED'
    ).count()
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


@router.put("/{order_id}/progress", response_model=schemas.Order)
def update_order_progress(
    order_id: int,
    progress_update: dict,  # Expecting {"completed": int}
    db: Session = Depends(get_db)
):
    """Update the completed count for an order"""
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    new_completed = progress_update.get("completed")
    if new_completed is None:
        raise HTTPException(status_code=400, detail="Missing 'completed' field")
    
    if new_completed < 0 or new_completed > order.quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Completed count must be between 0 and {order.quantity}"
        )
    
    order.completed = new_completed
    order.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/recalculate-progress", response_model=schemas.Order)  
def recalculate_order_progress(order_id: int, db: Session = Depends(get_db)):
    """Automatically recalculate the completed count based on actual inspected items"""
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Only count items from the last 24 hours to avoid old test data
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    # Count items with PASSED or OVERRIDDEN status as completed (recent items only)
    actual_completed = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id,
        InspectedItem.status.in_(['PASSED', 'OVERRIDDEN']),
        InspectedItem.created_at >= yesterday  # Only count recent inspections
    ).count()
    
    # Also check total items for this order (for debugging)
    total_items = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id
    ).count()
    
    recent_items = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id,
        InspectedItem.created_at >= yesterday
    ).count()
    
    # Update the order with the actual completed count
    old_completed = order.completed
    order.completed = actual_completed
    order.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    
    print(f"📊 Order {order_id} recalculated: {old_completed} → {actual_completed}")
    print(f"   Total items in DB: {total_items}, Recent items (24h): {recent_items}")
    print(f"   Recent completed items: {actual_completed}")
    
    return order


@router.post("/shipping", response_model=schemas.ShippingDetail, status_code=status.HTTP_201_CREATED)
def create_shipping_record(payload: schemas.ShippingDetailCreate, db: Session = Depends(get_db)):
    """Create a shipping record for a completed order"""
    # Validate order exists and can be shipped
    order = db.query(Order).get(payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.completed < order.quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Order not ready for shipping. Completed: {order.completed}/{order.quantity}"
        )
    
    # Check if order is already shipped
    existing_shipping = db.query(ShippingDetail).filter(
        ShippingDetail.order_id == payload.order_id
    ).first()
    
    if existing_shipping:
        raise HTTPException(
            status_code=400, 
            detail="Order has already been shipped"
        )
    
    shipping_record = ShippingDetail(
        **payload.model_dump(),
        created_at=datetime.utcnow()
    )
    
    db.add(shipping_record)
    db.commit()
    db.refresh(shipping_record)
    
    return shipping_record


@router.get("/{order_id}/shipping-status")
def get_order_shipping_status(order_id: int, db: Session = Depends(get_db)):
    """Check if an order has been shipped"""
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if there's a shipping detail with shipped_at timestamp
    shipping_detail = db.query(ShippingDetail).filter(
        ShippingDetail.order_id == order_id,
        ShippingDetail.shipped_at.isnot(None)
    ).first()
    
    return {
        "order_id": order_id,
        "is_shipped": shipping_detail is not None,
        "shipped_at": shipping_detail.shipped_at if shipping_detail else None,
        "tracking_number": shipping_detail.tracking_number if shipping_detail else None,
        "carrier": shipping_detail.shipping_method if shipping_detail else None
    }


@router.delete("/{order_id}/cleanup-test-data", response_model=schemas.Order)
def cleanup_order_test_data(order_id: int, db: Session = Depends(get_db)):
    """Clean up old test inspection data and reset order to fresh state"""
    order = db.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Count current inspection items
    current_items = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id
    ).count()
    
    # Delete ALL inspection items for this order (clean slate)
    deleted_count = db.query(InspectedItem).filter(
        InspectedItem.order_id == order_id
    ).delete()
    
    # Reset order progress to 0
    old_completed = order.completed
    order.completed = 0
    order.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    
    print(f"🧹 Order {order_id} cleanup complete:")
    print(f"   Removed {deleted_count} inspection items")
    print(f"   Reset completed: {old_completed} → 0")
    
    return order