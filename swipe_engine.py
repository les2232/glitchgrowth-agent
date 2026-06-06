from __future__ import annotations

import csv
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

DATA_DIR = Path(__file__).parent / "data"
SWIPE_FILE_PATH = DATA_DIR / "swipe_file.csv"

SWIPE_FIELDS = [
    "id",
    "created_at",
    "content_type",
    "source",
    "hook",
    "caption",
    "text_overlay",
    "cta",
    "why_it_works",
    "tone_tags",
    "notes",
]


def ensure_swipe_file_exists() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SWIPE_FILE_PATH.exists():
        with SWIPE_FILE_PATH.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SWIPE_FIELDS)
            writer.writeheader()
    return SWIPE_FILE_PATH


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def save_swipe_item(item: Dict[str, Any]) -> Dict[str, str]:
    ensure_swipe_file_exists()
    row = {
        "id": uuid4().hex,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "content_type": _stringify(item.get("content_type", "example")),
        "source": _stringify(item.get("source", "")),
        "hook": _stringify(item.get("hook", "")),
        "caption": _stringify(item.get("caption", "")),
        "text_overlay": _stringify(item.get("text_overlay", "")),
        "cta": _stringify(item.get("cta", "")),
        "why_it_works": _stringify(item.get("why_it_works", "")),
        "tone_tags": _stringify(item.get("tone_tags", "")),
        "notes": _stringify(item.get("notes", "")),
    }
    with SWIPE_FILE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SWIPE_FIELDS)
        writer.writerow(row)
    return row


def load_swipe_file() -> List[Dict[str, str]]:
    ensure_swipe_file_exists()
    with SWIPE_FILE_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {field: row.get(field, "") for field in SWIPE_FIELDS}
            for row in reader
        ]


def search_swipe_file(query: str, content_type: Optional[str] = None) -> List[Dict[str, str]]:
    rows = load_swipe_file()
    query_l = (query or "").strip().lower()
    searchable_fields = ["hook", "caption", "notes", "tone_tags"]

    results = []
    for row in rows:
        if content_type and row.get("content_type") != content_type:
            continue
        if query_l and not any(query_l in row.get(field, "").lower() for field in searchable_fields):
            continue
        results.append(row)
    return results


def get_random_examples(limit: int = 3) -> List[Dict[str, str]]:
    rows = load_swipe_file()
    safe_limit = max(0, int(limit or 3))
    if safe_limit >= len(rows):
        return rows
    return random.sample(rows, safe_limit)
