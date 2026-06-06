import shutil
from pathlib import Path
from uuid import uuid4

import queue_engine


def _workspace_temp_dir():
    path = Path(__file__).parent / ".queue_tmp" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleanup_temp_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    try:
        path.parent.rmdir()
    except OSError:
        pass


def test_add_load_update_remove_queue_item(monkeypatch):
    temp_dir = _workspace_temp_dir()
    queue_path = temp_dir / "posting_queue.csv"
    monkeypatch.setattr(queue_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(queue_engine, "QUEUE_PATH", queue_path)

    try:
        saved = queue_engine.add_to_queue({
            "library_item_id": "lib-1",
            "platform": "Instagram",
            "format": "meme_post",
            "title": "AI agents meme",
            "goal": "lead capture",
            "caption": "AI agents have entered the chat.",
            "cta": "comment KIT",
        })
        rows = queue_engine.load_queue()
        updated = queue_engine.update_queue_item(saved["queue_id"], {"status": "posted", "planned_date": "2026-06-07"})
        removed = queue_engine.remove_from_queue(saved["queue_id"])

        assert queue_path.exists()
        assert len(rows) == 1
        assert rows[0]["status"] == "planned"
        assert updated["status"] == "posted"
        assert updated["planned_date"] == "2026-06-07"
        assert removed is True
        assert queue_engine.load_queue() == []
    finally:
        _cleanup_temp_dir(temp_dir)


def test_search_queue(monkeypatch):
    temp_dir = _workspace_temp_dir()
    queue_path = temp_dir / "posting_queue.csv"
    monkeypatch.setattr(queue_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(queue_engine, "QUEUE_PATH", queue_path)

    try:
        queue_engine.add_to_queue({
            "platform": "Instagram",
            "title": "Creator kit post",
            "caption": "Posting chaos needs a tiny system.",
            "notes": "Launch this first.",
        })
        queue_engine.add_to_queue({
            "platform": "TikTok",
            "title": "Reel idea",
            "caption": "AI workflow behind the scenes.",
            "notes": "Later.",
        })

        results = queue_engine.search_queue("tiny", status="planned", platform="Instagram")

        assert len(results) == 1
        assert results[0]["title"] == "Creator kit post"
    finally:
        _cleanup_temp_dir(temp_dir)
