from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document Categories
    path('categories/', views.DocumentCategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.DocumentCategoryCreateView.as_view(), name='category_create'),
    path('categories/<uuid:pk>/', views.DocumentCategoryDetailView.as_view(), name='category_detail'),
    path('categories/<uuid:pk>/update/', views.DocumentCategoryUpdateView.as_view(), name='category_update'),
    path('categories/<uuid:pk>/delete/', views.DocumentCategoryDeleteView.as_view(), name='category_delete'),
    
    # Documents
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('create/', views.DocumentCreateView.as_view(), name='document_create'),
    path('search/', views.document_search, name='document_search'),
    path('chat/', views.ai_chat, name='ai_chat'),
    path('bulk-action/', views.bulk_document_action, name='bulk_action'),
    path('<uuid:pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('<uuid:pk>/update/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('<uuid:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    path('<uuid:pk>/download/', views.download_document, name='document_download'),
    path('<uuid:pk>/view/', views.view_document, name='document_view'),
    path('<uuid:pk>/preview/', views.preview_document, name='document_preview'),
    
    # Document Sharing
    path('<uuid:document_id>/share/', views.DocumentShareView.as_view(), name='document_share'),
    path('shares/', views.DocumentShareListView.as_view(), name='share_list'),
    path('shares/<uuid:share_id>/revoke/', views.RevokeDocumentShareView.as_view(), name='revoke_share'),
    path('shared/<str:token>/', views.DocumentSharedAccessView.as_view(), name='shared_access'),
    
    # Document Permissions
    path('permissions/', views.DocumentPermissionListView.as_view(), name='permission_list'),
    path('permissions/create/', views.DocumentPermissionCreateView.as_view(), name='permission_create'),
    path('permissions/<uuid:pk>/update/', views.DocumentPermissionUpdateView.as_view(), name='permission_update'),
    path('permissions/<uuid:pk>/delete/', views.DocumentPermissionDeleteView.as_view(), name='permission_delete'),
    
    # Document Activities & Comments
    path('<uuid:document_id>/activities/', views.DocumentActivityListView.as_view(), name='document_activities'),
    path('<uuid:document_id>/comments/', views.DocumentCommentListView.as_view(), name='document_comments'),
    path('<uuid:document_id>/comments/create/', views.DocumentCommentCreateView.as_view(), name='comment_create'),
    
    # Document Tags
    path('tags/', views.DocumentTagListView.as_view(), name='tag_list'),
    path('tags/create/', views.DocumentTagCreateView.as_view(), name='tag_create'),
    path('tags/<uuid:pk>/', views.DocumentTagDetailView.as_view(), name='tag_detail'),
    path('tags/<uuid:pk>/update/', views.DocumentTagUpdateView.as_view(), name='tag_update'),
    path('tags/<uuid:pk>/delete/', views.DocumentTagDeleteView.as_view(), name='tag_delete'),
] 