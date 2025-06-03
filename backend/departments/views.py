from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import Department, Position, EmployeeDepartment, DepartmentBudget, Permission, PermissionTemplate, PermissionAuditLog, SystemSettings, SystemBackup
from .serializers import (
    DepartmentSerializer, 
    DepartmentListSerializer, 
    DepartmentTreeSerializer,
    PositionSerializer,
    EmployeeDepartmentSerializer,
    DepartmentBudgetSerializer
)
from django.contrib.auth import get_user_model
from datetime import date
import logging
import os
import json
import hashlib
import zipfile
import tempfile
from django.core.management import call_command
from django.conf import settings as django_settings
from django.utils import timezone
from django.http import HttpResponse, FileResponse

logger = logging.getLogger(__name__)
User = get_user_model()

def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class DepartmentListView(generics.ListAPIView):
    """API view to list all active departments"""
    queryset = Department.objects.filter(is_active=True).order_by('name')
    serializer_class = DepartmentListSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            departments = self.get_queryset()
            serializer = self.get_serializer(departments, many=True)
            logger.info(f"Departments API called by {request.user.email}, returning {departments.count()} departments")
            return Response({
                'results': serializer.data,
                'count': departments.count()
            })
        except Exception as e:
            logger.error(f"Error in DepartmentListView: {e}")
            return Response({'error': 'Failed to fetch departments'}, status=500)

class DepartmentDetailView(generics.RetrieveAPIView):
    """API view to get a specific department"""
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_tree(request):
    """Get department hierarchy tree"""
    try:
        # Get root departments (no parent)
        root_departments = Department.objects.filter(
            parent_department__isnull=True, 
            is_active=True
        ).order_by('name')
        
        serializer = DepartmentTreeSerializer(root_departments, many=True)
        logger.info(f"Department tree requested by {request.user.email}")
        return Response(serializer.data)
    except Exception as e:
        logger.error(f"Error in department_tree: {e}")
        return Response({'error': 'Failed to fetch department tree'}, status=500)

class DepartmentCreateView(generics.CreateAPIView):
    """Create a new department (admin only)"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Only admins can create departments
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can create departments")
        serializer.save()

class DepartmentUpdateView(generics.UpdateAPIView):
    """Update a department (admin only)"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Only admins can update departments
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can update departments")
        return super().get_object()

class DepartmentDeleteView(generics.DestroyAPIView):
    """Delete a department (admin only)"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        # Only admins can delete departments
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can delete departments")
        
        department = super().get_object()
        
        # Check if department has employees
        if department.employees.filter(end_date__isnull=True).exists():
            from django.core.exceptions import ValidationError
            raise ValidationError("Cannot delete department with active employees")
        
        return department

class PositionListView(generics.ListAPIView):
    queryset = Position.objects.filter(is_active=True)
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]

class PositionCreateView(generics.CreateAPIView):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can create positions")
        serializer.save()

class PositionDetailView(generics.RetrieveAPIView):
    queryset = Position.objects.filter(is_active=True)
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]

class PositionUpdateView(generics.UpdateAPIView):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can update positions")
        return super().get_object()

class PositionDeleteView(generics.DestroyAPIView):
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can delete positions")
        return super().get_object()

class EmployeeAssignmentListView(generics.ListAPIView):
    queryset = EmployeeDepartment.objects.all()
    serializer_class = EmployeeDepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        department_id = self.request.query_params.get('department_id')
        if department_id:
            return EmployeeDepartment.objects.filter(
                department_id=department_id,
                end_date__isnull=True
            ).order_by('-start_date')
        return EmployeeDepartment.objects.filter(end_date__isnull=True).order_by('-start_date')

class EmployeeAssignmentCreateView(generics.CreateAPIView):
    queryset = EmployeeDepartment.objects.all()
    serializer_class = EmployeeDepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can assign employees to departments")
        
        # Set start_date to today if not provided
        if not serializer.validated_data.get('start_date'):
            serializer.validated_data['start_date'] = date.today()
        
        serializer.save()

class EmployeeAssignmentDetailView(generics.RetrieveAPIView):
    queryset = EmployeeDepartment.objects.all()
    serializer_class = EmployeeDepartmentSerializer
    permission_classes = [IsAuthenticated]

class EmployeeAssignmentUpdateView(generics.UpdateAPIView):
    queryset = EmployeeDepartment.objects.all()
    serializer_class = EmployeeDepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        if self.request.user.role != 'admin':
            raise permissions.PermissionDenied("Only admins can update employee assignments")
        return super().get_object()

class DepartmentBudgetListView(generics.ListAPIView):
    queryset = DepartmentBudget.objects.all()
    serializer_class = DepartmentBudgetSerializer
    permission_classes = [IsAuthenticated]

class DepartmentBudgetCreateView(generics.CreateAPIView):
    queryset = DepartmentBudget.objects.all()
    serializer_class = DepartmentBudgetSerializer
    permission_classes = [IsAuthenticated]

class DepartmentBudgetDetailView(generics.RetrieveAPIView):
    queryset = DepartmentBudget.objects.all()
    serializer_class = DepartmentBudgetSerializer
    permission_classes = [IsAuthenticated]

class DepartmentBudgetUpdateView(generics.UpdateAPIView):
    queryset = DepartmentBudget.objects.all()
    serializer_class = DepartmentBudgetSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_stats(request):
    """Get department statistics"""
    try:
        total_departments = Department.objects.filter(is_active=True).count()
        total_positions = Position.objects.filter(is_active=True).count()
        
        return Response({
            'total_departments': total_departments,
            'total_positions': total_positions,
            'message': 'Department statistics'
        })
    except Exception as e:
        logger.error(f"Error in department_stats: {e}")
        return Response({'error': 'Failed to fetch department stats'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_employees(request, department_id):
    """Get employees in a specific department"""
    try:
        department = Department.objects.get(id=department_id, is_active=True)
        employees = department.get_all_employees()
        
        return Response({
            'department': department.name,
            'employees_count': len(employees),
            'message': f'Department {department.name} employees'
        })
    except Department.DoesNotExist:
        return Response({'error': 'Department not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in department_employees: {e}")
        return Response({'error': 'Failed to fetch department employees'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_assignment(request, pk):
    """End an employee assignment"""
    try:
        if request.user.role != 'admin':
            return Response({'error': 'Only admins can end assignments'}, status=403)
        
        assignment = EmployeeDepartment.objects.get(id=pk, end_date__isnull=True)
        assignment.end_date = date.today()
        assignment.save()
        
        logger.info(f"Assignment ended by {request.user.email} for assignment {pk}")
        return Response({'message': 'Assignment ended successfully'})
    except EmployeeDepartment.DoesNotExist:
        return Response({'error': 'Assignment not found or already ended'}, status=404)
    except Exception as e:
        logger.error(f"Error ending assignment: {e}")
        return Response({'error': 'Failed to end assignment'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_employees(request):
    """Get employees available for department assignment"""
    try:
        # Get all active users who are not assigned to any department
        assigned_employee_ids = EmployeeDepartment.objects.filter(
            end_date__isnull=True
        ).values_list('employee_id', flat=True)
        
        available_users = User.objects.filter(
            is_active=True
        ).exclude(id__in=assigned_employee_ids).order_by('first_name', 'last_name')
        
        users_data = []
        for user in available_users:
            users_data.append({
                'id': str(user.id),
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'role': user.role
            })
        
        return Response({
            'results': users_data,
            'count': len(users_data)
        })
    except Exception as e:
        logger.error(f"Error fetching available employees: {e}")
        return Response({'error': 'Failed to fetch available employees'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_budget(request, pk):
    return Response({'message': 'Approve budget endpoint'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organization_chart(request):
    return Response({'message': 'Organization chart endpoint'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_report(request):
    return Response({'message': 'Performance report endpoint'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_utilization_report(request):
    """Get budget utilization report"""
    try:
        # Mock data for now
        report_data = {
            'total_budget': 1000000.00,
            'allocated_budget': 850000.00,
            'spent_budget': 650000.00,
            'utilization_percentage': 76.5,
            'departments': [
                {'name': 'IT', 'allocated': 300000, 'spent': 250000, 'utilization': 83.3},
                {'name': 'HR', 'allocated': 150000, 'spent': 120000, 'utilization': 80.0},
                {'name': 'Finance', 'allocated': 200000, 'spent': 180000, 'utilization': 90.0},
            ]
        }
        
        logger.info(f"Budget utilization report requested by {request.user.email}")
        return Response(report_data)
    except Exception as e:
        logger.error(f"Error in budget_utilization_report: {e}")
        return Response({'error': 'Failed to generate budget utilization report'}, status=500)

# Permissions Management Views

class PermissionListView(generics.ListAPIView):
    """List all permissions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=403)
        
        try:
            permissions = Permission.objects.filter(is_active=True).order_by('-granted_at')
            
            data = []
            for perm in permissions:
                # Get entity name based on type
                entity_name = "Unknown"
                if perm.entity_type == 'user':
                    try:
                        user = User.objects.get(id=perm.entity_id)
                        entity_name = user.get_full_name() or user.email
                    except User.DoesNotExist:
                        entity_name = "User not found"
                elif perm.entity_type == 'department':
                    try:
                        dept = Department.objects.get(id=perm.entity_id)
                        entity_name = dept.name
                    except Department.DoesNotExist:
                        entity_name = "Department not found"
                elif perm.entity_type == 'category':
                    try:
                        from documents.models import DocumentCategory
                        cat = DocumentCategory.objects.get(id=perm.entity_id)
                        entity_name = cat.name
                    except:
                        entity_name = "Category not found"
                
                data.append({
                    'id': str(perm.id),
                    'entity_type': perm.entity_type,
                    'entity_id': str(perm.entity_id),
                    'entity_name': entity_name,
                    'permission': perm.permission,
                    'permission_category': perm.permission_category,
                    'granted_by': perm.granted_by.get_full_name() or perm.granted_by.email,
                    'granted_at': perm.granted_at,
                    'is_active': perm.is_active,
                    'expires_at': perm.expires_at,
                    'notes': perm.notes
                })
            
            return Response({'results': data})
        except Exception as e:
            logger.error(f"Error in PermissionListView: {e}")
            return Response({'error': 'Failed to fetch permissions'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def entity_permissions(request, entity_type, entity_id):
    """Get permissions for a specific entity"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        permissions = Permission.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id,
            is_active=True
        ).order_by('-granted_at')
        
        data = []
        for perm in permissions:
            data.append({
                'id': str(perm.id),
                'permission': perm.permission,
                'permission_category': perm.permission_category,
                'granted_by': perm.granted_by.get_full_name() or perm.granted_by.email,
                'granted_at': perm.granted_at,
                'expires_at': perm.expires_at,
                'notes': perm.notes
            })
        
        return Response({'results': data})
    except Exception as e:
        logger.error(f"Error in entity_permissions: {e}")
        return Response({'error': 'Failed to fetch entity permissions'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def grant_permission(request):
    """Grant permission to an entity"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        entity_type = request.data.get('entityType')
        entity_id = request.data.get('entityId')
        permission_key = request.data.get('permission')
        
        if not all([entity_type, entity_id, permission_key]):
            return Response({'error': 'Missing required fields'}, status=400)
        
        # Determine permission category
        permission_category = permission_key.split('.')[0] if '.' in permission_key else 'system'
        
        # Create permission
        permission, created = Permission.objects.get_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            permission=permission_key,
            defaults={
                'permission_category': permission_category,
                'granted_by': request.user,
                'notes': request.data.get('notes', '')
            }
        )
        
        if not created:
            # Update existing permission
            permission.is_active = True
            permission.granted_by = request.user
            permission.save()
        
        # Log the action
        PermissionAuditLog.objects.create(
            action='grant',
            permission=permission_key,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            notes=f"Permission granted via admin interface"
        )
        
        return Response({
            'id': str(permission.id),
            'message': 'Permission granted successfully'
        })
    except Exception as e:
        logger.error(f"Error in grant_permission: {e}")
        return Response({'error': 'Failed to grant permission'}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def revoke_permission(request, permission_id):
    """Revoke a permission"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        permission = Permission.objects.get(id=permission_id)
        
        # Log the action before deletion
        PermissionAuditLog.objects.create(
            action='revoke',
            permission=permission.permission,
            entity_type=permission.entity_type,
            entity_id=permission.entity_id,
            performed_by=request.user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            notes=f"Permission revoked via admin interface"
        )
        
        permission.delete()
        
        return Response({'message': 'Permission revoked successfully'})
    except Permission.DoesNotExist:
        return Response({'error': 'Permission not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in revoke_permission: {e}")
        return Response({'error': 'Failed to revoke permission'}, status=500)

class PermissionTemplateListView(generics.ListAPIView):
    """List permission templates"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        if request.user.role != 'admin':
            return Response({'error': 'Admin access required'}, status=403)
        
        try:
            templates = PermissionTemplate.objects.filter(is_active=True).order_by('name')
            
            data = []
            for template in templates:
                data.append({
                    'id': str(template.id),
                    'name': template.name,
                    'description': template.description,
                    'permissions': template.permissions,
                    'created_by': template.created_by.get_full_name() or template.created_by.email,
                    'created_at': template.created_at,
                    'usage_count': template.usage_count
                })
            
            return Response({'results': data})
        except Exception as e:
            logger.error(f"Error in PermissionTemplateListView: {e}")
            return Response({'error': 'Failed to fetch permission templates'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_permission_template(request):
    """Create a new permission template"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        name = request.data.get('name')
        description = request.data.get('description')
        permissions = request.data.get('permissions', [])
        
        if not all([name, description]):
            return Response({'error': 'Name and description are required'}, status=400)
        
        template = PermissionTemplate.objects.create(
            name=name,
            description=description,
            permissions=permissions,
            created_by=request.user
        )
        
        # Log the action
        PermissionAuditLog.objects.create(
            action='template_create',
            permission=f'template:{template.name}',
            entity_type='template',
            entity_id=template.id,
            performed_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'template_name': name,
                'permissions_count': len(permissions),
                'permissions': permissions
            }
        )
        
        return Response({
            'id': str(template.id),
            'message': 'Permission template created successfully',
            'template': {
                'id': str(template.id),
                'name': template.name,
                'description': template.description,
                'permissions': template.permissions,
                'created_by': template.created_by.get_full_name() or template.created_by.email,
                'created_at': template.created_at,
                'usage_count': 0
            }
        })
    except Exception as e:
        logger.error(f"Error in create_permission_template: {e}")
        return Response({'error': 'Failed to create permission template'}, status=500)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_permission_template(request, template_id):
    """Update an existing permission template"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        template = PermissionTemplate.objects.get(id=template_id)
        
        name = request.data.get('name', template.name)
        description = request.data.get('description', template.description)
        permissions = request.data.get('permissions', template.permissions)
        
        old_data = {
            'name': template.name,
            'description': template.description,
            'permissions': template.permissions
        }
        
        template.name = name
        template.description = description
        template.permissions = permissions
        template.save()
        
        # Log the action
        PermissionAuditLog.objects.create(
            action='template_update',
            permission=f'template:{template.name}',
            entity_type='template',
            entity_id=template.id,
            performed_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'old_data': old_data,
                'new_data': {
                    'name': name,
                    'description': description,
                    'permissions': permissions
                }
            }
        )
        
        return Response({
            'message': 'Permission template updated successfully',
            'template': {
                'id': str(template.id),
                'name': template.name,
                'description': template.description,
                'permissions': template.permissions,
                'created_by': template.created_by.get_full_name() or template.created_by.email,
                'created_at': template.created_at,
                'usage_count': template.usage_count
            }
        })
    except PermissionTemplate.DoesNotExist:
        return Response({'error': 'Permission template not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in update_permission_template: {e}")
        return Response({'error': 'Failed to update permission template'}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_permission_template(request, template_id):
    """Delete a permission template"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        template = PermissionTemplate.objects.get(id=template_id)
        
        # Store template info for logging
        template_info = {
            'name': template.name,
            'description': template.description,
            'permissions': template.permissions,
            'usage_count': template.usage_count
        }
        
        # Check if template is in use
        if template.usage_count > 0:
            return Response({
                'error': f'Cannot delete template "{template.name}" as it is currently applied to {template.usage_count} users. Remove template from users first.'
            }, status=400)
        
        # Log the action before deletion
        PermissionAuditLog.objects.create(
            action='template_delete',
            permission=f'template:{template.name}',
            entity_type='template',
            entity_id=template.id,
            performed_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata=template_info
        )
        
        template.delete()
        
        return Response({'message': 'Permission template deleted successfully'})
    except PermissionTemplate.DoesNotExist:
        return Response({'error': 'Permission template not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in delete_permission_template: {e}")
        return Response({'error': 'Failed to delete permission template'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_template_to_users(request, template_id):
    """Apply a permission template to multiple users"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        template = PermissionTemplate.objects.get(id=template_id)
        user_ids = request.data.get('user_ids', [])
        overwrite = request.data.get('overwrite', False)  # Whether to overwrite existing permissions
        
        if not user_ids:
            return Response({'error': 'No users specified'}, status=400)
        
        # Validate users exist
        users = User.objects.filter(id__in=user_ids)
        if users.count() != len(user_ids):
            return Response({'error': 'Some specified users do not exist'}, status=400)
        
        applied_count = 0
        skipped_count = 0
        errors = []
        
        for user in users:
            try:
                permissions_created = 0
                
                for permission_key in template.permissions:
                    # Check if user already has this permission
                    existing_permission = Permission.objects.filter(
                        entity_type='user',
                        entity_id=user.id,
                        permission=permission_key,
                        is_active=True
                    ).first()
                    
                    if existing_permission and not overwrite:
                        skipped_count += 1
                        continue
                    
                    if existing_permission and overwrite:
                        # Update existing permission
                        existing_permission.granted_by = request.user
                        existing_permission.notes = f'Updated by template: {template.name}'
                        existing_permission.save()
                    else:
                        # Create new permission
                        permission_category = permission_key.split('.')[0] if '.' in permission_key else 'system'
                        
                        Permission.objects.create(
                            entity_type='user',
                            entity_id=user.id,
                            permission=permission_key,
                            permission_category=permission_category,
                            granted_by=request.user,
                            notes=f'Applied from template: {template.name}'
                        )
                    
                    permissions_created += 1
                
                if permissions_created > 0:
                    applied_count += 1
                    
                    # Log the template application
                    PermissionAuditLog.objects.create(
                        action='template_apply',
                        permission=f'template:{template.name}',
                        entity_type='user',
                        entity_id=user.id,
                        performed_by=request.user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'template_name': template.name,
                            'permissions_applied': permissions_created,
                            'user_email': user.email,
                            'overwrite': overwrite
                        }
                    )
                    
            except Exception as e:
                errors.append(f'Error applying template to {user.email}: {str(e)}')
                logger.error(f"Error applying template to user {user.id}: {e}")
        
        # Update template usage count
        template.usage_count = Permission.objects.filter(
            notes__icontains=f'template: {template.name}'
        ).values('entity_id').distinct().count()
        template.save()
        
        result = {
            'message': f'Template applied successfully to {applied_count} users',
            'applied_count': applied_count,
            'skipped_count': skipped_count,
            'template_name': template.name
        }
        
        if errors:
            result['errors'] = errors
        
        return Response(result)
        
    except PermissionTemplate.DoesNotExist:
        return Response({'error': 'Permission template not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in apply_template_to_users: {e}")
        return Response({'error': 'Failed to apply permission template'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_permissions(request):
    """Get all available permissions in the system"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        # Define all available permissions categorized
        available_permissions = {
            'documents': [
                {'key': 'documents.view_all', 'name': 'View All Documents', 'description': 'Can view all documents regardless of category'},
                {'key': 'documents.create', 'name': 'Create Documents', 'description': 'Can upload and create new documents'},
                {'key': 'documents.edit_all', 'name': 'Edit All Documents', 'description': 'Can edit any document in the system'},
                {'key': 'documents.delete_all', 'name': 'Delete All Documents', 'description': 'Can delete any document in the system'},
                {'key': 'documents.approve', 'name': 'Approve Documents', 'description': 'Can approve documents for publication'},
                {'key': 'documents.share', 'name': 'Share Documents', 'description': 'Can share documents with users and departments'},
            ],
            'categories': [
                {'key': 'categories.view_all', 'name': 'View All Categories', 'description': 'Can view all document categories'},
                {'key': 'categories.create', 'name': 'Create Categories', 'description': 'Can create new document categories'},
                {'key': 'categories.edit', 'name': 'Edit Categories', 'description': 'Can modify existing categories'},
                {'key': 'categories.delete', 'name': 'Delete Categories', 'description': 'Can delete categories'},
                {'key': 'categories.assign', 'name': 'Assign Categories', 'description': 'Can assign categories to documents'},
            ],
            'departments': [
                {'key': 'departments.view_all', 'name': 'View All Departments', 'description': 'Can view all department information'},
                {'key': 'departments.manage', 'name': 'Manage Departments', 'description': 'Can create, edit, and delete departments'},
                {'key': 'departments.assign_users', 'name': 'Assign Users', 'description': 'Can assign users to departments'},
                {'key': 'departments.view_employees', 'name': 'View Department Employees', 'description': 'Can see employee lists in departments'},
            ],
            'users': [
                {'key': 'users.view_all', 'name': 'View All Users', 'description': 'Can view all user profiles and information'},
                {'key': 'users.create', 'name': 'Create Users', 'description': 'Can create new user accounts'},
                {'key': 'users.edit', 'name': 'Edit Users', 'description': 'Can modify user accounts and profiles'},
                {'key': 'users.deactivate', 'name': 'Deactivate Users', 'description': 'Can deactivate user accounts'},
                {'key': 'users.assign_roles', 'name': 'Assign Roles', 'description': 'Can change user roles and permissions'},
            ],
            'system': [
                {'key': 'system.admin_settings', 'name': 'Admin Settings', 'description': 'Can access admin settings panel'},
                {'key': 'system.view_analytics', 'name': 'View Analytics', 'description': 'Can view system analytics and reports'},
                {'key': 'system.manage_settings', 'name': 'Manage Settings', 'description': 'Can modify system configuration'},
                {'key': 'system.backup', 'name': 'Backup Management', 'description': 'Can manage system backups'},
            ]
        }
        
        return Response({'available_permissions': available_permissions})
        
    except Exception as e:
        logger.error(f"Error in get_available_permissions: {e}")
        return Response({'error': 'Failed to get available permissions'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def permission_report(request):
    """Generate permissions report"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        # Get summary statistics
        total_permissions = Permission.objects.filter(is_active=True).count()
        user_permissions = Permission.objects.filter(entity_type='user', is_active=True).count()
        dept_permissions = Permission.objects.filter(entity_type='department', is_active=True).count()
        category_permissions = Permission.objects.filter(entity_type='category', is_active=True).count()
        
        # Get permission categories breakdown
        from django.db.models import Count
        category_breakdown = Permission.objects.filter(is_active=True).values(
            'permission_category'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Get recent activities
        recent_logs = PermissionAuditLog.objects.order_by('-performed_at')[:10]
        recent_activities = []
        for log in recent_logs:
            recent_activities.append({
                'action': log.action,
                'permission': log.permission,
                'entity_type': log.entity_type,
                'performed_by': log.performed_by.get_full_name() or log.performed_by.email,
                'performed_at': log.performed_at,
                'notes': log.notes
            })
        
        report_data = {
            'summary': {
                'total_permissions': total_permissions,
                'user_permissions': user_permissions,
                'department_permissions': dept_permissions,
                'category_permissions': category_permissions
            },
            'category_breakdown': list(category_breakdown),
            'recent_activities': recent_activities,
            'generated_at': date.today(),
            'generated_by': request.user.get_full_name() or request.user.email
        }
        
        return Response(report_data)
    except Exception as e:
        logger.error(f"Error in permission_report: {e}")
        return Response({'error': 'Failed to generate permission report'}, status=500)

class PermissionRevokeView(APIView):
    """Revoke a permission (admin only)"""
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    def delete(self, request, permission_id):
        try:
            permission = Permission.objects.get(id=permission_id)
            
            # Log the revocation
            PermissionAuditLog.objects.create(
                action='REVOKE',
                permission=permission.permission,
                entity_type=permission.entity_type,
                entity_id=permission.entity_id,
                performed_by=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'permission_id': str(permission.id),
                    'original_granted_by': str(permission.granted_by.id),
                    'original_granted_at': permission.created_at.isoformat()
                }
            )
            
            permission.delete()
            
            return Response({
                'message': 'Permission revoked successfully',
                'permission_id': permission_id
            })
            
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error revoking permission {permission_id}: {str(e)}")
            return Response(
                {'error': 'Failed to revoke permission'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserPermissionsView(APIView):
    """Get current user's permissions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all permissions for the current user"""
        try:
            user = request.user
            user_permissions = []
            
            # Admin users have all permissions
            if user.role == 'admin':
                all_permissions = [
                    'documents.view_all', 'documents.create', 'documents.edit_all', 'documents.delete_all',
                    'documents.approve', 'documents.share', 'categories.view_all', 'categories.create',
                    'categories.edit', 'categories.delete', 'categories.assign', 'departments.view_all',
                    'departments.manage', 'departments.assign_users', 'departments.view_employees',
                    'users.view_all', 'users.create', 'users.edit', 'users.deactivate', 'users.assign_roles',
                    'system.admin_settings', 'system.view_analytics', 'system.manage_settings', 'system.backup'
                ]
                return Response({'permissions': all_permissions})
            
            # Get direct user permissions
            direct_permissions = Permission.objects.filter(
                entity_type='user',
                entity_id=user.id,
                is_active=True
            ).values_list('permission', flat=True)
            
            user_permissions.extend(direct_permissions)
            
            # Get department permissions
            user_departments = user.department_assignments.filter(
                end_date__isnull=True
            ).values_list('department_id', flat=True)
            
            department_permissions = Permission.objects.filter(
                entity_type='department',
                entity_id__in=user_departments,
                is_active=True
            ).values_list('permission', flat=True)
            
            user_permissions.extend(department_permissions)
            
            # Remove duplicates
            unique_permissions = list(set(user_permissions))
            
            return Response({'permissions': unique_permissions})
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {str(e)}")
            return Response(
                {'error': 'Failed to get user permissions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# System Settings Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_system_settings(request):
    """Get current system settings"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        settings_obj = SystemSettings.get_settings()
        if not settings_obj:
            # Create default settings
            settings_obj = SystemSettings.objects.create(
                updated_by=request.user
            )
        
        return Response({
            'site_name': settings_obj.site_name,
            'max_file_size': str(settings_obj.max_file_size),
            'allowed_file_types': settings_obj.allowed_file_types,
            'enable_ai_chat': settings_obj.enable_ai_chat,
            'enable_document_sharing': settings_obj.enable_document_sharing,
            'require_document_approval': settings_obj.require_document_approval,
            'auto_backup_enabled': settings_obj.auto_backup_enabled,
            'backup_frequency': settings_obj.backup_frequency,
            'backup_retention_days': settings_obj.backup_retention_days,
            'password_expiry_days': settings_obj.password_expiry_days,
            'max_login_attempts': settings_obj.max_login_attempts,
            'updated_at': settings_obj.updated_at,
            'updated_by': settings_obj.updated_by.get_full_name() or settings_obj.updated_by.email
        })
        
    except Exception as e:
        logger.error(f"Error getting system settings: {e}")
        return Response({'error': 'Failed to get system settings'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_system_settings(request):
    """Update system settings"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        settings_obj = SystemSettings.get_settings()
        if not settings_obj:
            settings_obj = SystemSettings.objects.create(updated_by=request.user)
        
        # Update fields
        if 'site_name' in request.data:
            settings_obj.site_name = request.data['site_name']
        if 'max_file_size' in request.data:
            settings_obj.max_file_size = int(request.data['max_file_size'])
        if 'allowed_file_types' in request.data:
            settings_obj.allowed_file_types = request.data['allowed_file_types']
        if 'enable_ai_chat' in request.data:
            settings_obj.enable_ai_chat = request.data['enable_ai_chat']
        if 'enable_document_sharing' in request.data:
            settings_obj.enable_document_sharing = request.data['enable_document_sharing']
        if 'require_document_approval' in request.data:
            settings_obj.require_document_approval = request.data['require_document_approval']
        if 'auto_backup_enabled' in request.data:
            settings_obj.auto_backup_enabled = request.data['auto_backup_enabled']
        if 'backup_frequency' in request.data:
            settings_obj.backup_frequency = request.data['backup_frequency']
        if 'backup_retention_days' in request.data:
            settings_obj.backup_retention_days = int(request.data['backup_retention_days'])
        if 'password_expiry_days' in request.data:
            settings_obj.password_expiry_days = int(request.data['password_expiry_days'])
        if 'max_login_attempts' in request.data:
            settings_obj.max_login_attempts = int(request.data['max_login_attempts'])
        
        settings_obj.updated_by = request.user
        settings_obj.clean()  # Validate
        settings_obj.save()
        
        # Log the action
        PermissionAuditLog.objects.create(
            action='settings_update',
            permission='system.manage_settings',
            entity_type='system',
            entity_id=settings_obj.id,
            performed_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'settings_updated': list(request.data.keys()),
                'site_name': settings_obj.site_name
            }
        )
        
        return Response({
            'message': 'System settings updated successfully',
            'settings': {
                'site_name': settings_obj.site_name,
                'max_file_size': str(settings_obj.max_file_size),
                'allowed_file_types': settings_obj.allowed_file_types,
                'enable_ai_chat': settings_obj.enable_ai_chat,
                'enable_document_sharing': settings_obj.enable_document_sharing,
                'require_document_approval': settings_obj.require_document_approval,
                'auto_backup_enabled': settings_obj.auto_backup_enabled,
                'backup_frequency': settings_obj.backup_frequency
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating system settings: {e}")
        return Response({'error': f'Failed to update system settings: {str(e)}'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_system_backup(request):
    """Create a system backup"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        # Create backup record
        backup_name = request.data.get('name', f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}")
        
        backup = SystemBackup.objects.create(
            name=backup_name,
            backup_type='manual',
            created_by=request.user,
            includes_documents=request.data.get('include_documents', True),
            includes_database=request.data.get('include_database', True),
            includes_settings=request.data.get('include_settings', True),
            includes_user_data=request.data.get('include_user_data', True)
        )
        
        backup.started_at = timezone.now()
        backup.status = 'in_progress'
        backup.save()
        
        try:
            # Create backup directory
            backup_dir = os.path.join(django_settings.MEDIA_ROOT, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_filename = f"{backup_name}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Create backup zip file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                
                # Include database dump
                if backup.includes_database:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_db:
                        call_command('dumpdata', '--indent=2', stdout=temp_db)
                        zipf.write(temp_db.name, 'database.json')
                        os.unlink(temp_db.name)
                
                # Include system settings
                if backup.includes_settings:
                    settings_data = {
                        'system_settings': {},
                        'django_settings': {
                            'SECRET_KEY': '[REDACTED]',  # Don't include secret key
                            'DEBUG': django_settings.DEBUG,
                            'ALLOWED_HOSTS': django_settings.ALLOWED_HOSTS,
                            'TIME_ZONE': django_settings.TIME_ZONE,
                        }
                    }
                    
                    settings_obj = SystemSettings.get_settings()
                    if settings_obj:
                        settings_data['system_settings'] = {
                            'site_name': settings_obj.site_name,
                            'max_file_size': settings_obj.max_file_size,
                            'allowed_file_types': settings_obj.allowed_file_types,
                            'enable_ai_chat': settings_obj.enable_ai_chat,
                            'enable_document_sharing': settings_obj.enable_document_sharing,
                            'require_document_approval': settings_obj.require_document_approval,
                            'auto_backup_enabled': settings_obj.auto_backup_enabled,
                            'backup_frequency': settings_obj.backup_frequency
                        }
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_settings:
                        json.dump(settings_data, temp_settings, indent=2, default=str)
                        zipf.write(temp_settings.name, 'settings.json')
                        os.unlink(temp_settings.name)
                
                # Include document files
                if backup.includes_documents:
                    from documents.models import Document
                    documents = Document.objects.all()
                    for doc in documents:
                        if doc.file and os.path.exists(doc.file.path):
                            zipf.write(doc.file.path, f"documents/{doc.file.name}")
                
                # Create backup metadata
                metadata = {
                    'backup_name': backup_name,
                    'created_at': backup.created_at.isoformat(),
                    'created_by': backup.created_by.email,
                    'includes': {
                        'documents': backup.includes_documents,
                        'database': backup.includes_database,
                        'settings': backup.includes_settings,
                        'user_data': backup.includes_user_data
                    },
                    'statistics': {
                        'total_documents': backup.total_documents,
                        'total_users': backup.total_users,
                        'total_departments': backup.total_departments
                    }
                }
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_meta:
                    json.dump(metadata, temp_meta, indent=2)
                    zipf.write(temp_meta.name, 'metadata.json')
                    os.unlink(temp_meta.name)
            
            # Calculate file size and checksum
            file_size = os.path.getsize(backup_path)
            
            with open(backup_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            
            # Update backup record
            backup.file_path = backup_path
            backup.file_size = file_size
            backup.checksum = checksum
            backup.status = 'completed'
            backup.completed_at = timezone.now()
            
            # Get statistics
            from documents.models import Document
            backup.total_documents = Document.objects.count()
            backup.total_users = User.objects.count()
            backup.total_departments = Department.objects.count()
            
            backup.save()
            
            logger.info(f"System backup created successfully: {backup_name} by {request.user.email}")
            
            return Response({
                'message': 'System backup created successfully',
                'backup': {
                    'id': str(backup.id),
                    'name': backup.name,
                    'file_size_mb': backup.file_size_mb,
                    'status': backup.status,
                    'created_at': backup.created_at,
                    'duration': str(backup.duration) if backup.duration else None
                }
            })
            
        except Exception as e:
            # Update backup record with error
            backup.status = 'failed'
            backup.error_message = str(e)
            backup.completed_at = timezone.now()
            backup.save()
            
            logger.error(f"Backup creation failed: {e}")
            return Response({'error': f'Backup creation failed: {str(e)}'}, status=500)
        
    except Exception as e:
        logger.error(f"Error creating system backup: {e}")
        return Response({'error': 'Failed to create system backup'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_system_backups(request):
    """List all system backups"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        backups = SystemBackup.objects.all()[:20]  # Latest 20 backups
        
        backup_data = []
        for backup in backups:
            backup_data.append({
                'id': str(backup.id),
                'name': backup.name,
                'backup_type': backup.backup_type,
                'status': backup.status,
                'file_size_mb': backup.file_size_mb,
                'created_by': backup.created_by.get_full_name() or backup.created_by.email,
                'created_at': backup.created_at,
                'completed_at': backup.completed_at,
                'duration': str(backup.duration) if backup.duration else None,
                'error_message': backup.error_message,
                'includes': {
                    'documents': backup.includes_documents,
                    'database': backup.includes_database,
                    'settings': backup.includes_settings,
                    'user_data': backup.includes_user_data
                },
                'statistics': {
                    'total_documents': backup.total_documents,
                    'total_users': backup.total_users,
                    'total_departments': backup.total_departments
                }
            })
        
        return Response({'backups': backup_data})
        
    except Exception as e:
        logger.error(f"Error listing system backups: {e}")
        return Response({'error': 'Failed to list system backups'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_system_backup(request, backup_id):
    """Download a system backup file"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        backup = SystemBackup.objects.get(id=backup_id)
        
        if backup.status != 'completed':
            return Response({'error': 'Backup is not completed'}, status=400)
        
        if not backup.file_path or not os.path.exists(backup.file_path):
            return Response({'error': 'Backup file not found'}, status=404)
        
        # Log download
        PermissionAuditLog.objects.create(
            action='backup_download',
            permission='system.backup',
            entity_type='backup',
            entity_id=backup.id,
            performed_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'backup_name': backup.name,
                'file_size_mb': backup.file_size_mb
            }
        )
        
        response = FileResponse(
            open(backup.file_path, 'rb'),
            as_attachment=True,
            filename=f"{backup.name}.zip"
        )
        response['Content-Length'] = backup.file_size
        
        return response
        
    except SystemBackup.DoesNotExist:
        return Response({'error': 'Backup not found'}, status=404)
    except Exception as e:
        logger.error(f"Error downloading system backup: {e}")
        return Response({'error': 'Failed to download system backup'}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_system_backup(request, backup_id):
    """Delete a system backup"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        backup = SystemBackup.objects.get(id=backup_id)
        
        # Delete backup file
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        
        # Log deletion
        PermissionAuditLog.objects.create(
            action='backup_delete',
            permission='system.backup',
            entity_type='backup',
            entity_id=backup.id,
            performed_by=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'backup_name': backup.name,
                'file_size_mb': backup.file_size_mb
            }
        )
        
        backup.delete()
        
        return Response({'message': 'Backup deleted successfully'})
        
    except SystemBackup.DoesNotExist:
        return Response({'error': 'Backup not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting system backup: {e}")
        return Response({'error': 'Failed to delete system backup'}, status=500)
