import asyncio
import logging

from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    FaithfulnessMetric,
    GEval,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from langfuse import Langfuse

from src.services.guardrails import PIIMaskingService

logger = logging.getLogger(__name__)

# Default model for judging (cost-efficient)
EVAL_MODEL = "gpt-4o-mini"
THRESHOLD = 0.5


class DeepEvalService:
    """
    Service for automated external evaluation using DeepEval and Langfuse.
    Integrates S.C.R.I.P.T. rubric via G-Eval.
    """

    def __init__(
        self,
        langfuse: Langfuse,
        pii_service: PIIMaskingService,
        model: str = EVAL_MODEL,
        threshold: float = THRESHOLD,
    ) -> None:
        self.langfuse = langfuse
        self.pii_service = pii_service
        self.model = model
        self.threshold = threshold

        # Initialize core metrics (sync_mode=False for background usage)
        self.relevancy_metric = AnswerRelevancyMetric(
            threshold=threshold, model=model, async_mode=False
        )
        self.faithfulness_metric = FaithfulnessMetric(
            threshold=threshold, model=model, async_mode=False
        )
        self.toxicity_metric = ToxicityMetric(
            threshold=threshold, model=model, async_mode=False
        )
        self.bias_metric = BiasMetric(
            threshold=threshold, model=model, async_mode=False
        )

        # Custom S.C.R.I.P.T. Metric using G-Eval
        self.script_metric = GEval(
            name="Viral S.C.R.I.P.T. Compliance",
            criteria=(
                "Determine if the script follows the S.C.R.I.P.T. method (Segment, "
                "Context, Retention, Intent, Persona, Temporal). It must have zero "
                "generic starts, clear audio-visual synergy, and a strong hook."
            ),
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            threshold=threshold,
            model=model,
        )

        # Hook Strength (Viral Script Integrity) Metric
        self.hook_strength_metric = GEval(
            name="Viral Script Integrity",
            criteria=(
                "1. Hook Strength: Is the first sentence impossible to scroll past? "
                "(Must be < 5 words)\n"
                "2. Pacing: Does every sentence move the story forward? (No fluff)\n"
                "3. Structural Integrity: Does it follow the 3-act viral structure "
                "(Hook, Value, CTA)?\n"
                "4. Tone Consistency: Is it energetic and punchy throughout?\n"
                "5. Call to Action: Is there a clear, high-friction CTA at the end?"
            ),
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            model=model,
            async_mode=False,
        )

    async def evaluate_and_log(
        self,
        trace_id: str,
        input_text: str,
        actual_output: str,
        retrieval_context: list[str] | None = None,
    ) -> None:
        """
        Runs DeepEval metrics and logs them to Langfuse.
        This should be called as a BackgroundTask.
        """
        try:
            # Step 1: PII Masking (Safety first for external judges)
            safe_input = self.pii_service.mask_text(input_text)
            safe_output = self.pii_service.mask_text(actual_output)

            # Step 2: Create Test Case
            test_case = LLMTestCase(
                input=safe_input,
                actual_output=safe_output,
                retrieval_context=retrieval_context or [safe_input],
            )

            # Step 3: Run metrics (using asyncio.to_thread for blocking DeepEval calls)
            logger.info(f"🚀 Starting DeepEval for trace {trace_id}...")
            
            # Helper to run metric and log to Langfuse
            def run_and_log(metric, name):
                try:
                    metric.measure(test_case)
                    score = metric.score
                    reason = getattr(metric, "reason", "No reason provided")
                    
                    if score is not None:
                        self.langfuse.create_score(
                            trace_id=trace_id,
                            name=f"deepeval_{name}",
                            value=float(score),
                            comment=reason
                        )
                    else:
                        logger.warning(
                            f"⚠️ DeepEval metric {name} produced None score "
                            f"for trace {trace_id}"
                        )
                    return score
                except Exception as e:
                    logger.error(
                        f"❌ Failed to run or log DeepEval metric {name}: {str(e)}"
                    )
                    return None

            # Run metrics in parallel where possible (or just sequentially in thread)
            # Since DeepEval metrics are synchronous in this config, we use to_thread
            await asyncio.to_thread(
                run_and_log, self.relevancy_metric, "relevancy"
            )
            await asyncio.to_thread(
                run_and_log, self.faithfulness_metric, "faithfulness"
            )
            await asyncio.to_thread(
                run_and_log, self.toxicity_metric, "toxic"
            )
            await asyncio.to_thread(
                run_and_log, self.bias_metric, "bias"
            )
            await asyncio.to_thread(
                run_and_log, self.script_metric, "script_compliance"
            )
            await asyncio.to_thread(
                run_and_log, self.hook_strength_metric, "hook_strength"
            )

            self.langfuse.flush()
            logger.info(f"✅ DeepEval metrics logged for trace {trace_id}")

        except Exception as e:
            logger.error(f"❌ DeepEval evaluation failed: {str(e)}", exc_info=True)
