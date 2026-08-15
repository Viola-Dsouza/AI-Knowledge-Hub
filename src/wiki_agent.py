import os
import re

WIKI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "wiki")

_WORD_RE = re.compile(r"[a-z0-9]+")

# Common English function words excluded from overlap scoring — without
# this, every document "matches" any question purely by sharing words like
# "for" or "the", so overlap > 0 never actually means zero relevant results.
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "for", "of", "on", "in", "to", "and", "or", "but", "with", "at", "by",
    "from", "up", "about", "into", "over", "after", "i", "you", "your",
    "my", "me", "it", "its", "this", "that", "do", "does", "did", "how",
    "what", "who", "when", "where", "why", "can", "will", "would", "should",
    "if", "not", "no", "so", "as", "we", "our", "us",
}


class WikiAgent:
    """
    Wiki Agent responsible for knowledge retrieval from internal process
    documentation (markdown files under data/wiki/) — how-to guides and
    FAQs, distinct in kind from the formal policy PDFs served by SearchAgent.

    Relevance is scored by simple keyword overlap between the question and
    each document, which is enough to rank a handful of local markdown
    files without needing an external search index for this source.
    """

    def __init__(self, wiki_dir: str = WIKI_DIR):
        self.wiki_dir = wiki_dir

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(_WORD_RE.findall(text.lower())) - _STOPWORDS

    def search(self, question: str, max_results: int = 3) -> list[dict]:
        if not os.path.isdir(self.wiki_dir):
            return []

        query_tokens = self._tokenize(question)

        scored = []
        for filename in sorted(os.listdir(self.wiki_dir)):
            if not filename.endswith(".md"):
                continue

            file_path = os.path.join(self.wiki_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            doc_tokens = self._tokenize(content) | self._tokenize(filename)
            overlap = len(query_tokens & doc_tokens)

            if overlap > 0:
                scored.append({
                    "file_name": filename,
                    "content": content.strip(),
                    "path": file_path,
                    "score": float(overlap),
                    "source": "wiki",
                })

        scored.sort(key=lambda d: d["score"], reverse=True)
        return scored[:max_results]
