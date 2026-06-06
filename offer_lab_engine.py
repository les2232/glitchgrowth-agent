from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

DATA_DIR = Path(__file__).parent / "data"
OFFERS_PATH = DATA_DIR / "offers.json"

OFFER_STATUSES = ["idea", "building", "ready", "launched", "archived"]
OFFER_FORMATS = ["template pack", "prompt pack", "service", "audit", "guide", "other"]

OFFER_FIELDS = [
    "id",
    "created_at",
    "name",
    "status",
    "audience",
    "pain_point",
    "promise",
    "deliverables",
    "format",
    "price",
    "cta_keyword",
    "checkout_url",
    "notes",
]


def ensure_offers_file_exists() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not OFFERS_PATH.exists():
        OFFERS_PATH.write_text("[]\n", encoding="utf-8")
    offers, changed = _read_normalized_offers()
    if changed:
        _write_offers(offers)
    return OFFERS_PATH


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value)


def _slug_id(name: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in name)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-")[:60] or uuid4().hex


def _infer_format(offer: Dict[str, Any]) -> str:
    text = " ".join(_stringify(offer.get(key, "")) for key in ["name", "description", "deliverables"]).lower()
    if "audit" in text:
        return "audit"
    if "service" in text:
        return "service"
    if "prompt" in text:
        return "prompt pack"
    if "template" in text or "kit" in text:
        return "template pack"
    if "guide" in text:
        return "guide"
    return "other"


def _infer_keyword(offer: Dict[str, Any]) -> str:
    cta = _stringify(offer.get("cta", "")).upper()
    for token in cta.replace('"', " ").replace("'", " ").split():
        clean = "".join(ch for ch in token if ch.isalnum())
        if clean in {"KIT", "PROMPTS", "AUDIT", "GUIDE", "HELP"}:
            return clean
    name = _stringify(offer.get("name", "KIT")).split()
    return "".join(ch for ch in (name[-1] if name else "KIT").upper() if ch.isalnum()) or "KIT"


def _normalize_offer(offer: Dict[str, Any]) -> Dict[str, str]:
    name = _stringify(offer.get("name", "Untitled Offer")).strip() or "Untitled Offer"
    description = _stringify(offer.get("description", ""))
    deliverables = _stringify(offer.get("deliverables", "")) or description
    promise = _stringify(offer.get("promise", "")) or description or f"A small useful offer around {name}."
    pain_point = _stringify(offer.get("pain_point", "")) or "posting consistently while feeling scattered"
    audience = _stringify(offer.get("audience", "")) or "tech creators and chaotic online creators"
    status = _stringify(offer.get("status", "idea")).lower()
    content_format = _stringify(offer.get("format", "")) or _infer_format(offer)

    if status not in OFFER_STATUSES:
        status = "idea"
    if content_format not in OFFER_FORMATS:
        content_format = "other"

    normalized = {
        "id": _stringify(offer.get("id", "")) or _slug_id(name),
        "created_at": _stringify(offer.get("created_at", "")) or datetime.now().isoformat(timespec="seconds"),
        "name": name,
        "status": status,
        "audience": audience,
        "pain_point": pain_point,
        "promise": promise,
        "deliverables": deliverables,
        "format": content_format,
        "price": _stringify(offer.get("price", "")),
        "cta_keyword": _stringify(offer.get("cta_keyword", "")) or _infer_keyword(offer),
        "checkout_url": _stringify(offer.get("checkout_url", "")),
        "notes": _stringify(offer.get("notes", "")),
    }
    return normalized


def _read_normalized_offers() -> tuple[List[Dict[str, str]], bool]:
    if not OFFERS_PATH.exists():
        return [], True
    try:
        raw = json.loads(OFFERS_PATH.read_text(encoding="utf-8") or "[]")
    except json.JSONDecodeError:
        raw = []
    if isinstance(raw, dict):
        raw_offers = raw.get("offers", [])
    else:
        raw_offers = raw
    if not isinstance(raw_offers, list):
        raw_offers = []
    normalized = [_normalize_offer(offer) for offer in raw_offers if isinstance(offer, dict)]
    changed = raw != normalized
    return normalized, changed


def _write_offers(offers: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OFFERS_PATH.write_text(json.dumps(offers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_offers() -> List[Dict[str, str]]:
    ensure_offers_file_exists()
    offers, _ = _read_normalized_offers()
    return offers


def save_offer(offer: Dict[str, Any]) -> Dict[str, str]:
    offers = load_offers()
    normalized = _normalize_offer({**offer, "id": offer.get("id") or uuid4().hex})
    offers.append(normalized)
    _write_offers(offers)
    return normalized


def update_offer(offer_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, str]]:
    offers = load_offers()
    updated_offer: Optional[Dict[str, str]] = None
    allowed_updates = {field: _stringify(value) for field, value in updates.items() if field in OFFER_FIELDS}
    if "status" in allowed_updates and allowed_updates["status"] not in OFFER_STATUSES:
        allowed_updates["status"] = "idea"
    if "format" in allowed_updates and allowed_updates["format"] not in OFFER_FORMATS:
        allowed_updates["format"] = "other"

    for offer in offers:
        if offer.get("id") == offer_id:
            offer.update(allowed_updates)
            updated_offer = _normalize_offer(offer)
            offer.update(updated_offer)
            break

    if updated_offer is not None:
        _write_offers(offers)
    return updated_offer


def archive_offer(offer_id: str) -> Optional[Dict[str, str]]:
    return update_offer(offer_id, {"status": "archived"})


def search_offers(query: str, status: Optional[str] = None, format: Optional[str] = None) -> List[Dict[str, str]]:
    query_l = (query or "").strip().lower()
    status_l = (status or "").strip().lower()
    format_l = (format or "").strip().lower()
    searchable_fields = ["name", "audience", "pain_point", "promise", "deliverables", "notes"]

    results = []
    for offer in load_offers():
        if status_l and offer.get("status") != status_l:
            continue
        if format_l and offer.get("format") != format_l:
            continue
        if query_l and not any(query_l in offer.get(field, "").lower() for field in searchable_fields):
            continue
        results.append(offer)
    return results


def _tone_suffix(tone_tags=None) -> str:
    tags = [str(tag).strip() for tag in (tone_tags or []) if str(tag).strip()]
    return f" Tone: {', '.join(tags[:3])}." if tags else ""


def generate_launch_pack(offer: Dict[str, Any], tone_tags=None) -> Dict[str, Any]:
    normalized = _normalize_offer(offer)
    name = normalized["name"]
    audience = normalized["audience"]
    pain = normalized["pain_point"]
    promise = normalized["promise"]
    deliverables = normalized["deliverables"]
    price = normalized["price"] or "intro price TBD"
    keyword = normalized["cta_keyword"] or "KIT"
    tone = _tone_suffix(tone_tags)
    checkout = normalized.get("checkout_url", "")
    checkout_line = f"\n\nCheckout link: {checkout}" if checkout else ""

    launch_post = {
        "type": "launch_post",
        "title": f"{name} launch",
        "text_overlay": f"{name} is here",
        "caption": (
            f"I made {name} for {audience} who are dealing with {pain}.\n\n"
            f"The promise: {promise}\n\n"
            f"Inside: {deliverables}\n\n"
            f"Intro price: {price}\n\n"
            f'Comment "{keyword}" if you want the details.{checkout_line}{tone}'
        ),
        "cta": f'comment "{keyword}" for {name}',
    }
    soft_sell_post = {
        "type": "soft_sell_post",
        "title": f"{name} soft sell",
        "text_overlay": "your messy workflow deserves a tiny system",
        "caption": (
            f"If {pain} keeps slowing you down, {name} is the small version of the fix.\n\n"
            f"It is not a huge course or overbuilt system. It is {deliverables} designed to help {audience} get moving.\n\n"
            f"Save this, or comment {keyword} if you want to see it.{tone}"
        ),
        "cta": f"save this or comment {keyword}",
    }
    urgency_post = {
        "type": "urgency_post",
        "title": f"{name} final call",
        "text_overlay": "early version window",
        "caption": (
            f"I am keeping the first version of {name} small, useful, and easy to test.\n\n"
            f"If you want help with {pain}, this is the early version to grab before I polish it too much.\n\n"
            f"Price: {price}\n\n"
            f"Comment {keyword} and I will send the details.{checkout_line}"
        ),
        "cta": f"comment {keyword} for details",
    }

    return {
        "type": "offer_launch_pack",
        "offer_id": normalized["id"],
        "offer_name": name,
        "offer_positioning_summary": f"{name} helps {audience} solve {pain} by delivering {promise}.",
        "audience_pain_summary": f"{audience} want momentum, but {pain} makes the next post, product, or workflow feel heavier than it should.",
        "launch_post": launch_post,
        "soft_sell_post": soft_sell_post,
        "urgency_final_call_post": urgency_post,
        "story_slides": [
            {"slide": 1, "type": "poll", "copy": f"be honest: is {pain} slowing you down?", "options": ["yes", "painfully"]},
            {"slide": 2, "type": "behind_the_scenes", "copy": f"I built {name} because this kept showing up in my own workflow."},
            {"slide": 3, "type": "value", "copy": f"Inside: {deliverables}"},
            {"slide": 4, "type": "proof_prompt", "copy": f"Want the tiny system for {audience}?"},
            {"slide": 5, "type": "cta", "copy": f"Comment {keyword} or DM me {keyword} for details."},
        ],
        "comment_ctas": [
            f'comment "{keyword}" if you want {name}',
            f"comment {keyword} and I will send the details",
            f"drop {keyword} if {pain} is your current side quest",
        ],
        "dm_reply_templates": [
            f"Yes. {name} is for {audience} dealing with {pain}. It includes {deliverables}. Price is {price}.",
            f"Totally. The promise is: {promise}. If that fits what you need, {name} is probably the right tiny next step.",
            f"I can send the details. Quick version: {name} helps with {pain}, includes {deliverables}, and is priced at {price}.",
        ],
        "short_faq": [
            {"question": "Who is this for?", "answer": audience},
            {"question": "What does it help with?", "answer": pain},
            {"question": "What is included?", "answer": deliverables},
            {"question": "What does it cost?", "answer": price},
        ],
        "common_objections_replies": [
            {"objection": "I do not have time.", "reply": "That is exactly why the offer is small and action-first."},
            {"objection": "I am not ready to buy.", "reply": "Save the post and use the free launch content as a starting point."},
            {"objection": "Will this sound like me?", "reply": "Use the templates as structure, then swap in your own examples and voice."},
        ],
        "recommended_first_week_posting_plan": [
            {"day": "Monday", "post": "launch_post", "goal": "announce the offer and collect keyword comments"},
            {"day": "Tuesday", "post": "story_slides", "goal": "validate pain and answer questions"},
            {"day": "Wednesday", "post": "soft_sell_post", "goal": "explain who it helps without pressure"},
            {"day": "Thursday", "post": "FAQ / objection replies", "goal": "reduce hesitation"},
            {"day": "Friday", "post": "urgency_final_call_post", "goal": "invite final early-version buyers"},
        ],
    }
