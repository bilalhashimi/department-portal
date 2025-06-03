"""
Document utility functions including permission checking
"""
from typing import List, Optional
from django.contrib.auth import get_user_model
from departments.models import Permission

User = get_user_model()

def user_has_permission(user: User, permission_key: str) -> bool:
    """
    Check if a user has a specific permission either directly or through department
    
    Args:
        user: The user to check permissions for
        permission_key: The permission key (e.g., 'documents.view_all')
    
    Returns:
        bool: True if user has the permission, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    # Admin users have all permissions
    if user.role == 'admin':
        return True
    
    # Check direct user permissions
    user_permission = Permission.objects.filter(
        entity_type='user',
        entity_id=user.id,
        permission=permission_key,
        is_active=True
    ).exists()
    
    if user_permission:
        return True
    
    # Check department permissions
    # Get user's active departments
    user_departments = user.department_assignments.filter(
        end_date__isnull=True
    ).values_list('department_id', flat=True)
    
    department_permission = Permission.objects.filter(
        entity_type='department',
        entity_id__in=user_departments,
        permission=permission_key,
        is_active=True
    ).exists()
    
    return department_permission

def get_user_permissions(user: User) -> List[str]:
    """
    Get all permissions for a user (direct + department)
    
    Args:
        user: The user to get permissions for
    
    Returns:
        List[str]: List of permission keys the user has
    """
    if not user or not user.is_authenticated:
        return []
    
    # Admin users have all permissions
    if user.role == 'admin':
        return [
            'documents.view_all', 'documents.create', 'documents.edit_all', 'documents.delete_all',
            'documents.approve', 'documents.share', 'categories.view_all', 'categories.create',
            'categories.edit', 'categories.delete', 'categories.assign', 'departments.view_all',
            'departments.manage', 'departments.assign_users', 'departments.view_employees',
            'users.view_all', 'users.create', 'users.edit', 'users.deactivate', 'users.assign_roles',
            'system.admin_settings', 'system.view_analytics', 'system.manage_settings', 'system.backup'
        ]
    
    permissions = set()
    
    # Direct user permissions
    user_permissions = Permission.objects.filter(
        entity_type='user',
        entity_id=user.id,
        is_active=True
    ).values_list('permission', flat=True)
    permissions.update(user_permissions)
    
    # Department permissions
    user_departments = user.department_assignments.filter(
        end_date__isnull=True
    ).values_list('department_id', flat=True)
    
    department_permissions = Permission.objects.filter(
        entity_type='department',
        entity_id__in=user_departments,
        is_active=True
    ).values_list('permission', flat=True)
    permissions.update(department_permissions)
    
    return list(permissions)

def get_accessible_document_categories(user: User) -> List:
    """
    Get categories that a user can access based on permissions
    
    Args:
        user: The user to check permissions for
    
    Returns:
        List: List of category IDs the user can access
    """
    from documents.models import DocumentCategory
    
    if not user or not user.is_authenticated:
        return []
    
    # Admin users can access all categories
    if user.role == 'admin':
        return list(DocumentCategory.objects.values_list('id', flat=True))
    
    accessible_categories = set()
    
    # If user has categories.view_all permission, they can see all categories
    if user_has_permission(user, 'categories.view_all'):
        accessible_categories.update(DocumentCategory.objects.values_list('id', flat=True))
    else:
        # Check category-specific permissions
        user_departments = user.department_assignments.filter(
            end_date__isnull=True
        ).values_list('department_id', flat=True)
        
        # Categories with user permissions
        user_category_permissions = Permission.objects.filter(
            entity_type='user',
            entity_id=user.id,
            permission='categories.view_all',
            is_active=True
        ).values_list('entity_id', flat=True)
        
        # Categories with department permissions
        dept_category_permissions = Permission.objects.filter(
            entity_type='department',
            entity_id__in=user_departments,
            permission='categories.view_all',
            is_active=True
        ).values_list('entity_id', flat=True)
        
        # Public categories
        public_categories = DocumentCategory.objects.filter(
            is_public=True
        ).values_list('id', flat=True)
        
        accessible_categories.update(user_category_permissions)
        accessible_categories.update(dept_category_permissions)
        accessible_categories.update(public_categories)
    
    return list(accessible_categories) 