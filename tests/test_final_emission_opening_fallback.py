"""Owner tests for opening adapter result semantics.

This module owns prepared-payload selection, sealed fail-closed metadata,
adapter-level opening ownership fields, attach-then-helper fixture semantics,
and response-type helper bypass behavior for ``game.final_emission_opening_fallback``.
The gate delegation test at the end is the only intended gate-integration pin
here; final output, FEM propagation, and gate ordering remain gate-suite work.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest

import game.final_emission_gate as final_emission_gate
import game.final_emission_opening_fallback as opening_fallback
from game.final_emission_visibility_fallback import VisibilitySelectedFallback
import game.opening_deterministic_fallback as opening_deterministic_fallback
from game.defaults import default_scene
from game.diegetic_fallback_narration import fallback_template_metadata
from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    opening_fallback_owner_bucket_from_meta,
)
from game.realization_provenance import REALIZATION_FALLBACK_FAMILY_FIELD, UPSTREAM_PREPARED_EMISSION
from game.opening_deterministic_fallback import (
    OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER,
    deterministic_opening_fallback_text_and_meta,
)
from game.upstream_response_repairs import (
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
    build_upstream_prepared_opening_fallback_payload,
)
from tests.helpers.emission_smoke_assertions import response_type_contract
from tests.helpers.opening_fallback_evidence import (
    EXPECTED_FRONTIER_GATE_OPENING_FALLBACK,
    assert_fallback_owner_bucket,
    assert_final_emission_meta_contains,
    opening_gm_output,
)
from tests.helpers.opening_fallback_gate_harness import opening_gate_attach_then_enforce_response_type_contract
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL


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
        "opening_fallback_composition_meta": {
            "fallback_family_used": "scene_opening",
            "fallback_temporal_frame": "first_impression",
            "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        },
    }


def _select(gm_output: Dict[str, Any]) -> VisibilitySelectedFallback:
    return opening_fallback.opening_scene_safe_fallback_selection(
        gm_output,
        fail_closed_composition_meta_factory=_fail_closed_composition_meta,
    )


def _assert_owner_bucket(meta: Dict[str, Any], *, repair_kind: str, expected: str) -> None:
    assert_fallback_owner_bucket(
        expected,
        from_fields={
            "final_emitted_source": "opening_deterministic_fallback",
            "opening_recovered_via_fallback": True,
            "opening_fallback_authorship_source": meta.get("opening_fallback_authorship_source"),
            "response_type_repair_kind": repair_kind,
            "fallback_family": meta.get("fallback_family_used"),
            "fallback_temporal_frame": meta.get("fallback_temporal_frame"),
        },
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
        assert selected.fallback_kind == "opening_deterministic_fallback"
        assert selected.final_emitted_source == "opening_deterministic_fallback"
        assert selected.fallback_strategy == "opening_scene_safe_fallback"
        assert selected.fallback_candidate_source == "opening_deterministic_fallback"
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
        "opening_deterministic_fallback",
        "opening_deterministic_fallback",
        "opening_scene_safe_fallback",
        "opening_deterministic_fallback",
    )
    meta = dict(selected.composition_meta)
    assert meta == payload["opening_fallback_composition_meta"]
    assert meta is not payload["opening_fallback_composition_meta"]
    assert meta["opening_fallback_authorship_source"] == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    _assert_owner_bucket(meta, repair_kind=selected.fallback_kind, expected=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED)


def test_select_mirrors_authorship_from_upstream_composition_meta() -> None:
    gm_output = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: _prepared_payload()}
    _text, meta, _stub, selected, _upstream = (
        opening_fallback.select_opening_fallback_for_response_type_contract(gm_output)
    )
    assert selected is True
    assert meta["opening_fallback_authorship_source"] == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED


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
    assert selected.fallback_kind == "opening_deterministic_fallback"
    meta = dict(selected.composition_meta)
    assert meta["opening_fallback_failed_closed"] is True
    assert meta["opening_fallback_missing_upstream_prepared_payload"] is True
    assert meta["opening_fallback_missing_curated_facts"] is False
    assert meta["opening_fallback_basis_count"] == 1
    assert meta["opening_fallback_authorship_source"] is None
    assert meta["fallback_family_used"] == "scene_opening"
    assert meta["fallback_temporal_frame"] == "first_impression"
    _assert_owner_bucket(
        meta,
        repair_kind="opening_deterministic_fallback_failed_closed",
        expected=OPENING_FALLBACK_OWNER_SEALED_GATE,
    )


def test_adapter_insufficient_curated_facts_fails_closed_with_existing_metadata_shape() -> None:
    selected = _select({"opening_curated_facts": []})

    assert selected.text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    meta = dict(selected.composition_meta)
    assert meta["opening_fallback_failed_closed"] is True
    assert meta["opening_fallback_missing_upstream_prepared_payload"] is True
    assert meta["opening_fallback_compatibility_local_disabled"] is True
    assert meta["opening_fallback_context_missing"] is True
    assert meta["opening_curated_facts_present"] is False
    assert meta["opening_curated_facts_count"] == 0
    assert meta["opening_fallback_authorship_source"] is None
    _assert_owner_bucket(
        meta,
        repair_kind="opening_deterministic_fallback_failed_closed",
        expected=OPENING_FALLBACK_OWNER_SEALED_GATE,
    )


def test_adapter_unusable_upstream_stub_preserves_fail_closed_metadata() -> None:
    selected = _select(
        {
            "opening_curated_facts": ["Rain needles the stones at the gate."],
            UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: {"prepared_opening_fallback_text": PREPARED_TEXT},
        }
    )

    assert selected.text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    meta = dict(selected.composition_meta)
    assert meta["opening_fallback_failed_closed"] is True
    assert meta["opening_fallback_upstream_payload_unusable"] is True
    assert meta["opening_fallback_upstream_payload_recovered"] is False
    assert meta["opening_fallback_missing_upstream_prepared_payload"] is False
    assert meta["opening_fallback_compatibility_local_disabled"] is True
    assert meta["opening_fallback_authorship_source"] is None
    _assert_owner_bucket(
        meta,
        repair_kind="opening_deterministic_fallback_failed_closed",
        expected=OPENING_FALLBACK_OWNER_SEALED_GATE,
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
    assert dbg.get("response_type_repair_kind") == "opening_deterministic_fallback"
    assert dbg.get("fallback_family_used") == "scene_opening"
    family = dbg[REALIZATION_FALLBACK_FAMILY_FIELD]
    assert family == UPSTREAM_PREPARED_EMISSION
    assert_final_emission_meta_contains(
        dbg,
        opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    )
    assert dbg.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert_fallback_owner_bucket(OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED, meta=dbg)


def test_gate_opening_failure_text_only_stub_fails_closed_without_rebuild(monkeypatch: pytest.MonkeyPatch) -> None:
    gm = opening_gm_output()
    gm[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = {"prepared_opening_fallback_text": EXPECTED_FRONTIER_GATE_OPENING_FALLBACK}

    calls: list[int] = []

    def _counting_local_deterministic_opening(*a: Any, **k: Any) -> tuple[str, dict]:
        calls.append(1)
        return deterministic_opening_fallback_text_and_meta(*a, **k)

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _counting_local_deterministic_opening)
    text, dbg = final_emission_gate._enforce_response_type_contract(
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
    assert dbg.get("response_type_repair_kind") == "opening_deterministic_fallback_failed_closed"
    assert_final_emission_meta_contains(dbg, opening_fallback_authorship_source=None)
    assert dbg.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert_fallback_owner_bucket(OPENING_FALLBACK_OWNER_SEALED_GATE, meta=dbg)


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
    assert meta == {"fallback_family": "scene_opening", "temporal_frame": "first_impression"}
    assert meta.get("fallback_family") != observe_meta.get("fallback_family")
    assert meta.get("temporal_frame") not in {"reinspection", "continuation"}
    assert dbg.get("fallback_family_used") == "scene_opening"
    assert dbg.get("fallback_temporal_frame") == "first_impression"


def test_opening_visibility_safe_fallback_routes_to_opening_family_not_observe() -> None:
    selected = final_emission_gate._standard_visibility_safe_fallback(
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
    assert selected.fallback_kind == "opening_deterministic_fallback"
    assert selected.composition_meta.get("fallback_family_used") == "scene_opening"
    assert selected.composition_meta.get("fallback_temporal_frame") == "first_impression"
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

    assert dbg.get("response_type_repair_kind") == "opening_deterministic_fallback"
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


def test_gate_opening_selection_wrapper_delegates_to_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = VisibilitySelectedFallback(
        text="text",
        fallback_pool="pool",
        fallback_kind="kind",
        final_emitted_source="emitted",
        fallback_strategy="strategy",
        fallback_candidate_source="candidate",
        composition_meta={"meta": True},
    )
    captured: Dict[str, Any] = {}

    def fake_adapter(
        gm_output: Dict[str, Any],
        *,
        fail_closed_composition_meta_factory: Any,
    ) -> VisibilitySelectedFallback:
        captured["gm_output"] = gm_output
        captured["meta_factory"] = fail_closed_composition_meta_factory
        return sentinel

    monkeypatch.setattr(final_emission_gate, "_opening_scene_safe_fallback_selection_from_adapter", fake_adapter)
    gm_output = {"opening_curated_facts": []}

    assert final_emission_gate._opening_scene_safe_fallback_selection(gm_output) is sentinel
    assert captured["gm_output"] is gm_output
    assert captured["meta_factory"] is final_emission_gate._first_mention_composition_meta
