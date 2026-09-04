"""SQLite history database."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.utils.paths import project_root, resolve_path


@dataclass
class HistoryRow:
    project_id: str
    seed: int
    created_at: str
    duration: float
    width: int
    height: int
    fps: int
    engine: str
    style: str
    params_json: str
    output_path: str
    thumbnail_path: str | None
    render_time: float
    status: str


class Database:
    """Persistent store for generated video metadata."""

    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            db_path = project_root() / "data" / "history.db"
        else:
            db_path = resolve_path(path) if not Path(path).is_absolute() else Path(path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    seed INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    duration REAL NOT NULL,
                    width INTEGER NOT NULL,
                    height INTEGER NOT NULL,
                    fps INTEGER NOT NULL,
                    engine TEXT NOT NULL,
                    style TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    render_time REAL NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_videos_seed ON videos(seed)"
            )
            conn.commit()

    def insert_video(self, row: HistoryRow) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO videos (
                    project_id, seed, created_at, duration, width, height, fps,
                    engine, style, params_json, output_path, thumbnail_path,
                    render_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.project_id,
                    row.seed,
                    row.created_at,
                    row.duration,
                    row.width,
                    row.height,
                    row.fps,
                    row.engine,
                    row.style,
                    row.params_json,
                    row.output_path,
                    row.thumbnail_path,
                    row.render_time,
                    row.status,
                ),
            )
            conn.commit()
            return int(cur.lastrowid)

    def list_videos(self, limit: int = 100) -> list[HistoryRow]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM videos ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._to_row(r) for r in rows]

    def get_by_seed(self, seed: int) -> HistoryRow | None:
        with self._connect() as conn:
            r = conn.execute(
                "SELECT * FROM videos WHERE seed = ? ORDER BY id DESC LIMIT 1",
                (seed,),
            ).fetchone()
        return self._to_row(r) if r else None

    @staticmethod
    def _to_row(r: sqlite3.Row) -> HistoryRow:
        return HistoryRow(
            project_id=r["project_id"],
            seed=r["seed"],
            created_at=r["created_at"],
            duration=r["duration"],
            width=r["width"],
            height=r["height"],
            fps=r["fps"],
            engine=r["engine"],
            style=r["style"],
            params_json=r["params_json"],
            output_path=r["output_path"],
            thumbnail_path=r["thumbnail_path"],
            render_time=r["render_time"],
            status=r["status"],
        )

    @staticmethod
    def params_to_json(params: dict[str, Any]) -> str:
        return json.dumps(params, default=str)

    @staticmethod
    def now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")
