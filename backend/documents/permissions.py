"""
Custom permission classes for document operations
"""
from rest_framework import permissions
from departments.models import Permission
from .utils import user_has_permission
import logging

logger = logging.getLogger(__name__)

class HasDocumentPermission(permissions.BasePermission):
    """
    Custom permission class that checks our custom permission system
    """
    
    # Map actions to required permissions
    PERMISSION_MAP = {
        'list': 'documents.view_all',
        'retrieve': 'documents.view_all', 
        'create': 'documents.create',
        'update': 'documents.edit_all',
        'partial_update': 'documents.edit_all',
        'destroy': 'documents.delete_all',
        'download': 'documents.view_all',  # For now, viewing allows download
        'share': 'documents.share',
        'approve': 'documents.approve',
    }
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has basic access"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin always has access
        if request.user.role == 'admin':
            return True
            
        # Get the action being performed
        action = getattr(view, 'action', None)
        if not action:
            # For function-based views, try to infer from method and view name
            if hasattr(view, 'get_view_name'):
                view_name = view.get_view_name().lower()
                if 'download' in view_name:
                    action = 'download'
                elif 'preview' in view_name:
                    action = 'retrieve'
                elif request.method == 'POST':
                    action = 'create'
                elif request.method in ['PUT', 'PATCH']:
                    action = 'update'
                elif request.method == 'DELETE':
                    action = 'destroy'
                else:
                    action = 'retrieve'
        
        # Get required permission for this action
        required_permission = self.PERMISSION_MAP.get(action, 'documents.view_all')
        
        # Check if user has the required permission
        has_perm = user_has_permission(request.user, required_permission)
        
        if not has_perm:
            logger.warning(
                f"Permission denied: {request.user.email} attempted {action} "
                f"but lacks {required_permission} permission"
            )
        
        return has_perm
    
    def has_object_permission(self, request, view, obj):
        """Check permissions for specific document objects"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin always has access
        if request.user.role == 'admin':
            return True
        
        # Document owner has access to their own documents
        if hasattr(obj, 'owned_by') and obj.owned_by == request.user:
            return True
        
        # Check the same permission as has_permission
        action = getattr(view, 'action', None)
        if not action:
            if request.method == 'POST':
                action = 'create'
            elif request.method in ['PUT', 'PATCH']:
                action = 'update'
            elif request.method == 'DELETE':
                action = 'destroy'
            else:
                action = 'retrieve'
        
        required_permission = self.PERMISSION_MAP.get(action, 'documents.view_all')
        return user_has_permission(request.user, required_permission)

class CanCreateDocuments(permissions.BasePermission):
    """Check if user can create documents"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
            
        return user_has_permission(request.user, 'documents.create')

class CanViewAllDocuments(permissions.BasePermission):
    """Check if user can view all documents"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
            
        return user_has_permission(request.user, 'documents.view_all')

class CanEditAllDocuments(permissions.BasePermission):
    """Check if user can edit all documents"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
            
        return user_has_permission(request.user, 'documents.edit_all')

class CanDeleteAllDocuments(permissions.BasePermission):
    """Check if user can delete all documents"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
            
        return user_has_permission(request.user, 'documents.delete_all')

class CanShareDocuments(permissions.BasePermission):
    """Check if user can share documents"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
            
        return user_has_permission(request.user, 'documents.share')

class CanApproveDocuments(permissions.BasePermission):
    """Check if user can approve documents"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
            
        return user_has_permission(request.user, 'documents.approve') 