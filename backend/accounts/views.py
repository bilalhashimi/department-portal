from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from .models import User, UserProfile, LoginAttempt
from .serializers import (
    UserSerializer, UserListSerializer, UserProfileSerializer,
    LoginSerializer, ChangePasswordSerializer, UserProfileUpdateSerializer,
    LoginAttemptSerializer, GroupSerializer, GroupMemberSerializer, GroupListSerializer
)
from .permissions import CanManageUsers
from departments.models import Permission
from documents.utils import user_has_permission
import logging

# Setup security logging
security_logger = logging.getLogger('security')
logger = logging.getLogger(__name__)


class EnhancedAccessToken(AccessToken):
    """Enhanced access token with role and department information"""
    
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        # Add custom claims to JWT payload
        token['role'] = user.role
        token['email'] = user.email
        token['is_verified'] = user.is_verified
        token['full_name'] = user.get_full_name()
        return token


class LoginView(TokenObtainPairView):
    """Enhanced login view with comprehensive security features"""
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        # Get client info for security logging
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        email = request.data.get('email', '')
        
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            
            # Additional security checks
            if not user.is_verified:
                security_logger.warning(f"Unverified user login attempt: {email} from {ip_address}")
                return Response(
                    {'error': 'Please verify your email before logging in'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Generate enhanced tokens with role information
            refresh = RefreshToken.for_user(user)
            access = EnhancedAccessToken.for_user(user)
            
            # Log successful login
            LoginAttempt.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                successful=True
            )
            
            security_logger.info(f"Successful login: {user.email} (role: {user.role}) from {ip_address}")
            
            return Response({
                'refresh': str(refresh),
                'access': str(access),
                'user': UserSerializer(user).data,
                'permissions': self.get_user_permissions(user)
            })
            
        except Exception as e:
            # Log failed login attempt with more details
            user = None
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    pass
            
            LoginAttempt.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                successful=False
            )
            
            security_logger.warning(f"Failed login attempt: {email} from {ip_address} - {str(e)}")
            
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_user_permissions(self, user):
        """Get user permissions for frontend authorization"""
        permissions = {
            'can_create_users': user.role in ['admin', 'department_head'],
            'can_manage_departments': user.role == 'admin',
            'can_view_all_documents': user.role == 'admin',
            'can_approve_documents': user.role in ['admin', 'department_head', 'manager'],
            'can_delete_any_document': user.role == 'admin',
            'can_share_documents': True,  # All authenticated users can share
            'can_view_analytics': user.role in ['admin', 'department_head', 'manager'],
            'can_access_admin_panel': user.role == 'admin'
        }
        return permissions


class RegisterView(generics.CreateAPIView):
    """Enhanced user registration with security features"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Enhanced password handling
        password = serializer.validated_data.get('password')
        if password:
            # Hash password using Django's secure methods
            serializer.validated_data['password'] = make_password(password)
        
        user = serializer.save()
        
        # Log registration
        ip_address = self.get_client_ip(request)
        security_logger.info(f"New user registered: {user.email} from {ip_address}")
        
        # Generate tokens for immediate login
        refresh = RefreshToken.for_user(user)
        access = EnhancedAccessToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(access),
            'message': 'User registered successfully. Please verify your email.',
            'permissions': self.get_user_permissions(user)
        }, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_user_permissions(self, user):
        """Get user permissions for frontend authorization"""
        permissions = {
            'can_create_users': user.role in ['admin', 'department_head'],
            'can_manage_departments': user.role == 'admin',
            'can_view_all_documents': user.role == 'admin',
            'can_approve_documents': user.role in ['admin', 'department_head', 'manager'],
            'can_delete_any_document': user.role == 'admin',
            'can_share_documents': True,
            'can_view_analytics': user.role in ['admin', 'department_head', 'manager'],
            'can_access_admin_panel': user.role == 'admin'
        }
        return permissions


class ProfileView(generics.RetrieveUpdateAPIView):
    """Current user profile view"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ProfileUpdateView(generics.UpdateAPIView):
    """Update user profile information"""
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully'})
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class UserListView(generics.ListAPIView):
    """List all users with role-based filtering"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['role', 'is_active']
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['first_name', 'last_name', 'email', 'created_at']
    ordering = ['first_name', 'last_name']
    
    def get_queryset(self):
        """Filter users based on role permissions"""
        user = self.request.user
        queryset = super().get_queryset()
        
        if user.role == 'admin':
            # Admin can see all users
            return queryset
        elif user.role == 'department_head':
            # Department heads can see users in their departments
            user_departments = user.department_assignments.filter(
                end_date__isnull=True,
                role='head'
            ).values_list('department', flat=True)
            return queryset.filter(
                department_assignments__department__in=user_departments,
                department_assignments__end_date__isnull=True
            ).distinct()
        else:
            # Regular users can only see themselves
            return queryset.filter(id=user.id)


class UserDetailView(generics.RetrieveAPIView):
    """Get user details with permission checks"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Apply permission checks for user detail access"""
        obj = super().get_object()
        user = self.request.user
        
        # Users can always access their own profile
        if obj.id == user.id:
            return obj
        
        # Admin can access any user
        if user.role == 'admin':
            return obj
        
        # Department heads can access users in their departments
        if user.role == 'department_head':
            user_departments = user.department_assignments.filter(
                end_date__isnull=True,
                role='head'
            ).values_list('department', flat=True)
            
            target_departments = obj.department_assignments.filter(
                end_date__isnull=True
            ).values_list('department', flat=True)
            
            if any(dept in user_departments for dept in target_departments):
                return obj
        
        # Log unauthorized access attempt
        security_logger.warning(
            f"Unauthorized user access attempt: {user.email} tried to access {obj.email}'s profile"
        )
        raise permissions.PermissionDenied("You don't have permission to view this user")


class UserCreateView(generics.CreateAPIView):
    """Create new user (admin and department heads only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        """Enhanced user creation with role checks and logging"""
        user = self.request.user
        
        # Check permissions
        if user.role not in ['admin', 'department_head']:
            security_logger.warning(
                f"Unauthorized user creation attempt by {user.email} (role: {user.role})"
            )
            raise permissions.PermissionDenied("You don't have permission to create users")
        
        # Department heads can only create certain roles
        new_user_role = serializer.validated_data.get('role', 'employee')
        if user.role == 'department_head' and new_user_role in ['admin', 'department_head']:
            security_logger.warning(
                f"Department head {user.email} attempted to create {new_user_role} user"
            )
            raise permissions.PermissionDenied("Department heads cannot create admin or department head users")
        
        # Save the user
        new_user = serializer.save()
        
        # Log user creation
        security_logger.info(
            f"User created: {new_user.email} (role: {new_user.role}) by {user.email}"
        )


class UserUpdateView(generics.UpdateAPIView):
    """Update user with enhanced permission checks"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        """Enhanced user update with role checks and logging"""
        user = self.request.user
        target_user = self.get_object()
        
        # Users can update their own profile (limited fields)
        if target_user.id == user.id:
            # Users can only update certain fields for themselves
            allowed_fields = ['first_name', 'last_name', 'email']
            for field in serializer.validated_data:
                if field not in allowed_fields and field != 'password':
                    raise permissions.PermissionDenied(f"You cannot update the '{field}' field")
        else:
            # Only admin and department heads can update other users
            if user.role not in ['admin', 'department_head']:
                security_logger.warning(
                    f"Unauthorized user update attempt: {user.email} tried to update {target_user.email}"
                )
                raise permissions.PermissionDenied("You don't have permission to update other users")
            
            # Department heads have restrictions
            if user.role == 'department_head':
                # Cannot update admin or other department head roles
                if target_user.role in ['admin', 'department_head']:
                    security_logger.warning(
                        f"Department head {user.email} attempted to update {target_user.role} user {target_user.email}"
                    )
                    raise permissions.PermissionDenied("You cannot update admin or department head users")
                
                # Cannot assign admin or department head roles
                new_role = serializer.validated_data.get('role')
                if new_role and new_role in ['admin', 'department_head']:
                    raise permissions.PermissionDenied("You cannot assign admin or department head roles")
        
        # Save changes
        old_role = target_user.role
        updated_user = serializer.save()
        new_role = updated_user.role
        
        # Log role changes
        if old_role != new_role:
            security_logger.info(
                f"Role change: {updated_user.email} role changed from {old_role} to {new_role} by {user.email}"
            )
        else:
            security_logger.info(f"User updated: {updated_user.email} by {user.email}")


class DeactivateUserView(APIView):
    """Deactivate user account with enhanced security"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, user_id):
        user = request.user
        
        # Only admin can deactivate users
        if user.role != 'admin':
            security_logger.warning(
                f"Unauthorized deactivation attempt by {user.email} (role: {user.role})"
            )
            return Response(
                {'error': 'Only administrators can deactivate users'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Prevent self-deactivation
            if target_user.id == user.id:
                return Response(
                    {'error': 'You cannot deactivate your own account'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Prevent deactivating the last admin
            if target_user.role == 'admin':
                active_admins = User.objects.filter(role='admin', is_active=True).count()
                if active_admins <= 1:
                    return Response(
                        {'error': 'Cannot deactivate the last admin user'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            target_user.is_active = False
            target_user.save()
            
            # Log deactivation
            security_logger.info(
                f"User deactivated: {target_user.email} (role: {target_user.role}) by {user.email}"
            )
            
            return Response({'message': 'User deactivated successfully'})
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class LoginHistoryView(generics.ListAPIView):
    """View login history with role-based access"""
    serializer_class = LoginAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'admin':
            # Admin can see all login attempts
            return LoginAttempt.objects.all()
        else:
            # Users can only see their own login attempts
            return LoginAttempt.objects.filter(user=user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """Get user statistics (admin only)"""
    user = request.user
    
    if user.role != 'admin':
        security_logger.warning(
            f"Unauthorized stats access attempt by {user.email} (role: {user.role})"
        )
        return Response(
            {'error': 'Only administrators can view user statistics'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'verified_users': User.objects.filter(is_verified=True).count(),
        'users_by_role': {},
        'recent_registrations': User.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
        'recent_logins': LoginAttempt.objects.filter(
            successful=True,
            attempted_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
        'failed_logins_today': LoginAttempt.objects.filter(
            successful=False,
            attempted_at__gte=timezone.now().replace(hour=0, minute=0, second=0)
        ).count()
    }
    
    # Count users by role
    for role_code, role_name in User.ROLE_CHOICES:
        stats['users_by_role'][role_name] = User.objects.filter(role=role_code).count()
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_users(request):
    """Search users by name or email"""
    query = request.GET.get('q', '')
    if not query:
        return Response({'users': []})
    
    users = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query),
        is_active=True
    )[:10]  # Limit to 10 results
    
    serializer = UserListSerializer(users, many=True)
    return Response({'users': serializer.data})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_email(request):
    """Verify user email"""
    # This would typically involve sending an email with a verification token
    # For now, we'll just mark the email as verified
    user = request.user
    user.is_verified = True
    user.save()
    
    return Response({'message': 'Email verified successfully'})


class LogoutView(APIView):
    """Logout user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except Exception as e:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class GroupListView(generics.ListAPIView):
    """List all groups"""
    queryset = Group.objects.all()
    serializer_class = GroupListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter groups based on user permissions"""
        user = self.request.user
        if user.role == 'admin':
            return Group.objects.all()
        elif user.role == 'department_head':
            # Department heads can see groups they manage
            return Group.objects.filter(
                Q(user__id=user.id) | Q(name__icontains='department')
            ).distinct()
        else:
            # Regular users can see groups they belong to
            return user.groups.all()


class GroupDetailView(generics.RetrieveAPIView):
    """Get group details"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupCreateView(generics.CreateAPIView):
    """Create a new group"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    
    def perform_create(self, serializer):
        """Enhanced group creation with role checks and logging"""
        user = self.request.user
        
        # Check permissions
        if user.role not in ['admin', 'department_head']:
            security_logger.warning(
                f"Unauthorized group creation attempt by {user.email} (role: {user.role})"
            )
            raise permissions.PermissionDenied("You don't have permission to create groups")
        
        # Save the group
        group = serializer.save()
        
        # Log group creation
        security_logger.info(
            f"Group created: {group.name} by {user.email}"
        )


class GroupUpdateView(generics.UpdateAPIView):
    """Update a group"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    
    def perform_update(self, serializer):
        """Enhanced group update with role checks and logging"""
        user = self.request.user
        target_group = self.get_object()
        
        # Users can update their own group
        if target_group.id == user.id:
            # Users can only update certain fields for themselves
            allowed_fields = ['name']
            for field in serializer.validated_data:
                if field not in allowed_fields:
                    raise permissions.PermissionDenied(f"You cannot update the '{field}' field")
        else:
            # Only admin and department heads can update other groups
            if user.role not in ['admin', 'department_head']:
                security_logger.warning(
                    f"Unauthorized group update attempt: {user.email} tried to update {target_group.name}"
                )
                raise permissions.PermissionDenied("You don't have permission to update other groups")
        
        # Save changes
        old_name = target_group.name
        updated_group = serializer.save()
        new_name = updated_group.name
        
        # Log group changes
        if old_name != new_name:
            security_logger.info(
                f"Group updated: {updated_group.name} name changed from {old_name} to {new_name} by {user.email}"
            )
        else:
            security_logger.info(f"Group updated: {updated_group.name} by {user.email}")


class GroupDeleteView(generics.DestroyAPIView):
    """Delete a group"""
    queryset = Group.objects.all()
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    
    def perform_destroy(self, instance):
        """Enhanced group deletion with role checks and logging"""
        user = self.request.user
        
        # Only admin can delete groups
        if user.role != 'admin':
            security_logger.warning(
                f"Unauthorized group deletion attempt by {user.email} (role: {user.role})"
            )
            raise permissions.PermissionDenied("Only administrators can delete groups")
        
        # Prevent deleting the last admin group
        if instance.id == user.id:
            security_logger.warning(
                f"Unauthorized group deletion attempt: {user.email} attempted to delete the last admin group"
            )
            raise permissions.PermissionDenied("Cannot delete the last admin group")
        
        # Delete the group
        instance.delete()
        
        # Log group deletion
        security_logger.info(
            f"Group deleted: {instance.name} by {user.email}"
        )


class GroupMemberAddView(generics.CreateAPIView):
    """Add a member to a group"""
    queryset = Group.objects.all()
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    
    def perform_create(self, serializer):
        """Enhanced group member addition with role checks and logging"""
        user = self.request.user
        group = self.get_object()
        
        # Check permissions
        if user.role not in ['admin', 'department_head']:
            security_logger.warning(
                f"Unauthorized group member addition attempt by {user.email} (role: {user.role})"
            )
            raise permissions.PermissionDenied("You don't have permission to add members to groups")
        
        # Save the group member
        serializer.save(group=group)
        
        # Log group member addition
        security_logger.info(
            f"Group member added: {serializer.validated_data['user']} to {group.name} by {user.email}"
        )


class GroupMemberRemoveView(generics.DestroyAPIView):
    """Remove a member from a group"""
    queryset = Group.objects.all()
    serializer_class = GroupMemberSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]
    
    def perform_destroy(self, instance):
        """Enhanced group member removal with role checks and logging"""
        user = self.request.user
        group = self.get_object()
        
        # Check permissions
        if user.role not in ['admin', 'department_head']:
            security_logger.warning(
                f"Unauthorized group member removal attempt by {user.email} (role: {user.role})"
            )
            raise permissions.PermissionDenied("You don't have permission to remove members from groups")
        
        # Prevent removing the last admin from the group
        if instance.role == 'admin':
            security_logger.warning(
                f"Unauthorized group member removal attempt: {user.email} attempted to remove the last admin from {group.name}"
            )
            raise permissions.PermissionDenied("Cannot remove the last admin from the group")
        
        # Delete the group member
        instance.delete()
        
        # Log group member removal
        security_logger.info(
            f"Group member removed: {instance.user} from {group.name} by {user.email}"
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_user_to_group(request, group_id):
    """Add a user to a group"""
    user = request.user
    
    # Check permissions
    if user.role not in ['admin', 'department_head']:
        return Response(
            {'error': 'You do not have permission to manage groups'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        group = Group.objects.get(id=group_id)
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        target_user = User.objects.get(id=user_id, is_active=True)
        group.user_set.add(target_user)
        
        security_logger.info(
            f"User {target_user.email} added to group {group.name} by {user.email}"
        )
        
        return Response({
            'message': f'User {target_user.get_full_name()} added to group {group.name}',
            'group': GroupSerializer(group).data
        })
        
    except Group.DoesNotExist:
        return Response(
            {'error': 'Group not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_user_from_group(request, group_id, user_id):
    """Remove a user from a group"""
    user = request.user
    
    # Check permissions
    if user.role not in ['admin', 'department_head']:
        return Response(
            {'error': 'You do not have permission to manage groups'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        group = Group.objects.get(id=group_id)
        target_user = User.objects.get(id=user_id, is_active=True)
        
        if target_user not in group.user_set.all():
            return Response(
                {'error': 'User is not a member of this group'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        group.user_set.remove(target_user)
        
        security_logger.info(
            f"User {target_user.email} removed from group {group.name} by {user.email}"
        )
        
        return Response({
            'message': f'User {target_user.get_full_name()} removed from group {group.name}',
            'group': GroupSerializer(group).data
        })
        
    except Group.DoesNotExist:
        return Response(
            {'error': 'Group not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_permissions(request):
    """Get current user's permissions for frontend authorization"""
    user = request.user
    
    # Define all possible permissions
    permission_map = {
        'documents': {
            'view_all': user_has_permission(user, 'documents.view_all'),
            'create': user_has_permission(user, 'documents.create'),
            'edit_all': user_has_permission(user, 'documents.edit_all'),
            'delete_all': user_has_permission(user, 'documents.delete_all'),
            'approve': user_has_permission(user, 'documents.approve'),
            'share': user_has_permission(user, 'documents.share'),
        },
        'categories': {
            'view_all': user_has_permission(user, 'categories.view_all'),
            'create': user_has_permission(user, 'categories.create'),
            'edit': user_has_permission(user, 'categories.edit'),
            'delete': user_has_permission(user, 'categories.delete'),
            'assign': user_has_permission(user, 'categories.assign'),
        },
        'departments': {
            'view_all': user_has_permission(user, 'departments.view_all'),
            'manage': user_has_permission(user, 'departments.manage'),
            'assign_users': user_has_permission(user, 'departments.assign_users'),
            'view_employees': user_has_permission(user, 'departments.view_employees'),
        },
        'users': {
            'view_all': user_has_permission(user, 'users.view_all'),
            'create': user_has_permission(user, 'users.create'),
            'edit': user_has_permission(user, 'users.edit'),
            'deactivate': user_has_permission(user, 'users.deactivate'),
            'assign_roles': user_has_permission(user, 'users.assign_roles'),
        },
        'system': {
            'admin_settings': user_has_permission(user, 'system.admin_settings'),
            'view_analytics': user_has_permission(user, 'system.view_analytics'),
            'manage_settings': user_has_permission(user, 'system.manage_settings'),
            'backup': user_has_permission(user, 'system.backup'),
        }
    }
    
    # Add role-based information
    user_info = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'is_admin': user.role == 'admin',
        'permissions': permission_map,
        'timestamp': timezone.now().isoformat()
    }
    
    return Response(user_info)
