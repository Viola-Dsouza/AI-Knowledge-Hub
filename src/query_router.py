DATABASE_KEYWORDS = [
    "employee", "employees", "staff", "intern", "interns", "department",
    "team member", "directory", "headcount", "how many people", "who is",
    "who works", "contact for", "email of", "location of", "org chart",
]

WIKI_KEYWORDS = [
    "how do i", "how to", "steps to", "step by step", "process for",
    "guide", "faq", "onboarding", "reimbursement", "expense", "vpn",
    "reset my password", "laptop", "it support", "new hire", "checklist",
]


class QueryRouter:
    """
    Decides which source(s) a question needs before querying anything.

    This is the "balance speed vs. accuracy/relevance" piece of the
    orchestration workflow: querying every source for every question is
    the most thorough option but pays every connector's latency on every
    request. Routing narrows to the source(s) actually implicated by the
    question's wording, so most questions only pay for one connector.

    Classification is a cheap keyword match rather than an extra LLM call —
    an LLM-based router would add real accuracy for ambiguous phrasing, but
    also adds a full model round-trip to every single query before any
    retrieval even starts, which works against the "speed" side of the
    tradeoff this router exists to make. If a question matches no source's
    keywords, routing falls back to the documents source (the original,
    most general-purpose source) rather than guessing narrowly.

    This class only picks the *primary* source(s) — it doesn't decide
    whether to expand beyond them. That's KnowledgeOrchestrator._retrieve's
    job: if the primary source(s) picked here come back with zero results,
    the orchestrator queries the remaining source(s) as a fallback before
    giving up, so a wrong/narrow keyword guess here doesn't necessarily
    mean nothing gets found. That fallback only triggers on a genuinely
    empty result, though — a single weak keyword-overlap match (e.g. a
    wiki doc matching only because its title shares one word with the
    question) still counts as "found something" and won't trigger
    expansion, so classification can still steer to a paper-thin match.
    """

    @staticmethod
    def classify(question: str) -> list[str]:
        query_text = question.strip().lower()

        sources = []
        if any(kw in query_text for kw in DATABASE_KEYWORDS):
            sources.append("database")
        if any(kw in query_text for kw in WIKI_KEYWORDS):
            sources.append("wiki")

        # "documents" (Azure AI Search over policy PDFs) is the default,
        # general-purpose source: included whenever nothing more specific
        # matched, and also whenever the question sounds like a policy
        # question even alongside a database/wiki match (e.g. "what is the
        # leave policy and who is my HR contact" needs both).
        if not sources or "policy" in query_text or "polic" in query_text:
            sources.append("documents")

        return sources
