from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import uuid
from pathlib import Path

from app.core.config import get_settings


class UserStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.settings = settings
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
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """
            )

            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(users)").fetchall()
            }
            if "is_admin" not in columns:
                connection.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

    def _hash_password(self, password: str, salt: str | None = None) -> str:
        real_salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), real_salt.encode("utf-8"), 120000)
        return f"{real_salt}${digest.hex()}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        salt, stored = password_hash.split("$", 1)
        computed = self._hash_password(password, salt).split("$", 1)[1]
        return hmac.compare_digest(stored, computed)

    def _should_be_admin(self, email: str) -> bool:
        normalized_email = email.strip().lower()
        admin_emails = {
            item.strip().lower()
            for item in self.settings.admin_emails.split(",")
            if item.strip()
        }
        if normalized_email in admin_emails:
            return True
        with self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        return count == 0

    def create_user(self, email: str, password: str) -> dict:
        user_id = uuid.uuid4().hex
        normalized_email = email.strip().lower()
        password_hash = self._hash_password(password)
        is_admin = 1 if self._should_be_admin(normalized_email) else 0
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO users (id, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
                (user_id, normalized_email, password_hash, is_admin),
            )
            row = connection.execute(
                "SELECT id, email, is_admin, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return self._serialize_user(row)

    def authenticate(self, email: str, password: str) -> dict | None:
        normalized_email = email.strip().lower()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, email, password_hash, is_admin, created_at FROM users WHERE email = ?",
                (normalized_email,),
            ).fetchone()
        if not row:
            return None
        payload = dict(row)
        if not self._verify_password(password, payload["password_hash"]):
            return None
        return {
            "id": payload["id"],
            "email": payload["email"],
            "is_admin": bool(payload["is_admin"]),
            "created_at": payload["created_at"],
        }

    def issue_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO auth_tokens (token, user_id) VALUES (?, ?)",
                (token, user_id),
            )
        return token

    def get_user_by_token(self, token: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT users.id, users.email, users.is_admin, users.created_at
                FROM auth_tokens
                JOIN users ON users.id = auth_tokens.user_id
                WHERE auth_tokens.token = ?
                """,
                (token,),
            ).fetchone()
        return self._serialize_user(row) if row else None

    def list_users(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, email, is_admin, created_at FROM users ORDER BY created_at ASC"
            ).fetchall()
        return [self._serialize_user(row) for row in rows]

    def set_admin(self, user_id: str, is_admin: bool, actor_user_id: str) -> dict | None:
        if user_id == actor_user_id and not is_admin:
            return self.get_user_by_id(user_id)
        with self._connect() as connection:
            connection.execute(
                "UPDATE users SET is_admin = ? WHERE id = ?",
                (1 if is_admin else 0, user_id),
            )
            row = connection.execute(
                "SELECT id, email, is_admin, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return self._serialize_user(row) if row else None

    def get_user_by_id(self, user_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, email, is_admin, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
        return self._serialize_user(row) if row else None

    def _serialize_user(self, row: sqlite3.Row | dict) -> dict:
        payload = dict(row)
        payload["is_admin"] = bool(payload.get("is_admin", 0))
        return payload
