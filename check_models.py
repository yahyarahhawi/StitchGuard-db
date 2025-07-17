import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cur = conn.cursor()

print("=== DETAILED MODEL INFORMATION ===")
cur.execute('SELECT * FROM models ORDER BY id;')
models = cur.fetchall()

if models:
    for row in models:
        print(f"\nModel ID: {row[0]}")
        print(f"  Name: {row[1]}")
        print(f"  Type: {row[2]}")
        print(f"  Version: {row[3]}")
        print(f"  Description: {row[4]}")
        print(f"  Platform: {row[5]}")
        print(f"  File URL: {row[6]}")
        print(f"  Created: {row[7]}")
        print(f"  Updated: {row[8]}")
else:
    print("No models found")

print("\n=== PRODUCT-MODEL RELATIONSHIPS ===")
cur.execute('''
    SELECT p.id, p.name, p.model_ids, 
           CASE WHEN p.model_ids IS NOT NULL THEN 
               (SELECT string_agg(m.name, ', ') 
                FROM models m 
                WHERE m.id = ANY(p.model_ids))
           ELSE 'No models'
           END as model_names
    FROM products p
    ORDER BY p.id;
''')

relationships = cur.fetchall()
if relationships:
    for row in relationships:
        print(f"\nProduct {row[0]}: {row[1]}")
        print(f"  Model IDs: {row[2]}")
        print(f"  Model Names: {row[3]}")
else:
    print("No product-model relationships found")

conn.close() 