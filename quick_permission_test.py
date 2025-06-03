#!/usr/bin/env python3
"""
Quick Permission Test
Simplified version to test permissions management system

Usage: python3 quick_permission_test.py
"""

import requests
import json
import time

class QuickPermissionTest:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.admin_token = None
        
    def login_admin(self, email="bilalhashimi89@gmail.com", password="admin123"):
        """Login as admin - you can modify credentials here"""
        print(f"🔐 Attempting admin login with {email}...")
        
        response = requests.post(f"{self.base_url}/accounts/auth/login/", json={
            'email': email,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data['access']
            print("✅ Admin login successful!")
            return True
        else:
            print(f"❌ Admin login failed: {response.text}")
            print("💡 Try these common passwords: 'admin123', 'password', 'admin', or check your admin credentials")
            return False
    
    def create_test_user(self):
        """Create a test user with known credentials"""
        print("👤 Creating test user...")
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        test_user_data = {
            'email': 'permission_test_user@test.com',
            'username': 'permission_test_user',
            'first_name': 'Permission',
            'last_name': 'Test',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'role': 'employee',
            'is_active': True
        }
        
        response = requests.post(f"{self.base_url}/accounts/users/create/", json=test_user_data, headers=headers)
        
        print(f"User creation response status: {response.status_code}")
        print(f"User creation response: {response.text}")
        
        if response.status_code in [200, 201]:
            user_data = response.json()
            print(f"✅ Created test user: {test_user_data['email']}")
            return {
                'id': user_data.get('id'),
                'email': test_user_data['email'],
                'password': test_user_data['password']
            }
        else:
            print(f"⚠️  Could not create test user: {response.text}")
            # User might already exist, try to get existing user
            users_response = requests.get(f"{self.base_url}/accounts/users/", headers=headers)
            if users_response.status_code == 200:
                users = users_response.json().get('results', [])
                for user in users:
                    if user['email'] == test_user_data['email']:
                        print(f"✅ Found existing test user: {test_user_data['email']}")
                        return {
                            'id': user['id'],
                            'email': test_user_data['email'],
                            'password': test_user_data['password']
                        }
        
        return None
    
    def get_test_user(self):
        """Get an existing employee user for testing"""
        # First try to create a test user with known password
        test_user = self.create_test_user()
        if test_user:
            return test_user
            
        # Fallback to existing user method
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        response = requests.get(f"{self.base_url}/accounts/users/", headers=headers)
        
        if response.status_code == 200:
            users = response.json().get('results', [])
            # Find an employee (non-admin) user
            for user in users:
                if user['role'] == 'employee':
                    print(f"📋 Found existing user: {user['email']} ({user['role']})")
                    return {
                        'id': user['id'],
                        'email': user['email'],
                        'password': None  # Unknown password
                    }
        
        print("⚠️  No employee users found. You may need to create one first.")
        return None
    
    def grant_permission(self, user_id, permission):
        """Grant a permission to a user"""
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        data = {
            'entityType': 'user',
            'entityId': user_id,
            'permission': permission
        }
        
        response = requests.post(f"{self.base_url}/departments/permissions/grant/", json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Granted permission: {permission}")
            return True
        else:
            print(f"❌ Failed to grant permission {permission}: {response.text}")
            return False
    
    def test_user_login(self, test_user):
        """Test logging in as a user with known or guessed password"""
        email = test_user['email']
        known_password = test_user.get('password')
        
        print(f"🔐 Testing login as {email}...")
        
        # If we have a known password, try it first
        if known_password:
            response = requests.post(f"{self.base_url}/accounts/auth/login/", json={
                'email': email,
                'password': known_password
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User login successful with known password")
                return data['access']
        
        # If no known password or known password failed, try common passwords
        common_passwords = ["password123", "admin123", "123456", "password", "user123", "testpass123"]
        
        for password in common_passwords:
            response = requests.post(f"{self.base_url}/accounts/auth/login/", json={
                'email': email,
                'password': password
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ User login successful with password: {password}")
                return data['access']
        
        print(f"❌ User login failed with all attempted passwords")
        print("💡 Available passwords tried:", ", ".join(common_passwords))
        return None
    
    def test_permission_functionality(self, user_token, permission):
        """Test if a permission actually works"""
        headers = {'Authorization': f'Bearer {user_token}'}
        
        print(f"🧪 Testing permission: {permission}")
        
        if permission == 'documents.view_all':
            response = requests.get(f"{self.base_url}/documents/", headers=headers)
            success = response.status_code == 200
            print(f"  📄 Documents access: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
        elif permission == 'documents.create':
            response = requests.get(f"{self.base_url}/documents/categories/", headers=headers)
            if response.status_code == 200:
                categories = response.json().get('results', [])
                if categories:
                    # Try to create a document
                    files = {'file': ('test.txt', 'Test content', 'text/plain')}
                    data = {
                        'title': f'Test Doc {int(time.time())}',
                        'description': 'Permission test document',
                        'category': categories[0]['id']
                    }
                    
                    # Remove Authorization from headers for file upload
                    response = requests.post(f"{self.base_url}/documents/create/", 
                                           files=files, data=data, headers=headers)
                    success = response.status_code in [200, 201]
                    print(f"  📄 Document creation: {'✅ SUCCESS' if success else '❌ FAILED'}")
                else:
                    print("  📄 Document creation: ❌ FAILED (No categories available)")
            else:
                print("  📄 Document creation: ❌ FAILED (Cannot access categories)")
                
        elif permission == 'users.view_all':
            response = requests.get(f"{self.base_url}/accounts/users/", headers=headers)
            success = response.status_code == 200
            print(f"  👥 Users access: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
        elif permission == 'departments.view_all':
            response = requests.get(f"{self.base_url}/departments/", headers=headers)
            success = response.status_code == 200
            print(f"  🏢 Departments access: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
        elif permission == 'categories.view_all':
            response = requests.get(f"{self.base_url}/documents/categories/", headers=headers)
            success = response.status_code == 200
            print(f"  📁 Categories access: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
        elif permission == 'system.admin_settings':
            # Test admin-only endpoint
            response = requests.get(f"{self.base_url}/departments/permissions/", headers=headers)
            success = response.status_code == 200
            print(f"  ⚙️  Admin settings access: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
        else:
            print(f"  ⚠️  Permission test not implemented for: {permission}")
    
    def revoke_permission(self, permission_name):
        """Revoke a permission by finding it in the list"""
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        response = requests.get(f"{self.base_url}/departments/permissions/", headers=headers)
        
        if response.status_code == 200:
            permissions = response.json().get('results', [])
            for perm in permissions:
                if perm['permission'] == permission_name:
                    delete_response = requests.delete(
                        f"{self.base_url}/departments/permissions/{perm['id']}/revoke/", 
                        headers=headers
                    )
                    if delete_response.status_code == 200:
                        print(f"🗑️  Revoked permission: {permission_name}")
                        return True
        
        print(f"⚠️  Could not revoke permission: {permission_name}")
        return False
    
    def run_quick_test(self):
        """Run a quick test of the permission system"""
        print("🚀 Department Portal - Quick Permission Test")
        print("=" * 50)
        
        # Step 1: Login as admin
        if not self.login_admin():
            print("\n💡 To fix admin login:")
            print("   1. Check if admin user exists")
            print("   2. Try different passwords: admin123, password, admin")
            print("   3. Or modify the credentials in this script")
            return
        
        # Step 2: Get a test user
        test_user = self.get_test_user()
        if not test_user:
            print("\n💡 To fix user issue:")
            print("   1. Create an employee user in the admin panel")
            print("   2. Or register a new user via the frontend")
            return
        
        # Step 3: Test different permissions
        permissions_to_test = [
            'documents.view_all',
            'documents.create', 
            'users.view_all',
            'departments.view_all',
            'categories.view_all',
            'system.admin_settings'
        ]
        
        for permission in permissions_to_test:
            print(f"\n📝 Testing Permission: {permission}")
            print("-" * 30)
            
            # Grant permission
            if self.grant_permission(test_user['id'], permission):
                
                # Login as test user
                user_token = self.test_user_login(test_user)
                if user_token:
                    
                    # Test the permission
                    self.test_permission_functionality(user_token, permission)
                    
                    # Revoke permission for next test
                    self.revoke_permission(permission)
                else:
                    print("  ❌ Could not login as test user")
            else:
                print("  ❌ Could not grant permission")
            
            time.sleep(1)  # Brief pause between tests
        
        print("\n🎉 Quick permission test completed!")
        print("=" * 50)

def main():
    """Main function"""
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health/")
        if response.status_code != 200:
            print("❌ Backend is not running. Please start it first:")
            print("   docker-compose up backend")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure Docker containers are running")
        return
    
    # Run the test
    tester = QuickPermissionTest()
    tester.run_quick_test()

if __name__ == "__main__":
    main() 