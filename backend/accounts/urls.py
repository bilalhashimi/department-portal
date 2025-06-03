from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password Management
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Profile Management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('profile/verify-email/', views.verify_email, name='verify_email'),
    
    # User Management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/search/', views.search_users, name='user_search'),
    path('users/stats/', views.user_stats, name='user_stats'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<uuid:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<uuid:user_id>/deactivate/', views.DeactivateUserView.as_view(), name='user_deactivate'),
    
    # Permissions
    path('users/permissions/', views.get_user_permissions, name='user_permissions'),
    
    # Login History
    path('login-history/', views.LoginHistoryView.as_view(), name='login_history'),
    
    # Group Management
    path('groups/', views.GroupListView.as_view(), name='group_list'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:pk>/update/', views.GroupUpdateView.as_view(), name='group_update'),
    path('groups/<int:pk>/delete/', views.GroupDeleteView.as_view(), name='group_delete'),
    path('groups/<int:group_id>/add-user/', views.add_user_to_group, name='add_user_to_group'),
    path('groups/<int:group_id>/remove-user/<uuid:user_id>/', views.remove_user_from_group, name='remove_user_from_group'),
] 