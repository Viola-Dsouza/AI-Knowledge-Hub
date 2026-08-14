from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_API_KEY,
    AZURE_SEARCH_INDEX_NAME,
)


class SearchAgent:
    """
    Search Agent responsible for knowledge retrieval from Azure AI Search.
    Filters and scopes search results strictly to the designated user folder
    under the shared storage path: internpdfs/<folder_name>/
    """

    def __init__(self):
        self.endpoint = AZURE_SEARCH_ENDPOINT
        self.api_key = AZURE_SEARCH_API_KEY
        self.index_name = AZURE_SEARCH_INDEX_NAME

    def _get_client(self) -> SearchClient:
        return SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.api_key),
        )

    def search(self, question: str, folder_name: str, max_results: int = 5) -> list[dict]:
        """
        Retrieves the most relevant document chunks from Azure AI Search
        filtered by the specified folder name.
        """
        if not folder_name or not folder_name.strip():
            return []

        folder_name_clean = folder_name.strip().lower()
        folder_pattern = f"/internpdfs/{folder_name_clean}/"

        client = self._get_client()
        query_text = question.strip()

        # Check if user asks for a broad summary or all documents
        is_broad_summary = any(
            phrase in query_text.lower()
            for phrase in [
                "summarize all",
                "summarise all",
                "all documents",
                "overview of all",
                "summarize the documents",
                "summarise the documents",
                "list all",
                "everything",
            ]
        )

        search_query = "*" if (is_broad_summary or not query_text) else query_text

        # Fetch up to 100 results from shared index to ensure candidate pool
        # includes documents belonging to the user's specific folder
        results = client.search(
            search_text=search_query,
            top=100,
            select=["content", "metadata_storage_name", "metadata_storage_path"],
        )

        documents = []
        for item in results:
            path = item.get("metadata_storage_path", "")
            # Filter strictly by the user's folder path
            if folder_pattern not in path.lower():
                continue

            content = item.get("content", "").strip()
            if not content:
                continue

            documents.append({
                "file_name": item.get("metadata_storage_name", "Unknown Document"),
                "content": content,
                "path": path,
                "score": float(item.get("@search.score", 0.0)),
            })

        # Sort documents by relevance score descending
        documents.sort(key=lambda x: x["score"], reverse=True)

        # Return up to max_results for specific questions, or up to 20 for broad summary
        limit = 20 if is_broad_summary else max_results
        return documents[:limit]
