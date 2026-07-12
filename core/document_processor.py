import os
import re
import hashlib
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import PyPDF2
import pdfplumber
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.chunk_size = 500
        self.chunk_overlap = 100
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.vectorizer = TfidfVectorizer(max_features=384)
        self.upload_dir = "uploads"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def process_multiple(self, files: List) -> List[Dict[str, Any]]:
        """Process multiple files in parallel"""
        tasks = [self.process_file(file) for file in files]
        results = await asyncio.gather(*tasks)
        return results
    
    async def process_file(self, file) -> Dict[str, Any]:
        """Process a single file"""
        try:
            # Save file
            file_path = os.path.join(self.upload_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Extract text
            text = await self._extract_text(file_path)
            
            if not text or len(text.strip()) < 50:
                return {
                    "filename": file.filename,
                    "status": "failed",
                    "error": "Not enough text extracted"
                }
            
            # Create chunks
            chunks = await self._create_chunks(text)
            
            # Generate summaries
            summaries = [self._generate_summary(chunk) for chunk in chunks]
            
            # Generate embeddings
            embeddings = await self._generate_embeddings(chunks)
            
            # Document ID
            doc_id = hashlib.md5(f"{file.filename}_{os.path.getsize(file_path)}".encode()).hexdigest()
            
            return {
                "document_id": doc_id,
                "filename": file.filename,
                "chunks": chunks,
                "summaries": summaries,
                "embeddings": embeddings,
                "total_chunks": len(chunks),
                "status": "completed",
                "file_size": os.path.getsize(file_path),
                "char_count": len(text)
            }
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}")
            return {
                "filename": file.filename,
                "status": "failed",
                "error": str(e)
            }
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF using multiple strategies"""
        text = ""
        
        # Strategy 1: PyPDF2
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.debug(f"PyPDF2 failed: {str(e)}")
        
        # Strategy 2: pdfplumber
        if len(text.strip()) < 100:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                logger.debug(f"pdfplumber failed: {str(e)}")
        
        # Clean text
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:()-]', '', text)
        return text.strip()
    
    async def _create_chunks(self, text: str) -> List[str]:
        """Create intelligent chunks"""
        if not text:
            return []
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                overlap_words = current_chunk.split()[-10:] if current_chunk else []
                current_chunk = " ".join(overlap_words) + " " + sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_summary(self, chunk: str, max_len: int = 200) -> str:
        """Generate a summary for a chunk"""
        if len(chunk) <= max_len:
            return chunk
        sentences = chunk.split('.')
        if len(sentences) >= 3:
            return '. '.join(sentences[:2] + [sentences[-1]])
        return chunk[:max_len] + "..."
    
    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Generate vector embeddings"""
        if not chunks:
            return []
        vectors = self.vectorizer.fit_transform(chunks)
        return vectors.toarray().tolist()