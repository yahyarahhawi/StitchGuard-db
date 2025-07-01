-- Rollback partial migration
-- This removes the sewer_id column that was added but not properly populated

BEGIN;

-- Remove the sewer_id column (this will also remove the foreign key constraint)
ALTER TABLE orders DROP COLUMN IF EXISTS sewer_id;

-- Drop the index if it exists
DROP INDEX IF EXISTS idx_orders_sewer_id;

COMMIT;

-- Verify rollback
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'orders' AND table_schema = 'public'
ORDER BY ordinal_position; 