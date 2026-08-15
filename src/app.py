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
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --bg: #000000;
        --surface: #1c1c1e;
        --surface-elevated: #2c2c2e;
        --border: rgba(255, 255, 255, 0.08);
        --border-strong: rgba(255, 255, 255, 0.16);
        --text-primary: #f5f5f7;
        --text-secondary: #86868b;
        --accent: #0071e3;
        --accent-hover: #147ce5;
        --success: #30d158;
        --warning: #ff9f0a;
        --danger: #ff453a;
        --radius-md: 12px;
        --radius-sm: 8px;
        --ease: cubic-bezier(0.28, 0.11, 0.32, 1);
    }

    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @media (prefers-reduced-motion: reduce) {
        * { animation: none !important; transition: none !important; }
    }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: var(--bg) !important;
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text",
            "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    [data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

    .stMainBlockContainer {
        max-width: 800px !important;
        padding-top: 3.5rem;
        padding-bottom: 4rem;
    }

    a, a:visited { color: var(--accent); }

    :focus-visible {
        outline: 2px solid var(--accent) !important;
        outline-offset: 2px;
    }

    hr { border-color: var(--border) !important; margin: 1.25rem 0 !important; }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebarContent"] { padding-top: 1.5rem; }

    .brand-name {
        font-size: 1.0625rem;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--text-primary);
        margin: 0 0 6px 0;
    }
    .brand-desc {
        font-size: 0.8125rem;
        color: var(--text-secondary);
        line-height: 1.5;
        margin: 0;
    }

    .eyebrow {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin: 0 0 10px 0;
        letter-spacing: 0.01em;
    }

    /* Sample-question rows: quiet list, not colorful chips */
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        border-bottom: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        font-weight: 400 !important;
        font-size: 0.8125rem !important;
        text-align: left;
        justify-content: flex-start !important;
        padding: 0.6rem 0.35rem !important;
        transition: background 0.15s var(--ease);
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
        background: var(--surface-elevated) !important;
        color: var(--text-primary) !important;
        border-color: var(--border) !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
        color: inherit !important;
        font-size: inherit !important;
        text-align: left !important;
    }

    .status-row {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.8125rem;
        color: var(--text-primary);
        padding: 8px 0;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .status-dot.ok { background: var(--success); box-shadow: 0 0 0 3px rgba(48, 209, 88, 0.16); }
    .status-dot.bad { background: var(--danger); box-shadow: 0 0 0 3px rgba(255, 69, 58, 0.16); }
    .status-dot.partial { background: var(--warning); box-shadow: 0 0 0 3px rgba(255, 159, 10, 0.16); }

    /* ---------- Text input & buttons (global) ---------- */
    .stTextInput input {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-size: 0.9375rem !important;
        padding: 0.625rem 0.875rem !important;
        transition: border-color 0.2s var(--ease), box-shadow 0.2s var(--ease);
    }
    .stTextInput input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.15) !important;
    }
    .stTextInput input::placeholder { color: var(--text-secondary) !important; }
    .stTextInput label { color: var(--text-secondary) !important; font-size: 0.8125rem !important; }

    [data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
        background: var(--accent) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 0.9375rem !important;
        padding: 0.625rem 1.25rem !important;
        transition: background 0.2s var(--ease), transform 0.08s var(--ease);
        box-shadow: none !important;
    }
    [data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primaryFormSubmit"] p {
        color: #ffffff !important;
        font-weight: 500 !important;
    }
    [data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {
        background: var(--accent-hover) !important;
    }
    [data-testid="stBaseButton-primary"]:active, [data-testid="stBaseButton-primaryFormSubmit"]:active {
        transform: scale(0.98);
    }

    /* ---------- Notices (replace default alert styling) ---------- */
    .notice {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--text-secondary);
        border-radius: var(--radius-sm);
        padding: 0.875rem 1rem;
        font-size: 0.875rem;
        color: var(--text-primary);
        line-height: 1.5;
        margin: 0.75rem 0;
    }
    .notice.warning { border-left-color: var(--warning); }
    .notice.error { border-left-color: var(--danger); }
    .notice.info { border-left-color: var(--accent); }

    /* ---------- Hero ---------- */
    .hero-title {
        font-size: 2rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        margin: 0;
    }
    .hero-subtitle {
        font-size: 1.0625rem;
        color: var(--text-secondary);
        line-height: 1.47;
        margin: 8px 0 0 0;
        max-width: 640px;
    }

    /* ---------- Pipeline stepper (static, informational) ---------- */
    .stepper {
        display: flex;
        flex-wrap: wrap;
        gap: 20px 24px;
        margin: 36px 0 40px 0;
    }
    .step {
        flex: 1 1 160px;
        min-width: 160px;
        opacity: 0;
        animation: fadeSlideIn 0.5s var(--ease) forwards;
    }
    .step:nth-child(1) { animation-delay: 0.05s; }
    .step:nth-child(2) { animation-delay: 0.12s; }
    .step:nth-child(3) { animation-delay: 0.19s; }
    .step:nth-child(4) { animation-delay: 0.26s; }
    .step-marker {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 1.5px solid var(--border-strong);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--text-secondary);
        margin-bottom: 12px;
    }
    .step-title {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    .step-desc {
        font-size: 0.75rem;
        color: var(--text-secondary);
        line-height: 1.45;
    }

    /* ---------- Route trace ---------- */
    .route-trace {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
        font-size: 0.8125rem;
        color: var(--text-secondary);
        margin-bottom: 14px;
        opacity: 0;
        animation: fadeSlideIn 0.45s var(--ease) forwards;
    }
    .route-source {
        color: var(--accent);
        font-weight: 500;
    }

    /* ---------- Answer card ---------- */
    /* Targets Streamlit's native st.container(border=True) so the answer
       renders through real markdown (lists, bold, etc.) instead of being
       dumped as a raw string into an HTML div, which left literal "- "
       bullets and other markdown syntax visible in the rendered text. */
    [data-testid="stVerticalBlockBorderWrapper"]:has(.answer-card-marker) {
        background: var(--surface);
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        margin-bottom: 1.25rem;
        opacity: 0;
        animation: fadeSlideIn 0.5s var(--ease) forwards;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.answer-card-marker) [data-testid="stMarkdownContainer"] {
        color: var(--text-primary);
        font-size: 1.0625rem;
        line-height: 1.55;
    }
    .answer-card-marker { display: none; }

    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary);
        letter-spacing: 0.01em;
        margin: 2rem 0 0.75rem 0;
        padding-top: 1.25rem;
        border-top: 1px solid var(--border);
    }
    .section-label.first { padding-top: 0; border-top: none; }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.9375rem;
        font-weight: 500;
        color: var(--text-primary);
    }

    /* ---------- Source expanders ---------- */
    [data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        margin-bottom: 8px;
    }
    [data-testid="stExpander"] summary {
        color: var(--text-primary) !important;
        font-size: 0.875rem !important;
    }
    [data-testid="stExpander"] p, [data-testid="stExpander"] span {
        color: var(--text-secondary);
    }

    [data-testid="stSpinner"] { color: var(--text-secondary) !important; }
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


def notice(message: str, kind: str = "info") -> None:
    st.markdown(f'<div class="notice {kind}">{message}</div>', unsafe_allow_html=True)


# Validate environment
is_config_valid, missing_keys = validate_config()

# ---------------------------------------------------------
# SIDEBAR: CONFIGURATION & SAMPLE PROMPTS
# ---------------------------------------------------------
with st.sidebar:
    st.markdown('<p class="brand-name">AI Knowledge Hub</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="brand-desc">A Semantic Kernel multi-agent system connected to Azure AI Search and Azure OpenAI.</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<p class="eyebrow">Knowledge scope</p>', unsafe_allow_html=True)
    folder_input = st.text_input(
        "Folder name",
        value="viola",
        help="Retrieves documents stored under internpdfs/<folder_name>/",
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown('<p class="eyebrow">Sample questions</p>', unsafe_allow_html=True)
    sample_queries = [
        "What is the company name?",
        "What is the work-from-home policy?",
        "Summarize the documents",
        "What are the security guidelines?",
        "How many employees are in the Engineering department?",
        "How do I reset my password?",
        "What is the secret recipe for Coca-Cola?",
    ]

    for sample in sample_queries:
        if st.button(sample, use_container_width=True):
            st.session_state["question_text"] = sample

    st.divider()

    st.markdown('<p class="eyebrow">System status</p>', unsafe_allow_html=True)
    if is_config_valid:
        st.markdown(
            '<div class="status-row"><span class="status-dot ok"></span>Azure services connected</div>',
            unsafe_allow_html=True,
        )
        with st.expander("Connected endpoints"):
            st.caption(f"OpenAI model: {AZURE_OPENAI_DEPLOYMENT}")
            st.caption(f"OpenAI endpoint: {AZURE_OPENAI_ENDPOINT}")
            st.caption(f"Search index: {AZURE_SEARCH_INDEX_NAME}")
            st.caption(f"Search service: {AZURE_SEARCH_ENDPOINT}")
    else:
        st.markdown(
            f'<div class="status-row"><span class="status-dot bad"></span>Missing config: {", ".join(missing_keys)}</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------
# MAIN INTERFACE
# ---------------------------------------------------------
st.markdown(
    """
    <h1 class="hero-title">AI Knowledge Hub</h1>
    <p class="hero-subtitle">Ask a question in plain language. Every answer is checked against your
    team's documents, employee directory, and internal guides before it reaches you.</p>
    """,
    unsafe_allow_html=True,
)

# Pipeline overview — a genuine sequential process, so the numbering carries
# real meaning rather than decorating four unrelated feature callouts.
st.markdown(
    """
    <div class="stepper">
        <div class="step">
            <div class="step-marker">1</div>
            <div class="step-title">Route</div>
            <div class="step-desc">Decides which source this question needs.</div>
        </div>
        <div class="step">
            <div class="step-marker">2</div>
            <div class="step-title">Retrieve</div>
            <div class="step-desc">Pulls matching content from documents, the employee directory, or internal guides.</div>
        </div>
        <div class="step">
            <div class="step-marker">3</div>
            <div class="step-title">Summarize</div>
            <div class="step-desc">Writes an answer using only what was retrieved.</div>
        </div>
        <div class="step">
            <div class="step-marker">4</div>
            <div class="step-title">Validate</div>
            <div class="step-desc">Checks the answer against the source before you see it.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not is_config_valid:
    notice(
        f"Application configuration is incomplete. Check your <code>.env</code> file. Missing keys: {', '.join(missing_keys)}",
        kind="error",
    )
    st.stop()

# Query Input Form
default_q = st.session_state.get("question_text", "")
with st.form(key="ask_form"):
    user_question = st.text_input(
        "Question",
        value=default_q,
        placeholder="What is the company's work-from-home policy?",
        label_visibility="collapsed",
    )
    col_btn, col_empty = st.columns([2, 8])
    with col_btn:
        submit_button = st.form_submit_button("Ask", type="primary", use_container_width=True)

# ---------------------------------------------------------
# EXECUTION & RESULTS
# ---------------------------------------------------------
if submit_button:
    if not folder_input.strip():
        notice("Enter a folder name in the sidebar (e.g. \"viola\").", kind="warning")
    elif not user_question.strip():
        notice("Enter a question.", kind="warning")
    else:
        orchestrator = get_orchestrator()

        with st.spinner("Running the multi-agent pipeline…"):
            try:
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
                primary_sources = result.get("primary_sources", [])
                fallback_sources = result.get("fallback_sources", [])

                # ---------------------------------------------
                # 1. ANSWER SECTION
                # ---------------------------------------------
                st.markdown('<p class="section-label first">Answer</p>', unsafe_allow_html=True)

                if primary_sources:
                    trace_parts = [
                        f'<span class="route-source">{s.capitalize()}</span>' for s in primary_sources
                    ]
                    trace_html = f'Routed to {", ".join(trace_parts)}'
                    if fallback_sources:
                        fallback_parts = [
                            f'<span class="route-source">{s.capitalize()}</span>' for s in fallback_sources
                        ]
                        trace_html += f' — found nothing, expanded to {", ".join(fallback_parts)}'
                    st.markdown(f'<div class="route-trace">{trace_html}</div>', unsafe_allow_html=True)

                with st.container(border=True):
                    st.markdown('<span class="answer-card-marker"></span>', unsafe_allow_html=True)
                    st.markdown(answer)

                # ---------------------------------------------
                # 2. VALIDATION SECTION
                # ---------------------------------------------
                st.markdown('<p class="section-label">Validation</p>', unsafe_allow_html=True)

                status_map = {
                    "SUPPORTED": ("ok", "Supported"),
                    "PARTIALLY SUPPORTED": ("partial", "Partially supported"),
                }
                dot_class, status_label = status_map.get(status, ("bad", "Not supported"))
                st.markdown(
                    f'<div class="status-indicator"><span class="status-dot {dot_class}"></span>{status_label}</div>',
                    unsafe_allow_html=True,
                )
                notice(reason, kind="info")

                # ---------------------------------------------
                # 3. SOURCE DOCUMENTS SECTION
                # ---------------------------------------------
                st.markdown('<p class="section-label">Sources</p>', unsafe_allow_html=True)
                if not documents:
                    st.caption("No source documents matched this query or folder.")
                else:
                    st.caption(f"{len(documents)} excerpt(s) retrieved from folder “{folder_input}”")
                    for doc in documents:
                        source_label = doc.get("source", "documents").capitalize()
                        with st.expander(f"{doc['file_name']}  ·  {source_label}  ·  {doc['score']:.2f}"):
                            st.caption(f"Location: {doc['path']}")
                            st.text(doc["content"])

            except Exception as ex:
                notice(f"An error occurred during pipeline execution: {str(ex)}", kind="error")
