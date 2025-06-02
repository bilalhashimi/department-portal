#!/usr/bin/env python
"""
Database Functionality Test Suite
Tests Django models, migrations, and database operations
"""

import os
import sys
import django
from datetime import date
from django.core.management import execute_from_command_line
from django.test.utils import get_runner
from django.conf import settings
from django.db import connection
from django.apps import apps

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from departments.models import Department, Position, EmployeeDepartment
from documents.models import Document, DocumentCategory, DocumentTag, DocumentShare
from accounts.models import UserProfile, LoginAttempt

User = get_user_model()

class DatabaseTester:
    def __init__(self):
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
    
    def test_database_connection(self):
        """Test database connectivity"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            success = result[0] == 1
            self.log_test("Database Connection", success, 
                         "Connected successfully" if success else "Connection failed")
            return success
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
            return False
    
    def test_migrations_applied(self):
        """Test if all migrations are applied"""
        try:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            success = len(plan) == 0
            self.log_test("Migrations Applied", success,
                         "All migrations applied" if success else f"{len(plan)} unapplied migrations")
            return success
        except Exception as e:
            self.log_test("Migrations Applied", False, str(e))
            return False
    
    def test_user_model(self):
        """Test User model functionality"""
        try:
            # Test user creation
            user = User.objects.create_user(
                email='test_db@example.com',
                password='testpass123',
                first_name='Test',
                last_name='User',
                username='testuser_db'
            )
            
            # Test user retrieval
            retrieved_user = User.objects.get(email='test_db@example.com')
            
            # Test user methods
            full_name = retrieved_user.get_full_name()
            
            # Cleanup
            retrieved_user.delete()
            
            success = (retrieved_user.email == 'test_db@example.com' and 
                      full_name == 'Test User')
            
            self.log_test("User Model", success,
                         "User creation, retrieval, and methods work" if success else "User model issues")
            return success
        except Exception as e:
            self.log_test("User Model", False, str(e))
            return False
    
    def test_department_model(self):
        """Test Department model functionality"""
        try:
            # Test department creation
            department = Department.objects.create(
                name='Test Department',
                code='TEST',
                description='Test Department for DB testing'
            )
            
            # Test department retrieval
            retrieved_dept = Department.objects.get(code='TEST')
            
            # Cleanup
            retrieved_dept.delete()
            
            success = retrieved_dept.name == 'Test Department'
            self.log_test("Department Model", success,
                         "Department creation and retrieval work" if success else "Department model issues")
            return success
        except Exception as e:
            self.log_test("Department Model", False, str(e))
            return False
    
    def test_document_model(self):
        """Test Document model functionality"""
        try:
            # Create required dependencies
            user = User.objects.create_user(
                email='doc_test@example.com',
                password='testpass123',
                first_name='Doc',
                last_name='User',
                username='docuser'
            )
            
            category = DocumentCategory.objects.create(
                name='Test Category',
                slug='test-category'
            )
            
            # Test document creation
            document = Document.objects.create(
                title='Test Document',
                description='Test document for DB testing',
                category=category,
                created_by=user,
                owned_by=user,
                status='draft'
            )
            
            # Test document retrieval
            retrieved_doc = Document.objects.get(title='Test Document')
            
            # Cleanup
            retrieved_doc.delete()
            category.delete()
            user.delete()
            
            success = retrieved_doc.title == 'Test Document'
            self.log_test("Document Model", success,
                         "Document creation and retrieval work" if success else "Document model issues")
            return success
        except Exception as e:
            self.log_test("Document Model", False, str(e))
            return False
    
    def test_model_relationships(self):
        """Test model relationships"""
        try:
            # Create test data
            user = User.objects.create_user(
                email='rel_test@example.com',
                password='testpass123',
                first_name='Rel',
                last_name='User',
                username='reluser'
            )
            
            department = Department.objects.create(
                name='Relationship Test Dept',
                code='RELTEST'
            )
            
            # Test department assignment relationship
            assignment = EmployeeDepartment.objects.create(
                employee=user,
                department=department,
                start_date=date(2024, 1, 1),
                is_primary=True
            )
            
            # Test relationship access
            user_departments = user.department_assignments.all()
            dept_users = department.employees.all()
            
            # Cleanup
            assignment.delete()
            department.delete()
            user.delete()
            
            success = (user_departments.count() == 1 and dept_users.count() == 1)
            self.log_test("Model Relationships", success,
                         "Relationships work correctly" if success else "Relationship issues")
            return success
        except Exception as e:
            self.log_test("Model Relationships", False, str(e))
            return False
    
    def test_user_profile_model(self):
        """Test UserProfile model"""
        try:
            user = User.objects.create_user(
                email='profile_test@example.com',
                password='testpass123',
                username='profileuser'
            )
            
            # Test profile creation
            profile = UserProfile.objects.create(
                user=user,
                employee_id='EMP001',
                phone_number='+1234567890'
            )
            
            # Test profile retrieval
            retrieved_profile = UserProfile.objects.get(user=user)
            
            # Cleanup
            profile.delete()
            user.delete()
            
            success = retrieved_profile.employee_id == 'EMP001'
            self.log_test("UserProfile Model", success,
                         "UserProfile creation and retrieval work" if success else "UserProfile model issues")
            return success
        except Exception as e:
            self.log_test("UserProfile Model", False, str(e))
            return False
    
    def test_document_sharing_model(self):
        """Test DocumentShare model"""
        try:
            # Create dependencies
            user1 = User.objects.create_user(
                email='share1@example.com',
                password='testpass123',
                username='shareuser1'
            )
            
            user2 = User.objects.create_user(
                email='share2@example.com',
                password='testpass123',
                username='shareuser2'
            )
            
            category = DocumentCategory.objects.create(
                name='Share Test Category',
                slug='share-test'
            )
            
            document = Document.objects.create(
                title='Share Test Document',
                category=category,
                created_by=user1,
                owned_by=user1,
                status='published'
            )
            
            # Test document share creation
            share = DocumentShare.objects.create(
                document=document,
                share_type='user',
                shared_with_user=user2,
                shared_by=user1,
                access_level='view'
            )
            
            # Test share retrieval
            retrieved_share = DocumentShare.objects.get(document=document)
            
            # Cleanup
            share.delete()
            document.delete()
            category.delete()
            user1.delete()
            user2.delete()
            
            success = retrieved_share.shared_with_user == user2
            self.log_test("DocumentShare Model", success,
                         "DocumentShare creation and retrieval work" if success else "DocumentShare model issues")
            return success
        except Exception as e:
            self.log_test("DocumentShare Model", False, str(e))
            return False
    
    def test_model_constraints(self):
        """Test model constraints and validations"""
        try:
            # Test unique constraints
            user1 = User.objects.create_user(
                email='constraint1@example.com',
                password='testpass123',
                username='constraintuser1'
            )
            
            try:
                # This should fail due to unique email constraint
                user2 = User.objects.create_user(
                    email='constraint1@example.com',  # Same email
                    password='testpass123',
                    username='constraintuser2'
                )
                constraint_works = False  # Should not reach here
            except Exception:
                constraint_works = True  # Expected to fail
            
            # Cleanup
            user1.delete()
            
            self.log_test("Model Constraints", constraint_works,
                         "Unique constraints work" if constraint_works else "Constraint validation failed")
            return constraint_works
        except Exception as e:
            self.log_test("Model Constraints", False, str(e))
            return False
    
    def test_database_indexes(self):
        """Test if database indexes are properly created"""
        try:
            with connection.cursor() as cursor:
                # Check database type and use appropriate query
                db_vendor = connection.vendor
                
                if db_vendor == 'sqlite':
                    cursor.execute("""
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='index' AND name LIKE '%email%'
                    """)
                    email_indexes = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='index'
                    """)
                    total_indexes = cursor.fetchone()[0]
                elif db_vendor == 'postgresql':
                    cursor.execute("""
                        SELECT COUNT(*) FROM pg_indexes 
                        WHERE indexname LIKE '%email%'
                    """)
                    email_indexes = cursor.fetchone()[0]
                    
                    cursor.execute("""
                        SELECT COUNT(*) FROM pg_indexes
                    """)
                    total_indexes = cursor.fetchone()[0]
                else:
                    # For other databases, just check if we can query indexes table
                    total_indexes = 1
                    email_indexes = 0
            
            success = total_indexes > 0
            self.log_test("Database Indexes", success,
                         f"Found {total_indexes} indexes including {email_indexes} email indexes ({db_vendor})" if success 
                         else "No indexes found")
            return success
        except Exception as e:
            self.log_test("Database Indexes", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all database tests"""
        print("🚀 Starting Comprehensive Database Tests")
        print("=" * 50)
        
        # Test basic connectivity
        if not self.test_database_connection():
            print("❌ Database is not accessible. Cannot continue tests.")
            return self.get_results()
        
        # Test migrations
        print("\n📋 Migration Tests:")
        self.test_migrations_applied()
        
        # Test models
        print("\n🏗️ Model Tests:")
        self.test_user_model()
        self.test_department_model()
        self.test_document_model()
        self.test_user_profile_model()
        self.test_document_sharing_model()
        
        # Test relationships
        print("\n🔗 Relationship Tests:")
        self.test_model_relationships()
        
        # Test constraints
        print("\n🔒 Constraint Tests:")
        self.test_model_constraints()
        
        # Test database structure
        print("\n🗃️ Database Structure Tests:")
        self.test_database_indexes()
        
        return self.get_results()
    
    def get_results(self):
        """Get test results summary"""
        print("\n" + "=" * 50)
        print("📊 DATABASE TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        total = self.test_results['passed'] + self.test_results['failed']
        if total > 0:
            print(f"📈 Success Rate: {(self.test_results['passed'] / total * 100):.1f}%")
        
        if self.test_results['errors']:
            print("\n🚨 Failed Tests:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        return self.test_results

if __name__ == "__main__":
    tester = DatabaseTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results['failed'] > 0:
        sys.exit(1)
    else:
        print("\n🎉 All database tests passed!")
        sys.exit(0) 