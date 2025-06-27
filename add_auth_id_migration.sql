-- Migration: Add auth_id column to users table
-- Run this script on your Railway PostgreSQL database

-- Add auth_id column to users table
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS auth_id VARCHAR(255) UNIQUE;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_users_auth_id ON users(auth_id);

-- Update the updated_at timestamp for existing users (optional)
-- This helps track when the migration was applied
UPDATE users 
SET updated_at = NOW() 
WHERE auth_id IS NULL;

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Show current users (should now include auth_id column)
SELECT id, name, email, role, auth_id, created_at, updated_at 
FROM users 
ORDER BY id; 