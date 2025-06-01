from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


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
