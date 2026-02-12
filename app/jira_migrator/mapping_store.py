from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class MappingStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS project_map (
                    cloud_project_key TEXT PRIMARY KEY,
                    dc_project_key TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS issue_map (
                    cloud_issue_key TEXT PRIMARY KEY,
                    dc_issue_key TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS field_map (
                    cloud_field_id TEXT PRIMARY KEY,
                    dc_field_id TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS run_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def set_project_map(self, cloud_project_key: str, dc_project_key: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO project_map(cloud_project_key, dc_project_key) VALUES(?, ?)",
                (cloud_project_key, dc_project_key),
            )

    def get_project_map(self, cloud_project_key: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT dc_project_key FROM project_map WHERE cloud_project_key = ?",
                (cloud_project_key,),
            ).fetchone()
            return row["dc_project_key"] if row else None

    def set_issue_map(self, cloud_issue_key: str, dc_issue_key: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO issue_map(cloud_issue_key, dc_issue_key) VALUES(?, ?)",
                (cloud_issue_key, dc_issue_key),
            )

    def get_issue_map(self, cloud_issue_key: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT dc_issue_key FROM issue_map WHERE cloud_issue_key = ?",
                (cloud_issue_key,),
            ).fetchone()
            return row["dc_issue_key"] if row else None

    def set_field_map(self, cloud_field_id: str, dc_field_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO field_map(cloud_field_id, dc_field_id) VALUES(?, ?)",
                (cloud_field_id, dc_field_id),
            )

    def get_field_map(self, cloud_field_id: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT dc_field_id FROM field_map WHERE cloud_field_id = ?",
                (cloud_field_id,),
            ).fetchone()
            return row["dc_field_id"] if row else None

    def log(self, run_id: str, level: str, message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO run_log(run_id, level, message) VALUES(?, ?, ?)",
                (run_id, level, message),
            )
