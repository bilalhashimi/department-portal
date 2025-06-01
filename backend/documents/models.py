from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
import uuid
import os
from django.utils import timezone


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Generate filename
    filename = f"{uuid.uuid4()}.{ext}"
    # Return path
    return os.path.join('documents', str(instance.category.id), filename)


class DocumentCategory(models.Model):
    """
    Categories for organizing documents
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    
    # Hierarchy
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_categories'
    )
    
    # Permissions
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_categories'
    )
    is_public = models.BooleanField(default=False)
    
    # Colors for UI
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code for category")
    icon = models.CharField(max_length=50, default='folder', help_text="Icon name for category")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents_documentcategory'
        verbose_name = 'Document Category'
        verbose_name_plural = 'Document Categories'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_full_hierarchy(self):
        """Return full category hierarchy as string"""
        if self.parent_category:
            return f"{self.parent_category.get_full_hierarchy()} > {self.name}"
        return self.name


class Document(models.Model):
    """
    Main document model
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('obsolete', 'Obsolete'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField(blank=True)
    
    # File Information
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=[
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
            'txt', 'rtf', 'odt', 'ods', 'odp', 'csv', 'md'
        ])]
    )
    file_size = models.PositiveIntegerField(null=True, blank=True)  # Size in bytes
    file_type = models.CharField(max_length=100, blank=True)
    
    # Organization
    category = models.ForeignKey(DocumentCategory, on_delete=models.CASCADE, related_name='documents')
    tags = models.ManyToManyField('DocumentTag', blank=True, related_name='documents')
    
    # Ownership and Control
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_documents'
    )
    owned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_documents'
    )
    
    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Review Process
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_to_review'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Publishing
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Version Control
    version = models.CharField(max_length=20, default='1.0')
    is_latest_version = models.BooleanField(default=True)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newer_versions'
    )
    
    # Analytics
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents_document'
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['created_by']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if self.file and not self.file_size:
            self.file_size = self.file.size
        if self.file and not self.file_type:
            self.file_type = self.file.name.split('.')[-1].upper()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    @property
    def file_size_mb(self):
        """Return file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0


class DocumentTag(models.Model):
    """
    Tags for document categorization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#6B7280', help_text="Hex color code for tag")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents_documenttag'
        verbose_name = 'Document Tag'
        verbose_name_plural = 'Document Tags'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class DocumentPermission(models.Model):
    """
    Document access permissions
    """
    PERMISSION_CHOICES = [
        ('view', 'View'),
        ('download', 'Download'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('share', 'Share'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='permissions')
    
    # Grant permission to user or department
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_permissions'
    )
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='document_permissions'
    )
    
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='granted_permissions'
    )
    
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents_documentpermission'
        verbose_name = 'Document Permission'
        verbose_name_plural = 'Document Permissions'
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(department__isnull=False),
                name='either_user_or_department'
            )
        ]
    
    def __str__(self):
        target = self.user.get_full_name() if self.user else self.department.name
        return f"{self.document.title} - {self.permission} for {target}"


class DocumentActivity(models.Model):
    """
    Track document activities for audit trail
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('viewed', 'Viewed'),
        ('downloaded', 'Downloaded'),
        ('edited', 'Edited'),
        ('deleted', 'Deleted'),
        ('shared', 'Shared'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_activities'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional context
    previous_version = models.CharField(max_length=20, blank=True)
    new_version = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents_documentactivity'
        verbose_name = 'Document Activity'
        verbose_name_plural = 'Document Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} {self.action} {self.document.title}"


class DocumentComment(models.Model):
    """
    Comments on documents
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='document_comments'
    )
    
    content = models.TextField()
    
    # Reply system
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_comments'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents_documentcomment'
        verbose_name = 'Document Comment'
        verbose_name_plural = 'Document Comments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()} on {self.document.title}"


class DocumentShare(models.Model):
    """
    Document sharing relationships
    """
    SHARE_TYPE_CHOICES = [
        ('user', 'Individual User'),
        ('department', 'Department'),
        ('public_link', 'Public Link'),
    ]
    
    ACCESS_LEVEL_CHOICES = [
        ('view', 'View Only'),
        ('download', 'View & Download'),
        ('comment', 'View, Download & Comment'),
        ('edit', 'Full Edit Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='shares')
    
    # Sharing details
    share_type = models.CharField(max_length=20, choices=SHARE_TYPE_CHOICES)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='view')
    
    # Share targets
    shared_with_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_document_shares'
    )
    shared_with_department = models.ForeignKey(
        'departments.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='department_document_shares'
    )
    
    # Public link sharing
    public_link_token = models.CharField(max_length=64, null=True, blank=True, unique=True)
    link_password = models.CharField(max_length=128, null=True, blank=True)
    
    # Sharing metadata
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_documents'
    )
    shared_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Access tracking
    is_active = models.BooleanField(default=True)
    access_count = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    last_accessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_accessed_shares'
    )
    
    # Additional settings
    allow_download = models.BooleanField(default=True)
    allow_reshare = models.BooleanField(default=False)
    notify_on_access = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'documents_documentshare'
        verbose_name = 'Document Share'
        verbose_name_plural = 'Document Shares'
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(share_type='user', shared_with_user__isnull=False) |
                    models.Q(share_type='department', shared_with_department__isnull=False) |
                    models.Q(share_type='public_link', public_link_token__isnull=False)
                ),
                name='valid_share_target'
            )
        ]
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['shared_with_user']),
            models.Index(fields=['shared_with_department']),
            models.Index(fields=['public_link_token']),
            models.Index(fields=['expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Generate public link token if needed
        if self.share_type == 'public_link' and not self.public_link_token:
            import secrets
            self.public_link_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.share_type == 'user' and self.shared_with_user:
            target = self.shared_with_user.get_full_name()
        elif self.share_type == 'department' and self.shared_with_department:
            target = self.shared_with_department.name
        else:
            target = "Public Link"
        
        return f"{self.document.title} shared with {target}"
    
    def is_expired(self):
        """Check if the share has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def can_access(self, user):
        """Check if a user can access this share"""
        if not self.is_active or self.is_expired():
            return False
        
        if self.share_type == 'user':
            return self.shared_with_user == user
        elif self.share_type == 'department':
            return user.department_assignments.filter(
                department=self.shared_with_department,
                end_date__isnull=True
            ).exists()
        elif self.share_type == 'public_link':
            return True  # Public links can be accessed by anyone with the token
        
        return False
