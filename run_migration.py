#!/usr/bin/env python3
"""
Run Order Assignment Migration
This script migrates the order assignment system from many-to-many to direct assignment
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def main():
    print("🔄 Running Order Assignment Migration...")
    print("=" * 50)
    
    # Load environment variables
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set in .env")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Read migration SQL
        migration_file = Path(__file__).parent / "migrate_order_assignment.sql"
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("📄 Migration SQL loaded")
        print("🚀 Executing migration...")
        
        # Execute migration
        with engine.connect() as conn:
            # Split the SQL into individual statements (excluding comments)
            statements = []
            current_statement = []
            
            for line in migration_sql.split('\n'):
                line = line.strip()
                if line and not line.startswith('--'):
                    current_statement.append(line)
                    if line.endswith(';'):
                        statements.append(' '.join(current_statement))
                        current_statement = []
            
            # Execute each statement
            for i, statement in enumerate(statements):
                if statement.strip().upper() in ['BEGIN;', 'COMMIT;']:
                    continue
                    
                print(f"  📝 Executing statement {i+1}...")
                try:
                    result = conn.execute(text(statement))
                    conn.commit()
                    print(f"  ✅ Statement {i+1} completed")
                except Exception as e:
                    print(f"  ❌ Statement {i+1} failed: {e}")
                    conn.rollback()
                    raise
        
        print("\n🔍 Running verification queries...")
        
        # Run verification queries
        with engine.connect() as conn:
            # Check total orders
            result = conn.execute(text("SELECT COUNT(*) as total_orders FROM orders"))
            total_orders = result.fetchone()[0]
            print(f"  📊 Total orders: {total_orders}")
            
            # Check orders with sewer assignments
            result = conn.execute(text("SELECT COUNT(*) as orders_with_sewer FROM orders WHERE sewer_id IS NOT NULL"))
            orders_with_sewer = result.fetchone()[0]
            print(f"  👷 Orders with sewer assigned: {orders_with_sewer}")
            
            # Show sample assignments
            result = conn.execute(text("""
                SELECT o.id, o.name, o.sewer_id, u.name as sewer_name 
                FROM orders o 
                JOIN users u ON o.sewer_id = u.id 
                LIMIT 5
            """))
            
            print("\n  📋 Sample order assignments:")
            for row in result:
                print(f"    Order {row[0]}: {row[1]} → Sewer: {row[3]} (ID: {row[2]})")
        
        print("\n✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 