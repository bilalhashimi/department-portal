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
    
    # Budgets
    path('budgets/', views.DepartmentBudgetListView.as_view(), name='budget_list'),
    path('budgets/create/', views.DepartmentBudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<uuid:pk>/', views.DepartmentBudgetDetailView.as_view(), name='budget_detail'),
    path('budgets/<uuid:pk>/update/', views.DepartmentBudgetUpdateView.as_view(), name='budget_update'),
    path('budgets/<uuid:pk>/approve/', views.approve_budget, name='budget_approve'),
    
    # Reporting
    path('reports/org-chart/', views.organization_chart, name='org_chart'),
    path('reports/performance/', views.performance_report, name='performance_report'),
    path('reports/budget-utilization/', views.budget_utilization_report, name='budget_utilization'),
] 