import asyncio
import time

import httpx
from pydantic import BaseModel


class EvalCase(BaseModel):
    name: str
    text: str

EVAL_DATASET = [
    EvalCase(name="Short Text", text="My name is John Doe and I'm feeling great today! I love programming in Python."),
    EvalCase(name="Business Email", text="Hello Team, sales increased by 20% in Q3. However, Sarah from London (sarah.l@gmail.com) is concerned about the new IBAN GB2982828282."),
    EvalCase(name="Negative Feedback", text="The product is terrible. I want a refund immediately. Contact me at 555-0199."),
    EvalCase(name="Long Context", text="Artificial Intelligence is transforming industries from healthcare to finance. Researchers at Stanford published a paper on Transformers in 2017. The sentiment is generally optimistic, but ethics remains a concern. Global investment in AI reached $200B in 2024."),
]

BASE_URL = "http://localhost:8000/api/v1"

async def run_eval():
    print("🚀 Starting AI Guardrails Benchmarking...\n")
    print(f"{'Case Name':<20} | {'Status':<10} | {'Latency (ms)':<12} | {'Sentiment':<10}")
    print("-" * 65)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for case in EVAL_DATASET:
            start_time = time.perf_counter()
            try:
                response = await client.post(
                    f"{BASE_URL}/extract",
                    json={"text": case.text}
                )
                end_time = time.perf_counter()
                
                if response.status_code == 200:
                    data = response.json()
                    latency = (end_time - start_time) * 1000
                    sentiment = data.get("sentiment_score", "N/A")
                    print(f"{case.name:<20} | {'SUCCESS':<10} | {latency:<12.2f} | {sentiment:<10}")
                else:
                    print(f"{case.name:<20} | {'ERROR':<10} | {'-':<12} | {'-'}")
            except Exception as e:
                print(f"{case.name:<20} | {'FAILED':<10} | {'-':<12} | {str(e)[:15]}...")

    print("\n✅ Evaluation complete. Check logs for PII masking and cost details.")

if __name__ == "__main__":
    # Ensure the server is running before executing this
    try:
        asyncio.run(run_eval())
    except KeyboardInterrupt:
        pass
