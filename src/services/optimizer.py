import logging

from src.models.schemas import (
    PromptDefinition,
    PromptSuggestion,
    ViralScriptResponse,
)
from src.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class PromptOptimizerService:
    """
    Automated Prompt Optimization (APO) using a 'Critique & Suggest' loop.
    Analyzes low-performing scripts and suggests prompt improvements.
    """

    def __init__(self, critic_provider: BaseLLMProvider):
        self.critic_provider = critic_provider

    async def critique_and_suggest(
        self,
        prompt_def: PromptDefinition,
        script_request_data: dict,
        output: ViralScriptResponse,
    ) -> PromptSuggestion | None:
        """
        Calls a Critic model to suggest prompt improvements based on Viral Audit.
        """
        # Threshold check: only optimize if hook_strength is below target
        # or a hard threshold (e.g., 0.7)
        threshold = prompt_def.metadata.performance_target or 0.7
        if output.audit.hook_strength >= threshold:
            logger.info(
                f"Script performance ({output.audit.hook_strength}) "
                f"meets target ({threshold}). No APO needed."
            )
            return None

        logger.info(
            f"Triggering APO: Score {output.audit.hook_strength} < {threshold}"
        )

        critic_system_prompt = """
        You are an Expert Prompt Engineer and Viral Content Consultant.
        Your task is to analyze a failed prompt and its output,
        then suggest a better prompt.
        Focus on fixing the specific weaknesses identified in the Audit.
        """

        critic_user_prompt = f"""
        ORIGINAL PROMPT ID: {prompt_def.id}
        ORIGINAL VERSION: {prompt_def.version}
        
        SYSTEM PROMPT:
        {prompt_def.system_prompt}
        
        USER TEMPLATE:
        {prompt_def.user_prompt_template}
        
        INPUT DATA:
        {script_request_data}
        
        GENERATED OUTPUT:
        {output.model_dump_json(indent=2)}
        
        AUDIT FEEDBACK:
        Hook Strength: {output.audit.hook_strength}
        Reasoning: {output.audit.retention_reasoning}
        Suggested Edits: {output.audit.suggested_edits}
        
        Based on this, suggest a NEW version of the prompt (System + User Template) 
        that would produce a better hook and higher retention.
        """

        try:
            # We use StructuredResponse for the suggestion
            response, _ = await self.critic_provider.validate_structured(
                critic_user_prompt, PromptSuggestion, system_prompt=critic_system_prompt
            )

            logger.info(f"APO Suggestion generated for {prompt_def.id}")
            return response

        except Exception as e:
            logger.error(f"APO Critique failed: {e}")
            return None
