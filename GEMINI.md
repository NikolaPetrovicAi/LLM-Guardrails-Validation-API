# Viral Content Engineer (Developer Context)

Sistem za generisanje viralnih TikTok/Reels/Shorts skripti sa ugrađenom automatizovanom revizijom kvaliteta (Viral Audit), zaštitom privatnosti i optimizacijom performansi.

## 📁 Struktura Projekta
- `src/api`: FastAPI rute (V1) i dependencije.
- `src/services`: Jezgro biznis logike (`ViralContentService`, Hibridno keširanje, PII Masking).
- `scripts`: Analitički alati (`advanced_analytics.py`, `semantic_diversity.py`, `evaluate.py`).
- `logs/metrics_data.jsonl`: Perzistentno skladište telemetrije za offline evaluaciju.

## 🏗️ Arhitektura & Inženjerski Standardi
- **FastAPI DI Arhitektura**: Potpuna kontrola zavisnosti kroz `deps.py`.
- **Structured Outputs**: Korišćenje `instructor` biblioteke za tipizirane LLM odgovore.
- **Custom Exception System (RFC-7807)**: Standardizovano rukovanje greškama.
- **Resilience**: Napredna retry logika koristeći `tenacity` sa exponential backoff-om.

## ✅ Funkcionalnosti & AI Inženjering

### 1. Viral Content Strategy & Guardrails
- **Automated Viral Audit**: Model vrši self-reflection ocenjujući `hook_strength` i `retention`.
- **PII Masking**: Automatska anonimizacija osetljivih podataka pre slanja LLM-u.

### 2. Hibridno Keširanje (Cost Optimization)
- **Exact & Semantic Cache**: SHA-256 i vektorsko keširanje (`all-MiniLM-L6-v2`) sa threshold-om od **0.92**.

### 3. Advanced AI Analytics (Novo 🚀)
- **Model Calibration Error**: Meri "objektivnost" modela upoređivanjem Self-Audit skora sa eksternim DeepEval Sudijom (`Calibration Gap`).
- **ROI (Efficiency) Analysis**: Izračunava odnos kvaliteta i cene (`External_Score / Cost_USD`) za optimizaciju budžeta.
- **DeepEval Framework**: Korišćenje nezavisnog LLM-a za validaciju Faithfulness, Toxicity i Relevancy metrika.

### 4. Creative Diversity Audit
- **Semantic Diversity Analysis**: Meri sličnost generisanih skripti koristeći `Cosine Similarity`.
- **Diversity Score**: `1 - Average_Similarity` (Cilj > 0.3 za visoku kreativnost).
- **Redundancy Check**: Identifikacija najsličnijih parova radi optimizacije promptova.

### 5. Ops & Observability
- **Enhanced Telemetry**: Svaki request loguje `request_id`, `latency_ms`, `cost_usd`, `input_text` i `output_text` u JSONL formatu za naknadnu evaluaciju.
- **Real-Time Streaming**: Asinhrono strimovanje parcijalnih objekata korisniku.

## 🛠️ Dev & CI/CD
- **Environment Variables**: Potreban `.env` sa `OPENAI_API_KEY`.
- **AI Benchmarking**: Skripte za evaluaciju performansi u realnom vremenu.

## 🚀 Brze komande
- **Pokretanje API-ja**: `uv run python -m src.main`
- **Svi testovi**: `uv run pytest`
- **Advanced Analytics**: `uv run python -m scripts.advanced_analytics`
- **Diversity Audit**: `uv run python scripts.semantic_diversity.py`
- **Benchmarking**: `uv run python scripts/evaluate.py`
