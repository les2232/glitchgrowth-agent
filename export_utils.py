from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

OUTPUTS_DIR = Path(__file__).parent / "outputs"

def ensure_outputs_dir() -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR

def slugify(text: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-")[:80] or "content-packet"

def render_markdown_packet(packet: Dict[str, Any]) -> str:
    lines: List[str] = []
    title = packet.get("title") or packet.get("type", "Content Packet").replace("_", " ").title()
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")

    def add_dict(obj: Dict[str, Any], level: int = 2):
        for key, value in obj.items():
            pretty = key.replace("_", " ").title()
            if isinstance(value, dict):
                lines.append(f"{'#' * level} {pretty}")
                lines.append("")
                add_dict(value, level + 1)
            elif isinstance(value, list):
                lines.append(f"{'#' * level} {pretty}")
                lines.append("")
                for item in value:
                    if isinstance(item, dict):
                        lines.append("---")
                        add_dict(item, min(level + 1, 5))
                    else:
                        lines.append(f"- {item}")
                lines.append("")
            else:
                lines.append(f"**{pretty}:**")
                lines.append("")
                lines.append(str(value))
                lines.append("")

    add_dict(packet)
    return "\n".join(lines)

def save_packet(packet: Dict[str, Any], name_hint: str = "content-packet") -> Path:
    ensure_outputs_dir()
    slug = slugify(name_hint)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUTPUTS_DIR / f"{stamp}-{slug}.md"
    path.write_text(render_markdown_packet(packet), encoding="utf-8")
    return path

def save_weekly_batch(batch: Dict[str, Any]) -> List[Path]:
    ensure_outputs_dir()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    theme_slug = slugify(batch.get("theme", "weekly-batch"))
    paths: List[Path] = []

    md_path = OUTPUTS_DIR / f"{stamp}-{theme_slug}-weekly-batch.md"
    md_path.write_text(render_markdown_packet(batch), encoding="utf-8")
    paths.append(md_path)

    csv_path = OUTPUTS_DIR / f"{stamp}-{theme_slug}-captions.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["slot", "format", "goal", "title", "caption", "cta", "hashtags"])
        writer.writeheader()
        for post in batch.get("posts", []):
            content = post.get("content", {})
            writer.writerow({
                "slot": post.get("slot", ""),
                "format": post.get("format", ""),
                "goal": post.get("goal", ""),
                "title": content.get("title") or content.get("product_name") or content.get("topic", ""),
                "caption": content.get("caption") or content.get("launch_post", {}).get("caption", ""),
                "cta": content.get("cta") or content.get("launch_post", {}).get("cta", ""),
                "hashtags": content.get("hashtags", ""),
            })
    paths.append(csv_path)

    json_path = OUTPUTS_DIR / f"{stamp}-{theme_slug}-weekly-batch.json"
    json_path.write_text(json.dumps(batch, indent=2), encoding="utf-8")
    paths.append(json_path)

    return paths
