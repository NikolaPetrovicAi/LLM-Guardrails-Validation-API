import asyncio
import json
import os

from dotenv import load_dotenv

from src.api.deps import get_llm_service
from src.models.schemas import ScriptRequest

# Load environment variables from .env
load_dotenv()


async def verify_lifecycle():
    print("🚀 Pokrećem verifikaciju Shadow Deployment-a i APO-a...")

    # Inicijalizacija servisa kroz postojeći DI sistem
    service = await get_llm_service()

    request = ScriptRequest(
        topic="Muzička industrija u 2026",
        target_audience="Ljubitelji muzike",
        tone="Inspirativno",
        platform="TikTok",
    )

    print("\n1. Šaljem zahtev ka LLM-u (Produkcija v1.0.0)...")
    response = await service.generate_viral_script(request)
    print(f"✅ Dobijen odgovor! Hook: {response.hook[:50]}...")
    print(f"📊 Viral Score: {response.audit.hook_strength}")

    # Čekamo trenutak da se asinhroni taskovi (Shadow i APO) izvrše u pozadini
    print("\n2. Čekam 2 sekunde da se asinhroni Shadow i APO taskovi završe...")
    await asyncio.sleep(2)

    print("\n3. Analiziram logs/metrics_data.jsonl...")
    metrics_file = "logs/metrics_data.jsonl"
    if os.path.exists(metrics_file):  # noqa: ASYNC240
        with open(metrics_file) as f:  # noqa: ASYNC230
            lines = f.readlines()
            # Uzimamo zadnjih nekoliko logova
            last_logs = [json.loads(line) for line in lines[-5:]]

            # Tražimo produkciju i shadow
            prod_log = next(
                (log for log in last_logs if log.get("prompt_version") == "1.0.0"), None
            )
            shadow_log = next(
                (log for log in last_logs if log.get("prompt_version") == "1.1.0"), None
            )

            if prod_log:
                print(
                    f"   🔹 Pronađen PROD log (v1.0.0): "
                    f"Latency: {prod_log.get('latency_ms')}ms"
                )
            if shadow_log:
                print(
                    f"   🔥 Pronađen SHADOW log (v1.1.0)! "
                    f"Latency: {shadow_log.get('latency_ms')}ms"
                )
            else:
                print("   ⚠️ Shadow log nije pronađen u zadnjih 5 unosa.")
    else:
        print(f"   ❌ Fajl {metrics_file} ne postoji.")


if __name__ == "__main__":
    asyncio.run(verify_lifecycle())
