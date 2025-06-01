from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for the User model"""
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'is_verified', 'created_at']
    list_filter = ['role', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Role & Permissions'), {
            'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser'),
        }),
        (_('Groups & Permissions'), {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_verified', 'is_staff'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for User Profile"""
    list_display = ['user', 'employee_id', 'phone_number', 'position', 'hire_date']
    list_filter = ['position', 'is_remote', 'hire_date', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'employee_id', 'position']
    raw_id_fields = ['user']
