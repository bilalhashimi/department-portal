#!/usr/bin/env python3
"""
Script to create test departments for testing department sharing functionality
"""

import os
import sys
import django

# Add the current directory to the Python path
sys.path.append('/app')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from departments.models import Department

User = get_user_model()

def create_test_departments():
    """Create test departments for testing"""
    
    print("🚀 Creating test departments...")
    
    # Get admin user to be department head
    try:
        admin_user = User.objects.get(email='bilalhashimi89@gmail.com')
        print(f"📝 Found admin user: {admin_user.email}")
    except User.DoesNotExist:
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            print("❌ No admin user found!")
            return
        print(f"📝 Using admin user: {admin_user.email}")
    
    # Test departments to create
    departments_to_create = [
        {
            'name': 'Human Resources',
            'code': 'HR',
            'description': 'Human Resources Department - Managing employee relations, recruitment, and policies',
            'email': 'hr@portal.com',
            'location': 'Building A, Floor 2'
        },
        {
            'name': 'Finance Department',
            'code': 'FIN',
            'description': 'Finance Department - Managing financial operations, budgets, and accounting',
            'email': 'finance@portal.com',
            'location': 'Building A, Floor 3'
        },
        {
            'name': 'Marketing Department',
            'code': 'MKT',
            'description': 'Marketing Department - Managing marketing campaigns, brand strategy, and communications',
            'email': 'marketing@portal.com',
            'location': 'Building B, Floor 1'
        },
        {
            'name': 'Operations Department',
            'code': 'OPS',
            'description': 'Operations Department - Managing daily operations, processes, and logistics',
            'email': 'operations@portal.com',
            'location': 'Building B, Floor 2'
        },
        {
            'name': 'Research & Development',
            'code': 'RND',
            'description': 'Research & Development - Innovation, product development, and research initiatives',
            'email': 'rnd@portal.com',
            'location': 'Building C, Floor 1'
        },
        {
            'name': 'Customer Support',
            'code': 'CS',
            'description': 'Customer Support Department - Handling customer inquiries and support services',
            'email': 'support@portal.com',
            'location': 'Building A, Floor 1'
        }
    ]
    
    created_count = 0
    for dept_data in departments_to_create:
        # Check if department already exists
        existing_dept = Department.objects.filter(
            name=dept_data['name']
        ).first()
        
        if existing_dept:
            print(f"📝 Department already exists: {existing_dept.name} ({existing_dept.code})")
        else:
            # Create department
            dept = Department.objects.create(
                name=dept_data['name'],
                code=dept_data['code'],
                description=dept_data['description'],
                email=dept_data['email'],
                location=dept_data['location'],
                head=admin_user,  # Admin as department head for testing
                is_active=True
            )
            created_count += 1
            print(f"✅ Created department: {dept.name} ({dept.code})")
    
    # Also ensure IT department exists (might be from fixtures)
    if not Department.objects.filter(code='IT').exists():
        it_dept = Department.objects.create(
            name='Information Technology',
            code='IT',
            description='Information Technology Department - Managing IT infrastructure and systems',
            email='it@portal.com',
            location='Building C, Floor 2',
            head=admin_user,
            is_active=True
        )
        created_count += 1
        print(f"✅ Created department: {it_dept.name} ({it_dept.code})")
    
    total_departments = Department.objects.filter(is_active=True).count()
    
    print(f"\n🎉 Department setup complete!")
    print(f"📊 Summary:")
    print(f"   - New departments created: {created_count}")
    print(f"   - Total active departments: {total_departments}")
    
    print(f"\n📋 All departments:")
    for dept in Department.objects.filter(is_active=True).order_by('name'):
        print(f"   - {dept.name} ({dept.code})")
    
    print(f"\n🔍 Now test department sharing by:")
    print(f"   1. Upload a document")
    print(f"   2. Click share button")
    print(f"   3. Select departments from the dropdown")
    print(f"   4. You should see {total_departments} departments available")

if __name__ == '__main__':
    create_test_departments() 