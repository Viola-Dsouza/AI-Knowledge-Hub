import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
)


class ValidatorAgent:
    """
    Validation Agent powered by Microsoft Semantic Kernel.
    Cross-checks the candidate answer against the retrieved documents to ensure
    factual grounding, prevent hallucinations, and verify source reliability.
    """

    def __init__(self):
        # Initialize Semantic Kernel
        self.kernel = sk.Kernel()

        # Add Azure OpenAI Chat Completion service
        chat_service = AzureChatCompletion(
            service_id="validator_chat",
            deployment_name=AZURE_OPENAI_DEPLOYMENT,
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
        )
        self.kernel.add_service(chat_service)

        # Register prompt-based Kernel Function for validation
        validation_prompt = """
You are the Validation Agent in an enterprise AI Knowledge Hub.

Your role is to rigorously check whether the Candidate Answer is fully supported by the Source Documents.

EVALUATION CRITERIA:
1. SUPPORTED: Every fact, statement, and claim in the Candidate Answer is directly backed by the Source Documents.
2. PARTIALLY SUPPORTED: Some facts in the Candidate Answer are backed by the Source Documents, but other statements lack direct evidence or make unverified assumptions.
3. NOT SUPPORTED: The Candidate Answer contains claims not found in the Source Documents, contradicts the documents, or states that information was not found.

User Question:
{{$question}}

Candidate Answer:
{{$answer}}

Source Documents:
{{$context}}

OUTPUT FORMAT:
Provide your response in EXACTLY the following two lines:
STATUS: <SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED>
REASON: <One clear sentence a general reader would understand, written in plain language.
Refer to "the answer" and "the source documents" — never use internal labels like
"Candidate Answer" or "Document 1".>
"""
        self.validate_func = self.kernel.add_function(
            prompt=validation_prompt,
            plugin_name="ValidationPlugins",
            function_name="ValidateAnswer",
        )

    async def validate(self, question: str, answer: str, documents: list[dict]) -> dict:
        """
        Validates the candidate answer against retrieved documents.
        Returns a dict with 'status' and 'reason'.
        """
        # If the answer explicitly states information was not found
        if not documents or "information not found" in answer.lower():
            return {
                "status": "NOT SUPPORTED",
                "reason": "Information was not available in the indexed documents for this folder.",
            }

        # Build context string
        context_parts = []
        for i, doc in enumerate(documents, start=1):
            context_parts.append(
                f"--- DOCUMENT {i}: {doc['file_name']} ---\n{doc['content']}\n"
            )
        full_context = "\n".join(context_parts)

        # Invoke Semantic Kernel function
        args = KernelArguments(
            question=question,
            answer=answer,
            context=full_context,
        )
        raw_result = str(await self.kernel.invoke(self.validate_func, args)).strip()

        status = "SUPPORTED"
        reason = "Answer is corroborated by internal source documents."

        for line in raw_result.splitlines():
            line_clean = line.strip()
            if line_clean.upper().startswith("STATUS:"):
                extracted_status = line_clean.split(":", 1)[1].strip().upper()
                if "PARTIALLY" in extracted_status:
                    status = "PARTIALLY SUPPORTED"
                elif "NOT SUPPORTED" in extracted_status or "UNSUPPORTED" in extracted_status:
                    status = "NOT SUPPORTED"
                elif "SUPPORTED" in extracted_status:
                    status = "SUPPORTED"
            elif line_clean.upper().startswith("REASON:"):
                reason = line_clean.split(":", 1)[1].strip()

        return {
            "status": status,
            "reason": reason,
            "raw": raw_result,
        }
