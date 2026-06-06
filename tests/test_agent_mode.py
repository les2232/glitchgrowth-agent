import agent_mode


def _fake_batch():
    return {
        "posts": [
            {
                "format": "meme",
                "goal": "lead capture",
                "content": {
                    "type": "meme_post",
                    "title": "High score post",
                    "caption": "Specific AI workflow caption.",
                    "cta": "comment KIT",
                },
            },
            {
                "format": "carousel",
                "goal": "growth",
                "content": {
                    "type": "carousel",
                    "title": "Low score post",
                    "caption": "Generic caption.",
                    "cta": "",
                },
            },
        ]
    }


def test_agent_mode_summary_fields_exist(monkeypatch):
    queued = []

    monkeypatch.setattr(agent_mode, "generate_weekly_batch", lambda *args, **kwargs: _fake_batch())
    monkeypatch.setattr(agent_mode, "score_content", lambda packet: {"overall_score": 80, "detected_issues": [], "improvement_suggestions": []})
    monkeypatch.setattr(agent_mode, "save_to_library", lambda packet: {"id": packet["title"], "title": packet["title"], "caption": packet.get("caption", ""), "cta": packet.get("cta", "")})
    monkeypatch.setattr(agent_mode, "add_to_queue", lambda item: queued.append(item) or {"queue_id": f"queue-{len(queued)}"})

    summary = agent_mode.run_weekly_agent_mode("AI week", "Creator Kit", "daily")

    assert set(summary.keys()) == {
        "generated_count",
        "saved_to_library_count",
        "queued_count",
        "needs_revision_count",
        "average_quality_score",
        "queued_items",
        "revision_items",
        "planned_schedule",
    }


def test_agent_mode_queues_high_score_items(monkeypatch):
    queued = []

    monkeypatch.setattr(agent_mode, "generate_weekly_batch", lambda *args, **kwargs: _fake_batch())
    monkeypatch.setattr(agent_mode, "score_content", lambda packet: {"overall_score": 90, "detected_issues": [], "improvement_suggestions": []})
    monkeypatch.setattr(agent_mode, "save_to_library", lambda packet: {"id": packet["title"], "title": packet["title"], "caption": packet.get("caption", ""), "cta": packet.get("cta", "")})
    monkeypatch.setattr(agent_mode, "add_to_queue", lambda item: queued.append(item) or {"queue_id": f"queue-{len(queued)}"})

    summary = agent_mode.run_weekly_agent_mode("AI week", "Creator Kit", "daily", minimum_quality_score=75)

    assert summary["queued_count"] == 2
    assert summary["needs_revision_count"] == 0
    assert len(queued) == 2
    assert queued[0]["planned_date"]
    assert queued[0]["planned_time"] == "09:00"


def test_agent_mode_does_not_queue_low_score_items(monkeypatch):
    queued = []

    monkeypatch.setattr(agent_mode, "generate_weekly_batch", lambda *args, **kwargs: _fake_batch())
    monkeypatch.setattr(agent_mode, "score_content", lambda packet: {"overall_score": 40, "detected_issues": ["Weak hook"], "improvement_suggestions": ["Make it specific"]})
    monkeypatch.setattr(agent_mode, "save_to_library", lambda packet: {"id": packet["title"], "title": packet["title"], "caption": packet.get("caption", ""), "cta": packet.get("cta", "")})
    monkeypatch.setattr(agent_mode, "add_to_queue", lambda item: queued.append(item) or {"queue_id": f"queue-{len(queued)}"})

    summary = agent_mode.run_weekly_agent_mode("AI week", "Creator Kit", "daily", minimum_quality_score=75)

    assert summary["queued_count"] == 0
    assert summary["needs_revision_count"] == 2
    assert queued == []
    assert summary["revision_items"][0]["issues"] == ["Weak hook"]
