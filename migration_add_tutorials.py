#!/usr/bin/env python3
"""
Database migration script to add tutorials and tutorial_steps tables
for product tutorial functionality.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

def main():
    print("🎓 Starting Tutorial Tables Migration...")
    print("=" * 50)
    
    # Load environment variables
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set in .env")
        return False
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        with engine.connect() as conn:
            print("📊 Current state - Checking existing products:")
            print("-" * 40)
            
            # Show current products
            result = conn.execute(text("SELECT id, name FROM products ORDER BY id"))
            products_data = []
            for row in result:
                print(f"  Product {row[0]}: {row[1]}")
                products_data.append((row[0], row[1]))
            
            # Step 1: Create tutorials table
            print("\n🏗️  Step 1: Creating tutorials table...")
            try:
                conn.execute(text("""
                    CREATE TABLE tutorials (
                        id SERIAL PRIMARY KEY,
                        product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        is_active BOOLEAN NOT NULL DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("✅ Created tutorials table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("ℹ️  tutorials table already exists, skipping...")
                else:
                    print(f"❌ Error creating tutorials table: {e}")
                    return False
            
            # Step 2: Create tutorial_steps table
            print("\n🏗️  Step 2: Creating tutorial_steps table...")
            try:
                conn.execute(text("""
                    CREATE TABLE tutorial_steps (
                        id SERIAL PRIMARY KEY,
                        tutorial_id INTEGER NOT NULL REFERENCES tutorials(id) ON DELETE CASCADE,
                        step_number INTEGER NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        image_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(tutorial_id, step_number)
                    )
                """))
                conn.commit()
                print("✅ Created tutorial_steps table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("ℹ️  tutorial_steps table already exists, skipping...")
                else:
                    print(f"❌ Error creating tutorial_steps table: {e}")
                    return False
            
            # Step 3: Add indexes for better performance
            print("\n🔗 Step 3: Adding indexes...")
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tutorials_product_id ON tutorials(product_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tutorials_active ON tutorials(is_active)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tutorial_steps_tutorial_id ON tutorial_steps(tutorial_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_tutorial_steps_order ON tutorial_steps(tutorial_id, step_number)"))
                conn.commit()
                print("✅ Added performance indexes")
            except Exception as e:
                print(f"⚠️  Could not add indexes: {e}")
                print("   This is okay - indexes might already exist")
            
            # Step 4: Create sample tutorial for each product
            print("\n📚 Step 4: Creating sample tutorials...")
            for product_id, product_name in products_data:
                # Create tutorial
                tutorial_title = f"{product_name} Production Tutorial"
                tutorial_description = f"Step-by-step tutorial for {product_name} production setup and quality inspection"
                
                result = conn.execute(text("""
                    INSERT INTO tutorials (product_id, title, description, is_active)
                    VALUES (:product_id, :title, :description, true)
                    RETURNING id
                """), {
                    "product_id": product_id,
                    "title": tutorial_title,
                    "description": tutorial_description
                })
                tutorial_id = result.fetchone()[0]
                conn.commit()
                
                print(f"  ✅ Created tutorial {tutorial_id} for {product_name}")
                
                # Create 5 tutorial steps
                tutorial_steps = [
                    {
                        "step_number": 1,
                        "title": "Prepare Workspace",
                        "description": f"Set up your workspace for {product_name} production. Ensure good lighting and clean surface."
                    },
                    {
                        "step_number": 2,
                        "title": "Position Product",
                        "description": f"Place the {product_name} in the correct orientation for inspection."
                    },
                    {
                        "step_number": 3,
                        "title": "Check Required Orientations",
                        "description": "Verify that you can access all required inspection orientations (Back, Front, etc.)"
                    },
                    {
                        "step_number": 4,
                        "title": "Camera Setup",
                        "description": "Position your device camera at the optimal distance for clear inspection images."
                    },
                    {
                        "step_number": 5,
                        "title": "Begin Inspection",
                        "description": "Start the inspection process following the on-screen prompts for each orientation."
                    }
                ]
                
                for step in tutorial_steps:
                    conn.execute(text("""
                        INSERT INTO tutorial_steps (tutorial_id, step_number, title, description, image_url)
                        VALUES (:tutorial_id, :step_number, :title, :description, :image_url)
                    """), {
                        "tutorial_id": tutorial_id,
                        "step_number": step["step_number"],
                        "title": step["title"],
                        "description": step["description"],
                        "image_url": None  # Will be added manually in Supabase
                    })
                    print(f"    📝 Added step {step['step_number']}: {step['title']}")
                
                conn.commit()
            
            # Step 5: Verify migration
            print("\n🔍 Step 5: Verifying migration...")
            print("-" * 40)
            
            # Count tutorials
            result = conn.execute(text("SELECT COUNT(*) FROM tutorials"))
            tutorial_count = result.fetchone()[0]
            print(f"📚 Total tutorials created: {tutorial_count}")
            
            # Count tutorial steps
            result = conn.execute(text("SELECT COUNT(*) FROM tutorial_steps"))
            steps_count = result.fetchone()[0]
            print(f"📝 Total tutorial steps created: {steps_count}")
            
            # Show tutorial details
            result = conn.execute(text("""
                SELECT t.id, t.title, t.product_id, p.name as product_name, 
                       COUNT(ts.id) as step_count
                FROM tutorials t
                JOIN products p ON t.product_id = p.id
                LEFT JOIN tutorial_steps ts ON t.id = ts.tutorial_id
                GROUP BY t.id, t.title, t.product_id, p.name
                ORDER BY t.id
            """))
            
            print(f"\n📋 Tutorial Summary:")
            for row in result:
                print(f"  Tutorial {row[0]}: '{row[1]}' for {row[3]} ({row[4]} steps)")
            
            print(f"\n✅ Migration completed successfully!")
            print(f"🎉 Tutorial system ready for use!")
            
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Next steps:")
        print("1. Update SQLAlchemy models to include Tutorial and TutorialStep")
        print("2. Update Pydantic schemas for API responses")
        print("3. Create API endpoints for tutorials")
        print("4. Add image URLs manually in Supabase storage")
        print("5. Test the tutorial functionality in the iOS app")
    else:
        print("\n💥 Migration failed - please check the errors above")