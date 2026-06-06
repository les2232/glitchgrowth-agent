from typing import Dict, List

def classify_single_message(message: str) -> Dict[str, str]:
    text = message.strip()
    low = text.lower()

    if not text:
        category = "empty"
        reply = ""
        next_action = "skip"
    elif any(word in low for word in ["price", "buy", "link", "send", "kit", "template", "prompts", "where can i get"]):
        category = "buyer intent"
        reply = "omg yes 🖤 I’m putting it together now. I can send you the early version/details when it’s ready."
        next_action = "reply manually and add to lead list"
    elif any(word in low for word in ["collab", "collaboration", "partner", "work together"]):
        category = "collaboration opportunity"
        reply = "this sounds interesting! send me a little more about what you’re thinking and I’ll take a look."
        next_action = "review profile/context before replying"
    elif any(word in low for word in ["sponsor", "brand", "paid", "partnership", "media kit"]):
        category = "sponsor opportunity"
        reply = "thank you for reaching out! I’d be happy to look at the details. What campaign or product did you have in mind?"
        next_action = "ask for details and prepare media kit"
    elif any(word in low for word in ["how do i", "help", "question", "can you explain", "stuck"]):
        category = "support question"
        reply = "yes — I can help. What part are you stuck on?"
        next_action = "answer briefly or turn into future content"
    elif any(word in low for word in ["follow me", "promo", "crypto", "forex", "guaranteed", "dm me now"]):
        category = "spam/no reply"
        reply = ""
        next_action = "ignore or delete"
    else:
        category = "fan engagement"
        reply = "no because this is painfully accurate 😭"
        next_action = "reply to strengthen community"

    return {
        "message": text,
        "category": category,
        "suggested_reply": reply,
        "next_action": next_action,
    }

def classify_messages(raw_messages: str) -> List[Dict[str, str]]:
    lines = [line.strip("-• \t") for line in raw_messages.splitlines() if line.strip()]
    if not lines and raw_messages.strip():
        lines = [raw_messages.strip()]
    return [classify_single_message(line) for line in lines]
