from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    # Departments
    path('', views.DepartmentListView.as_view(), name='department_list'),
    path('create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('tree/', views.department_tree, name='department_tree'),
    path('stats/', views.department_stats, name='department_stats'),
    path('<uuid:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('<uuid:pk>/update/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('<uuid:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    path('<uuid:department_id>/employees/', views.department_employees, name='department_employees'),
    
    # Positions
    path('positions/', views.PositionListView.as_view(), name='position_list'),
    path('positions/create/', views.PositionCreateView.as_view(), name='position_create'),
    path('positions/<uuid:pk>/', views.PositionDetailView.as_view(), name='position_detail'),
    path('positions/<uuid:pk>/update/', views.PositionUpdateView.as_view(), name='position_update'),
    path('positions/<uuid:pk>/delete/', views.PositionDeleteView.as_view(), name='position_delete'),
    
    # Employee Assignments
    path('assignments/', views.EmployeeAssignmentListView.as_view(), name='assignment_list'),
    path('assignments/create/', views.EmployeeAssignmentCreateView.as_view(), name='assignment_create'),
    path('assignments/<uuid:pk>/', views.EmployeeAssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<uuid:pk>/update/', views.EmployeeAssignmentUpdateView.as_view(), name='assignment_update'),
    path('assignments/<uuid:pk>/end/', views.end_assignment, name='assignment_end'),
    path('employees/available/', views.available_employees, name='available_employees'),
    
    # Budgets
    path('budgets/', views.DepartmentBudgetListView.as_view(), name='budget_list'),
    path('budgets/create/', views.DepartmentBudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<uuid:pk>/', views.DepartmentBudgetDetailView.as_view(), name='budget_detail'),
    path('budgets/<uuid:pk>/update/', views.DepartmentBudgetUpdateView.as_view(), name='budget_update'),
    path('budgets/<uuid:pk>/approve/', views.approve_budget, name='budget_approve'),
    
    # Permissions Management
    path('permissions/', views.PermissionListView.as_view(), name='permission_list'),
    path('permissions/grant/', views.grant_permission, name='permission_grant'),
    path('permissions/<uuid:permission_id>/revoke/', views.revoke_permission, name='permission_revoke'),
    path('permissions/entity/<str:entity_type>/<uuid:entity_id>/', views.entity_permissions, name='entity_permissions'),
    path('permissions/report/', views.permission_report, name='permission_report'),
    path('permissions/user/', views.UserPermissionsView.as_view(), name='user_permissions'),
    
    # Permission Templates
    path('permissions/templates/', views.PermissionTemplateListView.as_view(), name='permission_template_list'),
    path('permissions/templates/create/', views.create_permission_template, name='permission_template_create'),
    path('permissions/templates/<uuid:template_id>/update/', views.update_permission_template, name='permission_template_update'),
    path('permissions/templates/<uuid:template_id>/delete/', views.delete_permission_template, name='permission_template_delete'),
    path('permissions/templates/<uuid:template_id>/apply/', views.apply_template_to_users, name='permission_template_apply'),
    path('permissions/available/', views.get_available_permissions, name='available_permissions'),
    
    # Reports
    path('reports/organization-chart/', views.organization_chart, name='organization_chart'),
    path('reports/performance/', views.performance_report, name='performance_report'),
    path('reports/budget-utilization/', views.budget_utilization_report, name='budget_utilization'),
    
    # System Settings
    path('settings/', views.get_system_settings, name='get_system_settings'),
    path('settings/update/', views.update_system_settings, name='update_system_settings'),
    
    # System Backups
    path('backups/', views.list_system_backups, name='list_system_backups'),
    path('backups/create/', views.create_system_backup, name='create_system_backup'),
    path('backups/<uuid:backup_id>/download/', views.download_system_backup, name='download_system_backup'),
    path('backups/<uuid:backup_id>/delete/', views.delete_system_backup, name='delete_system_backup'),
] 