import asyncio
import hashlib
import logging
import time
import uuid
from collections.abc import AsyncGenerator

from diskcache import Cache
from langfuse import Langfuse
from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import (
    LLMValidationError,
)
from src.models.schemas import (
    ExtractionRequest,
    PromptDefinition,
    ScriptRequest,
    StructuredResponse,
    ViralScriptResponse,
)
from src.services.guardrails import PIIMaskingService
from src.services.optimizer import PromptOptimizerService
from src.services.prompt_manager import PromptManager
from src.services.providers.base import BaseLLMProvider
from src.services.semantic_cache import SemanticCacheService
from src.services.usage import UsageTrackerService

logger = logging.getLogger(__name__)


class ViralContentService:
    """
    Service for generating viral video scripts and performing audits.
    Supports PII masking, hybrid caching, and usage tracking.
    Now includes Shadow Deployment and Automated Prompt Optimization (APO).
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        pii_service: PIIMaskingService,
        usage_tracker: UsageTrackerService,
        semantic_cache: SemanticCacheService,
        prompt_manager: PromptManager,
        optimizer: PromptOptimizerService | None = None,
        langfuse: Langfuse | None = None,
        cache_path: str = settings.CACHE_PATH,
        cache_expire: int = settings.CACHE_EXPIRE,
    ) -> None:
        """
        Initializes the service with hybrid caching capabilities.
        """
        self.provider = provider
        self.pii_service = pii_service
        self.usage_tracker = usage_tracker
        self.semantic_cache = semantic_cache
        self.prompt_manager = prompt_manager
        self.optimizer = optimizer
        self.langfuse = langfuse
        self.cache = Cache(cache_path)
        self.cache_expire = cache_expire

    def _generate_cache_key(self, text: str) -> str:
        """Generates a unique cache key for exact match caching."""
        return hashlib.sha256(text.encode()).hexdigest()

    async def _run_llm_generation(
        self,
        request: ScriptRequest,
        prompt_def: PromptDefinition,
        request_id: str,
        is_shadow: bool = False,
    ) -> ViralScriptResponse:
        """
        Helper to run the LLM generation and logging logic for a given prompt.
        """
        # Step 0: Render Prompt
        system_prompt = self.prompt_manager.render_prompt(
            prompt_def.system_prompt, platform=request.platform
        )
        user_prompt = self.prompt_manager.render_prompt(
            prompt_def.user_prompt_template, **request.model_dump()
        )

        # Step 1: PII Masking (only mask user input)
        masked_text = self.pii_service.mask_text(user_prompt)

        # Step 4: LLM Generation
        start_time = time.perf_counter()
        response, usage = await self.provider.validate(
            masked_text,
            system_prompt=system_prompt,
            model=prompt_def.config.model_name,
            temperature=prompt_def.config.temperature,
            max_tokens=prompt_def.config.max_tokens,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        # Step 5: Cost & Quality Tracking
        usage_data = self.usage_tracker.extract_usage_and_log(
            usage=usage,
            model=getattr(self.provider, "model", "unknown"),
            request_id=request_id,
            latency_ms=round(latency_ms, 2),
            self_score=response.audit.hook_strength,
            input_text=masked_text,
            output_text=response.model_dump_json(),
            prompt_id=prompt_def.id,
            prompt_version=prompt_def.version,
        )

        # Basic Langfuse Logging (v4 SDK Migration)
        if self.langfuse:
            try:
                type_label = "SHADOW" if is_shadow else "PROD"
                print(
                    f"📡 Sending {type_label} data to Langfuse "
                    f"(Trace ID: {request_id})..."
                )

                # In v4, we use start_as_current_observation (Context Manager)
                # Tags and other trace-level properties go into trace_context
                with self.langfuse.start_as_current_observation(
                    name="viral_script_generation",
                    as_type="generation",
                    trace_context={
                        "trace_id": request_id,
                        "tags": [request.platform, type_label],
                    },
                    input=request.model_dump(),
                    output=response.model_dump(),
                    model=prompt_def.config.model_name,
                    version=prompt_def.version,
                    metadata={
                        "topic": request.topic,
                        "prompt_id": prompt_def.id,
                        "latency_ms": latency_ms,
                        "is_shadow": is_shadow,
                        "request_id": request_id,
                        "platform": request.platform,
                    },
                    usage_details={
                        "input": usage_data.get("prompt_tokens", 0),
                        "output": usage_data.get("completion_tokens", 0),
                        "total": usage_data.get("total_tokens", 0),
                    },
                ) as gen:
                    # Add scores to the trace
                    gen.score_trace(
                        name="hook_strength",
                        value=response.audit.hook_strength,
                        comment=f"Version: {prompt_def.version} ({type_label})",
                    )
                    gen.score_trace(
                        name="retention_score",
                        value=response.audit.retention_score,
                        comment=f"Platform: {request.platform}",
                    )

                # Force flush (optional but recommended for short-lived processes)
                self.langfuse.flush()
                print(f"✅ {type_label} data FLUSHED to Langfuse.")
            except Exception as lf_err:
                logger.error(
                    f"❌ Langfuse logging failed: {str(lf_err)}", exc_info=True
                )
                print(f"❌ Langfuse error: {str(lf_err)}")

        return response

    async def generate_viral_script(
        self,
        request: ScriptRequest,
        prompt_id: str = "tiktok_script_gen",
        version: str | None = "1.0.0",
    ) -> ViralScriptResponse:
        """
        Generates a viral script with hybrid caching and shadow deployment.
        """
        # Standardized 32-char hex trace_id for W3C compatibility (Langfuse v4)
        request_id = uuid.uuid4().hex

        # Step 0: Get Production Prompt
        prompt_def = self.prompt_manager.get_prompt(prompt_id, version)

        # Render production user prompt for caching (must be consistent)
        user_prompt_prod = self.prompt_manager.render_prompt(
            prompt_def.user_prompt_template, **request.model_dump()
        )
        masked_text_prod = self.pii_service.mask_text(user_prompt_prod)

        # Step 2: Exact Match Cache (Production only)
        cache_key = self._generate_cache_key(masked_text_prod)
        cached_response = self.cache.get(cache_key)

        if cached_response:
            logger.info("Exact Cache HIT", extra={"cache_status": "EXACT_HIT"})
            return ViralScriptResponse.model_validate_json(cached_response)

        # Step 3: Semantic Cache (Production only)
        semantic_response = self.semantic_cache.get(masked_text_prod)
        if semantic_response:
            return ViralScriptResponse.model_validate_json(semantic_response)

        # Step 4: Shadow Deployment Logic
        shadow_prompt_def = None
        if prompt_def.shadow_version:
            try:
                shadow_prompt_def = self.prompt_manager.get_prompt(
                    prompt_id, prompt_def.shadow_version
                )
            except Exception as e:
                logger.warning(
                    f"Could not load shadow version {prompt_def.shadow_version}: {e}"
                )

        if shadow_prompt_def:
            # Create a separate ID for Shadow in Langfuse to avoid collisions
            shadow_trace_id = uuid.uuid4().hex
            logger.info(
                f"🚀 Shadow Deployment ACTIVE: Triggering "
                f"{shadow_prompt_def.version} in background "
                f"(Trace: {shadow_trace_id})"
            )

            # Run shadow version asynchronously with a small initial delay
            async def run_shadow_with_delay():
                await asyncio.sleep(0.5)
                await self._run_llm_generation(
                    request, shadow_prompt_def, shadow_trace_id, is_shadow=True
                )

            asyncio.create_task(run_shadow_with_delay())

        # Step 5: Main LLM Generation
        try:
            response = await self._run_llm_generation(
                request, prompt_def, request_id, is_shadow=False
            )

            # Step 6: Automated Prompt Optimization (APO)
            if self.optimizer:
                # Run APO asynchronously so we don't block the user
                asyncio.create_task(
                    self.optimizer.critique_and_suggest(
                        prompt_def, request.model_dump(), response
                    )
                )

            # Step 7: Store in both caches
            resp_json = response.model_dump_json()
            self.cache.set(cache_key, resp_json, expire=self.cache_expire)
            self.semantic_cache.set(
                masked_text_prod, resp_json, expire=self.cache_expire
            )

            return response

        except ValidationError as e:
            raise LLMValidationError(
                message="LLM output failed structural validation.", details=e.errors()
            ) from e
        except Exception as e:
            raise e

    async def extract_legacy_data(
        self, request: ExtractionRequest
    ) -> StructuredResponse:
        """
        Legacy extraction for compatibility with judge tests.
        """
        masked_text = self.pii_service.mask_text(request.text)

        try:
            request_id = str(uuid.uuid4())
            start_time = time.perf_counter()
            response, usage = await self.provider.validate_structured(
                masked_text, StructuredResponse
            )
            latency_ms = (time.perf_counter() - start_time) * 1000

            self.usage_tracker.extract_usage_and_log(
                usage=usage,
                model=getattr(self.provider, "model", "unknown"),
                request_id=request_id,
                latency_ms=round(latency_ms, 2),
                self_score=0.0,  # Legacy doesn't have hook_strength
            )

            return response

        except ValidationError as e:
            raise LLMValidationError(
                message="Legacy extraction failed structural validation.",
                details=e.errors(),
            ) from e
        except Exception as e:
            raise e

    async def stream_viral_script(
        self,
        request: ScriptRequest,
        prompt_id: str = "tiktok_script_gen",
        version: str | None = None,
    ) -> AsyncGenerator[ViralScriptResponse, None]:
        """
        Streams partial script results. Bypasses cache for real-time feedback.
        """
        prompt_def = self.prompt_manager.get_prompt(prompt_id, version)
        system_prompt = self.prompt_manager.render_prompt(
            prompt_def.system_prompt, platform=request.platform
        )
        user_prompt = self.prompt_manager.render_prompt(
            prompt_def.user_prompt_template, **request.model_dump()
        )

        masked_text = self.pii_service.mask_text(user_prompt)

        async for partial in self.provider.stream(
            masked_text,
            system_prompt=system_prompt,
            model=prompt_def.config.model_name,
            temperature=prompt_def.config.temperature,
            max_tokens=prompt_def.config.max_tokens,
        ):
            yield partial

    async def check_health(self) -> bool:
        """
        Check health of LLM provider and cache.
        """
        llm_health = await self.provider.check_health()

        cache_health = False
        try:
            self.cache.set("__health_check__", "ok", expire=10)
            if self.cache.get("__health_check__") == "ok":
                cache_health = True
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")

        return llm_health and cache_health
