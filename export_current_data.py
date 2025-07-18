#!/usr/bin/env python3
"""
Export current database data to understand what needs to be in the seed file
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime

def main():
    print("📊 Exporting Current Database Data...")
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
            print("👥 USERS:")
            print("-" * 30)
            result = conn.execute(text("SELECT id, name, email, role, auth_id FROM users ORDER BY id"))
            for row in result:
                auth_id = row[4] if row[4] else "None"
                print(f"  ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Role: {row[3]}, Auth ID: {auth_id[:8]}...")
            
            print("\n🤖 MODELS:")
            print("-" * 30)
            result = conn.execute(text("SELECT id, name, type, version, platform, file_url, description FROM models ORDER BY id"))
            for row in result:
                print(f"  ID: {row[0]}, Name: {row[1]}, Type: {row[2]}, Version: {row[3]}")
                print(f"    Platform: {row[4]}, URL: {row[5]}")
                print(f"    Description: {row[6]}")
            
            print("\n👕 PRODUCTS:")
            print("-" * 30)
            result = conn.execute(text("SELECT id, name, description, model_ids, orientations_required FROM products ORDER BY id"))
            for row in result:
                print(f"  ID: {row[0]}, Name: {row[1]}")
                print(f"    Description: {row[2]}")
                print(f"    Model IDs: {row[3]}")
                print(f"    Orientations: {row[4]}")
            
            print("\n📋 INSPECTION RULES:")
            print("-" * 30)
            result = conn.execute(text("SELECT id, product_id, orientation, flaw_type, rule_type, stability_seconds FROM inspection_rules ORDER BY product_id, orientation"))
            for row in result:
                print(f"  ID: {row[0]}, Product: {row[1]}, Orientation: {row[2]}")
                print(f"    Flaw: {row[3]}, Rule: {row[4]}, Stability: {row[5]}s")
            
            print("\n📦 ORDERS:")
            print("-" * 30)
            result = conn.execute(text("SELECT id, name, supervisor_id, sewer_id, product_id, quantity, completed, deadline FROM orders ORDER BY id"))
            for row in result:
                print(f"  ID: {row[0]}, Name: {row[1]}")
                print(f"    Supervisor: {row[2]}, Sewer: {row[3]}, Product: {row[4]}")
                print(f"    Quantity: {row[5]}, Completed: {row[6]}, Deadline: {row[7]}")
            
            print("\n👷 ASSIGNED SEWERS:")
            print("-" * 30)
            result = conn.execute(text("SELECT id, order_id, sewer_id FROM assigned_sewers ORDER BY id"))
            for row in result:
                print(f"  ID: {row[0]}, Order: {row[1]}, Sewer: {row[2]}")
            
            print("\n🔍 INSPECTED ITEMS:")
            print("-" * 30)
            result = conn.execute(text("SELECT COUNT(*) FROM inspected_items"))
            count = result.fetchone()[0]
            print(f"  Total inspected items: {count}")
            
            if count > 0:
                result = conn.execute(text("SELECT id, serial_number, order_id, sewer_id, status FROM inspected_items ORDER BY id LIMIT 5"))
                for row in result:
                    print(f"  ID: {row[0]}, Serial: {row[1]}, Order: {row[2]}, Sewer: {row[3]}, Status: {row[4]}")
            
            print("\n🚢 SHIPPING DETAILS:")
            print("-" * 30)
            result = conn.execute(text("SELECT COUNT(*) FROM shipping_details"))
            count = result.fetchone()[0]
            print(f"  Total shipping records: {count}")
            
            if count > 0:
                result = conn.execute(text("SELECT id, order_id, tracking_number, shipping_method FROM shipping_details ORDER BY id LIMIT 5"))
                for row in result:
                    print(f"  ID: {row[0]}, Order: {row[1]}, Tracking: {row[2]}, Method: {row[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    main()