import asyncio
import os
import sys
import time

import httpx
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    FaithfulnessMetric,
    ToxicityMetric,
)
from deepeval.test_case import LLMTestCase
from pydantic import BaseModel

sys.path.append(os.getcwd())
from src.core.config import settings
from src.main import app
from tests.eval_data import SYNTHETIC_DATASET, EvalCase

THRESHOLD = 0.5
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY.get_secret_value()


class EvalResult(BaseModel):
    name: str
    input: str
    actual_output: str
    relevancy: float
    faithfulness: float
    toxicity: float
    bias: float
    success: bool = True
    error: str = ""


async def get_api_response(client: httpx.AsyncClient, text: str) -> str:
    response = await client.post("/api/v1/extract", json={"text": text})
    if response.status_code == 200:
        data = response.json()
        return f"Summary: {data['summary']}\nEntities: {', '.join(data['entities'])}"
    raise Exception(f"API Error: {response.status_code}")


async def collect_responses(cases: list[EvalCase]) -> list[tuple[EvalCase, str]]:
    print(f"--- Step 1: Collecting API Responses ({len(cases)} cases) ---")
    results = []
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test", timeout=60.0
    ) as client:
        for case in cases:
            print(f"  Calling API for: {case.name}...")
            try:
                output = await get_api_response(client, case.input)
                results.append((case, output))
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
    return results


def run_sync_evaluation(api_outputs: list[tuple[EvalCase, str]]) -> list[EvalResult]:
    print("\n--- Step 2: Evaluating with LLM-as-a-Judge (Sync Mode) ---")
    eval_model = "gpt-4o-mini"
    metrics = {
        "relevancy": AnswerRelevancyMetric(
            threshold=THRESHOLD, model=eval_model, async_mode=False
        ),
        "faithfulness": FaithfulnessMetric(
            threshold=THRESHOLD, model=eval_model, async_mode=False
        ),
        "toxicity": ToxicityMetric(
            threshold=THRESHOLD, model=eval_model, async_mode=False
        ),
        "bias": BiasMetric(threshold=THRESHOLD, model=eval_model, async_mode=False),
    }
    results = []
    for case, actual_output in api_outputs:
        print(f"Evaluating: {case.name}...")
        try:
            test_case = LLMTestCase(
                input=case.input,
                actual_output=actual_output,
                retrieval_context=[case.input],
            )
            scores = {}
            for name, metric in metrics.items():
                print(f"    Measuring {name}...")
                metric.measure(test_case)
                scores[name] = metric.score or 0.0
                time.sleep(1)
            results.append(
                EvalResult(
                    name=case.name,
                    input=case.input,
                    actual_output=actual_output,
                    relevancy=scores["relevancy"],
                    faithfulness=scores["faithfulness"],
                    toxicity=1.0 - scores["toxicity"],
                    bias=1.0 - scores["bias"],
                )
            )
            time.sleep(2)
        except Exception as e:
            print(f"  ❌ Eval Error: {str(e)}")
            results.append(
                EvalResult(
                    name=case.name,
                    input=case.input,
                    actual_output=actual_output,
                    relevancy=0,
                    faithfulness=0,
                    toxicity=0,
                    bias=0,
                    success=False,
                    error=str(e),
                )
            )
    return results


def generate_report(results: list[EvalResult]):
    report_path = "reports/llm_judge_report.md"
    os.makedirs("reports", exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# ⚖️ LLM-as-a-Judge Evaluation Report\n\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary Table
        f.write("## 📊 Summary\n\n")
        f.write("| Metric | Average Score |\n")
        f.write("| :--- | :--- |\n")

        successful_results = [r for r in results if r.success]
        if successful_results:
            n = len(successful_results)
            avg_rel = sum(r.relevancy for r in successful_results) / n
            avg_faith = sum(r.faithfulness for r in successful_results) / n
            avg_tox = sum(r.toxicity for r in successful_results) / n
            avg_bias = sum(r.bias for r in successful_results) / n

            f.write(f"| Answer Relevancy | {avg_rel:.2f} |\n")
            f.write(f"| Faithfulness | {avg_faith:.2f} |\n")
            f.write(f"| Toxicity (Cleanliness) | {avg_tox:.2f} |\n")
            f.write(f"| Bias (Fairness) | {avg_bias:.2f} |\n\n")
        else:
            f.write("| No successful results to summarize |\n\n")

        # Detailed Results
        f.write("## 📝 Detailed Results\n\n")
        f.write("| Case | Rel. | Faith. | Clean | Fair | OK |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")

        for r in results:
            success_icon = "✅" if r.success else "❌"
            f.write(
                f"| {r.name} | {r.relevancy:.2f} | {r.faithfulness:.2f} | "
                f"{r.toxicity:.2f} | {r.bias:.2f} | {success_icon} |\n"
            )

        f.write("\n\n### 🔍 Edge Cases Analysis\n\n")
        for r in results:
            if not r.success or r.relevancy < THRESHOLD or r.faithfulness < THRESHOLD:
                f.write(f"#### {r.name}\n")
                f.write(f"- **Input**: {r.input[:200]}...\n")
                f.write(f"- **Output**: {r.actual_output}\n")
                if r.error:
                    f.write(f"- **Error**: {r.error}\n")
                f.write("\n")

    print(f"\n✅ Report generated at: {report_path}")


if __name__ == "__main__":
    # Test with first 3 examples initially as requested
    outputs = asyncio.run(collect_responses(SYNTHETIC_DATASET[:3]))
    final_results = run_sync_evaluation(outputs)
    generate_report(final_results)
