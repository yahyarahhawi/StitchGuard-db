from typing import List
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

import backend.schemas as schemas
from backend.deps import get_db
from db.models import Order, User, InspectedItem, Flaw

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=schemas.OrderStats)
def get_overview_stats(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db)
):
    """Get overall system statistics"""
    
    # Build date filter
    date_filter = []
    if start_date:
        date_filter.append(InspectedItem.inspected_at >= start_date)
    if end_date:
        date_filter.append(InspectedItem.inspected_at <= end_date)
    
    # Total orders
    total_orders = db.query(Order).count()
    
    # Completed orders (where completed >= quantity)
    completed_orders = db.query(Order).filter(
        Order.completed >= Order.quantity
    ).count()
    
    pending_orders = total_orders - completed_orders
    
    # Inspection statistics
    items_query = db.query(InspectedItem)
    if date_filter:
        items_query = items_query.filter(and_(*date_filter))
    
    total_items = items_query.count()
    passed_items = items_query.filter(InspectedItem.passed == True).count()
    failed_items = total_items - passed_items
    pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0
    
    return schemas.OrderStats(
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        total_items=total_items,
        passed_items=passed_items,
        failed_items=failed_items,
        pass_rate=pass_rate
    )


@router.get("/users/{user_id}/stats", response_model=schemas.UserStats)
def get_user_stats(
    user_id: int,
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db)
):
    """Get statistics for a specific user"""
    
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build date filter
    date_filter = [InspectedItem.sewer_id == user_id]
    if start_date:
        date_filter.append(InspectedItem.inspected_at >= start_date)
    if end_date:
        date_filter.append(InspectedItem.inspected_at <= end_date)
    
    # User inspection statistics
    total_inspections = db.query(InspectedItem).filter(and_(*date_filter)).count()
    passed_inspections = db.query(InspectedItem).filter(
        and_(*date_filter),
        InspectedItem.passed == True
    ).count()
    
    failed_inspections = total_inspections - passed_inspections
    pass_rate = (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0
    
    return schemas.UserStats(
        total_inspections=total_inspections,
        passed_inspections=passed_inspections,
        failed_inspections=failed_inspections,
        pass_rate=pass_rate
    )


@router.get("/flaws/frequency")
def get_flaw_frequency(
    start_date: date = Query(None),
    end_date: date = Query(None),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get most common flaws"""
    
    # Build date filter through InspectedItem relationship
    query = db.query(
        Flaw.flaw_type,
        func.count(Flaw.id).label('count')
    ).join(InspectedItem)
    
    if start_date:
        query = query.filter(InspectedItem.inspected_at >= start_date)
    if end_date:
        query = query.filter(InspectedItem.inspected_at <= end_date)
    
    results = query.group_by(Flaw.flaw_type).order_by(
        func.count(Flaw.id).desc()
    ).limit(limit).all()
    
    return [{"flaw_type": flaw_type, "count": count} for flaw_type, count in results]


@router.get("/trends/daily")
def get_daily_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get daily inspection trends"""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Get daily inspection counts
    results = db.query(
        func.date(InspectedItem.inspected_at).label('date'),
        func.count(InspectedItem.id).label('total'),
        func.sum(func.cast(InspectedItem.passed, Integer)).label('passed')
    ).filter(
        InspectedItem.inspected_at >= start_date,
        InspectedItem.inspected_at <= end_date
    ).group_by(
        func.date(InspectedItem.inspected_at)
    ).order_by(
        func.date(InspectedItem.inspected_at)
    ).all()
    
    return [
        {
            "date": str(date),
            "total": total,
            "passed": passed or 0,
            "failed": total - (passed or 0),
            "pass_rate": ((passed or 0) / total * 100) if total > 0 else 0
        }
        for date, total, passed in results
    ] 