from typing import Dict, List

DEFAULT_OFFERS = [
    {
        "name": "Chaotic Tech Creator Kit",
        "price": "$9-$19",
        "best_for": ["lead capture", "product sale", "creator help"],
        "description": "A small kit with tech meme prompts, caption templates, CTAs, carousel structures, and AI workflow prompts.",
        "cta": "comment KIT if you want early access",
    },
    {
        "name": "Chaotic Creator Prompt Pack",
        "price": "$7-$15",
        "best_for": ["lead capture", "product sale", "AI content"],
        "description": "Prompt templates for turning messy ideas into posts, captions, Reels, and carousels.",
        "cta": "comment PROMPTS and I’ll send the list",
    },
    {
        "name": "Mini AI Workflow Audit",
        "price": "$49-$99",
        "best_for": ["service lead", "higher intent"],
        "description": "A short review of a creator or small business workflow with AI automation suggestions.",
        "cta": "DM me AUDIT if your workflow is a mess",
    },
]

def recommend_offer(post_goal: str, topic: str = "") -> Dict[str, str]:
    goal = (post_goal or "").lower()
    topic_l = (topic or "").lower()

    if "service" in goal or "automation" in topic_l or "workflow" in topic_l:
        return DEFAULT_OFFERS[2]
    if "prompt" in topic_l or "ai" in topic_l or "lead" in goal:
        return DEFAULT_OFFERS[1]
    return DEFAULT_OFFERS[0]

def build_cta(goal: str, offer_name: str = "") -> str:
    goal_l = (goal or "").lower()
    offer = offer_name or "the kit"

    if "growth" in goal_l:
        return "follow for more tech chaos + creator survival systems"
    if "engagement" in goal_l:
        return "tell me your most emotionally damaging tech problem"
    if "lead" in goal_l:
        return f'comment "KIT" if you want the early version of {offer}'
    if "product" in goal_l or "sale" in goal_l:
        return f"{offer} is in progress — comment KIT if you want first access"
    if "affiliate" in goal_l:
        return "affiliate link disclosed — I only share tools I’d actually use"
    if "service" in goal_l:
        return 'DM me "AUDIT" if your workflow has 47 tabs open'
    return "save this for later and follow for more"

def monetization_angle(goal: str, offer_name: str = "") -> str:
    goal_l = (goal or "").lower()
    if "growth" in goal_l:
        return "Growth post. No hard sell. Build audience identity first."
    if "engagement" in goal_l:
        return "Engagement post. Use replies/comments as market research."
    if "lead" in goal_l:
        return f"Lead capture for {offer_name or 'a digital product'}."
    if "product" in goal_l or "sale" in goal_l:
        return f"Soft product promotion for {offer_name or 'your offer'}."
    if "service" in goal_l:
        return "Service lead generation. Look for people describing workflow pain."
    if "affiliate" in goal_l:
        return "Affiliate content. Add clear disclosure before posting."
    return "Mixed goal. Track comments, saves, shares, follows, and profile visits."
