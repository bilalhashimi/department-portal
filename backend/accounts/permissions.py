from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
import logging

security_logger = logging.getLogger('security')


class BaseRolePermission(permissions.BasePermission):
    """Base class for role-based permissions"""
    
    required_roles = []
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not request.user.is_verified:
            security_logger.warning(f"Unverified user attempting access: {request.user.email}")
            return False
        
        if request.user.role in self.required_roles:
            return True
        
        # Log permission denial
        security_logger.warning(
            f"Permission denied: {request.user.email} (role: {request.user.role}) "
            f"attempted to access {request.path} requiring roles: {self.required_roles}"
        )
        return False


class IsAdminUser(BaseRolePermission):
    """Permission class for admin-only access"""
    required_roles = ['admin']


class IsAdminOrDepartmentHead(BaseRolePermission):
    """Permission class for admin or department head access"""
    required_roles = ['admin', 'department_head']


class IsAdminOrManager(BaseRolePermission):
    """Permission class for admin or manager access"""
    required_roles = ['admin', 'department_head', 'manager']


class IsVerifiedUser(permissions.BasePermission):
    """Permission class to ensure user is verified"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not request.user.is_verified:
            security_logger.warning(f"Unverified user attempting access: {request.user.email}")
            return False
        
        return True


class CanManageUsers(BaseRolePermission):
    """Permission for user management operations"""
    required_roles = ['admin', 'department_head']


class CanViewAnalytics(BaseRolePermission):
    """Permission for viewing analytics and reports"""
    required_roles = ['admin', 'department_head', 'manager']


class DocumentOwnerOrAdmin(permissions.BasePermission):
    """Permission class for document owners or admins"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can access everything
        if request.user.role == 'admin':
            return True
        
        # Document owner can access their documents
        if hasattr(obj, 'owned_by') and obj.owned_by == request.user:
            return True
        
        # Department heads can access documents in their departments
        if request.user.role == 'department_head':
            # Check if user is head of document's department
            if hasattr(obj, 'department'):
                user_departments = request.user.department_assignments.filter(
                    end_date__isnull=True,
                    role='head'
                ).values_list('department', flat=True)
                if obj.department.id in user_departments:
                    return True
        
        # Log permission denial
        security_logger.warning(
            f"Document access denied: {request.user.email} attempted to access "
            f"document {getattr(obj, 'title', 'unknown')}"
        )
        return False


class DocumentSharePermission(permissions.BasePermission):
    """Permission class for document sharing operations"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only document owners, admins, or users with share permission can share
        if request.user.role == 'admin':
            return True
        
        if hasattr(obj, 'owned_by') and obj.owned_by == request.user:
            return True
        
        # Check if user has explicit share permission
        if hasattr(obj, 'permissions'):
            has_share_permission = obj.permissions.filter(
                user=request.user,
                permission='share',
                is_active=True
            ).exists()
            if has_share_permission:
                return True
        
        security_logger.warning(
            f"Share permission denied: {request.user.email} attempted to share "
            f"document {getattr(obj, 'title', 'unknown')}"
        )
        return False


class DepartmentPermission(permissions.BasePermission):
    """Permission class for department-specific operations"""
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin can access all departments
        if request.user.role == 'admin':
            return True
        
        # Department heads can manage their own departments
        if request.user.role == 'department_head':
            user_departments = request.user.department_assignments.filter(
                end_date__isnull=True,
                role='head'
            ).values_list('department', flat=True)
            if obj.id in user_departments:
                return True
        
        # Regular users can view departments they belong to
        if view.action in ['retrieve', 'list']:
            user_departments = request.user.department_assignments.filter(
                end_date__isnull=True
            ).values_list('department', flat=True)
            if obj.id in user_departments:
                return True
        
        return False


def check_role_permission(user, required_roles, action_description=""):
    """
    Helper function to check role permissions and log security events
    
    Args:
        user: User object
        required_roles: List of required roles
        action_description: Description of the action for logging
    
    Returns:
        bool: True if user has permission, False otherwise
    
    Raises:
        PermissionDenied: If permission is denied
    """
    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication required")
    
    if not user.is_verified:
        security_logger.warning(f"Unverified user attempting {action_description}: {user.email}")
        raise PermissionDenied("Email verification required")
    
    if user.role not in required_roles:
        security_logger.warning(
            f"Permission denied: {user.email} (role: {user.role}) "
            f"attempted {action_description} requiring roles: {required_roles}"
        )
        raise PermissionDenied(f"Insufficient permissions. Required roles: {', '.join(required_roles)}")
    
    return True


def log_security_event(user, action, resource=None, success=True, details=""):
    """
    Log security-related events for audit purposes
    
    Args:
        user: User object
        action: Action performed
        resource: Resource affected (optional)
        success: Whether the action was successful
        details: Additional details
    """
    status = "SUCCESS" if success else "FAILURE"
    resource_info = f" on {resource}" if resource else ""
    
    security_logger.info(
        f"{status}: {user.email} (role: {user.role}) "
        f"performed {action}{resource_info}. {details}"
    ) 