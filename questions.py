import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "questions.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                topic TEXT NOT NULL,
                question TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def add_question(student_name, topic, question):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO questions (
                student_name,
                topic,
                question,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                student_name,
                topic,
                question,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )


def get_questions():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            SELECT id, student_name, topic, question, created_at
            FROM questions
            ORDER BY id DESC
            """
        )

        return cursor.fetchall()