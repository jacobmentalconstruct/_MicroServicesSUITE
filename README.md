# _MicroServicesSUITE

> **The "Lego Box" for Cognitive Architectures.**

**\_MicroServicesSUITE** is a modular library of high-performance, self-contained Python microservices designed for building advanced AI agents, RAG systems, and developer tools.

Unlike monolithic frameworks, each service here is atomic. You can use them individually (as Python imports), wrap them instantly as REST APIs (via `_APIGatewayMS`), or let an AI Architect assemble them into custom applications.

-----

## 📂 The Catalog

### 🧠 The Brain (Cognition & Memory)

| Microservice | Description |
| :--- | :--- |
| **`_CognitiveMemoryMS`** | Orchestrates tiered memory (Working RAM → Short-Term JSONL → Long-Term Vector DB). |
| **`_PromptVaultMS`** | A SQLite-backed CMS for prompt templates with versioning (v1, v2) and Jinja2 rendering. |
| **`_PromptOptimizerMS`** | An "AI-for-AI" tool that uses LLMs to refine prompts and generate A/B testing variations. |
| **`_RoleManagerMS`** | Manages Agent Personas (System Prompts, Knowledge access, Memory policies). |
| **`_TaskVaultMS`** | A hierarchical task database supporting infinite sub-task nesting and status tracking. |

### 👁️ The Eyes (Ingestion & RAG)

| Microservice | Description |
| :--- | :--- |
| **`_IngestEngineMS`** | The main orchestrator for reading files, embedding content, and populating the Knowledge Graph. |
| **`_SmartChunkerMS`** | Recursive text splitter (Paragraph → Sentence) for high-quality semantic chunking. |
| **`_CodeChunkerMS`** | Structure-aware code splitter using **Tree-Sitter** to preserve function boundaries and docstrings. |
| **`_WebScraperMS`** | Fetches URLs and strips boilerplate/ads using `readability` for clean context injection. |
| **`_SearchEngineMS`** | Performs Hybrid Search (Vector + Keyword) using Reciprocal Rank Fusion (RRF). |
| **`_RegexWeaverMS`** | Fault-tolerant dependency scanner that maps code imports using Regex (AST fallback). |

### ✋ The Hands (Action & Safety)

| Microservice | Description |
| :--- | :--- |
| **`_SandboxManagerMS`** | A safety harness that mirrors projects into a sandbox for safe AI code editing. |
| **`_DiffEngineMS`** | Tracks file evolution using a "Head" (Cache) + "History" (Delta Logs) architecture. |
| **`_GitPilotMS`** | A drop-in Tkinter GUI for Git operations (Stage, Commit, Push, Log). |
| **`_ArchiveBotMS`** | Creates smart `.tar.gz` snapshots, automatically excluding `node_modules`, `.venv`, etc. |
| **`_LibrarianMS`** | Manages the physical creation, duplication, and deletion of SQLite Knowledge Bases. |

### 🖥️ The Interface (UI Components)

| Microservice | Description |
| :--- | :--- |
| **`_MonacoHostMS`** | Embeds a full VS Code-like editor (Monaco) inside Python apps using `pywebview`. |
| **`_GraphEngineMS`** | Client-side physics simulation for visualizing Knowledge Graphs (Pygame). |
| **`_NetworkLayoutMS`** | Server-side graph topology calculator (NetworkX) for static graph rendering. |
| **`_ThoughtStreamMS`** | A real-time "Matrix style" log viewer for visualizing AI thought processes. |
| **`_LogViewMS`** | A professional logging console with message consolidation and level filtering. |
| **`_ExplorerWidgetMS`** | A rich file tree widget with checkbox selection and async size calculation. |

### ⚙️ The Core (Infrastructure)

| Microservice | Description |
| :--- | :--- |
| **`_ServiceRegistryMS`** | **The Tokenizer.** Scans this suite and generates a JSON manifest of all available tools. |
| **`_APIGatewayMS`** | A factory that wraps *any* microservice logic into a FastAPI REST server with Swagger UI. |
| **`_IsoProcessMS`** | Runs heavy/unstable tasks (ML inference) in isolated processes to prevent crashes. |
| **`_VectorFactoryMS`** | Database-agnostic adapter. Switch between `ChromaDB` and `FAISS` via config. |
| **`_AuthMS`** | Handles user authentication, password hashing, and JWT-like session tokens. |
| **`_FingerprintScannerMS`** | Calculates deterministic Merkle Roots for directory trees to detect changes instantly. |
| **`_SysInspectorMS`** | Cross-platform hardware auditor (CPU/GPU/RAM metrics) for environment debugging. |

-----

## 🚀 Usage

### 1\. Direct Python Import (The "Monolith" Way)

You can import any service directly into your script. All services are designed to be importable without side effects.

```python
# Example: Building a Safe Code Editor
from _MonacoHostMS.monaco_host import MonacoHostMS
from _SandboxManagerMS.sandbox_manager import SandboxManagerMS

sandbox = SandboxManagerMS("./live_project", "./sandbox")
sandbox.init_sandbox()

editor = MonacoHostMS()
editor.launch()
```

### 2\. The API Gateway (The "Microservices" Way)

Turn any logic class into a REST API instantly.

```python
from _APIGatewayMS.api_gateway import APIGatewayMS
from _SearchEngineMS.search_engine import SearchEngineMS

# Initialize the logic
engine = SearchEngineMS("./knowledge.db")

# Wrap it
gateway = APIGatewayMS(engine)
gateway.add_endpoint("/search", "POST", lambda req: engine.search(req['query']))
gateway.start(port=8000)
```

### 3\. The AI Architect Workflow (The "Future" Way)

This suite is designed to be read by AI.

1.  Run `python _ServiceRegistryMS/service_registry.py`.
2.  This generates `registry.json` in the root.
3.  Feed `registry.json` to an LLM with the prompt:
    > "I need an app that scrapes websites and saves them to a Vector DB. Use the tools in the registry to generate the `app.py` code."

-----

## 🏗️ Development Standards

To add a new service to the suite, follow these rules so the **Registry** can detect it:

1.  **Naming:** Folder must be `_NameMS`. Main file should be snake\_case (e.g., `name.py`).
2.  **Class:** The main class should end in `MS` (e.g., `NameMS`).
3.  **Independence:** The service should run its own logic. Use `_IsoProcessMS` if you need to import heavy conflicting libraries (like torch vs tensorflow).
4.  **Self-Test:** Every script must have an `if __name__ == "__main__":` block that demonstrates its functionality.

-----

## 📚 Snippets Library

Check `_examples-and-snippets/MASTER_Snippets_Library.json` for a collection of 30+ high-value, copy-pasteable logic blocks (Regex patterns, SQL triggers, Algorithms) extracted from these services.

-----

**Built for the Age of Agents.**