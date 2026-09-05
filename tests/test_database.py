"""Database tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database.database import Database, HistoryRow


def test_database_insert_and_list(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    row = HistoryRow(
        project_id="art_0001",
        seed=42,
        created_at=Database.now_iso(),
        duration=3.0,
        width=320,
        height=180,
        fps=10,
        engine="particles",
        style="cosmic",
        params_json="{}",
        output_path=str(tmp_path / "a.mp4"),
        thumbnail_path=None,
        render_time=1.2,
        status="ok",
    )
    db.insert_video(row)
    rows = db.list_videos()
    assert len(rows) == 1
    assert rows[0].seed == 42
    found = db.get_by_seed(42)
    assert found is not None
    assert found.engine == "particles"
