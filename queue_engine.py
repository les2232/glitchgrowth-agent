from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

DATA_DIR = Path(__file__).parent / "data"
QUEUE_PATH = DATA_DIR / "posting_queue.csv"

QUEUE_STATUSES = ["planned", "drafted", "posted", "skipped", "archived"]

QUEUE_FIELDS = [
    "queue_id",
    "library_item_id",
    "created_at",
    "planned_date",
    "planned_time",
    "platform",
    "format",
    "title",
    "goal",
    "status",
    "caption",
    "cta",
    "notes",
]


def ensure_queue_exists() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not QUEUE_PATH.exists():
        with QUEUE_PATH.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=QUEUE_FIELDS)
            writer.writeheader()
    return QUEUE_PATH


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _normalize_status(status: str) -> str:
    status = (status or "planned").strip().lower()
    return status if status in QUEUE_STATUSES else "planned"


def _item_to_row(item: Dict[str, Any]) -> Dict[str, str]:
    content_format = item.get("format") or item.get("content_type", "")
    return {
        "queue_id": uuid4().hex,
        "library_item_id": _stringify(item.get("library_item_id") or item.get("id", "")),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "planned_date": _stringify(item.get("planned_date", "")),
        "planned_time": _stringify(item.get("planned_time", "")),
        "platform": _stringify(item.get("platform", "")),
        "format": _stringify(content_format),
        "title": _stringify(item.get("title", "")),
        "goal": _stringify(item.get("goal", "")),
        "status": _normalize_status(_stringify(item.get("status", "planned"))),
        "caption": _stringify(item.get("caption", "")),
        "cta": _stringify(item.get("cta", "")),
        "notes": _stringify(item.get("notes", "")),
    }


def _write_rows(rows: List[Dict[str, str]]) -> None:
    ensure_queue_exists()
    with QUEUE_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in QUEUE_FIELDS})


def add_to_queue(item: Dict[str, Any]) -> Dict[str, str]:
    ensure_queue_exists()
    row = _item_to_row(item)
    with QUEUE_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=QUEUE_FIELDS)
        writer.writerow(row)
    return row


def load_queue() -> List[Dict[str, str]]:
    ensure_queue_exists()
    with QUEUE_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {field: row.get(field, "") for field in QUEUE_FIELDS}
            for row in reader
        ]


def update_queue_item(queue_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, str]]:
    rows = load_queue()
    updated_row: Optional[Dict[str, str]] = None
    allowed_updates = {}
    for field, value in updates.items():
        if field not in QUEUE_FIELDS:
            continue
        allowed_updates[field] = _normalize_status(value) if field == "status" else _stringify(value)

    for row in rows:
        if row.get("queue_id") == queue_id:
            row.update(allowed_updates)
            updated_row = row
            break

    if updated_row is not None:
        _write_rows(rows)
    return updated_row


def remove_from_queue(queue_id: str) -> bool:
    rows = load_queue()
    remaining = [row for row in rows if row.get("queue_id") != queue_id]
    removed = len(remaining) != len(rows)
    if removed:
        _write_rows(remaining)
    return removed


def search_queue(
    query: str,
    status: Optional[str] = None,
    platform: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = load_queue()
    query_l = (query or "").strip().lower()
    status_l = (status or "").strip().lower()
    platform_l = (platform or "").strip().lower()
    searchable_fields = ["title", "caption", "notes"]

    results = []
    for row in rows:
        if status_l and row.get("status", "").lower() != status_l:
            continue
        if platform_l and row.get("platform", "").lower() != platform_l:
            continue
        if query_l and not any(query_l in row.get(field, "").lower() for field in searchable_fields):
            continue
        results.append(row)
    return results
