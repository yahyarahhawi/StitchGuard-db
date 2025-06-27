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
    supervisor = User(
        name="Sam Wood",
        email="sam@builtmfgco.com",
        role="supervisor"
    )
    yahya = User(
        name="Yahya Rahhawi",
        email="yahya@builtmfgco.com",
        role="sewer"
    )
    jane = User(
        name="Jane Smith",
        email="jane@builtmfgco.com",
        role="sewer"
    )
    session.add_all([supervisor, yahya, jane])
    session.flush()  # ensures IDs are assigned

    print("🤖 Creating ML models for bra inspection...")
    
    # ---------- Models (Only for Bra Inspection) ----------
    orientation_clf = Model(
        name="bra-orientation",
        type="cnn",
        version="1.0",
        platform="coreml",
        file_url="https://stitchguard-db-production.up.railway.app/api/v1/models/files/bra-orientation.mlmodelc",
        description="Classifies bra orientations: Back, Front, No Bra"
    )
    yolov8_model = Model(
        name="bra-yolo",
        type="yolov8",
        version="1.0",
        platform="coreml",
        file_url="https://stitchguard-db-production.up.railway.app/api/v1/models/files/bra-yolo.mlmodelc",
        description="Detects GO, Logo, NGO flaws in bras"
    )
    session.add_all([orientation_clf, yolov8_model])
    session.flush()

    print("👕 Creating bra inspection product...")
    
    # ---------- Products (Only Bra) ----------
    bra_product = Product(
        name="Sports Bra Model A",
        description="High-performance sports bra with logo requirements",
        model_ids=[orientation_clf.id, yolov8_model.id],
        orientations_required=["Back", "Front"]
    )
    
    session.add_all([bra_product])
    session.flush()

    print("📋 Creating inspection rules for bra only...")
    
    # ---------- Inspection Rules for Bra Only ----------
    bra_rules = [
        InspectionRule(
            product_id=bra_product.id,
            orientation="Back",
            flaw_type="NGO",
            rule_type="fail_if_present",
            stability_seconds=3.0
        ),
        InspectionRule(
            product_id=bra_product.id,
            orientation="Back",
            flaw_type="GO",
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

    print("📦 Creating bra inspection order for Yahya...")
    
    # ---------- Order (Only Bra Inspection) ----------
    bra_order = Order(
        name="Bra Quality Inspection Batch #001",
        supervisor_id=supervisor.id,
        product_id=bra_product.id,
        quantity=50,
        completed=0,
        assigned_by="Sam Wood",
        deadline=date.today() + timedelta(days=30)
    )
    
    session.add(bra_order)
    session.flush()

    print("👷 Assigning bra inspection order to Yahya...")
    
    # ---------- Assigned Sewer (Only Yahya) ----------
    assignment = AssignedSewer(
        order_id=bra_order.id,
        sewer_id=yahya.id
    )
    
    session.add(assignment)
    session.flush()

    print("🚫 Skipping other orders and sample inspection data as requested")

    # ---------- Commit everything ----------
    session.commit()

    print("✅ Database seeded successfully!")
    print(f"📊 Created:")
    print(f"   • {len([supervisor, yahya, jane])} users")
    print(f"   • {len([orientation_clf, yolov8_model])} ML models (bra inspection only)")
    print(f"   • {len([bra_product])} products (bra only)")
    print(f"   • {len(bra_rules)} inspection rules (bra only)")
    print(f"   • 1 order (bra inspection assigned to Yahya)")
    print(f"   • 1 assignment (Yahya assigned to bra inspection)")
    print(f"\n🌐 Your API will be available at: http://localhost:8000")
    print(f"📚 API documentation: http://localhost:8000/docs")
    print(f"\n✅ Yahya Rahhawi should now see the bra inspection order in the iOS app!")