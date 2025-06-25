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
# 2)  Seed data (Sam, Yahya, Bra product, rules, order)
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

    print("🤖 Creating ML models...")
    
    # ---------- Models ----------
    orientation_clf = Model(
        name="bra-orientation",
        type="cnn",
        version="1.0",
        platform="coreml",
        file_url="https://cdn.example.com/models/bra-orientation-v1.0.mlpackage",
        description="Classifies garment orientations: Back, Front, No Bra"
    )
    yolov8_model = Model(
        name="bra-yolo",
        type="yolov8",
        version="1.0",
        platform="coreml",
        file_url="https://cdn.example.com/models/bra-yolo-v1.0.mlmodel",
        description="Detects GO, Logo, NGO flaws in bras"
    )
    session.add_all([orientation_clf, yolov8_model])
    session.flush()

    print("👕 Creating products...")
    
    # ---------- Products ----------
    bra_product = Product(
        name="Sports Bra Model A",
        description="High-performance sports bra with logo requirements",
        model_ids=[orientation_clf.id, yolov8_model.id],
        orientations_required=["Back", "Front"]
    )
    
    tshirt_product = Product(
        name="Cotton T-Shirt",
        description="Basic cotton t-shirt with quality checks",
        model_ids=[orientation_clf.id, yolov8_model.id],
        orientations_required=["Front", "Back"]
    )
    
    session.add_all([bra_product, tshirt_product])
    session.flush()

    print("📋 Creating inspection rules...")
    
    # ---------- Inspection Rules for Bra ----------
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
    
    # ---------- Inspection Rules for T-Shirt ----------
    tshirt_rules = [
        InspectionRule(
            product_id=tshirt_product.id,
            orientation="Front",
            flaw_type="Stain",
            rule_type="fail_if_present",
            stability_seconds=2.0
        ),
        InspectionRule(
            product_id=tshirt_product.id,
            orientation="Back",
            flaw_type="Loose Thread",
            rule_type="alert_if_present",
            stability_seconds=2.0
        )
    ]
    
    session.add_all(bra_rules + tshirt_rules)
    session.flush()

    print("📦 Creating orders...")
    
    # ---------- Orders ----------
    bra_order = Order(
        name="Bra Production Batch #001",
        supervisor_id=supervisor.id,
        product_id=bra_product.id,
        quantity=50,
        completed=15,
        assigned_by="Sam Wood",
        deadline=date.today() + timedelta(days=30)
    )
    
    tshirt_order = Order(
        name="T-Shirt Summer Collection",
        supervisor_id=supervisor.id,
        product_id=tshirt_product.id,
        quantity=100,
        completed=25,
        assigned_by="Sam Wood",
        deadline=date.today() + timedelta(days=45)
    )
    
    session.add_all([bra_order, tshirt_order])
    session.flush()

    print("👷 Assigning sewers to orders...")
    
    # ---------- Assigned Sewers ----------
    assignments = [
        AssignedSewer(
            order_id=bra_order.id,
            sewer_id=yahya.id
        ),
        AssignedSewer(
            order_id=tshirt_order.id,
            sewer_id=jane.id
        )
    ]
    session.add_all(assignments)
    session.flush()

    print("🔍 Creating sample inspection results...")
    
    # ---------- Sample Inspected Items ----------
    sample_items = []
    sample_flaws = []
    
    # Create some passed and failed items for bra order
    for i in range(1, 16):  # 15 completed items
        passed = i % 4 != 0  # Fail every 4th item
        
        item = InspectedItem(
            serial_number=f"BRA-{bra_order.id:03d}-{i:03d}",
            order_id=bra_order.id,
            sewer_id=yahya.id,
            passed=passed,
            inspected_at=datetime.now() - timedelta(days=i)
        )
        sample_items.append(item)
        
        # Add flaws for failed items
        if not passed:
            flaw = Flaw(
                flaw_type="NGO",
                orientation="Back",
                detected_at=item.inspected_at
            )
            sample_flaws.append((item, flaw))
    
    # Create some items for t-shirt order
    for i in range(1, 26):  # 25 completed items
        passed = i % 5 != 0  # Fail every 5th item
        
        item = InspectedItem(
            serial_number=f"TSHIRT-{tshirt_order.id:03d}-{i:03d}",
            order_id=tshirt_order.id,
            sewer_id=jane.id,
            passed=passed,
            inspected_at=datetime.now() - timedelta(days=i)
        )
        sample_items.append(item)
        
        # Add flaws for failed items
        if not passed:
            flaw = Flaw(
                flaw_type="Stain",
                orientation="Front",
                detected_at=item.inspected_at
            )
            sample_flaws.append((item, flaw))
    
    session.add_all(sample_items)
    session.flush()
    
    # Add flaws with proper item_id references
    for item, flaw in sample_flaws:
        flaw.item_id = item.id
        session.add(flaw)

    # ---------- Commit everything ----------
    session.commit()

    print("✅ Database seeded successfully!")
    print(f"📊 Created:")
    print(f"   • {len([supervisor, yahya, jane])} users")
    print(f"   • {len([orientation_clf, yolov8_model])} ML models")
    print(f"   • {len([bra_product, tshirt_product])} products")
    print(f"   • {len(bra_rules + tshirt_rules)} inspection rules")
    print(f"   • {len([bra_order, tshirt_order])} orders")
    print(f"   • {len(sample_items)} inspected items")
    print(f"   • {len(sample_flaws)} flaws")
    print(f"\n🌐 Your API will be available at: http://localhost:8000")
    print(f"📚 API documentation: http://localhost:8000/docs")