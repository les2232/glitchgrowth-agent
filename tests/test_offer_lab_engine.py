import shutil
from pathlib import Path
from uuid import uuid4

import offer_lab_engine


def _workspace_temp_dir():
    path = Path(__file__).parent / ".offer_tmp" / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleanup_temp_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    try:
        path.parent.rmdir()
    except OSError:
        pass


def _sample_offer():
    return {
        "name": "Creator Systems Kit",
        "status": "idea",
        "audience": "AI creators",
        "pain_point": "turning messy ideas into posts",
        "promise": "ship a week of content from one idea",
        "deliverables": "prompts, captions, CTAs, and carousel templates",
        "format": "template pack",
        "price": "$19",
        "cta_keyword": "KIT",
        "checkout_url": "",
        "notes": "early offer",
    }


def test_save_and_load_offer(monkeypatch):
    temp_dir = _workspace_temp_dir()
    offer_path = temp_dir / "offers.json"
    monkeypatch.setattr(offer_lab_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(offer_lab_engine, "OFFERS_PATH", offer_path)

    try:
        saved = offer_lab_engine.save_offer(_sample_offer())
        offers = offer_lab_engine.load_offers()

        assert offer_path.exists()
        assert len(offers) == 1
        assert offers[0]["id"] == saved["id"]
        assert offers[0]["name"] == "Creator Systems Kit"
    finally:
        _cleanup_temp_dir(temp_dir)


def test_update_search_and_archive_offer(monkeypatch):
    temp_dir = _workspace_temp_dir()
    offer_path = temp_dir / "offers.json"
    monkeypatch.setattr(offer_lab_engine, "DATA_DIR", temp_dir)
    monkeypatch.setattr(offer_lab_engine, "OFFERS_PATH", offer_path)

    try:
        saved = offer_lab_engine.save_offer(_sample_offer())
        updated = offer_lab_engine.update_offer(saved["id"], {"status": "ready", "price": "$29"})
        results = offer_lab_engine.search_offers("messy", status="ready", format="template pack")
        archived = offer_lab_engine.archive_offer(saved["id"])

        assert updated["status"] == "ready"
        assert updated["price"] == "$29"
        assert len(results) == 1
        assert results[0]["id"] == saved["id"]
        assert archived["status"] == "archived"
    finally:
        _cleanup_temp_dir(temp_dir)


def test_generate_launch_pack_expected_fields():
    pack = offer_lab_engine.generate_launch_pack(_sample_offer(), tone_tags=["chaotic", "useful"])

    expected_fields = {
        "offer_positioning_summary",
        "audience_pain_summary",
        "launch_post",
        "soft_sell_post",
        "urgency_final_call_post",
        "story_slides",
        "comment_ctas",
        "dm_reply_templates",
        "short_faq",
        "common_objections_replies",
        "recommended_first_week_posting_plan",
    }
    assert expected_fields.issubset(pack.keys())
    assert len(pack["story_slides"]) == 5
    assert len(pack["comment_ctas"]) == 3
    assert len(pack["dm_reply_templates"]) == 3
