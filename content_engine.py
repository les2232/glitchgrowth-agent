from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from offer_engine import build_cta, monetization_angle, recommend_offer

HASHTAG_BANK = [
    "#TechMemes",
    "#ITSupport",
    "#HelpDeskLife",
    "#WomenInTech",
    "#AIMemes",
    "#CreatorTools",
    "#OfficeHumor",
    "#TechTok",
    "#ContentCreator",
    "#ProductivityTools",
]

MOOD_WORDS = {
    "chaotic": ["unhinged", "feral", "47-tabs-open", "emotionally caffeinated"],
    "funny": ["painfully accurate", "too real", "absurdly specific", "quietly devastating"],
    "dramatic": ["main character crisis", "final boss energy", "emotional damage", "end credits"],
    "soft": ["gentle chaos", "cozy productivity", "tiny system", "low-pressure"],
    "smart": ["operator mode", "workflow brain", "systems thinking", "signal over noise"],
}


def _pick_hashtags(topic: str, count: int = 7) -> str:
    topic_l = (topic or "").lower()
    tags = []
    if "ai" in topic_l:
        tags.extend(["#AIMemes", "#AITools", "#CreatorTools"])
    if "it" in topic_l or "help desk" in topic_l or "printer" in topic_l:
        tags.extend(["#ITSupport", "#HelpDeskLife", "#TechMemes"])
    if "creator" in topic_l or "content" in topic_l:
        tags.extend(["#ContentCreator", "#CreatorEconomy", "#CreatorTools"])
    tags.extend(HASHTAG_BANK)
    deduped = []
    for tag in tags:
        if tag not in deduped:
            deduped.append(tag)
    return " ".join(deduped[:count])


def _mood_phrase(mood: str) -> str:
    mood_l = (mood or "chaotic").lower()
    for key, options in MOOD_WORDS.items():
        if key in mood_l:
            return options[0]
    return "chaotic but useful"


def _clean_examples(swipe_examples) -> List[Dict[str, Any]]:
    return [example for example in (swipe_examples or []) if isinstance(example, dict)][:3]


def _word_count(text: str) -> int:
    return len((text or "").split())


def pick_swipe_tone_tags(swipe_examples) -> List[str]:
    tags = []
    for example in _clean_examples(swipe_examples):
        raw_tags = example.get("tone_tags", "")
        for tag in raw_tags.replace("#", "").replace(";", ",").split(","):
            cleaned = tag.strip().lower()
            if cleaned and cleaned not in tags:
                tags.append(cleaned)
    return tags[:4]


def pick_swipe_cta_style(swipe_examples) -> str:
    ctas = " ".join(example.get("cta", "") for example in _clean_examples(swipe_examples)).lower()
    if "comment" in ctas:
        return "direct_comment"
    if "dm" in ctas or "message" in ctas:
        return "dm_prompt"
    if "save" in ctas:
        return "save_first"
    return ""


def pick_swipe_hook_pattern(swipe_examples) -> str:
    hooks = [example.get("hook", "") for example in _clean_examples(swipe_examples) if example.get("hook")]
    if not hooks:
        return ""

    average_words = sum(_word_count(hook) for hook in hooks) / len(hooks)
    lower_hooks = " ".join(hooks).lower()
    if average_words <= 8:
        return "short_punchy"
    if "pov" in lower_hooks:
        return "pov"
    if average_words >= 14:
        return "story_hook"
    return "direct"


def summarize_swipe_style(swipe_examples) -> str:
    examples = _clean_examples(swipe_examples)
    if not examples:
        return ""

    guidance = []
    tone_tags = pick_swipe_tone_tags(examples)
    hook_pattern = pick_swipe_hook_pattern(examples)
    cta_style = pick_swipe_cta_style(examples)
    why_notes = [example.get("why_it_works", "") for example in examples if example.get("why_it_works")]

    if tone_tags:
        guidance.append(f"tone: {', '.join(tone_tags)}")
    if hook_pattern:
        guidance.append(f"hook pattern: {hook_pattern}")
    if cta_style:
        guidance.append(f"cta style: {cta_style}")
    if why_notes:
        guidance.append("structure: " + " / ".join(note.strip() for note in why_notes[:2]))
    return "; ".join(guidance)


def _caption_style(swipe_examples) -> str:
    captions = [example.get("caption", "") for example in _clean_examples(swipe_examples) if example.get("caption")]
    if not captions:
        return ""
    average_words = sum(_word_count(caption) for caption in captions) / len(captions)
    if average_words >= 35:
        return "story"
    if average_words <= 14:
        return "short"
    return "balanced"


def _blend_mood(mood_phrase: str, swipe_examples) -> str:
    tags = pick_swipe_tone_tags(swipe_examples)
    if not tags:
        return mood_phrase
    return f"{mood_phrase}, with {', '.join(tags[:2])} energy"


def _style_note(swipe_examples) -> str:
    summary = summarize_swipe_style(swipe_examples)
    if not summary:
        return ""
    return f"Swipe style guidance, use as inspiration only: {summary}."


def _adapt_cta(default_cta: str, offer_name: str, swipe_examples, keyword: str = "KIT") -> str:
    cta_style = pick_swipe_cta_style(swipe_examples)
    if cta_style == "direct_comment":
        return f'comment "{keyword}" if you want {offer_name}'
    if cta_style == "dm_prompt":
        return f'DM me "{keyword}" if you want {offer_name}'
    if cta_style == "save_first":
        return f"save this, then comment {keyword} if you want {offer_name}"
    return default_cta


def generate_meme_post(
    topic: str,
    audience: str,
    mood: str,
    content_goal: str,
    offer: str = "",
    swipe_examples=None,
) -> Dict[str, str]:
    topic = topic.strip() or "AI tools and creator chaos"
    audience = audience.strip() or "tech creators"
    content_goal = content_goal.strip() or "growth"
    offer_obj = recommend_offer(content_goal, topic)
    offer_name = offer.strip() or offer_obj["name"]
    mood_phrase = _blend_mood(_mood_phrase(mood), swipe_examples)
    hook_pattern = pick_swipe_hook_pattern(swipe_examples)
    caption_style = _caption_style(swipe_examples)

    title = f"{topic.title()} Meme"
    overlay = (
        f"POV: {topic.lower()}\nagain"
        if hook_pattern == "short_punchy"
        else f"me trying to handle {topic.lower()}\nwhile pretending I am totally normal"
    )
    visual = (
        f"A chaotic-but-cute tech creator at a laptop, surrounded by floating error popups, "
        f"sticky notes, browser tabs, and one tiny robot assistant causing mild drama. "
        f"Vibe: {mood_phrase}. Audience: {audience}."
    )
    if caption_style == "story":
        caption = (
            f"I thought {topic.lower()} was going to be the simple part.\n\n"
            f"Then it turned into a tiny saga: one idea, three half-finished tabs, a content plan, "
            f"and the sudden realization that my workflow has side quests.\n\n"
            f"Still, there is something useful hiding in the mess: if people relate to the chaos, "
            f"that is usually the post telling you what to build next.\n\n"
            f"anyone else in their {mood_phrase} era?"
        )
    else:
        caption = (
            f"{topic.lower()} really said: what if your productivity system needed emotional support?\n\n"
            f"I am trying to be organized, but my brain has a dashboard, a content plan, "
            f"three side quests, and somehow still no clean laundry.\n\n"
            f"anyone else in their {mood_phrase} era?"
        )
    cta = _adapt_cta(build_cta(content_goal, offer_name), offer_name, swipe_examples)
    image_prompt = (
        f"Create a square Instagram meme image. Style: cyber-cute, tech desk chaos, expressive, "
        f"funny, modern internet meme aesthetic. Scene: {visual}. "
        f"Leave clean empty space at the top for text overlay: {overlay!r}. "
        f"Do not include logos or real brand names. {_style_note(swipe_examples)}"
    )

    return {
        "type": "meme_post",
        "title": title,
        "visual_concept": visual,
        "text_overlay": overlay,
        "caption": caption,
        "cta": cta,
        "hashtags": _pick_hashtags(topic),
        "monetization_angle": monetization_angle(content_goal, offer_name),
        "image_generation_prompt": image_prompt.strip(),
        "metric_to_track": "comments, saves, shares, follows, profile visits",
    }


def generate_carousel(
    topic: str,
    number_of_slides: int,
    goal: str,
    offer: str = "",
    swipe_examples=None,
) -> Dict[str, object]:
    topic = topic.strip() or "turning content chaos into a system"
    number_of_slides = max(4, min(int(number_of_slides or 7), 10))
    offer_obj = recommend_offer(goal, topic)
    offer_name = offer.strip() or offer_obj["name"]
    hook_pattern = pick_swipe_hook_pattern(swipe_examples)
    caption_style = _caption_style(swipe_examples)
    tone_tags = pick_swipe_tone_tags(swipe_examples)
    tone_note = f" Tone: {', '.join(tone_tags[:2])}." if tone_tags else ""
    final_cta = _adapt_cta(f"Comment KIT and I will send the early version of {offer_name}.", offer_name, swipe_examples)

    slides = []
    slides.append({
        "slide": 1,
        "copy": f"{topic.title()}\nquick version" if hook_pattern == "short_punchy" else f"{topic.title()}\nfor people whose brain has 47 tabs open",
        "layout_note": f"Big bold title, messy desk or browser-tabs visual.{tone_note}",
    })

    middle_templates = [
        ("Notice the pain", "What are people laughing about because it is painfully real? That pain is the content signal."),
        ("Turn the pain into a format", "Make it a meme, carousel, Reel, story, or tiny checklist."),
        ("Add one useful point", "The best posts are funny first, useful second, and sell only when it makes sense."),
        ("Attach the right CTA", "Growth posts ask for follows. Conversation posts ask for comments. Lead posts ask for a keyword."),
        ("Reuse the idea", "One strong idea can become a meme, Reel, carousel, story, and product angle."),
        ("Track the clue", "Comments show pain. Saves show usefulness. Shares show relatability. Follows show positioning."),
        ("Make the tiny offer", "Do not build a huge course first. Build the smallest useful thing someone would actually want."),
    ]

    style_note = _style_note(swipe_examples)
    for idx, (heading, body) in enumerate(middle_templates[: number_of_slides - 2], start=2):
        slides.append({
            "slide": idx,
            "copy": f"{idx-1}. {heading}\n\n{body}",
            "layout_note": f"Simple text card with one small icon or screenshot-style visual. {style_note}".strip(),
        })

    slides.append({
        "slide": number_of_slides,
        "copy": f"Want the shortcut?\n\n{final_cta}",
        "layout_note": "CTA slide. Make it clean, high contrast, and easy to read.",
    })

    if caption_style == "story":
        caption = (
            f"I used to make {topic.lower()} feel way bigger than it needed to be.\n\n"
            f"The better version is smaller: notice the pain, turn it into one useful format, "
            f"and let the response tell you what to build next.\n\n"
            f"{final_cta}"
        )
    else:
        caption = (
            f"this is your reminder that {topic.lower()} does not have to become a huge dramatic project.\n\n"
            f"start with one useful post.\nturn it into one small offer.\nthen let the audience reaction tell you what to make next.\n\n"
            f"{final_cta}"
        )

    return {
        "type": "carousel",
        "title": topic.title(),
        "slides": slides,
        "caption": caption,
        "cta": _adapt_cta(build_cta(goal, offer_name), offer_name, swipe_examples),
        "hashtags": _pick_hashtags(topic),
        "monetization_angle": monetization_angle(goal, offer_name),
        "image_layout_notes": "Use 1080x1350 vertical carousel size. Keep each slide low-text and punchy.",
        "metric_to_track": "saves, shares, comments, profile visits",
    }


def generate_reel(
    topic: str,
    desired_length: str,
    style: str,
    offer: str = "",
    swipe_examples=None,
) -> Dict[str, object]:
    topic = topic.strip() or "AI productivity chaos"
    style = style.strip() or "fast chaotic talking-head"
    offer_name = offer.strip() or recommend_offer("lead capture", topic)["name"]
    tone_tags = pick_swipe_tone_tags(swipe_examples)
    hook_pattern = pick_swipe_hook_pattern(swipe_examples)
    caption_style = _caption_style(swipe_examples)
    cta = _adapt_cta(f'comment "PROMPTS" if you want the workflow behind {offer_name}', offer_name, swipe_examples, "PROMPTS")
    if tone_tags:
        style = f"{style}, {', '.join(tone_tags[:2])}"

    scenes = [
        {
            "time": "0-2s",
            "on_screen_text": f"POV: {topic.lower()}" if hook_pattern == "short_punchy" else f"me using AI for one simple {topic.lower()} problem",
            "visual": "Stare at laptop with suspicious optimism.",
        },
        {
            "time": "3-6s",
            "on_screen_text": "12 minutes later",
            "visual": "Cut to too many tabs, notes, Canva, calendar, and a half-built product idea.",
        },
        {
            "time": "7-11s",
            "on_screen_text": "this was supposed to save time",
            "visual": "Slow zoom while looking emotionally betrayed by your own workflow.",
        },
        {
            "time": "12-15s",
            "on_screen_text": cta,
            "visual": "Point to comment area or show simple note card.",
        },
    ]

    if caption_style == "story":
        voiceover = (
            f"I opened AI to help with {topic.lower()} because I thought it would be a two-minute task.\n"
            "Then the idea expanded into a content system, a tiny offer, and three things I suddenly wanted to test.\n"
            f"Anyway, {cta}."
        )
    else:
        voiceover = (
            f"I opened AI to help with {topic.lower()}.\n"
            "Now I have a content calendar, a product idea, a lead magnet, and a mild identity crisis.\n"
            f"Anyway, {cta}."
        )

    return {
        "type": "reel",
        "title": f"Reel: {topic.title()}",
        "style": style,
        "desired_length": desired_length or "12-18 seconds",
        "hook": f"POV: {topic.lower()}" if hook_pattern == "short_punchy" else f"POV: {topic.lower()} was supposed to make your life easier",
        "scenes": scenes,
        "voiceover": voiceover,
        "caption": f"{topic.lower()} is just side quest management with better branding.",
        "cta": cta,
        "hashtags": _pick_hashtags(topic),
        "monetization_angle": f"Lead capture for {offer_name}.",
        "metric_to_track": "rewatches, comments, saves, profile visits",
    }


def generate_story_pack(topic: str, offer: str = "", goal: str = "lead capture", swipe_examples=None) -> Dict[str, object]:
    topic = topic.strip() or "posting consistently with AI"
    offer_name = offer.strip() or recommend_offer(goal, topic)["name"]
    tone_tags = pick_swipe_tone_tags(swipe_examples)
    hook_pattern = pick_swipe_hook_pattern(swipe_examples)
    cta = _adapt_cta(f"comment KIT for {offer_name}", offer_name, swipe_examples)
    opener = f"quick check:\n\n{topic.lower()}?" if hook_pattern == "short_punchy" else f"be honest:\n\nare you using AI for {topic.lower()}?"
    tone_note = f"\n\nvibe: {', '.join(tone_tags[:2])}" if tone_tags else ""

    stories = [
        {
            "type": "poll",
            "copy": opener + tone_note,
            "options": ["yes constantly", "no I fear the robot"],
        },
        {
            "type": "question_box",
            "copy": "what is the hardest part of posting consistently?",
            "options": [],
        },
        {
            "type": "behind_the_scenes",
            "copy": "today's content system:\n1 idea -> meme -> carousel -> Reel -> CTA\n\ntrying to stop wasting good ideas.",
            "options": [],
        },
        {
            "type": "soft_sell",
            "copy": f"I am building {offer_name} for people who want to create faster without sounding like LinkedIn.\n\nwant it?",
            "options": ["yes pls", "show me first"],
        },
        {
            "type": "final_cta",
            "copy": cta,
            "options": [],
        },
    ]

    return {
        "type": "story_pack",
        "topic": topic,
        "stories": stories,
        "cta": cta,
        "monetization_angle": monetization_angle(goal, offer_name),
        "metric_to_track": "poll taps, question replies, DMs, profile clicks",
    }


def generate_product_promo(
    product_name: str,
    product_description: str,
    price: str,
    audience_pain_point: str,
    swipe_examples=None,
) -> Dict[str, object]:
    product_name = product_name.strip() or "Chaotic Tech Creator Kit"
    product_description = product_description.strip() or "meme prompts, caption templates, CTA ideas, carousel structures, and AI workflows"
    price = price.strip() or "$9-$19"
    pain = audience_pain_point.strip() or "wanting to post more while feeling overwhelmed"
    tone_tags = pick_swipe_tone_tags(swipe_examples)
    hook_pattern = pick_swipe_hook_pattern(swipe_examples)
    caption_style = _caption_style(swipe_examples)
    cta = _adapt_cta('comment "KIT" for early access', product_name, swipe_examples)
    tone_line = f"\n\nTone I am aiming for: {', '.join(tone_tags[:2])}." if tone_tags and caption_style == "story" else ""

    launch_post = {
        "text_overlay": "tiny system, big relief" if hook_pattern == "short_punchy" else "for creators whose brain has 47 tabs open",
        "caption": (
            f"I am building {product_name}\n\n"
            f"It is for people who are dealing with {pain}.\n\n"
            f"Inside: {product_description}.\n\n"
            f"I am keeping the first version small, useful, and not painfully corporate.\n\n"
            f"Estimated price: {price}\n\n"
            f"{cta}.{tone_line}"
        ),
        "cta": cta,
    }

    soft_sell = {
        "text_overlay": "your messy content brain deserves a tiny system",
        "caption": (
            f"{product_name} is basically a content survival kit for chaotic creators.\n\n"
            "not a huge course.\nnot a 90-page ebook.\njust the templates/prompts I wish I had when my ideas were scattered everywhere."
        ),
        "cta": _adapt_cta("save this or comment KIT if you want it", product_name, swipe_examples),
    }

    urgency_post = {
        "text_overlay": "early version loading...",
        "caption": (
            f"I am putting together the first version of {product_name} this week.\n\n"
            "If you want the messy-but-useful early version before I polish it too much, comment KIT."
        ),
        "cta": _adapt_cta("comment KIT", product_name, swipe_examples),
    }

    dm_reply = (
        f"omg yes. I am putting together {product_name} now. "
        f"It will include {product_description}. "
        f"I am aiming to keep it simple and useful around {price}. "
        "I can send you the early version when it is ready."
    )

    return {
        "type": "product_promo",
        "product_name": product_name,
        "price": price,
        "launch_post": launch_post,
        "soft_sell_post": soft_sell,
        "urgency_post": urgency_post,
        "story_sequence": generate_story_pack(product_name, product_name, swipe_examples=swipe_examples)["stories"],
        "dm_reply": dm_reply,
        "metric_to_track": "comments with KIT, DMs, link clicks, saves",
    }


def generate_weekly_batch(
    week_theme: str,
    posting_frequency: str,
    offer: str,
    swipe_examples=None,
) -> Dict[str, object]:
    theme = week_theme.strip() or "AI creator chaos"
    offer_name = offer.strip() or "Chaotic Tech Creator Kit"

    schedule = [
        ("Monday AM", "meme", "growth"),
        ("Monday PM", "carousel", "lead capture"),
        ("Tuesday AM", "meme", "engagement"),
        ("Tuesday PM", "reel", "lead capture"),
        ("Wednesday AM", "meme", "growth"),
        ("Wednesday PM", "product_promo", "product sale"),
        ("Thursday AM", "story_pack", "lead capture"),
        ("Thursday PM", "carousel", "save/share"),
        ("Friday AM", "meme", "engagement"),
        ("Friday PM", "reel", "service lead"),
    ]

    posts = []
    for slot, kind, goal in schedule:
        topic = f"{theme} - {slot}"
        if kind == "meme":
            content = generate_meme_post(topic, "tech creators and IT people", "chaotic funny", goal, offer_name, swipe_examples=swipe_examples)
        elif kind == "carousel":
            content = generate_carousel(topic, 7, goal, offer_name, swipe_examples=swipe_examples)
        elif kind == "reel":
            content = generate_reel(topic, "12-18 seconds", "fast chaotic talking-head", offer_name, swipe_examples=swipe_examples)
        elif kind == "story_pack":
            content = generate_story_pack(topic, offer_name, goal, swipe_examples=swipe_examples)
        else:
            content = generate_product_promo(
                offer_name,
                "tech meme prompts, caption templates, CTAs, carousel structures, and AI workflow prompts",
                "$9-$19",
                "posting consistently while feeling scattered",
                swipe_examples=swipe_examples,
            )

        posts.append({
            "slot": slot,
            "format": kind,
            "goal": goal,
            "content": content,
        })

    return {
        "type": "weekly_batch",
        "theme": theme,
        "posting_frequency": posting_frequency or "2 posts per weekday",
        "offer": offer_name,
        "posts": posts,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
