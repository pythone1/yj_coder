"""
项目名称: llm-chatbot
技术领域: 03-llm-agents
模块说明: session_store.py - 核心业务算法实现
作者: 杨佳 (资深 AI 算法与遥感工程师)
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from app.core.config import get_settings


class SessionStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.db_path = Path(settings.app_data_dir) / "chat_sessions.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (session_id) REFERENCES sessions (id)
                )
                """
            )

            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
            }
            if "user_id" not in columns:
                connection.execute("ALTER TABLE sessions ADD COLUMN user_id TEXT")

    def create_session(self, user_id: str, title: str = "新对话") -> dict:
        session_id = uuid.uuid4().hex
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO sessions (id, user_id, title) VALUES (?, ?, ?)",
                (session_id, user_id, title),
            )
            row = connection.execute(
                "SELECT id, title, created_at, updated_at FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return dict(row)

    def ensure_session(self, user_id: str, session_id: str | None, fallback_title: str) -> dict:
        if session_id:
            session = self.get_session(user_id, session_id)
            if session:
                return session
        return self.create_session(user_id, self._build_title(fallback_title))

    def _build_title(self, question: str) -> str:
        compact = " ".join(question.strip().split())
        return compact[:24] if compact else "新对话"

    def get_session(self, user_id: str, session_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()
        return dict(row) if row else None

    def list_sessions(self, user_id: str) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC, created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def rename_session(self, user_id: str, session_id: str, title: str) -> dict | None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE sessions SET title = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
                (title, session_id, user_id),
            )
            row = connection.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, user_id: str, session_id: str) -> bool:
        with self._connect() as connection:
            owned = connection.execute(
                "SELECT id FROM sessions WHERE id = ? AND user_id = ?",
                (session_id, user_id),
            ).fetchone()
            if not owned:
                return False
            connection.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor = connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        return cursor.rowcount > 0

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = datetime('now') WHERE id = ?",
                (session_id,),
            )

    def list_messages(self, user_id: str, session_id: str) -> list[dict]:
        session = self.get_session(user_id, session_id)
        if not session:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def recent_messages(self, user_id: str, session_id: str, limit: int) -> list[dict]:
        session = self.get_session(user_id, session_id)
        if not session:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return list(reversed([dict(row) for row in rows]))
