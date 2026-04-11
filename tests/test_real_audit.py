import asyncio
import os
import random
import sys

from dotenv import load_dotenv

from src.api.deps import get_llm_service
from src.models.schemas import ScriptRequest

# Ensure src is in path
sys.path.append(os.getcwd())

load_dotenv()

TOPICS = [
    "How to quit your job and travel the world on 5 dollars a day",
    "Why AI engineers will be replaced by prompts in 2027",
    "The secret way to get unlimited free coffee at Starbucks",
    "How to build a billion dollar startup from your bedroom",
    "Why you should never use a database again",
]


async def test_audit_realism():
    # Use the official dependency provider to get a fully configured service
    service = await get_llm_service()

    topic = random.choice(TOPICS)  # noqa: S311

    request = ScriptRequest(
        topic=topic,
        target_audience="Tech-savvy Gen Z",
        tone="Punchy and controversial",
        platform="TikTok",
    )

    print(f"\n🚀 Generating script for: {request.topic}...")
    # Use the correct method name: generate_viral_script
    response = await service.generate_viral_script(request)

    print("\n" + "=" * 50)
    print("🔥 RIGOROUS LLM SELF-AUDIT RESULTS 🔥")
    print("=" * 50)
    print(f"❌ CRITIQUE (Negative):\n   {response.audit.critique_negative}")
    print(f"\n✅ CRITIQUE (Positive):\n   {response.audit.critique_positive}")
    print(f"\n📊 HOOK STRENGTH (Self): {response.audit.hook_strength}")
    print(f"🧐 RETENTION REASONING: {response.audit.retention_reasoning}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(test_audit_realism())
