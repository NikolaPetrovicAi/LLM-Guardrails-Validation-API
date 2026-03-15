import json
import os
import sys
import time
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from pydantic import BaseModel

# Ensure src is in path
sys.path.append(os.getcwd())
from src.core.config import settings

# Set OpenAI key for DeepEval
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY.get_secret_value()

LOG_FILE = "logs/metrics_data.jsonl"
REPORT_FILE = "reports/advanced_metrics.md"
NUM_EXAMPLES = 5
THRESHOLD = 0.5
EVAL_MODEL = "gpt-4o-mini"

class AnalyticsResult(BaseModel):
    request_id: str
    model_name: str
    self_score: float
    external_score: float
    calibration_gap: float
    cost_usd: float
    roi: float

def run_analytics():
    print(f"--- 📊 Viral Content Advanced Analytics ---")
    
    if not os.path.exists(LOG_FILE):
        print(f"❌ Log file {LOG_FILE} not found.")
        return

    # Read last N lines from logs
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    last_entries = [json.loads(line) for line in lines[-NUM_EXAMPLES:]]
    print(f"Processing {len(last_entries)} most recent requests...")

    metric = AnswerRelevancyMetric(threshold=THRESHOLD, model=EVAL_MODEL, async_mode=False)
    results = []

    for entry in last_entries:
        request_id = entry.get("request_id", "N/A")
        print(f"Evaluating Request: {request_id}...")
        
        input_text = entry.get("input_text", "")
        output_text = entry.get("output_text", "")
        self_score = entry.get("self_audit_hook_strength", 0.0)
        cost_usd = entry.get("cost_usd", 0.0)
        
        if not input_text or not output_text:
            print(f"  ⚠️ Skipping {request_id}: missing input/output text.")
            continue

        try:
            test_case = LLMTestCase(
                input=input_text,
                actual_output=output_text,
                retrieval_context=[input_text]
            )
            
            metric.measure(test_case)
            external_score = metric.score if metric.score is not None else 0.0
            
            calibration_gap = abs(self_score - external_score)
            roi = external_score / cost_usd if cost_usd > 0 else 0.0
            
            results.append(AnalyticsResult(
                request_id=request_id,
                model_name=entry.get("model_name", "unknown"),
                self_score=self_score,
                external_score=external_score,
                calibration_gap=round(calibration_gap, 4),
                cost_usd=cost_usd,
                roi=round(roi, 2)
            ))
            print(
                f"  ✅ Self: {self_score:.2f} | External: {external_score:.2f} | "
                f"Gap: {calibration_gap:.4f} | ROI: {roi:.2f}"
            )
            
        except Exception as e:
            print(f"  ❌ Error evaluating {request_id}: {str(e)}")
            results.append(AnalyticsResult(
                request_id=request_id,
                model_name=entry.get("model_name", "unknown"),
                self_score=self_score,
                external_score=0.0,
                calibration_gap=self_score,
                cost_usd=cost_usd,
                roi=0.0
            ))

    generate_markdown_report(results)

def generate_markdown_report(results: list[AnalyticsResult]):
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# 🚀 Advanced Viral Metrics Report\n\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 📊 Calibration & ROI Analysis\n\n")
        f.write("| Request ID | Model | Self Score | External Score | Calibration Gap | Cost (USD) | ROI |\n")
        f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |\n")
        
        for r in results:
            f.write(f"| {r.request_id[:8]}... | {r.model_name} | {r.self_score:.2f} | {r.external_score:.2f} | {r.calibration_gap:.4f} | ${r.cost_usd:.6f} | {r.roi:.2f} |\n")
        
        f.write("\n\n## 💡 Executive Summary\n\n")
        
        if results:
            avg_gap = sum(r.calibration_gap for r in results) / len(results)
            avg_calibration = (1 - avg_gap) * 100
            
            # Find most cost-effective model
            # For this simple case, we might have only one model, but let's handle multiples
            model_roi = {}
            for r in results:
                if r.model_name not in model_roi:
                    model_roi[r.model_name] = []
                model_roi[r.model_name].append(r.roi)
            
            best_model = "N/A"
            best_avg_roi = -1
            for model, rois in model_roi.items():
                avg_roi = sum(rois) / len(rois)
                if avg_roi > best_avg_roi:
                    best_avg_roi = avg_roi
                    best_model = model
            
            f.write(f"Prosečna kalibracija sistema je **{avg_calibration:.1f}%**, a najisplativiji model je **{best_model}**.\n")
        else:
            f.write("Nema dovoljno podataka za analizu.\n")

    print(f"\n✅ Report generated at: {REPORT_FILE}")

if __name__ == "__main__":
    run_analytics()
