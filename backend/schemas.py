"""
Pydantic schemas for API I/O
Compatible with Pydantic v2 (uses ConfigDict / from_attributes)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


# ------------------------------------------------------------------ #
#  USERS
# ------------------------------------------------------------------ #
class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    role: str  # 'sewer' | 'supervisor'


class UserAuthSync(BaseModel):
    auth_id: str
    email: str
    name: str
    role: str = "sewer"  # Default role


class User(UserBase):
    id: int
    role: str
    auth_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  PRODUCTS
# ------------------------------------------------------------------ #
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    orientations_required: List[str] = []


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductWithModels(ProductBase):
    """Product response with associated models included"""
    id: int
    created_at: datetime
    updated_at: datetime
    models: List['Model'] = []

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  ORDERS
# ------------------------------------------------------------------ #
class OrderBase(BaseModel):
    name: str
    product_id: int
    quantity: int
    deadline: date


class OrderCreate(OrderBase):
    supervisor_id: int
    sewer_id: int  # NEW: Direct sewer assignment


class OrderUpdate(BaseModel):
    completed: Optional[int] = None
    deadline: Optional[date] = None
    sewer_id: Optional[int] = None  # NEW: Allow updating sewer assignment


class Order(OrderBase):
    id: int
    supervisor_id: int
    sewer_id: int  # NEW: Direct sewer assignment
    completed: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderWithNames(OrderBase):
    """Enhanced Order response with supervisor and sewer names for UI display"""
    id: int
    supervisor_id: int
    sewer_id: int
    completed: int = 0
    created_at: datetime
    updated_at: datetime
    
    # Additional fields for UI
    supervisor_name: str
    sewer_name: str

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  INSPECTION CONFIG & RULES
# ------------------------------------------------------------------ #
class InspectionRuleBase(BaseModel):
    orientation: str
    flaw_type: str
    rule_type: str
    stability_seconds: float = 3.0


class InspectionRuleCreate(InspectionRuleBase):
    product_id: int


class InspectionRuleOut(InspectionRuleBase):
    id: int
    product_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectionConfigOut(BaseModel):
    product_id: int
    orientations_required: List[str]
    rules: List[InspectionRuleOut]


# ------------------------------------------------------------------ #
#  INSPECTED ITEM (POST)
# ------------------------------------------------------------------ #
class FlawIn(BaseModel):
    flaw_type: str
    orientation: str
    detected_at: Optional[datetime] = None


class FlawOut(FlawIn):
    id: int
    item_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InspectedItemCreate(BaseModel):
    serial_number: str
    order_id: int
    sewer_id: int
    status: str  # 'PASSED', 'FAILED', 'OVERRIDDEN'
    front_image_url: Optional[str] = None
    back_image_url: Optional[str] = None
    inspected_at: Optional[datetime] = None
    flaws: List[FlawIn] = []


class InspectedItemOut(BaseModel):
    id: int
    serial_number: str
    order_id: int
    sewer_id: int
    status: str  # 'PASSED', 'FAILED', 'OVERRIDDEN'
    front_image_url: Optional[str] = None
    back_image_url: Optional[str] = None
    inspected_at: datetime
    created_at: datetime
    flaws: List[FlawOut] = []

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  MODELS
# ------------------------------------------------------------------ #
class ModelBase(BaseModel):
    name: str
    type: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    platform: Optional[str] = None
    file_url: Optional[str] = None
    product_id: Optional[int] = None


class ModelCreate(ModelBase):
    product_id: int  # Required when creating a model


class Model(ModelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  SHIPPING DETAILS
# ------------------------------------------------------------------ #
class ShippingDetailBase(BaseModel):
    address: Optional[str] = None
    shipping_method: Optional[str] = None
    tracking_number: Optional[str] = None
    completion_date: Optional[date] = None
    shipping_cost: Optional[float] = None
    receipt_photo_url: Optional[str] = None
    notes: Optional[str] = None
    shipped_at: Optional[datetime] = None


class ShippingDetailCreate(BaseModel):
    """Schema for creating shipping details when an order is shipped"""
    order_id: int
    address: str  # Required for shipping
    shipping_method: str  # Required - acts as carrier (UPS, FedEx, etc.)
    tracking_number: str  # Required
    notes: Optional[str] = None
    shipped_at: datetime  # When the order was actually shipped


class ShippingDetailUpdate(ShippingDetailBase):
    pass


class ShippingDetail(ShippingDetailBase):
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  STATISTICS & ANALYTICS
# ------------------------------------------------------------------ #
class OrderStats(BaseModel):
    total_orders: int
    completed_orders: int
    pending_orders: int
    total_items: int
    passed_items: int
    failed_items: int
    pass_rate: float


class UserStats(BaseModel):
    total_inspections: int
    passed_inspections: int
    failed_inspections: int
    pass_rate: float