-- Migration: Update existing shipping_details table
-- Date: 2024-12-30

-- Add missing fields for shipping workflow
ALTER TABLE shipping_details 
ADD COLUMN IF NOT EXISTS notes TEXT,
ADD COLUMN IF NOT EXISTS shipped_at TIMESTAMP;

-- Update shipping_method to be NOT NULL (carrier is required)
-- First set default for existing NULL values
UPDATE shipping_details SET shipping_method = 'Unknown' WHERE shipping_method IS NULL;
ALTER TABLE shipping_details ALTER COLUMN shipping_method SET NOT NULL;

-- Update address to be NOT NULL (shipping address is required)
-- First set default for existing NULL values
UPDATE shipping_details SET address = 'Unknown' WHERE address IS NULL;
ALTER TABLE shipping_details ALTER COLUMN address SET NOT NULL;

-- Update tracking_number to be NOT NULL
UPDATE shipping_details SET tracking_number = 'Unknown' WHERE tracking_number IS NULL;
ALTER TABLE shipping_details ALTER COLUMN tracking_number SET NOT NULL;

-- Add index for tracking number lookups
CREATE INDEX IF NOT EXISTS idx_shipping_details_tracking ON shipping_details(tracking_number);

-- Add index for shipped_at lookups
CREATE INDEX IF NOT EXISTS idx_shipping_details_shipped_at ON shipping_details(shipped_at); 