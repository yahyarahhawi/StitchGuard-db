from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Text,
    Date, TIMESTAMP, Float, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY   # ⚠️ requires PostgreSQL back-end
from sqlalchemy.sql import func

Base = declarative_base()

# ---------------------------  USER  ---------------------------------
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False)  # 'sewer' | 'supervisor'
    auth_id = Column(String(255), unique=True, nullable=True)  # Supabase auth ID
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    supervised_orders = relationship("Order", back_populates="supervisor",
                                     foreign_keys='Order.supervisor_id')
    inspections = relationship("InspectedItem", back_populates="sewer",
                               foreign_keys='InspectedItem.sewer_id')


# --------------------------  PRODUCT  -------------------------------
class Product(Base):
    """
    A product (bra, shirt, …).  Each product knows:

    • which CoreML / ONNX models are needed (model_ids)
    • which physical orientations must be inspected (orientations_required)
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # IDs of the ML models used during inspection
    model_ids = Column(ARRAY(Integer), default=[])
    
    # Ordered list of orientations required for this product
    # e.g. ['Back', 'Front', 'Inside-Out Back']
    orientations_required = Column(ARRAY(String), default=[])
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    inspection_rules = relationship("InspectionRule", back_populates="product")
    orders = relationship("Order", back_populates="product")


# ---------------------------  MODEL  --------------------------------
class Model(Base):
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50))        # 'yolov8' | 'cnn' | …
    version = Column(String(50))
    description = Column(Text)

    platform = Column(String(50))           # 'coreml' | 'onnx' | 'pt'
    file_url = Column(Text)             # where the weight file is stored
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# -----------------------  INSPECTION RULE  --------------------------
class InspectionRule(Base):
    """
    Rule types (snake_case):

      • fail_if_present
      • alert_if_present
      • fail_if_absent
      • alert_if_absent
    """
    __tablename__ = 'inspection_rules'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    orientation = Column(String(100), nullable=False)              # 'Back', 'Front', …
    flaw_type = Column(String(100), nullable=False)              # 'NGO', 'GO', 'Loose Thread', …
    rule_type = Column(String(50), nullable=False)
    stability_seconds = Column(Float, default=3.0)  # Changed to Float for precision
    created_at = Column(DateTime, default=func.now())

    product = relationship("Product", back_populates="inspection_rules")


# ----------------------------  ORDER  -------------------------------
class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # Added missing name field
    supervisor_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    completed = Column(Integer, default=0)  # Added completed count
    assigned_by = Column(String(255))  # Added for iOS app compatibility
    deadline = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    supervisor = relationship("User", back_populates="supervised_orders",
                              foreign_keys=[supervisor_id])
    product = relationship("Product", back_populates="orders")
    assigned_sewers = relationship("AssignedSewer", back_populates="order")
    inspected_items = relationship("InspectedItem", back_populates="order")
    shipping_detail = relationship("ShippingDetail", back_populates="order",
                                   uselist=False)


# ---------------------  ASSIGNED SEWER (join)  ----------------------
class AssignedSewer(Base):
    __tablename__ = 'assigned_sewers'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    sewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_at = Column(DateTime, default=func.now())

    order = relationship("Order", back_populates="assigned_sewers")
    sewer = relationship("User")


# -----------------------  INSPECTED ITEM  ---------------------------
class InspectedItem(Base):
    __tablename__ = 'inspected_items'

    id = Column(Integer, primary_key=True)
    serial_number = Column(String(255), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    sewer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    passed = Column(Boolean, nullable=False)
    front_image_url = Column(Text)
    back_image_url = Column(Text)
    inspected_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    order = relationship("Order", back_populates="inspected_items")
    sewer = relationship("User", back_populates="inspections")
    flaws = relationship("Flaw", back_populates="item")


# -----------------------------  FLAW  -------------------------------
class Flaw(Base):
    __tablename__ = 'flaws'

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('inspected_items.id'), nullable=False)
    flaw_type = Column(String(100), nullable=False)
    orientation = Column(String(100), nullable=False)
    detected_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    item = relationship("InspectedItem", back_populates="flaws")


# -----------------------  SHIPPING DETAIL  -------------------------
class ShippingDetail(Base):
    __tablename__ = 'shipping_details'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    address = Column(Text, nullable=False)  # Updated to be required
    shipping_method = Column(String(100), nullable=False)  # Updated to be required (carrier)
    tracking_number = Column(String(255), nullable=False)  # Updated to be required
    completion_date = Column(Date)
    shipping_cost = Column(Float)
    receipt_photo_url = Column(Text)
    notes = Column(Text)  # New field for shipping notes
    shipped_at = Column(DateTime)  # New field for actual ship timestamp
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="shipping_detail")