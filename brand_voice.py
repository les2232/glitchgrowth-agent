import json
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path(__file__).parent / "data"
BRAND_VOICE_PATH = DATA_DIR / "brand_voice.json"

DEFAULT_BRAND_VOICE: Dict[str, Any] = {
    "name": "GlitchGrowth",
    "account_style": [
        "funny",
        "chaotic",
        "tech-savvy",
        "slightly flirty",
        "emotionally relatable",
        "meme-heavy",
        "beginner-friendly but smart",
    ],
    "topics": [
        "IT support chaos",
        "AI news",
        "creator tools",
        "automation",
        "internet culture",
        "women in tech",
        "productivity systems",
    ],
    "voice_rules": [
        "Sound like a funny creator, not a corporate brand.",
        "Use specific tech details when it makes the joke sharper.",
        "Keep sales CTAs soft and human.",
        "Prefer practical, ready-to-post content.",
        "Do not use spammy growth tactics.",
    ],
    "default_offer": "Chaotic Tech Creator Kit",
}

def load_brand_voice() -> Dict[str, Any]:
    if not BRAND_VOICE_PATH.exists():
        save_brand_voice(DEFAULT_BRAND_VOICE)
        return DEFAULT_BRAND_VOICE.copy()

    with BRAND_VOICE_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_brand_voice(profile: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with BRAND_VOICE_PATH.open("w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)
