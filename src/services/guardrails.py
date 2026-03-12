import re
from typing import Dict, Pattern

class PIIMaskingService:
    """
    Service for identifying and masking Personally Identifiable Information (PII) 
    using regular expressions.
    """

    def __init__(self) -> None:
        # Define regex patterns for common PII types
        # Reordered to check IBAN before PHONE to avoid partial matches
        # Added word boundaries \b where appropriate
        self.patterns: Dict[str, Pattern] = {
            "EMAIL": re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"),
            "IBAN": re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}\b"),
            "PHONE": re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4,6}"),
        }

    def mask_text(self, text: str) -> str:
        """
        Scans the input text and masks detected PII with generic placeholders.

        Args:
            text: The raw input string.

        Returns:
            str: The text with PII masked.
        """
        masked_text = text
        # Order of iteration matters for overlapping patterns
        for pii_type in ["EMAIL", "IBAN", "PHONE"]:
            pattern = self.patterns[pii_type]
            masked_text = pattern.sub(f"[{pii_type}_MASKED]", masked_text)
        return masked_text
