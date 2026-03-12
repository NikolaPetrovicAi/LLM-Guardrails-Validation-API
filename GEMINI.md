# Enterprise LLM Guardrails & Validation API (Portfolio Project)

This project is a middleware service developed as a portfolio piece to demonstrate key skills for an AI Engineer role. It sits between clients and Large Language Models (LLMs) to enforce JSON schema outputs and run validation guardrails using Python, FastAPI, and Pydantic.

## 🏗️ Project Architecture
- **`src/api/`**: FastAPI routers, endpoints, and `deps.py` for Dependency Injection.
- **`src/core/`**: Configuration (`config.py`), security, and global `exceptions.py`.
- **`src/models/`**: Pydantic V2 schemas for validation and LLM structured output.
- **`src/services/`**: Core LLM orchestration using `instructor` with robust error mapping.
- **`tests/`**: Pytest suite for API, service logic, and DI validation.

## 🛠️ Tech Stack & Tooling
- **Python**: 3.11+ (Strict type hinting).
- **Package Manager**: `uv` (Fast and efficient dependency management).
- **API Framework**: `FastAPI` (Asynchronous, Dependency Injection).
- **Validation**: `Pydantic V2` (Strict data validation and serialization).
- **LLM Structured Output**: `instructor` (Best-in-class tool for structured LLM data).
- **Linting & Formatting**: `ruff` (Consistent, high-speed Python tooling).
- **Testing**: `pytest` & `pytest-asyncio`.

## ✅ Implemented Features
- [x] **Core Configuration**: Centralized settings with `pydantic-settings` and `SecretStr`.
- [x] **Dependency Injection**: Refactored services to use FastAPI `Depends` for better testability.
- [x] **Custom Exception System**: RFC-7807 compliant global handler with `AppException` hierarchy.
- [x] **Request Logging Middleware**: Automatic auditing of method, path, status, and latency.
- [x] **LLM Service**: `LLMValidatorService` with OpenAI error mapping (Authentication, Timeout).
- [x] **API Endpoints**: `/api/v1/extract` and `/health` with full DI support.
- [x] **Comprehensive Testing Suite**: Full suite covering models, config, services, and API.

## 🧪 Testing Strategy
A robust testing strategy was implemented using `pytest`:
- **Unit & Integration Tests**: Testing components in isolation and as a system.
- **Dependency Overrides**: Using `app.dependency_overrides` for clean API testing with mocks.
- **Mocking**: Simulating OpenAI responses to ensure fast, deterministic, and cost-free tests.

## 🧠 Development Guidelines
- **Strict Typing**: Always use Python 3.11+ type hints.
- **Dependency Injection**: Never instantiate services directly in endpoints; use `deps.py`.
- **Error Handling**: Raise specific `AppException` subclasses; avoid raw `HTTPException` in services.
- **Logging**: Middleware handles basic request logging; use `logger` for service-level events.
- **Security**: Never log or print `SecretStr` values.
- **Testing**: Every new feature or fix must include corresponding tests.

## 🚀 Common Commands
- **Install Dependencies**: `uv sync`
- **Run API (Dev)**: `uv run python -m src.main`
- **Run Tests**: `uv run pytest`
- **Lint Code**: `uv run ruff check . --fix`

---

### 📝 LLM Validation Service Summary
The `LLMValidatorService` (in `src/services/llm_service.py`) acts as the core engine. It wraps an asynchronous OpenAI client with the `instructor` library, forcing the LLM to return data that strictly adheres to the `StructuredResponse` Pydantic model. This ensures that downstream applications always receive valid, typed data.
