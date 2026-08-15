"""
Seeds data/knowledge_hub.db (the demo structured-data source for DatabaseAgent).

Run from the repo root: python data/seed_db.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_hub.db")

EMPLOYEES = [
    (1, "Viola Dsouza", "Engineering", "AI Intern", "viola@laratech.com", "Bengaluru"),
    (2, "Rakshitha Shetty", "IT", "IT Support Intern", "rakshitha@laratech.com", "Bengaluru"),
    (3, "Vaishali Rao", "HR", "HR Intern", "vaishali@laratech.com", "Mumbai"),
    (4, "Apoorva Nair", "Finance", "Finance Intern", "apoorva@laratech.com", "Mumbai"),
    (5, "Riyona Fernandes", "Engineering", "AI Intern", "riyona@laratech.com", "Bengaluru"),
    (6, "Adaline Pinto", "Marketing", "Marketing Intern", "adaline@laratech.com", "Pune"),
    (7, "Veeranagouda Patil", "Engineering", "AI Intern", "veeranagouda@laratech.com", "Bengaluru"),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS employees")
    cur.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)
    cur.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?)", EMPLOYEES)

    conn.commit()
    conn.close()
    print(f"Seeded {len(EMPLOYEES)} employees into {DB_PATH}")


if __name__ == "__main__":
    seed()
