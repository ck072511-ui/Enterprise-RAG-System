from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: Optional[int] = Field(3, ge=1, le=10)
    document_id: Optional[str] = None
    use_cache: Optional[bool] = True

class QueryResponse(BaseModel):
    query_id: str
    answer: str
    sources: List[Dict[str, Any]]
    chunks_found: int
    processing_time: float
    timestamp: datetime
    cache_hit: bool = False

class DocumentResponse(BaseModel):
    id: str
    filename: str
    total_chunks: int
    chunk_summaries: List[str]
    status: DocumentStatus
    upload_time: datetime
    file_size: int