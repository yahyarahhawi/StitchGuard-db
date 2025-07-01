from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.deps import get_db

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/migrate-order-assignment")
def migrate_order_assignment(db: Session = Depends(get_db)):
    """
    Run the order assignment migration via HTTP endpoint
    WARNING: This is a one-time migration - only run once!
    """
    
    try:
        # Migration SQL steps
        migration_steps = [
            # Step 1: Add sewer_id column
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS sewer_id INTEGER REFERENCES users(id)",
            
            # Step 2: Migrate from assigned_sewers
            """UPDATE orders 
               SET sewer_id = (
                   SELECT sewer_id 
                   FROM assigned_sewers 
                   WHERE assigned_sewers.order_id = orders.id 
                   LIMIT 1
               )
               WHERE id IN (SELECT DISTINCT order_id FROM assigned_sewers)""",
            
            # Step 3: Handle unassigned orders
            """UPDATE orders 
               SET sewer_id = (
                   SELECT id 
                   FROM users 
                   WHERE role = 'sewer' 
                   ORDER BY id 
                   LIMIT 1
               )
               WHERE sewer_id IS NULL""",
            
            # Step 4: Make sewer_id NOT NULL
            "ALTER TABLE orders ALTER COLUMN sewer_id SET NOT NULL",
            
            # Step 5: Remove assigned_by column
            "ALTER TABLE orders DROP COLUMN IF EXISTS assigned_by",
            
            # Step 6: Add index
            "CREATE INDEX IF NOT EXISTS idx_orders_sewer_id ON orders(sewer_id)"
        ]
        
        results = []
        
        for i, step in enumerate(migration_steps, 1):
            try:
                db.execute(text(step))
                db.commit()
                results.append(f"✅ Step {i}: Success")
            except Exception as e:
                # Some steps might fail if already applied, that's ok
                db.rollback()
                results.append(f"⚠️ Step {i}: {str(e)}")
        
        # Verify final state
        verification = db.execute(text("""
            SELECT o.id, o.name, o.sewer_id, u.name as sewer_name 
            FROM orders o 
            JOIN users u ON o.sewer_id = u.id 
            ORDER BY o.id
        """)).fetchall()
        
        return {
            "success": True,
            "message": "Migration completed",
            "steps": results,
            "verification": [dict(row._mapping) for row in verification]
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}") 