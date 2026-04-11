import pytest

from src.services.guardrails import PIIMaskingService


@pytest.fixture
def pii_service():
    return PIIMaskingService()


def test_mask_email(pii_service):
    text = "Contact me at john.doe@example.com for more info."
    masked = pii_service.mask_text(text)
    assert "john.doe@example.com" not in masked
    assert "[EMAIL_MASKED]" in masked


def test_mask_phone(pii_service):
    text = "My phone number is +1-555-123-4567."
    masked = pii_service.mask_text(text)
    assert "+1-555-123-4567" not in masked
    assert "[PHONE_MASKED]" in masked


def test_mask_iban(pii_service):
    text = "My IBAN is DE12345678901234567890."
    masked = pii_service.mask_text(text)
    assert "DE12345678901234567890" not in masked
    assert "[IBAN_MASKED]" in masked


def test_no_pii(pii_service):
    text = "This is a normal sentence with no PII."
    masked = pii_service.mask_text(text)
    assert masked == text
