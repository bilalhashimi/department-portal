from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class Department(models.Model):
    """
    Department model for organizational structure
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="Short department code (e.g., 'HR', 'IT')")
    description = models.TextField(blank=True)
    
    # Hierarchy
    parent_department = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='sub_departments'
    )
    
    # Department Head
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )
    
    # Contact Information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Budget Information
    annual_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments_department'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_full_hierarchy(self):
        """Return full department hierarchy as string"""
        if self.parent_department:
            return f"{self.parent_department.get_full_hierarchy()} > {self.name}"
        return self.name
    
    def get_all_employees_count(self):
        """Get total count of employees in this department and sub-departments"""
        count = self.employees.count()
        for sub_dept in self.sub_departments.all():
            count += sub_dept.get_all_employees_count()
        return count

    def get_all_employees(self):
        """Get all employees in this department and sub-departments"""
        employees = list(self.employees.filter(end_date__isnull=True))
        for sub_dept in self.sub_departments.all():
            employees.extend(sub_dept.get_all_employees())
        return employees


class Position(models.Model):
    """
    Job positions within departments
    """
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
    ]
    
    LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('junior', 'Junior'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior'),
        ('lead', 'Lead'),
        ('manager', 'Manager'),
        ('director', 'Director'),
        ('executive', 'Executive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    
    # Position Details
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='mid')
    
    # Salary Information
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Reports To
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments_position'
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
        ordering = ['department__name', 'title']
        unique_together = ['title', 'department']
    
    def __str__(self):
        return f"{self.title} - {self.department.name}"


class EmployeeDepartment(models.Model):
    """
    Employee assignment to departments with positions and dates
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='department_assignments'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='employees'
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='employees',
        null=True,
        blank=True
    )
    
    # Assignment Details
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=True, help_text="Is this the employee's primary department?")
    
    # Performance
    performance_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text="Performance rating from 1-5"
    )
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments_employeedepartment'
        verbose_name = 'Employee Department Assignment'
        verbose_name_plural = 'Employee Department Assignments'
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'is_primary'],
                condition=models.Q(is_primary=True, end_date__isnull=True),
                name='unique_primary_department'
            )
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.department.name}"
    
    @property
    def is_active(self):
        """Check if assignment is currently active"""
        return self.end_date is None


class DepartmentBudget(models.Model):
    """
    Annual budget tracking for departments
    """
    BUDGET_TYPE_CHOICES = [
        ('operational', 'Operational'),
        ('capital', 'Capital'),
        ('personnel', 'Personnel'),
        ('training', 'Training'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='budgets')
    
    # Budget Details
    fiscal_year = models.IntegerField()
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_budgets'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments_departmentbudget'
        verbose_name = 'Department Budget'
        verbose_name_plural = 'Department Budgets'
        ordering = ['-fiscal_year', 'budget_type']
        unique_together = ['department', 'fiscal_year', 'budget_type']
    
    def __str__(self):
        return f"{self.department.name} - {self.budget_type} Budget {self.fiscal_year}"
    
    @property
    def remaining_amount(self):
        """Calculate remaining budget amount"""
        return self.allocated_amount - self.spent_amount
    
    @property
    def utilization_percentage(self):
        """Calculate budget utilization percentage"""
        if self.allocated_amount > 0:
            return (self.spent_amount / self.allocated_amount) * 100
        return 0


class Permission(models.Model):
    """
    Permission system for fine-grained access control
    """
    ENTITY_TYPES = [
        ('user', 'User'),
        ('department', 'Department'),
        ('category', 'Category'),
    ]
    
    PERMISSION_CATEGORIES = [
        ('documents', 'Documents'),
        ('categories', 'Categories'),
        ('departments', 'Departments'),
        ('users', 'Users'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Entity this permission applies to
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    entity_id = models.UUIDField(help_text="ID of the entity (user, department, or category)")
    
    # Permission details
    permission = models.CharField(max_length=100, help_text="Permission key (e.g., 'documents.view_all')")
    permission_category = models.CharField(max_length=20, choices=PERMISSION_CATEGORIES)
    
    # Metadata
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entity_permissions_granted'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    # Audit fields
    notes = models.TextField(blank=True, help_text="Optional notes about why this permission was granted")
    
    class Meta:
        db_table = 'departments_permission'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        unique_together = ['entity_type', 'entity_id', 'permission']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['permission']),
            models.Index(fields=['permission_category']),
        ]
    
    def __str__(self):
        return f"{self.permission} for {self.entity_type}:{self.entity_id}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False


class PermissionTemplate(models.Model):
    """
    Reusable permission templates for common roles
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    # Template permissions (stored as JSON array)
    permissions = models.JSONField(
        default=list,
        help_text="List of permission keys included in this template"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_permission_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'departments_permission_template'
        verbose_name = 'Permission Template'
        verbose_name_plural = 'Permission Templates'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def apply_to_entity(self, entity_type, entity_id, granted_by):
        """Apply this template's permissions to an entity"""
        permissions_created = []
        for perm_key in self.permissions:
            permission, created = Permission.objects.get_or_create(
                entity_type=entity_type,
                entity_id=entity_id,
                permission=perm_key,
                defaults={
                    'permission_category': perm_key.split('.')[0],
                    'granted_by': granted_by,
                    'notes': f'Applied from template: {self.name}'
                }
            )
            if created:
                permissions_created.append(permission)
        
        # Update usage count
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
        
        return permissions_created


class PermissionAuditLog(models.Model):
    """
    Audit log for permission changes
    """
    ACTION_CHOICES = [
        ('grant', 'Grant Permission'),
        ('revoke', 'Revoke Permission'),
        ('template_apply', 'Apply Template'),
        ('template_create', 'Create Template'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Permission details
    permission = models.CharField(max_length=100, blank=True)
    entity_type = models.CharField(max_length=20, blank=True)
    entity_id = models.UUIDField(null=True, blank=True)
    
    # Template details (if applicable)
    template = models.ForeignKey(
        PermissionTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Actor and metadata
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='permission_audit_logs'
    )
    performed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional context
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'departments_permission_audit_log'
        verbose_name = 'Permission Audit Log'
        verbose_name_plural = 'Permission Audit Logs'
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.action} by {self.performed_by} at {self.performed_at}"


class SystemSettings(models.Model):
    """
    System-wide configuration settings
    """
    BACKUP_FREQUENCIES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # General Settings
    site_name = models.CharField(max_length=100, default='Department Portal')
    max_file_size = models.PositiveIntegerField(
        default=50, 
        validators=[MinValueValidator(1), MaxValueValidator(1000)],
        help_text="Maximum file size in MB"
    )
    allowed_file_types = models.TextField(
        default='pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,png',
        help_text="Comma-separated list of allowed file extensions"
    )
    
    # Feature Settings
    enable_ai_chat = models.BooleanField(default=True)
    enable_document_sharing = models.BooleanField(default=True)
    require_document_approval = models.BooleanField(default=False)
    
    # Backup Settings
    auto_backup_enabled = models.BooleanField(default=True)
    backup_frequency = models.CharField(
        max_length=20, 
        choices=BACKUP_FREQUENCIES, 
        default='daily'
    )
    backup_retention_days = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Number of days to retain backups"
    )
    
    # Security Settings
    password_expiry_days = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(30), MaxValueValidator(365)],
        help_text="Number of days before password expires"
    )
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(3), MaxValueValidator(10)],
        help_text="Maximum login attempts before account lockout"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='system_settings_updates'
    )
    
    class Meta:
        db_table = 'departments_system_settings'
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return f"System Settings - {self.site_name}"
    
    @classmethod
    def get_settings(cls):
        """Get current system settings, create default if none exist"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        settings_obj = cls.objects.first()
        if not settings_obj:
            # Create default settings with first admin user
            admin_user = User.objects.filter(role='admin').first()
            if admin_user:
                settings_obj = cls.objects.create(updated_by=admin_user)
        return settings_obj
    
    def get_allowed_file_types_list(self):
        """Get allowed file types as a list"""
        return [ext.strip() for ext in self.allowed_file_types.split(',') if ext.strip()]
    
    def clean(self):
        """Validate settings"""
        if self.max_file_size < 1 or self.max_file_size > 1000:
            raise ValidationError("Max file size must be between 1 and 1000 MB")
        
        # Validate file types format
        try:
            types = self.get_allowed_file_types_list()
            for file_type in types:
                if not file_type.isalnum():
                    raise ValidationError(f"Invalid file type: {file_type}")
        except Exception as e:
            raise ValidationError(f"Invalid file types format: {e}")


class SystemBackup(models.Model):
    """
    System backup records
    """
    BACKUP_TYPES = [
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ]
    
    BACKUP_STATUS = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Backup Details
    name = models.CharField(max_length=255)
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPES)
    status = models.CharField(max_length=20, choices=BACKUP_STATUS, default='pending')
    
    # File Information
    file_path = models.TextField(blank=True, help_text="Path to backup file")
    file_size = models.BigIntegerField(null=True, blank=True, help_text="Backup file size in bytes")
    checksum = models.CharField(max_length=64, blank=True, help_text="SHA256 checksum of backup file")
    
    # Backup Content
    includes_documents = models.BooleanField(default=True)
    includes_database = models.BooleanField(default=True)
    includes_settings = models.BooleanField(default=True)
    includes_user_data = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='system_backups_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error information
    error_message = models.TextField(blank=True)
    
    # Backup statistics
    total_documents = models.PositiveIntegerField(default=0)
    total_users = models.PositiveIntegerField(default=0)
    total_departments = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'departments_system_backup'
        verbose_name = 'System Backup'
        verbose_name_plural = 'System Backups'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backup: {self.name} ({self.status})"
    
    @property
    def duration(self):
        """Calculate backup duration"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
