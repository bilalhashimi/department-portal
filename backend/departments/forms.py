from django import forms
from django.contrib.auth import get_user_model
from .models import Permission, PermissionTemplate, Department

User = get_user_model()

class PermissionForm(forms.ModelForm):
    """Custom form for Permission model with predefined choices"""
    
    PERMISSION_CHOICES = [
        # Document Permissions
        ('documents.view_all', 'Documents: View All Documents'),
        ('documents.create', 'Documents: Create Documents'),
        ('documents.edit_all', 'Documents: Edit All Documents'),
        ('documents.delete_all', 'Documents: Delete All Documents'),
        ('documents.approve', 'Documents: Approve Documents'),
        ('documents.share', 'Documents: Share Documents'),
        ('documents.download', 'Documents: Download Documents'),
        ('documents.view_stats', 'Documents: View Statistics'),
        
        # Category Permissions
        ('categories.view_all', 'Categories: View All Categories'),
        ('categories.create', 'Categories: Create Categories'),
        ('categories.edit', 'Categories: Edit Categories'),
        ('categories.delete', 'Categories: Delete Categories'),
        ('categories.assign', 'Categories: Assign to Documents'),
        
        # Department Permissions
        ('departments.view_all', 'Departments: View All Departments'),
        ('departments.manage', 'Departments: Manage Departments'),
        ('departments.assign_users', 'Departments: Assign Users'),
        ('departments.view_employees', 'Departments: View Employee List'),
        ('departments.manage_budget', 'Departments: Manage Budget'),
        
        # User Permissions
        ('users.view_all', 'Users: View All Users'),
        ('users.create', 'Users: Create Users'),
        ('users.edit', 'Users: Edit Users'),
        ('users.deactivate', 'Users: Deactivate Users'),
        ('users.assign_roles', 'Users: Assign Roles'),
        ('users.manage_permissions', 'Users: Manage Permissions'),
        
        # System Permissions
        ('system.admin_settings', 'System: Access Admin Settings'),
        ('system.view_analytics', 'System: View Analytics'),
        ('system.manage_settings', 'System: Manage System Settings'),
        ('system.backup', 'System: Manage Backups'),
        ('system.view_logs', 'System: View System Logs'),
        ('system.manage_templates', 'System: Manage Permission Templates'),
    ]
    
    permission = forms.ChoiceField(
        choices=PERMISSION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'style': 'width: 100%;'
        }),
        help_text="Select a permission to grant"
    )
    
    class Meta:
        model = Permission
        fields = ['permission', 'permission_category', 'entity_type', 'entity_id', 'is_active', 'expires_at', 'notes']
        widgets = {
            'entity_type': forms.Select(attrs={'class': 'form-control'}),
            'permission_category': forms.Select(attrs={'class': 'form-control'}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Auto-set permission_category based on permission choice
        if 'permission' in self.data:
            permission_key = self.data.get('permission')
            if permission_key:
                category = permission_key.split('.')[0]
                self.fields['permission_category'].initial = category
        
        # Help text for fields
        self.fields['entity_type'].help_text = "What this permission applies to"
        self.fields['entity_id'].help_text = "ID of the specific user, department, or category"
        self.fields['expires_at'].help_text = "Optional: When this permission expires"
        
    def clean(self):
        cleaned_data = super().clean()
        permission = cleaned_data.get('permission')
        permission_category = cleaned_data.get('permission_category')
        
        # Auto-set permission_category if not provided
        if permission and not permission_category:
            cleaned_data['permission_category'] = permission.split('.')[0]
            
        return cleaned_data

class UserPermissionForm(forms.ModelForm):
    """Simplified form for user permissions inline"""
    
    permission = forms.ChoiceField(
        choices=PermissionForm.PERMISSION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select a permission to grant to this user"
    )
    
    class Meta:
        model = Permission
        fields = ['permission', 'is_active', 'expires_at', 'notes']
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set default values for inline forms
        if not instance.entity_type:
            instance.entity_type = 'user'
        
        # Auto-set permission_category
        if instance.permission:
            instance.permission_category = instance.permission.split('.')[0]
            
        if commit:
            instance.save()
        return instance

class PermissionTemplateForm(forms.ModelForm):
    """Form for creating permission templates"""
    
    available_permissions = forms.MultipleChoiceField(
        choices=PermissionForm.PERMISSION_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'permission-checkboxes'}),
        help_text="Select all permissions to include in this template"
    )
    
    class Meta:
        model = PermissionTemplate
        fields = ['name', 'description', 'available_permissions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing existing template, pre-select permissions
        if self.instance.pk and self.instance.permissions:
            self.fields['available_permissions'].initial = self.instance.permissions
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Convert selected permissions to JSON format
        selected_permissions = self.cleaned_data.get('available_permissions', [])
        instance.permissions = list(selected_permissions)
        
        if commit:
            instance.save()
        return instance

class BulkPermissionForm(forms.Form):
    """Form for bulk permission operations"""
    
    ACTION_CHOICES = [
        ('grant', 'Grant Permissions'),
        ('revoke', 'Revoke Permissions'),
        ('apply_template', 'Apply Template'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select users to apply the action to"
    )
    
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Optionally select departments to apply the action to"
    )
    
    permissions = forms.MultipleChoiceField(
        choices=PermissionForm.PERMISSION_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select permissions (for grant/revoke actions)"
    )
    
    template = forms.ModelChoiceField(
        queryset=PermissionTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select template (for apply template action)"
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        help_text="Optional notes for this bulk operation"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        permissions = cleaned_data.get('permissions')
        template = cleaned_data.get('template')
        
        if action in ['grant', 'revoke'] and not permissions:
            raise forms.ValidationError("You must select at least one permission for grant/revoke actions.")
            
        if action == 'apply_template' and not template:
            raise forms.ValidationError("You must select a template for apply template action.")
            
        return cleaned_data 