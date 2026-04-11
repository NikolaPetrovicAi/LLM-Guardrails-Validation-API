from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    """
    Legacy model representing the initial extraction request.
    Keep for compatibility with existing tests.
    """

    text: str = Field(
        ...,
        description="The raw text to be analyzed by the LLM.",
        min_length=1,
    )


class StructuredResponse(BaseModel):
    """
    Legacy model representing structured output.
    Keep for compatibility with existing tests.
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
        description="Sentiment score from 0.0 to 1.0.",
        ge=0.0,
        le=1.0,
    )
    sentiment_label: str = Field(
        ...,
        description="Sentiment label (e.g., 'Positive', 'Negative').",
    )


class ScriptRequest(BaseModel):
    """
    Request model for generating a viral video script.
    """

    topic: str = Field(..., description="The core idea or topic of the video.")
    target_audience: str = Field(
        ..., description="Who is this video for (e.g., 'Junior Developers')."
    )
    tone: str = Field(
        ..., description="The style or vibe (e.g., 'Hype', 'Educational')."
    )
    platform: str = Field(
        ..., description="The target platform (TikTok, Reels, or Shorts)."
    )


class ScriptSegment(BaseModel):
    """
    A single segment of the video script.
    """

    text: str = Field(..., description="What is being said or the text overlay.")
    visual_cue: str = Field(
        ..., description="Detailed description of what is happening on screen."
    )
    duration_seconds: float = Field(
        ..., description="Estimated duration of this segment in seconds."
    )


class ViralAudit(BaseModel):
    """
    Automated quality and engagement audit of the generated script.
    """

    critique_negative: str = Field(
        ..., description="Be brutal. What is WRONG with this script? Why will it FAIL?"
    )
    critique_positive: str = Field(
        ..., description="What are the strong points of the script?"
    )
    hook_strength: float = Field(
        ...,
        description="Score from 0.0 to 1.0. BE CRITICAL. 0.9+ is only for viral perfection.",
        ge=0.0,
        le=1.0,
    )
    retention_score: float = Field(
        ...,
        description="Score from 0.0 to 1.0 representing the likelihood of viewers watching until the end.",
        ge=0.0,
        le=1.0,
    )
    retention_reasoning: str = Field(
        ..., description="Explanation of why this script will keep viewers."
    )
    suggested_edits: list[str] = Field(
        default_factory=list, description="Specific improvements for virality."
    )


class ViralScriptResponse(BaseModel):
    """
    The final structured response containing the script and its viral audit.
    """

    hook: str = Field(..., description="The opening 'grabber' to stop the scroll.")
    segments: list[ScriptSegment] = Field(
        ..., description="The full chronological flow of the video."
    )
    audit: ViralAudit = Field(
        ..., description="The automated quality check for virality."
    )


class EnhancedUsageReport(BaseModel):
    """
    Advanced telemetry report linking performance, cost, and quality.
    Used for ROI and Calibration Score calculations.
    """

    request_id: str = Field(..., description="Unique identifier for the request.")
    model_name: str = Field(..., description="Name of the LLM model used.")
    total_tokens: int = Field(..., description="Total tokens consumed.")
    cost_usd: float = Field(..., description="Estimated cost in USD.")
    latency_ms: float = Field(..., description="Request latency in milliseconds.")
    self_audit_hook_strength: float = Field(
        ..., description="The hook strength score assigned by the model itself."
    )


class PromptConfig(BaseModel):
    """
    Model parameters for the LLM.
    """

    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, gt=0)
    model_name: str = Field(default="gpt-4o")


class PromptMetadata(BaseModel):
    """
    Metadata for prompt lifecycle management.
    """

    performance_target: float = Field(
        default=0.8, description="Target hook_strength for this prompt."
    )
    last_optimized_at: str | None = Field(
        None, description="ISO timestamp of the last APO run."
    )
    is_active: bool = Field(default=True, description="Whether this version is active.")


class PromptDefinition(BaseModel):
    """
    Schema for externalized prompt definitions (Prompt Ops).
    """

    id: str = Field(..., description="Unique identifier for the prompt.")
    version: str = Field(..., description="Semantic version of the prompt.")
    system_prompt: str = Field(
        ..., description="The system prompt template with placeholders."
    )
    user_prompt_template: str = Field(
        ..., description="The user prompt template with placeholders."
    )
    config: PromptConfig = Field(
        default_factory=PromptConfig, description="LLM configuration parameters."
    )
    metadata: PromptMetadata = Field(
        default_factory=PromptMetadata, description="Prompt lifecycle metadata."
    )
    shadow_version: str | None = Field(
        None, description="Version to run in shadow mode for this prompt ID."
    )


class PromptSuggestion(BaseModel):
    """
    Structured output for Automated Prompt Optimization (APO).
    Contains improved system and user templates.
    """

    improved_system_prompt: str = Field(
        ..., description="The optimized system prompt template."
    )
    improved_user_template: str = Field(
        ..., description="The optimized user prompt template."
    )
    reasoning: str = Field(
        ..., description="Explanation of why these changes were made."
    )
