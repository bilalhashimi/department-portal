#!/usr/bin/env python3
"""
Script to create test document shares for testing the 'Shared With Me' functionality
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
from documents.models import Document, DocumentShare, DocumentCategory
from departments.models import Department

User = get_user_model()

def create_test_shares():
    """Create test document shares for testing"""
    
    print("🚀 Creating test document shares...")
    
    # Get or create a test user to share FROM
    test_user_email = 'testuser@portal.com'
    test_user, created = User.objects.get_or_create(
        email=test_user_email,
        defaults={
            'first_name': 'Test',
            'last_name': 'User', 
            'role': 'employee',
            'is_active': True,
            'is_verified': True
        }
    )
    if created:
        test_user.set_password('testpassword123')
        test_user.save()
        print(f"✅ Created test user: {test_user_email}")
    else:
        print(f"📝 Using existing test user: {test_user_email}")
    
    # Get the admin user to share WITH
    try:
        admin_user = User.objects.get(email='bilalhashimi89@gmail.com')
        print(f"📝 Found admin user: {admin_user.email}")
    except User.DoesNotExist:
        # Fallback to any admin user
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            print("❌ No admin user found!")
            return
        print(f"📝 Using admin user: {admin_user.email}")
    
    # Get or create a test category
    category, created = DocumentCategory.objects.get_or_create(
        name='Shared Documents',
        defaults={
            'description': 'Documents for sharing tests',
            'is_public': False
        }
    )
    if created:
        print(f"✅ Created category: {category.name}")
    
    # Create some test documents owned by the test user
    documents_to_create = [
        {
            'title': 'Project Plan - Shared Document',
            'description': 'This is a test document shared with you',
            'status': 'published'
        },
        {
            'title': 'Meeting Minutes - Shared',
            'description': 'Shared meeting minutes document',
            'status': 'published'
        },
        {
            'title': 'Policy Document - Shared',
            'description': 'Shared policy document for review',
            'status': 'approved'
        }
    ]
    
    created_docs = []
    for doc_data in documents_to_create:
        # Check if document already exists
        existing_doc = Document.objects.filter(
            title=doc_data['title'],
            created_by=test_user
        ).first()
        
        if existing_doc:
            print(f"📝 Using existing document: {existing_doc.title}")
            created_docs.append(existing_doc)
        else:
            # Create a minimal document without file
            doc = Document.objects.create(
                title=doc_data['title'],
                description=doc_data['description'],
                status=doc_data['status'],
                category=category,
                created_by=test_user,
                owned_by=test_user,
                file_type='PDF',
                file_size=1024,  # 1KB fake size
            )
            created_docs.append(doc)
            print(f"✅ Created document: {doc.title}")
    
    # Create document shares
    shares_created = 0
    for doc in created_docs:
        # Check if share already exists
        existing_share = DocumentShare.objects.filter(
            document=doc,
            share_type='user',
            shared_with_user=admin_user,
            is_active=True
        ).first()
        
        if existing_share:
            print(f"📝 Share already exists: {doc.title} -> {admin_user.email}")
        else:
            share = DocumentShare.objects.create(
                document=doc,
                share_type='user',
                shared_with_user=admin_user,
                shared_by=test_user,
                access_level='download',
                allow_download=True,
                allow_reshare=False
            )
            shares_created += 1
            print(f"✅ Created share: {doc.title} -> {admin_user.email}")
    
    print(f"\n🎉 Test setup complete!")
    print(f"📊 Summary:")
    print(f"   - Test user: {test_user.email}")
    print(f"   - Admin user: {admin_user.email}")
    print(f"   - Documents created/found: {len(created_docs)}")
    print(f"   - New shares created: {shares_created}")
    print(f"   - Total active shares: {DocumentShare.objects.filter(shared_with_user=admin_user, is_active=True).count()}")
    
    print(f"\n🔍 Now test by:")
    print(f"   1. Login as: {admin_user.email}")
    print(f"   2. Navigate to 'Shared With Me'")
    print(f"   3. You should see {DocumentShare.objects.filter(shared_with_user=admin_user, is_active=True).count()} shared documents")

if __name__ == '__main__':
    create_test_shares() 