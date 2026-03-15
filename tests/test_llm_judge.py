import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    FaithfulnessMetric,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase
from fastapi.testclient import TestClient

from src.main import app
from tests.eval_data import SYNTHETIC_DATASET

# Configure threshold
THRESHOLD = 0.5
EVAL_MODEL = "gpt-4o-mini"

client = TestClient(app)


@pytest.mark.parametrize("case", SYNTHETIC_DATASET[:2])
def test_llm_quality_judge(case):
    """
    Integration test using LLM-as-a-Judge (DeepEval).
    This calls our real API and then uses GPT-4 to judge the output.
    """
    # 1. Call our API
    response = client.post("/api/v1/extract", json={"text": case.input})
    assert response.status_code == 200
    data = response.json()

    # 2. Format actual output for the judge
    actual_output = (
        f"Summary: {data['summary']}\n" f"Entities: {', '.join(data['entities'])}"
    )

    # 3. Create DeepEval Test Case
    test_case = LLMTestCase(
        input=case.input, actual_output=actual_output, retrieval_context=[case.input]
    )

    # 4. Define Metrics (using sync_mode=False to avoid async conflicts)
    relevancy_metric = AnswerRelevancyMetric(
        threshold=THRESHOLD, model=EVAL_MODEL, async_mode=False
    )
    faithfulness_metric = FaithfulnessMetric(
        threshold=THRESHOLD, model=EVAL_MODEL, async_mode=False
    )
    toxicity_metric = ToxicityMetric(
        threshold=THRESHOLD, model=EVAL_MODEL, async_mode=False
    )
    bias_metric = BiasMetric(threshold=THRESHOLD, model=EVAL_MODEL, async_mode=False)

    # 5. Assert test with multiple metrics
    assert_test(
        test_case,
        [relevancy_metric, faithfulness_metric, toxicity_metric, bias_metric],
    )
