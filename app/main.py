from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from datetime import datetime
import uvicorn
import logging
import os
import sys
import re
import hashlib
import PyPDF2
import pdfplumber
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings
from app.models import QueryRequest, QueryResponse

# ============================================
# LOGGING
# ============================================
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/rag_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================
# APP INIT
# ============================================
app = FastAPI(
    title="Enterprise RAG System",
    version="3.0.0",
    description="Enterprise-Grade RAG System for MNC Deployments",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
os.makedirs("uploads", exist_ok=True)

# ============================================
# DOCUMENT STORE
# ============================================
document_store = {}

# ============================================
# TEXT EXTRACTION
# ============================================
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {str(e)}")
    
    if len(text.strip()) < 100:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed: {str(e)}")
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:()-]', '', text)
    return text.strip()

# ============================================
# CHUNKING
# ============================================
def create_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    if not text:
        return []
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            overlap_words = current_chunk.split()[-10:] if current_chunk else []
            current_chunk = " ".join(overlap_words) + " " + sentence + " "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def generate_summary(chunk: str, max_len: int = 200) -> str:
    if len(chunk) <= max_len:
        return chunk
    sentences = chunk.split('.')
    if len(sentences) >= 3:
        summary = '. '.join(sentences[:2] + [sentences[-1]])
    else:
        summary = chunk[:max_len] + "..."
    return summary

# ============================================
# RAG ENGINE FUNCTIONS
# ============================================
class SimpleRAGEngine:
    def __init__(self):
        self.document_store = {}
    
    def add_document(self, doc_data: dict):
        doc_id = doc_data.get("document_id")
        if doc_id:
            self.document_store[doc_id] = doc_data
            logger.info(f"✅ Added document: {doc_data.get('filename')} ({doc_data.get('total_chunks')} chunks)")
    
    def get_all_documents(self):
        return list(self.document_store.values())
    
    def get_document(self, doc_id: str):
        return self.document_store.get(doc_id)
    
    def delete_document(self, doc_id: str):
        if doc_id in self.document_store:
            del self.document_store[doc_id]
            return True
        return False
    
    def get_total_chunks(self):
        return sum(doc.get("total_chunks", 0) for doc in self.document_store.values())
    
    def process_query(self, query: str, top_k: int = 3, use_cache: bool = True):
        query_words = query.lower().split()
        all_chunks = []
        all_summaries = []
        all_sources = []
        seen = set()
        
        for doc_id, doc_data in self.document_store.items():
            chunks = doc_data.get("chunks", [])
            summaries = doc_data.get("summaries", [])
            filename = doc_data.get("filename", "Unknown")
            
            for i, chunk in enumerate(chunks):
                chunk_lower = chunk.lower()
                match_count = sum(1 for word in query_words if word in chunk_lower)
                if match_count > 0:
                    key = chunk[:100]
                    if key not in seen:
                        seen.add(key)
                        all_chunks.append(chunk)
                        all_summaries.append(summaries[i] if i < len(summaries) else generate_summary(chunk))
                        all_sources.append({
                            "filename": filename,
                            "chunk_index": i,
                            "document_id": doc_id
                        })
        
        # Sort by match count
        all_sources.sort(key=lambda x: x.get("match_count", 0), reverse=True)
        
        # Limit results
        all_chunks = all_chunks[:top_k]
        all_summaries = all_summaries[:top_k]
        all_sources = all_sources[:top_k]
        
        if all_chunks:
            answer = f"📄 **Answer for: '{query}'**\n\n"
            answer += f"🔍 Found {len(all_chunks)} relevant chunks\n\n"
            answer += "📝 **Details:**\n\n"
            
            for i, (chunk, summary) in enumerate(zip(all_chunks, all_summaries)):
                answer += f"**Chunk {i+1}:** {summary}\n\n"
            
            answer += f"\n📚 **Sources:**\n"
            for source in all_sources:
                answer += f"• {source['filename']} (Chunk {source['chunk_index']+1})\n"
        else:
            answer = f"📄 **No information found for: '{query}'**\n\n"
            answer += "💡 **Suggestions:**\n"
            answer += "• Try different keywords\n"
            answer += "• Upload more documents\n"
            answer += "• Ask a more specific question"
        
        return {
            "query_id": f"q_{int(datetime.utcnow().timestamp())}",
            "answer": answer,
            "sources": all_sources,
            "chunks_found": len(all_chunks),
            "cache_hit": False
        }
    
    def get_metrics(self):
        return {
            "total_documents": len(self.document_store),
            "total_chunks": self.get_total_chunks()
        }

rag_engine = SimpleRAGEngine()

# ============================================
# API ROUTES
# ============================================

@app.get("/")
async def root():
    return {
        "app_name": "Enterprise RAG System",
        "version": "3.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "docs": "/api/docs",
            "upload": "/api/upload",
            "query": "/api/query",
            "documents": "/api/documents",
            "health": "/api/health"
        }
    }

@app.post("/api/upload")
async def upload_documents(
    files: List[UploadFile] = File(...)
):
    """Upload and process documents"""
    try:
        if len(files) > 5:
            raise HTTPException(400, "Maximum 5 files per request")
        
        results = []
        
        for file in files:
            try:
                file_path = f"uploads/{file.filename}"
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                text = extract_text_from_pdf(file_path)
                
                if not text or len(text.strip()) < 50:
                    results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": "Not enough text extracted"
                    })
                    continue
                
                # Create chunks
                chunks = create_chunks(text, chunk_size=500, overlap=100)
                summaries = [generate_summary(chunk) for chunk in chunks]
                
                doc_id = hashlib.md5(f"{file.filename}_{os.path.getsize(file_path)}".encode()).hexdigest()
                
                # Store in document store
                doc_data = {
                    "document_id": doc_id,
                    "id": doc_id,
                    "filename": file.filename,
                    "chunks": chunks,
                    "summaries": summaries,
                    "total_chunks": len(chunks),
                    "status": "completed",
                    "upload_time": datetime.utcnow().isoformat(),
                    "file_size": os.path.getsize(file_path)
                }
                
                rag_engine.add_document(doc_data)
                
                results.append({
                    "filename": file.filename,
                    "status": "completed",
                    "total_chunks": len(chunks),
                    "document_id": doc_id
                })
                
                logger.info(f"✅ {file.filename}: {len(chunks)} chunks stored")
                
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "message": f"Processed {len(files)} files",
            "results": results,
            "total_documents": len(rag_engine.document_store)
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/api/query")
async def query(request: dict):
    """Query the RAG system"""
    try:
        query_text = request.get("query", "").strip()
        top_k = request.get("top_k", 3)
        use_cache = request.get("use_cache", True)
        
        if not query_text:
            raise HTTPException(400, "Query cannot be empty")
        
        result = rag_engine.process_query(
            query=query_text,
            top_k=top_k,
            use_cache=use_cache
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(500, str(e))

@app.get("/api/documents")
async def get_documents():
    """Get all processed documents"""
    docs = rag_engine.get_all_documents()
    return {
        "documents": docs,
        "total": len(docs)
    }

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get specific document details"""
    doc = rag_engine.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    success = rag_engine.delete_document(doc_id)
    if not success:
        raise HTTPException(404, "Document not found")
    return {"status": "deleted", "document_id": doc_id}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "documents": len(rag_engine.document_store),
        "total_chunks": rag_engine.get_total_chunks(),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0"
    }

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    return rag_engine.get_metrics()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )