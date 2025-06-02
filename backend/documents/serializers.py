from rest_framework import serializers
from .models import (
    DocumentCategory, Document, DocumentTag, DocumentPermission,
    DocumentActivity, DocumentComment, DocumentShare
)
from django.utils.text import slugify


class DocumentCategorySerializer(serializers.ModelSerializer):
    """Serializer for document category"""
    parent_category_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    hierarchy = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'name', 'slug', 'description', 'parent_category',
            'parent_category_name', 'department', 'department_name',
            'is_public', 'color', 'icon', 'is_active', 'documents_count',
            'hierarchy', 'created_at', 'updated_at'
        ]
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')
    
    def get_parent_category_name(self, obj):
        return obj.parent_category.name if obj.parent_category else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_documents_count(self, obj):
        return obj.documents.count()
    
    def get_hierarchy(self, obj):
        return obj.get_full_hierarchy()


class DocumentCategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for document category lists"""
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'name', 'color', 'icon', 'documents_count', 'is_public'
        ]
    
    def get_documents_count(self, obj):
        return obj.documents.filter(status='published').count()


class DocumentTagSerializer(serializers.ModelSerializer):
    """Serializer for document tag"""
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentTag
        fields = [
            'id', 'name', 'slug', 'color', 'documents_count', 'created_at'
        ]
        read_only_fields = ('id', 'slug', 'created_at')
    
    def get_documents_count(self, obj):
        return obj.documents.count()


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for document model"""
    category_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    owned_by_name = serializers.SerializerMethodField()
    reviewer_name = serializers.SerializerMethodField()
    tags = DocumentTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    file_size_mb = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'slug', 'description', 'file', 'file_size',
            'file_size_mb', 'file_type', 'category', 'category_name',
            'tags', 'tag_ids', 'created_by', 'created_by_name',
            'owned_by', 'owned_by_name', 'status', 'priority',
            'reviewer', 'reviewer_name', 'reviewed_at', 'review_notes',
            'published_at', 'expires_at', 'version', 'is_latest_version',
            'previous_version', 'download_count', 'view_count',
            'comments_count', 'created_at', 'updated_at'
        ]
        read_only_fields = (
            'id', 'slug', 'file_size', 'file_type', 'created_by',
            'download_count', 'view_count', 'created_at', 'updated_at'
        )
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name()
    
    def get_owned_by_name(self, obj):
        return obj.owned_by.get_full_name()
    
    def get_reviewer_name(self, obj):
        return obj.reviewer.get_full_name() if obj.reviewer else None
    
    def get_file_size_mb(self, obj):
        return obj.file_size_mb
    
    def get_comments_count(self, obj):
        return obj.comments.count()
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        validated_data['created_by'] = self.context['request'].user
        if not validated_data.get('owned_by'):
            validated_data['owned_by'] = self.context['request'].user
        
        document = Document.objects.create(**validated_data)
        
        if tag_ids:
            tags = DocumentTag.objects.filter(id__in=tag_ids)
            document.tags.set(tags)
        
        return document
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        if tag_ids is not None:
            tags = DocumentTag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)
        
        return instance


class DocumentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for document lists"""
    category_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'category_name', 'created_by_name',
            'status', 'priority', 'file_type', 'file_size_mb',
            'version', 'created_at', 'updated_at'
        ]
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name()
    
    def get_file_size_mb(self, obj):
        return obj.file_size_mb


class DocumentPermissionSerializer(serializers.ModelSerializer):
    """Serializer for document permission"""
    document_title = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    granted_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentPermission
        fields = [
            'id', 'document', 'document_title', 'user', 'user_name',
            'department', 'department_name', 'permission', 'granted_by',
            'granted_by_name', 'expires_at', 'is_active', 'created_at'
        ]
        read_only_fields = ('id', 'granted_by', 'created_at')
    
    def get_document_title(self, obj):
        return obj.document.title
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() if obj.user else None
    
    def get_department_name(self, obj):
        return obj.department.name if obj.department else None
    
    def get_granted_by_name(self, obj):
        return obj.granted_by.get_full_name()
    
    def create(self, validated_data):
        validated_data['granted_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentActivitySerializer(serializers.ModelSerializer):
    """Serializer for document activity"""
    document_title = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentActivity
        fields = [
            'id', 'document', 'document_title', 'user', 'user_name',
            'action', 'description', 'ip_address', 'previous_version',
            'new_version', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')
    
    def get_document_title(self, obj):
        return obj.document.title
    
    def get_user_name(self, obj):
        return obj.user.get_full_name()


class DocumentCommentSerializer(serializers.ModelSerializer):
    """Serializer for document comment"""
    author_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentComment
        fields = [
            'id', 'document', 'author', 'author_name', 'content',
            'parent_comment', 'is_resolved', 'resolved_by',
            'resolved_by_name', 'resolved_at', 'replies', 'replies_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = (
            'id', 'author', 'resolved_by', 'resolved_at',
            'created_at', 'updated_at'
        )
    
    def get_author_name(self, obj):
        return obj.author.get_full_name()
    
    def get_resolved_by_name(self, obj):
        return obj.resolved_by.get_full_name() if obj.resolved_by else None
    
    def get_replies(self, obj):
        if obj.parent_comment is None:  # Only get replies for top-level comments
            replies = obj.replies.all()
            return DocumentCommentSerializer(replies, many=True, context=self.context).data
        return []
    
    def get_replies_count(self, obj):
        return obj.replies.count()
    
    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document version information"""
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'version', 'created_by_name', 'file', 'file_size_mb',
            'is_latest_version', 'created_at'
        ]
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name()


class DocumentSearchSerializer(serializers.ModelSerializer):
    """Serializer for document search results"""
    category_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    tags = DocumentTagSerializer(many=True, read_only=True)
    highlight = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category_name',
            'created_by_name', 'status', 'tags', 'file_type',
            'created_at', 'highlight'
        ]
    
    def get_category_name(self, obj):
        return obj.category.name
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name()
    
    def get_highlight(self, obj):
        # This would be used for search result highlighting
        # Implementation depends on search backend (e.g., Elasticsearch)
        return getattr(obj, '_highlight', {})


class DocumentStatsSerializer(serializers.Serializer):
    """Serializer for document statistics"""
    total_documents = serializers.IntegerField()
    documents_by_status = serializers.DictField()
    documents_by_category = serializers.DictField()
    recent_activities = DocumentActivitySerializer(many=True)
    top_downloaded = DocumentListSerializer(many=True)
    total_downloads = serializers.IntegerField()
    total_views = serializers.IntegerField()


class BulkDocumentActionSerializer(serializers.Serializer):
    """Serializer for bulk document actions"""
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        ('delete', 'Delete'),
        ('archive', 'Archive'),
        ('publish', 'Publish'),
        ('change_category', 'Change Category'),
        ('add_tags', 'Add Tags'),
        ('remove_tags', 'Remove Tags'),
    ])
    category_id = serializers.UUIDField(required=False)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    
    def validate(self, attrs):
        action = attrs.get('action')
        if action == 'change_category' and not attrs.get('category_id'):
            raise serializers.ValidationError("category_id is required for change_category action")
        if action in ['add_tags', 'remove_tags'] and not attrs.get('tag_ids'):
            raise serializers.ValidationError("tag_ids is required for tag actions")
        return attrs 


class DocumentShareSerializer(serializers.ModelSerializer):
    """Serializer for document sharing"""
    document_title = serializers.SerializerMethodField()
    shared_by_name = serializers.SerializerMethodField()
    shared_with_user_name = serializers.SerializerMethodField()
    shared_with_department_name = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    public_link_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentShare
        fields = [
            'id', 'document', 'document_title', 'share_type', 'access_level',
            'shared_with_user', 'shared_with_user_name', 'shared_with_department',
            'shared_with_department_name', 'public_link_token', 'public_link_url',
            'shared_by', 'shared_by_name', 'shared_at', 'expires_at', 'is_active',
            'access_count', 'last_accessed_at', 'allow_download', 'allow_reshare',
            'notify_on_access', 'is_expired'
        ]
        read_only_fields = [
            'id', 'shared_by', 'shared_at', 'access_count', 'last_accessed_at',
            'public_link_token'
        ]
    
    def get_document_title(self, obj):
        return obj.document.title
    
    def get_shared_by_name(self, obj):
        return obj.shared_by.get_full_name()
    
    def get_shared_with_user_name(self, obj):
        return obj.shared_with_user.get_full_name() if obj.shared_with_user else None
    
    def get_shared_with_department_name(self, obj):
        return obj.shared_with_department.name if obj.shared_with_department else None
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_public_link_url(self, obj):
        if obj.share_type == 'public_link' and obj.public_link_token:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(
                    f'/api/v1/documents/shared/{obj.public_link_token}/'
                )
        return None
    
    def validate(self, attrs):
        """Validate share data"""
        share_type = attrs.get('share_type')
        
        if share_type == 'user' and not attrs.get('shared_with_user'):
            raise serializers.ValidationError("shared_with_user is required for user shares")
        
        if share_type == 'department' and not attrs.get('shared_with_department'):
            raise serializers.ValidationError("shared_with_department is required for department shares")
        
        # Clear inappropriate fields based on share type
        if share_type != 'user':
            attrs['shared_with_user'] = None
        if share_type != 'department':
            attrs['shared_with_department'] = None
        if share_type != 'public_link':
            attrs['public_link_token'] = None
            attrs['link_password'] = None
        
        return attrs
    
    def create(self, validated_data):
        validated_data['shared_by'] = self.context['request'].user
        return super().create(validated_data)


class ShareDocumentSerializer(serializers.Serializer):
    """Serializer for sharing document requests"""
    share_type = serializers.ChoiceField(choices=DocumentShare.SHARE_TYPE_CHOICES)
    access_level = serializers.ChoiceField(
        choices=DocumentShare.ACCESS_LEVEL_CHOICES,
        default='view'
    )
    
    # User sharing
    user_email = serializers.EmailField(required=False)
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=False
    )
    
    # Department sharing
    department_id = serializers.UUIDField(required=False)
    
    # Public link sharing
    link_password = serializers.CharField(required=False, allow_blank=True)
    expires_at = serializers.DateTimeField(required=False)
    
    # Additional options
    allow_download = serializers.BooleanField(default=True)
    allow_reshare = serializers.BooleanField(default=False)
    notify_on_access = serializers.BooleanField(default=False)
    send_notification = serializers.BooleanField(default=True)
    message = serializers.CharField(required=False, allow_blank=True, max_length=500)
    
    def validate(self, attrs):
        share_type = attrs.get('share_type')
        
        if share_type == 'user':
            if not attrs.get('user_email') and not attrs.get('user_ids'):
                raise serializers.ValidationError(
                    "Either user_email or user_ids is required for user shares"
                )
        elif share_type == 'department':
            if not attrs.get('department_id'):
                raise serializers.ValidationError(
                    "department_id is required for department shares"
                )
        
        return attrs


class DocumentAccessSerializer(serializers.Serializer):
    """Serializer for document access via public links"""
    password = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        fields = ['password']


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for document retrieval"""
    category_name = serializers.SerializerMethodField()
    owned_by_name = serializers.SerializerMethodField()
    tags = DocumentTagSerializer(many=True, read_only=True)
    permissions = DocumentPermissionSerializer(many=True, read_only=True)
    activities = DocumentActivitySerializer(many=True, read_only=True)
    comments = DocumentCommentSerializer(many=True, read_only=True)
    shares = DocumentShareSerializer(many=True, read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = '__all__'
    
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    
    def get_owned_by_name(self, obj):
        return obj.owned_by.get_full_name() if obj.owned_by else None
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for document creation"""
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    
    # Document visibility options
    visibility = serializers.ChoiceField(
        choices=[
            ('private', 'Private (Admin Only)'),
            ('department', 'Department'),
            ('users', 'Specific Users'),
            ('public', 'Public')
        ],
        default='private'
    )
    
    # For department sharing
    shared_departments = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    
    # For user sharing
    shared_user_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True
    )
    
    # Access permissions
    allow_download = serializers.BooleanField(default=True)
    allow_reshare = serializers.BooleanField(default=False)
    
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'file', 'category', 'tag_names',
            'status', 'version', 'visibility', 
            'shared_departments', 'shared_user_emails', 
            'allow_download', 'allow_reshare'
        ]
    
    def create(self, validated_data):
        # Extract visibility options
        visibility = validated_data.pop('visibility', 'private')
        shared_departments = validated_data.pop('shared_departments', [])
        shared_user_emails = validated_data.pop('shared_user_emails', [])
        allow_download = validated_data.pop('allow_download', True)
        allow_reshare = validated_data.pop('allow_reshare', False)
        tag_names = validated_data.pop('tag_names', [])
        
        # Set both created_by and owned_by to the current user
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['owned_by'] = user
        
        document = super().create(validated_data)
        
        # Handle tags
        if tag_names:
            for tag_name in tag_names:
                tag, created = DocumentTag.objects.get_or_create(
                    name=tag_name.strip(),
                    defaults={'slug': slugify(tag_name.strip())}
                )
                document.tags.add(tag)
        
        # Handle document visibility and permissions
        self._handle_document_visibility(
            document, visibility, shared_departments, 
            shared_user_emails, allow_download, allow_reshare
        )
        
        return document
    
    def _handle_document_visibility(self, document, visibility, shared_departments, 
                                   shared_user_emails, allow_download, allow_reshare):
        """Handle document visibility and create appropriate shares/permissions"""
        from django.contrib.auth import get_user_model
        from departments.models import Department
        
        User = get_user_model()
        
        if visibility == 'department' and shared_departments:
            # Share with specific departments
            for dept_id in shared_departments:
                try:
                    department = Department.objects.get(id=dept_id)
                    DocumentShare.objects.create(
                        document=document,
                        share_type='department',
                        access_level='download' if allow_download else 'view',
                        shared_with_department=department,
                        shared_by=self.context['request'].user,
                        allow_download=allow_download,
                        allow_reshare=allow_reshare,
                        is_active=True
                    )
                except Department.DoesNotExist:
                    continue
        
        elif visibility == 'users' and shared_user_emails:
            # Share with specific users
            for email in shared_user_emails:
                try:
                    user = User.objects.get(email=email)
                    DocumentShare.objects.create(
                        document=document,
                        share_type='user',
                        access_level='download' if allow_download else 'view',
                        shared_with_user=user,
                        shared_by=self.context['request'].user,
                        allow_download=allow_download,
                        allow_reshare=allow_reshare,
                        is_active=True
                    )
                except User.DoesNotExist:
                    continue
        
        elif visibility == 'public':
            # Create public link
            import secrets
            DocumentShare.objects.create(
                document=document,
                share_type='public_link',
                access_level='download' if allow_download else 'view',
                public_link_token=secrets.token_urlsafe(32),
                shared_by=self.context['request'].user,
                allow_download=allow_download,
                allow_reshare=allow_reshare,
                is_active=True
            )
        
        # For 'private' visibility, no additional sharing is created
        # Document remains accessible only to admin and owner


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for document updates"""
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'file', 'category', 'tag_names',
            'status', 'priority', 'version'
        ]
    
    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        
        # Update document fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_names is not None:
            instance.tags.clear()
            for tag_name in tag_names:
                tag, created = DocumentTag.objects.get_or_create(
                    name=tag_name.strip(),
                    defaults={'slug': slugify(tag_name.strip())}
                )
                instance.tags.add(tag)
        
        return instance 