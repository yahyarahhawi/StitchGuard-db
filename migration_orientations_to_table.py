#!/usr/bin/env python3
"""
Migration: Move orientations_required from JSON array to separate table

This migration:
1. Creates new product_orientations table
2. Migrates existing orientation data from products.orientations_required
3. Updates Product model relationships
4. Removes the old orientations_required column

Run with: python migration_orientations_to_table.py
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path so we can import our models
sys.path.append(str(Path(__file__).parent))

from db.models import Base, Product

def main():
    """Run the migration"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        DATABASE_URL = "sqlite:///./stitchguard.db"
        print(f"⚠️  No DATABASE_URL found, using SQLite: {DATABASE_URL}")

    engine = create_engine(DATABASE_URL, echo=True)
    
    with Session(engine) as session:
        try:
            print("🚀 Starting orientations migration...")
            
            # Step 1: Create the new product_orientations table
            print("📝 Creating product_orientations table...")
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS product_orientations (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL,
                    orientation VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_product_orientations_product_id 
                        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    CONSTRAINT unique_product_orientation 
                        UNIQUE(product_id, orientation)
                )
            """))
            
            # Step 2: Get all products with their current orientations
            print("📊 Fetching existing products and orientations...")
            result = session.execute(text(
                "SELECT id, name, orientations_required FROM products WHERE orientations_required IS NOT NULL"
            ))
            
            products_data = result.fetchall()
            print(f"📦 Found {len(products_data)} products with orientation data")
            
            # Step 3: Migrate data from JSON array to relational table
            print("🔄 Migrating orientation data...")
            total_orientations = 0
            
            for product_id, product_name, orientations_json in products_data:
                if orientations_json:
                    print(f"  📋 Processing product: {product_name} (ID: {product_id})")
                    
                    # Parse orientations (they should be a list)
                    if isinstance(orientations_json, list):
                        orientations = orientations_json
                    else:
                        print(f"    ⚠️  Unexpected orientation format for product {product_id}: {orientations_json}")
                        continue
                    
                    # Insert each orientation as a separate row
                    for orientation in orientations:
                        try:
                            session.execute(text("""
                                INSERT INTO product_orientations (product_id, orientation) 
                                VALUES (:product_id, :orientation)
                                ON CONFLICT (product_id, orientation) DO NOTHING
                            """), {
                                "product_id": product_id,
                                "orientation": orientation.strip()
                            })
                            total_orientations += 1
                            print(f"    ✅ Added orientation: {orientation}")
                        except Exception as e:
                            print(f"    ❌ Failed to insert orientation '{orientation}' for product {product_id}: {e}")
            
            # Step 4: Verify the migration
            print("🔍 Verifying migration...")
            verification_result = session.execute(text("""
                SELECT p.id, p.name, po.orientation 
                FROM products p 
                LEFT JOIN product_orientations po ON p.id = po.product_id 
                ORDER BY p.id, po.orientation
            """))
            
            verification_data = verification_result.fetchall()
            print("📊 Migration verification:")
            current_product = None
            for product_id, product_name, orientation in verification_data:
                if current_product != product_id:
                    print(f"  📦 Product: {product_name} (ID: {product_id})")
                    current_product = product_id
                if orientation:
                    print(f"    🎯 Orientation: {orientation}")
                else:
                    print(f"    📭 No orientations found")
            
            # Step 5: Drop the old orientations_required column
            print("🗑️  Removing old orientations_required column...")
            session.execute(text("ALTER TABLE products DROP COLUMN IF EXISTS orientations_required"))
            
            # Commit all changes
            session.commit()
            
            print(f"✅ Migration completed successfully!")
            print(f"📊 Summary:")
            print(f"   • Processed {len(products_data)} products")
            print(f"   • Migrated {total_orientations} orientation records")
            print(f"   • Created product_orientations table")
            print(f"   • Removed orientations_required column")
            print(f"")
            print(f"🔄 Next steps:")
            print(f"   1. Update db/models.py to include ProductOrientation model")
            print(f"   2. Update backend schemas to use the new relationship")
            print(f"   3. Update API endpoints to query the new table")
            print(f"   4. Test the changes")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            session.rollback()
            raise
        
if __name__ == "__main__":
    main()