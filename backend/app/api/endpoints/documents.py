"""
HRCE — Documents API Endpoints (Auth-protected + Rate Limited)
File uploads are heavier operations — limited to 30/min.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.services.document_service import DocumentService

router = APIRouter()


@router.post("/upload")
@limiter.limit("30/minute")
async def upload_document(
    request: Request,
    file: UploadFile,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document. Triggers background embedding via Celery. Rate limited to 30/min."""
    service = DocumentService(session)
    try:
        doc = await service.process_upload(file)

        # Expand embedding in background
        try:
            from app.workers.agent_tasks import process_document_task
            process_document_task.delay(str(doc.id))
        except Exception:
            pass  # Never fail upload if Celery is down

        return {"id": doc.id, "title": doc.title, "message": "Document uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
@limiter.limit("60/minute")
async def search_documents(
    request: Request,
    q: str = Query(..., min_length=3),
    limit: int = 5,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search documents by semantic similarity. Rate limited to 60/min."""
    service = DocumentService(session)
    try:
        results = await service.search_documents(q, limit)
        return [
            {"id": doc.id, "title": doc.title, "score": "N/A"}
            for doc in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
