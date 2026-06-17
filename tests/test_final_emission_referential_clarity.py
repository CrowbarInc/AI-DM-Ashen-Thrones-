"""Owner tests for referential clarity helper module.

Direct owner for ``game.final_emission_referential_clarity``. Layer enforcement
orchestration lives in ``game.final_emission_visibility_fallback``; gate integration
remains in ``tests/test_final_emission_visibility.py`` and ``tests/test_final_emission_gate.py``.
"""

from __future__ import annotations

from unittest.mock import patch

import game.final_emission_referential_clarity as referential_clarity


def test_build_referential_clarity_violation_sample_caps_at_three() -> None:
    violations = [
        {
            "kind": "ambiguous_entity_reference",
            "token": "he",
            "candidate_entity_ids": ["a"],
            "candidate_aliases": [],
            "sentence_text": f"Line {index}.",
            "offset": index,
        }
        for index in range(5)
    ]

    sample = referential_clarity._build_referential_clarity_violation_sample(violations)

    assert len(sample) == 3
    assert sample[0]["kind"] == "ambiguous_entity_reference"
    assert sample[0]["token"] == "he"


def test_apply_default_referential_clarity_meta_stamps_null_pass_shape() -> None:
    meta: dict = {"other": True}
    referential_clarity._apply_default_referential_clarity_meta(meta, passed=None)

    assert meta["referential_clarity_validation_passed"] is None
    assert meta["referential_clarity_replacement_applied"] is False
    assert meta["referential_clarity_violation_kinds"] == []
    assert meta["referential_clarity_local_substitution_attempted"] is False
    assert meta["referential_clarity_fallback_after_failed_local_repair"] is False


def test_referential_clarity_violations_only_dialogue_attribution_they_detects_tag() -> None:
    violations = [
        {
            "kind": "ambiguous_entity_reference",
            "sentence_text": '"Keep your voice down," they murmur.',
        }
    ]

    assert referential_clarity._referential_clarity_violations_only_dialogue_attribution_they(violations)


def test_try_strict_social_local_pronoun_substitution_repair_replaces_single_pronoun() -> None:
    violations = [
        {
            "kind": "ambiguous_entity_reference",
            "token": "She",
            "candidate_entity_ids": ["runner"],
            "sentence_text": 'She says, "East gate is watched by patrol sentries."',
        }
    ]
    eff_resolution = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner"},
    }

    with (
        patch.object(referential_clarity, "_active_interlocutor_visible_person_like", return_value=True),
        patch.object(referential_clarity, "_strict_social_dialogue_substantive_for_local_ref_repair", return_value=True),
        patch.object(referential_clarity, "validate_player_facing_referential_clarity", return_value={"ok": True}),
        patch.object(referential_clarity, "validate_player_facing_first_mentions", return_value={"ok": True}),
        patch.object(referential_clarity, "validate_player_facing_visibility", return_value={"ok": True}),
    ):
        repaired, dbg = referential_clarity._try_strict_social_local_pronoun_substitution_repair(
            'She says, "East gate is watched by patrol sentries."',
            violations=violations,
            session={},
            scene={},
            world={},
            scene_id="scene_investigate",
            eff_resolution=eff_resolution,
            active_interlocutor="runner",
        )

    assert repaired is not None
    assert repaired.startswith("The Tavern Runner says")
    assert dbg["referential_clarity_local_substitution_applied"] is True
    assert dbg["referential_clarity_local_substitution_token"] == "She"
    assert dbg["referential_clarity_local_substitution_replacement"] == "The Tavern Runner"
