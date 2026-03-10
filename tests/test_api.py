import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app
from src.models.schemas import StructuredResponse

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
    Test the POST /api/v1/extract endpoint by mocking the LLM service.
    """
    # Create mock response data
    mock_data = {
        "entities": ["API Test", "Integration"],
        "summary": "This is a mock summary for API test.",
        "sentiment_score": 0.85,
        "sentiment_label": "Positive"
    }

    # Use patch to intercept the service method call inside the API
    with patch("src.api.v1.endpoints.llm_service.extract_structured_data", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = StructuredResponse(**mock_data)

        request_payload = {"text": "Testing the API endpoint integration."}
        response = client.post("/api/v1/extract", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["sentiment_label"] == "Positive"
        assert "API Test" in response_json["entities"]
        mock_extract.assert_called_once()

def test_extract_endpoint_validation_error():
    """
    Test the endpoint with invalid input (e.g., empty text).
    Pydantic should catch this before it reaches the service.
    """
    request_payload = {"text": ""}  # min_length is 1 in schema
    response = client.post("/api/v1/extract", json=request_payload)
    
    assert response.status_code == 422  # Unprocessable Entity (Validation Error)
    assert response.json()["detail"][0]["type"] == "string_too_short"
