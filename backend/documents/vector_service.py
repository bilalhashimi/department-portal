import os
import logging
import numpy as np
import uuid
from typing import List, Dict, Any, Optional
from django.conf import settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range
from sentence_transformers import SentenceTransformer
import openai
import magic
import PyPDF2
from docx import Document as DocxDocument
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

class VectorService:
    """Service for managing vector embeddings and semantic search"""
    
    def __init__(self):
        self.client = QdrantClient(url=settings.VECTOR_DB_URL)
        self.collection_name = settings.VECTOR_COLLECTION_NAME
        self.embedding_model = None
        self.use_local_embeddings = settings.USE_LOCAL_EMBEDDINGS
        
        # Initialize OpenAI if API key is provided
        if settings.OPENAI_API_KEY and not self.use_local_embeddings:
            openai.api_key = settings.OPENAI_API_KEY
        
        # Initialize local embedding model if needed
        if self.use_local_embeddings:
            self._load_local_model()
        
        # Initialize NLTK data
        self._init_nltk()
        
        # Create collection if it doesn't exist
        self._ensure_collection_exists()
    
    def _load_local_model(self):
        """Load local sentence transformer model"""
        try:
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded local embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load local embedding model: {e}")
            raise
    
    def _init_nltk(self):
        """Initialize NLTK data"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            logger.warning(f"Failed to download NLTK data: {e}")
    
    def _ensure_collection_exists(self):
        """Create the documents collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                vector_size = 1536 if not self.use_local_embeddings else 384  # OpenAI vs local model
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text content from various file types"""
        try:
            text = ""
            
            if file_type.lower() == 'pdf':
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            
            elif file_type.lower() in ['doc', 'docx']:
                doc = DocxDocument(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            elif file_type.lower() in ['txt', 'md']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
            
            elif file_type.lower() in ['html', 'htm']:
                with open(file_path, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file.read(), 'html.parser')
                    text = soup.get_text()
            
            else:
                # Try to read as plain text
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        text = file.read()
                except:
                    logger.warning(f"Could not extract text from file type: {file_type}")
                    return ""
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def chunk_text(self, text: str, chunk_size: int = None) -> List[str]:
        """Split text into chunks for embedding"""
        if not chunk_size:
            chunk_size = settings.CHUNK_SIZE
        
        # Split by sentences first
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI or local model"""
        try:
            if self.use_local_embeddings:
                if not self.embedding_model:
                    self._load_local_model()
                
                embedding = self.embedding_model.encode(text)
                return embedding.tolist()
            else:
                # Use OpenAI embeddings
                response = openai.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                return response.data[0].embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def index_document(self, document_id: str, title: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Index a document in the vector database"""
        try:
            # Split content into chunks if too long
            chunks = self.chunk_text(content)
            points = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Generate embedding
                embedding = self.generate_embedding(chunk)
                
                # Create point with metadata
                point_id = uuid.uuid4().hex
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "document_id": document_id,
                        "title": title,
                        "content": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        **metadata
                    }
                )
                points.append(point)
            
            # Upsert points to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Indexed document {document_id} with {len(points)} chunks")
            return True
        
        except Exception as e:
            logger.error(f"Error indexing document {document_id}: {e}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document from the vector database"""
        try:
            # Delete all chunks for this document
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match={"value": document_id}
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted document {document_id} from vector database")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def search_documents(
        self, 
        query: str, 
        limit: int = 10, 
        department_id: str = None,
        user_id: str = None,
        filter_params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for documents using semantic similarity"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build filter conditions
            filter_conditions = []
            
            if department_id:
                filter_conditions.append(
                    FieldCondition(
                        key="department_id",
                        match={"value": department_id}
                    )
                )
            
            if user_id:
                filter_conditions.append(
                    FieldCondition(
                        key="accessible_by",
                        match={"value": user_id}
                    )
                )
            
            if filter_params:
                for key, value in filter_params.items():
                    filter_conditions.append(
                        FieldCondition(
                            key=key,
                            match={"value": value}
                        )
                    )
            
            # Perform search
            search_filter = Filter(must=filter_conditions) if filter_conditions else None
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )
            
            # Process results
            processed_results = []
            seen_documents = set()
            
            for result in results:
                doc_id = result.payload.get("document_id")
                
                # Avoid duplicate documents (when multiple chunks match)
                if doc_id in seen_documents:
                    continue
                
                seen_documents.add(doc_id)
                
                processed_results.append({
                    "document_id": doc_id,
                    "title": result.payload.get("title"),
                    "content_snippet": result.payload.get("content", "")[:200] + "...",
                    "score": result.score,
                    "metadata": {k: v for k, v in result.payload.items() 
                               if k not in ["document_id", "title", "content"]}
                })
            
            logger.info(f"Found {len(processed_results)} documents for query: {query}")
            return processed_results
        
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "total_points": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance,
                "status": "healthy"
            }
        
        except Exception as e:
            logger.error(f"Error getting vector database stats: {e}")
            return {"status": "error", "error": str(e)}


# Singleton instance
vector_service = VectorService() 