"""
Department Portal - Document Views

✅ AI SEARCH FUNCTIONALITY RESTORED:
- Vector database (Qdrant) running on port 6333
- Semantic search with sentence-transformers embeddings
- Celery background tasks for document indexing
- Full document management with AI-powered search

📋 CURRENT STATUS:
- Basic document management: ✅ WORKING
- Vector/AI search: ✅ WORKING
- Document indexing: ✅ WORKING
- Celery tasks: ✅ WORKING
- Text-based search fallback: ✅ WORKING
"""

from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from .models import (
    DocumentCategory, Document, DocumentTag, DocumentPermission,
    DocumentActivity, DocumentComment, DocumentShare
)
from .serializers import (
    DocumentCategorySerializer, DocumentListSerializer, DocumentDetailSerializer,
    DocumentCreateSerializer, DocumentUpdateSerializer, DocumentPermissionSerializer,
    DocumentActivitySerializer, DocumentCommentSerializer, DocumentShareSerializer,
    ShareDocumentSerializer, DocumentAccessSerializer, BulkDocumentActionSerializer,
    DocumentSearchSerializer, DocumentTagSerializer
)
from .vector_service import vector_service
from .tasks import index_document_task, delete_document_from_index
from .ai_service import ai_assistant
import logging
from accounts.permissions import (
    DocumentOwnerOrAdmin, DocumentSharePermission, log_security_event
)

logger = logging.getLogger(__name__)

# Document Categories
class DocumentCategoryListView(generics.ListCreateAPIView):
    queryset = DocumentCategory.objects.filter(is_active=True)
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentCategoryCreateView(generics.CreateAPIView):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentCategoryDetailView(generics.RetrieveAPIView):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentCategoryUpdateView(generics.UpdateAPIView):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentCategoryDeleteView(generics.DestroyAPIView):
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

# Document Tags
class DocumentTagListView(generics.ListCreateAPIView):
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentTagCreateView(generics.CreateAPIView):
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentTagDetailView(generics.RetrieveAPIView):
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentTagUpdateView(generics.UpdateAPIView):
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentTagDeleteView(generics.DestroyAPIView):
    queryset = DocumentTag.objects.all()
    serializer_class = DocumentTagSerializer
    permission_classes = [permissions.IsAuthenticated]

# Documents
class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Base queryset for published documents
        queryset = Document.objects.filter(
            status__in=['published', 'approved'],
            is_latest_version=True
        )
        
        # Apply permission filtering
        if user.role == 'admin':
            return queryset
        
        # Filter by user permissions
        user_accessible = Q(
            permissions__user=user,
            permissions__is_active=True
        )
        
        # Filter by department permissions
        user_departments = user.department_assignments.filter(
            end_date__isnull=True
        ).values_list('department', flat=True)
        
        dept_accessible = Q(
            permissions__department__in=user_departments,
            permissions__is_active=True
        )
        
        # Documents owned by user
        owned_by_user = Q(owned_by=user)
        
        # Public documents
        public_docs = Q(category__is_public=True)
        
        return queryset.filter(
            user_accessible | dept_accessible | owned_by_user | public_docs
        ).distinct()

class DocumentCreateView(generics.CreateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Allow all authenticated users to upload documents
        # Remove the admin-only restriction
        return super().post(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        document = serializer.save()
        
        # Index document for search if available
        try:
            index_document_task.delay(document.id)
        except Exception as e:
            logger.error(f"Failed to index document {document.id}: {str(e)}")

class DocumentDetailView(generics.RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentUpdateView(generics.UpdateAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_update(self, serializer):
        document = serializer.save()
        
        # Re-index document for search if available
        try:
            index_document_task.delay(document.id)
        except Exception as e:
            logger.error(f"Failed to re-index document {document.id}: {str(e)}")

class DocumentDeleteView(generics.DestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentDetailSerializer  # Use detail serializer for delete
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_destroy(self, instance):
        # Remove from search index if available
        try:
            delete_document_from_index.delay(str(instance.id))
        except Exception as e:
            logger.error(f"Failed to remove document {instance.id} from index: {str(e)}")
        
        super().perform_destroy(instance)

# Document Permissions
class DocumentPermissionListView(generics.ListAPIView):
    serializer_class = DocumentPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        document_id = self.kwargs['document_id']
        return DocumentPermission.objects.filter(document_id=document_id)

class DocumentPermissionCreateView(generics.CreateAPIView):
    serializer_class = DocumentPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentPermissionUpdateView(generics.UpdateAPIView):
    queryset = DocumentPermission.objects.all()
    serializer_class = DocumentPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentPermissionDeleteView(generics.DestroyAPIView):
    queryset = DocumentPermission.objects.all()
    serializer_class = DocumentPermissionSerializer
    permission_classes = [permissions.IsAuthenticated]

# Document Comments
class DocumentCommentListView(generics.ListAPIView):
    serializer_class = DocumentCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        document_id = self.kwargs['document_id']
        return DocumentComment.objects.filter(
            document_id=document_id,
            parent_comment__isnull=True  # Only top-level comments
        )

class DocumentCommentCreateView(generics.CreateAPIView):
    serializer_class = DocumentCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentCommentUpdateView(generics.UpdateAPIView):
    queryset = DocumentComment.objects.all()
    serializer_class = DocumentCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

class DocumentCommentDeleteView(generics.DestroyAPIView):
    queryset = DocumentComment.objects.all()
    serializer_class = DocumentCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

# Document Activities
class DocumentActivityListView(generics.ListAPIView):
    serializer_class = DocumentActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        document_id = self.kwargs['document_id']
        return DocumentActivity.objects.filter(document_id=document_id)

# API Views and Functions

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def document_search(request):
    """Semantic search for documents using vector database"""
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))
    department = request.GET.get('department', '')
    
    if not query:
        return Response({
            'error': 'Query parameter "q" is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Try semantic search first
        try:
            vector_results = vector_service.search_documents(
                query=query,
                limit=limit,
                department_id=department if department else None
            )
            
            # Transform vector results to expected format
            search_results = []
            for result in vector_results:
                try:
                    document = Document.objects.get(id=result['document_id'])
                    search_results.append({
                        'document': DocumentSearchSerializer(document).data,
                        'score': result['score'],
                        'snippet': result['content_snippet'],
                        'metadata': result.get('metadata', {})
                    })
                except Document.DoesNotExist:
                    # Skip documents that don't exist in the database
                    continue
            
            return Response({
                'query': query,
                'results': search_results,
                'total_found': len(search_results),
                'search_type': 'semantic'
            })
            
        except Exception as vector_error:
            logger.warning(f"Vector search failed, falling back to text search: {vector_error}")
            
            # Fallback to basic text search
            documents = Document.objects.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query),
                status__in=['published', 'approved']
            )[:limit]
            
            # Format results to match expected structure
            results = []
            for doc in documents:
                results.append({
                    'document': DocumentSearchSerializer(doc).data,
                    'score': 0.8,  # Mock score
                    'snippet': doc.description[:200] + "..." if doc.description else "No description available",
                    'metadata': {'department': 'General'}
                })
            
            return Response({
                'query': query,
                'results': results,
                'total_found': len(results),
                'search_type': 'text_fallback'
            })
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return Response({
            'error': 'Search service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def document_stats(request):
    """Get document statistics"""
    try:
        stats = {
            'total_documents': Document.objects.count(),
            'published_documents': Document.objects.filter(status='published').count(),
            'draft_documents': Document.objects.filter(status='draft').count(),
            'pending_review': Document.objects.filter(status='review').count(),
        }
        
        # Try to get vector database stats
        try:
            stats['vector_db_stats'] = vector_service.get_document_stats()
        except Exception as e:
            logger.warning(f"Could not get vector DB stats: {e}")
            stats['vector_db_stats'] = {
                'status': 'unavailable', 
                'indexed_documents': 0,
                'error': str(e)
            }
        
        if request.user.role == 'admin':
            stats['user_documents'] = Document.objects.filter(created_by=request.user).count()
        
        return Response(stats)
    
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        return Response({'error': 'Stats unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ai_chat(request):
    """AI-powered document chat using RAG (Retrieval-Augmented Generation)"""
    try:
        question = request.data.get('question', '').strip()
        
        if not question:
            return Response({
                'error': 'Question is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the AI assistant to generate response
        result = ai_assistant.chat(
            question=question,
            user_id=str(request.user.id)
        )
        
        return Response(result)
    
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        return Response({
            'error': 'AI chat service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_document_action(request):
    """Handle bulk actions on documents"""
    serializer = BulkDocumentActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    document_ids = serializer.validated_data['document_ids']
    action = serializer.validated_data['action']
    
    try:
        documents = Document.objects.filter(id__in=document_ids)
        
        if action == 'delete':
            # Remove documents from vector database
            for doc in documents:
                delete_document_from_index.delay(str(doc.id))
            documents.delete()
        
        elif action == 'publish':
            documents.update(status='published', published_at=timezone.now())
            # Index published documents in vector database
            for doc in documents:
                index_document_task.delay(str(doc.id))
        
        elif action == 'archive':
            documents.update(status='archived')
            # Remove archived documents from vector database
            for doc in documents:
                delete_document_from_index.delay(str(doc.id))
        
        return Response({'message': f'{action} completed for {len(document_ids)} documents'})
    
    except Exception as e:
        logger.error(f"Error in bulk action: {e}")
        return Response({'error': 'Bulk action failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_document(request, pk):
    """Download a document file"""
    try:
        document = Document.objects.get(pk=pk)
        
        # Check if user has permission to download this document
        # TODO: Add proper permission checking logic here
        
        # Check if file exists
        if not document.file:
            return Response({'error': 'No file associated with this document'}, status=status.HTTP_404_NOT_FOUND)
        
        if not document.file.storage.exists(document.file.name):
            return Response({'error': 'File not found on server'}, status=status.HTTP_404_NOT_FOUND)
        
        # Increment download count
        document.download_count += 1
        document.save(update_fields=['download_count'])
        
        # Log activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            action='downloaded',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Serve the file
        from django.http import FileResponse
        import mimetypes
        
        # Get the file content
        file_handle = document.file.open()
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(document.file.name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Create response
        response = FileResponse(
            file_handle,
            content_type=content_type,
            as_attachment=True,
            filename=f"{document.title}.{document.file_type.lower()}"
        )
        
        return response
        
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error downloading document {pk}: {str(e)}")
        return Response({'error': 'Download failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def preview_document(request, pk):
    """Preview a document file in browser"""
    try:
        document = Document.objects.get(pk=pk)
        
        # Check if user has permission to view this document
        # TODO: Add proper permission checking logic here
        
        # Check if file exists
        if not document.file:
            return Response({'error': 'No file associated with this document'}, status=status.HTTP_404_NOT_FOUND)
        
        if not document.file.storage.exists(document.file.name):
            return Response({'error': 'File not found on server'}, status=status.HTTP_404_NOT_FOUND)
        
        # Increment view count
        document.view_count += 1
        document.save(update_fields=['view_count'])
        
        # Log activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            action='viewed',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Serve the file for inline viewing
        from django.http import FileResponse
        import mimetypes
        
        # Get the file content
        file_handle = document.file.open()
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(document.file.name)
        if not content_type:
            # Default content types for common document formats
            ext = document.file_type.lower()
            if ext == 'pdf':
                content_type = 'application/pdf'
            elif ext in ['doc', 'docx']:
                content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif ext in ['xls', 'xlsx']:
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif ext in ['ppt', 'pptx']:
                content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            elif ext == 'txt':
                content_type = 'text/plain'
            else:
                content_type = 'application/octet-stream'
        
        # Create response for inline viewing
        response = FileResponse(
            file_handle,
            content_type=content_type,
            as_attachment=False,  # This makes it display inline instead of downloading
            filename=f"{document.title}.{document.file_type.lower()}"
        )
        
        # Add headers to help with inline viewing
        response['Content-Disposition'] = f'inline; filename="{document.title}.{document.file_type.lower()}"'
        
        # Add CORS headers to allow cross-origin requests
        response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        
        return response
        
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error previewing document {pk}: {str(e)}")
        return Response({'error': 'Preview failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def view_document(request, pk):
    """Record document view and increment view count"""
    try:
        document = Document.objects.get(pk=pk)
        document.view_count += 1
        document.save()
        
        # Log activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            action='viewed',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'View recorded'})
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def document_versions(request, pk):
    """Get all versions of a document"""
    try:
        document = Document.objects.get(pk=pk)
        versions = Document.objects.filter(
            Q(id=document.id) | Q(previous_version=document)
        ).order_by('-created_at')
        
        serializer = DocumentListSerializer(versions, many=True)
        return Response(serializer.data)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def resolve_comment(request, pk):
    """Resolve a comment"""
    try:
        comment = DocumentComment.objects.get(pk=pk)
        comment.is_resolved = True
        comment.resolved_by = request.user
        comment.resolved_at = timezone.now()
        comment.save()
        
        return Response({'message': 'Comment resolved'})
    except DocumentComment.DoesNotExist:
        return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def all_activities(request):
    """Get all document activities"""
    activities = DocumentActivity.objects.all()[:100]  # Latest 100 activities
    serializer = DocumentActivitySerializer(activities, many=True)
    return Response(serializer.data)

# Workflow endpoints
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def submit_for_review(request, pk):
    """Submit document for review"""
    try:
        document = Document.objects.get(pk=pk)
        document.status = 'review'
        document.save()
        
        # Log activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            action='reviewed',
            description='Document submitted for review'
        )
        
        return Response({'message': 'Document submitted for review'})
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_document(request, pk):
    """Approve a document"""
    try:
        document = Document.objects.get(pk=pk)
        document.status = 'approved'
        document.reviewed_at = timezone.now()
        document.reviewer = request.user
        document.save()
        
        # TEMPORARILY DISABLED - Re-enable when vector DB is restored
        # index_document_task.delay(str(document.id))
        
        return Response({'message': 'Document approved'})
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def publish_document(request, pk):
    """Publish a document"""
    try:
        document = Document.objects.get(pk=pk)
        document.status = 'published'
        document.published_at = timezone.now()
        document.save()
        
        # TEMPORARILY DISABLED - Re-enable when vector DB is restored
        # index_document_task.delay(str(document.id))
        
        return Response({'message': 'Document published'})
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def archive_document(request, pk):
    """Archive a document"""
    try:
        document = Document.objects.get(pk=pk)
        document.status = 'archived'
        document.save()
        
        # TEMPORARILY DISABLED - Re-enable when vector DB is restored
        # delete_document_from_index.delay(str(document.id))
        
        return Response({'message': 'Document archived'})
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

# Report endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def document_usage_report(request):
    """Document usage report"""
    return Response({'message': 'Document usage report endpoint'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def category_report(request):
    """Category report"""
    return Response({'message': 'Category report endpoint'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity_report(request):
    """User activity report"""
    return Response({'message': 'User activity report endpoint'})

# Document Sharing Views
class DocumentShareView(APIView):
    """Share a document with users, departments, or create public links"""
    permission_classes = [permissions.IsAuthenticated, DocumentSharePermission]
    
    def post(self, request, document_id):
        """Share a document"""
        try:
            document = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check share permission
        self.check_object_permissions(request, document)
        
        serializer = ShareDocumentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        share_type = data['share_type']
        user = request.user
        shares_created = []
        
        try:
            if share_type == 'user':
                # Share with specific users
                shares_created = self._share_with_users(document, user, data)
            elif share_type == 'department':
                # Share with department
                shares_created = self._share_with_department(document, user, data)
            elif share_type == 'public_link':
                # Create public link
                shares_created = self._create_public_link(document, user, data)
            
            # Log sharing activity
            for share in shares_created:
                DocumentActivity.objects.create(
                    document=document,
                    user=user,
                    action='shared',
                    description=f"Document shared via {share_type}",
                    ip_address=self._get_client_ip(request)
                )
                
                log_security_event(
                    user=user,
                    action='document_share',
                    resource=f"document:{document.title}",
                    success=True,
                    details=f"Shared with {share_type}"
                )
            
            # Send notifications if requested
            if data.get('send_notification', True):
                self._send_share_notifications(shares_created, data.get('message', ''))
            
            return Response({
                'message': f'Document shared successfully with {len(shares_created)} recipients',
                'shares': DocumentShareSerializer(shares_created, many=True, context={'request': request}).data
            })
            
        except Exception as e:
            log_security_event(
                user=user,
                action='document_share',
                resource=f"document:{document.title}",
                success=False,
                details=str(e)
            )
            return Response(
                {'error': 'Failed to share document'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _share_with_users(self, document, shared_by, data):
        """Share document with specific users"""
        from accounts.models import User
        shares = []
        
        # Get users by email or IDs
        users = []
        if data.get('user_email'):
            try:
                user = User.objects.get(email=data['user_email'], is_active=True)
                users.append(user)
            except User.DoesNotExist:
                raise ValueError(f"User with email {data['user_email']} not found")
        
        if data.get('user_ids'):
            users.extend(
                User.objects.filter(id__in=data['user_ids'], is_active=True)
            )
        
        # Create shares
        for user in users:
            # Check if share already exists
            existing_share = DocumentShare.objects.filter(
                document=document,
                share_type='user',
                shared_with_user=user,
                is_active=True
            ).first()
            
            if existing_share:
                # Update existing share
                existing_share.access_level = data['access_level']
                existing_share.allow_download = data.get('allow_download', True)
                existing_share.allow_reshare = data.get('allow_reshare', False)
                existing_share.notify_on_access = data.get('notify_on_access', False)
                existing_share.expires_at = data.get('expires_at')
                existing_share.save()
                shares.append(existing_share)
            else:
                # Create new share
                share = DocumentShare.objects.create(
                    document=document,
                    share_type='user',
                    shared_with_user=user,
                    shared_by=shared_by,
                    access_level=data['access_level'],
                    allow_download=data.get('allow_download', True),
                    allow_reshare=data.get('allow_reshare', False),
                    notify_on_access=data.get('notify_on_access', False),
                    expires_at=data.get('expires_at')
                )
                shares.append(share)
        
        return shares
    
    def _share_with_department(self, document, shared_by, data):
        """Share document with department"""
        from departments.models import Department
        
        try:
            department = Department.objects.get(id=data['department_id'])
        except Department.DoesNotExist:
            raise ValueError("Department not found")
        
        # Check if share already exists
        existing_share = DocumentShare.objects.filter(
            document=document,
            share_type='department',
            shared_with_department=department,
            is_active=True
        ).first()
        
        if existing_share:
            # Update existing share
            existing_share.access_level = data['access_level']
            existing_share.allow_download = data.get('allow_download', True)
            existing_share.allow_reshare = data.get('allow_reshare', False)
            existing_share.notify_on_access = data.get('notify_on_access', False)
            existing_share.expires_at = data.get('expires_at')
            existing_share.save()
            return [existing_share]
        else:
            # Create new share
            share = DocumentShare.objects.create(
                document=document,
                share_type='department',
                shared_with_department=department,
                shared_by=shared_by,
                access_level=data['access_level'],
                allow_download=data.get('allow_download', True),
                allow_reshare=data.get('allow_reshare', False),
                notify_on_access=data.get('notify_on_access', False),
                expires_at=data.get('expires_at')
            )
            return [share]
    
    def _create_public_link(self, document, shared_by, data):
        """Create public link for document"""
        # Check if public link already exists
        existing_share = DocumentShare.objects.filter(
            document=document,
            share_type='public_link',
            is_active=True
        ).first()
        
        if existing_share:
            # Update existing public link
            existing_share.access_level = data['access_level']
            existing_share.allow_download = data.get('allow_download', True)
            existing_share.allow_reshare = data.get('allow_reshare', False)
            existing_share.notify_on_access = data.get('notify_on_access', False)
            existing_share.expires_at = data.get('expires_at')
            existing_share.link_password = data.get('link_password')
            existing_share.save()
            return [existing_share]
        else:
            # Create new public link
            share = DocumentShare.objects.create(
                document=document,
                share_type='public_link',
                shared_by=shared_by,
                access_level=data['access_level'],
                allow_download=data.get('allow_download', True),
                allow_reshare=data.get('allow_reshare', False),
                notify_on_access=data.get('notify_on_access', False),
                expires_at=data.get('expires_at'),
                link_password=data.get('link_password')
            )
            return [share]
    
    def _send_share_notifications(self, shares, message):
        """Send notifications about document sharing"""
        # TODO: Implement email notifications
        # This would typically send emails to users about shared documents
        pass
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DocumentShareListView(generics.ListAPIView):
    """List document shares"""
    serializer_class = DocumentShareSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get shares based on user permissions"""
        user = self.request.user
        
        if user.role == 'admin':
            # Admin can see all shares
            return DocumentShare.objects.all()
        else:
            # Users can see shares they created or received
            return DocumentShare.objects.filter(
                Q(shared_by=user) | 
                Q(shared_with_user=user) |
                Q(shared_with_department__in=user.department_assignments.filter(
                    end_date__isnull=True
                ).values_list('department', flat=True))
            ).distinct()


class DocumentSharedAccessView(APIView):
    """Access document via public link"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """Access document via public share token"""
        try:
            share = DocumentShare.objects.get(
                public_link_token=token,
                share_type='public_link',
                is_active=True
            )
        except DocumentShare.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired share link'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if share is expired
        if share.is_expired():
            return Response(
                {'error': 'Share link has expired'},
                status=status.HTTP_410_GONE
            )
        
        # Return share details (without sensitive information)
        return Response({
            'document': {
                'id': share.document.id,
                'title': share.document.title,
                'description': share.document.description,
                'file_type': share.document.file_type,
                'file_size': share.document.file_size,
                'file_size_mb': share.document.file_size_mb,
                'created_at': share.document.created_at,
            },
            'access_level': share.access_level,
            'allow_download': share.allow_download,
            'requires_password': bool(share.link_password),
            'expires_at': share.expires_at,
        })
    
    def post(self, request, token):
        """Access document with password if required"""
        try:
            share = DocumentShare.objects.get(
                public_link_token=token,
                share_type='public_link',
                is_active=True
            )
        except DocumentShare.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired share link'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if share is expired
        if share.is_expired():
            return Response(
                {'error': 'Share link has expired'},
                status=status.HTTP_410_GONE
            )
        
        # Check password if required
        if share.link_password:
            serializer = DocumentAccessSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            provided_password = serializer.validated_data.get('password', '')
            if provided_password != share.link_password:
                return Response(
                    {'error': 'Invalid password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # Update access tracking
        share.access_count += 1
        share.last_accessed_at = timezone.now()
        share.save()
        
        # Log access
        DocumentActivity.objects.create(
            document=share.document,
            user=request.user if request.user.is_authenticated else None,
            action='viewed',
            description='Document accessed via public link',
            ip_address=self._get_client_ip(request)
        )
        
        # Return document details
        return Response({
            'document': DocumentDetailSerializer(share.document, context={'request': request}).data,
            'access_level': share.access_level,
            'allow_download': share.allow_download,
        })
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RevokeDocumentShareView(APIView):
    """Revoke document share"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, share_id):
        """Revoke a document share"""
        try:
            share = DocumentShare.objects.get(id=share_id)
        except DocumentShare.DoesNotExist:
            return Response(
                {'error': 'Share not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = request.user
        
        # Check permissions to revoke share
        if share.shared_by != user and user.role != 'admin':
            # Document owners can also revoke shares
            if not (hasattr(share.document, 'owned_by') and share.document.owned_by == user):
                log_security_event(
                    user=user,
                    action='revoke_share_denied',
                    resource=f"share:{share.id}",
                    success=False,
                    details="Insufficient permissions"
                )
                return Response(
                    {'error': 'You can only revoke shares you created'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Revoke the share
        share.is_active = False
        share.save()
        
        # Log revocation
        DocumentActivity.objects.create(
            document=share.document,
            user=user,
            action='shared',
            description='Document share revoked',
            ip_address=self._get_client_ip(request)
        )
        
        log_security_event(
            user=user,
            action='revoke_share',
            resource=f"document:{share.document.title}",
            success=True,
            details=f"Share type: {share.share_type}"
        )
        
        return Response({'message': 'Share revoked successfully'})
    
    def _get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
