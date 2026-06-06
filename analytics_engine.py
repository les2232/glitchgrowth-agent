from typing import Dict, List

def analyze_post_metrics(
    post_title: str,
    post_format: str,
    reach: int,
    likes: int,
    comments: int,
    shares: int,
    saves: int,
    follows: int,
    profile_visits: int,
) -> Dict[str, object]:
    reach = max(int(reach or 0), 1)
    likes = int(likes or 0)
    comments = int(comments or 0)
    shares = int(shares or 0)
    saves = int(saves or 0)
    follows = int(follows or 0)
    profile_visits = int(profile_visits or 0)

    engagement = likes + comments + shares + saves
    engagement_rate = round((engagement / reach) * 100, 2)
    save_rate = round((saves / reach) * 100, 2)
    share_rate = round((shares / reach) * 100, 2)
    follow_rate = round((follows / reach) * 100, 2)
    profile_visit_rate = round((profile_visits / reach) * 100, 2)

    what_worked: List[str] = []
    improve: List[str] = []
    test_next: List[str] = []

    if share_rate >= 1:
        what_worked.append("High share signal. The post was relatable or funny enough for people to send around.")
        test_next.append("Make another version with the same emotional pain point but a sharper punchline.")
    else:
        improve.append("Shares were low. Make the hook more painfully specific or more immediately recognizable.")

    if save_rate >= 1:
        what_worked.append("Good save signal. The post had practical or reusable value.")
        test_next.append("Turn the idea into a carousel or checklist.")
    else:
        improve.append("Saves were low. Add one useful takeaway, checklist, or reminder.")

    if comments >= max(3, reach * 0.002):
        what_worked.append("Comments show conversation potential. This topic may reveal audience pain.")
        test_next.append("Use the comments as prompts for a follow-up post or product angle.")
    else:
        improve.append("Comments were quiet. Ask a simpler, more personal question in the CTA.")

    if follow_rate >= 0.5:
        what_worked.append("Strong follow conversion. The post matched your account identity.")
    else:
        improve.append("Follow conversion could be stronger. Make the account promise clearer in the caption or bio.")

    if profile_visit_rate >= 2:
        what_worked.append("People were curious enough to check your profile.")
    else:
        improve.append("Profile visits were low. Strengthen the first line and make the post feel more connected to your niche.")

    return {
        "post_title": post_title or "Untitled post",
        "post_format": post_format or "unknown",
        "rates": {
            "engagement_rate_percent": engagement_rate,
            "save_rate_percent": save_rate,
            "share_rate_percent": share_rate,
            "follow_rate_percent": follow_rate,
            "profile_visit_rate_percent": profile_visit_rate,
        },
        "what_worked": what_worked or ["No obvious strong signal yet. Treat this as a baseline."],
        "what_to_improve": improve,
        "what_to_test_next": test_next or ["Test a clearer hook, stronger niche reference, and one direct CTA."],
        "recommended_next_post": "Create a follow-up that keeps the same topic but changes the format: meme → carousel or carousel → Reel.",
    }
