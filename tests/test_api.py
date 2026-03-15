from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from src.api.deps import get_llm_service
from src.main import app
from src.models.schemas import ViralScriptResponse
from src.services.llm_service import ViralContentService

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

def test_generate_endpoint_success():
    """
    Test the POST /api/v1/generate endpoint by overriding the dependency.
    """
    # Create mock response data
    mock_data = {
        "hook": "Stop scrolling if you want to master Python!",
        "segments": [
            {"text": "Trick 1: List comprehensions", "visual_cue": "Code on screen", "duration_seconds": 5.0}
        ],
        "audit": {
            "hook_strength": 0.9,
            "retention_reasoning": "Strong hook and fast pacing.",
            "suggested_edits": ["Add background music"]
        }
    }

    # Mock service instance
    mock_service = MagicMock(spec=ViralContentService)
    mock_service.generate_viral_script = AsyncMock(
        return_value=ViralScriptResponse(**mock_data)
    )

    # Override the dependency
    app.dependency_overrides[get_llm_service] = lambda: mock_service

    try:
        request_payload = {
            "topic": "Python Tricks",
            "target_audience": "Devs",
            "tone": "Hype",
            "platform": "TikTok"
        }
        response = client.post("/api/v1/generate", json=request_payload)

        assert response.status_code == 200
        response_json = response.json()
        assert response_json["hook"] == "Stop scrolling if you want to master Python!"
        assert response_json["audit"]["hook_strength"] == 0.9
        mock_service.generate_viral_script.assert_called_once()
    finally:
        # Clear overrides for other tests
        app.dependency_overrides.clear()

def test_generate_endpoint_validation_error():
    """
    Test the endpoint with invalid input (missing required fields).
    """
    request_payload = {"topic": "Only Topic"} 
    response = client.post("/api/v1/generate", json=request_payload)
    
    # Standard Pydantic validation error returns 422
    assert response.status_code == 422
