#!/usr/bin/env python3
"""
Database migration script to add product_id foreign key to models table
and migrate existing data from products.model_ids array to the new structure.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, Integer, ForeignKey
from sqlalchemy.orm import Session

def main():
    print("🔄 Starting Database Migration...")
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
            print("📊 Current state - Products with model_ids:")
            print("-" * 40)
            
            # Show current products and their model_ids
            result = conn.execute(text("SELECT id, name, model_ids FROM products ORDER BY id"))
            products_data = []
            for row in result:
                print(f"  Product {row[0]}: {row[1]} -> Models: {row[2]}")
                products_data.append((row[0], row[1], row[2]))
            
            print("\n🤖 Current models:")
            print("-" * 40)
            result = conn.execute(text("SELECT id, name, type FROM models ORDER BY id"))
            models_data = []
            for row in result:
                print(f"  Model {row[0]}: {row[1]} ({row[2]})")
                models_data.append((row[0], row[1], row[2]))
            
            # Step 1: Add product_id column to models table
            print("\n🏗️  Step 1: Adding product_id column to models table...")
            try:
                conn.execute(text("ALTER TABLE models ADD COLUMN product_id INTEGER"))
                conn.commit()
                print("✅ Added product_id column")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print("ℹ️  product_id column already exists, skipping...")
                else:
                    print(f"❌ Error adding column: {e}")
                    return False
            
            # Step 2: Migrate data from products.model_ids to models.product_id
            print("\n🔄 Step 2: Migrating model assignments...")
            for product_id, product_name, model_ids in products_data:
                if model_ids:  # If there are model_ids to migrate
                    print(f"  Assigning models {model_ids} to product '{product_name}' (ID: {product_id})")
                    for model_id in model_ids:
                        # Update the model to reference this product
                        conn.execute(text(
                            "UPDATE models SET product_id = :product_id WHERE id = :model_id"
                        ), {"product_id": product_id, "model_id": model_id})
                        print(f"    ✅ Model {model_id} -> Product {product_id}")
                    conn.commit()
            
            # Step 3: Add foreign key constraint
            print("\n🔗 Step 3: Adding foreign key constraint...")
            try:
                conn.execute(text(
                    "ALTER TABLE models ADD CONSTRAINT fk_models_product_id "
                    "FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE"
                ))
                conn.commit()
                print("✅ Added foreign key constraint")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("ℹ️  Foreign key constraint already exists, skipping...")
                else:
                    print(f"❌ Error adding foreign key: {e}")
                    return False
            
            # Step 4: Remove model_ids column from products (optional - comment out if you want to keep it for backup)
            print("\n🗑️  Step 4: Removing model_ids column from products...")
            try:
                conn.execute(text("ALTER TABLE products DROP COLUMN model_ids"))
                conn.commit()
                print("✅ Removed model_ids column from products")
            except Exception as e:
                print(f"⚠️  Could not remove model_ids column: {e}")
                print("   This is okay - you can remove it manually later")
            
            # Step 5: Verify migration
            print("\n🔍 Step 5: Verifying migration...")
            print("-" * 40)
            
            result = conn.execute(text(
                "SELECT m.id, m.name, m.product_id, p.name as product_name "
                "FROM models m "
                "LEFT JOIN products p ON m.product_id = p.id "
                "ORDER BY m.id"
            ))
            
            for row in result:
                product_info = f"Product: {row[3]}" if row[3] else "No Product"
                print(f"  Model {row[0]}: {row[1]} -> {product_info}")
            
            print(f"\n✅ Migration completed successfully!")
            print(f"🎉 Models now reference products via foreign key relationship")
            
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Next steps:")
        print("1. Update your SQLAlchemy models")
        print("2. Update your API schemas") 
        print("3. Update your API endpoints")
        print("4. Test the new relationship queries")
    else:
        print("\n💥 Migration failed - please check the errors above")