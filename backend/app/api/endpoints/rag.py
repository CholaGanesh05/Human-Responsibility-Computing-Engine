from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    session: AsyncSession = Depends(get_db)
):
    try:
        service = RAGService(session)
        result = await service.answer_query(request.query, user_id=request.user_id)
        return RAGQueryResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
