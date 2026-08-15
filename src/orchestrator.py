import asyncio
from database_agent import DatabaseAgent
from query_router import QueryRouter
from search_agent import SearchAgent
from summarizer_agent import SummarizerAgent
from validator_agent import ValidatorAgent
from wiki_agent import WikiAgent


ALL_SOURCES = ("documents", "database", "wiki")


class KnowledgeOrchestrator:
    """
    Multi-Agent Orchestrator coordinating the execution pipeline:
    User Question -> Query Router -> Source Agent(s) -> Summarization Agent -> Validation Agent -> Final Answer

    The Query Router selects which source(s) a question needs (documents /
    database / wiki) before any retrieval happens, so most questions only
    pay the latency of the one connector that's actually relevant instead
    of always fanning out to every source.

    If the router's pick comes back with nothing, the remaining source(s)
    are queried as a fallback before giving up — this keeps the speed win
    for the common case (one retrieval round-trip) while still catching
    the case where the router's keyword guess missed the source that
    actually has the answer.
    """

    def __init__(self):
        self.router = QueryRouter()
        self.search_agent = SearchAgent()
        self.database_agent = DatabaseAgent()
        self.wiki_agent = WikiAgent()
        self.summarizer_agent = SummarizerAgent()
        self.validator_agent = ValidatorAgent()

    def _query_sources(self, source_names: list[str], question: str, folder_name: str) -> list[dict]:
        """Runs the given source agent(s) and merges their results into one document list."""
        documents: list[dict] = []
        if "documents" in source_names:
            documents.extend(self.search_agent.search(question, folder_name))
        if "database" in source_names:
            documents.extend(self.database_agent.search(question))
        if "wiki" in source_names:
            documents.extend(self.wiki_agent.search(question))
        return documents

    def _retrieve(self, question: str, folder_name: str) -> tuple[list[dict], list[str], list[str]]:
        """
        Routes to the primary source(s), then falls back to the remaining
        source(s) only if the primary pick returned nothing.

        Returns (documents, primary_sources, fallback_sources) — kept
        separate rather than merged into one list so callers (e.g. the UI)
        can show what the router actually chose versus what expansion
        added, instead of it looking like the router picked everything.
        """
        primary_sources = self.router.classify(question)
        documents = self._query_sources(primary_sources, question, folder_name)
        fallback_sources: list[str] = []

        if not documents:
            fallback_sources = [s for s in ALL_SOURCES if s not in primary_sources]
            if fallback_sources:
                documents.extend(self._query_sources(fallback_sources, question, folder_name))

        return documents, primary_sources, fallback_sources

    async def run(self, question: str, folder_name: str) -> dict:
        """
        Executes the full multi-agent workflow: route, retrieve, summarize, validate.
        """
        cleaned_question = question.strip()
        cleaned_folder = folder_name.strip()

        if not cleaned_folder:
            return {
                "success": False,
                "error": "Please specify a folder name (e.g., 'viola').",
                "answer": "Folder name is required to retrieve documents.",
                "validation": {"status": "NOT SUPPORTED", "reason": "No folder specified."},
                "documents": [],
                "primary_sources": [],
                "fallback_sources": [],
            }

        if not cleaned_question:
            return {
                "success": False,
                "error": "Please enter a question to ask.",
                "answer": "Question cannot be empty.",
                "validation": {"status": "NOT SUPPORTED", "reason": "No question provided."},
                "documents": [],
                "primary_sources": [],
                "fallback_sources": [],
            }

        # Step 1: Query Router + source agent(s), with fallback expansion
        documents, primary_sources, fallback_sources = self._retrieve(cleaned_question, cleaned_folder)
        sources_queried = primary_sources + fallback_sources

        if not documents:
            return {
                "success": True,
                "answer": "Information not found in the provided documents.",
                "validation": {
                    "status": "NOT SUPPORTED",
                    "reason": f"No matching content found in the queried source(s): {', '.join(sources_queried)}.",
                },
                "documents": [],
                "primary_sources": primary_sources,
                "fallback_sources": fallback_sources,
            }

        # Step 2: Summarization Agent
        answer = await self.summarizer_agent.summarize(cleaned_question, documents)

        # Step 3: Validation Agent
        validation = await self.validator_agent.validate(cleaned_question, answer, documents)

        return {
            "success": True,
            "answer": answer,
            "validation": validation,
            "documents": documents,
            "primary_sources": primary_sources,
            "fallback_sources": fallback_sources,
        }
