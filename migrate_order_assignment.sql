-- Migration: Restructure Order Assignment System
-- This migration simplifies order assignment by moving from a many-to-many
-- relationship to a direct sewer_id foreign key in the orders table

BEGIN;

-- Step 1: Add sewer_id column to orders table
ALTER TABLE orders 
ADD COLUMN sewer_id INTEGER REFERENCES users(id);

-- Step 2: Migrate data from assigned_sewers to orders.sewer_id
-- For orders with multiple assigned sewers, we'll take the first one
UPDATE orders 
SET sewer_id = (
    SELECT sewer_id 
    FROM assigned_sewers 
    WHERE assigned_sewers.order_id = orders.id 
    LIMIT 1
)
WHERE id IN (SELECT DISTINCT order_id FROM assigned_sewers);

-- Step 3: Make sewer_id NOT NULL (after data migration)
ALTER TABLE orders 
ALTER COLUMN sewer_id SET NOT NULL;

-- Step 4: Remove the redundant assigned_by column
ALTER TABLE orders 
DROP COLUMN assigned_by;

-- Step 5: Add index for performance
CREATE INDEX idx_orders_sewer_id ON orders(sewer_id);

-- Step 6: Update User model relationships (we'll handle this in the model file)
-- The assigned_sewers table will remain for now but won't be used in new code

COMMIT;

-- Verification queries (run these after migration to verify)
-- SELECT o.id, o.name, o.sewer_id, u.name as sewer_name 
-- FROM orders o 
-- JOIN users u ON o.sewer_id = u.id;

-- SELECT COUNT(*) as total_orders FROM orders;
-- SELECT COUNT(*) as orders_with_sewer FROM orders WHERE sewer_id IS NOT NULL; 