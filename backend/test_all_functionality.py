#!/usr/bin/env python
"""
Comprehensive Backend API Test Suite
Tests all functionality including:
- Authentication
- User Management  
- Document Management
- Group Management
- Department Management
- Database Operations
"""

import requests
import json
import os
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
HEALTH_URL = "http://localhost:8000/health/"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        
        if passed:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append(f"{test_name}: {details}")
    
    def test_health_check(self):
        """Test server health endpoint"""
        try:
            response = requests.get(HEALTH_URL, timeout=5)
            self.log_test("Health Check", response.status_code == 200, 
                         f"Status: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        try:
            test_user = {
                "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                "password": "TestPassword123!",
                "password_confirm": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User",
                "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = self.session.post(f"{self.base_url}/accounts/auth/register/", 
                                       json=test_user)
            
            success = response.status_code == 201
            if success:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
            
            self.log_test("User Registration", success, 
                         f"Status: {response.status_code}, Response: {response.text[:200]}")
            return success
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False
    
    def test_user_login(self):
        """Test user login"""
        try:
            login_data = {
                "email": "admin@example.com",
                "password": "admin123"
            }
            
            response = self.session.post(f"{self.base_url}/accounts/auth/login/", 
                                       json=login_data)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                self.access_token = data.get('access')
                self.refresh_token = data.get('refresh')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
            
            self.log_test("User Login", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False
    
    def test_user_profile(self):
        """Test user profile retrieval"""
        try:
            response = self.session.get(f"{self.base_url}/accounts/profile/")
            success = response.status_code == 200
            
            self.log_test("User Profile", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("User Profile", False, str(e))
            return False
    
    def test_users_list(self):
        """Test users list endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/accounts/users/")
            success = response.status_code == 200
            
            self.log_test("Users List", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Users List", False, str(e))
            return False
    
    def test_departments_list(self):
        """Test departments list endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/departments/")
            success = response.status_code == 200
            
            self.log_test("Departments List", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Departments List", False, str(e))
            return False
    
    def test_groups_list(self):
        """Test groups list endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/accounts/groups/")
            success = response.status_code == 200
            
            self.log_test("Groups List", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Groups List", False, str(e))
            return False
    
    def test_group_creation(self):
        """Test group creation"""
        try:
            group_data = {
                "name": f"Test Group {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            response = self.session.post(f"{self.base_url}/accounts/groups/create/", 
                                       json=group_data)
            success = response.status_code == 201
            
            self.log_test("Group Creation", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Group Creation", False, str(e))
            return False
    
    def test_documents_list(self):
        """Test documents list endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/documents/")
            success = response.status_code == 200
            
            self.log_test("Documents List", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Documents List", False, str(e))
            return False
    
    def test_document_categories(self):
        """Test document categories endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/documents/categories/")
            success = response.status_code == 200
            
            self.log_test("Document Categories", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Document Categories", False, str(e))
            return False
    
    def test_document_search(self):
        """Test document search endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/documents/search/?q=test")
            success = response.status_code in [200, 503]  # 503 is acceptable if vector search is down
            
            self.log_test("Document Search", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Document Search", False, str(e))
            return False
    
    def test_document_stats(self):
        """Test document statistics endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/documents/stats/")
            success = response.status_code in [200, 503]  # 503 is acceptable if vector search is down
            
            self.log_test("Document Stats", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Document Stats", False, str(e))
            return False
    
    def test_ai_chat(self):
        """Test AI chat endpoint"""
        try:
            chat_data = {
                "question": "What documents are available?"
            }
            
            response = self.session.post(f"{self.base_url}/documents/chat/", 
                                       json=chat_data)
            success = response.status_code in [200, 503]  # 503 is acceptable if AI service is down
            
            self.log_test("AI Chat", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("AI Chat", False, str(e))
            return False
    
    def test_token_refresh(self):
        """Test token refresh endpoint"""
        try:
            if not self.refresh_token:
                self.log_test("Token Refresh", False, "No refresh token available")
                return False
            
            refresh_data = {
                "refresh": self.refresh_token
            }
            
            response = self.session.post(f"{self.base_url}/accounts/auth/refresh/", 
                                       json=refresh_data)
            success = response.status_code == 200
            
            self.log_test("Token Refresh", success, 
                         f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Token Refresh", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Backend API Tests")
        print("=" * 50)
        
        # Test basic connectivity
        if not self.test_health_check():
            print("❌ Server is not responding. Cannot continue tests.")
            return self.get_results()
        
        # Authentication tests
        print("\n📋 Authentication Tests:")
        self.test_user_registration()
        self.test_user_login()
        self.test_token_refresh()
        
        # User management tests
        print("\n👥 User Management Tests:")
        self.test_user_profile()
        self.test_users_list()
        
        # Group management tests
        print("\n🏷️ Group Management Tests:")
        self.test_groups_list()
        self.test_group_creation()
        
        # Department tests
        print("\n🏢 Department Tests:")
        self.test_departments_list()
        
        # Document management tests
        print("\n📄 Document Management Tests:")
        self.test_documents_list()
        self.test_document_categories()
        self.test_document_search()
        self.test_document_stats()
        
        # AI features tests
        print("\n🤖 AI Features Tests:")
        self.test_ai_chat()
        
        return self.get_results()
    
    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 Failed Tests:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        return self.test_results

if __name__ == "__main__":
    tester = APITester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results['failed'] > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0) 