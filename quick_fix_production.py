#!/usr/bin/env python3
"""
Quick fix for production database counter issue
Uses existing API endpoints to reset order progress
"""

import requests
import json

# Production API base URL  
API_BASE = "https://stitchguard-db-production.up.railway.app/api/v1"

def reset_order_progress(order_id: int, new_completed: int = 0):
    """Reset order progress using existing progress endpoint"""
    url = f"{API_BASE}/orders/{order_id}/progress"
    
    payload = {"completed": new_completed}
    
    try:
        response = requests.put(url, json=payload)
        response.raise_for_status()
        
        order_data = response.json()
        print(f"✅ Successfully reset order {order_id}")
        print(f"   Order: {order_data['name']}")
        print(f"   Completed: {order_data['completed']}/{order_data['quantity']}")
        return order_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to reset order {order_id}: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None

def get_order_info(order_id: int):
    """Get current order information"""
    url = f"{API_BASE}/orders/{order_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        order_data = response.json()
        print(f"📦 Order {order_id}: {order_data['name']}")
        print(f"   Completed: {order_data['completed']}/{order_data['quantity']}")
        return order_data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get order {order_id}: {e}")
        return None

def count_inspection_items_by_status(order_id: int):
    """Count inspection items by status for debugging"""
    url = f"{API_BASE}/inspection/items?order_id={order_id}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        items = response.json()
        
        status_counts = {}
        for item in items:
            status = item['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"📊 Inspection items for order {order_id}:")
        print(f"   Total items: {len(items)}")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        passed_and_overridden = status_counts.get('PASSED', 0) + status_counts.get('OVERRIDDEN', 0)
        print(f"   PASSED + OVERRIDDEN: {passed_and_overridden} ← This is what's causing the issue!")
        
        return status_counts
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to count items: {e}")
        return {}

def main():
    print("🔧 StitchGuard Production Quick Fix")
    print("=" * 50)
    
    order_id = 1
    
    # Show current state
    print("\n1. Current order state:")
    order_info = get_order_info(order_id)
    
    print("\n2. Current inspection items breakdown:")
    item_counts = count_inspection_items_by_status(order_id)
    
    if order_info and order_info['completed'] > 0:
        print(f"\n⚠️  Order shows {order_info['completed']} completed, but this is wrong due to old test data")
        print("\n3. Resetting order progress to 0...")
        
        reset_result = reset_order_progress(order_id, new_completed=0)
        
        if reset_result:
            print(f"\n✅ Quick fix complete!")
            print(f"   Order progress reset to 0/{reset_result['quantity']}")
            print(f"   Override should now work properly")
            print(f"\n⚠️  Note: Old inspection records still exist in database")
            print(f"   But the order counter is now correct for testing")
        
    else:
        print(f"\n✅ Order progress already looks correct at {order_info['completed'] if order_info else 'unknown'}")

if __name__ == "__main__":
    main() 