"""Pure owner tests for ``game.final_emission_visibility_fallback``.

This suite owns pure visibility fallback helper behavior: route, payload, metadata,
annotation, owner-bucket, dispatch, defensive-copy, and logging-payload shaping.
It does not own visibility legality semantics or gate orchestration.
"""
from __future__ import annotations

import ast
import inspect
from typing import Any

import pytest

from game.final_emission_meta import (
    VISIBILITY_FALLBACK_OWNER_BUCKETS,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS,
    VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
)
import game.final_emission_visibility_fallback as visibility_fallback
from tests.helpers.final_emission_gate_fixtures import assert_visibility_pool

pytestmark = pytest.mark.unit

def test_visibility_fallback_route_helper_importable_and_callable_from_new_module() -> None:
    fn = visibility_fallback.route_visibility_enforcement_after_failed_validation

    assert callable(fn)
    assert fn(
        tag_list_gate=[],
        dbg_gate="",
        violation_kinds=["offscene_entity"],
        checked_entities=["_force_visibility_entity_check"],
        checked_facts=[],
        candidate_text="The guard nods once.",
    ) == "sealed_hard_replace"


@pytest.mark.parametrize(
    ("case", "kwargs", "expected"),
    [
        (
            "hard_replace",
            {
                "tag_list_gate": [],
                "dbg_gate": "",
                "violation_kinds": ["unseen_entity_reference"],
                "checked_entities": [{"entity_id": "lord_aldric"}],
                "checked_facts": [],
                "candidate_text": "Lord Aldric watches from the square.",
            },
            "sealed_hard_replace",
        ),
        (
            "continuity_lead_exemption",
            {
                "tag_list_gate": ["known_fact_guard"],
                "dbg_gate": "recent_dialogue_continuity",
                "violation_kinds": ["unseen_entity_reference"],
                "checked_entities": [{"entity_id": "runner"}],
                "checked_facts": [],
                "candidate_text": "The runner answers.",
            },
            "continuity_lead_exemption",
        ),
        (
            "concrete_interaction_no_hard_replace",
            {
                "tag_list_gate": [],
                "dbg_gate": "",
                "violation_kinds": ["visibility_probe"],
                "checked_entities": [],
                "checked_facts": [],
                "candidate_text": '"Stay close," the guard says.',
            },
            "concrete_interaction_no_hard_replace",
        ),
    ],
)
def test_visibility_fallback_route_helper_decisions(case: str, kwargs: dict[str, Any], expected: str) -> None:
    del case
    assert visibility_fallback.route_visibility_enforcement_after_failed_validation(**kwargs) == expected


def test_visibility_fallback_route_module_contains_no_fallback_prose_literals() -> None:
    source = inspect.getsource(visibility_fallback)
    forbidden = (
        "voices shift",
        "Nothing confirms progress",
        "Enough watching",
        "Ask me now",
        "lose the trail",
    )

    for snippet in forbidden:
        assert snippet not in source


@pytest.mark.parametrize(
    ("case", "kwargs", "expected"),
    [
        (
            "sealed_gate_global",
            {
                "fallback_pool": "global_scene_narrative",
                "fallback_kind": "narrative_safe_fallback",
                "final_emitted_source": "global_scene_fallback",
            },
            VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
        ),
        (
            "strict_social_pool",
            {
                "fallback_pool": "strict_social_visibility_minimal",
                "fallback_kind": "visibility_minimal_social_fallback",
                "final_emitted_source": "minimal_social_emergency_fallback",
            },
            VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        ),
        (
            "strict_social_kind",
            {
                "fallback_pool": "",
                "fallback_kind": "visibility_minimal_social_fallback",
                "final_emitted_source": "",
            },
            VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        ),
        (
            "opening_pool",
            {
                "fallback_pool": "scene_opening_deterministic",
                "fallback_kind": "opening_deterministic_fallback",
                "final_emitted_source": "opening_deterministic_fallback",
            },
            VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
        ),
        (
            "opening_kind",
            {
                "fallback_pool": "",
                "fallback_kind": "opening_deterministic_fallback",
                "final_emitted_source": "",
            },
            VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
        ),
        (
            "unknown_none",
            {
                "fallback_pool": "",
                "fallback_kind": "",
                "final_emitted_source": "",
            },
            VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE,
        ),
    ],
)
def test_visibility_fallback_owner_bucket_classifier(case: str, kwargs: dict[str, str], expected: str) -> None:
    del case
    assert_visibility_pool(owner_bucket=expected, **kwargs)


def test_visibility_fallback_owner_bucket_taxonomy_includes_ambiguous_bucket() -> None:
    assert VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS in VISIBILITY_FALLBACK_OWNER_BUCKETS


def test_visibility_fallback_owner_bucket_constants_match_canonical_registry() -> None:
    assert visibility_fallback.VISIBILITY_FALLBACK_OWNER_SEALED_GATE is VISIBILITY_FALLBACK_OWNER_SEALED_GATE
    assert (
        visibility_fallback.VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY
        is VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY
    )
    assert (
        visibility_fallback.VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY
        is VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY
    )
    assert visibility_fallback.VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE is VISIBILITY_FALLBACK_OWNER_UNKNOWN_NONE
    assert (
        visibility_fallback.VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS
        is VISIBILITY_FALLBACK_OWNER_UNKNOWN_AMBIGUOUS
    )
    assert visibility_fallback.VISIBILITY_FALLBACK_OWNER_BUCKETS == VISIBILITY_FALLBACK_OWNER_BUCKETS
    assert VISIBILITY_FALLBACK_OWNER_BUCKETS == frozenset(
        {
            "sealed-gate",
            "strict-social-visibility",
            "opening-visibility",
            "unknown-none",
            "unknown-ambiguous",
        }
    )


def test_build_visibility_validation_observation_shapes_pass_result() -> None:
    observation = visibility_fallback.build_visibility_validation_observation(
        {
            "ok": True,
            "violations": "not-a-list",
            "visibility_checked_entities": [{"entity_id": "guard"}],
            "visibility_checked_facts": [{"fact": "visible brazier"}],
        }
    )

    assert observation.validation_passed is True
    assert observation.violation_kinds == []
    assert observation.violation_sample == []
    assert observation.checked_entities == [{"entity_id": "guard"}]
    assert observation.checked_facts == [{"fact": "visible brazier"}]


def test_build_visibility_validation_observation_shapes_failed_result() -> None:
    observation = visibility_fallback.build_visibility_validation_observation(
        {
            "ok": False,
            "violations": [
                {
                    "kind": "unseen_entity_reference",
                    "token": "Lord Aldric",
                    "matched_entity_id": "lord_aldric",
                },
                {
                    "kind": "undiscovered_fact_assertion",
                    "token": "payoff",
                    "matched_fact": "ash cowl payoff",
                },
                {"kind": "unseen_entity_reference", "token": "Aldric again"},
                {"kind": "extra_visibility_probe", "token": "fourth"},
                {"kind": ""},
                "malformed",
            ],
            "visibility_checked_entities": [{"entity_id": "lord_aldric"}],
            "visibility_checked_facts": [{"fact": "ash cowl payoff"}],
        }
    )

    assert observation.validation_passed is False
    assert observation.violation_kinds == [
        "unseen_entity_reference",
        "undiscovered_fact_assertion",
        "extra_visibility_probe",
    ]
    assert observation.violation_sample == [
        {
            "kind": "unseen_entity_reference",
            "token": "Lord Aldric",
            "matched_entity_id": "lord_aldric",
            "matched_fact": None,
        },
        {
            "kind": "undiscovered_fact_assertion",
            "token": "payoff",
            "matched_entity_id": None,
            "matched_fact": "ash cowl payoff",
        },
        {
            "kind": "unseen_entity_reference",
            "token": "Aldric again",
            "matched_entity_id": None,
            "matched_fact": None,
        },
    ]
    assert observation.checked_entities == [{"entity_id": "lord_aldric"}]
    assert observation.checked_facts == [{"fact": "ash cowl payoff"}]


def test_build_visibility_pre_route_validation_context_wraps_validation_result_and_observation() -> None:
    validation_result = {
        "ok": False,
        "violations": [
            {
                "kind": "unseen_entity_reference",
                "token": "Lord Aldric",
                "matched_entity_id": "lord_aldric",
            },
        ],
        "visibility_checked_entities": [{"entity_id": "lord_aldric"}],
        "visibility_checked_facts": [],
    }

    context = visibility_fallback.build_visibility_pre_route_validation_context(
        candidate_text="Lord Aldric watches the gate.",
        validation_result=validation_result,
    )

    assert context.candidate_text == "Lord Aldric watches the gate."
    assert context.validation_result is validation_result
    assert context.observation == visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[
            {
                "kind": "unseen_entity_reference",
                "token": "Lord Aldric",
                "matched_entity_id": "lord_aldric",
                "matched_fact": None,
            }
        ],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
    )


def test_build_visibility_default_metadata_payload_collects_initial_stamp_kwargs() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[{"kind": "unseen_entity_reference", "token": "Lord Aldric"}],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[{"fact": "hidden"}],
    )

    payload = visibility_fallback.build_visibility_default_metadata_payload(observation)

    assert payload == visibility_fallback.VisibilityDefaultMetadataPayload(
        validation_passed=False,
        replacement_applied=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[{"kind": "unseen_entity_reference", "token": "Lord Aldric"}],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[{"fact": "hidden"}],
    )
    assert payload.stamp_kwargs() == {
        "validation_passed": False,
        "replacement_applied": False,
        "violation_kinds": ["unseen_entity_reference"],
        "violation_sample": [{"kind": "unseen_entity_reference", "token": "Lord Aldric"}],
        "checked_entities": [{"entity_id": "lord_aldric"}],
        "checked_facts": [{"fact": "hidden"}],
    }
    assert "fallback_pool" not in payload.stamp_kwargs()
    assert "fallback_kind" not in payload.stamp_kwargs()
    assert "fallback_owner_bucket" not in payload.stamp_kwargs()


def test_build_visibility_first_mention_default_metadata_payload_collects_ordered_meta_updates() -> None:
    payload = visibility_fallback.build_visibility_first_mention_default_metadata_payload(
        default_first_mention_composition_layers=["default_layer"],
    )

    assert payload == visibility_fallback.VisibilityFirstMentionDefaultMetadataPayload(
        first_mention_validation_passed=None,
        first_mention_replacement_applied=False,
        first_mention_violation_kinds=[],
        first_mention_checked_entities=[],
        first_mention_leading_pronoun_detected=False,
        first_mention_first_explicit_entity_offset=None,
        first_mention_fallback_strategy=None,
        first_mention_fallback_candidate_source=None,
        opening_scene_first_mention_preference_used=False,
        first_mention_composition_used=False,
        first_mention_composition_layers=["default_layer"],
    )
    assert list(payload.meta_updates().items()) == [
        ("first_mention_validation_passed", None),
        ("first_mention_replacement_applied", False),
        ("first_mention_violation_kinds", []),
        ("first_mention_checked_entities", []),
        ("first_mention_leading_pronoun_detected", False),
        ("first_mention_first_explicit_entity_offset", None),
        ("first_mention_fallback_strategy", None),
        ("first_mention_fallback_candidate_source", None),
        ("opening_scene_first_mention_preference_used", False),
        ("first_mention_composition_used", False),
        ("first_mention_composition_layers", ["default_layer"]),
    ]


def test_build_visibility_pre_route_metadata_context_groups_default_payloads() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[{"kind": "unseen_entity_reference", "token": "Lord Aldric"}],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
    )

    context = visibility_fallback.build_visibility_pre_route_metadata_context(
        observation=observation,
        default_first_mention_composition_layers=["default_layer"],
    )

    assert context == visibility_fallback.VisibilityPreRouteMetadataContext(
        first_mention_defaults=visibility_fallback.VisibilityFirstMentionDefaultMetadataPayload(
            first_mention_validation_passed=None,
            first_mention_replacement_applied=False,
            first_mention_violation_kinds=[],
            first_mention_checked_entities=[],
            first_mention_leading_pronoun_detected=False,
            first_mention_first_explicit_entity_offset=None,
            first_mention_fallback_strategy=None,
            first_mention_fallback_candidate_source=None,
            opening_scene_first_mention_preference_used=False,
            first_mention_composition_used=False,
            first_mention_composition_layers=["default_layer"],
        ),
        visibility_defaults=visibility_fallback.VisibilityDefaultMetadataPayload(
            validation_passed=False,
            replacement_applied=False,
            violation_kinds=["unseen_entity_reference"],
            violation_sample=[{"kind": "unseen_entity_reference", "token": "Lord Aldric"}],
            checked_entities=[{"entity_id": "lord_aldric"}],
            checked_facts=[],
        ),
    )
    assert list(context.first_mention_defaults.meta_updates()) == [
        "first_mention_validation_passed",
        "first_mention_replacement_applied",
        "first_mention_violation_kinds",
        "first_mention_checked_entities",
        "first_mention_leading_pronoun_detected",
        "first_mention_first_explicit_entity_offset",
        "first_mention_fallback_strategy",
        "first_mention_fallback_candidate_source",
        "opening_scene_first_mention_preference_used",
        "first_mention_composition_used",
        "first_mention_composition_layers",
    ]
    assert context.visibility_defaults.stamp_kwargs()["replacement_applied"] is False


def test_build_visibility_enforcement_stage_context_groups_pre_route_objects() -> None:
    validation_result = {
        "ok": False,
        "violations": [
            {
                "kind": "unseen_entity_reference",
                "token": "Lord Aldric",
                "matched_entity_id": "lord_aldric",
            },
        ],
        "visibility_checked_entities": [{"entity_id": "lord_aldric"}],
        "visibility_checked_facts": [],
    }

    context = visibility_fallback.build_visibility_enforcement_stage_context(
        candidate_text="Lord Aldric watches the gate.",
        validation_result=validation_result,
        default_first_mention_composition_layers=["default_layer"],
        tag_list_gate=["known_fact_guard"],
        dbg_gate="recent_dialogue_continuity",
    )

    assert isinstance(context, visibility_fallback.VisibilityEnforcementStageContext)
    assert context.pre_route_validation.validation_result is validation_result
    assert context.pre_route_validation.candidate_text == "Lord Aldric watches the gate."
    assert context.pre_route_validation.observation.violation_kinds == ["unseen_entity_reference"]
    assert context.pre_route_metadata.first_mention_defaults.first_mention_composition_layers == ["default_layer"]
    assert context.pre_route_metadata.visibility_defaults.stamp_kwargs() == {
        "validation_passed": False,
        "replacement_applied": False,
        "violation_kinds": ["unseen_entity_reference"],
        "violation_sample": [
            {
                "kind": "unseen_entity_reference",
                "token": "Lord Aldric",
                "matched_entity_id": "lord_aldric",
                "matched_fact": None,
            }
        ],
        "checked_entities": [{"entity_id": "lord_aldric"}],
        "checked_facts": [],
    }
    assert context.route_decision_inputs == visibility_fallback.VisibilityRouteDecisionInputs(
        tag_list_gate=["known_fact_guard"],
        dbg_gate="recent_dialogue_continuity",
        violation_kinds=["unseen_entity_reference"],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
        candidate_text="Lord Aldric watches the gate.",
    )


def test_stamp_visibility_fallback_metadata_writes_visibility_fields_only() -> None:
    meta: dict[str, Any] = {"final_emitted_source": "global_scene_fallback"}

    visibility_fallback.stamp_visibility_fallback_metadata(
        meta,
        validation_passed=False,
        replacement_applied=True,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[{"kind": "unseen_entity_reference", "entity_id": "lord_aldric"}],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
    )

    assert meta == {
        "final_emitted_source": "global_scene_fallback",
        "visibility_validation_passed": False,
        "visibility_replacement_applied": True,
        "visibility_violation_kinds": ["unseen_entity_reference"],
        "visibility_violation_sample": [{"kind": "unseen_entity_reference", "entity_id": "lord_aldric"}],
        "visibility_checked_entities": [{"entity_id": "lord_aldric"}],
        "visibility_checked_facts": [],
        "visibility_fallback_pool": "global_scene_narrative",
        "visibility_fallback_kind": "narrative_safe_fallback",
        "visibility_fallback_owner_bucket": VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    }


def test_stamp_visibility_fallback_metadata_can_mark_nonreplacement_routes() -> None:
    meta: dict[str, Any] = {"visibility_replacement_applied": False}

    visibility_fallback.stamp_visibility_fallback_metadata(
        meta,
        validation_passed=True,
        replacement_applied=False,
        continuity_lead_exemption=True,
    )

    assert meta["visibility_validation_passed"] is True
    assert meta["visibility_replacement_applied"] is False
    assert meta["visibility_continuity_lead_exemption"] is True
    assert "visibility_fallback_owner_bucket" not in meta


def test_build_visibility_route_metadata_outcome_for_hard_replacement() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
    )

    outcome = visibility_fallback.build_visibility_route_metadata_outcome(
        observation=observation,
        route="sealed_hard_replace",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
    )

    assert outcome.validation_passed is False
    assert outcome.replacement_applied is True
    assert outcome.fallback_pool == "global_scene_narrative"
    assert outcome.fallback_kind == "narrative_safe_fallback"
    assert outcome.fallback_owner_bucket == VISIBILITY_FALLBACK_OWNER_SEALED_GATE
    assert outcome.stamp_kwargs() == {
        "validation_passed": False,
        "replacement_applied": True,
        "fallback_pool": "global_scene_narrative",
        "fallback_kind": "narrative_safe_fallback",
        "fallback_owner_bucket": VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    }


@pytest.mark.parametrize(
    ("route", "expected"),
    [
        (
            "continuity_lead_exemption",
            {
                "validation_passed": True,
                "replacement_applied": False,
                "continuity_lead_exemption": True,
            },
        ),
        (
            "concrete_interaction_no_hard_replace",
            {
                "validation_passed": None,
            },
        ),
    ],
)
def test_build_visibility_route_metadata_outcome_for_nonreplacement_routes(route: str, expected: dict[str, Any]) -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    outcome = visibility_fallback.build_visibility_route_metadata_outcome(
        observation=observation,
        route=route,
    )

    assert outcome.stamp_kwargs() == expected
    assert outcome.fallback_owner_bucket is None


def test_build_visibility_non_replacement_route_context_for_continuity_lead_exemption() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[{"kind": "unseen_entity_reference", "token": "Guard Captain"}],
        checked_entities=[{"entity_id": "guard_captain"}],
        checked_facts=[],
    )

    context = visibility_fallback.build_visibility_non_replacement_route_context(
        observation=observation,
        route="continuity_lead_exemption",
    )

    assert context == visibility_fallback.VisibilityNonReplacementRouteContext(
        route="continuity_lead_exemption",
        observation=observation,
        route_metadata_outcome=visibility_fallback.VisibilityRouteMetadataOutcome(
            validation_passed=True,
            replacement_applied=False,
            continuity_lead_exemption=True,
        ),
        return_token="apply_first_mention_enforcement",
        debug_notes_to_add=None,
    )
    assert context.route_metadata_outcome.stamp_kwargs() == {
        "validation_passed": True,
        "replacement_applied": False,
        "continuity_lead_exemption": True,
    }


def test_build_visibility_non_replacement_route_context_for_concrete_interaction_no_hard_replace() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    context = visibility_fallback.build_visibility_non_replacement_route_context(
        observation=observation,
        route="concrete_interaction_no_hard_replace",
    )

    assert context.route == "concrete_interaction_no_hard_replace"
    assert context.observation is observation
    assert context.return_token == "return_current_output"
    assert context.debug_notes_to_add is None
    assert context.route_metadata_outcome.stamp_kwargs() == {
        "validation_passed": None,
    }
    assert context.route_metadata_outcome.fallback_owner_bucket is None


def test_build_visibility_replacement_annotations_for_hard_replacement() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference", "undiscovered_fact_assertion"],
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    annotations = visibility_fallback.build_visibility_replacement_annotations(observation)

    assert annotations.tags_to_add == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:unseen_entity_reference",
        "visibility_violation:undiscovered_fact_assertion",
    ]
    assert (
        annotations.debug_notes_to_add
        == "final_emission_gate:visibility_replaced:unseen_entity_reference,undiscovered_fact_assertion"
    )


def test_build_visibility_replacement_annotations_caps_debug_violation_list() -> None:
    kinds = [f"kind_{index}" for index in range(10)]
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=kinds,
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    annotations = visibility_fallback.build_visibility_replacement_annotations(observation)

    assert annotations.tags_to_add == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
    ] + [f"visibility_violation:{kind}" for kind in kinds]
    assert annotations.debug_notes_to_add == "final_emission_gate:visibility_replaced:" + ",".join(kinds[:8])


def test_build_visibility_hard_replacement_plan_collects_side_effect_inputs() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[{"kind": "unseen_entity_reference", "token": "Lord Aldric"}],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
    )
    outcome = visibility_fallback.build_visibility_route_metadata_outcome(
        observation=observation,
        route="sealed_hard_replace",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
    )
    annotations = visibility_fallback.build_visibility_replacement_annotations(observation)
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta={},
    )

    plan = visibility_fallback.build_visibility_hard_replacement_plan(
        observation=observation,
        route_metadata_outcome=outcome,
        annotations=annotations,
        selected_fallback=selected_fallback,
    )

    assert plan == visibility_fallback.VisibilityHardReplacementPlan(
        fallback_text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        observation=observation,
        route_metadata_outcome=outcome,
        annotations=annotations,
    )
    assert plan.route_metadata_outcome.stamp_kwargs() == {
        "validation_passed": False,
        "replacement_applied": True,
        "fallback_pool": "global_scene_narrative",
        "fallback_kind": "narrative_safe_fallback",
        "fallback_owner_bucket": VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    }


def test_visibility_selected_fallback_round_trips_legacy_tuple() -> None:
    composition_meta = {
        "first_mention_composition_used": True,
        "first_mention_composition_layers": ["opening", "entity_intro"],
    }
    legacy = (
        "Selected fallback text.",
        "global_scene_narrative",
        "narrative_safe_fallback",
        "global_scene_fallback",
        "standard_safe_fallback",
        "global_scene_fallback",
        composition_meta,
    )

    selected = visibility_fallback.VisibilitySelectedFallback.from_legacy_tuple(legacy)

    assert selected == visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta=composition_meta,
    )
    assert selected.as_legacy_tuple() == legacy
    assert visibility_fallback.VisibilitySelectedFallback.from_legacy_tuple(legacy) == selected


def test_scene_emit_integrity_global_fallback_selection_returns_canonical_dataclass() -> None:
    """Gate global integrity selection returns the canonical visibility dataclass wire."""
    import game.final_emission_gate as feg

    scene = {"scene": {"id": "yard", "visible_facts": ["A guard watches the gate."]}}
    selection_kwargs = {
        "authoritative_resolution": None,
        "session": None,
        "world": None,
        "res_kind": "observe",
        "response_type_required": "narration",
    }
    selected = feg._scene_emit_integrity_global_fallback_selection(scene, "yard", **selection_kwargs)
    assert isinstance(selected, visibility_fallback.VisibilitySelectedFallback)
    assert selected.final_emitted_source == "global_scene_fallback"
    assert selected.fallback_pool == "global_scene_narrative"
    assert selected.fallback_kind == "narrative_safe_fallback"
    assert selected.fallback_strategy == "standard_safe_fallback"
    assert selected.fallback_candidate_source == "global_scene_fallback"
    assert selected.text


def test_passive_scene_pressure_candidates_return_canonical_dataclass() -> None:
    """Gate passive-pressure selection returns canonical visibility dataclass candidates."""
    import game.final_emission_gate as feg
    from game.defaults import default_session, default_world
    from game.storage import get_scene_runtime

    session = default_session()
    sid = "scene_investigate"
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_passive"] = True
    rt["passive_action_streak"] = 1
    rt["recent_contextual_leads"] = [
        {
            "key": "tattered-man-by-the-shuttered-well",
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
            "named": False,
            "positioned": True,
            "mentions": 2,
            "last_turn": 1,
        }
    ]
    scene = {"scene": {"id": sid, "location": "square", "visible_facts": []}}
    kwargs = {"session": session, "scene": scene, "scene_id": sid}
    selected = feg._passive_scene_pressure_fallback_candidates(**kwargs)
    assert selected
    assert all(isinstance(candidate, visibility_fallback.VisibilitySelectedFallback) for candidate in selected)
    assert selected[0].final_emitted_source == "passive_scene_pressure_fallback"
    assert selected[0].fallback_pool == "passive_scene_pressure"
    assert selected[0].fallback_strategy == "passive_scene_pressure_fallback"
    assert "passive_scene_pressure:lead_figure" == selected[0].fallback_candidate_source


def test_grounded_scene_intro_fallback_candidates_return_canonical_dataclass() -> None:
    import game.final_emission_gate as feg

    from game.defaults import default_scene, default_session, default_world
    from game.interaction_context import rebuild_active_scene_entities

    session = default_session()
    world = default_world()
    scene = default_scene("frontier_gate")
    scene["scene"]["visible_facts"] = ["A brazier throws orange sparks over the checkpoint."]
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    kwargs = {
        "session": session,
        "scene": scene,
        "world": world,
        "active_interlocutor": "guard_captain",
    }
    selected = feg._grounded_scene_intro_fallback_candidates(**kwargs)
    assert selected
    assert all(isinstance(candidate, visibility_fallback.VisibilitySelectedFallback) for candidate in selected)
    dedup_keys = {
        (
            candidate.text,
            candidate.fallback_pool,
            candidate.fallback_kind,
            candidate.final_emitted_source,
            candidate.fallback_strategy,
            candidate.fallback_candidate_source,
        )
        for candidate in selected
    }
    assert len(dedup_keys) == len(selected)
    assert any(candidate.fallback_pool == "visible_scene_composed_intro" for candidate in selected)
    assert any(candidate.final_emitted_source == "visible_fact_scene_intro" for candidate in selected)


def test_build_visibility_first_mention_metadata_payload_collects_composition_values() -> None:
    payload = visibility_fallback.build_visibility_first_mention_metadata_payload(
        composition_meta={
            "first_mention_composition_used": True,
            "first_mention_composition_layers": ["opening", "entity_intro"],
        },
        default_first_mention_composition_layers=["default"],
    )

    assert payload == visibility_fallback.VisibilityFirstMentionMetadataPayload(
        first_mention_composition_used=True,
        first_mention_composition_layers=["opening", "entity_intro"],
    )
    assert payload.meta_updates() == {
        "first_mention_composition_used": True,
        "first_mention_composition_layers": ["opening", "entity_intro"],
    }


def test_build_visibility_first_mention_metadata_payload_defaults_when_composition_empty() -> None:
    payload = visibility_fallback.build_visibility_first_mention_metadata_payload(
        composition_meta={},
        default_first_mention_composition_layers=["default"],
    )

    assert payload.meta_updates() == {
        "first_mention_composition_used": False,
        "first_mention_composition_layers": ["default"],
    }


def test_build_first_mention_selected_fallback_metadata_payload_collects_replacement_fields() -> None:
    layers = {"environment": "market", "motion": "approach", "entities": ["Tavern Runner"]}
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="scene_opening_deterministic",
        fallback_kind="opening_deterministic_fallback",
        final_emitted_source="opening_scene_fallback",
        fallback_strategy="opening_scene_safe_fallback",
        fallback_candidate_source="upstream_prepared_opening_fallback",
        composition_meta={
            "first_mention_composition_used": True,
            "first_mention_composition_layers": layers,
        },
    )

    payload = visibility_fallback.build_first_mention_selected_fallback_metadata_payload(
        selected_fallback,
        opening_scene_first_mention_preference_used=True,
        default_first_mention_composition_layers={"environment": None, "motion": None, "entities": []},
    )

    assert payload == visibility_fallback.FirstMentionSelectedFallbackMetadataPayload(
        first_mention_validation_passed=False,
        first_mention_replacement_applied=True,
        first_mention_fallback_strategy="opening_scene_safe_fallback",
        first_mention_fallback_candidate_source="upstream_prepared_opening_fallback",
        opening_scene_first_mention_preference_used=True,
        first_mention_composition_used=True,
        first_mention_composition_layers=layers,
    )
    assert list(payload.meta_updates()) == [
        "first_mention_validation_passed",
        "first_mention_replacement_applied",
        "first_mention_fallback_strategy",
        "first_mention_fallback_candidate_source",
        "opening_scene_first_mention_preference_used",
        "first_mention_composition_used",
        "first_mention_composition_layers",
    ]
    assert payload.meta_updates()["first_mention_composition_layers"] is layers


def test_build_first_mention_selected_fallback_metadata_payload_uses_default_layers() -> None:
    default_layers = {"environment": None, "motion": None, "entities": []}
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta={},
    )

    payload = visibility_fallback.build_first_mention_selected_fallback_metadata_payload(
        selected_fallback,
        opening_scene_first_mention_preference_used=False,
        default_first_mention_composition_layers=default_layers,
    )

    assert payload.meta_updates() == {
        "first_mention_validation_passed": False,
        "first_mention_replacement_applied": True,
        "first_mention_fallback_strategy": "standard_safe_fallback",
        "first_mention_fallback_candidate_source": "global_scene_fallback",
        "opening_scene_first_mention_preference_used": False,
        "first_mention_composition_used": False,
        "first_mention_composition_layers": default_layers,
    }


def test_build_referential_clarity_selected_fallback_metadata_payload_collects_replacement_fields() -> None:
    layers = {"environment": "street", "motion": None, "entities": ["Guard Captain"]}
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="strict_social_visibility_minimal",
        fallback_kind="visibility_minimal_social_fallback",
        final_emitted_source="minimal_social_emergency_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="minimal_social_emergency_fallback",
        composition_meta={
            "first_mention_composition_used": True,
            "first_mention_composition_layers": layers,
        },
    )

    payload = visibility_fallback.build_referential_clarity_selected_fallback_metadata_payload(
        selected_fallback,
        default_first_mention_composition_layers={"environment": None, "motion": None, "entities": []},
    )

    assert payload == visibility_fallback.ReferentialClaritySelectedFallbackMetadataPayload(
        referential_clarity_validation_passed=False,
        referential_clarity_replacement_applied=True,
        first_mention_composition_used=True,
        first_mention_composition_layers=layers,
    )
    assert list(payload.meta_updates()) == [
        "referential_clarity_validation_passed",
        "referential_clarity_replacement_applied",
        "first_mention_composition_used",
        "first_mention_composition_layers",
    ]
    assert payload.meta_updates()["first_mention_composition_layers"] is layers


def test_build_referential_clarity_selected_fallback_metadata_payload_uses_default_layers() -> None:
    default_layers = {"environment": None, "motion": None, "entities": []}
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta={},
    )

    payload = visibility_fallback.build_referential_clarity_selected_fallback_metadata_payload(
        selected_fallback,
        default_first_mention_composition_layers=default_layers,
    )

    assert payload.meta_updates() == {
        "referential_clarity_validation_passed": False,
        "referential_clarity_replacement_applied": True,
        "first_mention_composition_used": False,
        "first_mention_composition_layers": default_layers,
    }


def test_build_first_mention_replacement_logging_payload_matches_gate_decision_shape() -> None:
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="scene_opening_deterministic",
        fallback_kind="opening_deterministic_fallback",
        final_emitted_source="opening_scene_fallback",
        fallback_strategy="opening_scene_safe_fallback",
        fallback_candidate_source="upstream_prepared_opening_fallback",
        composition_meta={},
    )
    violation_kinds = [f"kind_{index}" for index in range(14)]

    payload = visibility_fallback.build_first_mention_replacement_logging_payload(
        selected_fallback,
        strict_social_active=True,
        violation_kinds=violation_kinds,
        active_interlocutor="tavern_runner",
    )

    assert payload == visibility_fallback.FirstMentionReplacementLoggingPayload(
        social_route=True,
        candidate_ok=False,
        rejection_reasons=violation_kinds[:12],
        fallback_pool="scene_opening_deterministic",
        fallback_kind="opening_deterministic_fallback",
        active_interlocutor="tavern_runner",
    )
    assert payload.decision_payload() == {
        "stage": "final_emission_gate_first_mention",
        "social_route": True,
        "candidate_ok": False,
        "rejection_reasons": violation_kinds[:12],
        "fallback_pool": "scene_opening_deterministic",
        "fallback_kind": "opening_deterministic_fallback",
        "active_interlocutor": "tavern_runner",
    }
    assert list(payload.decision_payload()) == [
        "stage",
        "social_route",
        "candidate_ok",
        "rejection_reasons",
        "fallback_pool",
        "fallback_kind",
        "active_interlocutor",
    ]
    violation_kinds.append("late_mutation")
    assert payload.decision_payload()["rejection_reasons"] == [f"kind_{index}" for index in range(12)]


def test_build_first_mention_replacement_logging_payload_normalizes_empty_interlocutor() -> None:
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta={},
    )

    payload = visibility_fallback.build_first_mention_replacement_logging_payload(
        selected_fallback,
        strict_social_active=False,
        violation_kinds=["first_mention_unearned_familiarity"],
        active_interlocutor="",
    )

    assert payload.decision_payload()["active_interlocutor"] is None
    assert payload.decision_payload()["rejection_reasons"] == ["first_mention_unearned_familiarity"]


def test_build_referential_clarity_replacement_logging_payload_matches_gate_decision_shape() -> None:
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="strict_social_visibility_minimal",
        fallback_kind="visibility_minimal_social_fallback",
        final_emitted_source="minimal_social_emergency_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="minimal_social_emergency_fallback",
        composition_meta={},
    )
    violation_kinds = [f"kind_{index}" for index in range(13)]

    payload = visibility_fallback.build_referential_clarity_replacement_logging_payload(
        selected_fallback,
        strict_social_active=True,
        violation_kinds=violation_kinds,
        active_interlocutor="guard_captain",
        referential_clarity_fallback_after_failed_local_repair=True,
    )

    assert payload == visibility_fallback.ReferentialClarityReplacementLoggingPayload(
        social_route=True,
        candidate_ok=False,
        rejection_reasons=violation_kinds[:12],
        fallback_pool="strict_social_visibility_minimal",
        fallback_kind="visibility_minimal_social_fallback",
        active_interlocutor="guard_captain",
        referential_clarity_fallback_after_failed_local_repair=True,
    )
    assert payload.decision_payload() == {
        "stage": "final_emission_gate_referential_clarity",
        "social_route": True,
        "candidate_ok": False,
        "rejection_reasons": violation_kinds[:12],
        "fallback_pool": "strict_social_visibility_minimal",
        "fallback_kind": "visibility_minimal_social_fallback",
        "active_interlocutor": "guard_captain",
        "referential_clarity_fallback_after_failed_local_repair": True,
    }
    assert list(payload.decision_payload()) == [
        "stage",
        "social_route",
        "candidate_ok",
        "rejection_reasons",
        "fallback_pool",
        "fallback_kind",
        "active_interlocutor",
        "referential_clarity_fallback_after_failed_local_repair",
    ]


def test_build_referential_clarity_replacement_logging_payload_normalizes_boolean_and_interlocutor() -> None:
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta={},
    )

    payload = visibility_fallback.build_referential_clarity_replacement_logging_payload(
        selected_fallback,
        strict_social_active=False,
        violation_kinds=["ambiguous_entity_reference"],
        active_interlocutor="",
        referential_clarity_fallback_after_failed_local_repair=1,
    )

    assert payload.decision_payload()["active_interlocutor"] is None
    assert payload.decision_payload()["referential_clarity_fallback_after_failed_local_repair"] is True


def test_build_visibility_hard_replacement_logging_payload_collects_decision_and_trace_inputs() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference", "undiscovered_fact_assertion"],
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    payload = visibility_fallback.build_visibility_hard_replacement_logging_payload(
        strict_social_active=True,
        observation=observation,
        fallback_pool="strict_social_visibility_minimal",
        fallback_kind="visibility_minimal_social_fallback",
        active_interlocutor="tavern_runner",
    )

    assert payload == visibility_fallback.VisibilityHardReplacementLoggingPayload(
        social_route=True,
        candidate_ok=False,
        rejection_reasons=["unseen_entity_reference", "undiscovered_fact_assertion"],
        fallback_pool="strict_social_visibility_minimal",
        fallback_kind="visibility_minimal_social_fallback",
        active_interlocutor="tavern_runner",
        trace_stage="final_emission_gate_visibility_replace",
    )
    assert payload.decision_payload() == {
        "stage": "final_emission_gate_visibility",
        "social_route": True,
        "candidate_ok": False,
        "rejection_reasons": ["unseen_entity_reference", "undiscovered_fact_assertion"],
        "fallback_pool": "strict_social_visibility_minimal",
        "fallback_kind": "visibility_minimal_social_fallback",
        "active_interlocutor": "tavern_runner",
    }
    assert payload.trace_payload({"visibility_replacement_applied": True}) == {
        "visibility_replacement_applied": True,
        "stage": "final_emission_gate_visibility_replace",
    }


def test_build_visibility_hard_replacement_logging_payload_caps_reasons_and_normalizes_empty_interlocutor() -> None:
    kinds = [f"kind_{index}" for index in range(14)]
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=kinds,
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    payload = visibility_fallback.build_visibility_hard_replacement_logging_payload(
        strict_social_active=False,
        observation=observation,
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        active_interlocutor="",
    )

    assert payload.decision_payload()["rejection_reasons"] == kinds[:12]
    assert payload.decision_payload()["active_interlocutor"] is None


def test_build_visibility_hard_replacement_context_groups_existing_payloads() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[{"kind": "unseen_entity_reference", "token": "Lord Aldric"}],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
    )
    selected_fallback = visibility_fallback.VisibilitySelectedFallback(
        text="Selected fallback text.",
        fallback_pool="global_scene_narrative",
        fallback_kind="narrative_safe_fallback",
        final_emitted_source="global_scene_fallback",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="global_scene_fallback",
        composition_meta={
            "first_mention_composition_used": True,
            "first_mention_composition_layers": ["opening", "entity_intro"],
        },
    )

    context = visibility_fallback.build_visibility_hard_replacement_context(
        observation=observation,
        route="sealed_hard_replace",
        selected_fallback=selected_fallback,
        default_first_mention_composition_layers=["default"],
        strict_social_active=False,
        active_interlocutor="",
    )

    assert isinstance(context, visibility_fallback.VisibilityHardReplacementContext)
    assert context.replacement_plan.fallback_text == "Selected fallback text."
    assert context.replacement_plan.final_emitted_source == "global_scene_fallback"
    assert context.replacement_plan.annotations.tags_to_add == [
        "final_emission_gate_replaced",
        "visibility_enforcement_replaced",
        "visibility_violation:unseen_entity_reference",
    ]
    assert context.replacement_plan.route_metadata_outcome.stamp_kwargs() == {
        "validation_passed": False,
        "replacement_applied": True,
        "fallback_pool": "global_scene_narrative",
        "fallback_kind": "narrative_safe_fallback",
        "fallback_owner_bucket": VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    }
    assert context.first_mention_payload.meta_updates() == {
        "first_mention_composition_used": True,
        "first_mention_composition_layers": ["opening", "entity_intro"],
    }
    assert context.logging_payload.decision_payload() == {
        "stage": "final_emission_gate_visibility",
        "social_route": False,
        "candidate_ok": False,
        "rejection_reasons": ["unseen_entity_reference"],
        "fallback_pool": "global_scene_narrative",
        "fallback_kind": "narrative_safe_fallback",
        "active_interlocutor": None,
    }


def test_visibility_fallback_helper_module_contains_no_fallback_prose_literals() -> None:
    source = inspect.getsource(visibility_fallback)
    module = ast.parse(source)
    string_literals = [
        node.value
        for node in ast.walk(module)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]

    forbidden_fragments = [
        "For a breath",
        "scene holds",
        "scene stays still",
        "voices shift around you",
    ]
    for literal in string_literals:
        for fragment in forbidden_fragments:
            assert fragment not in literal


def test_build_visibility_fallback_selection_inputs_collects_hard_replace_context() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
    )

    bundle = visibility_fallback.build_visibility_fallback_selection_inputs(
        observation=observation,
        route="sealed_hard_replace",
        active_interlocutor="guard_captain",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
        emit_integrity_response_type_required="",
        response_type_required_meta="dialogue",
    )

    assert bundle == visibility_fallback.VisibilityFallbackSelectionInputs(
        route="sealed_hard_replace",
        strict_social_route=True,
        strict_social_suppressed_non_social_turn=False,
        has_active_social_interlocutor=True,
        violation_kinds=["unseen_entity_reference"],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
        emit_integrity_response_type_required="dialogue",
    )


def test_build_visibility_fallback_selection_inputs_prefers_explicit_response_type_context() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=[],
        violation_sample=[],
        checked_entities=[],
        checked_facts=[{"fact": "hidden"}],
    )

    bundle = visibility_fallback.build_visibility_fallback_selection_inputs(
        observation=observation,
        route="sealed_hard_replace",
        active_interlocutor=" ",
        strict_social_active=False,
        strict_social_suppressed_non_social_turn=True,
        emit_integrity_response_type_required="answer",
        response_type_required_meta="dialogue",
    )

    assert bundle.strict_social_route is False
    assert bundle.strict_social_suppressed_non_social_turn is True
    assert bundle.has_active_social_interlocutor is False
    assert bundle.checked_facts == [{"fact": "hidden"}]
    assert bundle.emit_integrity_response_type_required == "answer"


def test_build_visibility_route_dispatch_context_for_sealed_hard_replace() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
    )

    context = visibility_fallback.build_visibility_route_dispatch_context(
        observation=observation,
        route="sealed_hard_replace",
        active_interlocutor="guard_captain",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
        emit_integrity_response_type_required="",
        response_type_required_meta="dialogue",
    )

    assert context.route == "sealed_hard_replace"
    assert context.observation is observation
    assert context.non_replacement_context is None
    assert context.selection_inputs == visibility_fallback.VisibilityFallbackSelectionInputs(
        route="sealed_hard_replace",
        strict_social_route=True,
        strict_social_suppressed_non_social_turn=False,
        has_active_social_interlocutor=True,
        violation_kinds=["unseen_entity_reference"],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[],
        emit_integrity_response_type_required="dialogue",
    )


def test_build_visibility_route_dispatch_context_for_continuity_lead_exemption() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    context = visibility_fallback.build_visibility_route_dispatch_context(
        observation=observation,
        route="continuity_lead_exemption",
        active_interlocutor="guard_captain",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=True,
        emit_integrity_response_type_required="answer",
        response_type_required_meta="dialogue",
    )

    assert context.route == "continuity_lead_exemption"
    assert context.observation is observation
    assert context.selection_inputs is None
    assert context.non_replacement_context is not None
    assert context.non_replacement_context.return_token == "apply_first_mention_enforcement"
    assert context.non_replacement_context.route_metadata_outcome.stamp_kwargs() == {
        "validation_passed": True,
        "replacement_applied": False,
        "continuity_lead_exemption": True,
    }


def test_build_visibility_route_dispatch_context_for_concrete_interaction_no_hard_replace() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[],
        checked_facts=[],
    )

    context = visibility_fallback.build_visibility_route_dispatch_context(
        observation=observation,
        route="concrete_interaction_no_hard_replace",
        active_interlocutor="",
        strict_social_active=False,
        strict_social_suppressed_non_social_turn=False,
        emit_integrity_response_type_required="",
        response_type_required_meta="",
    )

    assert context.route == "concrete_interaction_no_hard_replace"
    assert context.observation is observation
    assert context.selection_inputs is None
    assert context.non_replacement_context is not None
    assert context.non_replacement_context.return_token == "return_current_output"
    assert context.non_replacement_context.route_metadata_outcome.stamp_kwargs() == {
        "validation_passed": None,
    }


def test_build_visibility_route_decision_inputs_collects_selector_arguments() -> None:
    observation = visibility_fallback.VisibilityValidationObservation(
        validation_passed=False,
        violation_kinds=["unseen_entity_reference"],
        violation_sample=[],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[{"fact": "hidden"}],
    )
    tags = ["known_fact_guard", "other"]

    bundle = visibility_fallback.build_visibility_route_decision_inputs(
        tag_list_gate=tags,
        dbg_gate="recent_dialogue_continuity",
        observation=observation,
        candidate_text="Lord Aldric watches.",
    )

    assert bundle == visibility_fallback.VisibilityRouteDecisionInputs(
        tag_list_gate=["known_fact_guard", "other"],
        dbg_gate="recent_dialogue_continuity",
        violation_kinds=["unseen_entity_reference"],
        checked_entities=[{"entity_id": "lord_aldric"}],
        checked_facts=[{"fact": "hidden"}],
        candidate_text="Lord Aldric watches.",
    )
    tags.append("late_mutation")
    observation.violation_kinds.append("late_kind")
    assert bundle.tag_list_gate == ["known_fact_guard", "other"]
    assert bundle.violation_kinds == ["unseen_entity_reference"]
