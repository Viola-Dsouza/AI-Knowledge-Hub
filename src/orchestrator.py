import asyncio
from search_agent import SearchAgent
from summarizer_agent import SummarizerAgent
from validator_agent import ValidatorAgent


class KnowledgeOrchestrator:
    """
    Multi-Agent Orchestrator coordinating the execution pipeline:
    User Question -> Search Agent -> Summarization Agent -> Validation Agent -> Final Answer
    """

    def __init__(self):
        self.search_agent = SearchAgent()
        self.summarizer_agent = SummarizerAgent()
        self.validator_agent = ValidatorAgent()

    async def run(self, question: str, folder_name: str) -> dict:
        """
        Executes the full multi-agent workflow sequentially.
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
            }

        if not cleaned_question:
            return {
                "success": False,
                "error": "Please enter a question to ask.",
                "answer": "Question cannot be empty.",
                "validation": {"status": "NOT SUPPORTED", "reason": "No question provided."},
                "documents": [],
            }

        # Step 1: Search Agent
        documents = self.search_agent.search(cleaned_question, cleaned_folder)

        if not documents:
            return {
                "success": True,
                "answer": "Information not found in the provided documents.",
                "validation": {
                    "status": "NOT SUPPORTED",
                    "reason": f"No indexed documents found under folder '{cleaned_folder}'.",
                },
                "documents": [],
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
        }
