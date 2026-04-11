# Viral Content Engineer (Developer Context)

Sistem za generisanje viralnih TikTok/Reels/Shorts skripti sa ugrađenom automatizovanom revizijom kvaliteta (Viral Audit), zaštitom privatnosti i optimizacijom performansi.

## 📁 Struktura Projekta
- `src/api`: FastAPI rute (V1) i dependencije.
- `src/prompts`: YAML definicije promptova sa verzisanjem (Prompt Ops).
- `src/services`: Jezgro biznis logike (`ViralContentService`, `PromptManager`, `PromptOptimizerService`, Hibridno keširanje, PII Masking).
- `scripts`: Analitički alati (`advanced_analytics.py`, `semantic_diversity.py`, `evaluate.py`, `verify_lifecycle.py`).
- `logs/metrics_data.jsonl`: Perzistentno skladište telemetrije za offline evaluaciju.

## 🏗️ Arhitektura & Inženjerski Standardi
- **Prompt Ops (Versioning & Externalization)**: Izmeštanje promptova iz koda u YAML fajlove. Podrška za "version pinning" i dinamičko renderovanje pomoću Jinja2.
- **FastAPI DI Arhitektura**: Potpuna kontrola zavisnosti kroz `deps.py`, uključujući `PromptManager`.
- **Strategy Pattern (Caching & Storage)**: Razdvajanje logike embedding-a, pretrage vektora i skladištenja u čiste interfejse radi lakše zamene komponenti (npr. FAISS, Qdrant).
- **Structured Outputs**: Korišćenje `instructor` biblioteke za tipizirane LLM odgovore.
- **Custom Exception System (RFC-7807)**: Standardizovano rukovanje greškama.
- **Resilience**: Napredna retry logika koristeći `tenacity` sa exponential backoff-om.

## ✅ Funkcionalnosti & AI Inženjering

### 1. Viral Content Strategy & Prompt Ops
- **Automated Viral Audit**: Model vrši self-reflection ocenjujući `hook_strength` i `retention`.
- **Versioned Prompts**: Omogućava A/B testiranje promptova i brzo vraćanje na prethodne stabilne verzije.
- **Shadow Deployment**: Paralelno izvršavanje kandidat verzija promptova bez uticaja na korisničko iskustvo radi real-time evaluacije.
- **Automated Prompt Optimization (APO)**: "Critique & Suggest" petlja koja koristi Critic model za automatsko poboljšanje promptova na osnovu audit feedback-a.
- **PII Masking**: Automatska anonimizacija osetljivih podataka pre slanja LLM-u.

### 2. Tiered Caching & Dynamic Thresholding (Novo 🚀)
- **Tiered Architecture (L1/L2)**: 
    - **L1 (In-Memory LRU)**: Ultra-brzi keš za trenutni pristup (latency < 1ms).
    - **L2 (Persistent Vector Store)**: Semantička pretraga koristeći `all-MiniLM-L6-v2` i `diskcache`.
- **Dynamic Thresholding (Intent-Based)**: Prilagođavanje strogosti pretrage na osnovu kompleksnosti upita:
    - **Informativni (< 10 reči)**: Visok threshold (**0.95**) za maksimalnu preciznost.
    - **Standardni (10-50 reči)**: Threshold (**0.92**).
    - **Kreativni (> 50 reči)**: Nizak threshold (**0.88**) za veću fleksibilnost scenarija.
- **Cache Efficiency Analytics**: Automatsko logovanje `latency_savings_ms` i `cost_savings_usd` za svaki keš hit u telemetriju.

### 3. Advanced AI Analytics (Novo 🚀)
- **Model Calibration Error**: Meri "objektivnost" modela upoređivanjem Self-Audit skora sa eksternim DeepEval Sudijom (`Calibration Gap`).
- **ROI (Efficiency) Analysis**: Izračunava odnos kvaliteta i cene (`External_Score / Cost_USD`) za optimizaciju budžeta.
- **Prompt ROI Analysis**: Praćenje performansi specifičnih verzija promptova kroz telemetriju.

### 4. Creative Diversity Audit
- **Semantic Diversity Analysis**: Meri sličnost generisanih skripti koristeći `Cosine Similarity`.
- **Diversity Score**: `1 - Average_Similarity` (Cilj > 0.3 za visoku kreativnost).
- **Redundancy Check**: Identifikacija najsličnijih parova radi optimizacije promptova.

### 5. Ops & Observability
- **Langfuse v4 (W3C Tracing)**: Implementiran standardizovani 32-karakterni hex `trace_id`. Obavezno korišćenje `generation.end()` za ispravno slanje podataka u dashboard.
- **Enhanced Telemetry**: Svaki request loguje `request_id`, `prompt_id`, `prompt_version`, `latency_ms`, `cost_usd`, `input_text` i `output_text` u JSONL formatu.
- **Real-Time Streaming**: Asinhrono strimovanje parcijalnih objekata korisniku uz podršku za dinamičke promptove.

## 🛠️ Dev & CI/CD
- **Environment Variables**: Potreban `.env` sa `OPENAI_API_KEY`.
- **API Documentation**: Swagger UI dostupan na `/api/v1/docs`.
- **AI Benchmarking**: Skripte za evaluaciju performansi u realnom vremenu.
- **Prompt Testing**: Unit testovi za validaciju template-a i injektovanja varijabli (`tests/test_prompt_manager.py`).

## 🚀 Brze komande
- **Pokretanje API-ja**: `uv run python -m src.main`
- **Swagger Docs**: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
- **Svi testovi**: `uv run pytest`
- **Advanced Analytics**: `uv run python -m scripts.advanced_analytics`
- **Diversity Audit**: `uv run python scripts.semantic_diversity.py`
- **Benchmarking**: `uv run python scripts/evaluate.py`
