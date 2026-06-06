from quality_engine import detect_generic_phrases, rewrite_caption_variants, score_content


def _sample_packet():
    return {
        "type": "meme_post",
        "text_overlay": "POV: your AI workflow has 47 tabs",
        "visual_concept": "Chaotic tech creator desk with browser tabs and prompt notes.",
        "caption": "AI workflows are useful until your tiny system becomes a side quest. Anyone else organizing the chaos today?",
        "cta": 'comment "KIT" if you want the workflow',
        "hashtags": "#AIMemes #CreatorTools",
        "goal": "lead capture",
        "monetization_angle": "Lead capture for a creator kit.",
    }


def test_detect_generic_phrases():
    phrases = detect_generic_phrases("This ultimate guide will help you level up and go viral.")
    assert "ultimate guide" in phrases
    assert "level up" in phrases
    assert "go viral" in phrases


def test_score_content_returns_expected_score_fields():
    result = score_content(_sample_packet())
    expected_fields = {
        "overall_score",
        "hook_score",
        "caption_score",
        "cta_score",
        "brand_fit_score",
        "specificity_score",
        "monetization_fit_score",
        "detected_issues",
        "improvement_suggestions",
        "recommended_format",
        "rewritten_caption_variants",
    }
    assert expected_fields.issubset(result.keys())
    assert 0 <= result["overall_score"] <= 100


def test_rewrite_caption_variants_returns_three_variants():
    variants = rewrite_caption_variants(_sample_packet())
    assert set(variants.keys()) == {"punchier", "more_chaotic", "softer_sell"}
    assert all(variants.values())
