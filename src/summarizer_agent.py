import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)


class SummarizerAgent:
    """
    Summarization Agent powered by Microsoft Semantic Kernel.
    Synthesizes answers strictly using retrieved document context.
    Prevents hallucination by falling back to 'Information not found in the provided documents.'
    """

    def __init__(self):
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()

        # Add Azure OpenAI Chat Completion service
        chat_service = AzureChatCompletion(
            service_id="summarizer_chat",
            deployment_name=AZURE_OPENAI_DEPLOYMENT,
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        self.kernel.add_service(chat_service)

        # Register prompt-based Kernel Function for summarization
        summarize_prompt = """
You are the Summarization Agent for an internal enterprise AI Knowledge Hub.

Your goal is to answer the user's question clearly and accurately using ONLY the provided document excerpts below.

STRICT RULES:
1. Rely exclusively on facts mentioned in the Document Context. Do NOT use external knowledge, guesses, or assumptions.
2. If the answer is NOT present in the Document Context, or if the documents are insufficient to answer the question, you MUST return EXACTLY:
Information not found in the provided documents.
3. If the answer is found, provide a well-structured, clear, and professional response.

User Question:
{{$question}}

Document Context:
{{$context}}
"""
        self.summarize_func = self.kernel.add_function(
            prompt=summarize_prompt,
            plugin_name="KnowledgePlugins",
            function_name="SummarizeKnowledge",
        )

    async def summarize(self, question: str, documents: list[dict]) -> str:
        """
        Summarizes the retrieved documents to answer the user's question.
        """
        if not documents:
            return "Information not found in the provided documents."

        # Format retrieved context with source attribution
        context_parts = []
        for i, doc in enumerate(documents, start=1):
            context_parts.append(
                f"--- DOCUMENT {i}: {doc['file_name']} ---\n{doc['content']}\n"
            )
        full_context = "\n".join(context_parts)

        # Invoke Semantic Kernel function
        args = KernelArguments(
            question=question,
            context=full_context,
        )
        result = await self.kernel.invoke(self.summarize_func, args)
        return str(result).strip()
