from pydantic import BaseModel, Field
from typing import List


class ScriptRequest(BaseModel):
    """
    Request model for generating a viral video script.
    """
    topic: str = Field(..., description="The core idea or topic of the video.")
    target_audience: str = Field(..., description="Who is this video for (e.g., 'Junior Developers').")
    tone: str = Field(..., description="The style or vibe (e.g., 'Hype', 'Educational', 'Sarcastic').")
    platform: str = Field(..., description="The target platform (TikTok, Reels, or Shorts).")


class ScriptSegment(BaseModel):
    """
    A single segment of the video script.
    """
    text: str = Field(..., description="What is being said or the text overlay.")
    visual_cue: str = Field(..., description="Detailed description of what is happening on screen.")
    duration_seconds: float = Field(..., description="Estimated duration of this segment in seconds.")


class ViralAudit(BaseModel):
    """
    Automated quality and engagement audit of the generated script.
    """
    hook_strength: float = Field(..., description="Score from 0.0 to 1.0 based on how well the hook grabs attention.", ge=0.0, le=1.0)
    retention_reasoning: str = Field(..., description="Explanation of why this script will keep viewers watching.")
    suggested_edits: List[str] = Field(default_factory=list, description="Specific improvements to increase virality.")


class ViralScriptResponse(BaseModel):
    """
    The final structured response containing the script and its viral audit.
    """
    hook: str = Field(..., description="The opening 'grabber' to stop the scroll.")
    segments: List[ScriptSegment] = Field(..., description="The full chronological flow of the video.")
    audit: ViralAudit = Field(..., description="The automated quality check for virality.")
