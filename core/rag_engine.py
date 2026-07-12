import hashlib
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)

class RAGEngine:
    def __init__(self):
        self.document_store = {}
        self.query_cache = {}
        self.metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "avg_response_time": 0
        }
    
    async def add_document(self, doc_data: Dict[str, Any]) -> None:
        """Add a processed document to the store"""
        doc_id = doc_data.get("document_id")
        if doc_id:
            self.document_store[doc_id] = doc_data
            logger.info(f"Added document: {doc_data.get('filename')} ({doc_data.get('total_chunks')} chunks)")
    
    async def process_query(self, query: str, top_k: int = 3, use_cache: bool = True) -> Dict[str, Any]:
        """Process a query and return results"""
        start_time = time.time()
        
        # Check cache
        cache_key = hashlib.md5(query.encode()).hexdigest()
        if use_cache and cache_key in self.query_cache:
            self.metrics["cache_hits"] += 1
            result = self.query_cache[cache_key]
            result["cache_hit"] = True
            return result
        
        # Search for relevant chunks
        all_chunks = []
        all_summaries = []
        all_sources = []
        seen = set()
        
        query_words = query.lower().split()
        
        for doc_id, doc_data in self.document_store.items():
            chunks = doc_data.get("chunks", [])
            summaries = doc_data.get("summaries", [])
            filename = doc_data.get("filename", "Unknown")
            
            for i, chunk in enumerate(chunks):
                chunk_lower = chunk.lower()
                # Calculate relevance score
                match_count = sum(1 for word in query_words if word in chunk_lower)
                if match_count > 0:
                    key = chunk[:100]
                    if key not in seen:
                        seen.add(key)
                        all_chunks.append({
                            "text": chunk,
                            "score": match_count / len(query_words) if query_words else 0,
                            "index": i
                        })
                        all_summaries.append(summaries[i] if i < len(summaries) else chunk[:200])
                        all_sources.append({
                            "filename": filename,
                            "chunk_index": i,
                            "document_id": doc_id
                        })
        
        # Sort by relevance
        all_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        # Limit results
        top_chunks = all_chunks[:top_k]
        top_summaries = all_summaries[:top_k]
        top_sources = all_sources[:top_k]
        
        # Generate answer
        if top_chunks:
            answer = f"📄 **Answer for: '{query}'**\n\n"
            answer += f"🔍 Found {len(top_chunks)} relevant chunks\n\n"
            answer += "📝 **Details:**\n\n"
            
            for i, (chunk, summary) in enumerate(zip(top_chunks, top_summaries)):
                answer += f"**Chunk {i+1}** (Relevance: {chunk['score']*100:.0f}%)\n"
                answer += f"{summary}\n\n"
            
            answer += f"\n📚 **Sources:**\n"
            for source in top_sources:
                answer += f"• {source['filename']} (Chunk {source['chunk_index']+1})\n"
        else:
            answer = f"📄 **No information found for: '{query}'**\n\n"
            answer += "💡 **Suggestions:**\n"
            answer += "• Try different keywords\n"
            answer += "• Upload more documents\n"
            answer += "• Ask a more specific question"
        
        # Prepare result
        result = {
            "query_id": f"q_{int(time.time())}",
            "answer": answer,
            "sources": top_sources,
            "chunks_found": len(top_chunks),
            "cache_hit": False
        }
        
        # Update metrics
        self.metrics["total_queries"] += 1
        self.metrics["avg_response_time"] = (
            (self.metrics["avg_response_time"] * (self.metrics["total_queries"] - 1) + 
             (time.time() - start_time)) / self.metrics["total_queries"]
        )
        
        # Cache result
        if use_cache:
            self.query_cache[cache_key] = result
        
        return result
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        return self.document_store.get(doc_id)
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents"""
        return list(self.document_store.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self.document_store:
            del self.document_store[doc_id]
            return True
        return False
    
    def get_total_chunks(self) -> int:
        """Get total number of chunks"""
        return sum(doc.get("total_chunks", 0) for doc in self.document_store.values())
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        return {
            **self.metrics,
            "total_documents": len(self.document_store),
            "total_chunks": self.get_total_chunks(),
            "cache_size": len(self.query_cache)
        }