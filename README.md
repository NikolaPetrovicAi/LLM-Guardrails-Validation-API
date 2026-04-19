# 🚀 Viral Content Engine: Production-Grade AI Framework

This project is not just a script generator for social media; it is a **comprehensive AI Engineering framework** designed to solve the core challenges of deploying LLMs in production: **quality at scale, reliability, evaluation, and cost optimization.**

The system demonstrates how to transform raw foundation models into a stable product through advanced Prompt Ops, automated quality audits, and intelligent caching infrastructures.

---

## 🛠️ Core Engineering Pillars

### 1. Prompt Ops & Reliability (Prompts as Code)
Prompts are treated as production infrastructure rather than hardcoded strings:
*   **Externalized Prompting:** All prompts are stored in versioned YAML files, enabling A/B testing and rapid iterations without code deployments.
*   **Structured Outputs:** Leverages the `instructor` library to enforce strict Pydantic schemas, ensuring the backend receives typed, validated data every time.
*   **Dynamic Rendering:** Uses Jinja2 templating to balance complex logic with reliability, allowing for highly contextualized generations.

### 2. Automated Evaluation & Quality (Defining "Good")
To move beyond "vibe-based" engineering, I implemented a rigorous evaluation framework:
*   **Viral Audit (Self-Reflection):** A built-in "critic" loop where the model performs a self-audit, scoring content on `hook_strength`, `retention`, and `viral_potential`.
*   **LLM-as-a-Judge:** An evaluation pipeline where higher-tier models (e.g., GPT-4o) grade the outputs of smaller/faster models, providing objective quality benchmarks.
*   **Calibration Gap Analysis:** Systematic tracking of the difference between "self-scores" and "judge-scores" to identify and fix model hallucinations or quality drops.

### 3. Performance & Cost Engineering
Built for scale, the system focuses on minimizing latency and maximizing ROI:
*   **Tiered Semantic Caching (L1/L2):** A hybrid architecture combining ultra-fast In-Memory LRU (L1) with Persistent Vector Search (L2). This reduces latency to <1ms for known queries and significantly cuts API costs.
*   **Dynamic Thresholding:** The system intelligently adjusts cache sensitivity based on the complexity of the user's intent—ensuring high precision for simple queries and more creative flexibility for complex ones.
*   **ROI Analytics:** Every request logs `cost_savings_usd` and `latency_savings_ms`, providing a clear view of infrastructure efficiency.

### 4. Observability & Telemetry
A production system is only as good as its visibility:
*   **W3C Tracing & Langfuse:** Fully integrated lifecycle tracing using standard 32-character hex IDs to monitor every step from input to final generation.
*   **Semantic Diversity Audit:** Uses vector embeddings to measure the "creativity" of generated content, ensuring the system doesn't become repetitive over time.
*   **PII Masking:** Automated anonymization of sensitive data before it reaches external LLM providers, ensuring privacy and compliance.

---

## 🏗️ Tech Stack
*   **Backend:** Python (FastAPI)
*   **AI Orchestration:** OpenAI, Anthropic, and Instructor (Structured Data)
*   **Evaluation:** DeepEval & Custom Metric Pipelines
*   **Data & Caching:** Diskcache, FAISS/Sentence-Transformers (Embeddings)
*   **Observability:** Langfuse (Tracing) & JSONL Telemetry

---

## 💡 Why This Matters
As an AI Engineer, my focus is not just on the "magic" of a single prompt, but on the **predictability and scalability of the entire system.** This project proves the ability to own the full AI lifecycle: from designing complex evaluation frameworks and optimizing latency/cost, to building the robust software engineering foundations that modern AI products require.

---

### Quick Start
1. Configure your `.env` with API keys.
2. Run the API: `uv run python -m src.main`
3. Access interactive documentation at `/api/v1/docs`.
