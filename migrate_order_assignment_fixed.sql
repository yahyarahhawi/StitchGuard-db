-- Migration: Restructure Order Assignment System (FIXED)
-- This migration handles orders without sewer assignments

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

-- Step 3: Handle orders WITHOUT sewer assignments
-- Assign them to the first available sewer
UPDATE orders 
SET sewer_id = (
    SELECT id 
    FROM users 
    WHERE role = 'sewer' 
    ORDER BY id 
    LIMIT 1
)
WHERE sewer_id IS NULL;

-- Step 4: Make sewer_id NOT NULL (after data migration and assignment)
ALTER TABLE orders 
ALTER COLUMN sewer_id SET NOT NULL;

-- Step 5: Remove the redundant assigned_by column
ALTER TABLE orders 
DROP COLUMN assigned_by;

-- Step 6: Add index for performance
CREATE INDEX idx_orders_sewer_id ON orders(sewer_id);

COMMIT;

-- Show final results
SELECT o.id, o.name, o.sewer_id, u.name as sewer_name 
FROM orders o 
JOIN users u ON o.sewer_id = u.id
ORDER BY o.id; 