import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_backend.settings')
django.setup()

from accounts.models import User

# Check your existing account
try:
    user = User.objects.get(email='bilalhashimi89@gmail.com')
    print(f"✅ Found your account: {user.email}")
    print(f"   Role: {user.role}")
    print(f"   Active: {user.is_active}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Superuser: {user.is_superuser}")
    
    # Reset password to 'admin123'
    user.set_password('admin123')
    user.save()
    print("✅ Password reset to 'admin123'")
    
    print("\n🔑 Your login credentials:")
    print(f"📧 Email: bilalhashimi89@gmail.com")
    print(f"🔒 Password: admin123")
    
except User.DoesNotExist:
    print("❌ User not found")
    
    # Create the user if it doesn't exist
    user = User.objects.create_superuser(
        email='bilalhashimi89@gmail.com',
        password='admin123',
        first_name='Ahmad',
        last_name='Bilal',
        role='admin'
    )
    print("✅ Admin user created!")
    print(f"📧 Email: bilalhashimi89@gmail.com")
    print(f"🔒 Password: admin123") 