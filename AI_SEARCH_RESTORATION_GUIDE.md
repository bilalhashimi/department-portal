# AI Search Functionality Restoration Guide

## 🎯 Current Status

**✅ WORKING:**
- Department Portal backend and frontend are running successfully
- Basic document management (CRUD operations)
- Text-based search (temporary fallback)
- User authentication and authorization
- All core API endpoints

**❌ TEMPORARILY DISABLED:**
- AI-powered semantic search
- Vector database indexing
- Celery background tasks
- Document auto-indexing

---

## 🔧 Steps to Restore AI Search Functionality

### 1. Fix Dependency Compatibility Issue

The main blocker is a version conflict between `sentence-transformers` and `huggingface_hub`:

```bash
# Navigate to backend directory
cd backend
source venv/bin/activate

# Try updating dependencies
pip install --upgrade huggingface_hub sentence-transformers

# Alternative: Pin compatible versions
pip install sentence-transformers==2.2.2 huggingface_hub==0.16.4
```

### 2. Start Vector Database Service

```bash
# From project root
docker-compose up -d qdrant
```

### 3. Re-enable Imports

**File: `backend/documents/views.py`**
Uncomment these lines:
```python
from .vector_service import vector_service
from .tasks import index_document_task, delete_document_from_index
```

**File: `backend/portal_backend/__init__.py`**
Uncomment these lines:
```python
from .celery import app as celery_app
__all__ = ('celery_app',)
```

### 4. Restore Vector Service References

In `backend/documents/views.py`, find and uncomment all lines marked with:
```python
# TEMPORARILY DISABLED - Re-enable when vector DB is restored
```

This includes:
- Document create/update/delete indexing
- Semantic search in `document_search()`
- Vector database stats in `document_stats()`
- Bulk action indexing
- Workflow indexing (approve, publish, archive)

### 5. Initialize Vector Database

```bash
cd backend
source venv/bin/activate
python manage.py init_vector_db
```

### 6. Start Celery Worker (Optional for Background Tasks)

```bash
# In a separate terminal
cd backend
source venv/bin/activate
celery -A portal_backend worker --loglevel=info
```

### 7. Test AI Search

```bash
# Test semantic search endpoint
curl -X GET "http://localhost:8000/api/v1/documents/search/?q=your search query" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🚀 Current Access Points

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health/
- **Qdrant UI** (when enabled): http://localhost:6334

---

## 📝 Files Modified for Temporary Disable

1. `backend/documents/views.py` - All Celery task calls commented out
2. `backend/portal_backend/__init__.py` - Celery import commented out
3. Document search replaced with basic text search

---

## 🔍 Search Functionality Details

**Current (Basic Text Search):**
- Searches document titles and descriptions
- Uses Django Q objects with `icontains`
- Returns mock similarity scores
- No semantic understanding

**Future (AI Semantic Search):**
- Vector similarity search using Qdrant
- Sentence transformer embeddings
- Semantic understanding of queries
- Relevance scoring based on vector distance
- Content chunking and indexing

---

## ⚡ Quick Status Check

Run these commands to verify system status:

```bash
# Check if services are running
lsof -i :8000  # Django backend
lsof -i :5173  # React frontend
lsof -i :6333  # Qdrant (when enabled)

# Test backend health
curl http://localhost:8000/health/

# Check frontend
curl -I http://localhost:5173
```

---

*Created: May 29, 2025*  
*Last Updated: May 29, 2025*  
*Status: AI Search Temporarily Disabled, Core System Operational* 