# Viral Content Engineer (Developer Context)

Sistem za generisanje viralnih TikTok/Reels/Shorts skripti sa ugrađenom automatizovanom revizijom kvaliteta (Viral Audit), zaštitom privatnosti i optimizacijom performansi.

## 📁 Struktura Projekta
- `src/api`: FastAPI rute (V1) i dependencije.
- `src/core`: Konfiguracija, logovanje i custom exception sistem.
- `src/models`: Pydantic šeme za viralne skripte, segmente i audit.
- `src/services`: Jezgro biznis logike (`ViralContentService`, Hibridno keširanje, PII Masking).
- `scripts`: Skripte za benchmarking (`evaluate.py`) i LLM-as-a-Judge evaluaciju.
- `tests`: Sveobuhvatni test suite (API, Resilience, Eval).

## 🏗️ Arhitektura & Inženjerski Standardi
Sistem je dizajniran prateći **Strategy** i **Dependency Injection** paterne za maksimalnu testabilnost i fleksibilnost.

- **FastAPI DI Arhitektura**: Kompletan sistem zavisnosti se kontroliše kroz `src/api/deps.py`, omogućavajući lako menjanje provajdera ili servisa.
- **Multi-Provider Support**: Apstraktni sloj (`BaseLLMProvider`) omogućava laku integraciju različitih LLM modela (`OpenAIProvider` implementiran kao "Elite Viral Strategist").
- **Custom Exception System (RFC-7807)**: Strukturirano rukovanje greškama koje klijentima vraća standardizovane JSON odgovore (npr. `LLMValidationError`, `LLMTimeoutError`).
- **Resilience**: Napredna retry logika koristeći `tenacity` sa eksponencijalnim backoff-om za 429 i 5xx greške.

## ✅ Funkcionalnosti & AI Inženjering
Projekat demonstrira napredne AI "production-ready" koncepte:

### 1. Viral Content Strategy & Guardrails
- **Automated Viral Audit**: Svaka generisana skripta prolazi kroz audit koji ocenjuje `hook_strength` i daje razloge za zadržavanje pažnje (retention).
- **PII Masking Service**: Automatsko maskiranje osetljivih podataka (**Email, Telefon, IBAN**) pomoću regex obrazaca pre slanja LLM-u, osiguravajući privatnost čak i pri generisanju skripti.

### 2. Hibridno Keširanje (Cost Optimization)
- **Exact Match Cache**: SHA-256 hash keširanje za identične upite (koristi `diskcache`).
- **Semantic Cache**: Vektorsko keširanje koristeći `Sentence-Transformers` (`all-MiniLM-L6-v2`) sa threshold-om od **0.92** za prepoznavanje sličnih tema/upita.

### 3. LLM-as-a-Judge Evaluation (Novo 🚀)
- **DeepEval Framework**: Integrisan za kvantitativno merenje kvaliteta generisanih skripti pomoću drugog LLM-a.
- **Metrike**: 
    - *Hook Strength*: Meri jačinu prve sekunde skripte.
    - *Adherence to Tone*: Proverava da li skripta prati zadati ton (npr. "Hype", "Educational").
    - *Faithfulness & Toxicity*: Potvrda bezbednosti i odsustva halucinacija.
- **Reporting**: `scripts/llm_judge_report.py` generiše Markdown izveštaje u `reports/`.

### 4. Real-Time Capabilities
- **Streaming Generation**: Podrška za asinhrono strimovanje parcijalnih Pydantic objekata putem `/generate-stream` endpointa koristeći **`instructor`** biblioteku.

### 5. Ops & Observability
- **Strukturirano JSON Logovanje**: Logovi spremni za ELK/Datadog koji sadrže `request_id`, `latency_ms`, `cache_status`, `usage` i `estimated_cost_usd`.
- **Usage & Cost Tracking**: Automatsko računanje troškova na osnovu tokena.

## 🛠️ Dev & CI/CD
- **Environment Variables**: Potreban `.env` fajl sa `OPENAI_API_KEY`.
- **Dockerizacija**: Multi-stage Dockerfile za minimalnu veličinu image-a.
- **CI Pipeline**: GitHub Actions koji automatski pokreće `ruff` (linting) i `pytest`.
- **AI Benchmarking Tool**: Skripta `scripts/evaluate.py` za merenje latencije i `hook_strength` u realnom vremenu.

## 🧪 Strategija Testiranja
- **Unit & Integration Tests**: Pokrivaju API rute, servise i modele (`pytest`).
- **Resilience Tests**: Simulacija mrežnih grešaka i timeout-a.
- **Semantic Cache Tests**: Validacija preciznosti vektorskog pretraživanja.

## 🧠 Ključne Biblioteke
- `FastAPI`, `instructor` (Structured Outputs), `pydantic-settings`.
- `sentence-transformers`, `numpy` (Vektorske operacije).
- `diskcache`, `tenacity`, `httpx`, `structlog`.

## 🚀 Brze komande
- **Pokretanje API-ja**: `uv run python -m src.main`
- **Svi testovi**: `uv run pytest`
- **Benchmarking**: `uv run python scripts/evaluate.py`
- **LLM Judge Report**: `uv run python scripts/llm_judge_report.py`
