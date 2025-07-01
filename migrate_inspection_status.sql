-- Migration: Change inspected_items.passed from boolean to status enum
-- Created: 2025-01-07
-- Purpose: Support PASSED, FAILED, and OVERRIDDEN inspection statuses

BEGIN;

-- Step 1: Add new status column
ALTER TABLE inspected_items 
ADD COLUMN status VARCHAR(20) DEFAULT 'PASSED';

-- Step 2: Populate status based on existing passed column
UPDATE inspected_items 
SET status = CASE 
    WHEN passed = true THEN 'PASSED'
    WHEN passed = false THEN 'FAILED'
    ELSE 'PASSED'
END;

-- Step 3: Make status NOT NULL
ALTER TABLE inspected_items 
ALTER COLUMN status SET NOT NULL;

-- Step 4: Add check constraint for valid values
ALTER TABLE inspected_items 
ADD CONSTRAINT inspected_items_status_check 
CHECK (status IN ('PASSED', 'FAILED', 'OVERRIDDEN'));

-- Step 5: Drop old passed column
ALTER TABLE inspected_items 
DROP COLUMN passed;

COMMIT; 