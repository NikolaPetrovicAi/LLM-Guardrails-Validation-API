# 🚀 Viral Content Engine: Technical Deep Dive

This document provides a comprehensive overview of the engineering architecture, Prompt Ops strategies, and evaluation frameworks powering the **Viral Content Engine**. Designed for engineers, this deep dive focuses on the "how" and "why" of our AI infrastructure, emphasizing scalability, observability, and performance optimization.

---

## 1. System Architecture & Orchestration

The system is built on a modular **FastAPI** backend, utilizing a strict **Dependency Injection (DI)** pattern to ensure high testability and separation of concerns.

### High-Level Data Flow
1. **API Layer**: Validates incoming Pydantic schemas and injects dependencies.
2. **Orchestration (`ViralContentService`)**: Coordinates the lifecycle of a request: PII masking -> Semantic Cache lookup -> Prompt Rendering -> LLM Execution -> Telemetry.
3. **Provider Abstraction**: A strategy pattern for LLM backends (OpenAI, Anthropic), wrapped with the `instructor` library for guaranteed **Structured Outputs**.

```ascii
[Client] -> [FastAPI Endpoints] -> [deps.py (DI)]
                                        |
               [ViralContentService (Orchestrator)]
                /          |           |          \
      [PIIMasking]  [PromptManager] [SemanticCache] [LLM Provider]
            |              |           |               |
      (Regex/NLP)    (YAML/Jinja2)  (L1/L2 Tiered)  (Instructor/Pydantic)
```

### Dependency Injection (`src/api/deps.py`)
We leverage `functools.lru_cache` for singleton service instantiation. This allows for seamless provider swapping (e.g., switching from GPT-4o to Claude 3.5 Sonnet) and simplifies unit testing by allowing easy dependency overrides.

---

## 2. Prompt Ops: Prompts as Code

Prompt engineering is treated with the same rigor as production code. Prompts are externalized into YAML files within `src/prompts/`, enabling **Version Pinning** and **Shadow Deployments**.

### Versioning & Shadow Deployment
Our `PromptManager` supports loading specific versions and "shadow" versions for A/B testing:
```yaml
id: tiktok_script_v1
version: 1.0.2
shadow_version: 1.1.0-candidate  # Runs in parallel for evaluation
config:
  model_name: "gpt-4o"
  temperature: 0.7
system_prompt: "You are a viral strategist for {{ platform }}..."
```

### Key Components:
- **Jinja2 Rendering**: Allows for complex logic within templates (e.g., platform-specific instructions or dynamic few-shot examples).
- **Structured Outputs**: By using `instructor`, we eliminate parsing errors. The LLM's output is directly validated against Pydantic models (e.g., `ViralScriptResponse`), ensuring downstream reliability.

---

## 3. Tiered Semantic Caching & Latency Optimization

To achieve sub-millisecond lookups for common intents and significant cost savings, we implemented a **Tiered Semantic Cache** (`src/services/semantic_cache.py`).

### Cache Layers:
1. **L1 (In-Memory LRU)**: An `OrderedDict`-based cache for exact or near-exact matches, serving responses in **<1ms**.
2. **L2 (Persistent Vector Store)**: Uses `SentenceTransformers` (`all-MiniLM-L6-v2`) and `diskcache`. This layer performs semantic similarity searches.

### Dynamic Thresholding (Intent-Based)
The system dynamically adjusts the similarity threshold based on the query complexity to prevent "hallucinated" cache hits:
- **Short Informational (<10 words)**: High threshold (**0.95**) for maximum precision.
- **Creative/Long-Form (>50 words)**: Lower threshold (**0.88**) to allow for semantic flexibility in complex scenarios.

---

## 4. Evaluation Framework: The "Math" of Quality

We move beyond "vibe checks" by implementing a quantitative evaluation framework using **LLM-as-a-Judge** (via `DeepEval`).

### Core Metrics:
- **Mean Calibration Error (MCE)**: Measures the "Calibration Gap" between the model's self-audit (how good it *thinks* it is) and an external GPT-4o judge.
- **ROI (Efficiency Ratio)**: Calculated as `(Judge_Score / USD_Cost)`. This helps us identify the Pareto frontier between model performance and price.
- **Semantic Diversity**: Uses `Cosine Similarity` across the generated dataset to ensure the system isn't producing repetitive outputs, which is critical for creative "viral" content.

### Calibration Audit Example
| Trace ID | Version | Model | Self-Audit | Judge Score | MCE (Gap) | ROI |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `8f2a1c...` | 1.0.2 | gpt-4o | 0.90 | 0.85 | 0.05 | 120x |

---

## 5. Observability & Telemetry

Full-stack tracing and telemetry are mandatory for production stability.

- **W3C Tracing**: Integrated with **Langfuse** using 32-character hex `trace_id`s. Every LLM call, cache hit, and evaluation is linked.
- **Telemetry (`logs/metrics_data.jsonl`)**: We log every request with metadata: `prompt_id`, `version`, `latency_ms`, `cost_usd`, and `tokens_used`. This enables offline ROI analysis and model performance auditing.
- **PII Masking**: Integrated into the pipeline to ensure sensitive user data is never sent to the LLM providers or stored in logs.

---

## 6. Local Development & Benchmarking

### Setup
```bash
# Install dependencies using 'uv'
uv sync

# Run the production API
uv run python -m src.main
```

### Benchmarking & Analytics
The project includes specialized scripts for deep-dive analysis:
- **Advanced Analytics**: `uv run python scripts/advanced_analytics.py` (Calculates MCE and ROI).
- **Diversity Audit**: `uv run python scripts/semantic_diversity.py` (Measures output creativity).
- **Lifecycle Verification**: `uv run python scripts/verify_lifecycle.py` (E2E smoke tests).

---

**Engineering Philosophy**: This engine is designed to be model-agnostic and metric-driven. By treating prompts as versioned assets and evaluation as a continuous integration step, we ensure that improvements in the "viral" quality are measurable, reproducible, and cost-effective at scale.
