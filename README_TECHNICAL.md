# 🚀 Aivy Workspace: High-Fidelity AI Document Engine

**Aivy Workspace** is a specialized document orchestration system designed to eliminate the non-deterministic nature of LLM-generated content. Unlike traditional AI writing tools that rely on fragile free-form text parsing, Aivy implements a schema-driven workflow that enforces structural integrity through a dedicated Intermediate Representation (IR).

By leveraging OpenAI Structured Outputs and a custom index-sensitive mapping engine, the system transforms abstract AI intents into precise Google Docs API `batchUpdate` sequences. This ensures 100% layout parity and allows for complex document structures to be rendered deterministically within the Google Workspace ecosystem.


---

## 🌟 Key Features

*   **Asynchronous Planner–Writer Pipeline** The system decouples document architecture from content synthesis. The Planner (`aiPlanner.js`) performs context-aware block selection (Business vs. Non-Business logic), organizing "Small" and "Large" logical templates into a paginated blueprint. The Writer (`aiWriter.js`) then populates these templates, adhering to strict heuristic constraints (e.g., maximum item limits per list) to ensure visual consistency and professional document density.

*   **Deterministic Generation via OpenAI Structured Outputs:** Aivy leverages OpenAI Structured Outputs with strict JSON schemas (strict: true) to ensure the LLM output is 100% compliant with the application's internal data model. This approach eliminates the need for heuristic-based parsing and allows for the direct transformation of JSON data into hierarchical Google Docs elements, guaranteeing valid document structures for every generation.

*   **Context-Aware Editing with State-Isolated Streaming:** The in-editor AI assistant (aiEditor.js) performs range-restricted modifications by analyzing the full document context for style and tone consistency, while strictly limiting edits to the user-selected text. To maintain a responsive 60FPS experience, the system uses a state isolation strategy: streaming updates are injected directly into the ProseMirror state, bypassing React's reconciliation cycle during active generation. Global state synchronization is deferred until the stream is complete, preventing UI lag.


---

## 🛠 Engineering Challenges & Solutions

### 1. Structured AI-to-Document Mapping via JSON Schemas
**Problem:** Mapping non-deterministic LLM outputs to the strictly indexed Google Docs API often results in structural failures or malformed documents due to unpredictable AI-generated syntax.

**Solution:** Implemented a dedicated Intermediate Representation (IR) layer leveraging OpenAI Structured Outputs with strict: true. This architecture forces the LLM to generate a sequence of typed block-primitives (e.g., STATS_ROW_BLOCK, SWOT_LIST_BLOCK) that map directly to pre-defined batchUpdate request sequences. By validating AI outputs against a strict JSON schema, the system ensures that all generated content is structurally compliant with the Google Docs API requirements before any document modification begins.

### 2. High-Fidelity Rendering & Style Inheritance Control
**Problem:** Achieving visual parity between a browser-based DOM and the linear, index-sensitive Google Docs API is difficult due to the API's implicit style inheritance model, where new paragraphs automatically carry over formatting from preceding blocks.

**Solution:** Developed an Explicit Style Translation layer utilizing a two-phase rendering algorithm. The first phase performs a recursive DOM traversal to map HTML nodes into a linear, index-aware array. The second phase executes a Priority-Based Operation Sequence: it performs an Atomic Style Cleanup of inherited properties (using targeted delete requests) before applying new formatting. This ensures precise control over indentation, alignment, and spacing, guaranteeing that the final document matches the editor's layout deterministically.

### 3. State-Isolated Streaming & Performance Optimization
**Problem:** Streaming AI-generated text directly into a React-based rich-text editor at high frequencies triggers massive reconciliation cycles, leading to UI "choking," input lag, and a degraded 60FPS user experience.

**Solution:** Implemented a State Isolation strategy within the Tiptap/ProseMirror environment. During active AI generation, the system bypasses the global React state update cycle (onPageUpdate). Instead, incoming text chunks are injected directly into the editor’s internal ProseMirror state. Global state synchronization and "de-buffering" (flush) only occur once the stream is closed. This architecture drastically reduces the number of re-renders, maintaining a highly responsive UI even during long-form content generation.

---

## 🧠 AI Logic & Prompt Engineering
Aivy Workspace utilizes modularized AI engines for different document lifecycle stages. You can review the prompt engineering and JSON schemas in the following backend files:

- **Document Planner (backend/ai/aiPlanner.js):** Orchestrates initial blueprinting and block selection based on domain context.
- **Structured Writer (backend/ai/aiWriter.js):** Uses OpenAI Structured Outputs to populate templates while enforcing strict visual density constraints.
- **Contextual Editor (backend/ai/aiEditor.js):** Performs range-restricted transformations, analyzing full document context to maintain style consistency.

---

## 🏗 Architecture & Tech Stack

### Frontend
- **Framework:** Next.js (App Router) with React.
- **Editor:** Tiptap (ProseMirror) with custom extensions for structured content, alignment, and AI-assisted editing.
- **Styling:** Tailwind CSS for consistent, utility-driven UI composition.

### Backend
- **Runtime:** Node.js with Express.
- **AI Orchestration:** OpenAI API with streaming support and schema-constrained generation.
- **Integrations:** Google Workspace APIs (Docs, Drive, OAuth 2.0).
- **Session Management:** Secure multi-user session handling for OAuth tokens and editor state.

---

## 🚀 Installation & Setup

### Prerequisites
- Node.js 20+
- Google Cloud Project with Docs/Drive APIs enabled.
- OpenAI API Key.

### Quick Start
1. **Clone & Install:**
   ```bash
   git clone https://github.com/your-username/aivy-workspace
   cd aivy-workspace
   npm install && cd frontend && npm install && cd ../backend && npm install
   ```
2. **Environment Setup:** Create a `.env` in the `backend/` folder (see `.env.example`).
3. **Run Locally:**
   - **Backend:** `cd backend && node index.js`
   - **Frontend:** `cd frontend && npm run dev`
4. **Authenticate:** Visit `http://localhost:3000`. The application will automatically redirect you to the Google login page to link your account.
