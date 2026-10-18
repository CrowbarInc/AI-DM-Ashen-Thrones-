"""PR-CN contextual visible-figure extraction integrity."""
from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.gm import _extract_visible_figure_candidate, extract_contextual_leads_from_text
from game.response_policy_enforcement import _pick_passive_pressure_source
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world


_TARGET_LINE = "As you watch the scene, a guard leans near the checkpoint, watching the road."


@pytest.mark.parametrize(
    ("line", "expected_subject", "expected_position"),
    [
        ("As you watch the scene, a guard leans against the checkpoint.", "guard", ""),
        ("Looking across the square, you notice a merchant packing away his stall.", "merchant", ""),
        ("Near the bridge, a traveler waits beside a cart.", "traveler", "near the bridge"),
        ("A cloaked figure watches the doorway.", "cloaked figure", ""),
        ("While you survey the road, a rider approaches the distant crossing.", "rider", ""),
    ],
)
def test_pr_cn_positive_visible_figure_controls_exclude_observer_frame(
    line: str,
    expected_subject: str,
    expected_position: str,
) -> None:
    candidate = _extract_visible_figure_candidate(line)

    assert candidate is not None
    assert candidate["subject"] == expected_subject
    assert candidate["position"] == expected_position
    assert candidate["subject"] not in {"as you", "while you", "when you"}


@pytest.mark.parametrize(
    "line",
    [
        "As you watch the scene, rain falls across the road.",
        "Looking around, you see nothing moving.",
        "From where you stand, the gate remains closed.",
        "The wind rattles the shutters.",
        "No guard is visible near the bridge.",
        "The rumor says a guard vanished beyond the ridge.",
    ],
)
def test_pr_cn_negative_controls_do_not_invent_visible_figure_leads(line: str) -> None:
    assert _extract_visible_figure_candidate(line) is None
    assert not any(
        item.get("kind") in {"visible_suspicious_figure", "visible_named_figure", "recent_named_figure"}
        for item in extract_contextual_leads_from_text(line)
    )


def test_pr_cn_target_line_extracts_guard_not_observer_frame() -> None:
    candidate = _extract_visible_figure_candidate(_TARGET_LINE)
    extracted = extract_contextual_leads_from_text(_TARGET_LINE)

    assert candidate is not None
    assert candidate["kind"] == "visible_suspicious_figure"
    assert candidate["subject"] == "guard"
    assert candidate["position"] == "near the checkpoint"
    assert not any(str(item.get("subject") or "") == "as you" for item in extracted if isinstance(item, dict))
    assert any(
        item.get("kind") == "visible_suspicious_figure" and item.get("subject") == "guard"
        for item in extracted
    )


@pytest.mark.integration
def test_pr_cn_persistence_context_and_pressure_use_guard_not_as_you(tmp_path, monkeypatch) -> None:
    _seed_shared_world(tmp_path, monkeypatch)
    scene = copy.deepcopy(storage.load_scene("scene_investigate"))
    scene.pop("_is_canon", None)
    scene["scene"]["visible_facts"] = [
        "A guard leans near the checkpoint, watching the road.",
        "A missing patrol notice curls in the damp beside him.",
    ]
    storage.save_scene(scene)
    captured: list[list] = []
    phase = {"line": "The damp air hangs over the gate as everyone watches everyone else."}

    def _gpt(messages):
        captured.append(messages)
        return _gm_response(phase["line"])

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        assert client.post("/api/chat", json={"text": "I wait."}).status_code == 200
        assert client.post("/api/chat", json={"text": "I hold position and watch."}).status_code == 200
        phase["line"] = "Rain continues to bead on the stone."
        assert client.post("/api/chat", json={"text": "I wait."}).status_code == 200

    runtime = ((storage.load_session().get("scene_runtime") or {}).get("scene_investigate") or {})
    leads = [lead for lead in (runtime.get("recent_contextual_leads") or []) if isinstance(lead, dict)]
    assert not any(str(lead.get("subject") or "") == "as you" for lead in leads)
    guard_leads = [lead for lead in leads if str(lead.get("subject") or "") == "guard"]
    assert guard_leads

    reloaded_leads = [
        lead
        for lead in (((storage.load_session().get("scene_runtime") or {}).get("scene_investigate") or {}).get("recent_contextual_leads") or [])
        if isinstance(lead, dict)
    ]
    assert not any(str(lead.get("subject") or "") == "as you" for lead in reloaded_leads)
    assert any(str(lead.get("subject") or "") == "guard" for lead in reloaded_leads)
    assert "as_you" not in str(captured[-1]).lower()
    assert str(guard_leads[0].get("key") or "").lower() in str(captured[-1]).lower()

    source = _pick_passive_pressure_source(
        {
            "recent_contextual_leads": leads,
            "visible_facts": list((storage.load_scene("scene_investigate").get("scene") or {}).get("visible_facts") or []),
        },
        {},
    )
    assert source.get("source") == "lead_figure"
    assert source.get("subject") == "guard"
