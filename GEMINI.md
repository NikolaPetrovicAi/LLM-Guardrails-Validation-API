# Enterprise LLM Guardrails API (Developer Context)

Middleware servis za validaciju LLM izlaza, zaštitu privatnosti, optimizaciju troškova i evaluaciju performansi.

## 🏗️ Arhitektura & Inženjerski Standardi
Sistem je dizajniran prateći **Strategy** i **Dependency Injection** paterne za maksimalnu testabilnost i fleksibilnost.

- **FastAPI DI Arhitektura**: Kompletan sistem zavisnosti se kontroliše kroz `src/api/deps.py`, omogućavajući lako menjanje provajdera ili servisa.
- **Multi-Provider Support**: Apstraktni sloj (`BaseLLMProvider`) omogućava laku integraciju različitih LLM modela (OpenAI implementiran, Anthropic spreman).
- **Custom Exception System (RFC-7807)**: Strukturirano rukovanje greškama koje klijentima vraća standardizovane JSON odgovore (npr. `LLMValidationError`, `LLMTimeoutError`).
- **Resilience**: Napredna retry logika koristeći `tenacity` sa eksponencijalnim backoff-om za 429 i 5xx greške.

## ✅ Funkcionalnosti & AI Inženjering
Projekat demonstrira napredne AI "production-ready" koncepte:

### 1. Guardrails & Privacy
- **PII Masking Service**: Automatsko maskiranje osetljivih podataka (Email, Telefon, IBAN) pomoću regex obrazaca pre slanja LLM-u.

### 2. Hibridno Keširanje (Cost Optimization)
- **Exact Match Cache**: SHA-256 hash keširanje za identične upite.
- **Semantic Cache**: Vektorsko keširanje koristeći `Sentence-Transformers` (all-MiniLM-L6-v2). Prepoznaje značenje upita i vraća odgovor čak i ako su formulacije različite (npr. "What is capital of France?" vs "Tell me the capital of France").

### 3. Real-Time Capabilities
- **Streaming & Partial Validation**: Podrška za asinhrono strimovanje parcijalnih Pydantic objekata putem `/extract-stream` endpointa.

### 4. Ops & Observability
- **Strukturirano JSON Logovanje**: Logovi spremni za ELK/Datadog koji sadrže `request_id`, `latency_ms`, `cache_status`, `usage` i `estimated_cost_usd`.
- **Usage & Cost Tracking**: Automatsko računanje troškova na osnovu tokena i konfigurisanih cena po modelu.
- **Health Checks**: Endpoint `/api/v1/health` za monitoring statusa konekcija i keša.

## 🛠️ Dev & CI/CD
- **Dockerizacija**: Multi-stage Dockerfile za minimalnu veličinu image-a i Docker Compose za lokalni razvoj.
- **CI Pipeline**: GitHub Actions koji automatski pokreće `ruff` (linting) i `pytest` pri svakom push-u.
- **AI Benchmarking Tool**: Skripta `scripts/evaluate.py` za merenje latencije, troškova i preciznosti na testnim podacima.

## 🧠 Ključne Biblioteke
- `FastAPI`, `instructor` (Structured Outputs), `pydantic-settings`.
- `sentence-transformers`, `numpy` (Vektorske operacije).
- `diskcache`, `tenacity`, `httpx`, `structlog` (ili JSON logger).

## 🚀 Brze komande
- **Benchmarking**: `uv run python scripts/evaluate.py`
- **Svi testovi**: `uv run pytest`
- **Testovi otpornosti**: `uv run pytest tests/test_resilience.py`
- **Pokretanje**: `uv run python -m src.main`
