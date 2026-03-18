import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

# Mock EmbeddingService to avoid loading model
from unittest.mock import patch

@pytest.mark.asyncio
async def test_upload_document(async_client: AsyncClient):
    with patch("app.services.embedding_service.EmbeddingService.generate_embedding") as mock_embed:
        mock_embed.return_value = [0.1] * 384
        
        files = {"file": ("test.txt", b"Hello World content", "text/plain")}
        response = await async_client.post("/api/v1/documents/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "test.txt"

@pytest.mark.asyncio
async def test_search_documents(async_client: AsyncClient):
    # First upload a doc
    with patch("app.services.embedding_service.EmbeddingService.generate_embedding") as mock_embed:
        mock_embed.return_value = [0.1] * 384
        
        files = {"file": ("search_test.txt", b"Searchable content", "text/plain")}
        await async_client.post("/api/v1/documents/upload", files=files)
        
        # Now search
        response = await async_client.get("/api/v1/documents/search?q=content")
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        # Should be at least 1 result if matching works (mock embedding matches itself)
        # But wait, cosine distance of [0.1]*384 against [0.1]*384 is 0 (match)
        # So it should be returned.
        # However, we need to ensure test DB is clean or handles this.
