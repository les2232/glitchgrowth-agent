from __future__ import annotations

import re
from typing import Any, Dict, List

GENERIC_PHRASES = [
    "game changer",
    "level up",
    "unlock your potential",
    "crush it",
    "go viral",
    "hustle harder",
    "boost your productivity",
    "take it to the next level",
    "ultimate guide",
    "secret formula",
    "work smarter not harder",
]

CTA_WORDS = ["comment", "dm", "save", "share", "follow", "click", "reply", "send"]
SPECIFICITY_WORDS = ["ai", "agent", "prompt", "workflow", "template", "carousel", "reel", "meme", "kit", "creator", "dashboard"]
CHAOTIC_VOICE_WORDS = ["chaos", "chaotic", "tiny", "messy", "tabs", "side quest", "soft", "meme", "funny", "creator"]


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n\n".join(_text(item) for item in value)
    if isinstance(value, dict):
        return "\n\n".join(_text(item) for item in value.values())
    return str(value)


def _first_packet_value(packet: Dict[str, Any], keys: List[str]) -> str:
    for key in keys:
        value = packet.get(key)
        if value:
            return _text(value)
    return ""


def _packet_parts(packet: Dict[str, Any]) -> Dict[str, str]:
    return {
        "hook": _first_packet_value(packet, ["text_overlay", "hook", "title"]),
        "visual": _first_packet_value(packet, ["visual_concept", "image_generation_prompt", "image_layout_notes", "scenes"]),
        "caption": _first_packet_value(packet, ["caption", "launch_post", "soft_sell_post"]),
        "cta": _first_packet_value(packet, ["cta", "launch_post", "urgency_post"]),
        "hashtags": _text(packet.get("hashtags", "")),
        "goal": _text(packet.get("goal") or packet.get("content_goal") or packet.get("monetization_angle", "")),
        "monetization": _text(packet.get("monetization_angle", "")),
    }


def _clamp(score: int) -> int:
    return max(0, min(100, int(score)))


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text or ""))


def detect_generic_phrases(text: str) -> List[str]:
    text_l = (text or "").lower()
    return [phrase for phrase in GENERIC_PHRASES if phrase in text_l]


def _score_hook(hook: str) -> int:
    if not hook:
        return 20
    words = _word_count(hook)
    score = 70
    if 3 <= words <= 14:
        score += 20
    elif words > 24:
        score -= 20
    if any(marker in hook.lower() for marker in ["pov", "me trying", "be honest", "quick", "want"]):
        score += 8
    score -= len(detect_generic_phrases(hook)) * 12
    return _clamp(score)


def _score_caption(caption: str) -> int:
    if not caption:
        return 15
    words = _word_count(caption)
    score = 65
    if 18 <= words <= 120:
        score += 15
    if "\n" in caption:
        score += 8
    if "?" in caption:
        score += 5
    score -= len(detect_generic_phrases(caption)) * 10
    return _clamp(score)


def _score_cta(cta: str) -> int:
    if not cta:
        return 15
    cta_l = cta.lower()
    score = 60
    if any(word in cta_l for word in CTA_WORDS):
        score += 25
    if any(keyword in cta_l for keyword in ["kit", "prompts", "workflow", "early access"]):
        score += 10
    if _word_count(cta) > 24:
        score -= 12
    return _clamp(score)


def _score_brand_fit(text: str, brand_voice=None) -> int:
    score = 55
    text_l = text.lower()
    voice_terms = CHAOTIC_VOICE_WORDS[:]
    if isinstance(brand_voice, dict):
        for key in ["account_style", "topics", "voice_rules"]:
            for value in brand_voice.get(key, []):
                voice_terms.extend(str(value).lower().replace("-", " ").split())
    matches = {term for term in voice_terms if term and term in text_l}
    score += min(35, len(matches) * 5)
    if detect_generic_phrases(text):
        score -= 12
    return _clamp(score)


def _score_specificity(text: str) -> int:
    text_l = text.lower()
    score = 45
    matches = [word for word in SPECIFICITY_WORDS if word in text_l]
    score += min(35, len(matches) * 7)
    if re.search(r"\d+", text):
        score += 8
    if detect_generic_phrases(text):
        score -= 15
    return _clamp(score)


def _score_monetization(goal: str, cta: str, monetization: str) -> int:
    combined = f"{goal} {cta} {monetization}".lower()
    score = 55
    if any(word in combined for word in ["lead", "sale", "product", "affiliate", "offer", "kit"]):
        score += 20
    if any(word in combined for word in CTA_WORDS):
        score += 15
    if "spam" in combined or "viral" in combined:
        score -= 20
    return _clamp(score)


def suggest_improvements(packet: Dict[str, Any]) -> List[str]:
    parts = _packet_parts(packet)
    full_text = " ".join(parts.values())
    suggestions = []
    if _score_hook(parts["hook"]) < 75:
        suggestions.append("Tighten the hook into one specific, instantly recognizable creator problem.")
    if _score_caption(parts["caption"]) < 75:
        suggestions.append("Add a clearer mini-story or pain point before the CTA.")
    if _score_cta(parts["cta"]) < 75:
        suggestions.append("Make the CTA more direct: ask for a comment, save, DM, or keyword.")
    if _score_specificity(full_text) < 70:
        suggestions.append("Add concrete details like the tool, workflow, audience, or exact offer.")
    if detect_generic_phrases(full_text):
        suggestions.append("Replace generic growth language with more specific tech-creator wording.")
    if not suggestions:
        suggestions.append("Strong draft. Consider testing a punchier hook variant before posting.")
    return suggestions


def recommend_best_format(packet: Dict[str, Any]) -> str:
    parts = _packet_parts(packet)
    caption_words = _word_count(parts["caption"])
    hook = parts["hook"].lower()
    goal = parts["goal"].lower()
    if "save" in goal or caption_words > 90:
        return "carousel"
    if "pov" in hook or caption_words < 35:
        return "meme post"
    if "lead" in goal or "comment" in parts["cta"].lower():
        return "reel or meme post"
    return "meme post"


def rewrite_caption_variants(packet: Dict[str, Any]) -> Dict[str, str]:
    parts = _packet_parts(packet)
    caption = parts["caption"].strip() or "This idea is painfully real for creators trying to turn chaos into a system."
    cta = parts["cta"].strip() or "comment KIT if you want the workflow"
    topic = parts["hook"].strip() or "content chaos"
    short_topic = topic.split("\n")[0][:90]

    return {
        "punchier": f"{short_topic}.\n\nThe tiny fix: make one useful post, attach one clear CTA, and watch what people react to.\n\n{cta}",
        "more_chaotic": f"{caption}\n\ncurrent status: 47 tabs, one half-built idea, and a suspiciously useful little system forming in the background.\n\n{cta}",
        "softer_sell": f"{caption}\n\nNo pressure, but if this is the exact flavor of chaos you are trying to organize, {cta}.",
    }


def score_content(packet: Dict[str, Any], brand_voice=None) -> Dict[str, Any]:
    parts = _packet_parts(packet)
    full_text = " ".join(parts.values())
    hook_score = _score_hook(parts["hook"])
    caption_score = _score_caption(parts["caption"])
    cta_score = _score_cta(parts["cta"])
    brand_fit_score = _score_brand_fit(full_text, brand_voice)
    specificity_score = _score_specificity(full_text)
    monetization_fit_score = _score_monetization(parts["goal"], parts["cta"], parts["monetization"])
    detected_issues = []

    generic_phrases = detect_generic_phrases(full_text)
    if generic_phrases:
        detected_issues.append(f"Generic phrases detected: {', '.join(generic_phrases)}")
    if hook_score < 70:
        detected_issues.append("Hook may be too vague or too long.")
    if cta_score < 70:
        detected_issues.append("CTA could be clearer or more actionable.")
    if specificity_score < 70:
        detected_issues.append("Draft could use more specific creator, tech, or offer details.")
    if not detected_issues:
        detected_issues.append("No major issues detected.")

    scores = [
        hook_score,
        caption_score,
        cta_score,
        brand_fit_score,
        specificity_score,
        monetization_fit_score,
    ]

    return {
        "overall_score": _clamp(sum(scores) / len(scores)),
        "hook_score": hook_score,
        "caption_score": caption_score,
        "cta_score": cta_score,
        "brand_fit_score": brand_fit_score,
        "specificity_score": specificity_score,
        "monetization_fit_score": monetization_fit_score,
        "detected_issues": detected_issues,
        "improvement_suggestions": suggest_improvements(packet),
        "recommended_format": recommend_best_format(packet),
        "rewritten_caption_variants": rewrite_caption_variants(packet),
    }
