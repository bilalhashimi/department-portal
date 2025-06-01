#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if admin user already exists
admin_username = 'admin'
admin_email = 'admin@portal.com'
admin_password = 'admin123'

if User.objects.filter(username=admin_username).exists():
    print(f"User '{admin_username}' already exists. Updating password...")
    user = User.objects.get(username=admin_username)
    user.set_password(admin_password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"Password updated for user '{admin_username}'")
else:
    print(f"Creating new superuser '{admin_username}'...")
    user = User.objects.create_superuser(
        username=admin_username,
        email=admin_email,
        password=admin_password
    )
    print(f"Superuser '{admin_username}' created successfully!")

print(f"\nLogin credentials:")
print(f"Username: {admin_username}")
print(f"Password: {admin_password}")
print(f"Email: {admin_email}") 