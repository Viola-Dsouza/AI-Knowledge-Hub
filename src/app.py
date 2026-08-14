import asyncio
import streamlit as st

from config import (
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_INDEX_NAME,
    validate_config,
)
from orchestrator import KnowledgeOrchestrator

# ---------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Knowledge Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern enterprise styling
st.markdown(
    """
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 24px;
        color: #F8FAFC;
    }
    .header-card h1 {
        color: #38BDF8;
        margin: 0 0 8px 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .header-card p {
        color: #94A3B8;
        margin: 0;
        font-size: 0.95rem;
    }
    
    /* Agent Flow Pipeline Container */
    .agent-pipeline {
        display: flex;
        gap: 12px;
        margin: 16px 0 24px 0;
        flex-wrap: wrap;
    }
    .agent-step {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #E2E8F0;
        flex: 1;
        min-width: 180px;
    }
    .agent-step strong {
        color: #38BDF8;
        display: block;
        margin-bottom: 4px;
    }

    /* Validation Status Badges */
    .badge-supported {
        display: inline-block;
        background-color: #064E3B;
        color: #6EE7B7;
        border: 1px solid #059669;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .badge-partial {
        display: inline-block;
        background-color: #78350F;
        color: #FCD34D;
        border: 1px solid #D97706;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .badge-unsupported {
        display: inline-block;
        background-color: #7F1D1D;
        color: #FCA5A5;
        border: 1px solid #DC2626;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* Answer card */
    .answer-card {
        background-color: #0F172A;
        border: 1px solid #334155;
        border-left: 4px solid #38BDF8;
        border-radius: 8px;
        padding: 20px;
        margin-top: 12px;
        margin-bottom: 20px;
        color: #F1F5F9;
        font-size: 1rem;
        line-height: 1.6;
    }

    /* Source Item */
    .source-box {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# INITIALIZATION & STATE
# ---------------------------------------------------------
@st.cache_resource
def get_orchestrator():
    return KnowledgeOrchestrator()


# Validate environment
is_config_valid, missing_keys = validate_config()

# ---------------------------------------------------------
# SIDEBAR: CONFIGURATION & SAMPLE PROMPTS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏢 AI Knowledge Hub")
    st.markdown(
        "Semantic Kernel multi-agent system connected to **Azure AI Search** & **Azure OpenAI**."
    )
    st.divider()

    st.markdown("#### 📁 Knowledge Scope")
    folder_input = st.text_input(
        "User Folder Name",
        value="viola",
        help="Retrieves documents stored under internpdfs/<folder_name>/",
    )

    st.divider()

    st.markdown("#### 💡 Quick Sample Questions")
    sample_queries = [
        "What is the company name?",
        "What is the work-from-home policy?",
        "Summarize the documents",
        "What are the security guidelines?",
        "What is the secret recipe for Coca-Cola?",
    ]

    for sample in sample_queries:
        if st.button(f"👉 {sample}", use_container_width=True):
            st.session_state["question_text"] = sample

    st.divider()

    st.markdown("#### ⚙️ System Status")
    if is_config_valid:
        st.success("🟢 Azure Services Connected", icon="✅")
        with st.expander("Connected Endpoints"):
            st.caption(f"**OpenAI Model:** {AZURE_OPENAI_DEPLOYMENT}")
            st.caption(f"**OpenAI Endpoint:** {AZURE_OPENAI_ENDPOINT}")
            st.caption(f"**Search Index:** {AZURE_SEARCH_INDEX_NAME}")
            st.caption(f"**Search Service:** {AZURE_SEARCH_ENDPOINT}")
    else:
        st.error(f"🔴 Missing Config: {', '.join(missing_keys)}", icon="⚠️")

# ---------------------------------------------------------
# MAIN INTERFACE
# ---------------------------------------------------------
st.markdown(
    """
    <div class="header-card">
        <h1>🧠 Enterprise AI Knowledge Hub</h1>
        <p>Ask questions in natural language and receive grounded, validated answers from your organizational documents.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Multi-Agent Workflow Diagram
st.markdown(
    """
    <div class="agent-pipeline">
        <div class="agent-step">
            <strong>1. 🔍 Search Agent</strong>
            Retrieves relevant chunks from Azure AI Search index filtered by user folder.
        </div>
        <div class="agent-step">
            <strong>2. 📝 Summarization Agent</strong>
            Semantic Kernel agent synthesizes answer strictly from retrieved text.
        </div>
        <div class="agent-step">
            <strong>3. 🛡️ Validation Agent</strong>
            Verifies answer against source documents to eliminate hallucinations.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_config_valid:
    st.error(
        f"⚠️ Application configuration is incomplete. Please check your `.env` file. Missing keys: {missing_keys}"
    )
    st.stop()

# Query Input Form
default_q = st.session_state.get("question_text", "")
with st.form(key="ask_form"):
    user_question = st.text_input(
        "Enter your question:",
        value=default_q,
        placeholder="e.g., What is the company's work-from-home policy?",
    )
    col_btn, col_empty = st.columns([2, 8])
    with col_btn:
        submit_button = st.form_submit_button("🔍 Ask Knowledge Hub", type="primary", use_container_width=True)

# ---------------------------------------------------------
# EXECUTION & RESULTS
# ---------------------------------------------------------
if submit_button:
    if not folder_input.strip():
        st.warning("⚠️ Please provide a folder name in the sidebar (e.g., 'viola').")
    elif not user_question.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        orchestrator = get_orchestrator()

        with st.spinner("🤖 Multi-Agent Orchestration in progress..."):
            try:
                # Run the asynchronous multi-agent pipeline
                result = asyncio.run(
                    orchestrator.run(
                        question=user_question,
                        folder_name=folder_input,
                    )
                )

                answer = result.get("answer", "")
                validation = result.get("validation", {})
                status = validation.get("status", "NOT SUPPORTED")
                reason = validation.get("reason", "")
                documents = result.get("documents", [])

                # ---------------------------------------------
                # 1. ANSWER SECTION
                # ---------------------------------------------
                st.markdown("### 💬 Generated Answer")
                st.markdown(
                    f"""
                    <div class="answer-card">
                        {answer}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # ---------------------------------------------
                # 2. VALIDATION SECTION
                # ---------------------------------------------
                st.markdown("### 🛡️ Agent Validation")
                col_badge, col_reason = st.columns([1, 3])

                with col_badge:
                    if status == "SUPPORTED":
                        st.markdown(
                            '<div class="badge-supported">✅ SUPPORTED</div>',
                            unsafe_allow_html=True,
                        )
                    elif status == "PARTIALLY SUPPORTED":
                        st.markdown(
                            '<div class="badge-partial">⚠️ PARTIALLY SUPPORTED</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div class="badge-unsupported">❌ NOT SUPPORTED</div>',
                            unsafe_allow_html=True,
                        )

                with col_reason:
                    st.info(f"**Validation Verdict:** {reason}")

                # ---------------------------------------------
                # 3. SOURCE DOCUMENTS SECTION
                # ---------------------------------------------
                st.markdown("### 📄 Source Documents")
                if not documents:
                    st.caption("No internal source documents matched this query or folder.")
                else:
                    st.caption(f"Retrieved **{len(documents)}** relevant document excerpt(s) from folder `{folder_input}`:")
                    for i, doc in enumerate(documents, start=1):
                        with st.expander(f"📄 [{i}] {doc['file_name']} (Relevance Score: {doc['score']:.2f})"):
                            st.caption(f"**Storage Path:** `{doc['path']}`")
                            st.markdown("**Content Excerpt:**")
                            st.text(doc["content"])

            except Exception as ex:
                st.error(f"❌ An error occurred during pipeline execution: {str(ex)}")
