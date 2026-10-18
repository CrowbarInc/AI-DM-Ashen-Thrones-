"""PR-BR slice 3: decision-to-narration semantic fidelity.

Deterministic only. No gameplay/model calls.
"""
from __future__ import annotations

from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    audit_narration_against_decision,
    attach_gm_resolution_decision,
)


BASE_SESSION = {
    "active_scene_id": "river_market",
    "bounded_improvisation": {
        "entries": [
            {
                "id": "claim_well_tainted",
                "kind": "npc_claim",
                "category": "uncertain_claim",
                "content": "Mira suspects the market well may be tainted.",
                "scope": "scene",
                "scene_id": "river_market",
                "speaker_id": "mira",
                "epistemic_status": "uncertain",
                "status": "promoted",
                "semantic_identity": {
                    "kind": "npc_claim",
                    "subject": "market_well",
                    "subject_aliases": ["water", "well"],
                    "relation": "condition",
                    "value": "tainted",
                    "value_aliases": ["wrong with the water", "tainted"],
                    "speaker_name": "Mira",
                    "speaker_name_aliases": ["Mira"],
                    "epistemic_status": "uncertain",
                    "authority": "claim_only",
                },
            }
        ],
    },
}
BASE_WORLD = {"npcs": [{"id": "mira", "name": "Mira", "role": "mason"}]}


def _resolution(kind: str = "inspect", target_scene_id: str | None = None) -> dict:
    res = {
        "kind": kind,
        "metadata": {
            "resolution_contract": {
                "contract_id": "slice3_contract",
                "operation": "inspect" if kind != "scene_transition" else "follow",
                "dimensions": ["appearance"],
            }
        },
    }
    if target_scene_id:
        res["target_scene_id"] = target_scene_id
    return res


def _scene(*facts: object) -> dict:
    return {
        "scene": {
            "id": "river_market",
            "summary": "A river market with a bridge, well, warehouse, gate, and mooring.",
            "visible_facts": list(facts),
            "exits": [{"label": "Cross toward River Arch", "target_scene_id": "river_arch"}],
        }
    }


def _decision(scene: dict, *, session: dict | None = None, resolution: dict | None = None) -> dict:
    res = resolution or _resolution()
    attach_gm_resolution_decision(
        res,
        session=session if session is not None else BASE_SESSION,
        scene=scene,
        world=BASE_WORLD,
    )
    return res["metadata"][DECISION_METADATA_KEY]


def _audit(text: str, decision: dict, scene: dict) -> dict:
    corpus = "\n".join(
        item.get("text", "") if isinstance(item, dict) else str(item)
        for item in scene["scene"].get("visible_facts") or []
    )
    return audit_narration_against_decision(text, decision=decision, authored_corpus=corpus)


BRIDGE_COLLAPSED = {
    "text": "The eastern bridge collapsed yesterday.",
    "semantic_identity": {
        "kind": "world_fact",
        "subject": "eastern_bridge",
        "subject_aliases": ["eastern bridge", "crossing", "eastern span"],
        "relation": "status",
        "value": "collapsed",
        "value_aliases": ["collapsed", "gave way", "came down"],
        "qualifiers": {"time": "yesterday", "time_aliases": ["previous day", "yesterday"]},
        "authority": "world_truth",
    },
}


def test_valid_structured_paraphrases_do_not_require_token_overlap():
    scene = _scene(BRIDGE_COLLAPSED)
    decision = _decision(scene)

    for text in (
        "The crossing gave way the previous day.",
        "Yesterday, the eastern span came down.",
    ):
        audit = _audit(text, decision, scene)
        assert audit["hard_valid"] is True, audit
        assert audit["proposed_facts"][0]["semantic_identity"]["value"] == "collapsed"


def test_semantic_strengthening_is_rejected_despite_shared_subject_tokens():
    damaged = {
        "text": "The eastern bridge is damaged.",
        "semantic_identity": {
            "kind": "world_fact",
            "subject": "eastern_bridge",
            "subject_aliases": ["eastern bridge"],
            "relation": "status",
            "value": "damaged",
            "value_aliases": ["damaged"],
            "authority": "world_truth",
        },
    }
    scene = _scene(damaged)
    decision = _decision(scene)

    audit = _audit("The eastern bridge collapsed yesterday.", decision, scene)
    assert audit["hard_valid"] is False
    assert "semantic_strengthening:value" in audit["violations"][0]["reason_codes"]


def test_polarity_inversion_is_rejected_with_high_token_overlap():
    locked = {
        "text": "The cellar door is locked.",
        "semantic_identity": {
            "kind": "world_fact",
            "subject": "cellar_door",
            "subject_aliases": ["cellar door"],
            "relation": "status",
            "value": "locked",
            "value_aliases": ["locked"],
            "authority": "world_truth",
        },
    }
    scene = _scene(locked)
    decision = _decision(scene)

    audit = _audit("The cellar door is unlocked.", decision, scene)
    assert audit["hard_valid"] is False
    assert "semantic_polarity:value" in audit["violations"][0]["reason_codes"]


def test_material_time_location_identity_certainty_and_causality_are_preserved():
    ship = {
        "text": "The ship departed today from the east gate after one unnamed guard saw the signal.",
        "semantic_identity": {
            "kind": "world_fact",
            "subject": "ship",
            "subject_aliases": ["ship"],
            "relation": "departure",
            "value": "departed",
            "value_aliases": ["departed"],
            "qualifiers": {
                "time": "today",
                "location": "east gate",
                "identity": "one unnamed guard",
            },
            "authority": "world_truth",
        },
    }
    damaged = {
        "text": "The side door is damaged.",
        "semantic_identity": {
            "kind": "world_fact",
            "subject": "side_door",
            "subject_aliases": ["side door"],
            "relation": "status",
            "value": "damaged",
            "value_aliases": ["damaged"],
            "authority": "world_truth",
        },
    }
    scene = _scene(ship, damaged)
    decision = _decision(scene)

    invalids = [
        "The ship departed three days ago from the east gate after one unnamed guard saw the signal.",
        "The ship departed today inside the barracks after one unnamed guard saw the signal.",
        "The ship departed today from the east gate after Captain Merrow saw the signal.",
        "The side door is damaged because thieves broke it.",
    ]
    for text in invalids:
        audit = _audit(text, decision, scene)
        assert audit["hard_valid"] is False, audit


def test_epistemic_claim_cannot_promote_to_world_truth_but_paraphrase_is_allowed():
    scene = _scene("Rain darkens the stones.")
    decision = _decision(scene)

    valid = _audit("Mira is not certain, but she suspects something is wrong with the water.", decision, scene)
    assert valid["hard_valid"] is True
    assert valid["proposed_facts"][0]["authority"] == "claim_only"

    promoted = _audit("The well is poisoned.", decision, scene)
    assert promoted["hard_valid"] is False


def test_movement_structured_outcome_allows_flexible_arrival_and_rejects_extra_geography():
    scene = _scene("The market bridge spans the river.")
    resolution = _resolution(kind="scene_transition", target_scene_id="river_arch")
    decision = _decision(scene, resolution=resolution)

    valid = _audit("You cross the market bridge and emerge beneath River Arch.", decision, scene)
    assert valid["hard_valid"] is True

    invalid = _audit("You arrive at River Arch after discovering a hidden trail to the watchtower.", decision, scene)
    assert invalid["hard_valid"] is False
    assert "semantic_overreach:causality" in invalid["violations"][0]["reason_codes"]


def test_incidental_texture_and_legacy_free_text_remain_compatible():
    scene = _scene("The old lintel bears three shallow scratches.")
    decision = _decision(scene)

    incidental = _audit("Rain beads on Mira's sleeve while the market murmurs around you.", decision, scene)
    assert incidental["hard_valid"] is True
    assert incidental["proposed_facts"][0]["authority"] == "bounded_incidental"

    legacy = _audit("The old lintel bears three shallow scratches.", decision, scene)
    assert legacy["hard_valid"] is True
    assert legacy["proposed_facts"][0]["reason_codes"] == ["authored_state_source"]
