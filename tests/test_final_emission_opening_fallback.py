"""Owner tests for opening adapter result semantics.

This module owns prepared-payload selection, sealed fail-closed metadata,
adapter-level opening ownership fields, attach-then-helper fixture semantics,
response-type helper bypass behavior for ``game.final_emission_opening_fallback``,
opening mode detection / visible-anchor candidate text for
``game.final_emission_opening_mode``, and full-gate opening fallback integration
(BH-1). Gate-order pin for upstream attach-before-composer remains in
``tests/test_final_emission_gate.py`` (Block L).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping

import pytest

import game.final_emission_non_strict_stack as non_strict_stack
import game.final_emission_response_type as response_type
import game.final_emission_opening_fallback as opening_fallback
import game.final_emission_opening_mode as opening_mode
import game.final_emission_validators as opening_validators
import game.opening_deterministic_fallback as opening_deterministic_fallback
from game.defaults import default_scene, default_session, default_world
from game.diegetic_fallback_narration import fallback_template_metadata
from game.final_emission_gate import apply_final_emission_gate
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output as read_final_emission_meta_dict
from game.attribution_read_views import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
import game.final_emission_visibility_fallback as visibility_fallback
from game.interaction_context import rebuild_active_scene_entities
from game.narrative_mode_contract import build_narrative_mode_contract
from game.opening_deterministic_fallback import (
    OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER,
    deterministic_opening_fallback_text_and_meta,
    deterministic_opening_fallback_text_and_meta as _deterministic_opening_under_test,
)
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    LEGACY_DIEGETIC_FALLBACK,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    UPSTREAM_PREPARED_EMISSION,
)
from game.upstream_response_repairs import (
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
    build_upstream_prepared_opening_fallback_payload,
)
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.response_type_smoke import response_type_contract
from tests.helpers.opening_fallback_evidence import (
    EXPECTED_FRONTIER_GATE_OPENING_FALLBACK,
    OPENING_FAILED_CLOSED_REPAIR_KIND,
    OPENING_FALLBACK_FAMILY,
    OPENING_SUCCESS_REPAIR_KIND,
    OPENING_SUCCESS_SOURCE,
    assert_fallback_owner_bucket,
    assert_final_emission_meta_contains,
    assert_opening_fallback_authorship,
    assert_opening_fallback_fail_closed,
    assert_opening_fallback_family_temporal,
    assert_opening_fallback_source,
    assert_opening_fallback_upstream_prepared,
    legacy_compatibility_local_opening_authorship_source,
    opening_gm_output,
    opening_owner_bucket_projection_fields,
    opening_upstream_composition_meta_slice,
    opening_validation_context,
    successful_opening_fem_meta,
)
from tests.helpers.opening_fallback_gate_harness import (
    opening_gate_attach_then_enforce_response_type_contract,
    opening_gate_attach_then_opening_scene_safe_fallback_selection,
)


pytestmark = pytest.mark.unit

PREPARED_TEXT = "Rain glints on the checkpoint stones while a queue waits beneath the gate."


def _fail_closed_composition_meta() -> Dict[str, Any]:
    return {
        "first_mention_composition_used": False,
        "first_mention_composition_layers": {"environment": None, "motion": None, "entities": []},
    }


def _prepared_payload() -> Dict[str, Any]:
    return {
        "prepared_opening_fallback_text": PREPARED_TEXT,
        "opening_fallback_meta": {"opening_fallback_failed_closed": False},
        "opening_fallback_composition_meta": opening_upstream_composition_meta_slice(),
    }


def _select(gm_output: Dict[str, Any]) -> VisibilitySelectedFallback:
    return opening_fallback.opening_scene_safe_fallback_selection(
        gm_output,
        fail_closed_composition_meta_factory=_fail_closed_composition_meta,
    )


def _assert_owner_bucket(meta: Dict[str, Any], *, repair_kind: str, expected: str) -> None:
    assert_fallback_owner_bucket(
        expected,
        from_fields=opening_owner_bucket_projection_fields(meta, repair_kind=repair_kind),
    )


def test_opening_scene_safe_fallback_selection_returns_canonical_dataclass_and_metadata() -> None:
    """Dataclass selection preserves replay-facing composition meta without tuple wire."""
    prepared_gm = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: _prepared_payload()}
    fail_closed_gm = {"opening_curated_facts": ["Rain needles the stones at the gate."]}
    for gm_output in (prepared_gm, fail_closed_gm):
        selected = opening_fallback.opening_scene_safe_fallback_selection(
            gm_output,
            fail_closed_composition_meta_factory=_fail_closed_composition_meta,
        )
        assert isinstance(selected, VisibilitySelectedFallback)
        assert selected.fallback_pool == "scene_opening_deterministic"
        assert selected.fallback_kind == OPENING_SUCCESS_SOURCE
        assert selected.final_emitted_source == OPENING_SUCCESS_SOURCE
        assert selected.fallback_strategy == "opening_scene_safe_fallback"
        assert selected.fallback_candidate_source == OPENING_SUCCESS_SOURCE
        meta = dict(selected.composition_meta)
        if gm_output is prepared_gm:
            assert selected.text == PREPARED_TEXT
            assert meta.get("opening_fallback_authorship_source") == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
        else:
            assert selected.text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
            assert meta.get("opening_fallback_compatibility_local_disabled") is True
            assert meta.get("opening_fallback_authorship_source") is None
            assert meta.get("opening_fallback_failed_closed") is True


def test_adapter_selects_usable_upstream_prepared_payload_unchanged() -> None:
    payload = _prepared_payload()
    gm_output = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: payload}

    selected = opening_fallback.opening_scene_safe_fallback_selection(
        gm_output,
        fail_closed_composition_meta_factory=lambda: pytest.fail("prepared selection must not build fail-closed meta"),
    )

    assert selected.text == PREPARED_TEXT
    assert (
        selected.fallback_pool,
        selected.fallback_kind,
        selected.final_emitted_source,
        selected.fallback_strategy,
        selected.fallback_candidate_source,
    ) == (
        "scene_opening_deterministic",
        OPENING_SUCCESS_SOURCE,
        OPENING_SUCCESS_SOURCE,
        "opening_scene_safe_fallback",
        OPENING_SUCCESS_SOURCE,
    )
    meta = dict(selected.composition_meta)
    expected = dict(payload["opening_fallback_composition_meta"])
    for key, value in expected.items():
        assert meta[key] == value
    assert meta is not payload["opening_fallback_composition_meta"]
    assert_opening_fallback_authorship(meta, OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED)
    assert meta.get("opening_fallback_owner_bucket") == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    _assert_owner_bucket(meta, repair_kind=selected.fallback_kind, expected=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED)


def test_select_mirrors_authorship_from_upstream_composition_meta() -> None:
    gm_output = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: _prepared_payload()}
    _text, meta, _stub, selected, _upstream = (
        opening_fallback.select_opening_fallback_for_response_type_contract(gm_output)
    )
    assert selected is True
    assert_opening_fallback_authorship(meta, OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED)


def test_select_does_not_infer_authorship_when_composition_meta_lacks_field() -> None:
    payload = _prepared_payload()
    composition = dict(payload["opening_fallback_composition_meta"])
    composition.pop("opening_fallback_authorship_source", None)
    payload["opening_fallback_composition_meta"] = composition
    gm_output = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: payload}
    _text, meta, _stub, selected, _upstream = (
        opening_fallback.select_opening_fallback_for_response_type_contract(gm_output)
    )
    assert selected is True
    assert "opening_fallback_authorship_source" not in meta


def test_adapter_missing_upstream_payload_fails_closed_with_existing_metadata_shape() -> None:
    selected = _select({"opening_curated_facts": ["Rain needles the stones at the gate."]})

    assert selected.text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    assert selected.fallback_kind == OPENING_SUCCESS_SOURCE
    meta = dict(selected.composition_meta)
    assert_opening_fallback_fail_closed(
        meta,
        assert_owner_via_projection=True,
        include_family_temporal=True,
        opening_fallback_missing_upstream_prepared_payload=True,
        opening_fallback_missing_curated_facts=False,
        opening_fallback_basis_count=1,
    )


def test_adapter_insufficient_curated_facts_fails_closed_with_existing_metadata_shape() -> None:
    selected = _select({"opening_curated_facts": []})

    assert selected.text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    meta = dict(selected.composition_meta)
    assert_opening_fallback_fail_closed(
        meta,
        assert_owner_via_projection=True,
        opening_fallback_missing_upstream_prepared_payload=True,
        opening_fallback_compatibility_local_disabled=True,
        opening_fallback_context_missing=True,
        opening_curated_facts_present=False,
        opening_curated_facts_count=0,
    )


def test_opening_fallback_fail_closed_paths_never_stamp_compatibility_local_authorship() -> None:
    """Production selection paths never stamp retired compatibility-local authorship."""
    prepared_gm = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: _prepared_payload()}
    fail_closed_cases = (
        {"opening_curated_facts": []},
        {"opening_curated_facts": ["Rain needles the stones at the gate."]},
        {
            "opening_curated_facts": ["Rain needles the stones at the gate."],
            UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: {"prepared_opening_fallback_text": PREPARED_TEXT},
        },
    )
    for gm_output in fail_closed_cases:
        selected = _select(gm_output)
        meta = dict(selected.composition_meta)
        assert_opening_fallback_authorship(meta, None)
        assert meta.get("opening_fallback_failed_closed") is True
        assert meta.get("opening_fallback_compatibility_local_disabled") is True

    prepared = _select(prepared_gm)
    assert_opening_fallback_authorship(
        prepared.composition_meta,
        OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    )


def test_canonical_opening_paths_never_emit_either_legacy_compat_local_authorship_token() -> None:
    """Production canonical opening paths must not stamp either legacy compat-local authorship token."""
    from game.attribution_read_views import (
        OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES,
        OPENING_FALLBACK_RETIRED_SHORT_COMPATIBILITY_LOCAL_AUTHORSHIP,
    )

    forbidden = frozenset(OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES) | frozenset(
        {OPENING_FALLBACK_RETIRED_SHORT_COMPATIBILITY_LOCAL_AUTHORSHIP}
    )

    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = final_emission_meta_from_output(out)
    authorship = fem.get("opening_fallback_authorship_source")
    assert authorship is not None
    assert authorship not in forbidden
    assert authorship == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED


def test_opening_fallback_compatibility_local_disabled_is_telemetry_not_authorship() -> None:
    """Disabled flags are telemetry-only; they must not co-occur with legacy compat-local authorship."""
    from game.attribution_read_views import (
        OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES,
        OPENING_FALLBACK_RETIRED_SHORT_COMPATIBILITY_LOCAL_AUTHORSHIP,
    )
    from game.final_emission_opening_fallback import (
        OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY,
        OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY,
    )

    forbidden = frozenset(OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES) | frozenset(
        {OPENING_FALLBACK_RETIRED_SHORT_COMPATIBILITY_LOCAL_AUTHORSHIP}
    )

    selected = _select({"opening_curated_facts": []})
    meta = dict(selected.composition_meta)
    assert meta.get(OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY) is True
    assert meta.get(OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY) is True
    authorship = meta.get("opening_fallback_authorship_source")
    assert authorship is None or authorship not in forbidden


def test_opening_fallback_fail_closed_diagnostic_keys_are_classified_and_constant_aligned() -> None:
    """Fail-closed diagnostic keys are explicitly registered and writer constants stay aligned."""
    from game.observability_attribution_read import (
        OPENING_FALLBACK_EMITTED_METADATA_FIELDS,
        OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS,
        opening_fallback_metadata_classification_parity_errors,
    )
    from game.final_emission_opening_fallback import (
        OPENING_FALLBACK_MISSING_CURATED_FACTS_KEY,
        OPENING_FALLBACK_MISSING_UPSTREAM_PREPARED_PAYLOAD_KEY,
        OPENING_FALLBACK_UPSTREAM_PAYLOAD_RECOVERED_KEY,
        OPENING_FALLBACK_UPSTREAM_PAYLOAD_UNUSABLE_KEY,
    )

    assert opening_fallback_metadata_classification_parity_errors() == []
    assert frozenset(OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS) == frozenset(
        {
            OPENING_FALLBACK_MISSING_UPSTREAM_PREPARED_PAYLOAD_KEY,
            OPENING_FALLBACK_MISSING_CURATED_FACTS_KEY,
            OPENING_FALLBACK_UPSTREAM_PAYLOAD_UNUSABLE_KEY,
            OPENING_FALLBACK_UPSTREAM_PAYLOAD_RECOVERED_KEY,
        }
    )
    assert frozenset(OPENING_FALLBACK_FAIL_CLOSED_DIAGNOSTIC_FIELDS).issubset(
        OPENING_FALLBACK_EMITTED_METADATA_FIELDS
    )

    missing_payload = _select({"opening_curated_facts": ["Rain needles the stones at the gate."]})
    meta = dict(missing_payload.composition_meta)
    assert meta[OPENING_FALLBACK_MISSING_UPSTREAM_PREPARED_PAYLOAD_KEY] is True
    assert meta[OPENING_FALLBACK_MISSING_CURATED_FACTS_KEY] is False


def test_opening_fallback_local_composition_disabled_quarantined_from_fem_rtd_merge() -> None:
    """Both disabled keys co-stamp composition_meta; only canonical key RTD-merges into FEM."""
    from game.observability_attribution_read import (
        OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS,
        merge_response_type_meta,
    )
    from game.final_emission_opening_fallback import (
        OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY,
        OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY,
    )

    assert OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY not in (
        OPENING_FALLBACK_OUT_OF_BAND_TELEMETRY_RTD_MERGE_FIELDS
    )

    selected = _select({"opening_curated_facts": []})
    composition = dict(selected.composition_meta)
    assert composition[OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY] is True
    assert composition[OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY] is True

    fem_from_merge: dict = {}
    merge_response_type_meta(fem_from_merge, composition)
    assert fem_from_merge.get(OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY) is True
    assert OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY not in fem_from_merge

    gm = {
        "response_policy": {"response_type_contract": response_type_contract("scene_opening")},
        "opening_curated_facts": [],
        "player_facing_text": "Nearby crates appear disturbed.",
        "tags": [],
    }
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="empty_opening",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get(OPENING_FALLBACK_COMPATIBILITY_LOCAL_DISABLED_KEY) is True
    assert OPENING_FALLBACK_LOCAL_COMPOSITION_DISABLED_KEY not in fem


def test_adapter_unusable_upstream_stub_preserves_fail_closed_metadata() -> None:
    selected = _select(
        {
            "opening_curated_facts": ["Rain needles the stones at the gate."],
            UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: {"prepared_opening_fallback_text": PREPARED_TEXT},
        }
    )

    assert selected.text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    meta = dict(selected.composition_meta)
    assert_opening_fallback_fail_closed(
        meta,
        assert_owner_via_projection=True,
        opening_fallback_upstream_payload_unusable=True,
        opening_fallback_upstream_payload_recovered=False,
        opening_fallback_missing_upstream_prepared_payload=False,
        opening_fallback_compatibility_local_disabled=True,
    )


def test_adapter_does_not_export_prose_authorship_or_payload_packaging() -> None:
    assert not hasattr(opening_fallback, "deterministic_opening_fallback_text_and_meta")
    assert not hasattr(opening_fallback, "build_upstream_prepared_opening_fallback_payload")


def test_upstream_prepared_opening_payload_if_usable_requires_full_snapshot_shape() -> None:
    assert opening_fallback._upstream_prepared_opening_fallback_payload_if_usable(None) is None
    assert opening_fallback._upstream_prepared_opening_fallback_payload_if_usable({}) is None
    partial_text_only = {
        UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: {"prepared_opening_fallback_text": "Some opening."},
    }
    assert opening_fallback._upstream_prepared_opening_fallback_payload_if_usable(partial_text_only) is None
    gm = opening_gm_output()
    built = build_upstream_prepared_opening_fallback_payload(gm)
    gm_attached = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: built}
    usable = opening_fallback._upstream_prepared_opening_fallback_payload_if_usable(gm_attached)
    assert isinstance(usable, dict)
    assert usable["prepared_opening_fallback_text"].strip()


def test_fail_closed_empty_curated_facts_skips_local_deterministic_opening_composer_on_enforce_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gm = {
        "response_policy": {"response_type_contract": response_type_contract("scene_opening")},
        "opening_curated_facts": [],
    }

    def _boom(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("local deterministic opening must not run on fail-closed path")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _boom)
    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="empty_opening",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert text.startswith("[opening_fallback_failed_closed:")
    assert dbg.get("opening_fallback_compatibility_local_disabled") is True


def test_opening_scene_safe_fallback_selection_skips_local_composer_when_empty_curated_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gm = {
        "response_policy": {"response_type_contract": response_type_contract("scene_opening")},
        "opening_curated_facts": [],
    }

    def _boom(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("local deterministic opening must not run on fail-closed path")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _boom)
    selected = opening_fallback.opening_scene_safe_fallback_selection(
        gm,
        fail_closed_composition_meta_factory=_fail_closed_composition_meta,
    )
    assert selected.text.startswith("[opening_fallback_failed_closed:")
    assert selected.composition_meta.get("opening_fallback_compatibility_local_disabled") is True


def test_deterministic_opening_fallback_helper_exact_text_and_meta_snapshot() -> None:
    text, meta = deterministic_opening_fallback_text_and_meta(opening_gm_output())

    assert text == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert meta["opening_fallback_context_source"] == "opening_curated_facts"
    assert meta["opening_fallback_basis_count"] == 3
    assert meta["opening_fallback_context_missing"] is False
    assert meta["opening_fallback_failed_closed"] is False
    assert meta["opening_curated_facts_present"] is True
    assert meta["opening_curated_facts_source"] == "realization"
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in meta


def test_canonical_opening_failure_recovers_via_upstream_prepared_payload_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gm = opening_gm_output()
    gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = build_upstream_prepared_opening_fallback_payload(gm)

    def _should_not_run_local_deterministic_opening(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("local deterministic opening must not run when upstream payload is present")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _should_not_run_local_deterministic_opening)
    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert dbg.get("response_type_repair_kind") == OPENING_SUCCESS_REPAIR_KIND
    assert dbg[REALIZATION_FALLBACK_FAMILY_FIELD] == UPSTREAM_PREPARED_EMISSION
    assert_opening_fallback_upstream_prepared(
        dbg,
        final_emitted_source=None,
        opening_recovered_via_fallback=True,
        fallback_family_used=OPENING_FALLBACK_FAMILY,
    )


def test_gate_opening_failure_text_only_stub_fails_closed_without_rebuild(monkeypatch: pytest.MonkeyPatch) -> None:
    gm = opening_gm_output()
    gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = {"prepared_opening_fallback_text": EXPECTED_FRONTIER_GATE_OPENING_FALLBACK}

    calls: list[int] = []

    def _counting_local_deterministic_opening(*a: Any, **k: Any) -> tuple[str, dict]:
        calls.append(1)
        return deterministic_opening_fallback_text_and_meta(*a, **k)

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _counting_local_deterministic_opening)
    text, dbg = response_type.enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert calls == []
    assert text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    assert dbg.get("response_type_repair_kind") == OPENING_FAILED_CLOSED_REPAIR_KIND
    assert_opening_fallback_fail_closed(dbg)


def test_valid_scene_opening_skips_deterministic_fallback() -> None:
    candidate = (
        "You stand in the churned mud before Cinderwatch's eastern gate as rain spatters soot-dark stone "
        "and frayed banners snap above you. Refugees press shoulder to shoulder around the wagon line "
        "while guards hold the choke under shouted orders."
    )
    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        candidate,
        opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == candidate
    assert dbg.get("opening_fallback_skipped") is True
    assert dbg.get("response_type_repair_used") is False
    assert dbg.get("response_type_repair_kind") is None
    assert dbg.get("opening_repair_source") in {
        "preserved_candidate",
        "preserved_candidate_validity_check",
    }
    assert dbg.get("fallback_family_used") is None
    assert dbg.get(REALIZATION_FALLBACK_FAMILY_FIELD) is None
    assert dbg.get("opening_fallback_authorship_source") is None


def test_scene_opening_candidate_not_rejected_for_lacking_action_result_language() -> None:
    gm = opening_gm_output()
    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        (
            "Cinderwatch Gate District gathers rain, refugees, wagons, guards, and torchlight "
            "around the eastern gate. You can read the notice board or approach the guards."
        ),
        gm,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Cinderwatch Gate District" in text
    assert dbg.get("response_type_required") == "scene_opening"
    assert dbg.get("response_type_candidate_ok") is True
    assert "action_outcome_missing_result" not in dbg.get("response_type_rejection_reasons")
    assert dbg.get("response_type_repair_used") is False


def test_scene_opening_fallback_with_opening_seed_facts_emits_seed_facts() -> None:
    curated = [
        "Ash Quay crouches under black rain and lantern smoke.",
        "Dock guards hold a shouting crowd behind a rope line.",
        "A brass notice board points newcomers toward the harbor clerk.",
    ]
    gm_output = {
        "response_policy": {"response_type_contract": response_type_contract("scene_opening")},
        "opening_curated_facts": list(curated),
        "prompt_context": {
            "opening_inputs_are_curated": True,
            "narration_obligations": {"is_opening_scene": True},
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Ash Quay"]},
                "scene_anchors": {"location_anchors": ["Ash Quay"]},
            },
            "scene": {
                "public": {
                    "id": "ash_quay",
                    "location": "Ash Quay",
                    "opening_seed_facts": [
                        "This opening_seed_facts line must not be the fallback source.",
                    ],
                }
            },
        },
    }

    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="ash_quay",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Ash Quay crouches under black rain" in text
    assert "Dock guards hold a shouting crowd" in text
    assert "brass notice board" in text
    assert "opening_seed_facts line" not in text
    # Emission-debug curated-context stamps: scenario diagnostic locks (meta vs dbg sinks differ by test).
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"
    assert dbg.get("opening_fallback_basis_count") == 3
    assert dbg.get("opening_fallback_failed_closed") is False


def test_scene_opening_fallback_prefers_opening_curated_facts() -> None:
    curated = [
        "Glass rain hangs over the Argent Court hall's silent balconies.",
        "Court guards keep a velvet rope across the marble stair.",
        "A silver notice board names the first petitioners for the morning.",
    ]
    gm_output = opening_gm_output()
    gm_output["opening_curated_facts"] = curated
    gm_output["metadata"]["emission_debug"]["opening_curated_facts_count"] = len(curated)
    gm_output["metadata"]["emission_debug"]["opening_curated_facts_source"] = "realization"
    gm_output["prompt_context"]["narration_visibility"]["visible_facts"] = [
        "This narration_visibility fact should not be used while curated facts exist."
    ]

    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="argent_court",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Argent Court hall's silent balconies" in text
    assert "velvet rope" in text
    assert "should not be used" not in text
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"
    assert dbg.get("opening_curated_facts_present") is True
    assert dbg.get("opening_curated_facts_count") == 3
    assert dbg.get("opening_curated_facts_source") == "realization"
    assert dbg.get("opening_fallback_failed_closed") is False


def test_opening_failure_fallback_classification_excludes_observe_family() -> None:
    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "A bad response type.",
        opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    repair_kind = str(dbg.get("response_type_repair_kind") or "")
    meta = fallback_template_metadata(repair_kind)
    observe_meta = fallback_template_metadata("observe_perception_fallback")
    assert text
    assert meta == {"fallback_family": OPENING_FALLBACK_FAMILY, "temporal_frame": "first_impression"}
    assert meta.get("fallback_family") != observe_meta.get("fallback_family")
    assert meta.get("temporal_frame") not in {"reinspection", "continuation"}
    assert_opening_fallback_family_temporal(dbg)


def test_opening_visibility_safe_fallback_routes_to_opening_family_not_observe() -> None:
    selected = visibility_fallback.standard_visibility_safe_fallback(
        gm_output=opening_gm_output(),
        session={},
        scene={"scene": opening_gm_output()["prompt_context"]["scene"]["public"]},
        world={},
        scene_id="frontier_gate",
        eff_resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        active_interlocutor="",
        strict_social_active=False,
        strict_social_suppressed_non_social_turn=False,
    )

    low = selected.text.lower()
    assert selected.fallback_kind == OPENING_SUCCESS_SOURCE
    assert_opening_fallback_family_temporal(selected.composition_meta)
    assert "look again" not in low
    assert "still" not in low


def test_opening_fallback_ignores_contaminated_public_scene_visible_facts() -> None:
    gm_output = opening_gm_output()
    gm_output["prompt_context"]["scene"]["public"]["visible_facts"] = [
        "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate.",
        "GM hint: the captain plans to arrest the player after sundown.",
        "Backstage: the hidden cult controls the west-road patrol.",
    ]

    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    low = text.lower()
    assert dbg.get("opening_recovered_via_fallback") is True
    assert "gm hint" not in low
    assert "captain plans" not in low
    assert "backstage" not in low
    assert "hidden cult" not in low


def test_opening_fallback_never_uses_polluted_narration_visibility_facts() -> None:
    gm_output = opening_gm_output()
    gm_output["opening_curated_facts"] = [
        "Blue rain beads on the Gate Ward's iron lamps.",
        "Ward guards keep travelers moving past the toll arch.",
        "A brass notice board names the morning crossings.",
    ]
    gm_output["prompt_context"]["narration_visibility"]["visible_facts"] = [
        "A dead drop waits beneath the third bench.",
        "Muddy footprints lead toward the shuttered apothecary.",
    ]

    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    low = text.lower()
    assert "dead drop" not in low
    assert "footprints" not in low
    assert "gate ward's iron lamps" in text.lower()
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"


def test_failed_scene_opening_never_emits_generic_the_scene_fallback() -> None:
    gm_output = opening_gm_output()
    plan = gm_output["prompt_context"]["narrative_plan"]
    plan["scene_opening"]["location_anchors"] = []
    plan["scene_anchors"]["location_anchors"] = []
    gm_output["prompt_context"]["scene"]["public"].pop("location", None)

    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert dbg.get("response_type_repair_kind") == OPENING_SUCCESS_REPAIR_KIND
    assert "the scene" not in text.lower()
    assert "before you is immediately before you" not in text.lower()
    assert "the scene is immediately before you" not in text.lower()
    assert text


def test_frontier_gate_opening_fallback_uses_top_level_curated_facts() -> None:
    public_scene = default_scene("frontier_gate")["scene"]
    curated = [
        "Cold rain needles Cinderwatch's eastern gate while torchlight smears across the stone.",
        "Refugees, wagons, and travelers crowd the muddy checkpoint.",
        "A notice board announces new taxes and curfews beside the guard post.",
    ]
    gm_output = {
        "response_policy": {"response_type_contract": response_type_contract("scene_opening")},
        "opening_curated_facts": curated,
        "prompt_context": {
            "opening_inputs_are_curated": True,
            "narration_obligations": {"is_opening_scene": True},
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Cinderwatch Gate"]},
                "scene_anchors": {"location_anchors": ["Cinderwatch Gate"]},
            },
            "scene": {"public": public_scene},
        },
    }

    text, dbg = opening_gate_attach_then_enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Cold rain needles Cinderwatch's eastern gate" in text
    assert any(
        phrase in text
        for phrase in (
            "refugees, wagons, and travelers",
            "notice board announces new taxes and curfews",
            "tavern runner is hawking hot stew",
            "ragged stranger hangs back",
        )
    )
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"
    assert dbg.get("opening_fallback_failed_closed") is False
    assert "immediately before you" not in text.lower()


def test_scene_opening_rt_contract_accept_path_promotes_candidate_true_case() -> None:
    rd: dict[str, Any] = {
        "response_type_required": "scene_opening",
        "response_type_candidate_ok": True,
        "response_type_repair_used": False,
        "scene_opening_candidate_contract_passed": True,
    }
    assert opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate(rd) is True


@pytest.mark.parametrize(
    "response_type_debug",
    [
        {
            "response_type_required": "dialogue",
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
            "scene_opening_candidate_contract_passed": True,
        },
        {
            "response_type_required": "scene_opening",
            "response_type_candidate_ok": False,
            "response_type_repair_used": False,
            "scene_opening_candidate_contract_passed": True,
        },
        {
            "response_type_required": "scene_opening",
            "response_type_repair_used": False,
            "scene_opening_candidate_contract_passed": True,
        },
        {
            "response_type_required": "scene_opening",
            "response_type_candidate_ok": True,
            "response_type_repair_used": True,
            "scene_opening_candidate_contract_passed": True,
        },
        {
            "response_type_required": "scene_opening",
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
            "scene_opening_candidate_contract_passed": False,
        },
        {
            "response_type_required": "scene_opening",
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
        },
    ],
    ids=[
        "required_not_scene_opening",
        "candidate_ok_false",
        "candidate_ok_missing",
        "repair_used_true",
        "scene_opening_contract_passed_false",
        "scene_opening_contract_passed_missing",
    ],
)
def test_scene_opening_rt_contract_accept_path_promotes_candidate_false_cases(
    response_type_debug: dict[str, Any],
) -> None:
    assert opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate(response_type_debug) is False


def test_block_ai_scene_opening_rt_selector_does_not_mutate_inputs() -> None:
    """Relocated from gate (BG-2): scene-opening RT accept-path selector must not mutate debug dict."""
    rd: dict[str, Any] = {
        "response_type_required": "scene_opening",
        "response_type_candidate_ok": True,
        "response_type_repair_used": False,
        "scene_opening_candidate_contract_passed": True,
    }
    snap = json.dumps(rd, sort_keys=True)
    opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate(rd)
    assert json.dumps(rd, sort_keys=True) == snap


def test_block_ai_opening_upstream_prepared_snapshot_remains_preferred_over_compatibility_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Relocated from gate (BG-2): upstream-prepared opening snapshot blocks compatibility-local compose."""
    gm = opening_gm_output()
    gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = build_upstream_prepared_opening_fallback_payload(gm)

    def _compat_must_not_run(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("compatibility-local opening composer must not run when upstream snapshot is attached")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _compat_must_not_run)
    selected = opening_gate_attach_then_opening_scene_safe_fallback_selection(gm)
    composition_meta = selected.composition_meta or {}
    assert_opening_fallback_authorship(
        composition_meta,
        OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    )


def test_visibility_selected_fallback_candidate_builds_dataclass() -> None:
    selected = opening_fallback.opening_scene_safe_fallback_selection(
        {"opening_curated_facts": ["Rain needles the stones at the gate."]},
        fail_closed_composition_meta_factory=_fail_closed_composition_meta,
    )
    from game.final_emission_visibility_fallback import visibility_selected_fallback_candidate

    built = visibility_selected_fallback_candidate(
        selected.text,
        selected.fallback_pool,
        selected.fallback_kind,
        selected.final_emitted_source,
        selected.fallback_strategy,
        selected.fallback_candidate_source,
        selected.composition_meta,
    )
    assert built == selected


def test_opening_sealed_fallback_selection_projects_visibility_selection() -> None:
    gm_output = {"opening_curated_facts": ["Rain needles the stones at the gate."]}
    visibility = opening_fallback.opening_scene_safe_fallback_selection(
        gm_output,
        fail_closed_composition_meta_factory=_fail_closed_composition_meta,
    )
    sealed = opening_fallback.opening_sealed_fallback_selection(
        gm_output,
        fail_closed_composition_meta_factory=_fail_closed_composition_meta,
    )
    assert sealed.text == visibility.text
    assert sealed.fallback_pool == visibility.fallback_pool
    assert sealed.fallback_kind == visibility.fallback_kind
    assert sealed.final_emitted_source == visibility.final_emitted_source
    assert sealed.composition_meta == visibility.composition_meta


def test_make_opening_sealed_fallback_provider_binds_composition_meta_factory() -> None:
    captured: dict[str, Any] = {}

    def meta_factory() -> dict[str, Any]:
        captured["ran"] = True
        return _fail_closed_composition_meta()

    provider = opening_fallback.make_opening_sealed_fallback_provider(
        fail_closed_composition_meta_factory=meta_factory,
    )
    gm_output = {"opening_curated_facts": ["Rain needles the stones at the gate."]}
    sealed = provider(gm_output)
    assert captured.get("ran") is True
    assert sealed.text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER


# === Full-gate opening integration (relocated from test_final_emission_gate.py, BH-1) ===
# Gate-order pin remains in gate suite: test_block_l_apply_final_emission_gate_scene_opening_maybe_attach_runs_before_deterministic_opening_composer


def _ssa_contract(**overrides):
    base = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "frontier_gate",
        "scene_location_label": None,
        "location_tokens": [],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    base.update(overrides)
    return base


def _rich_scene_opening_candidate() -> str:
    return (
        "Rain spatters soot-dark stone across Cinderwatch's eastern gate while frayed banners snap "
        "above the muddy approach. You stand in the churned mud before the gate as refugees press "
        "shoulder to shoulder around the wagon line and guards hold the choke under shouted orders. "
        "A tavern runner weaves through the crush, calling offers of hot stew and paid rumor as the "
        "notice board waits beside the arch. The queue inches forward in fits, wagon wheels grinding "
        "through black ruts while wet canvas slaps against overloaded carts and the smell of damp wool, "
        "smoke, and sour road dust clings to everyone close enough to breathe on you. Somewhere ahead, "
        "a guard captain's voice cuts through the mutter of the crowd, sharp enough to make shoulders "
        "hunch and conversations die for a heartbeat before the pressure of bodies closes in again. "
        "You can read the notice board, press the guards, approach the tavern runner, or watch the "
        "silent figure in the crush."
    )

def test_apply_final_emission_gate_repairs_malformed_opening_fast_fallback_composition():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    session["turn_counter"] = 0
    session["visited_scene_ids"] = [sid]
    scene = default_scene(sid)
    scene["scene"]["location"] = "Frontier Gate"
    scene["scene"]["summary"] = "A rain-soaked checkpoint holds a nervous crowd at the gate."
    scene["scene"]["visible_facts"] = [
        "Several patrons exchange furtive glances.",
        "A notice board lists a missing patrol.",
        "Rain darkens the flagstones around the checkpoint.",
    ]
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])

    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "Emergent Lord Aldric Several patrons exchange furtive glances. "
                "The rain holds; beside it, a notice board lists a missing patrol."
            ),
            "tags": ["forced_retry_fallback", "upstream_api_fast_fallback"],
            "scene_state_anchor_contract": _ssa_contract(
                scene_id=sid,
                scene_location_label="Frontier Gate",
                location_tokens=["frontier gate", "gate", "checkpoint"],
                actor_tokens=["emergent lord aldric"],
            ),
        },
        resolution={"kind": "observe", "prompt": "Begin."},
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = read_final_emission_meta_dict(out) or {}
    assert "emergent lord aldric several" in low
    assert "holds; beside it" in low
    assert meta.get("fast_fallback_neutral_composition_malformed_detected") is True
    assert meta.get("fast_fallback_neutral_composition_repaired") is False
    assert meta.get("scene_state_anchor_passed") is True

def test_opening_validator_rejects_investigation_continuation_language():
    failures = opening_validators.validate_opening_output("Nearby crates appear disturbed.", opening_validation_context())

    assert "continuation_or_investigation_language" in failures
    assert "invalid_sentence_structure" in failures

def test_opening_validator_rejects_fragment_sentence():
    failures = opening_validators.validate_opening_output("At the Cinderwatch Gate District, rain and refugees.", opening_validation_context())

    assert "invalid_sentence_structure" in failures

def test_opening_validator_rejects_opening_without_actionable_hook():
    failures = opening_validators.validate_opening_output(
        "Cinderwatch Gate District. Rain spatters soot-dark stone while refugees and wagons clog the muddy approach.",
        opening_validation_context(),
    )

    assert "missing_hook" in failures

def test_full_gate_malformed_opening_payload_without_upstream_repair_is_sealed_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Block C9: full-gate path cannot turn malformed opening payloads into unknown/compat ownership."""
    gm_output = opening_gm_output()
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = {
        "prepared_opening_fallback_text": EXPECTED_FRONTIER_GATE_OPENING_FALLBACK,
    }
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    import game.final_emission_gate_preflight_upstream as gate_preflight_upstream

    def _skip_upstream_repair(out: dict[str, Any] | None, *, resolution: dict[str, Any] | None) -> None:
        return None

    monkeypatch.setattr(
        gate_preflight_upstream,
        "maybe_attach_upstream_prepared_opening_fallback_payload",
        _skip_upstream_repair,
    )
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = final_emission_meta_from_output(out)
    # Sealed-gate opening failure: malformed upstream stub must not emit prepared prose.
    assert_opening_fallback_fail_closed(
        fem,
        opening_fallback_upstream_payload_unusable=True,
        response_type_repair_kind=OPENING_FAILED_CLOSED_REPAIR_KIND,
    )
    assert out["player_facing_text"] != EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert EXPECTED_FRONTIER_GATE_OPENING_FALLBACK not in str(out.get("player_facing_text") or "")
    # N4 terminal replacement after sealed opening path (cf. empty curated facts sibling).
    assert fem["final_route"] == "replaced"
    assert fem["final_emitted_source"] == "acceptance_quality_global_scene_fallback"
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == GATE_TERMINAL_REPAIR
    assert out["player_facing_text"] == "For a breath, the scene holds while voices shift around you."

def test_scene_opening_accepted_candidate_promotes_over_short_stale_player_text(monkeypatch):
    short = "You stand at Cinderwatch's eastern gate in the rain. Guards hold the choke."
    rich = _rich_scene_opening_candidate()
    orig_enforce = response_type.enforce_response_type_contract

    def _select_rich_candidate(candidate_text, **kwargs):
        assert candidate_text == short
        return orig_enforce(rich, **kwargs)

    def _late_stale_rewrite(out, *, text, **kwargs):
        return short, [], False

    monkeypatch.setattr(response_type, "enforce_response_type_contract", _select_rich_candidate)
    monkeypatch.setattr(non_strict_stack, "apply_interaction_continuity_emission_step", _late_stale_rewrite)

    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = short
    gm_output["tags"] = []
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    emitted = str(out.get("player_facing_text") or "")
    emission_debug = ((out.get("metadata") or {}).get("emission_debug") or {})
    fem = read_final_emission_meta_dict(out) or {}

    assert emitted == rich
    assert emitted != short
    assert emission_debug.get("scene_opening_candidate_len") == len(rich)
    assert emission_debug.get("scene_opening_emitted_len") == len(rich)
    assert emission_debug.get("scene_opening_candidate_emitted_match") is True
    assert emission_debug.get("scene_opening_accepted_candidate_promoted") is True
    assert emission_debug.get("response_type_candidate_preview") == emission_debug.get("response_type_emitted_preview")
    assert fem.get("response_type_candidate_preview") == fem.get("response_type_emitted_preview")

def test_canonical_final_gate_opening_fallback_fem_is_upstream_prepared_not_compatibility_local() -> None:
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = final_emission_meta_from_output(out)
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    family = fem[REALIZATION_FALLBACK_FAMILY_FIELD]
    assert family in FALLBACK_FAMILIES
    assert family == UPSTREAM_PREPARED_EMISSION
    assert family != LEGACY_DIEGETIC_FALLBACK
    assert_opening_fallback_upstream_prepared(
        fem,
        response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
        opening_fallback_context_source="opening_curated_facts",
        opening_recovered_via_fallback=True,
        fallback_family_used=OPENING_FALLBACK_FAMILY,
    )

def test_canonical_final_gate_auto_attaches_upstream_opening_fallback_before_emission(monkeypatch) -> None:
    gm_output = opening_gm_output()
    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in gm_output
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    def _should_not_run_gate_local_deterministic_opening(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("gate-local deterministic opening must not run when upstream payload is present")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _should_not_run_gate_local_deterministic_opening)
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    pay = out.get(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY)
    assert isinstance(pay, dict)
    assert pay["prepared_opening_fallback_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    fem = final_emission_meta_from_output(out)
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == UPSTREAM_PREPARED_EMISSION
    assert_opening_fallback_upstream_prepared(fem, **successful_opening_fem_meta())

def test_block_n_opening_attach_build_failure_fails_closed_preserves_block_m_telemetry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Block N: attach build failure on full gate entry fails closed; Block M telemetry preserved; no compat compose."""
    import game.upstream_response_repairs as urr

    gm_output = opening_gm_output()
    gm_output.pop(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY, None)
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    def boom(_mapping: object) -> dict[str, object]:
        raise RuntimeError("simulated upstream attach build failure")

    monkeypatch.setattr(urr, "build_upstream_prepared_opening_fallback_payload", boom)

    calls: list[str] = []
    real_det = _deterministic_opening_under_test

    def wrapped_det(out: Mapping[str, Any] | None) -> tuple[str, dict[str, Any]]:
        calls.append("deterministic")
        return real_det(out)

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", wrapped_det)

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    # Response-type path emits the sealed marker; downstream visibility/N4 may replace with global stock (cf. Block H full gate).
    assert out["player_facing_text"] == "For a breath, the scene holds while voices shift around you."
    assert_opening_fallback_fail_closed(
        fem,
        opening_fallback_compatibility_local_disabled=True,
        blocked_repair_kind="opening_upstream_prepare_attach_failed",
        response_type_repair_kind="opening_deterministic_fallback_failed_closed",
        opening_upstream_prepare_attach_build_failed=True,
        opening_upstream_prepare_attach_failure_exc_type="RuntimeError",
        opening_upstream_prepare_attach_no_usable_payload_after_attempt=True,
    )
    assert not calls

def test_block_m_successful_upstream_attach_has_no_attach_failure_telemetry() -> None:
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("opening_upstream_prepare_attach_build_failed") is False
    assert fem.get("opening_upstream_prepare_attach_no_usable_payload_after_attempt") is False
    assert fem.get("opening_upstream_prepare_attach_failure_exc_type") in (None, "")
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert_opening_fallback_upstream_prepared(fem, final_emitted_source=None)

def test_fail_closed_sealed_gate_empty_curated_facts_skips_upstream_opening_payload() -> None:
    gm_output = opening_gm_output()
    gm_output["opening_curated_facts"] = []
    gm_output["opening_selector_selected_facts"] = []
    md = gm_output.setdefault("metadata", {})
    em = md.setdefault("emission_debug", {})
    em["opening_curated_facts_present"] = False
    em["opening_curated_facts_count"] = 0
    em["opening_selector_selected_facts"] = []
    em["opening_curated_facts"] = []
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in out
    assert out["player_facing_text"] == "For a breath, the scene holds while voices shift around you."
    fem = read_final_emission_meta_dict(out) or {}
    assert fem["response_type_repair_kind"] == "opening_deterministic_fallback_failed_closed"
    assert_opening_fallback_fail_closed(
        fem,
        opening_fallback_compatibility_local_disabled=True,
        opening_fallback_missing_upstream_prepared_payload=True,
    )
    # N4 terminal replacement route metadata — intentionally distinct from adapter-only fail-closed locks.
    assert fem["final_route"] == "replaced"
    assert fem["final_emitted_source"] == "acceptance_quality_global_scene_fallback"
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == GATE_TERMINAL_REPAIR

def test_canonical_final_gate_prefers_upstream_prepared_payload_when_present(monkeypatch) -> None:
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = build_upstream_prepared_opening_fallback_payload(gm_output)

    def _should_not_run_local_deterministic_opening(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("gate-local deterministic opening must not run when upstream payload is present")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _should_not_run_local_deterministic_opening)
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == UPSTREAM_PREPARED_EMISSION
    assert_opening_fallback_upstream_prepared(
        fem,
        response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
        opening_fallback_context_source="opening_curated_facts",
        opening_recovered_via_fallback=True,
        fallback_family_used=OPENING_FALLBACK_FAMILY,
    )

def test_final_gate_mirrors_authorship_from_upstream_payload_not_route_inference() -> None:
    gm_output = opening_gm_output()
    payload = build_upstream_prepared_opening_fallback_payload(gm_output)
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = payload
    _repaired, dbg = response_type.enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("opening_recovered_via_fallback") is True
    assert_opening_fallback_authorship(dbg, OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED)

def test_final_gate_does_not_infer_authorship_when_upstream_composition_lacks_field() -> None:
    gm_output = opening_gm_output()
    payload = build_upstream_prepared_opening_fallback_payload(gm_output)
    composition = dict(payload["opening_fallback_composition_meta"])
    composition.pop("opening_fallback_authorship_source", None)
    payload["opening_fallback_composition_meta"] = composition
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = payload
    _repaired, dbg = response_type.enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("opening_recovered_via_fallback") is True
    assert_opening_fallback_authorship(dbg, None, forbid_compat_local=False)

def test_final_gate_valid_opening_candidate_has_no_fallback_provenance() -> None:
    candidate = (
        "You stand in the churned mud before Cinderwatch's eastern gate as rain spatters soot-dark stone. "
        "Refugees press shoulder to shoulder around the wagon line while guards hold the choke. "
        "You can read the notice board or approach the guards."
    )
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = candidate
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == candidate
    assert fem["final_emitted_source"] == "generated_candidate"
    assert fem.get("fallback_family_used") is None
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) is None
    assert isinstance(out.get(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY), dict)
    assert fem.get("opening_fallback_authorship_source") is None

def test_canonical_missing_curated_facts_upstream_prepared_payload_still_wins(monkeypatch) -> None:
    gm_output = opening_gm_output()
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = build_upstream_prepared_opening_fallback_payload(gm_output)
    gm_output.pop("opening_curated_facts", None)
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    def _boom(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("compatibility-local deterministic opening must not run when upstream snapshot is attached")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _boom)
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    fem = read_final_emission_meta_dict(out) or {}
    assert_opening_fallback_upstream_prepared(
        fem,
        final_emitted_source=None,
        opening_fallback_missing_curated_facts=True,
        response_type_repair_kind="opening_deterministic_fallback",
    )

def test_fail_closed_sealed_gate_missing_curated_facts_records_fem() -> None:
    gm_output = opening_gm_output()
    gm_output.pop("opening_curated_facts", None)
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("opening_fallback_missing_curated_facts") is True
    assert fem.get("blocked_repair_kind") == "opening_missing_curated_facts"
    assert fem.get("response_type_repair_kind") == "opening_deterministic_fallback_failed_closed"
    assert_fallback_owner_bucket(OPENING_FALLBACK_OWNER_SEALED_GATE, meta=fem)

def test_narrative_mode_output_opening_validation_runs_for_scene_opening_response_type() -> None:
    nmc = build_narrative_mode_contract(narration_obligations={"is_opening_scene": True})
    gm_output = opening_gm_output()
    gm_output["prompt_context"]["narrative_plan"]["narrative_mode_contract"] = nmc
    gm_output["player_facing_text"] = (
        "Cinderwatch Gate District gathers rain, refugees, wagons, guards, and torchlight "
        "around the eastern gate. You can read the notice board or approach the guards."
    )
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}

    assert fem.get("response_type_required") == "scene_opening"
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_mode") == "opening"
    assert fem.get("narrative_mode_contract_mode") == "opening"


def test_opening_mode_active_for_turn_resolution_kind() -> None:
    assert opening_mode._opening_mode_active_for_turn(None, {"kind": "scene_opening"}) is True
    assert opening_mode._opening_mode_active_for_turn({}, {"kind": "dialogue"}) is False


def test_opening_mode_active_for_turn_narrative_mode_contract() -> None:
    gm_output = {
        "prompt_context": {
            "narrative_plan": {
                "narrative_mode_contract": {"mode": "opening"},
            },
        },
    }
    assert opening_mode._opening_mode_active_for_turn(gm_output, None) is True


def test_opening_mode_active_for_turn_narration_obligations() -> None:
    gm_output = {
        "prompt_context": {
            "narration_obligations": {"is_opening_scene": True},
        },
    }
    assert opening_mode._opening_mode_active_for_turn(gm_output, None) is True

    gm_output_renderer = {
        "prompt_context": {
            "renderer_inputs": {
                "narration_obligations": {"is_opening_scene": True},
            },
        },
    }
    assert opening_mode._opening_mode_active_for_turn(gm_output_renderer, None) is True


def test_opening_mode_active_for_turn_inactive() -> None:
    assert opening_mode._opening_mode_active_for_turn(None, None) is False
    assert opening_mode._opening_mode_active_for_turn({}, {}) is False


def test_opening_visible_anchor_fallback_text_builds_from_shipped_anchors() -> None:
    gm_output = {
        "prompt_context": {
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Frontier Gate"]},
                "allowable_entity_references": [{"descriptor": "Captain Aldric"}],
                "active_pressures": {"interaction_pressure": "reply_expected"},
            },
        },
    }
    text = opening_mode._opening_visible_anchor_fallback_text(gm_output)
    assert text == "Frontier Gate. Captain Aldric is here. A reply is expected."


def test_opening_visible_anchor_fallback_text_prefers_scene_opening_location() -> None:
    gm_output = {
        "prompt_context": {
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Opening Loc"]},
                "scene_anchors": {"location_anchors": ["Scene Loc"]},
            },
        },
    }
    assert opening_mode._opening_visible_anchor_fallback_text(gm_output) == "Opening Loc."


def test_opening_visible_anchor_fallback_text_empty_without_prompt_context() -> None:
    assert opening_mode._opening_visible_anchor_fallback_text(None) == ""
    assert opening_mode._opening_visible_anchor_fallback_text({}) == ""

