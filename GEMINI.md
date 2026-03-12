# Enterprise LLM Guardrails API

Middleware servis za validaciju LLM izlaza, zaštitu privatnosti i optimizaciju performansi.

## 🏗️ Arhitektura & Tech Stack
- **Framework**: FastAPI (Async, DI preko `deps.py`).
- **LLM**: OpenAI + `instructor` (Structured Output).
- **Guardrails**: `PIIMaskingService` (Regex PII maskiranje).
- **Caching**: `diskcache` (Smanjenje latencije i troškova).
- **Observability**: `python-json-logger` (RFC-7807 JSON logovi).
- **Infrastruktura**: Docker (Multi-stage), GitHub Actions (CI).

## ✅ Funkcionalnosti
- [x] **PII Masking**: Automatsko prepoznavanje i maskiranje Email, Phone i IBAN podataka.
- [x] **Response Caching**: Keširanje odgovora na osnovu SHA-256 hasha prompta.
- [x] **Structured Logging**: Logovi sadrže `request_id`, `latency_ms` i `cache_status`.
- [x] **Dockerized**: Spreman za produkciju uz `docker-compose`.

## 🧠 Smernice za razvoj
- **Privatnost**: Sav ulaz mora proći kroz `PIIMaskingService` pre slanja LLM-u.
- **Logovanje**: Koristiti `logger.info(..., extra={...})` za dodatna polja u JSON-u.
- **Testiranje**: Obavezni unit testovi za nove guardrail servise.

## 🚀 Brze komande
- **Testovi**: `uv run pytest`
- **Pokretanje**: `uv run python -m src.main`
- **Docker**: `docker-compose up --build`
