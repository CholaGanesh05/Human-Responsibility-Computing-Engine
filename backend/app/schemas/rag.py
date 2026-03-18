from pydantic import BaseModel, Field
from uuid import UUID

class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="The natural language question to ask.")
    user_id: UUID | None = Field(None, description="Optional user ID to filter context.")

class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[str] = []
