from urllib.parse import quote

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

    @staticmethod
    def _escape_odata_string(value: str) -> str:
        """Escapes single quotes for safe embedding inside an OData string literal."""
        return value.replace("'", "''")

    def search(self, question: str, folder_name: str, max_results: int = 5) -> list[dict]:
        """
        Retrieves the most relevant document chunks from Azure AI Search
        filtered by the specified folder name.

        Folder scoping is applied server-side via the `folder_normalized`
        field, populated at index time by the indexer's field mapping
        (metadata_storage_path -> folder_normalized, extractTokenAtPosition)
        and compared using Azure Search's built-in `lowercase` normalizer,
        so `eq` matches regardless of the folder's original casing in blob
        storage (e.g. "Viola" vs "viola"). Neither metadata_storage_path
        itself nor a plain `eq` on the unnormalized `folder` field can do
        this reliably — `search.ismatch`/`$filter` aren't supported on
        metadata_storage_path (not filterable/searchable on this index),
        and Azure Search's $filter grammar has no `tolower()` function to
        normalize case at query time.

        A small number of legacy index documents (indexed before this field
        existed, whose source blobs are no longer enumerable by the indexer)
        have folder_normalized = null and are intentionally excluded here
        rather than special-cased into the filter — that's a data-hygiene
        gap in the shared index, not something to paper over per-query.
        """
        if not folder_name or not folder_name.strip():
            return []

        # URL-encode after lowercasing so folder names containing spaces
        # (e.g. "Rakshitha Shetty") match the URL-encoded blob path segment
        # (".../Rakshitha%20Shetty/...") that both index fields are derived from.
        folder_name_clean = quote(folder_name.strip().lower())
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
        limit = 20 if is_broad_summary else max_results

        odata_folder = self._escape_odata_string(folder_name_clean)
        filter_expr = f"folder_normalized eq '{odata_folder}'"

        results = client.search(
            search_text=search_query,
            filter=filter_expr,
            top=limit,
            select=["content", "metadata_storage_name", "metadata_storage_path", "folder_normalized"],
        )

        documents = []
        for item in results:
            path = item.get("metadata_storage_path", "")
            # Cheap correctness backstop; the server-side filter above is
            # exact, so this should never actually exclude anything.
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
                "source": "documents",
            })

        # Sort documents by relevance score descending
        documents.sort(key=lambda x: x["score"], reverse=True)

        return documents[:limit]
