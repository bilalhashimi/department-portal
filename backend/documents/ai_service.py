import json
import logging
import requests
from typing import List, Dict, Any, Optional
from django.conf import settings
from .vector_service import vector_service
from .models import Document
from django.db import models

logger = logging.getLogger(__name__)

class AIDocumentAssistant:
    """AI-powered document assistant using Ollama and RAG"""
    
    def __init__(self):
        self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://ollama:11434')
        self.model_name = getattr(settings, 'OLLAMA_MODEL', 'tinyllama')
        self.max_context_docs = getattr(settings, 'MAX_CONTEXT_DOCS', 5)
        self.max_context_length = getattr(settings, 'MAX_CONTEXT_LENGTH', 4000)
    
    def ensure_model_loaded(self) -> bool:
        """Ensure the AI model is loaded and ready"""
        try:
            # Check if model is available
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name not in model_names:
                    logger.info(f"Downloading model {self.model_name}...")
                    # Pull the model
                    pull_response = requests.post(
                        f"{self.ollama_url}/api/pull",
                        json={"name": self.model_name},
                        timeout=300  # 5 minutes for model download
                    )
                    return pull_response.status_code == 200
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking/loading model: {e}")
            return False
    
    def search_relevant_documents(self, query: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for documents relevant to the user's question"""
        try:
            # Use vector search to find relevant documents (without user filtering first)
            vector_results = vector_service.search_documents(
                query=query,
                limit=self.max_context_docs * 2  # Get more results to filter by permissions
            )
            
            relevant_docs = []
            for result in vector_results:
                try:
                    # Get the full document
                    document = Document.objects.get(id=result['document_id'])
                    
                    # ⚠️ CRITICAL SECURITY CHECK: Verify user has permission to access this document
                    if user_id and not self._user_can_access_document(user_id, document):
                        logger.info(f"User {user_id} denied access to document {document.id} via AI assistant")
                        continue  # Skip this document - user doesn't have permission
                    
                    relevant_docs.append({
                        'title': result['title'],
                        'content_snippet': result['content_snippet'],
                        'score': result['score'],
                        'document_id': result['document_id'],
                        'category': document.category.name,
                        'file_type': document.file_type,
                        'created_at': document.created_at.strftime('%Y-%m-%d'),
                        'full_content': self._get_document_text(document)[:2000]  # Limit content
                    })
                    
                    # Stop once we have enough permitted documents
                    if len(relevant_docs) >= self.max_context_docs:
                        break
                        
                except (Document.DoesNotExist, ValueError) as e:
                    # Skip invalid document IDs or documents that don't exist
                    logger.warning(f"Skipping invalid document ID {result.get('document_id', 'unknown')}: {e}")
                    continue
            
            return relevant_docs
        
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _user_can_access_document(self, user_id: str, document: 'Document') -> bool:
        """Check if user has permission to access a document"""
        try:
            from accounts.models import User
            user = User.objects.get(id=user_id)
            
            # Check basic document visibility rules
            # 1. Document must be published (not draft)
            if document.status != 'published':
                return False
            
            # 2. Check if user is the document owner
            if str(document.created_by.id) == user_id:
                return True
            
            # 3. Check if user is admin/superuser (can access all documents)
            if user.is_staff or user.is_superuser:
                return True
            
            # 4. Check department-level access
            if hasattr(user, 'profile') and user.profile and user.profile.department:
                if document.category and document.category.department:
                    if user.profile.department == document.category.department.name:
                        return True
            
            # 5. Check explicit document permissions
            from .models import DocumentPermission
            permission = DocumentPermission.objects.filter(
                document=document,
                user=user,
                permission__in=['view', 'edit', 'delete']
            ).first()
            
            if permission:
                return True
            
            # 6. Check document shares
            from .models import DocumentShare
            from django.utils import timezone
            
            active_share = DocumentShare.objects.filter(
                document=document,
                shared_with_user=user,
                is_active=True
            ).filter(
                # Check expiry
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
            ).first()
            
            if active_share:
                return True
            
            # 7. Default: deny access
            return False
            
        except Exception as e:
            logger.error(f"Error checking document access for user {user_id}: {e}")
            return False  # Default to deny access on error
    
    def _get_document_text(self, document: Document) -> str:
        """Extract text content from a document"""
        try:
            if document.file:
                return vector_service.extract_text_from_file(
                    document.file.path, 
                    document.file_type
                )
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from document {document.id}: {e}")
            return ""
    
    def generate_response(self, question: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI response based on question and document context"""
        try:
            # Build context from relevant documents
            context = self._build_context(context_docs)
            
            # Create the prompt
            prompt = self._create_prompt(question, context)
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for factual responses
                        "top_p": 0.9,
                        "max_tokens": 1000
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "response": result.get("response", ""),
                    "sources": [doc['title'] for doc in context_docs],
                    "source_count": len(context_docs)
                }
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {
                    "status": "error",
                    "message": "AI service temporarily unavailable"
                }
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "status": "error",
                "message": f"Error generating response: {str(e)}"
            }
    
    def _build_context(self, docs: List[Dict[str, Any]]) -> str:
        """Build context string from relevant documents"""
        context_parts = []
        total_length = 0
        
        for doc in docs:
            doc_context = f"""
Document: {doc['title']}
Category: {doc['category']}
Type: {doc['file_type']}
Date: {doc['created_at']}
Content: {doc['full_content']}
---
"""
            if total_length + len(doc_context) > self.max_context_length:
                break
            
            context_parts.append(doc_context)
            total_length += len(doc_context)
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create the prompt for the AI model"""
        return f"""You are a helpful AI assistant that answers questions about documents. You have access to the following documents:

{context}

Based on the above documents, please answer the following question. Be specific and detailed, citing information from the documents when possible. If the answer is not in the documents, say so clearly.

Question: {question}

Answer:"""
    
    def chat(self, question: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Main chat interface - combines search and generation"""
        try:
            # Ensure model is loaded
            if not self.ensure_model_loaded():
                return {
                    "status": "error",
                    "message": "AI model is not available. Please try again in a few minutes."
                }
            
            # Check if this is a simple greeting or conversational query that doesn't need document search
            simple_queries = {
                'hello': "Hello! I'm your AI document assistant. I can help you find information from your uploaded documents. What would you like to know?",
                'hi': "Hi there! I'm here to help you search through your documents and answer questions about them. What can I help you find?",
                'hey': "Hey! I'm your AI document assistant. Ask me anything about your uploaded documents!",
                'good morning': "Good morning! I'm ready to help you find information in your documents. What would you like to know?",
                'good afternoon': "Good afternoon! I'm here to assist you with your document queries. How can I help?",
                'good evening': "Good evening! I'm your AI document assistant. What information can I help you find?",
                'how are you': "I'm doing well, thank you! I'm here to help you search and understand your documents. What would you like to know about them?",
                'thanks': "You're welcome! Is there anything else you'd like to know about your documents?",
                'thank you': "You're very welcome! Feel free to ask me any questions about your uploaded documents.",
                'help': "I'm your AI document assistant! I can help you find information from your uploaded documents. Try asking questions like 'What is Assignment 1 about?' or 'What are the course requirements?'",
                'what can you do': "I can search through your uploaded documents and answer questions about their content. I use AI to find relevant information and provide detailed answers with source citations. Try asking me about specific documents or topics!",
            }
            
            # Normalize the question for comparison
            normalized_question = question.lower().strip()
            
            # Check for exact matches or simple greetings
            for greeting, response in simple_queries.items():
                if normalized_question == greeting or (len(normalized_question.split()) <= 3 and greeting in normalized_question):
                    return {
                        "status": "success",
                        "response": response,
                        "sources": [],
                        "source_count": 0,
                        "document_details": []
                    }
            
            # If it's not a simple greeting, proceed with document search
            # Search for relevant documents
            relevant_docs = self.search_relevant_documents(question, user_id)
            
            if not relevant_docs:
                return {
                    "status": "success",
                    "response": "I couldn't find any relevant documents to answer your question. Please make sure documents are uploaded and indexed. You can also try rephrasing your question or asking about specific topics covered in your documents.",
                    "sources": [],
                    "source_count": 0
                }
            
            # Generate response
            result = self.generate_response(question, relevant_docs)
            
            # Add document details to response
            if result["status"] == "success":
                result["document_details"] = [
                    {
                        "title": doc["title"],
                        "category": doc["category"],
                        "score": doc["score"],
                        "document_id": doc["document_id"]
                    }
                    for doc in relevant_docs
                ]
            
            return result
        
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                "status": "error",
                "message": f"Chat service error: {str(e)}"
            }

# Singleton instance
ai_assistant = AIDocumentAssistant() 