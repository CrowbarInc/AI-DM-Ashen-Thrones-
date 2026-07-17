"""Visibility, referential, and hard-replacement fallback projection coverage."""
from __future__ import annotations

import pytest

from game.ownership_projection_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
)

from game.attribution_read_views import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
    VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.failure_classifier import validate_failure_classification_row
from tests.helpers.failure_classification_sync import (
    assert_split_owner_matrix_fem_projection,
    assert_split_owner_matrix_lineage_event,
    classify_replay_probe_row,
    exact_value_drift_row,
    project_split_owner_matrix_row,
    split_owner_acceptance_matrix_rows,
    split_owner_fem_projection_excluded,
    split_owner_lineage_event_from_matrix_row,
    split_owner_observed_row_from_matrix_row,
)
from tests.helpers.golden_replay_api import (
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    classify_golden_drift,
    format_golden_replay_debug,
    summarize_long_session_replay_observations,
)
from tests.helpers.golden_replay_fixtures import (
    fem_payload,
    minimal_gm_output_payload,
    project_synthetic_turn,
)
from tests.helpers.opening_fallback_evidence import (
    fail_closed_opening_fem_meta,
    successful_opening_fem_meta,
)

from tests.helpers.golden_replay_fallback_projection_helpers import (
    fallback_selected_event as _fallback_selected_event,
    mutation_event as _mutation_event,
)


def test_golden_projection_projects_visibility_fallback_evidence() -> None:
    observed = project_synthetic_turn(
        scenario_id="synthetic_visibility_owner",
        gm_text="A visibility fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket=VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            visibility_replacement_applied=True,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == VISIBILITY_FALLBACK_OWNER_SEALED_GATE
    assert observed["visibility_replacement_applied"] is True
    assert observed["visibility_fallback_pool"] == "global_scene_narrative"
    assert observed["visibility_fallback_kind"] == "narrative_safe_fallback"


@pytest.mark.parametrize(
    ("scenario_id", "pool", "kind", "source", "expected_bucket"),
    [
        (
            "visibility_hard_replace_sealed_gate",
            "global_scene_narrative",
            "narrative_safe_fallback",
            "global_scene_fallback",
            VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
        ),
        (
            "visibility_hard_replace_strict_social",
            "strict_social_visibility_minimal",
            "visibility_minimal_social_fallback",
            "minimal_social_emergency_fallback",
            VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        ),
        (
            "visibility_hard_replace_opening_visibility",
            "scene_opening_deterministic",
            "opening_deterministic_fallback",
            "opening_deterministic_fallback",
            VISIBILITY_FALLBACK_OWNER_OPENING_VISIBILITY,
        ),
    ],
)
def test_golden_projection_projects_visibility_hard_replacement_canonical_owner_buckets(
    scenario_id: str,
    pool: str,
    kind: str,
    source: str,
    expected_bucket: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=scenario_id,
        gm_text="A visibility hard-replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source=source,
            visibility_fallback_owner_bucket=expected_bucket,
            visibility_replacement_applied=True,
            visibility_fallback_pool=pool,
            visibility_fallback_kind=kind,
            producer_repair_kind="visibility_enforcement",
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == expected_bucket
    assert observed["visibility_fallback_pool"] == pool
    assert observed["visibility_fallback_kind"] == kind

@pytest.mark.parametrize(
    (
        "scenario_id",
        "replacement_flag",
        "fallback_kind",
        "producer_repair_kind",
        "mutation_kind",
        "expected_bucket",
        "expected_content_owner",
    ),
    [
        (
            "visibility_hard_replace_split_owner",
            {"visibility_replacement_applied": True},
            "visibility_hard_replacement",
            "visibility_enforcement",
            "visibility_replacement_mutation",
            VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "first_mention_hard_replace_split_owner",
            {"first_mention_replacement_applied": True},
            "first_mention_hard_replacement",
            "first_mention_enforcement",
            "first_mention_replacement_mutation",
            VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        ),
        (
            "referential_hard_replace_split_owner",
            {"referential_clarity_replacement_applied": True},
            "referential_clarity_hard_replacement",
            "referential_clarity_enforcement",
            "referential_clarity_replacement_mutation",
            VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
            "game.social_exchange_emission",
        ),
    ],
)
def test_golden_projection_projects_visibility_family_hard_replacement_split_owner_trifecta(
    scenario_id: str,
    replacement_flag: dict[str, bool],
    fallback_kind: str,
    producer_repair_kind: str,
    mutation_kind: str,
    expected_bucket: str,
    expected_content_owner: str,
) -> None:
    observed = project_synthetic_turn(
        scenario_id=scenario_id,
        gm_text="A visibility-family hard-replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket=expected_bucket,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            producer_repair_kind=producer_repair_kind,
            **replacement_flag,
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == expected_bucket
    fallback = _fallback_selected_event(observed)
    assert fallback["fallback_kind"] == fallback_kind
    assert fallback["fallback_owner_bucket"] == expected_bucket
    assert fallback["fallback_selection_owner"] == VISIBILITY_FALLBACK_SELECTION_OWNER
    assert fallback["fallback_content_owner"] == expected_content_owner
    assert fallback["repair_kind"] == producer_repair_kind
    mutation = _mutation_event(observed, mutation_kind)
    assert mutation["mutation_kind"] == mutation_kind


def test_golden_projection_projects_referential_local_substitution_owner_bucket_and_repair_kind() -> None:
    observed = project_synthetic_turn(
        scenario_id="referential_local_substitution_projection",
        gm_text="The Tavern Runner says she will return.",
        fem_meta=fem_payload(
            final_route="accept_candidate",
            referential_clarity_local_substitution_applied=True,
            referential_clarity_local_substitution_token="she",
            referential_clarity_local_substitution_replacement="The Tavern Runner",
            visibility_fallback_owner_bucket=VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
            producer_repair_kind="referential_clarity_local_substitution",
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY
    mutation = _mutation_event(observed, "referential_clarity_local_substitution_mutation")
    assert mutation["owner"] == "game.final_emission_gate"
    assert mutation["source"] == "she"


def test_golden_projection_observed_turn_passes_classifier_contract_for_visibility_family_split_owners() -> None:
    from tests.helpers.failure_classification_sync import classify_replay_probe_row

    observed = project_synthetic_turn(
        scenario_id="golden_classifier_visibility_family_bridge",
        gm_text="A first-mention hard-replacement line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            first_mention_replacement_applied=True,
            visibility_fallback_owner_bucket=VISIBILITY_FALLBACK_OWNER_SEALED_GATE,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            producer_repair_kind="first_mention_enforcement",
        ),
    )
    row = classify_replay_probe_row(
        observed_turn=observed,
        drift_row=exact_value_drift_row(
            "fallback_content_owner",
            expected="game.final_emission_gate",
            actual=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
            reason="golden replay classifier bridge",
        ),
        scenario_id=observed["scenario_id"],
        turn_index=observed["turn_index"],
    )

    assert row["fallback_selection_owner"] == VISIBILITY_FALLBACK_SELECTION_OWNER
    assert row["fallback_content_owner"] == SEALED_FALLBACK_MODULE_CONTENT_OWNER
    assert row["visibility_fallback_owner_bucket"] == VISIBILITY_FALLBACK_OWNER_SEALED_GATE
    assert row["repair_kind"] == "first_mention_enforcement"
    assert validate_failure_classification_row(row) == []
