#!/usr/bin/env python3
"""
Test script for Supabase authentication endpoints
Run this to verify the new auth endpoints are working
"""

import requests
import json
import uuid

# Configuration
BASE_URL = "https://stitchguard-db-production.up.railway.app/api/v1"

def test_auth_endpoints():
    print("🧪 Testing StitchGuard Authentication Endpoints")
    print("=" * 50)
    
    # Test 1: Create a new user via auth-sync
    print("\n1. Testing POST /users/auth-sync (create new user)")
    test_auth_id = str(uuid.uuid4())
    test_user_data = {
        "auth_id": test_auth_id,
        "email": "test-auth@example.com",
        "name": "Test Auth User",
        "role": "sewer"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/auth-sync", json=test_user_data)
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            user_data = response.json()
            print(f"✅ User created: {user_data['name']} (ID: {user_data['id']})")
            created_user_id = user_data['id']
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 2: Get user by auth_id
    print(f"\n2. Testing GET /users/by-auth-id/{test_auth_id}")
    try:
        response = requests.get(f"{BASE_URL}/users/by-auth-id/{test_auth_id}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ User found: {user_data['name']} (auth_id: {user_data['auth_id']})")
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Update existing user via auth-sync
    print(f"\n3. Testing POST /users/auth-sync (update existing user)")
    updated_user_data = {
        "auth_id": test_auth_id,
        "email": "test-auth-updated@example.com",
        "name": "Test Auth User Updated",
        "role": "supervisor"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/auth-sync", json=updated_user_data)
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            user_data = response.json()
            print(f"✅ User updated: {user_data['name']} (Role: {user_data['role']})")
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 4: Test with existing user email (migration scenario)
    print(f"\n4. Testing email migration scenario")
    migration_user_data = {
        "auth_id": str(uuid.uuid4()),
        "email": "yahya@builtmfgco.com",  # Existing user email
        "name": "Yahya Rahhawi (Authenticated)",
        "role": "supervisor"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/users/auth-sync", json=migration_user_data)
        print(f"Status: {response.status_code}")
        if response.status_code in [200, 201]:
            user_data = response.json()
            print(f"✅ Existing user migrated: {user_data['name']} (auth_id: {user_data['auth_id']})")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n🎉 Authentication endpoints test completed!")
    return True

def test_regular_endpoints():
    print("\n📋 Testing regular user endpoints")
    try:
        response = requests.get(f"{BASE_URL}/users/")
        print(f"GET /users/ - Status: {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Found {len(users)} users")
            for user in users[:3]:  # Show first 3 users
                auth_status = "✅ Has auth_id" if user.get('auth_id') else "❌ No auth_id"
                print(f"  - {user['name']} ({user['email']}) - {auth_status}")
        else:
            print(f"❌ Failed: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Test regular endpoints first
    test_regular_endpoints()
    
    # Test auth endpoints
    test_auth_endpoints() 