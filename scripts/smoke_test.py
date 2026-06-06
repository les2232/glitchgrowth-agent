import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_engine import (
    generate_carousel,
    generate_meme_post,
    generate_product_promo,
    generate_reel,
    generate_story_pack,
    generate_weekly_batch,
)
from agent_mode import run_weekly_agent_mode
from lead_engine import classify_messages
from analytics_engine import analyze_post_metrics
from compliance_engine import check_compliance
from library_engine import ensure_library_exists, load_library
from offer_lab_engine import ensure_offers_file_exists, generate_launch_pack, load_offers
from quality_engine import score_content
from queue_engine import ensure_queue_exists, load_queue
from swipe_engine import ensure_swipe_file_exists, load_swipe_file

def main():
    assert generate_meme_post("AI tools", "creators", "chaotic", "lead capture", "Prompt Pack")["caption"]
    swipe_examples = [{"hook": "Tiny system", "cta": "comment KIT", "tone_tags": "direct, playful"}]
    assert generate_meme_post("AI tools", "creators", "chaotic", "lead capture", "Prompt Pack", swipe_examples=swipe_examples)["cta"].startswith("comment")
    assert score_content(generate_meme_post("AI tools", "creators", "chaotic", "lead capture", "Prompt Pack"))["overall_score"] >= 0
    assert generate_carousel("Turn memes into products", 7, "lead capture", "Creator Kit")["slides"]
    assert generate_reel("AI gave me a business idea", "15s", "talking-head", "Prompt Pack")["voiceover"]
    assert generate_story_pack("AI content", "Creator Kit")["stories"]
    assert generate_product_promo("Creator Kit", "prompts and templates", "$9", "posting chaos")["launch_post"]
    assert generate_weekly_batch("AI creator chaos", "2 posts per weekday", "Creator Kit")["posts"]
    assert classify_messages("KIT please")[0]["category"] == "buyer intent"
    assert analyze_post_metrics("test", "meme", 1000, 100, 5, 10, 20, 3, 50)["rates"]
    assert check_compliance(False, False, True, False)["needs_disclosure"] is True
    assert ensure_library_exists().exists()
    assert isinstance(load_library(), list)
    assert ensure_swipe_file_exists().exists()
    assert isinstance(load_swipe_file(), list)
    assert ensure_queue_exists().exists()
    assert isinstance(load_queue(), list)
    assert ensure_offers_file_exists().exists()
    offers = load_offers()
    assert isinstance(offers, list)
    if offers:
        assert generate_launch_pack(offers[0])["launch_post"]
    fake_batch = {
        "posts": [{
            "format": "meme",
            "goal": "lead capture",
            "content": {"type": "meme_post", "title": "Smoke agent post", "caption": "AI workflow caption", "cta": "comment KIT"},
        }]
    }
    with patch("agent_mode.generate_weekly_batch", return_value=fake_batch), \
        patch("agent_mode.score_content", return_value={"overall_score": 90, "detected_issues": [], "improvement_suggestions": []}), \
        patch("agent_mode.save_to_library", return_value={"id": "smoke-lib", "title": "Smoke agent post", "caption": "AI workflow caption", "cta": "comment KIT"}), \
        patch("agent_mode.add_to_queue", return_value={"queue_id": "smoke-queue"}):
        assert run_weekly_agent_mode("AI week", "Creator Kit", "daily")["queued_count"] == 1
    print("Smoke test passed.")

if __name__ == "__main__":
    main()
