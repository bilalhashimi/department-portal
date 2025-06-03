from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Clean up Django admin permissions to keep only essential ones'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧹 Starting Django Admin Permission Cleanup...'))
        
        # Keep only essential permissions for admin functionality
        essential_permissions = [
            # User management essentials
            'accounts.view_user',
            'accounts.change_user',
            'accounts.add_user',
            'accounts.view_userprofile',
            'accounts.change_userprofile',
            
            # Department essentials
            'departments.view_department',
            'departments.change_department',
            'departments.add_department',
            'departments.view_employeedepartment',
            'departments.change_employeedepartment',
            'departments.add_employeedepartment',
            
            # Custom Permission System (KEEP ALL)
            'departments.view_permission',
            'departments.change_permission',
            'departments.add_permission',
            'departments.delete_permission',
            'departments.view_permissiontemplate',
            'departments.change_permissiontemplate',
            'departments.add_permissiontemplate',
            'departments.delete_permissiontemplate',
            'departments.view_permissionauditlog',
            
            # System settings
            'departments.view_systemsettings',
            'departments.change_systemsettings',
        ]
        
        # Get all permissions
        all_permissions = Permission.objects.filter(
            content_type__app_label__in=['accounts', 'departments', 'documents']
        )
        
        permissions_to_remove = []
        for perm in all_permissions:
            perm_code = f"{perm.content_type.app_label}.{perm.codename}"
            if perm_code not in essential_permissions:
                permissions_to_remove.append(perm)
        
        self.stdout.write(f"📊 Found {len(all_permissions)} total permissions")
        self.stdout.write(f"🔧 Keeping {len(essential_permissions)} essential permissions")
        self.stdout.write(f"🗑️  Removing {len(permissions_to_remove)} unnecessary permissions")
        
        if permissions_to_remove:
            self.stdout.write("\n🗑️ Removing these permissions:")
            for perm in permissions_to_remove:
                self.stdout.write(f"   - {perm.content_type.app_label}.{perm.codename}: {perm.name}")
            
            # Remove the permissions
            Permission.objects.filter(id__in=[p.id for p in permissions_to_remove]).delete()
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Removed {len(permissions_to_remove)} unnecessary permissions"))
        else:
            self.stdout.write("✨ No unnecessary permissions found")
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Admin permission cleanup completed!'))
        self.stdout.write(
            self.style.WARNING(
                '\n💡 Note: Django admin now shows only essential permissions.\n'
                '   Custom Department Portal permissions are managed through:\n'
                '   - /admin/departments/permission/ (individual permissions)\n'
                '   - /admin/accounts/user/ (user permissions inline)\n'
                '   - Frontend Admin Settings at http://localhost:5173/admin-settings'
            )
        ) 