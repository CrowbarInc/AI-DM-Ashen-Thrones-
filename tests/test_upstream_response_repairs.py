"""Direct-owner tests for :mod:`game.upstream_response_repairs` (C2 Block B)."""

from __future__ import annotations

import pytest

from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    RETRY_TERMINAL_FALLBACK,
    UPSTREAM_PREPARED_EMISSION,
)
from game.upstream_response_repairs import (
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    UPSTREAM_PREPARED_EMISSION_KEY,
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
    UPSTREAM_PREPARED_OPENING_FALLBACK_ORIGIN,
    build_minimal_action_outcome_contract_repair_text,
    build_upstream_prepared_emission_payload,
    build_upstream_prepared_opening_fallback_payload,
    is_structurally_usable_upstream_prepared_opening_fallback_payload,
    maybe_attach_upstream_prepared_opening_fallback_payload,
    merge_upstream_prepared_emission_into_gm_output,
)
from tests.helpers.final_emission_gate_fixtures import (
    EXPECTED_FRONTIER_GATE_OPENING_FALLBACK,
    opening_gm_output,
)
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_RESULT_META_FIELD_NAMES

pytestmark = pytest.mark.unit


def _assert_upstream_prepared_family(payload: dict) -> None:
    family = payload.get(REALIZATION_FALLBACK_FAMILY_FIELD)
    assert family == UPSTREAM_PREPARED_EMISSION
    assert family in FALLBACK_FAMILIES
    assert family != GATE_TERMINAL_REPAIR
    assert family != RETRY_TERMINAL_FALLBACK


def test_build_upstream_payload_includes_answer_action_and_sanitizer_stock() -> None:
    resolution = {
        "kind": "observe",
        "prompt": "I look around.",
        "adjudication": {"answer_type": "needs_concrete_action"},
    }
    session = {"active_scene_id": "tavern"}
    world: dict = {}
    p = build_upstream_prepared_emission_payload(resolution=resolution, session=session, world=world, scene_id="tavern")
    assert "prepared_answer_fallback_text" in p
    assert "prepared_action_fallback_text" in p
    assert p["prepared_sanitizer_empty_fallback_text"]
    assert p.get("upstream_prepared_bundle_origin") == "upstream_response_repairs.build_upstream_prepared_emission_payload"
    assert "concrete" in (p["prepared_answer_fallback_text"] or "").lower()
    _assert_upstream_prepared_family(p)
    line = build_minimal_action_outcome_contract_repair_text(player_input="I open the door", resolution=resolution)
    assert line.lower().startswith("you")


def test_merge_respects_nonempty_caller_override() -> None:
    gm: dict = {
        UPSTREAM_PREPARED_EMISSION_KEY: {"prepared_answer_fallback_text": "OVERRIDE_ANSWER."},
    }
    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "observe", "prompt": "x"},
        session={},
        world=None,
        scene_id="s",
    )
    assert gm[UPSTREAM_PREPARED_EMISSION_KEY]["prepared_answer_fallback_text"] == "OVERRIDE_ANSWER."
    assert gm[UPSTREAM_PREPARED_EMISSION_KEY]["prepared_action_fallback_text"]
    _assert_upstream_prepared_family(gm[UPSTREAM_PREPARED_EMISSION_KEY])


def test_merge_fills_missing_key_from_fresh() -> None:
    gm = {UPSTREAM_PREPARED_EMISSION_KEY: {}}
    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "travel", "prompt": "I go north", "resolved_transition": True},
        session={},
        world=None,
        scene_id="road",
    )
    assert isinstance(gm[UPSTREAM_PREPARED_EMISSION_KEY].get("prepared_action_fallback_text"), str)
    _assert_upstream_prepared_family(gm[UPSTREAM_PREPARED_EMISSION_KEY])


def test_build_upstream_payload_always_labels_prepared_answer_and_action_text() -> None:
    payload = build_upstream_prepared_emission_payload(
        resolution={
            "kind": "question",
            "prompt": "Do I know who sent the seal?",
            "check_request": {"player_prompt": "Roll History to place the seal."},
        },
        session={"active_scene_id": "archive"},
        world={},
        scene_id="archive",
    )

    assert payload["prepared_answer_fallback_text"] == "Roll History to place the seal."
    assert payload["prepared_action_fallback_text"]
    _assert_upstream_prepared_family(payload)


def test_merge_into_empty_gm_output_adds_known_upstream_family() -> None:
    gm: dict = {}
    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "observe", "prompt": "I study the ash marks."},
        session={},
        world={},
        scene_id="courtyard",
    )

    payload = gm[UPSTREAM_PREPARED_EMISSION_KEY]
    assert payload["prepared_answer_fallback_text"]
    assert payload["prepared_action_fallback_text"]
    _assert_upstream_prepared_family(payload)


def test_merge_normalizes_existing_payload_missing_family_to_upstream_prepared_emission() -> None:
    gm = {
        UPSTREAM_PREPARED_EMISSION_KEY: {
            "prepared_answer_fallback_text": "Existing answer.",
            "prepared_action_fallback_text": "Existing action.",
        }
    }

    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "observe", "prompt": "I look again."},
        session={},
        world={},
        scene_id="yard",
    )

    payload = gm[UPSTREAM_PREPARED_EMISSION_KEY]
    assert payload["prepared_answer_fallback_text"] == "Existing answer."
    assert payload["prepared_action_fallback_text"] == "Existing action."
    _assert_upstream_prepared_family(payload)


@pytest.mark.parametrize("wrong_family", [GATE_TERMINAL_REPAIR, RETRY_TERMINAL_FALLBACK, "not_a_family"])
def test_merge_normalizes_existing_invalid_or_wrong_family_to_upstream_prepared_emission(
    wrong_family: str,
) -> None:
    gm = {
        UPSTREAM_PREPARED_EMISSION_KEY: {
            "prepared_answer_fallback_text": "Caller answer.",
            REALIZATION_FALLBACK_FAMILY_FIELD: wrong_family,
        }
    }

    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "observe", "prompt": "I check the lock."},
        session={},
        world={},
        scene_id="gatehouse",
    )

    payload = gm[UPSTREAM_PREPARED_EMISSION_KEY]
    assert payload["prepared_answer_fallback_text"] == "Caller answer."
    _assert_upstream_prepared_family(payload)


def test_answer_style_repair_payload_is_labeled_upstream_prepared_emission() -> None:
    payload = build_upstream_prepared_emission_payload(
        resolution={
            "kind": "question",
            "prompt": "Can I tell what this machine does?",
            "adjudication": {"answer_type": "needs_concrete_action"},
        },
        session={},
        world={},
        scene_id="workshop",
    )

    assert "concrete" in str(payload["prepared_answer_fallback_text"]).lower()
    _assert_upstream_prepared_family(payload)


def test_action_outcome_style_repair_payload_is_labeled_upstream_prepared_emission() -> None:
    payload = build_upstream_prepared_emission_payload(
        resolution={
            "kind": "investigate",
            "prompt": "I search the burned desk",
            "state_changes": {"clue_revealed": True},
        },
        session={},
        world={},
        scene_id="study",
    )

    assert "concrete clue" in payload["prepared_action_fallback_text"]
    _assert_upstream_prepared_family(payload)


def test_upstream_prepared_opening_fallback_matches_gate_snapshot_and_family() -> None:
    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY == "upstream_prepared_opening_fallback"
    gm = opening_gm_output()
    payload = build_upstream_prepared_opening_fallback_payload(gm)

    assert payload["prepared_opening_fallback_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert payload["upstream_prepared_opening_fallback_origin"] == UPSTREAM_PREPARED_OPENING_FALLBACK_ORIGIN

    meta = payload["opening_fallback_meta"]
    assert meta["opening_fallback_context_source"] == "opening_curated_facts"
    assert meta["opening_fallback_basis_count"] == 3
    assert meta["opening_fallback_context_missing"] is False
    assert meta["opening_fallback_failed_closed"] is False
    assert meta["opening_curated_facts_present"] is True
    assert meta["opening_curated_facts_source"] == "realization"

    comp = payload["opening_fallback_composition_meta"]
    assert comp["fallback_family_used"] == "scene_opening"
    assert comp["fallback_temporal_frame"] == "first_impression"
    assert comp["opening_fallback_context_source"] == "opening_curated_facts"
    assert comp["opening_fallback_authorship_source"] == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    for key in OPENING_FALLBACK_RESULT_META_FIELD_NAMES:
        assert comp[key] == meta[key]

    fam = payload.get(REALIZATION_FALLBACK_FAMILY_FIELD)
    assert fam == UPSTREAM_PREPARED_EMISSION
    assert fam in FALLBACK_FAMILIES


def test_upstream_prepared_opening_authorship_stamped_only_on_composition_meta() -> None:
    """Success-path authorship is written once on composition meta, not opening_fallback_meta."""
    gm = opening_gm_output()
    payload = build_upstream_prepared_opening_fallback_payload(gm)
    assert "opening_fallback_authorship_source" not in payload["opening_fallback_meta"]
    assert (
        payload["opening_fallback_composition_meta"]["opening_fallback_authorship_source"]
        == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    )


def test_maybe_attach_upstream_opening_payload_scene_opening_with_curated_facts() -> None:
    gm = opening_gm_output()
    maybe_attach_upstream_prepared_opening_fallback_payload(gm, resolution={"kind": "scene_opening", "prompt": "Start."})
    assert gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY]["prepared_opening_fallback_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK


def test_maybe_attach_upstream_opening_skips_non_scene_opening_or_empty_facts() -> None:
    gm = opening_gm_output()
    maybe_attach_upstream_prepared_opening_fallback_payload(gm, resolution={"kind": "observe", "prompt": "Look."})
    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in gm

    gm2 = opening_gm_output()
    gm2["opening_curated_facts"] = []
    gm2["opening_selector_selected_facts"] = []
    maybe_attach_upstream_prepared_opening_fallback_payload(gm2, resolution={"kind": "scene_opening", "prompt": "Start."})
    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in gm2


def test_maybe_attach_upstream_opening_preserves_existing_nonempty_payload() -> None:
    gm = opening_gm_output()
    custom = build_upstream_prepared_opening_fallback_payload(gm)
    custom["prepared_opening_fallback_text"] = "CUSTOM_OPENING_FALLBACK."
    gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = custom
    maybe_attach_upstream_prepared_opening_fallback_payload(gm, resolution={"kind": "scene_opening", "prompt": "Start."})
    assert gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY]["prepared_opening_fallback_text"] == "CUSTOM_OPENING_FALLBACK."


def test_maybe_attach_upstream_opening_replaces_text_only_stub_with_full_snapshot() -> None:
    """Block I: text-only stub is not kept when curated facts can supply a full upstream snapshot."""
    gm = opening_gm_output()
    gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = {"prepared_opening_fallback_text": EXPECTED_FRONTIER_GATE_OPENING_FALLBACK}
    assert not is_structurally_usable_upstream_prepared_opening_fallback_payload(
        gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY]
    )
    maybe_attach_upstream_prepared_opening_fallback_payload(gm, resolution={"kind": "scene_opening", "prompt": "Start."})
    pay = gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY]
    assert is_structurally_usable_upstream_prepared_opening_fallback_payload(pay)
    assert pay["prepared_opening_fallback_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK


def test_block_m_maybe_attach_records_build_failure_on_emission_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    import game.upstream_response_repairs as urr

    gm = opening_gm_output()
    gm.pop(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY, None)

    def boom(_mapping: object) -> dict[str, object]:
        raise RuntimeError("attach build boom")

    monkeypatch.setattr(urr, "build_upstream_prepared_opening_fallback_payload", boom)
    maybe_attach_upstream_prepared_opening_fallback_payload(gm, resolution={"kind": "scene_opening", "prompt": "Start."})
    em = gm["metadata"]["emission_debug"]
    assert em["opening_upstream_prepare_attach_build_failed"] is True
    assert em["opening_upstream_prepare_attach_failure_exc_type"] == "RuntimeError"
    assert em["opening_upstream_prepare_attach_no_usable_payload_after_attempt"] is True
    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in gm


def test_block_m_maybe_attach_success_clears_stale_attach_failure_keys() -> None:
    gm = opening_gm_output()
    gm.pop(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY, None)
    md = gm.setdefault("metadata", {})
    em = md.setdefault("emission_debug", {})
    em["opening_upstream_prepare_attach_build_failed"] = True
    em["opening_upstream_prepare_attach_failure_exc_type"] = "StaleError"
    em["opening_upstream_prepare_attach_no_usable_payload_after_attempt"] = True
    maybe_attach_upstream_prepared_opening_fallback_payload(gm, resolution={"kind": "scene_opening", "prompt": "Start."})
    em2 = gm["metadata"]["emission_debug"]
    assert "opening_upstream_prepare_attach_build_failed" not in em2
    assert "opening_upstream_prepare_attach_failure_exc_type" not in em2
    assert "opening_upstream_prepare_attach_no_usable_payload_after_attempt" not in em2
