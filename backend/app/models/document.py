from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Text, DateTime, func, ARRAY, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # 384 dimensions for all-MiniLM-L6-v2, stored as standard array
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}')>"
