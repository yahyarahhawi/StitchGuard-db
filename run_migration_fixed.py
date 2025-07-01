#!/usr/bin/env python3
"""
Run Fixed Order Assignment Migration
This script rolls back the partial migration and runs the fixed version
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def run_sql_file(engine, filepath, description):
    """Run a SQL file and return success status"""
    print(f"📄 Running {description}...")
    
    with open(filepath, 'r') as f:
        sql_content = f.read()
    
    with engine.connect() as conn:
        # Split into statements and execute
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
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
                
            try:
                result = conn.execute(text(statement))
                conn.commit()
                
                # If it's a SELECT statement, show results
                if statement.strip().upper().startswith('SELECT'):
                    rows = result.fetchall()
                    if rows:
                        print(f"  📊 Results:")
                        for row in rows:
                            print(f"    {row}")
                    
            except Exception as e:
                print(f"  ❌ Statement failed: {e}")
                conn.rollback()
                raise
    
    print(f"  ✅ {description} completed")
    return True

def main():
    print("🔧 Running Fixed Order Assignment Migration...")
    print("=" * 55)
    
    # Load environment variables
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not set in .env")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        
        # Step 1: Rollback partial migration
        rollback_file = Path(__file__).parent / "rollback_migration.sql"
        if rollback_file.exists():
            run_sql_file(engine, rollback_file, "rollback of partial migration")
        
        # Step 2: Run fixed migration
        migration_file = Path(__file__).parent / "migrate_order_assignment_fixed.sql"
        if not migration_file.exists():
            print(f"❌ Fixed migration file not found: {migration_file}")
            return False
            
        run_sql_file(engine, migration_file, "fixed order assignment migration")
        
        print("\n✅ Fixed migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 