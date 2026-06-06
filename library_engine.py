from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

DATA_DIR = Path(__file__).parent / "data"
LIBRARY_PATH = DATA_DIR / "content_library.csv"

LIBRARY_FIELDS = [
    "id",
    "created_at",
    "content_type",
    "title",
    "status",
    "goal",
    "topic",
    "caption",
    "cta",
    "hashtags",
    "image_prompt",
    "notes",
    "posted_date",
]


def ensure_library_exists() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LIBRARY_PATH.exists():
        with LIBRARY_PATH.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=LIBRARY_FIELDS)
            writer.writeheader()
    return LIBRARY_PATH


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _first_packet_value(packet: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = packet.get(key)
        if value:
            return value
    return ""


def _packet_to_library_row(packet: Dict[str, Any]) -> Dict[str, str]:
    content_type = _stringify(packet.get("type") or "content")
    title = _stringify(
        _first_packet_value(packet, ["title", "topic", "product_name"])
        or content_type.replace("_", " ").title()
    )
    caption = _stringify(
        _first_packet_value(packet, ["caption"])
        or packet.get("launch_post", {}).get("caption", "")
    )
    cta = _stringify(
        _first_packet_value(packet, ["cta"])
        or packet.get("launch_post", {}).get("cta", "")
    )
    image_prompt = _stringify(
        _first_packet_value(packet, ["image_generation_prompt", "image_layout_notes", "scenes"])
    )

    return {
        "id": uuid4().hex,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "content_type": content_type,
        "title": title,
        "status": "draft",
        "goal": _stringify(_first_packet_value(packet, ["goal", "content_goal"])),
        "topic": _stringify(_first_packet_value(packet, ["topic", "title", "product_name"])),
        "caption": caption,
        "cta": cta,
        "hashtags": _stringify(packet.get("hashtags", "")),
        "image_prompt": image_prompt,
        "notes": "",
        "posted_date": "",
    }


def _write_rows(rows: List[Dict[str, str]]) -> None:
    ensure_library_exists()
    with LIBRARY_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LIBRARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in LIBRARY_FIELDS})


def save_to_library(packet: Dict[str, Any]) -> Dict[str, str]:
    ensure_library_exists()
    row = _packet_to_library_row(packet)
    with LIBRARY_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LIBRARY_FIELDS)
        writer.writerow(row)
    return row


def load_library() -> List[Dict[str, str]]:
    ensure_library_exists()
    with LIBRARY_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {field: row.get(field, "") for field in LIBRARY_FIELDS}
            for row in reader
        ]


def update_library_item(item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, str]]:
    rows = load_library()
    updated_row: Optional[Dict[str, str]] = None
    allowed_updates = {field: _stringify(value) for field, value in updates.items() if field in LIBRARY_FIELDS}

    for row in rows:
        if row.get("id") == item_id:
            row.update(allowed_updates)
            updated_row = row
            break

    if updated_row is not None:
        _write_rows(rows)
    return updated_row


def search_library(
    query: str,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, str]]:
    rows = load_library()
    query_l = (query or "").strip().lower()
    searchable_fields = ["title", "topic", "caption", "cta", "hashtags", "notes"]

    results = []
    for row in rows:
        if content_type and row.get("content_type") != content_type:
            continue
        if status and row.get("status") != status:
            continue
        if query_l and not any(query_l in row.get(field, "").lower() for field in searchable_fields):
            continue
        results.append(row)
    return results
