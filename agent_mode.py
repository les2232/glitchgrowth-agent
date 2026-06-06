from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from content_engine import generate_weekly_batch
from library_engine import save_to_library
from quality_engine import score_content
from queue_engine import add_to_queue

DEFAULT_POSTING_SLOTS = [
    ("Monday", "09:00"),
    ("Monday", "17:00"),
    ("Tuesday", "09:00"),
    ("Tuesday", "17:00"),
    ("Wednesday", "09:00"),
    ("Wednesday", "17:00"),
    ("Thursday", "09:00"),
    ("Thursday", "17:00"),
    ("Friday", "09:00"),
    ("Friday", "17:00"),
]

WEEKDAY_OFFSETS = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}


def _next_monday(today: date | None = None) -> date:
    today = today or date.today()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return today + timedelta(days=days_until_monday)


def _slot_for_index(index: int) -> Dict[str, str]:
    base_monday = _next_monday()
    day_name, planned_time = DEFAULT_POSTING_SLOTS[index % len(DEFAULT_POSTING_SLOTS)]
    planned_date = base_monday + timedelta(days=WEEKDAY_OFFSETS[day_name])
    return {
        "planned_day": day_name,
        "planned_date": planned_date.isoformat(),
        "planned_time": planned_time,
    }


def _average(scores: List[int]) -> int:
    if not scores:
        return 0
    return int(round(sum(scores) / len(scores)))


def run_weekly_agent_mode(
    week_theme,
    offer,
    posting_frequency,
    minimum_quality_score=75,
    use_swipe_examples=False,
    swipe_examples=None,
) -> Dict[str, Any]:
    examples = swipe_examples if use_swipe_examples else None
    batch = generate_weekly_batch(
        week_theme,
        posting_frequency,
        offer,
        swipe_examples=examples,
    )

    queued_items = []
    revision_items = []
    planned_schedule = []
    quality_scores = []
    saved_to_library_count = 0

    posts = batch.get("posts", [])
    for index, post in enumerate(posts):
        content = post.get("content", {})
        quality = score_content(content)
        overall_score = int(quality.get("overall_score", 0))
        quality_scores.append(overall_score)

        library_item = save_to_library(content)
        saved_to_library_count += 1

        slot = _slot_for_index(index)
        item_summary = {
            "title": library_item.get("title", ""),
            "format": post.get("format", content.get("type", "")),
            "goal": post.get("goal", ""),
            "quality_score": overall_score,
            "planned_day": slot["planned_day"],
            "planned_date": slot["planned_date"],
            "planned_time": slot["planned_time"],
        }

        if overall_score >= int(minimum_quality_score):
            queued = add_to_queue({
                "library_item_id": library_item.get("id", ""),
                "planned_date": slot["planned_date"],
                "planned_time": slot["planned_time"],
                "platform": "Instagram",
                "format": post.get("format", content.get("type", "")),
                "title": library_item.get("title", ""),
                "goal": post.get("goal", ""),
                "status": "planned",
                "caption": library_item.get("caption", ""),
                "cta": library_item.get("cta", ""),
                "notes": f"Agent Mode quality score: {overall_score}",
            })
            queued_item = {**item_summary, "queue_id": queued.get("queue_id", "")}
            queued_items.append(queued_item)
            planned_schedule.append(queued_item)
        else:
            revision_items.append({
                **item_summary,
                "issues": quality.get("detected_issues", []),
                "suggestions": quality.get("improvement_suggestions", []),
            })

    return {
        "generated_count": len(posts),
        "saved_to_library_count": saved_to_library_count,
        "queued_count": len(queued_items),
        "needs_revision_count": len(revision_items),
        "average_quality_score": _average(quality_scores),
        "queued_items": queued_items,
        "revision_items": revision_items,
        "planned_schedule": planned_schedule,
    }
