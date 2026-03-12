from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """
    Model representing the initial extraction request from the user.
    """

    text: str = Field(
        ...,
        description="The raw text to be analyzed by the LLM.",
        min_length=1,
    )


class StructuredResponse(BaseModel):
    """
    The structured output enforced on the LLM.
    """

    entities: list[str] = Field(
        default_factory=list,
        description="Key entities (people, places) mentioned in the text.",
    )
    summary: str = Field(
        ...,
        description="A concise summary of the main themes and context.",
    )
    sentiment_score: float = Field(
        ...,
        description="Sentiment score from 0.0 (negative) to 1.0 (positive).",
        ge=0.0,
        le=1.0,
    )
    sentiment_label: str = Field(
        ...,
        description="Sentiment label (e.g., 'Positive', 'Negative', 'Neutral').",
    )
