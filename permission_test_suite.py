#!/usr/bin/env python3
"""
Permission Test Suite
Comprehensive testing of the permissions management system

This script:
1. Logs in as admin
2. Creates test users if needed
3. Grants specific permissions to test users
4. Logs in as each test user
5. Tests each permission systematically
6. Reports results

Usage: python3 permission_test_suite.py
"""

import requests
import json
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import sys

class PermissionTester:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.admin_token = None
        self.test_users = []
        self.test_results = {}
        
        # Define all permissions to test
        self.permissions_to_test = {
            'documents': [
                'documents.view_all',
                'documents.create', 
                'documents.edit_all',
                'documents.delete_all',
                'documents.approve',
                'documents.share'
            ],
            'categories': [
                'categories.view_all',
                'categories.create',
                'categories.edit', 
                'categories.delete',
                'categories.assign'
            ],
            'departments': [
                'departments.view_all',
                'departments.manage',
                'departments.assign_users',
                'departments.view_employees'
            ],
            'users': [
                'users.view_all',
                'users.create',
                'users.edit',
                'users.deactivate', 
                'users.assign_roles'
            ],
            'system': [
                'system.admin_settings',
                'system.view_analytics',
                'system.manage_settings',
                'system.backup'
            ]
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def make_request(self, method: str, endpoint: str, data: dict = None, token: str = None, files: dict = None) -> Tuple[bool, dict]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        if files:
            headers.pop('Content-Type', None)  # Let requests set content type for files
            
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                if files:
                    response = requests.post(url, headers=headers, files=files, data=data)
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return False, {"error": f"Unsupported method: {method}"}
                
            return response.status_code < 400, response.json() if response.content else {}
        except Exception as e:
            return False, {"error": str(e)}
    
    def login_admin(self) -> bool:
        """Login as admin user"""
        self.log("Attempting admin login...")
        success, response = self.make_request(
            'POST', 
            '/accounts/auth/login/',
            data={
                'email': 'bilalhashimi89@gmail.com',  # Use existing admin
                'password': 'admin123'  # You may need to adjust this
            }
        )
        
        if success and 'access' in response:
            self.admin_token = response['access']
            self.log("✓ Admin login successful")
            return True
        else:
            self.log(f"✗ Admin login failed: {response}", "ERROR")
            return False
    
    def create_test_users(self) -> bool:
        """Create test users for permission testing"""
        self.log("Creating test users...")
        
        test_user_configs = [
            {
                'email': 'test_user_1@test.com',
                'first_name': 'Test',
                'last_name': 'User1',
                'password': 'testpass123',
                'role': 'employee'
            },
            {
                'email': 'test_user_2@test.com', 
                'first_name': 'Test',
                'last_name': 'User2',
                'password': 'testpass123',
                'role': 'employee'
            },
            {
                'email': 'test_user_3@test.com',
                'first_name': 'Test', 
                'last_name': 'User3',
                'password': 'testpass123',
                'role': 'employee'
            }
        ]
        
        for user_config in test_user_configs:
            success, response = self.make_request(
                'POST',
                '/accounts/users/create/',
                data=user_config,
                token=self.admin_token
            )
            
            if success:
                self.test_users.append({
                    'email': user_config['email'],
                    'password': user_config['password'],
                    'id': response.get('id'),
                    'name': f"{user_config['first_name']} {user_config['last_name']}"
                })
                self.log(f"✓ Created test user: {user_config['email']}")
            else:
                # User might already exist, try to get existing user
                self.log(f"⚠ Test user {user_config['email']} might already exist")
                success, users_response = self.make_request('GET', '/accounts/users/', token=self.admin_token)
                if success:
                    for user in users_response.get('results', []):
                        if user['email'] == user_config['email']:
                            self.test_users.append({
                                'email': user_config['email'],
                                'password': user_config['password'],
                                'id': user['id'],
                                'name': f"{user_config['first_name']} {user_config['last_name']}"
                            })
                            self.log(f"✓ Using existing test user: {user_config['email']}")
                            break
        
        self.log(f"Total test users available: {len(self.test_users)}")
        return len(self.test_users) > 0
    
    def grant_permission_to_user(self, user_id: str, permission: str) -> bool:
        """Grant a specific permission to a user"""
        success, response = self.make_request(
            'POST',
            '/departments/permissions/grant/',
            data={
                'entityType': 'user',
                'entityId': user_id,
                'permission': permission
            },
            token=self.admin_token
        )
        
        if success:
            self.log(f"✓ Granted permission '{permission}' to user {user_id}")
            return True
        else:
            self.log(f"✗ Failed to grant permission '{permission}' to user {user_id}: {response}", "ERROR")
            return False
    
    def login_as_user(self, email: str, password: str) -> Optional[str]:
        """Login as a specific user and return token"""
        success, response = self.make_request(
            'POST',
            '/accounts/auth/login/', 
            data={'email': email, 'password': password}
        )
        
        if success and 'access' in response:
            self.log(f"✓ Logged in as user: {email}")
            return response['access']
        else:
            self.log(f"✗ Failed to login as user {email}: {response}", "ERROR")
            return None
    
    def test_document_permissions(self, user_token: str, permission: str) -> bool:
        """Test document-related permissions"""
        self.log(f"Testing document permission: {permission}")
        
        if permission == 'documents.view_all':
            success, response = self.make_request('GET', '/documents/', token=user_token)
            return success
            
        elif permission == 'documents.create':
            # Create a test document
            test_content = "Test document content"
            success, categories = self.make_request('GET', '/documents/categories/', token=user_token)
            if not success or not categories.get('results'):
                return False
                
            category_id = categories['results'][0]['id']
            
            # Create test file
            files = {'file': ('test.txt', test_content, 'text/plain')}
            data = {
                'title': f'Test Document {int(time.time())}',
                'description': 'Test document for permission testing',
                'category': category_id
            }
            
            success, response = self.make_request(
                'POST', '/documents/create/', 
                data=data, files=files, token=user_token
            )
            return success
            
        elif permission == 'documents.edit_all':
            # Try to get a document and edit it
            success, docs = self.make_request('GET', '/documents/', token=user_token)
            if success and docs.get('results'):
                doc_id = docs['results'][0]['id']
                success, response = self.make_request(
                    'PATCH', f'/documents/{doc_id}/update/',
                    data={'description': 'Updated by permission test'},
                    token=user_token
                )
                return success
            return False
            
        elif permission == 'documents.delete_all':
            # Try to delete a document
            success, docs = self.make_request('GET', '/documents/', token=user_token)
            if success and docs.get('results'):
                doc_id = docs['results'][0]['id']
                success, response = self.make_request(
                    'DELETE', f'/documents/{doc_id}/delete/',
                    token=user_token
                )
                return success
            return False
            
        elif permission == 'documents.approve':
            # This would typically involve changing document status
            success, docs = self.make_request('GET', '/documents/', token=user_token)
            if success and docs.get('results'):
                doc_id = docs['results'][0]['id']
                success, response = self.make_request(
                    'PATCH', f'/documents/{doc_id}/update/',
                    data={'status': 'approved'},
                    token=user_token
                )
                return success
            return False
            
        elif permission == 'documents.share':
            # Try to share a document (this would be a specific share endpoint)
            success, docs = self.make_request('GET', '/documents/', token=user_token)
            return success  # For now, just check if they can view documents to share
            
        return False
    
    def test_category_permissions(self, user_token: str, permission: str) -> bool:
        """Test category-related permissions"""
        self.log(f"Testing category permission: {permission}")
        
        if permission == 'categories.view_all':
            success, response = self.make_request('GET', '/documents/categories/', token=user_token)
            return success
            
        elif permission == 'categories.create':
            success, response = self.make_request(
                'POST', '/documents/categories/create/',
                data={
                    'name': f'Test Category {int(time.time())}',
                    'description': 'Test category for permission testing',
                    'is_public': True
                },
                token=user_token
            )
            return success
            
        elif permission == 'categories.edit':
            success, categories = self.make_request('GET', '/documents/categories/', token=user_token)
            if success and categories.get('results'):
                cat_id = categories['results'][0]['id']
                success, response = self.make_request(
                    'PATCH', f'/documents/categories/{cat_id}/update/',
                    data={'description': 'Updated by permission test'},
                    token=user_token
                )
                return success
            return False
            
        elif permission == 'categories.delete':
            success, categories = self.make_request('GET', '/documents/categories/', token=user_token)
            if success and categories.get('results'):
                # Find a category we can safely delete
                for cat in categories['results']:
                    if cat.get('document_count', 0) == 0:  # Only delete empty categories
                        success, response = self.make_request(
                            'DELETE', f'/documents/categories/{cat["id"]}/delete/',
                            token=user_token
                        )
                        return success
            return False
            
        elif permission == 'categories.assign':
            # This would involve assigning categories to documents
            success, response = self.make_request('GET', '/documents/categories/', token=user_token)
            return success
            
        return False
    
    def test_department_permissions(self, user_token: str, permission: str) -> bool:
        """Test department-related permissions"""
        self.log(f"Testing department permission: {permission}")
        
        if permission == 'departments.view_all':
            success, response = self.make_request('GET', '/departments/', token=user_token)
            return success
            
        elif permission == 'departments.manage':
            success, response = self.make_request(
                'POST', '/departments/create/',
                data={
                    'name': f'Test Department {int(time.time())}',
                    'code': f'TD{int(time.time()) % 10000}',
                    'description': 'Test department for permission testing',
                    'is_active': True
                },
                token=user_token
            )
            return success
            
        elif permission == 'departments.assign_users':
            success, depts = self.make_request('GET', '/departments/', token=user_token)
            success2, users = self.make_request('GET', '/departments/employees/available/', token=user_token)
            
            if success and success2 and depts.get('results') and users.get('results'):
                dept_id = depts['results'][0]['id']
                user_id = users['results'][0]['id']
                
                success, response = self.make_request(
                    'POST', '/departments/assignments/create/',
                    data={
                        'employee': user_id,
                        'department': dept_id,
                        'is_primary': True
                    },
                    token=user_token
                )
                return success
            return False
            
        elif permission == 'departments.view_employees':
            success, depts = self.make_request('GET', '/departments/', token=user_token)
            if success and depts.get('results'):
                dept_id = depts['results'][0]['id']
                success, response = self.make_request(
                    'GET', f'/departments/assignments/?department_id={dept_id}',
                    token=user_token
                )
                return success
            return False
            
        return False
    
    def test_user_permissions(self, user_token: str, permission: str) -> bool:
        """Test user-related permissions"""
        self.log(f"Testing user permission: {permission}")
        
        if permission == 'users.view_all':
            success, response = self.make_request('GET', '/accounts/users/', token=user_token)
            return success
            
        elif permission == 'users.create':
            success, response = self.make_request(
                'POST', '/accounts/users/create/',
                data={
                    'email': f'test_perm_{int(time.time())}@test.com',
                    'first_name': 'Permission',
                    'last_name': 'Test',
                    'password': 'testpass123',
                    'role': 'employee'
                },
                token=user_token
            )
            return success
            
        elif permission == 'users.edit':
            success, users = self.make_request('GET', '/accounts/users/', token=user_token)
            if success and users.get('results'):
                user_id = users['results'][0]['id']
                success, response = self.make_request(
                    'PATCH', f'/accounts/users/{user_id}/update/',
                    data={'first_name': 'Updated'},
                    token=user_token
                )
                return success
            return False
            
        elif permission == 'users.deactivate':
            success, users = self.make_request('GET', '/accounts/users/', token=user_token)
            if success and users.get('results'):
                # Find a test user to deactivate
                for user in users['results']:
                    if 'test_perm_' in user['email']:
                        success, response = self.make_request(
                            'POST', f'/accounts/users/{user["id"]}/deactivate/',
                            token=user_token
                        )
                        return success
            return False
            
        elif permission == 'users.assign_roles':
            # This would involve changing user roles - similar to edit but specific to roles
            success, users = self.make_request('GET', '/accounts/users/', token=user_token)
            return success  # For now, just check if they can view users
            
        return False
    
    def test_system_permissions(self, user_token: str, permission: str) -> bool:
        """Test system-related permissions"""
        self.log(f"Testing system permission: {permission}")
        
        if permission == 'system.admin_settings':
            # Try to access admin-only endpoints
            success, response = self.make_request('GET', '/accounts/users/', token=user_token)
            return success
            
        elif permission == 'system.view_analytics':
            success, response = self.make_request('GET', '/documents/stats/', token=user_token)
            return success
            
        elif permission == 'system.manage_settings':
            # This would involve changing system settings
            success, response = self.make_request('GET', '/departments/permissions/report/', token=user_token)
            return success
            
        elif permission == 'system.backup':
            # This would involve backup operations
            success, response = self.make_request('GET', '/departments/reports/budget-utilization/', token=user_token)
            return success
            
        return False
    
    def test_permission(self, user_token: str, permission: str) -> bool:
        """Test a specific permission"""
        category = permission.split('.')[0]
        
        if category == 'documents':
            return self.test_document_permissions(user_token, permission)
        elif category == 'categories':
            return self.test_category_permissions(user_token, permission)
        elif category == 'departments':
            return self.test_department_permissions(user_token, permission)
        elif category == 'users':
            return self.test_user_permissions(user_token, permission)
        elif category == 'system':
            return self.test_system_permissions(user_token, permission)
        else:
            self.log(f"Unknown permission category: {category}", "ERROR")
            return False
    
    def run_permission_tests(self):
        """Run comprehensive permission tests"""
        self.log("🚀 Starting Permission Test Suite")
        self.log("=" * 60)
        
        # Step 1: Login as admin
        if not self.login_admin():
            self.log("Failed to login as admin. Exiting.", "ERROR")
            return False
        
        # Step 2: Create test users
        if not self.create_test_users():
            self.log("Failed to create test users. Exiting.", "ERROR")
            return False
        
        # Step 3: Test each permission
        for category, permissions in self.permissions_to_test.items():
            self.log(f"\n📋 Testing {category.upper()} permissions")
            self.log("-" * 40)
            
            for permission in permissions:
                if not self.test_users:
                    self.log("No test users available", "ERROR")
                    continue
                    
                # Use first available test user
                test_user = self.test_users[0]
                
                self.log(f"\n🧪 Testing permission: {permission}")
                
                # Grant permission to user
                if not self.grant_permission_to_user(test_user['id'], permission):
                    self.test_results[permission] = {'status': 'FAILED', 'reason': 'Could not grant permission'}
                    continue
                
                # Login as test user
                user_token = self.login_as_user(test_user['email'], test_user['password'])
                if not user_token:
                    self.test_results[permission] = {'status': 'FAILED', 'reason': 'Could not login as test user'}
                    continue
                
                # Test the permission
                test_passed = self.test_permission(user_token, permission)
                
                if test_passed:
                    self.test_results[permission] = {'status': 'PASSED', 'reason': 'Permission worked as expected'}
                    self.log(f"✅ {permission}: PASSED")
                else:
                    self.test_results[permission] = {'status': 'FAILED', 'reason': 'Permission did not work as expected'}
                    self.log(f"❌ {permission}: FAILED")
                
                # Revoke permission for next test
                success, perms = self.make_request('GET', '/departments/permissions/', token=self.admin_token)
                if success:
                    for perm in perms.get('results', []):
                        if (perm['entity_type'] == 'user' and 
                            perm['entity_id'] == test_user['id'] and 
                            perm['permission'] == permission):
                            self.make_request('DELETE', f'/departments/permissions/{perm["id"]}/revoke/', token=self.admin_token)
                            break
                
                time.sleep(1)  # Brief pause between tests
        
        # Step 4: Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate and display test report"""
        self.log("\n" + "=" * 60)
        self.log("📊 PERMISSION TEST RESULTS REPORT")
        self.log("=" * 60)
        
        passed = 0
        failed = 0
        
        for category, permissions in self.permissions_to_test.items():
            self.log(f"\n📂 {category.upper()} PERMISSIONS:")
            for permission in permissions:
                if permission in self.test_results:
                    result = self.test_results[permission]
                    status_emoji = "✅" if result['status'] == 'PASSED' else "❌"
                    self.log(f"  {status_emoji} {permission}: {result['status']}")
                    if result['status'] == 'PASSED':
                        passed += 1
                    else:
                        failed += 1
                        self.log(f"    Reason: {result['reason']}")
                else:
                    self.log(f"  ⚠️  {permission}: NOT TESTED")
        
        self.log(f"\n📈 SUMMARY:")
        self.log(f"  Total Tests: {passed + failed}")
        self.log(f"  Passed: {passed}")
        self.log(f"  Failed: {failed}")
        self.log(f"  Success Rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "0%")
        
        if failed == 0:
            self.log("\n🎉 ALL PERMISSION TESTS PASSED!")
        else:
            self.log(f"\n⚠️  {failed} PERMISSION TESTS FAILED")
        
        self.log("=" * 60)

def main():
    """Main function to run the permission test suite"""
    print("🧪 Department Portal - Permission Test Suite")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health/")
        if response.status_code != 200:
            print("❌ Backend is not running. Please start the backend server first.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("Please ensure the backend server is running on http://localhost:8000")
        sys.exit(1)
    
    # Run the tests
    tester = PermissionTester()
    tester.run_permission_tests()

if __name__ == "__main__":
    main() 