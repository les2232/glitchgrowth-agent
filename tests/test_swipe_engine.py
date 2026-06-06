import shutil
from pathlib import Path
from uuid import uuid4

import swipe_engine


def _workspace_temp_dir():
    path = Path(__file__).parent / ".swipe_tmp" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleanup_temp_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    try:
        path.parent.rmdir()
    except OSError:
        pass


def test_save_and_load_swipe_item(monkeypatch):
    temp_dir = _workspace_temp_dir()
    swipe_path = temp_dir / "swipe_file.csv"
    monkeypatch.setattr(swipe_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(swipe_engine, "SWIPE_FILE_PATH", swipe_path)

    try:
        saved = swipe_engine.save_swipe_item({
            "content_type": "meme",
            "source": "manual note",
            "hook": "POV: your AI workflow needs coffee",
            "caption": "A strong saved caption.",
            "tone_tags": "chaotic, useful",
        })
        rows = swipe_engine.load_swipe_file()

        assert swipe_path.exists()
        assert len(rows) == 1
        assert rows[0]["id"] == saved["id"]
        assert rows[0]["content_type"] == "meme"
        assert rows[0]["hook"] == "POV: your AI workflow needs coffee"
    finally:
        _cleanup_temp_dir(temp_dir)


def test_search_swipe_file(monkeypatch):
    temp_dir = _workspace_temp_dir()
    swipe_path = temp_dir / "swipe_file.csv"
    monkeypatch.setattr(swipe_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(swipe_engine, "SWIPE_FILE_PATH", swipe_path)

    try:
        swipe_engine.save_swipe_item({
            "content_type": "cta",
            "hook": "Comment KIT",
            "notes": "Good direct response structure.",
            "tone_tags": "direct, soft sell",
        })
        swipe_engine.save_swipe_item({
            "content_type": "caption",
            "hook": "Tiny system",
            "notes": "Useful carousel caption.",
            "tone_tags": "calm",
        })

        results = swipe_engine.search_swipe_file("soft", content_type="cta")
        random_examples = swipe_engine.get_random_examples(limit=1)

        assert len(results) == 1
        assert results[0]["content_type"] == "cta"
        assert len(random_examples) == 1
    finally:
        _cleanup_temp_dir(temp_dir)
