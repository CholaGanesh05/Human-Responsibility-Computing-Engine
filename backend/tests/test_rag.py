import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.rag_service import RAGService
from app.models.document import Document
from app.models.event import Event
from uuid import uuid4
from datetime import datetime

@pytest.mark.asyncio
async def test_rag_pipeline_flow():
    # Mock dependencies
    mock_session = AsyncMock()
    
    # Mock DocumentService
    with patch("app.services.rag_service.DocumentService") as MockDocService:
        mock_doc_service = MockDocService.return_value
        mock_doc_service.search_documents = AsyncMock(return_value=[
            Document(id=uuid4(), title="Doc 1", content="Content from Doc 1", filename="doc1.txt"),
            Document(id=uuid4(), title="Doc 2", content="Content from Doc 2", filename="doc2.txt")
        ])
        
        # Mock EventService
        with patch("app.services.rag_service.EventService") as MockEventService:
            mock_event_service = MockEventService.return_value
            mock_event_service.get_user_events = AsyncMock(return_value=[
                Event(id=uuid4(), title="Meeting", start_time=datetime.now(), owner_id=uuid4())
            ])
            
            # Mock ChatGroq to avoid init issues
            with patch("app.services.rag_service.ChatGroq") as MockChatGroq:
                
                # Mock LangChain components to handle the pipe operator |
                with patch("app.services.rag_service.ChatPromptTemplate") as MockPrompt, \
                     patch("app.services.rag_service.StrOutputParser") as MockParser:
                    
                    # Setup mock chain result
                    mock_chain = AsyncMock()
                    mock_chain.ainvoke.return_value = "Mocked Answer from Groq"
                    
                    # 1. Mock Prompt | LLM -> Intermediate
                    mock_prompt_instance = MockPrompt.from_messages.return_value
                    mock_intermediate = MagicMock()
                    mock_prompt_instance.__or__ = MagicMock(return_value=mock_intermediate)
                    
                    # 2. Mock Intermediate | Parser -> Chain
                    # The parser is the right operand, so it calls parser.__ror__(intermediate)
                    # OR intermediate.__or__(parser). We start with parser.__ror__.
                    mock_parser_instance = MockParser.return_value
                    mock_parser_instance.__ror__ = MagicMock(return_value=mock_chain)
                    
                    # Just in case intermediate.__or__ is called instead
                    mock_intermediate.__or__ = MagicMock(return_value=mock_chain)

                    # Initialize service
                    service = RAGService(mock_session)
                    
                    # Run Query
                    query = "Test Query"
                    user_id = uuid4()
                    result = await service.answer_query(query, user_id)
                    
                    # Assertions
                    assert result["answer"] == "Mocked Answer from Groq"
                    assert len(result["sources"]) == 2
                    assert "doc1.txt" in result["sources"]

                    # Verify DocumentService was called
                    mock_doc_service.search_documents.assert_awaited_once_with(query, limit=5)
                    
                    # Verify EventService was called
                    mock_event_service.get_user_events.assert_awaited_once_with(user_id, limit=5)
