from rest_framework import serializers
from .models import Department, Position, EmployeeDepartment, DepartmentBudget


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for department model"""
    head_name = serializers.SerializerMethodField()
    parent_department_name = serializers.SerializerMethodField()
    employees_count = serializers.SerializerMethodField()
    hierarchy = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'description', 'parent_department',
            'parent_department_name', 'head', 'head_name', 'email',
            'phone', 'location', 'annual_budget', 'is_active',
            'employees_count', 'hierarchy', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_head_name(self, obj):
        return obj.head.get_full_name() if obj.head else None
    
    def get_parent_department_name(self, obj):
        return obj.parent_department.name if obj.parent_department else None
    
    def get_employees_count(self, obj):
        return obj.get_all_employees_count()
    
    def get_hierarchy(self, obj):
        return obj.get_full_hierarchy()


class DepartmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for department lists"""
    head_name = serializers.SerializerMethodField()
    employees_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'head_name', 'location',
            'employees_count', 'is_active'
        ]
    
    def get_head_name(self, obj):
        return obj.head.get_full_name() if obj.head else None
    
    def get_employees_count(self, obj):
        return obj.employees.filter(end_date__isnull=True).count()


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for position model"""
    department_name = serializers.SerializerMethodField()
    reports_to_title = serializers.SerializerMethodField()
    current_employees_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = [
            'id', 'title', 'department', 'department_name', 'description',
            'requirements', 'employment_type', 'level', 'min_salary',
            'max_salary', 'reports_to', 'reports_to_title', 'is_active',
            'current_employees_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_department_name(self, obj):
        return obj.department.name
    
    def get_reports_to_title(self, obj):
        return obj.reports_to.title if obj.reports_to else None
    
    def get_current_employees_count(self, obj):
        return obj.employees.filter(end_date__isnull=True).count()


class PositionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for position lists"""
    department_name = serializers.SerializerMethodField()
    current_employees = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = [
            'id', 'title', 'department_name', 'level', 'employment_type',
            'current_employees', 'is_active'
        ]
    
    def get_department_name(self, obj):
        return obj.department.name
    
    def get_current_employees(self, obj):
        return obj.employees.filter(end_date__isnull=True).count()


class EmployeeDepartmentSerializer(serializers.ModelSerializer):
    """Serializer for employee department assignment"""
    employee_name = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    position_title = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeDepartment
        fields = [
            'id', 'employee', 'employee_name', 'employee_email',
            'department', 'department_name', 'position', 'position_title',
            'start_date', 'end_date', 'is_primary', 'performance_rating',
            'notes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name()
    
    def get_employee_email(self, obj):
        return obj.employee.email
    
    def get_department_name(self, obj):
        return obj.department.name
    
    def get_position_title(self, obj):
        return obj.position.title if obj.position else None
    
    def get_is_active(self, obj):
        return obj.is_active


class EmployeeDepartmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for employee department assignment lists"""
    employee_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    position_title = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeDepartment
        fields = [
            'id', 'employee_name', 'department_name', 'position_title',
            'start_date', 'is_primary', 'performance_rating'
        ]
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name()
    
    def get_department_name(self, obj):
        return obj.department.name
    
    def get_position_title(self, obj):
        return obj.position.title if obj.position else None


class DepartmentBudgetSerializer(serializers.ModelSerializer):
    """Serializer for department budget"""
    department_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()
    utilization_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = DepartmentBudget
        fields = [
            'id', 'department', 'department_name', 'fiscal_year',
            'budget_type', 'allocated_amount', 'spent_amount',
            'remaining_amount', 'utilization_percentage', 'approved_by',
            'approved_by_name', 'approved_at', 'notes', 'created_at',
            'updated_at'
        ]
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_department_name(self, obj):
        return obj.department.name
    
    def get_approved_by_name(self, obj):
        return obj.approved_by.get_full_name() if obj.approved_by else None
    
    def get_remaining_amount(self, obj):
        return obj.remaining_amount
    
    def get_utilization_percentage(self, obj):
        return round(obj.utilization_percentage, 2)


class DepartmentBudgetListSerializer(serializers.ModelSerializer):
    """Simplified serializer for department budget lists"""
    department_name = serializers.SerializerMethodField()
    utilization_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = DepartmentBudget
        fields = [
            'id', 'department_name', 'fiscal_year', 'budget_type',
            'allocated_amount', 'spent_amount', 'utilization_percentage'
        ]
    
    def get_department_name(self, obj):
        return obj.department.name
    
    def get_utilization_percentage(self, obj):
        return round(obj.utilization_percentage, 2)


class DepartmentTreeSerializer(serializers.ModelSerializer):
    """Serializer for department tree structure"""
    sub_departments = serializers.SerializerMethodField()
    employees_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'head', 'employees_count', 'sub_departments'
        ]
    
    def get_sub_departments(self, obj):
        sub_depts = obj.sub_departments.filter(is_active=True)
        return DepartmentTreeSerializer(sub_depts, many=True).data
    
    def get_employees_count(self, obj):
        return obj.employees.filter(end_date__isnull=True).count()


class DepartmentStatsSerializer(serializers.ModelSerializer):
    """Serializer for department statistics"""
    total_employees = serializers.SerializerMethodField()
    active_positions = serializers.SerializerMethodField()
    total_budget = serializers.SerializerMethodField()
    budget_utilization = serializers.SerializerMethodField()
    avg_performance = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'code', 'total_employees', 'active_positions',
            'total_budget', 'budget_utilization', 'avg_performance'
        ]
    
    def get_total_employees(self, obj):
        return obj.employees.filter(end_date__isnull=True).count()
    
    def get_active_positions(self, obj):
        return obj.positions.filter(is_active=True).count()
    
    def get_total_budget(self, obj):
        current_year = 2025  # You might want to make this dynamic
        budgets = obj.budgets.filter(fiscal_year=current_year)
        return sum(budget.allocated_amount for budget in budgets)
    
    def get_budget_utilization(self, obj):
        current_year = 2025
        budgets = obj.budgets.filter(fiscal_year=current_year)
        if budgets.exists():
            total_allocated = sum(budget.allocated_amount for budget in budgets)
            total_spent = sum(budget.spent_amount for budget in budgets)
            if total_allocated > 0:
                return round((total_spent / total_allocated) * 100, 2)
        return 0
    
    def get_avg_performance(self, obj):
        assignments = obj.employees.filter(
            end_date__isnull=True,
            performance_rating__isnull=False
        )
        if assignments.exists():
            total_rating = sum(assignment.performance_rating for assignment in assignments)
            return round(total_rating / assignments.count(), 2)
        return None 