#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_backend.settings')
django.setup()

from documents.vector_service import vector_service

def test_vector_db():
    print("Testing vector database connection...")
    
    try:
        # Initialize the collection
        vector_service.initialize_collection()
        print("✅ Vector database collection initialized successfully")
        
        # Test basic operations
        print("🔍 Testing vector database operations...")
        
        # Test embedding generation
        test_text = "This is a test document about employee policies and procedures."
        embedding = vector_service.generate_embedding(test_text)
        print(f"✅ Generated embedding with dimension: {len(embedding)}")
        
        # Test collection info
        collection_info = vector_service.get_collection_info()
        print(f"✅ Collection info: {collection_info}")
        
        print("🎉 Vector database is working correctly!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vector_db() 