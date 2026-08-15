import os
import re
import sqlite3

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DATA_DIR, "knowledge_hub.db")
_WORD_RE = re.compile(r"[a-z0-9]+")


class DatabaseAgent:
    """
    Database Agent responsible for knowledge retrieval from the structured
    company database (SQLite demo: an `employees` table). Rows are returned
    as document-shaped dicts so downstream agents can treat them exactly
    like search/wiki results, regardless of source.

    This is intentionally a fixed, parameterized query rather than
    LLM-generated SQL — accepting free text into a SQL string would be a
    SQL-injection vector, and a fixed keyword-filtered SELECT is sufficient
    to demonstrate a working database connector.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        if not os.path.isfile(self.db_path):
            raise RuntimeError(
                f"{self.db_path} is missing. Run: python data/seed_db.py"
            )

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search(self, question: str, max_results: int = 10) -> list[dict]:
        """
        Returns employees whose name, department, or role match a keyword
        from the question, or the full directory for broad/listing queries.
        """
        query_text = question.strip().lower()

        is_broad = any(
            phrase in query_text
            for phrase in ["how many", "list all", "list of employees", "everyone", "all employees", "directory"]
        )

        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT id, name, department, role, email, location FROM employees ORDER BY name"
            ).fetchall()
        finally:
            conn.close()

        # Try keyword filtering first (e.g. a department/name/role/location
        # mentioned alongside "how many"), and only fall back to the full
        # directory for genuinely broad queries or when nothing matched —
        # otherwise a phrase like "how many" would always short-circuit to
        # the whole table even when the question names a specific department.
        keywords = [w for w in _WORD_RE.findall(query_text) if len(w) > 2]
        matched = [
            row for row in rows
            if any(
                kw in row["name"].lower()
                or kw in row["department"].lower()
                or kw in row["role"].lower()
                or kw in row["location"].lower()
                for kw in keywords
            )
        ]

        if matched:
            rows = matched
        elif not is_broad:
            rows = []

        documents = []
        for row in rows[:max_results]:
            content = (
                f"Name: {row['name']}\n"
                f"Department: {row['department']}\n"
                f"Role: {row['role']}\n"
                f"Email: {row['email']}\n"
                f"Location: {row['location']}"
            )
            documents.append({
                "file_name": f"employees.db#{row['id']}",
                "content": content,
                "path": self.db_path,
                "score": 1.0,
                "source": "database",
            })

        return documents
