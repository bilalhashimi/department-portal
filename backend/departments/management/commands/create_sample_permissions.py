from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from departments.models import Permission, PermissionTemplate, Department

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample permissions and templates for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample permissions and templates...'))
        
        # Get or create an admin user to be the permission granter
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            self.stdout.write(self.style.WARNING('No admin user found. Creating one...'))
            admin_user = User.objects.create_user(
                email='admin@company.com',
                username='admin',
                password='admin123',
                role='admin',
                first_name='System',
                last_name='Administrator'
            )
        
        # Create permission templates
        templates = [
            {
                'name': 'Document Manager',
                'description': 'Full document management permissions including create, edit, delete, and approve',
                'permissions': [
                    'documents.view_all',
                    'documents.create',
                    'documents.edit_all',
                    'documents.delete_all',
                    'documents.approve',
                    'documents.share',
                    'documents.download',
                    'categories.view_all',
                    'categories.create',
                    'categories.edit',
                    'categories.assign'
                ]
            },
            {
                'name': 'Document Viewer',
                'description': 'Basic document viewing and downloading permissions',
                'permissions': [
                    'documents.view_all',
                    'documents.download',
                    'categories.view_all'
                ]
            },
            {
                'name': 'Department Head',
                'description': 'Department management and user oversight permissions',
                'permissions': [
                    'documents.view_all',
                    'documents.create',
                    'documents.approve',
                    'documents.share',
                    'departments.view_all',
                    'departments.assign_users',
                    'departments.view_employees',
                    'departments.manage_budget',
                    'users.view_all',
                    'users.edit',
                    'categories.view_all'
                ]
            },
            {
                'name': 'HR Manager',
                'description': 'Human resources management permissions',
                'permissions': [
                    'users.view_all',
                    'users.create',
                    'users.edit',
                    'users.assign_roles',
                    'departments.view_all',
                    'departments.assign_users',
                    'departments.view_employees',
                    'documents.view_all',
                    'documents.create',
                    'documents.share'
                ]
            },
            {
                'name': 'System Administrator',
                'description': 'Full system administration permissions',
                'permissions': [
                    'system.admin_settings',
                    'system.view_analytics',
                    'system.manage_settings',
                    'system.backup',
                    'system.view_logs',
                    'system.manage_templates',
                    'users.view_all',
                    'users.create',
                    'users.edit',
                    'users.deactivate',
                    'users.assign_roles',
                    'users.manage_permissions',
                    'departments.view_all',
                    'departments.manage',
                    'documents.view_all',
                    'documents.create',
                    'documents.edit_all',
                    'documents.delete_all'
                ]
            }
        ]
        
        created_templates = []
        for template_data in templates:
            template, created = PermissionTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'permissions': template_data['permissions'],
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            
            if created:
                created_templates.append(template)
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.name}')
                )
        
        # Create some sample user permissions
        sample_users = User.objects.filter(role__in=['employee', 'manager']).exclude(role='admin')[:3]
        
        if sample_users:
            for user in sample_users:
                # Grant basic document viewing permissions to all sample users
                permission, created = Permission.objects.get_or_create(
                    entity_type='user',
                    entity_id=user.id,
                    permission='documents.view_all',
                    defaults={
                        'permission_category': 'documents',
                        'granted_by': admin_user,
                        'is_active': True,
                        'notes': f'Sample permission granted for demonstration'
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Granted documents.view_all to {user.email}')
                    )
        
        # Create sample department permissions
        departments = Department.objects.filter(is_active=True)[:2]
        
        for dept in departments:
            # Grant basic permissions to departments
            permissions_to_grant = ['documents.create', 'categories.view_all']
            
            for perm in permissions_to_grant:
                permission, created = Permission.objects.get_or_create(
                    entity_type='department',
                    entity_id=dept.id,
                    permission=perm,
                    defaults={
                        'permission_category': perm.split('.')[0],
                        'granted_by': admin_user,
                        'is_active': True,
                        'notes': f'Sample department permission for {dept.name}'
                    }
                )
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Granted {perm} to department {dept.name}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample data creation complete!\n'
                f'Created {len(created_templates)} permission templates.\n'
                f'You can now view and manage permissions in Django Admin at:\n'
                f'- /admin/departments/permission/\n'
                f'- /admin/departments/permissiontemplate/\n'
                f'- /admin/accounts/user/ (with inline permissions)\n'
            )
        ) 