# 🧠 AI Knowledge Hub

An intelligent enterprise document search and knowledge management system built with **Microsoft Semantic Kernel**, **Azure AI Search**, and **Azure OpenAI (GPT-5 Mini)** with an interactive **Streamlit** user interface.

---

## 📌 Project Overview

Employees can ask natural language questions about company policies, documents, and internal knowledge. The system orchestrates multiple specialized AI agents to retrieve, synthesize, and validate information strictly grounded in internal documentation without hallucinations.

### 🌟 Key Features
- **Multi-Agent Orchestration**: A Query Router selects the relevant source(s), then **Search Agent**, **Database Agent**, and/or **Wiki Agent** retrieve content, followed by the **Summarization Agent** and **Validation Agent**.
- **Multi-Source Retrieval**: Connects to three distinct source types — Azure AI Search (policy PDFs), a structured SQLite database (employee directory), and local wiki/how-to markdown docs.
- **Microsoft Semantic Kernel Powered**: Utilizes Semantic Kernel connectors and kernel functions for agent prompt engineering and execution.
- **Folder-Scoped Document Retrieval**: Server-side filters internal documents within the shared Azure AI Search index by the user's assigned folder (e.g. `internpdfs/viola/`), via a filterable `folder_normalized` index field rather than client-side scanning.
- **Query Routing with Fallback**: A lightweight keyword classifier decides which source(s) a question needs *before* retrieval, so most questions only pay the latency of one connector instead of always querying every source. If the chosen source(s) return nothing, the orchestrator expands to the remaining source(s) before giving up — see [`src/query_router.py`](src/query_router.py) and [`src/orchestrator.py`](src/orchestrator.py) for the exact tradeoff this makes (expansion only triggers on a literally empty primary result; a single weak keyword-overlap match still counts as "found something" and won't trigger it).
- **Hallucination Prevention**: Returns *"Information not found in the provided documents."* with `NOT SUPPORTED` status if facts are not present in source documents.
- **Modern Streamlit UI**: Intuitive web interface with quick sample query chips, real-time agent execution pipeline indicators, validation badges, and source document viewers.

---

## 🏗️ Multi-Agent Architecture & Workflow

```
[ User Input in Streamlit UI ]
       │ (Question + Folder Name: e.g. "viola")
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 0. 🧭 Query Router                                            │
│    - Classifies the question by keyword (database/wiki/docs)│
│    - Selects only the source(s) the question actually needs │
└─────────────────────────────────────────────────────────────┘
       │ Selected source(s)
       ▼
┌───────────────┬─────────────────┬─────────────────────────┐
│ 🔍 Search Agent │ 🗄️ Database Agent │ 📚 Wiki Agent            │
│ Azure AI Search │ SQLite employee  │ Local markdown how-to/  │
│ (policy PDFs),  │ directory,       │ FAQ docs, scored by     │
│ folder-scoped   │ keyword-filtered │ keyword overlap         │
└───────────────┴─────────────────┴─────────────────────────┘
       │ Empty? Expand to the remaining, un-routed source(s)
       │ (fallback — only fires if the primary pick found nothing)
       ▼
       Retrieved Document Chunks (merged, tagged by source)
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 📝 Summarization Agent (Semantic Kernel)                     │
│    - Grounded strictly in retrieved source context          │
│    - Synthesizes clear, concise, professional answer        │
│    - Emits fallback if facts are missing                    │
└─────────────────────────────────────────────────────────────┘
       │ Candidate Answer + Source Context
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 🛡️ Validation Agent (Semantic Kernel)                        │
│    - Cross-examines candidate answer against source chunks  │
│    - Validates factual accuracy and eliminates hallucination│
│    - Classifies status: SUPPORTED / PARTIALLY / NOT         │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
[ Output: Formatted Answer + Validation Badge + Source Excerpts ]
```

### Agent Roles Explained
1. **Query Router (`src/query_router.py`)**: Keyword-based classifier that picks the *primary* source(s) a question needs before any retrieval runs — the "balance speed vs. accuracy/relevance" step. Falls back to the documents source when nothing more specific matches.
2. **Orchestrator fallback (`src/orchestrator.py::_retrieve`)**: If the router's primary pick returns zero documents, the orchestrator expands to the remaining source(s) before giving up — one extra retrieval round-trip only in the case where the initial guess found nothing, not on every query.
3. **Search Agent (`src/search_agent.py`)**: Interacts with Azure AI Search (`docsearchsrvc`) using `SearchClient`. Scopes queries server-side to the user's folder via a filterable, case-insensitive `folder_normalized` index field.
4. **Database Agent (`src/database_agent.py`)**: Queries a local SQLite `employees` table (structured org data: name, department, role, email, location) with a fixed, keyword-filtered `SELECT` — not LLM-generated SQL, to avoid a SQL-injection surface.
5. **Wiki Agent (`src/wiki_agent.py`)**: Retrieves from local markdown how-to/FAQ docs (`data/wiki/`), ranked by keyword overlap with the question (common stopwords excluded from scoring).
6. **Summarization Agent (`src/summarizer_agent.py`)**: Built with Microsoft Semantic Kernel. Uses `AzureChatCompletion` with prompt engineering to synthesize answers strictly from the retrieved excerpts, regardless of which source(s) they came from.
7. **Validation Agent (`src/validator_agent.py`)**: Built with Microsoft Semantic Kernel. Acts as an adversarial verification layer to check if the generated answer is strictly corroborated by the retrieved documents, preventing false claims.

---



## ⚙️ Prerequisites & Setup

### 1. Python Environment
Make sure Python 3.10+ is installed:
```bash
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Verify or create your `.env` file in the root directory:
```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_openai_endpint
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=your_api_version

# Azure AI Search
AZURE_SEARCH_ENDPOINT=your_search_endpoint
AZURE_SEARCH_API_KEY=your_azure_search_api_key
AZURE_SEARCH_INDEX_NAME=your_index_name
```

---

## 🚀 Running the Application

### Option A: Interactive Streamlit Web UI (Recommended)
Run the following command in your terminal:
```bash
streamlit run src/app.py
```
Open your browser at `http://localhost:8501`.

### Option B: Terminal / CLI Mode
```bash
python src/main.py
```
