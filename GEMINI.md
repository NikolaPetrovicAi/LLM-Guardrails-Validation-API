# Enterprise LLM Guardrails & Validation API (Portfolio Project)

This project is a middleware service developed as a portfolio piece to demonstrate key skills for an AI Engineer role. It sits between clients and Large Language Models (LLMs) to enforce JSON schema outputs and run validation guardrails using Python, FastAPI, and Pydantic.

## 🏗️ Project Architecture
- **`src/api/`**: FastAPI routers and endpoints.
- **`src/core/`**: Centralized configuration (`config.py`) and security.
- **`src/models/`**: Pydantic V2 schemas for validation and LLM structured output.
- **`src/services/`**: Core LLM orchestration and logic using `instructor`.
- **`tests/`**: Pytest suite for API and service logic validation.

## 🛠️ Tech Stack & Tooling
- **Python**: 3.11+ (Strict type hinting).
- **Package Manager**: `uv` (Fast and efficient dependency management).
- **API Framework**: `FastAPI` (Asynchronous, high performance).
- **Validation**: `Pydantic V2` (Strict data validation and serialization).
- **LLM Structured Output**: `instructor` (Best-in-class tool for structured LLM data).
- **Linting & Formatting**: `ruff` (Consistent, high-speed Python tooling).
- **Testing**: `pytest` & `pytest-asyncio`.

## ✅ Implemented Features
- [x] **Core Configuration**: Centralized settings with `pydantic-settings` and `SecretStr` for API keys.
- [x] **Pydantic Models**: `ExtractionRequest` and `StructuredResponse` for typed LLM interactions.
- [x] **LLM Service**: `LLMValidatorService` using `instructor` to enforce structured JSON output.
- [x] **API Endpoints**: `/api/v1/extract` and `/health` for data extraction and monitoring.
- [x] **Comprehensive Testing Suite**: A full suite of tests ensuring code reliability and correctness across all layers of the application.

## 🧪 Testing Strategy
A robust testing strategy was implemented using `pytest` to demonstrate best practices in software quality assurance:
- **Unit Tests**: Isolate and test individual components like Pydantic models (`test_models.py`), configuration (`test_config.py`), and services (`test_llm_service.py`). This ensures each piece works as expected on its own.
- **Integration Tests**: Verify that components work together correctly. `test_api.py` uses FastAPI's `TestClient` to test API endpoints and their interaction with the underlying service layer.
- **Mocking**: The `unittest.mock` library is used to simulate external services (like the OpenAI API). This makes tests fast, deterministic, and free of cost, a crucial skill when working with paid external APIs.

## 🧠 Development Guidelines
- **Strict Typing**: Always use Python 3.11+ type hints (e.g., `list[str]` instead of `List[str]`).
- **Configuration**: Use `src/core/config.py` with `pydantic-settings` for all environment variables.
- **Security**: Never log or print `SecretStr` values from `settings`.
- **Modularity**: Keep LLM logic isolated in `services/` and data structures in `models/`.
- **Testing**: Every new endpoint or service must have a corresponding test in `tests/`.
- **Tooling**: Use `uv run ruff check .` and `uv run pytest` before committing.

## 🚀 Common Commands
- **Install Dependencies**: `uv sync`
- **Run API (Dev)**: `uv run python src/main.py`
- **Run Tests**: `uv run pytest`
- **Lint Code**: `uv run ruff check . --fix`

---

### 📝 LLM Validation Service Summary
The `LLMValidatorService` (in `src/services/llm_service.py`) acts as the core engine. It wraps an asynchronous OpenAI client with the `instructor` library, forcing the LLM to return data that strictly adheres to the `StructuredResponse` Pydantic model. This ensures that downstream applications always receive valid, typed data.
