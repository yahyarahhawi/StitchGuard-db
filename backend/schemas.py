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


class User(UserBase):
    id: int
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  PRODUCTS
# ------------------------------------------------------------------ #
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    model_ids: List[int] = []
    orientations_required: List[str] = []


class ProductCreate(ProductBase):
    pass


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ #
#  ORDERS
# ------------------------------------------------------------------ #
class OrderBase(BaseModel):
    name: str
    product_id: int
    quantity: int
    deadline: date
    assigned_by: Optional[str] = None


class OrderCreate(OrderBase):
    supervisor_id: int


class OrderUpdate(BaseModel):
    completed: Optional[int] = None
    deadline: Optional[date] = None


class Order(OrderBase):
    id: int
    supervisor_id: int
    completed: int = 0
    created_at: datetime
    updated_at: datetime

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
    passed: bool
    front_image_url: Optional[str] = None
    back_image_url: Optional[str] = None
    inspected_at: Optional[datetime] = None
    flaws: List[FlawIn] = []


class InspectedItemOut(BaseModel):
    id: int
    serial_number: str
    order_id: int
    sewer_id: int
    passed: bool
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


class ModelCreate(ModelBase):
    pass


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


class ShippingDetailCreate(ShippingDetailBase):
    order_id: int


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