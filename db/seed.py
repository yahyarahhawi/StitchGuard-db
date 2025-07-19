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
    Order, AssignedSewer, InspectedItem, Flaw,
    Tutorial, TutorialStep
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

    print("👕 Creating bra inspection product first...")
    
    # ---------- Products (Only Bra) - Create BEFORE models ----------
    bra_product = Product(
        name="Sports Bra Model A",
        description="High-performance sports bra with logo requirements",
        orientations_required=["Back", "Front"]
    )
    
    session.add(bra_product)
    session.flush()  # Get the product ID

    print("🤖 Creating ML models for bra inspection...")
    
    # ---------- Models (3 models as in current database) ----------
    # ✅ SECURITY FIX: Use environment variables instead of hardcoded URLs
    # Now models reference the product via foreign key
    orientation_clf = Model(
        name="bra-orientation",
        type="cnn",
        version="1.0",
        platform="coreml",
        file_url=BRA_ORIENTATION_MODEL_URL,
        description="Classifies bra orientations: Back, Front, No Bra",
        product_id=bra_product.id
    )
    yolov8_model = Model(
        name="bra-yolo",
        type="yolov8",
        version="1.0",
        platform="coreml",
        file_url=BRA_YOLO_MODEL_URL,
        description="Detects GO, Logo, NGO flaws in bras",
        product_id=bra_product.id
    )
    yolov8_v2_model = Model(
        name="bra-yolo-v2",
        type="yolov8",
        version="1.0",
        platform="coreml",
        file_url=BRA_YOLO_V2_MODEL_URL,
        description="cache",
        product_id=bra_product.id
    )
    session.add_all([orientation_clf, yolov8_model, yolov8_v2_model])
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

    print("📚 Creating tutorial for bra production...")
    
    # ---------- Tutorial for Bra Product ----------
    bra_tutorial = Tutorial(
        product_id=bra_product.id,
        title="Sports Bra Production Tutorial",
        description="Step-by-step tutorial for Sports Bra production setup and quality inspection",
        is_active=True
    )
    
    session.add(bra_tutorial)
    session.flush()

    print("📝 Creating 5 tutorial steps...")
    
    # ---------- Tutorial Steps ----------
    tutorial_steps = [
        TutorialStep(
            tutorial_id=bra_tutorial.id,
            step_number=1,
            title="Prepare Workspace",
            description="Set up your workspace for Sports Bra production. Ensure good lighting and clean surface.",
            image_url=None  # Will be added manually in Supabase
        ),
        TutorialStep(
            tutorial_id=bra_tutorial.id,
            step_number=2,
            title="Position Product",
            description="Place the Sports Bra in the correct orientation for inspection.",
            image_url=None
        ),
        TutorialStep(
            tutorial_id=bra_tutorial.id,
            step_number=3,
            title="Check Required Orientations",
            description="Verify that you can access all required inspection orientations (Back, Front).",
            image_url=None
        ),
        TutorialStep(
            tutorial_id=bra_tutorial.id,
            step_number=4,
            title="Camera Setup",
            description="Position your device camera at the optimal distance for clear inspection images.",
            image_url=None
        ),
        TutorialStep(
            tutorial_id=bra_tutorial.id,
            step_number=5,
            title="Begin Inspection",
            description="Start the inspection process following the on-screen prompts for each orientation.",
            image_url=None
        )
    ]
    
    session.add_all(tutorial_steps)
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
    print(f"   • 1 tutorial with {len(tutorial_steps)} steps (bra production)")
    print(f"\n🌐 Your API will be available at: http://localhost:8000")
    print(f"📚 API documentation: http://localhost:8000/docs")
    print(f"\n✅ Sam Wood should now see the bra inspection order in the iOS app!")
    print(f"✅ Yahya Rahhawi can create new orders via the supervisor tab!")
    print(f"📚 Tutorial available at: /api/v1/tutorials/product/{bra_product.id}/active")