#!/usr/bin/env python3
"""
Script to clean up old test inspection data from production database
Run this to fix the issue where override jumps to 13 completed items
"""

import requests
import json

# Production API base URL
API_BASE = "https://stitchguard-db-production.up.railway.app/api/v1"

def cleanup_order_test_data(order_id: int):
    """Clean up old test data for a specific order"""
    url = f"{API_BASE}/orders/{order_id}/cleanup-test-data"
    
    try:
        response = requests.delete(url)
        response.raise_for_status()
        
        order_data = response.json()
        print(f"✅ Successfully cleaned up order {order_id}")
        print(f"   Order: {order_data['name']}")
        print(f"   Completed: {order_data['completed']}/{order_data['quantity']}")
        return order_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to cleanup order {order_id}: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None

def list_inspection_items(order_id: int = None):
    """List current inspection items to see what's in the database"""
    url = f"{API_BASE}/inspection/items"
    if order_id:
        url += f"?order_id={order_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        items = response.json()
        print(f"📋 Current inspection items: {len(items)}")
        
        if items:
            print("   Recent items:")
            for item in items[-5:]:  # Show last 5 items
                print(f"   - ID: {item['id']}, Status: {item['status']}, Order: {item['order_id']}")
        
        return items
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to list items: {e}")
        return []

def main():
    print("🧹 StitchGuard Production Database Cleanup")
    print("=" * 50)
    
    # First, show current state
    print("\n1. Current inspection items:")
    items = list_inspection_items(order_id=1)
    
    if len(items) > 5:
        print(f"\n⚠️  Found {len(items)} inspection items for order 1 - this is likely causing the override issue")
        
        # Clean up the order
        print("\n2. Cleaning up old test data...")
        cleaned_order = cleanup_order_test_data(order_id=1)
        
        if cleaned_order:
            print("\n3. Verification - checking items after cleanup:")
            items_after = list_inspection_items(order_id=1)
            print(f"   Items after cleanup: {len(items_after)}")
            
            print(f"\n✅ Cleanup complete!")
            print(f"   Order 1 is now reset to 0/{cleaned_order['quantity']} completed")
            print(f"   Override should now work properly and advance to next item")
        else:
            print("\n❌ Cleanup failed - check the error messages above")
    else:
        print(f"\n✅ Order looks clean with only {len(items)} items")

if __name__ == "__main__":
    main() 