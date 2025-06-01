from django.contrib import admin
from .models import (
    DocumentCategory, DocumentTag, Document, 
    DocumentPermission, DocumentActivity, DocumentComment, DocumentShare
)

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'is_public', 'created_at']
    list_filter = ['is_public', 'department', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'priority', 'created_by', 'file_type', 'created_at']
    list_filter = ['status', 'priority', 'category', 'file_type', 'created_at']
    search_fields = ['title', 'description', 'created_by__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['id', 'file_size', 'file_type', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'file')
        }),
        ('Organization', {
            'fields': ('category', 'tags')
        }),
        ('Ownership', {
            'fields': ('created_by', 'owned_by')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Metadata', {
            'fields': ('id', 'file_size', 'file_type', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new document
            obj.created_by = request.user
            if not obj.owned_by:
                obj.owned_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ['document', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['document__title', 'content', 'author__email']

@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ['document', 'permission', 'user', 'department', 'granted_by', 'is_active']
    list_filter = ['permission', 'is_active', 'created_at']
    search_fields = ['document__title', 'user__email']

@admin.register(DocumentShare)
class DocumentShareAdmin(admin.ModelAdmin):
    list_display = ['document', 'share_type', 'access_level', 'shared_by', 'is_active']
    list_filter = ['share_type', 'access_level', 'is_active']
    search_fields = ['document__title']

@admin.register(DocumentActivity)
class DocumentActivityAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['document__title', 'user__email']
