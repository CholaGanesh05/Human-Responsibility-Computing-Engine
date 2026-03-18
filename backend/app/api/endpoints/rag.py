from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse)
@limiter.limit("20/hour")
async def query_rag(
    request: Request,
    body: RAGQueryRequest,
    session: AsyncSession = Depends(get_db),
):
    """
    Query the RAG pipeline with a natural language question.
    Rate limited to 20 requests/hour (expensive LLM call).
    """
    try:
        service = RAGService(session)
        result = await service.answer_query(body.query, user_id=body.user_id)
        return RAGQueryResponse(
            answer=result["answer"],
            sources=result["sources"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
