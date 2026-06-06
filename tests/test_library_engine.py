import shutil
from pathlib import Path
from uuid import uuid4

from content_engine import generate_meme_post
import library_engine


def _workspace_temp_dir():
    path = Path(__file__).parent / ".library_tmp" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleanup_temp_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    try:
        path.parent.rmdir()
    except OSError:
        pass


def test_save_and_load_library_item(monkeypatch):
    temp_dir = _workspace_temp_dir()
    library_path = temp_dir / "content_library.csv"
    monkeypatch.setattr(library_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(library_engine, "LIBRARY_PATH", library_path)

    try:
        packet = generate_meme_post("AI agents", "tech creators", "chaotic", "lead capture", "Prompt Pack")
        saved = library_engine.save_to_library(packet)
        rows = library_engine.load_library()

        assert library_path.exists()
        assert len(rows) == 1
        assert rows[0]["id"] == saved["id"]
        assert rows[0]["content_type"] == "meme_post"
        assert rows[0]["caption"] == packet["caption"]
    finally:
        _cleanup_temp_dir(temp_dir)


def test_update_and_search_library_item(monkeypatch):
    temp_dir = _workspace_temp_dir()
    library_path = temp_dir / "content_library.csv"
    monkeypatch.setattr(library_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(library_engine, "LIBRARY_PATH", library_path)

    try:
        packet = generate_meme_post("AI agents", "tech creators", "chaotic", "lead capture", "Prompt Pack")
        saved = library_engine.save_to_library(packet)
        updated = library_engine.update_library_item(saved["id"], {"status": "posted", "notes": "Worked well"})
        results = library_engine.search_library("worked", content_type="meme_post", status="posted")

        assert updated["status"] == "posted"
        assert updated["notes"] == "Worked well"
        assert len(results) == 1
        assert results[0]["id"] == saved["id"]
    finally:
        _cleanup_temp_dir(temp_dir)
