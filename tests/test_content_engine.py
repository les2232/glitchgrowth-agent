from content_engine import (
    generate_carousel,
    generate_meme_post,
    generate_product_promo,
    generate_reel,
    generate_story_pack,
    generate_weekly_batch,
)
from lead_engine import classify_messages
from compliance_engine import check_compliance

def test_generate_meme_post_has_ready_to_use_fields():
    packet = generate_meme_post("AI agents", "tech creators", "chaotic", "lead capture", "Prompt Pack")
    assert packet["text_overlay"]
    assert packet["caption"]
    assert packet["cta"]
    assert packet["image_generation_prompt"]

def test_weekly_batch_has_ten_posts():
    batch = generate_weekly_batch("AI creator chaos", "2 posts per weekday", "Creator Kit")
    assert len(batch["posts"]) == 10

def test_generators_accept_empty_swipe_examples():
    assert generate_meme_post("AI agents", "tech creators", "chaotic", "lead capture", "Prompt Pack", swipe_examples=None)["caption"]
    assert generate_carousel("AI systems", 5, "lead capture", "Creator Kit", swipe_examples=None)["slides"]
    assert generate_reel("AI systems", "15s", "talking-head", "Creator Kit", swipe_examples=None)["voiceover"]
    assert generate_story_pack("AI systems", "Creator Kit", swipe_examples=None)["stories"]
    assert generate_product_promo("Creator Kit", "prompts", "$9", "posting chaos", swipe_examples=None)["launch_post"]
    assert generate_weekly_batch("AI systems", "daily", "Creator Kit", swipe_examples=None)["posts"]

def test_swipe_examples_influence_meme_output_without_copying():
    swipe_examples = [
        {
            "content_type": "meme",
            "hook": "Tiny system. Big relief.",
            "caption": (
                "I used to think the whole process had to be perfect before I posted anything. "
                "Then I realized the messy behind-the-scenes version was the part people actually related to. "
                "That changed the whole shape of the post."
            ),
            "cta": "comment BLUEPRINT",
            "tone_tags": "minimal, direct",
            "why_it_works": "Short hook, story caption, direct comment CTA.",
        }
    ]

    plain = generate_meme_post("AI agents", "tech creators", "chaotic", "lead capture", "Prompt Pack")
    influenced = generate_meme_post(
        "AI agents",
        "tech creators",
        "chaotic",
        "lead capture",
        "Prompt Pack",
        swipe_examples=swipe_examples,
    )

    assert influenced["text_overlay"] != plain["text_overlay"]
    assert "minimal" in influenced["visual_concept"]
    assert influenced["cta"].startswith("comment")
    assert "Tiny system. Big relief." not in influenced["text_overlay"]

def test_lead_classifier_buyer_intent():
    results = classify_messages("can you send the KIT?")
    assert results[0]["category"] == "buyer intent"

def test_compliance_affiliate_needs_disclosure():
    result = check_compliance(False, False, True, False)
    assert result["needs_disclosure"] is True
