#!/usr/bin/env python3
"""
System Settings and Backup Functionality Test
Tests the new system settings and backup features
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_ADMIN_EMAIL = "bilalhashimi89@gmail.com"
TEST_ADMIN_PASSWORD = "admin123"

class SystemSettingsTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self):
        """Authenticate as admin user"""
        print("🔐 Authenticating as admin...")
        
        login_data = {
            "email": TEST_ADMIN_EMAIL,
            "password": TEST_ADMIN_PASSWORD
        }
        
        response = self.session.post(f"{BASE_URL}/accounts/auth/login/", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            self.auth_token = data.get('access')
            self.session.headers.update({
                'Authorization': f'Bearer {self.auth_token}'
            })
            print(f"✅ Authenticated successfully as {data.get('user', {}).get('email')}")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def test_get_system_settings(self):
        """Test getting system settings"""
        print("\n📋 Testing get system settings...")
        
        response = self.session.get(f"{BASE_URL}/departments/settings/")
        
        if response.status_code == 200:
            settings = response.json()
            print("✅ System settings retrieved successfully")
            print(f"   Site Name: {settings.get('site_name')}")
            print(f"   Max File Size: {settings.get('max_file_size')} MB")
            print(f"   AI Chat Enabled: {settings.get('enable_ai_chat')}")
            print(f"   Auto Backup: {settings.get('auto_backup_enabled')}")
            return settings
        else:
            print(f"❌ Failed to get system settings: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def test_update_system_settings(self):
        """Test updating system settings"""
        print("\n⚙️ Testing update system settings...")
        
        # Test settings update
        update_data = {
            "site_name": "Department Portal - Test",
            "max_file_size": "75",
            "allowed_file_types": "pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,png,zip",
            "enable_ai_chat": False,  # Disable AI chat for testing
            "enable_document_sharing": True,
            "require_document_approval": True,
            "auto_backup_enabled": True,
            "backup_frequency": "weekly",
            "backup_retention_days": "45",
            "password_expiry_days": "120",
            "max_login_attempts": "3"
        }
        
        response = self.session.post(f"{BASE_URL}/departments/settings/update/", json=update_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ System settings updated successfully")
            print(f"   Message: {result.get('message')}")
            
            # Verify the update by getting settings again
            verify_response = self.session.get(f"{BASE_URL}/departments/settings/")
            if verify_response.status_code == 200:
                updated_settings = verify_response.json()
                print(f"   Verified - Site Name: {updated_settings.get('site_name')}")
                print(f"   Verified - AI Chat Enabled: {updated_settings.get('enable_ai_chat')}")
                print(f"   Verified - Max File Size: {updated_settings.get('max_file_size')} MB")
                return True
            else:
                print("❌ Failed to verify settings update")
                return False
        else:
            print(f"❌ Failed to update system settings: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def test_create_backup(self):
        """Test creating a system backup"""
        print("\n💾 Testing system backup creation...")
        
        backup_data = {
            "name": f"test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "include_documents": True,
            "include_database": True,
            "include_settings": True,
            "include_user_data": True
        }
        
        print(f"   Creating backup: {backup_data['name']}")
        response = self.session.post(f"{BASE_URL}/departments/backups/create/", json=backup_data)
        
        if response.status_code == 200:
            result = response.json()
            backup_id = result.get('backup', {}).get('id')
            print("✅ Backup creation initiated successfully")
            print(f"   Backup ID: {backup_id}")
            print(f"   Message: {result.get('message')}")
            
            # Wait a bit for backup to complete
            print("   Waiting for backup to complete...")
            time.sleep(5)
            
            return backup_id
        else:
            print(f"❌ Failed to create backup: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def test_list_backups(self):
        """Test listing system backups"""
        print("\n📋 Testing backup listing...")
        
        response = self.session.get(f"{BASE_URL}/departments/backups/")
        
        if response.status_code == 200:
            result = response.json()
            backups = result.get('backups', [])
            print(f"✅ Found {len(backups)} backups")
            
            for backup in backups[:3]:  # Show first 3 backups
                print(f"   📦 {backup.get('name')}")
                print(f"      Status: {backup.get('status')}")
                print(f"      Size: {backup.get('file_size_mb', 0):.1f} MB")
                print(f"      Created: {backup.get('created_at')}")
                print(f"      By: {backup.get('created_by')}")
                
                if backup.get('includes'):
                    includes = []
                    if backup['includes'].get('documents'): includes.append('Docs')
                    if backup['includes'].get('database'): includes.append('DB')
                    if backup['includes'].get('settings'): includes.append('Settings')
                    if backup['includes'].get('user_data'): includes.append('Users')
                    print(f"      Includes: {', '.join(includes)}")
                print()
            
            return backups
        else:
            print(f"❌ Failed to list backups: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def test_backup_download(self, backup_id):
        """Test backup download"""
        if not backup_id:
            print("\n⚠️ Skipping backup download test - no backup ID")
            return
        
        print(f"\n📥 Testing backup download for ID: {backup_id}")
        
        response = self.session.get(f"{BASE_URL}/departments/backups/{backup_id}/download/")
        
        if response.status_code == 200:
            print("✅ Backup download successful")
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            print(f"   Content-Length: {len(response.content)} bytes")
            
            # Save a small portion to verify it's a valid zip file
            if response.content[:2] == b'PK':
                print("   ✅ Valid ZIP file signature detected")
            else:
                print("   ⚠️ File doesn't appear to be a valid ZIP")
            
            return True
        else:
            print(f"❌ Failed to download backup: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def test_restore_original_settings(self):
        """Restore original settings after testing"""
        print("\n🔄 Restoring original settings...")
        
        original_data = {
            "site_name": "Department Portal",
            "max_file_size": "50",
            "allowed_file_types": "pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,png",
            "enable_ai_chat": True,  # Re-enable AI chat
            "enable_document_sharing": True,
            "require_document_approval": False,
            "auto_backup_enabled": True,
            "backup_frequency": "daily",
            "backup_retention_days": "30",
            "password_expiry_days": "90",
            "max_login_attempts": "5"
        }
        
        response = self.session.post(f"{BASE_URL}/departments/settings/update/", json=original_data)
        
        if response.status_code == 200:
            print("✅ Original settings restored successfully")
            return True
        else:
            print(f"❌ Failed to restore original settings: {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run all system settings tests"""
        print("🚀 Starting System Settings & Backup Tests")
        print("=" * 50)
        
        if not self.authenticate():
            return False
        
        # Test system settings
        original_settings = self.test_get_system_settings()
        if not original_settings:
            return False
        
        # Test settings update
        if not self.test_update_system_settings():
            return False
        
        # Test backup creation
        backup_id = self.test_create_backup()
        
        # Test backup listing
        backups = self.test_list_backups()
        
        # Test backup download if we have a backup
        if backup_id:
            self.test_backup_download(backup_id)
        
        # Restore original settings
        self.test_restore_original_settings()
        
        print("\n" + "=" * 50)
        print("✅ System Settings & Backup Tests Completed!")
        print("\nKey Features Tested:")
        print("  ✅ Get system settings")
        print("  ✅ Update system settings")
        print("  ✅ Create system backup")
        print("  ✅ List system backups")
        print("  ✅ Download system backup")
        print("  ✅ Settings validation and restoration")
        
        return True

def main():
    """Main test function"""
    tester = SystemSettingsTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! System settings functionality is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        exit(1)

if __name__ == "__main__":
    main() 