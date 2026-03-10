from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """
    Model representing the initial extraction request from the user.
    """

    text: str = Field(
        ...,
        description="The raw text input that the LLM will analyze and extract structured data from.",
        min_length=1,
    )


class StructuredResponse(BaseModel):
    """
    The structured output enforced on the LLM, containing entities, summary, and sentiment.
    """

    entities: list[str] = Field(
        default_factory=list,
        description="A list of key entities (people, places, organizations) mentioned in the text.",
    )
    summary: str = Field(
        ...,
        description="A concise summary of the provided text, capturing the main themes and context.",
    )
    sentiment_score: float = Field(
        ...,
        description="A sentiment score from 0.0 (extremely negative) to 1.0 (extremely positive).",
        ge=0.0,
        le=1.0,
    )
    sentiment_label: str = Field(
        ...,
        description="A label indicating the overall sentiment (e.g., 'Positive', 'Negative', 'Neutral').",
    )
