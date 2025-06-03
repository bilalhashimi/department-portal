from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import (
    Department, Position, EmployeeDepartment, DepartmentBudget,
    Permission, PermissionTemplate, PermissionAuditLog,
    SystemSettings, SystemBackup
)
from .forms import PermissionForm, UserPermissionForm, PermissionTemplateForm

User = get_user_model()

# Inline admins for related models
class EmployeeDepartmentInline(admin.TabularInline):
    model = EmployeeDepartment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['employee', 'position', 'start_date', 'end_date', 'is_primary']

class UserPermissionInline(admin.TabularInline):
    """Inline for managing custom permissions directly on user admin"""
    model = Permission
    form = UserPermissionForm
    extra = 0
    readonly_fields = ['granted_at', 'granted_by', 'permission_category']
    fields = ['permission', 'permission_category', 'is_active', 'expires_at', 'granted_by', 'granted_at']
    verbose_name = "🔐 Custom Permission"
    verbose_name_plural = "🔐 Custom Permissions (Department Portal)"
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(entity_type='user')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "granted_by":
            kwargs["initial"] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Model Admins
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'head', 'employees_count', 'is_active']
    list_filter = ['is_active', 'parent_department']
    search_fields = ['name', 'code', 'head__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [EmployeeDepartmentInline]
    
    fieldsets = (
        ('Department Information', {
            'fields': ('name', 'code', 'description', 'parent_department')
        }),
        ('Management', {
            'fields': ('head', 'annual_budget')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'location'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def employees_count(self, obj):
        return obj.get_all_employees_count()
    employees_count.short_description = 'Employees'

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    form = PermissionForm
    list_display = ['permission_display', 'entity_display', 'is_active', 'granted_by', 'granted_at']
    list_filter = ['entity_type', 'permission_category', 'is_active', 'granted_at']
    search_fields = ['permission', 'entity_id']
    readonly_fields = ['granted_at', 'permission_category']
    date_hierarchy = 'granted_at'
    
    fieldsets = (
        ('🔐 Permission Details', {
            'fields': ('permission', 'permission_category'),
            'description': 'Select the permission to grant. The category will be set automatically.'
        }),
        ('🎯 Target', {
            'fields': ('entity_type', 'entity_id'),
            'description': 'Who or what this permission applies to'
        }),
        ('⚙️ Settings', {
            'fields': ('is_active', 'expires_at', 'granted_by', 'notes')
        }),
    )
    
    def permission_display(self, obj):
        """Show a more readable permission name"""
        permission_map = dict(PermissionForm.PERMISSION_CHOICES)
        readable_name = permission_map.get(obj.permission, obj.permission)
        return format_html('<strong>{}</strong>', readable_name)
    permission_display.short_description = 'Permission'
    permission_display.admin_order_field = 'permission'
    
    def entity_display(self, obj):
        """Display the actual entity name instead of just the UUID"""
        if obj.entity_type == 'user':
            try:
                user = User.objects.get(id=obj.entity_id)
                return format_html(
                    '👤 <a href="{}">{}</a>',
                    reverse('admin:accounts_user_change', args=[user.id]),
                    user.get_full_name() or user.email
                )
            except User.DoesNotExist:
                return f"👤 User (Deleted)"
        elif obj.entity_type == 'department':
            try:
                dept = Department.objects.get(id=obj.entity_id)
                return format_html(
                    '🏢 <a href="{}">{}</a>',
                    reverse('admin:departments_department_change', args=[dept.id]),
                    dept.name
                )
            except Department.DoesNotExist:
                return f"🏢 Department (Deleted)"
        else:
            return f"📁 {obj.entity_id}"
    entity_display.short_description = 'Granted To'
    entity_display.admin_order_field = 'entity_id'
    
    def save_model(self, request, obj, form, change):
        # Auto-set permission_category and granted_by
        if obj.permission:
            obj.permission_category = obj.permission.split('.')[0]
        if not obj.granted_by_id:
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PermissionTemplate)
class PermissionTemplateAdmin(admin.ModelAdmin):
    form = PermissionTemplateForm
    list_display = ['name', 'permissions_count', 'usage_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at', 'permissions_preview']
    
    fieldsets = (
        ('📋 Template Details', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('🔐 Permissions', {
            'fields': ('available_permissions', 'permissions_preview'),
            'description': 'Select all permissions to include in this template'
        }),
        ('📊 Usage Stats', {
            'fields': ('created_by', 'usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def permissions_count(self, obj):
        count = len(obj.permissions) if obj.permissions else 0
        return format_html('<strong>{}</strong> permissions', count)
    permissions_count.short_description = 'Count'
    
    def permissions_preview(self, obj):
        """Show readable permission names"""
        if not obj.permissions:
            return "No permissions selected"
        
        permission_map = dict(PermissionForm.PERMISSION_CHOICES)
        readable_perms = [permission_map.get(perm, perm) for perm in obj.permissions[:5]]
        preview = '<br>'.join(readable_perms)
        
        if len(obj.permissions) > 5:
            preview += f'<br><em>... and {len(obj.permissions) - 5} more</em>'
            
        return format_html(preview)
    permissions_preview.short_description = 'Permissions Preview'
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'permission_display', 'entity_display', 'performed_by', 'performed_at']
    list_filter = ['action', 'entity_type', 'performed_at']
    search_fields = ['permission', 'performed_by__email']
    readonly_fields = ['performed_at']
    date_hierarchy = 'performed_at'
    
    fieldsets = (
        ('📝 Action Details', {
            'fields': ('action', 'permission', 'entity_type', 'entity_id')
        }),
        ('👤 Who & When', {
            'fields': ('performed_by', 'performed_at', 'ip_address')
        }),
        ('📄 Additional Info', {
            'fields': ('notes', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def permission_display(self, obj):
        """Show readable permission name"""
        if obj.permission:
            permission_map = dict(PermissionForm.PERMISSION_CHOICES)
            return permission_map.get(obj.permission, obj.permission)
        return "N/A"
    permission_display.short_description = 'Permission'
    
    def entity_display(self, obj):
        if obj.entity_type == 'user' and obj.entity_id:
            try:
                user = User.objects.get(id=obj.entity_id)
                return f"👤 {user.get_full_name() or user.email}"
            except User.DoesNotExist:
                return f"👤 User (Deleted)"
        elif obj.entity_type == 'department' and obj.entity_id:
            try:
                dept = Department.objects.get(id=obj.entity_id)
                return f"🏢 {dept.name}"
            except Department.DoesNotExist:
                return f"🏢 Department (Deleted)"
        return str(obj.entity_id) if obj.entity_id else "N/A"
    entity_display.short_description = 'Target'

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'max_file_size', 'enable_ai_chat', 'enable_document_sharing', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('🏢 General Settings', {
            'fields': ('site_name', 'max_file_size', 'allowed_file_types')
        }),
        ('🔧 Features', {
            'fields': ('enable_ai_chat', 'enable_document_sharing', 'require_document_approval')
        }),
        ('💾 Backup', {
            'fields': ('auto_backup_enabled', 'backup_frequency', 'backup_retention_days'),
            'classes': ('collapse',)
        }),
        ('🔒 Security', {
            'fields': ('password_expiry_days', 'max_login_attempts'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

# Only register essential models - hide the complex ones that aren't needed for daily admin work
# Position, EmployeeDepartment, DepartmentBudget, and SystemBackup are available but not prominently displayed

# Admin site customization
admin.site.site_header = "🏢 Department Portal Admin"
admin.site.site_title = "Department Portal"
admin.site.index_title = "Administration Dashboard"

# Add custom CSS for better UX
admin.site.enable_nav_sidebar = True
