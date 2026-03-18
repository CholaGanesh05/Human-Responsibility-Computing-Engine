import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from app.models.document import Document
from app.services.embedding_service import EmbeddingService

UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_upload(self, file: UploadFile) -> Document:
        # 1. Save file locally
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Extract content (Basic text reading for now)
        content = ""
        try:
            if file.filename and file.filename.lower().endswith(".pdf"):
                import PyPDF2
                with open(file_path, "rb") as f:
                    pdf = PyPDF2.PdfReader(f)
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            content += str(extracted) + "\n"
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
        except Exception:
            # Fallback for non-text files or encoding issues
            content = ""
            
        if not content:
            content = "Binary file or empty content"

        # 3. Generate Embedding
        # Only embed if there is content. 
        # Truncate content for embedding if too long (simple handling for now)
        embedding = None
        if content and content != "Binary file or empty content":
            # Taking first 500 characters for now to avoid token limits if any
            # In production, we should chunk the document.
            embedding_text = str(content)[:1000] 
            embedding = EmbeddingService.generate_embedding(embedding_text)

        # 4. Save to DB
        document = Document(
            id=file_id,
            title=file.filename or "Untitled",
            file_path=str(file_path),
            content=content,
            embedding=embedding
        )
        
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def search_documents(self, query: str, limit: int = 5) -> list[Document]:
        import numpy as np
        
        # 1. Get query embedding
        query_vector = EmbeddingService.generate_embedding(query)
        query_vec_np = np.array(query_vector)
        
        # 2. Fetch all documents with embeddings
        # Optimization: In a real app without pgvector, you'd want to cache these 
        # or use a local faiss index. For now, fetching all is acceptable for prototype.
        stmt = select(Document).where(Document.embedding.is_not(None))
        result = await self.session.execute(stmt)
        documents = result.scalars().all()
        
        # 3. Calculate similarities
        scored_docs: list[tuple[Document, float]] = []
        for doc in documents:
            if not doc.embedding:
                continue
            doc_vec_np = np.array(doc.embedding)
            
            # Cosine Similarity: (A . B) / (||A|| * ||B||)
            dot_product = np.dot(query_vec_np, doc_vec_np)
            norm_q = np.linalg.norm(query_vec_np)
            norm_d = np.linalg.norm(doc_vec_np)
            
            if norm_q == 0 or norm_d == 0:
                score = 0
            else:
                score = dot_product / (norm_q * norm_d)
                
            scored_docs.append((doc, score))
            
        # 4. Sort and return top K
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored_docs[:limit]]
