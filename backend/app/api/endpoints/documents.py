from fastapi import APIRouter, Depends, UploadFile, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.document_service import DocumentService
from app.models.document import Document

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile,
    session: AsyncSession = Depends(get_db)
):
    service = DocumentService(session)
    try:
        doc = await service.process_upload(file)

        # ─── Stage 10: expand embedding in background ─────────────────────────
        try:
            from app.workers.agent_tasks import process_document_task
            process_document_task.delay(str(doc.id))
        except Exception:
            pass  # Never fail upload if Celery is down

        return {"id": doc.id, "title": doc.title, "message": "Document uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_documents(
    q: str = Query(..., min_length=3),
    limit: int = 5,
    session: AsyncSession = Depends(get_db)
):
    service = DocumentService(session)
    try:
        results = await service.search_documents(q, limit)
        return [
            {"id": doc.id, "title": doc.title, "score": "N/A"} 
            # Note: score is hard to get back easily with ORM select unless explicitly selected
            for doc in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
