import logging
from celery import shared_task
from django.core.files.storage import default_storage
from .models import Document
from .vector_service import vector_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def index_document_task(self, document_id: str):
    """
    Celery task to index a document in the vector database
    """
    try:
        # Get the document
        document = Document.objects.get(id=document_id)
        
        # Get file path
        file_path = document.file.path
        
        # Extract text content
        content = vector_service.extract_text_from_file(file_path, document.file_type)
        
        if not content:
            logger.warning(f"No content extracted from document {document_id}")
            return {"status": "warning", "message": "No content extracted"}
        
        # Prepare metadata
        metadata = {
            "document_id": str(document.id),
            "category_id": str(document.category.id),
            "category_name": document.category.name,
            "status": document.status,
            "priority": document.priority,
            "file_type": document.file_type,
            "created_by": str(document.created_by.id),
            "owned_by": str(document.owned_by.id),
            "created_at": document.created_at.isoformat(),
        }
        
        # Add department information if available
        if document.category.department:
            metadata["department_id"] = str(document.category.department.id)
            metadata["department_name"] = document.category.department.name
        
        # Get accessible users (for permission filtering)
        accessible_users = []
        
        # Add document owner and creator
        accessible_users.extend([str(document.owned_by.id), str(document.created_by.id)])
        
        # Add users with explicit permissions
        for permission in document.permissions.filter(is_active=True):
            if permission.user:
                accessible_users.append(str(permission.user.id))
            elif permission.department:
                # Add all users in the department
                dept_users = permission.department.employees.filter(
                    end_date__isnull=True
                ).values_list('employee__id', flat=True)
                accessible_users.extend([str(uid) for uid in dept_users])
        
        metadata["accessible_by"] = list(set(accessible_users))
        
        # Index the document
        success = vector_service.index_document(
            document_id=str(document.id),
            title=document.title,
            content=content,
            metadata=metadata
        )
        
        if success:
            logger.info(f"Successfully indexed document {document_id}")
            return {"status": "success", "document_id": document_id}
        else:
            raise Exception("Failed to index document in vector database")
    
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return {"status": "error", "message": "Document not found"}
    
    except Exception as e:
        logger.error(f"Error indexing document {document_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying indexing for document {document_id}")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def delete_document_from_index(self, document_id: str):
    """
    Celery task to delete a document from the vector database
    """
    try:
        success = vector_service.delete_document(document_id)
        
        if success:
            logger.info(f"Successfully deleted document {document_id} from index")
            return {"status": "success", "document_id": document_id}
        else:
            raise Exception("Failed to delete document from vector database")
    
    except Exception as e:
        logger.error(f"Error deleting document {document_id} from index: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def reindex_all_documents(self):
    """
    Celery task to reindex all published documents
    """
    try:
        documents = Document.objects.filter(
            status__in=['published', 'approved'],
            is_latest_version=True
        )
        
        total_documents = documents.count()
        logger.info(f"Starting reindex of {total_documents} documents")
        
        success_count = 0
        error_count = 0
        
        for document in documents:
            try:
                result = index_document_task.apply_async(args=[str(document.id)])
                # Wait for task to complete (for reporting)
                task_result = result.get(timeout=300)  # 5 minutes timeout
                
                if task_result.get("status") == "success":
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error reindexing document {document.id}: {e}")
                error_count += 1
        
        logger.info(f"Reindex completed: {success_count} success, {error_count} errors")
        
        return {
            "status": "completed",
            "total_documents": total_documents,
            "success_count": success_count,
            "error_count": error_count
        }
    
    except Exception as e:
        logger.error(f"Error during bulk reindex: {e}")
        return {"status": "error", "message": str(e)}


@shared_task(bind=True)
def update_document_permissions(self, document_id: str):
    """
    Update the permissions for a document in the vector database
    """
    try:
        # This would update the accessible_by field in the vector database
        # For now, we'll re-index the document to update permissions
        return index_document_task.apply_async(args=[document_id]).get()
    
    except Exception as e:
        logger.error(f"Error updating permissions for document {document_id}: {e}")
        return {"status": "error", "message": str(e)} 