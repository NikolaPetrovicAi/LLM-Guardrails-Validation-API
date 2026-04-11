import pytest
from pydantic import ValidationError

from src.models.schemas import ExtractionRequest, StructuredResponse


def test_extraction_request_valid():
    """
    Test ExtractionRequest with valid data.
    """
    req = ExtractionRequest(text="This is valid text.")
    assert req.text == "This is valid text."


def test_extraction_request_too_short():
    """
    Test ExtractionRequest with empty text (should fail).
    """
    with pytest.raises(ValidationError):
        ExtractionRequest(text="")


def test_structured_response_valid():
    """
    Test StructuredResponse with valid data.
    """
    res = StructuredResponse(
        entities=["test"],
        summary="A summary",
        sentiment_score=0.5,
        sentiment_label="Neutral",
    )
    assert res.sentiment_score == 0.5
    assert res.sentiment_label == "Neutral"


def test_structured_response_invalid_sentiment_score():
    """
    Test StructuredResponse with invalid sentiment score range.
    """
    with pytest.raises(ValidationError):
        StructuredResponse(
            entities=["test"],
            summary="A summary",
            sentiment_score=1.5,  # Must be between 0 and 1
            sentiment_label="Positive",
        )
