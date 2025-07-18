# seed.py  ── run with:  python seed.py
import os
from datetime import date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the parent directory (project root)
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from models import (
    Base, User, Model, Product, InspectionRule,
    Order, AssignedSewer, InspectedItem, Flaw
)

# ------------------------------------------------------------------
# 1)  Database connection & table creation
# ------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Default to SQLite for development
    DATABASE_URL = "sqlite:///./stitchguard.db"
    print(f"⚠️  No DATABASE_URL found, using SQLite: {DATABASE_URL}")

# ✅ SECURITY FIX: Load model URLs from environment variables
BRA_ORIENTATION_MODEL_URL = os.getenv("BRA_ORIENTATION_MODEL_URL")
BRA_YOLO_MODEL_URL = os.getenv("BRA_YOLO_MODEL_URL")
BRA_YOLO_V2_MODEL_URL = os.getenv("BRA_YOLO_V2_MODEL_URL")

if not BRA_ORIENTATION_MODEL_URL:
    raise RuntimeError("BRA_ORIENTATION_MODEL_URL not set in .env")
if not BRA_YOLO_MODEL_URL:
    raise RuntimeError("BRA_YOLO_MODEL_URL not set in .env")
if not BRA_YOLO_V2_MODEL_URL:
    raise RuntimeError("BRA_YOLO_V2_MODEL_URL not set in .env")

engine = create_engine(DATABASE_URL, echo=False)

# DEV ONLY: wipe all existing tables so create_all() recreates them fresh
print("🗑️  Dropping all existing tables...")
Base.metadata.drop_all(engine)
print("🏗️  Creating all tables...")
Base.metadata.create_all(engine)

# ------------------------------------------------------------------
# 2)  Seed data (Sam, Yahya, Bra product, rules - NO ORDERS)
# ------------------------------------------------------------------
with Session(engine) as session:
    print("👥 Creating users...")
    
    # ---------- Users ----------
    # Note: Sam Wood is actually a sewer, Yahya Rahhawi is the supervisor
    sam_wood = User(
        name="Sam Wood",
        email="sam@builtmfgco.com",
        role="sewer",
        auth_id="B9908720-A3C6-4F7D-9D1B-123456789ABC"  # Placeholder, replace with actual if needed
    )
    yahya = User(
        name="Yahya Rahhawi",
        email="yahya@builtmfgco.com",
        role="supervisor",
        auth_id="0B0E9AB6-1234-5678-9ABC-DEF123456789"  # Placeholder, replace with actual if needed
    )
    jane = User(
        name="Jane Smith",
        email="jane@builtmfgco.com",
        role="sewer"
        # Jane doesn't have auth_id set yet
    )
    session.add_all([sam_wood, yahya, jane])
    session.flush()  # ensures IDs are assigned

    print("🤖 Creating ML models for bra inspection...")
    
    # ---------- Models (3 models as in current database) ----------
    # ✅ SECURITY FIX: Use environment variables instead of hardcoded URLs
    orientation_clf = Model(
        name="bra-orientation",
        type="cnn",
        version="1.0",
        platform="coreml",
        file_url=BRA_ORIENTATION_MODEL_URL,
        description="Classifies bra orientations: Back, Front, No Bra"
    )
    yolov8_model = Model(
        name="bra-yolo",
        type="yolov8",
        version="1.0",
        platform="coreml",
        file_url=BRA_YOLO_MODEL_URL,
        description="Detects GO, Logo, NGO flaws in bras"
    )
    yolov8_v2_model = Model(
        name="bra-yolo-v2",
        type="yolov8",
        version="1.0",
        platform="coreml",
        file_url=BRA_YOLO_V2_MODEL_URL,
        description="cache"
    )
    session.add_all([orientation_clf, yolov8_model, yolov8_v2_model])
    session.flush()

    print("👕 Creating bra inspection product...")
    
    # ---------- Products (Only Bra) ----------
    # Using model IDs [1, 3] as in current database (orientation + yolo-v2)
    bra_product = Product(
        name="Sports Bra Model A",
        description="High-performance sports bra with logo requirements",
        model_ids=[orientation_clf.id, yolov8_v2_model.id],  # Using v2 model as in current DB
        orientations_required=["Back", "Front"]
    )
    
    session.add_all([bra_product])
    session.flush()

    print("📋 Creating inspection rules for bra only...")
    
    # ---------- Inspection Rules for Bra Only (matching current database) ----------
    bra_rules = [
        InspectionRule(
            product_id=bra_product.id,
            orientation="Back",
            flaw_type="Bad-Straps",
            rule_type="fail_if_present",
            stability_seconds=3.0
        ),
        InspectionRule(
            product_id=bra_product.id,
            orientation="Back",
            flaw_type="Good-Straps",
            rule_type="fail_if_absent",
            stability_seconds=3.0
        ),
        InspectionRule(
            product_id=bra_product.id,
            orientation="Back",
            flaw_type="Logo",
            rule_type="fail_if_absent",
            stability_seconds=3.0
        ),
        InspectionRule(
            product_id=bra_product.id,
            orientation="Front",
            flaw_type="NonExistentFlaw",
            rule_type="fail_if_present",
            stability_seconds=3.0
        )
    ]
    
    session.add_all(bra_rules)
    session.flush()

    print("📦 Creating bra inspection order assigned to Sam (sewer)...")
    
    # ---------- Order (Matching current database: supervisor=1, sewer=2) ----------
    bra_order = Order(
        name="Bra Quality Inspection Batch #001",
        supervisor_id=yahya.id,  # Yahya is the supervisor
        sewer_id=sam_wood.id,   # Sam is the sewer
        product_id=bra_product.id,
        quantity=5,
        completed=1,
        deadline=date.today() + timedelta(days=30)
    )
    
    session.add(bra_order)
    session.flush()

    print("👷 Assigning bra inspection order to Sam (sewer)...")
    
    # ---------- Assigned Sewer (Sam assigned to the order) ----------
    assignment = AssignedSewer(
        order_id=bra_order.id,
        sewer_id=sam_wood.id
    )
    
    session.add(assignment)
    session.flush()

    print("🚫 Skipping other orders and sample inspection data as requested")

    # ---------- Commit everything ----------
    session.commit()

    print("✅ Database seeded successfully!")
    print(f"📊 Created:")
    print(f"   • {len([sam_wood, yahya, jane])} users")
    print(f"   • {len([orientation_clf, yolov8_model, yolov8_v2_model])} ML models (bra inspection)")
    print(f"   • {len([bra_product])} products (bra only)")
    print(f"   • {len(bra_rules)} inspection rules (bra only)")
    print(f"   • 1 order (bra inspection assigned to Sam by Yahya)")
    print(f"   • 1 assignment (Sam assigned to bra inspection)")
    print(f"\n🌐 Your API will be available at: http://localhost:8000")
    print(f"📚 API documentation: http://localhost:8000/docs")
    print(f"\n✅ Sam Wood should now see the bra inspection order in the iOS app!")
    print(f"✅ Yahya Rahhawi can create new orders via the supervisor tab!")