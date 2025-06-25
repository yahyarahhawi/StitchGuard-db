-- Update product 1 (Sports Bra) to include model IDs
UPDATE products 
SET model_ids = ARRAY[1, 2] 
WHERE id = 1;

-- Verify the update
SELECT id, name, model_ids FROM products WHERE id = 1; 