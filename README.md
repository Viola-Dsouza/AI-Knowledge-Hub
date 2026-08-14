# 🧠 AI Knowledge Hub

An intelligent enterprise document search and knowledge management system built with **Microsoft Semantic Kernel**, **Azure AI Search**, and **Azure OpenAI (GPT-5 Mini)** with an interactive **Streamlit** user interface.

---

## 📌 Project Overview

Employees can ask natural language questions about company policies, documents, and internal knowledge. The system orchestrates multiple specialized AI agents to retrieve, synthesize, and validate information strictly grounded in internal documentation without hallucinations.

### 🌟 Key Features
- **Multi-Agent Orchestration**: Three specialized agents working in sequence (**Search Agent**, **Summarization Agent**, and **Validation Agent**).
- **Microsoft Semantic Kernel Powered**: Utilizes Semantic Kernel connectors and kernel functions for agent prompt engineering and execution.
- **Folder-Scoped Document Retrieval**: Dynamically filters internal documents within the shared Azure AI Search index based on the user's assigned folder (e.g. `internpdfs/viola/`).
- **Hallucination Prevention**: Returns *"Information not found in the provided documents."* with `NOT SUPPORTED` status if facts are not present in source documents.
- **Modern Streamlit UI**: Intuitive web interface with quick sample query chips, real-time agent execution pipeline indicators, validation badges, and source document viewers.

---

## 🏗️ Multi-Agent Architecture & Workflow

```
[ User Input in Streamlit UI ]
       │ (Question + Folder Name: e.g. "viola")
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. 🔍 Search Agent                                           │
│    - Connects to Azure AI Search index `internpdfindexes`   │
│    - Scopes queries strictly to `internpdfs/<folder_name>/` │
│    - Extracts top relevant document chunks & scores         │
└─────────────────────────────────────────────────────────────┘
       │ Retrieved Document Chunks
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 📝 Summarization Agent (Semantic Kernel)                 │
│    - Grounded strictly in retrieved source context          │
│    - Synthesizes clear, concise, professional answer        │
│    - Emits fallback if facts are missing                    │
└─────────────────────────────────────────────────────────────┘
       │ Candidate Answer + Source Context
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 🛡️ Validation Agent (Semantic Kernel)                    │
│    - Cross-examines candidate answer against source chunks  │
│    - Validates factual accuracy and eliminates hallucination│
│    - Classifies status: SUPPORTED / PARTIALLY / NOT         │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
[ Output: Formatted Answer + Validation Badge + Source Excerpts ]
```

### Agent Roles Explained
1. **Search Agent (`src/search_agent.py`)**: Interacts with Azure AI Search (`docsearchsrvc`) using `SearchClient`. Scans the shared index `internpdfindexes` and filters candidate documents matching the user's folder (`/internpdfs/<folder_name>/`).
2. **Summarization Agent (`src/summarizer_agent.py`)**: Built with Microsoft Semantic Kernel. Uses `AzureChatCompletion` with prompt engineering to synthesize answers strictly from the document excerpts.
3. **Validation Agent (`src/validator_agent.py`)**: Built with Microsoft Semantic Kernel. Acts as an adversarial verification layer to check if the generated answer is strictly corroborated by the retrieved documents, preventing false claims.

---

## 📁 Project Structure

```
AI-Knowledge-Hub/
│
├── .env                       # Environment credentials (API keys, endpoints)
├── .env.example               # Template environment file
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation and presentation guide
│
└── src/
    ├── __init__.py
    ├── config.py              # Configuration loader & validation helpers
    ├── search_agent.py        # Search Agent for Azure AI Search
    ├── summarizer_agent.py    # Summarization Agent (Semantic Kernel)
    ├── validator_agent.py     # Validation Agent (Semantic Kernel)
    ├── orchestrator.py        # Multi-Agent pipeline orchestrator
    ├── app.py                 # Streamlit web application
    └── main.py                # Terminal / CLI entry point
```

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
AZURE_OPENAI_ENDPOINT=https://agentic-training2026.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://docsearchsrvc.search.windows.net
AZURE_SEARCH_API_KEY=your_azure_search_api_key
AZURE_SEARCH_INDEX_NAME=internpdfindexes
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

---

## 🧪 Sample Questions to Test & Demonstrate

| Query Type | Sample Question | Expected Behavior |
| :--- | :--- | :--- |
| **Direct Fact** | *What is the company name?* | Retrieves `companypolicy.txt` $\rightarrow$ Answers `LARATECH CONSULTING SERVICES` $\rightarrow$ `SUPPORTED`. |
| **Policy Query** | *What is the work-from-home policy?* | Retrieves `leave_policy.pdf` & `companypolicy.txt` $\rightarrow$ Details core hours, VPN requirements, up to 2 days/week $\rightarrow$ `SUPPORTED`. |
| **Broad Summary** | *Summarize the documents* | Retrieves all documents under the folder $\rightarrow$ Provides structured summary of all 3 policies $\rightarrow$ `SUPPORTED`. |
| **Security Query** | *What are the password requirements?* | Retrieves `security_policy.pdf` $\rightarrow$ Details 14+ characters, MFA requirements $\rightarrow$ `SUPPORTED`. |
| **Out of Domain** | *What is the secret recipe for Coca-Cola?* | Answers *"Information not found in the provided documents."* $\rightarrow$ `NOT SUPPORTED`. |
