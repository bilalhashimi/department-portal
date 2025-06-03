from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, UserProfile

# Import the enhanced Permission inline from departments admin
from departments.admin import UserPermissionInline
from departments.models import Permission

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model"""
    list_display = ['email', 'full_name_display', 'role', 'custom_permissions_count', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_verified', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    
    # Add the enhanced custom permissions inline
    inlines = [UserPermissionInline]
    
    fieldsets = (
        (_('Account'), {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Role & Status'), {
            'fields': ('role', 'is_active', 'is_verified'),
        }),
        (_('Admin Access'), {
            'fields': ('is_staff', 'is_superuser'),
            'classes': ('collapse',),
            'description': 'Only check these if this user needs Django admin access'
        }),
        (_('Dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (_('Create User'), {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_verified'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def full_name_display(self, obj):
        """Show full name or email if no name"""
        full_name = obj.get_full_name()
        if full_name:
            return full_name
        return obj.email
    full_name_display.short_description = 'Name'
    full_name_display.admin_order_field = 'first_name'
    
    def custom_permissions_count(self, obj):
        """Show count of custom permissions for this user"""
        if obj:
            count = Permission.objects.filter(
                entity_type='user',
                entity_id=obj.id,
                is_active=True
            ).count()
            if count > 0:
                return format_html(
                    '<strong style="color: #0066cc;">{} active</strong>',
                    count
                )
            return "0"
        return "N/A"
    custom_permissions_count.short_description = 'Custom Permissions'
    custom_permissions_count.admin_order_field = 'id'
    
    def save_formset(self, request, form, formset, change):
        """Override to set entity_id and entity_type for new permission instances"""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Permission):
                # Set the entity details for new permissions
                instance.entity_type = 'user'
                instance.entity_id = form.instance.id
                if not instance.granted_by_id:
                    instance.granted_by = request.user
                # Auto-set permission_category
                if instance.permission:
                    instance.permission_category = instance.permission.split('.')[0]
                instance.save()
        formset.save_m2m()

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for User Profile"""
    list_display = ['user', 'employee_id', 'position', 'phone_number', 'hire_date']
    list_filter = ['position', 'is_remote', 'hire_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'employee_id', 'position']
    raw_id_fields = ['user']
    
    fieldsets = (
        (_('Employee Information'), {
            'fields': ('user', 'employee_id', 'position', 'hire_date')
        }),
        (_('Contact Information'), {
            'fields': ('phone_number', 'address')
        }),
        (_('Work Details'), {
            'fields': ('is_remote', 'bio'),
            'classes': ('collapse',)
        }),
        (_('Profile Image'), {
            'fields': ('avatar',),
            'classes': ('collapse',)
        }),
    )
