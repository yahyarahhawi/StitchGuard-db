#!/usr/bin/env python3
"""
Check current order and sewer assignment data
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def main():
    print("🔍 Checking Order Assignment Data...")
    print("=" * 40)
    
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
            # Check total orders
            result = conn.execute(text("SELECT COUNT(*) FROM orders"))
            total_orders = result.fetchone()[0]
            print(f"📊 Total orders: {total_orders}")
            
            # Check orders with assignments
            result = conn.execute(text("SELECT COUNT(DISTINCT order_id) FROM assigned_sewers"))
            orders_with_assignments = result.fetchone()[0]
            print(f"👷 Orders with sewer assignments: {orders_with_assignments}")
            
            # Check orders without assignments
            result = conn.execute(text("""
                SELECT COUNT(*) FROM orders 
                WHERE id NOT IN (SELECT DISTINCT order_id FROM assigned_sewers)
            """))
            orders_without_assignments = result.fetchone()[0]
            print(f"❌ Orders WITHOUT assignments: {orders_without_assignments}")
            
            # Show sample unassigned orders
            if orders_without_assignments > 0:
                print("\n📋 Unassigned orders:")
                result = conn.execute(text("""
                    SELECT id, name, supervisor_id 
                    FROM orders 
                    WHERE id NOT IN (SELECT DISTINCT order_id FROM assigned_sewers)
                    LIMIT 5
                """))
                for row in result:
                    print(f"  Order {row[0]}: {row[1]} (Supervisor: {row[2]})")
            
            # Check available sewers
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE role = 'sewer'"))
            total_sewers = result.fetchone()[0]
            print(f"\n👤 Total sewers available: {total_sewers}")
            
            if total_sewers > 0:
                print("\n🔧 Available sewers:")
                result = conn.execute(text("SELECT id, name FROM users WHERE role = 'sewer' LIMIT 5"))
                for row in result:
                    print(f"  Sewer {row[0]}: {row[1]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main() 