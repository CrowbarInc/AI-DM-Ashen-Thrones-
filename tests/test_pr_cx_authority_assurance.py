"""PR-CX reduced-context authority assurance. Deterministic, no provider calls."""
from __future__ import annotations

import json

import pytest

import game.gm as gm
from game.immutable_valid_response import run_preserve_if_valid
from game.proposition_authority import CONSEQUENTIAL_KIND, classify_propositions
from tests.test_pr_cw_social_context_projection import POSITIVE_CONTROLS, _REAL_PROJECTOR, social_request


VIOLATION_CANDIDATES = (
    ("biography", "The guard captain was born in Blackharbor and served for twenty years.", "biography"),
    ("geography", "The old milestone lies east beyond the trading crossroads.", "geography"),
    ("hidden_information", "A secret tunnel runs beneath the gate into the keep.", "hidden_information"),
    ("npc_action", "The captain unlocks the gate and lets you pass.", "npc_action"),
    ("discovery", "You discover a hidden map beneath the notice board.", "discovery"),
)

PERMITTED_CANDIDATES = (
    ("preference", 'The guard captain says, "I prefer a dry watch."'),
    ("opinion", 'The guard captain says, "I like the square best after rain."'),
    ("incidental_characterization", "The guard captain shrugs and nods."),
    ("grounded_observation", "A notice board lists new taxes, curfews, and a posted warning about a missing patrol."),
)


def _seal(text: str, *, projection_enabled: bool, monkeypatch: pytest.MonkeyPatch) -> dict:
    monkeypatch.setattr(
        gm,
        "_project_harmless_social_provider_context",
        _REAL_PROJECTOR if projection_enabled else lambda payload, **kwargs: payload,
    )
    messages, resolution, scene, world, session = social_request(POSITIVE_CONTROLS[0][2])
    if projection_enabled:
        assert "provider_context_projection" in json.loads(messages[1]["content"])
    candidate = gm._safe_json(
        json.dumps({"narration": text}),
        require_structured_claims=True,
        provider_response_contract="narration_only",
    )
    return run_preserve_if_valid(
        candidate,
        regenerate=None,
        resolution=resolution,
        player_text=POSITIVE_CONTROLS[0][2],
        scene=scene,
        world=world,
        session=session,
    )


@pytest.mark.parametrize("label,text,family", VIOLATION_CANDIDATES)
def test_pr_cx_rejects_inherited_objective_authority_violations(label, text, family, monkeypatch):
    proposition_rows = classify_propositions(text)
    assert any(row["kind"] == CONSEQUENTIAL_KIND and row["family"] == family for row in proposition_rows)

    audits = []
    outputs = []
    for projection_enabled in (False, True):
        sealed = _seal(text, projection_enabled=projection_enabled, monkeypatch=monkeypatch)
        audit = sealed["metadata"]["hard_validation_attempt_1"]
        audits.append(audit)
        outputs.append(sealed["player_facing_text"])
        assert audit["hard_valid"] is False, (label, audit)
        assert "unauthorized_resolution_decision_fact" in audit["reasons"]
        assert sealed["player_facing_text"] != text

    assert audits[0] == audits[1]
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("label,text", PERMITTED_CANDIDATES)
def test_pr_cx_preserves_harmless_dialogue_and_grounded_observation(label, text, monkeypatch):
    audits = []
    for projection_enabled in (False, True):
        sealed = _seal(text, projection_enabled=projection_enabled, monkeypatch=monkeypatch)
        audit = sealed["metadata"]["hard_validation_attempt_1"]
        audits.append(audit)
        assert audit["hard_valid"] is True, (label, audit)
        assert sealed["player_facing_text"] == text
    assert audits[0] == audits[1]
