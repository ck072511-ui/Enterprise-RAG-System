import pickle
import json
import numpy as np
import faiss
import redis
from typing import List, Dict, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = {}
        self.id_counter = 0
        
        # Redis for caching
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
        except:
            self.redis_client = None
    
    async def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors to the store"""
        ids = []
        vectors_array = np.array(vectors).astype('float32')
        self.index.add(vectors_array)
        
        for i, meta in enumerate(metadata):
            vector_id = f"vec_{self.id_counter}"
            self.metadata[vector_id] = meta
            self.id_counter += 1
            ids.append(vector_id)
        
        return ids
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        query_array = np.array([query_vector]).astype('float32')
        distances, indices = self.index.search(query_array, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                vector_id = f"vec_{idx}"
                results.append({
                    "id": vector_id,
                    "distance": float(dist),
                    "metadata": self.metadata.get(vector_id, {})
                })
        
        return results
    
    async def delete_vectors(self, ids: List[str]):
        """Delete vectors from the store"""
        # FAISS doesn't support direct deletion, we rebuild index
        for vector_id in ids:
            if vector_id in self.metadata:
                del self.metadata[vector_id]
    
    async def get_vector_count(self) -> int:
        """Get total vector count"""
        return self.index.ntotal
    
    def save_index(self, path: str):
        """Save FAISS index to disk"""
        faiss.write_index(self.index, f"{path}/index.faiss")
        with open(f"{path}/metadata.pkl", 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load_index(self, path: str):
        """Load FAISS index from disk"""
        self.index = faiss.read_index(f"{path}/index.faiss")
        with open(f"{path}/metadata.pkl", 'rb') as f:
            self.metadata = pickle.load(f)