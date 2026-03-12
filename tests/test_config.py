from pydantic import SecretStr

from src.core.config import Settings, settings


def test_settings_initialization():
    """
    Test that settings are correctly initialized
    with default values or from environment.
    """
    assert settings.PROJECT_NAME == "Enterprise LLM Guardrails"
    assert settings.VERSION == "0.1.0"
    assert isinstance(settings.OPENAI_API_KEY, SecretStr)

def test_settings_api_v1_str():
    """
    Test that API_V1_STR is correctly formatted.
    """
    assert settings.API_V1_STR.startswith("/api/v1")

def test_custom_settings():
    """
    Test that Settings can be overridden (e.g., for testing purposes).
    """
    custom_settings = Settings(PROJECT_NAME="Test Project", DEBUG=True)
    assert custom_settings.PROJECT_NAME == "Test Project"
    assert custom_settings.DEBUG is True
