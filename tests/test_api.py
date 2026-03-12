from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from src.api.deps import get_llm_service
from src.main import app
from src.models.schemas import StructuredResponse
from src.services.llm_service import LLMValidatorService

client = TestClient(app)

def test_health_check_endpoint():
    """
    Test the /health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "project" in data

def test_extract_endpoint_success():
    """
    Test the POST /api/v1/extract endpoint by overriding the dependency.
    """
    # Create mock response data
    mock_data = {
        "entities": ["API Test", "Integration"],
        "summary": "This is a mock summary for API test.",
        "sentiment_score": 0.85,
        "sentiment_label": "Positive"
    }

    # Mock service instance
    mock_service = MagicMock(spec=LLMValidatorService)
    mock_service.extract_structured_data = AsyncMock(
        return_value=StructuredResponse(**mock_data)
    )

    # Override the dependency
    app.dependency_overrides[get_llm_service] = lambda: mock_service

    try:
        request_payload = {"text": "Testing the API endpoint integration."}
        response = client.post("/api/v1/extract", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["sentiment_label"] == "Positive"
        assert "API Test" in response_json["entities"]
        mock_service.extract_structured_data.assert_called_once()
    finally:
        # Clear overrides for other tests
        app.dependency_overrides.clear()

def test_extract_endpoint_validation_error():
    """
    Test the endpoint with invalid input (e.g., empty text).
    """
    request_payload = {"text": ""}  # min_length is 1 in schema
    response = client.post("/api/v1/extract", json=request_payload)
    
    # Standard Pydantic validation error returns 422
    assert response.status_code == 422
