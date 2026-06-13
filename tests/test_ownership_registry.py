"""Lightweight direct-owner registry + governance checks (tests only; no runtime hooks).

This module answers: *who may authoritatively define a new legality rule or shipped contract
edge case?* It does **not** claim to catalog all meaningful coverage.

Design notes (read before extending):
- **Direct owner** = exactly one canonical test module that is allowed to introduce detailed
  normative assertions for the responsibility. Other suites may overlap behaviorally.
- **Neighbor** paths (smoke, transcript, gauntlet, evaluator, downstream consumer, compatibility
  residue) are *supporting* surfaces. They must not be named as the direct owner for **live
  legality** responsibilities (gate-era rules, sanitizer post-processing, shipped policy
  materialization, etc.).
- **Downstream consumer** suites (Cycle AD-3 / AL4): integration-visible smoke only — player-facing
  text hygiene, repair/replacement evidence, contract threading through HTTP/API, and
  layer-specific checked/failed/repaired fields owned by that consumer (e.g. answer
  completeness, response delta). They must **not** restate exact gate orchestration tables
  (``final_route``, ``final_emitted_source``, owner-bucket mapping, repair-kind enumeration)
  already owned by ``tests/test_final_emission_gate.py``; prefer
  ``tests/helpers/emission_smoke_assertions.py`` for route/phrase smoke helpers.
- **Smoke facade** (Cycle AL4): ``tests/helpers/emission_smoke_assertions.py`` is the intended
  downstream assertion surface for HTTP/pipeline wiring — intentionally weaker than owner
  legality suites. Replay/golden projection helpers stay separate
  (``tests/helpers/golden_replay_projection.py``, ``tests/helpers/opening_fallback_evidence.py``).
- **Smoke suites**: survival / wiring / one-phrase hygiene checks; not full legality matrices.
- **Gauntlet / replay neighbors** (e.g. ``tests/test_golden_replay.py``): intentional
  diagnostic observation and drift projection locks — not runtime gate orchestration owners.
  Classifier/dashboard FEM bucket columns follow the same rule (diagnostic projection, not
  gate ownership).
- New validation rules should land with a clear direct owner first; only then add broad
  regression, transcript, or gauntlet coverage so failures stay attributable.
- **Gate magnet guard** (Cycle BA-7 / AG-10): gate-layer direct-owner suites (except FEM meta
  projection and gauntlet) must not import ``golden_replay_projection``, classifier, or
  dashboard read-side helpers, or accumulate replay/dashboard/classifier projection assertions.
  Enforced by ``test_ba7_gate_direct_owners_*`` in this module.
- **Gate dependency compression guard** (Cycle BD-6): non-owner tests must not reintroduce
  direct imports of gate entry, FEM read, replay projection, or owner-bucket constants already
  routed through helper facades during BD-2–BD-5. Enforced by ``test_bd6_gate_dependency_compression_*``.

Governance consumes the live inventory from ``tests/test_inventory_governance.json`` (regenerate via
``py -3 tools/test_audit.py``). Unclassified test files elsewhere in the repo do not affect
these checks.

Cycle AL4 legality-owner quick reference (downstream suites assert wiring/smoke only):
- Final emission gate orchestration / route tables → ``tests/test_final_emission_gate.py``
  (``final_emission_gate_orchestration``)
- FEM projection / lineage → ``tests/test_final_emission_meta.py`` (``final_emission_meta_projection``)
- Dialogue route classification table → ``tests/test_dialogue_routing_lock.py`` (pure
  ``choose_interaction_route``; HTTP packaging smoke → ``tests/test_turn_pipeline_shared.py``)
- Sanitizer phrase legality → ``tests/test_output_sanitizer.py`` (``output_sanitizer_final_string_cleanup``)
- Strict-social phrase/source legality → ``tests/test_social_exchange_emission.py``
  (``social_emission_legality_surface``)
- Downstream HTTP smoke/wiring → ``tests/test_turn_pipeline_shared.py`` (registered neighbor)
- Downstream smoke facade → ``tests/helpers/emission_smoke_assertions.py`` (helpers module)

Cycle BE6 — triple-layer scaffold / phrase split (documentation lock; **do not merge**):

1. ``tests/test_output_sanitizer.py`` — full sanitizer/procedural phrase **legality matrices**
2. ``tests/helpers/emission_smoke_assertions.py`` — weak HTTP/pipeline **smoke** phrases only
3. ``tests/helpers/golden_replay_projection.py`` — replay **scaffold-leakage projection**
   (``final_text_has_scaffold_leakage``, protected observation path)

Assertion-economy blocks must not unify these into one shared phrase matrix. Enforced by
``test_be6_scaffold_phrase_triple_layer_split_locked``.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import types
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import AbstractSet, Final, Mapping, Tuple

import pytest

try:
    from game import validation_layer_contracts as vlc
except ImportError:  # pragma: no cover - repo layout guard
    vlc = None  # type: ignore[assignment]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_INVENTORY_PATH = _REPO_ROOT / "tests" / "test_inventory_governance.json"
_TEST_AUDIT_PATH = _REPO_ROOT / "tools" / "test_audit.py"

# ---------------------------------------------------------------------------
# Canonical validation-layer ids (engine / planner / gpt / gate / evaluator)
# ---------------------------------------------------------------------------

_CANONICAL: Final[AbstractSet[str]] = (
    frozenset(vlc.CANONICAL_VALIDATION_LAYERS)
    if vlc is not None
    else frozenset({"engine", "planner", "gpt", "gate", "evaluator"})
)

# Heuristic inventory buckets that are too noisy to treat as contradicting a canonical owner.
_PERMISSIVE_INVENTORY_LAYERS: Final[AbstractSet[str]] = frozenset(
    {"smoke", "transcript", "gauntlet", "general"},
)

# Adjacent layers often co-score in static import heuristics; treat as compatible, not drift.
_SOFT_ADJACENT: Final[AbstractSet[frozenset[str]]] = frozenset(
    {
        frozenset({"engine", "planner"}),
        frozenset({"engine", "gpt"}),
        frozenset({"planner", "gpt"}),
    }
)

_LIVE_LEGALITY_GROUP_IDS: Final[AbstractSet[str]] = frozenset(
    {
        "final_emission_gate_orchestration",
        "final_emission_validators",
        "final_emission_repairs",
        "response_policy_contract_materialization",
        "prompt_context_contract_assembly",
        "output_sanitizer_final_string_cleanup",
        "social_emission_legality_surface",
    }
)

# Cycle AD-3: integration downstream smoke paths — registry neighbors only, never direct_owner.
_DOWNSTREAM_INTEGRATION_SMOKE_ONLY: Final[frozenset[str]] = frozenset(
    {
        "tests/test_turn_pipeline_shared.py",
        "tests/test_answer_completeness_rules.py",
        "tests/test_response_delta_requirement.py",
    }
)

# Cycle AL4: documented downstream smoke facade (helpers module — not a pytest suite path).
_DOWNSTREAM_SMOKE_FACADE: Final[str] = "tests/helpers/emission_smoke_assertions.py"

# Cycle AL4: legality owners locked by AL1–AL3 convergence (see module docstring).
_AL4_LEGALITY_OWNER_PATHS: Final[Mapping[str, str]] = {
    "final_emission_gate": "tests/test_final_emission_gate.py",
    "final_emission_meta": "tests/test_final_emission_meta.py",
    "dialogue_route_classification": "tests/test_dialogue_routing_lock.py",
    "output_sanitizer": "tests/test_output_sanitizer.py",
    "social_exchange_emission": "tests/test_social_exchange_emission.py",
    "turn_pipeline_http_smoke": "tests/test_turn_pipeline_shared.py",
}

# Cycle BA-7 / AG-10: gate orchestration direct owners must not import replay/dashboard/classifier
# read-side projection helpers (FEM meta projection + gauntlet/classifier neighbors are excluded).
_GATE_MAGNET_GUARD_EXCLUDED_GROUP_IDS: Final[frozenset[str]] = frozenset(
    {
        "final_emission_meta_projection",
        "gauntlet_playability_validation",
    }
)
_GATE_MAGNET_GUARD_EXCLUDED_PATHS: Final[frozenset[str]] = frozenset(
    {
        "tests/test_failure_classifier.py",
        "tests/test_failure_classification_contract.py",
        "tests/test_failure_dashboard_controlled_failures.py",
        "tests/test_golden_replay.py",
    }
)
_FORBIDDEN_REPLAY_READ_SIDE_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "tests.helpers.golden_replay_projection",
    "tests.helpers.golden_replay",
    "tests.helpers.failure_classifier",
    "tests.helpers.failure_dashboard_report",
    "tests.helpers.failure_dashboard_fixtures",
    "game.final_emission_replay_projection",
)
_FORBIDDEN_GATE_READ_SIDE_SOURCE_FRAGMENTS: Final[tuple[str, ...]] = (
    "game.final_emission_replay_projection",
    "read_side_lineage_projection_surface",
    "project_sealed_replacement_subkind_from_fem",
    "SEALED_REPLACEMENT_SUBKIND",
    "SEALED_REPLACEMENT_SUBKINDS",
    "build_fem_runtime_lineage_events",
    "final_emission_meta_read_side_surface",
    "fem_runtime_lineage_events",
    "tests.helpers.golden_replay_projection",
    "tests.helpers.failure_classifier",
    "tests.helpers.failure_dashboard_report",
    "protected_observation_field_registry",
    "protected_observation_field_paths",
    "project_turn_observation",
    "build_classified_dashboard_row",
    "validate_failure_classification_row",
    "FailureClassification",
)

# Cycle BD-6: compressed gate-owned imports non-owner tests must not reintroduce (BD-2–BD-5).
_BD6_SMOKE_FACADE: Final[str] = "tests/helpers/emission_smoke_assertions.py"
_BD6_GOLDEN_REPLAY_FACADE: Final[str] = "tests/helpers/golden_replay_projection.py"
# Cycle BE6: scaffold/phrase ownership layers — intentional separation; do not merge matrices.
_BE6_SCAFFOLD_PHRASE_LAYER_OWNERS: Final[Mapping[str, str]] = {
    "sanitizer_legality": "tests/test_output_sanitizer.py",
    "http_smoke_facade": _DOWNSTREAM_SMOKE_FACADE,
    "replay_scaffold_projection": _BD6_GOLDEN_REPLAY_FACADE,
}
_BJ4_SMOKE_FACADE_ALLOWED_GATE_BRIDGES: Final[frozenset[str]] = frozenset(
    {
        "apply_final_emission_gate_consumer",
        "enforce_response_type_contract_layer",
        "final_emission_meta_from_output",
        "read_turn_debug_notes",
    }
)
_BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES: Final[frozenset[str]] = frozenset(
    {
        "apply_answer_completeness_layer",
        "apply_response_delta_layer",
        "assert_no_boundary_reorder_repair",
        "assert_response_delta_boundary_validate_only",
        "inspect_response_delta_failure",
        "skip_answer_completeness_layer",
        "skip_response_delta_layer",
        "strict_social_answer_pressure_rd_contract_active",
        "validate_answer_completeness",
        "validate_response_delta",
    }
)
_BJ4_SMOKE_FACADE_FORBIDDEN_PUBLIC_NAME_FRAGMENTS: Final[Mapping[str, str]] = {
    "gate_legality": "full gate legality matrices belong to tests/test_final_emission_gate.py",
    "legality_matrix": "legality matrices belong to owner suites",
    "route_enum": "route enum tables belong to route/gate owner suites",
    "route_table": "route tables belong to route/gate owner suites",
    "sanitizer_legality": "sanitizer phrase legality belongs to tests/test_output_sanitizer.py",
    "sanitizer_phrase": "sanitizer phrase legality belongs to tests/test_output_sanitizer.py",
    "repair_matrix": "AC/RD repair semantics belong to owner suites",
    "repair_semantic": "AC/RD repair semantics belong to owner suites",
}

# Cycle BI-8: golden replay is a consumer/bridge, not a subsystem legality owner.
_BI8_GOLDEN_REPLAY_TARGETS: Final[tuple[str, ...]] = (
    "tests/test_golden_replay.py",
    "tests/helpers/golden_replay.py",
    "tests/helpers/golden_replay_api.py",
)
_BI8_GOLDEN_REPLAY_OWNED_EXPORTS: Final[frozenset[str]] = frozenset(
    {
        "run_golden_replay",
        "assert_golden_turn_observation",
        "assert_protected_golden_turn_observation",
        "assert_golden_replay_profile_bundle",
        "format_golden_replay_debug",
        "observed_turn_from_payload",
        "protected_social_speaker_observation_expectation",
        "protected_structural_expectation",
        "render_long_session_replay_summary_markdown",
        "summarize_long_session_replay_observations",
    }
)
_BI8_GOLDEN_REPLAY_FORBIDDEN_EXPORTS: Final[frozenset[str]] = frozenset(
    {
        "protected_no_scaffold_expectation",
        "protected_route_expectation",
        "protected_source_expectation",
        "protected_unavailable_expectation",
        "protected_social_structural_base",
        "protected_social_directed_question_expectation",
        "protected_social_trace_target_expectation",
        "protected_social_vocative_canonical_entry_expectation",
        "protected_social_supplemental_structural_expectation",
    }
)
_BI8_GOLDEN_REPLAY_FORBIDDEN_SOURCE_FRAGMENTS: Final[Mapping[str, str]] = {
    "PROTECTED_SOCIAL_RESOLUTION_KINDS": "route enum legality",
    "PROTECTED_SOCIAL_ROUTE_KINDS": "route enum legality",
    "PROTECTED_DIALOGUE_TRACE_ROUTES": "route enum legality",
    "PROTECTED_VOCATIVE_CANONICAL_ENTRY": "speaker/vocative legality",
    "protected_social_structural_base": "speaker legality",
    "protected_social_directed_question_expectation": "speaker legality",
    "protected_social_trace_target_expectation": "speaker legality",
    "protected_social_vocative_canonical_entry_expectation": "speaker/vocative legality",
    "protected_social_supplemental_structural_expectation": "speaker/route legality",
    "successful_opening_observed_fields": "opening/fallback owner-bucket semantics",
    "OPENING_FALLBACK_OWNER_": "opening/fallback owner-bucket semantics",
    "OPENING_FALLBACK_AUTHORSHIP": "opening fallback authorship semantics",
    "FRONTIER_GATE_SOCIAL_INQUIRY_STABILITY_PROFILE": "stability threshold meaning",
    "FRONTIER_GATE_SOCIAL_INQUIRY_LINEAGE_PROFILE": "lineage threshold meaning",
    "FRONTIER_GATE_SOCIAL_INQUIRY_FALLBACK_ESCALATION_PROFILE": "fallback escalation threshold meaning",
    "FRONTIER_GATE_RESUME_STABILITY_PROFILE": "stability threshold meaning",
    "FRONTIER_GATE_RESUME_LINEAGE_PROFILE": "lineage threshold meaning",
    "FRONTIER_GATE_RESUME_FALLBACK_ESCALATION_PROFILE": "fallback escalation threshold meaning",
    "FRONTIER_GATE_DIRECT_INTRUSION_STABILITY_PROFILE": "stability threshold meaning",
    "FRONTIER_GATE_DIRECT_INTRUSION_LINEAGE_PROFILE": "lineage threshold meaning",
    "FRONTIER_GATE_DIRECT_INTRUSION_FALLBACK_ESCALATION_PROFILE": "fallback escalation threshold meaning",
}
_BD6_OPENING_FACADE: Final[str] = "tests/helpers/opening_fallback_evidence.py"
_BD6_FORBIDDEN_FEM_READ_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "read_final_emission_meta_dict",
        "read_final_emission_meta_from_turn_payload",
        "read_emission_debug_lane_from_turn_payload",
    },
)
_BD6_FORBIDDEN_OWNER_BUCKET_PREFIXES: Final[tuple[str, ...]] = (
    "OPENING_FALLBACK_OWNER_",
    "SEALED_FALLBACK_OWNER_",
    "VISIBILITY_FALLBACK_OWNER_",
)
_BD6_COMPRESSED_OWNER_MODULES: Final[frozenset[str]] = frozenset(
    {
        "game.final_emission_gate",
        "game.final_emission_meta",
        "game.final_emission_replay_projection",
    },
)
# Narrow allowlist: primary owners, BD-2–BD-5 KEEP suites, facade delegates, gate monkeypatch helpers,
# and audit fixture modules that embed gate-import strings intentionally.
_BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST: Final[Mapping[str, str]] = {
    "tests/test_final_emission_gate.py": "Gate orchestration owner (BD-2/BD-5 KEEP)",
    "tests/test_final_emission_meta.py": "FEM projection / runtime-lineage owner (BD-3/BD-4/BD-5 KEEP)",
    "tests/test_fallback_behavior_gate.py": "Gate-adjacent behavior owner (BD-2 KEEP)",
    "tests/test_final_emission_boundary_no_semantic_repair.py": "Gate boundary owner; private feg._* seams (BD-2 KEEP)",
    "tests/test_block_s_speaker_local_rebind_equivalence.py": "Speaker equivalence / orchestration-order proof (BD-2 KEEP)",
    "tests/test_block_t_speaker_relocation_shadow_equivalence.py": "Speaker equivalence / orchestration-order proof (BD-2 KEEP)",
    "tests/test_block_u_finalize_stack_divergence.py": "Finalize-stack divergence proof (BD-2 KEEP)",
    "tests/test_social_exchange_emission.py": "Strict-social emission legality owner (BD-2 KEEP)",
    "tests/test_tone_escalation_rules.py": "Layer-order monkeypatch on feg namespace (BD-2 KEEP)",
    "tests/test_final_emission_visibility.py": "Visibility semantics owner (BD-3 KEEP)",
    "tests/test_final_emission_channel_separation.py": "FEM channel packaging owner-adjacent (BD-3 KEEP)",
    "tests/test_opening_fallback_owner_bucket.py": "Opening fallback owner-bucket mapping owner (BD-5 KEEP)",
    "tests/test_final_emission_opening_fallback.py": "Opening fallback owner (BD-5 KEEP)",
    "tests/test_final_emission_sealed_fallback.py": "Sealed fallback owner (BD-5 KEEP)",
    "tests/test_final_emission_visibility_fallback.py": "Visibility fallback owner-adjacent (BD-5 KEEP)",
    _BD6_SMOKE_FACADE: "Downstream smoke facade delegate (BD-2/BD-3 internal imports)",
    _BD6_GOLDEN_REPLAY_FACADE: "Golden replay / replay-projection facade delegate (BD-3/BD-4/BD-5)",
    _BD6_OPENING_FACADE: "Opening fallback evidence facade delegate (BD-5)",
    "tests/helpers/gate_equivalence_monkeypatch.py": "Gate namespace monkeypatch equivalence helper (BD-2 KEEP)",
    "tests/helpers/opening_fallback_gate_harness.py": "Opening attach-then gate harness; private feg._* seams (BD-2 KEEP)",
    "tests/helpers/post_speaker_finalize_probe.py": "Gate finalize-stack probe wrappers (BD-2 KEEP)",
    "tests/helpers/speaker_relocation_shadow_harness.py": "Speaker relocation shadow harness; feg namespace (BD-2 KEEP)",
    "tests/helpers/strict_social_harness.py": "Strict-social harness; feg monkeypatch + consumer entry (BD-2 KEEP)",
    "tests/test_architecture_audit_tool.py": "Audit fixture strings embed gate-import examples",
    "tests/test_validation_layer_audit_smoke.py": "Audit fixture strings embed gate-import examples",
    "tests/test_test_audit_tool.py": "Inventory audit fixture strings embed gate-import examples",
    "tests/test_realization_layer_audit.py": "Realization audit fixture strings embed gate-import examples",
    "tests/test_ownership_registry.py": "Governance module; AO5 runtime vs acceptance boundary check imports replay projection",
}


def _normalize_layer(name: str | None) -> str | None:
    if name is None:
        return None
    n = name.strip().lower()
    aliases = {"truth": "engine", "structure": "planner", "expression": "gpt", "legality": "gate", "scoring": "evaluator"}
    return aliases.get(n, n)


def _layers_compatible(declared: str | None, likely: str | None) -> bool:
    """Return True if inventory ``likely`` does not contradict ``declared`` in a sharp way."""
    if declared is None or likely is None:
        return True
    d = _normalize_layer(declared)
    l = _normalize_layer(likely)
    if d is None or l is None:
        return True
    if l in _PERMISSIVE_INVENTORY_LAYERS:
        return True
    if d == l:
        return True
    if d in _CANONICAL and l in _CANONICAL and frozenset({d, l}) in _SOFT_ADJACENT:
        return True
    return False


def _direct_owner_inventory_layer_ok(declared: str | None, likely: str | None) -> bool:
    """Inventory ``general`` is permissive for neighbors, but not for a declared direct owner with a layer."""
    if likely is None or not isinstance(likely, str):
        return True
    if _normalize_layer(likely) == "general" and declared is not None:
        return False
    return _layers_compatible(declared, likely)


_NEIGHBOR_SUITE_FIELDS: Final[tuple[str, ...]] = (
    "smoke_suites",
    "transcript_suites",
    "gauntlet_suites",
    "evaluator_suites",
    "downstream_consumer_suites",
    "compatibility_residue_suites",
)


def _neighbor_paths_for_group(rec: ResponsibilityRecord) -> list[tuple[str, str]]:
    """(normalized_path, field_name) for neighbor slots only."""
    out: list[tuple[str, str]] = []
    for field in _NEIGHBOR_SUITE_FIELDS:
        for p in getattr(rec, field):
            out.append((str(p).replace("\\", "/"), field))
    return out


def _paths_for_group(rec: ResponsibilityRecord) -> list[tuple[str, str]]:
    """All governed paths: direct_owner plus each neighbor field."""
    seq: list[tuple[str, str]] = [(rec.direct_owner.replace("\\", "/"), "direct_owner")]
    seq.extend(_neighbor_paths_for_group(rec))
    return seq


def _path_is_disallowed_live_legality_owner(path: str) -> bool:
    """True when ``path`` looks like transcript / gauntlet / playability / evaluator *suite* ownership."""
    norm = path.replace("\\", "/").lower()
    base = norm.rsplit("/", 1)[-1]
    if "playability" in base:
        return True
    if base.endswith("_eval.py") or "evaluator" in base:
        return True
    if "transcript_gauntlet" in base:
        return True
    if base == "test_transcript_regression.py" or "transcript_regressions" in base:
        return True
    if "gauntlet" in base:
        return True
    return False


@dataclass(frozen=True)
class ResponsibilityRecord:
    """One governed responsibility slice.

    Neighbor field semantics (Cycle AD-3):
    - ``direct_owner``: normative / full assertion home for the responsibility.
    - ``downstream_consumer_suites``: integration-visible smoke (HTTP/API packaging, consumer
      layer meta fields); not alternate gate orchestration owners.
    - ``smoke_suites``: thin wiring / survival checks only.
    - ``gauntlet_suites`` / ``transcript_suites``: end-to-end observation; replay/classifier
      FEM projection duplication is intentional diagnostic protection, not gate ownership.
    """

    human_title: str
    declared_architecture_layer: str | None
    direct_owner: str
    smoke_suites: Tuple[str, ...] = ()
    transcript_suites: Tuple[str, ...] = ()
    gauntlet_suites: Tuple[str, ...] = ()
    evaluator_suites: Tuple[str, ...] = ()
    downstream_consumer_suites: Tuple[str, ...] = ()
    compatibility_residue_suites: Tuple[str, ...] = ()


# Keys are stable ids consumed by governance tests.
RESPONSIBILITY_REGISTRY: Final[Mapping[str, ResponsibilityRecord]] = {
    "engine_truth_persistence_mechanics": ResponsibilityRecord(
        human_title="Engine truth / persistence / mechanics",
        declared_architecture_layer="engine",
        direct_owner="tests/test_save_load.py",
        smoke_suites=("tests/test_startup_and_timestamps.py",),
    ),
    "planner_prompt_bundle_shipped_contract": ResponsibilityRecord(
        human_title="Planner prompt bundle and shipped contract structure",
        declared_architecture_layer="planner",
        direct_owner="tests/test_narrative_plan_structural_readiness.py",
        smoke_suites=("tests/test_planner_convergence_live_pipeline.py",),
    ),
    # Normative GPT *shape* checks are thin here by design; gate suites own hard legality.
    "gpt_expression_surface_smoke": ResponsibilityRecord(
        human_title="GPT expression surface (smoke-oriented owner)",
        declared_architecture_layer="gpt",
        direct_owner="tests/test_narrative_mode_output_validator.py",
        # C4 live-pipeline: planner→prompt→gate wiring; final_route smoke via emission_smoke_assertions (AL3).
        smoke_suites=("tests/test_c4_narrative_mode_live_pipeline.py",),
    ),
    "final_emission_gate_orchestration": ResponsibilityRecord(
        # Direct owner: apply_final_emission_gate orchestration, layer order, exact final_route /
        # final_emitted_source / repair-kind tables. Downstream neighbors: HTTP/API smoke and
        # consumer-layer boundary validate-only traces only (see emission_smoke_assertions.py).
        human_title="Final emission gate orchestration",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_gate.py",
        transcript_suites=("tests/test_narration_transcript_regressions.py",),
        downstream_consumer_suites=(
            "tests/test_turn_pipeline_shared.py",
            "tests/test_answer_completeness_rules.py",
            "tests/test_response_delta_requirement.py",
            "tests/test_interaction_continuity_repair.py",
            "tests/test_diegetic_fallback_narration.py",
        ),
    ),
    "final_emission_meta_projection": ResponsibilityRecord(
        # Direct owner: FEM read/normalize/projection helpers. Golden replay / failure classifier
        # bucket columns are intentional diagnostic projection neighbors — not gate orchestration.
        human_title="Final emission meta (FEM) projection, replay read path, and sidecar reads",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_meta.py",
        downstream_consumer_suites=(
            "tests/test_turn_packet_stage_diff_integration.py",
            "tests/test_diegetic_fallback_narration.py",
        ),
    ),
    "final_emission_visibility_semantics": ResponsibilityRecord(
        human_title="Final emission visibility fallback semantics",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_visibility.py",
        downstream_consumer_suites=("tests/test_turn_pipeline_shared.py",),
    ),
    "final_emission_validators": ResponsibilityRecord(
        human_title="Final emission validators",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_validators.py",
        smoke_suites=("tests/test_final_emission_boundary_audit.py",),
    ),
    "final_emission_repairs": ResponsibilityRecord(
        human_title="Final emission repairs",
        declared_architecture_layer="gate",
        direct_owner="tests/test_final_emission_repairs.py",
        smoke_suites=("tests/test_final_emission_boundary_convergence.py",),
    ),
    "response_policy_contract_materialization": ResponsibilityRecord(
        human_title="Response policy contract materialization",
        declared_architecture_layer="engine",
        direct_owner="tests/test_response_policy_contracts.py",
    ),
    "prompt_context_contract_assembly": ResponsibilityRecord(
        human_title="Prompt context contract assembly",
        declared_architecture_layer="engine",
        direct_owner="tests/test_prompt_context.py",
        smoke_suites=("tests/test_prompt_context_plan_only_convergence.py",),
        downstream_consumer_suites=("tests/test_prompt_and_guard.py",),
    ),
    "output_sanitizer_final_string_cleanup": ResponsibilityRecord(
        # Direct owner: full procedural phrase-ban matrix (BE6 layer 1). Downstream neighbors:
        # HTTP smoke via emission_smoke_assertions (BE6 layer 2); replay scaffold observation
        # via golden_replay_projection (BE6 layer 3) — never merge into one phrase matrix.
        human_title="Output sanitizer final string cleanup",
        declared_architecture_layer="gate",
        direct_owner="tests/test_output_sanitizer.py",
        downstream_consumer_suites=(
            "tests/test_turn_pipeline_shared.py",
            "tests/test_prompt_and_guard.py",
        ),
    ),
    "social_engine_state_rules": ResponsibilityRecord(
        human_title="Social engine state / rules",
        declared_architecture_layer="engine",
        direct_owner="tests/test_social.py",
        smoke_suites=("tests/test_social_probe_determinism.py",),
    ),
    "social_emission_legality_surface": ResponsibilityRecord(
        # Direct owner: strict-social legality tables (question_resolution, first-sentence,
        # final_emitted_source semantics). Downstream policy consumers and HTTP smoke use
        # emission_smoke_assertions route/phrase helpers — not duplicate legality matrices.
        human_title="Social emission legality / surface",
        declared_architecture_layer="gate",
        direct_owner="tests/test_social_exchange_emission.py",
        transcript_suites=("tests/test_speaker_contract_enforcement.py",),
        downstream_consumer_suites=(
            "tests/test_answer_completeness_rules.py",
            "tests/test_response_delta_requirement.py",
        ),
    ),
    "lead_clue_lifecycle": ResponsibilityRecord(
        human_title="Lead / clue lifecycle",
        declared_architecture_layer="engine",
        direct_owner="tests/test_clue_lead_registry_integration.py",
        smoke_suites=("tests/test_clue_idempotence.py", "tests/test_clue_discovery.py"),
    ),
    "transcript_regression": ResponsibilityRecord(
        human_title="Transcript regression",
        declared_architecture_layer=None,
        direct_owner="tests/test_transcript_regression.py",
        transcript_suites=("tests/test_narration_transcript_regressions.py",),
        smoke_suites=("tests/test_transcript_runner_smoke.py",),
    ),
    "gauntlet_playability_validation": ResponsibilityRecord(
        # Direct owner: gauntlet orchestration. golden_replay gauntlet neighbor holds intentional
        # replay observation / FEM drift locks — diagnostic projection, not gate orchestration.
        human_title="Gauntlet / playability validation",
        declared_architecture_layer="gate",
        direct_owner="tests/test_gauntlet_regressions.py",
        gauntlet_suites=(
            "tests/test_behavioral_gauntlet_smoke.py",
            "tests/test_golden_replay.py",
        ),
        smoke_suites=("tests/test_playability_smoke.py",),
    ),
    "offline_evaluator_scoring": ResponsibilityRecord(
        human_title="Offline evaluator scoring",
        declared_architecture_layer="evaluator",
        direct_owner="tests/test_narrative_authenticity_eval.py",
        evaluator_suites=("tests/test_player_agency_evaluator.py", "tests/test_intent_fulfillment_evaluator.py"),
    ),
}

_REQUIRED_GROUP_IDS: Final[AbstractSet[str]] = frozenset(
    {
        "engine_truth_persistence_mechanics",
        "planner_prompt_bundle_shipped_contract",
        "gpt_expression_surface_smoke",
        "final_emission_gate_orchestration",
        "final_emission_meta_projection",
        "final_emission_visibility_semantics",
        "final_emission_validators",
        "final_emission_repairs",
        "response_policy_contract_materialization",
        "prompt_context_contract_assembly",
        "output_sanitizer_final_string_cleanup",
        "social_engine_state_rules",
        "social_emission_legality_surface",
        "lead_clue_lifecycle",
        "transcript_regression",
        "gauntlet_playability_validation",
        "offline_evaluator_scoring",
    }
)

# Block A cross-file duplicate top-level ``test_*`` names: tolerate only with an explicit reason.
_CROSS_FILE_DUPLICATE_ALLOWLIST: Final[Mapping[str, str]] = {
    "test_deterministic_json_stable": (
        "Parallel JSON stability probes in narrative planning vs referent tracking; "
        "distinct modules and docstrings disambiguate intent for pytest -k."
    ),
    "test_version_constant": (
        "Parallel shipped-version sentinels in narrative planning vs referent tracking; "
        "distinct modules disambiguate ownership of each contract surface."
    ),
    "test_maybe_attach_respects_env": (
        "Separate offline evaluator harnesses (intent fulfillment vs player agency) each "
        "need the same env-guard smoke; names intentionally parallel across evaluator suites."
    ),
    "test_real_repo_scan_does_not_require_zero_findings": (
        "Parallel realization audit tool smoke in layer vs provenance audit modules; distinct audit surfaces."
    ),
    "test_report_generation_writes_json_and_markdown": (
        "Parallel realization audit report writers in layer vs provenance audit modules."
    ),
    "test_severity_values_are_only_expected_values": (
        "Parallel realization audit severity contract smoke in layer vs provenance audit modules."
    ),
    "test_tool_imports_successfully": (
        "Parallel realization audit import smoke in layer vs provenance audit modules."
    ),
}


def build_ownership_registry_index(
    registry: Mapping[str, ResponsibilityRecord] | None = None,
) -> dict[str, object]:
    """Derive machine-readable neighbor maps from a responsibility registry (not committed in governance JSON)."""
    reg = RESPONSIBILITY_REGISTRY if registry is None else registry
    groups: dict[str, dict[str, object]] = {}
    for gid, rec in sorted(reg.items()):
        groups[gid] = {
            "human_title": rec.human_title,
            "declared_architecture_layer": rec.declared_architecture_layer,
            "direct_owner": rec.direct_owner.replace("\\", "/"),
            "smoke_suites": [p.replace("\\", "/") for p in rec.smoke_suites],
            "transcript_suites": [p.replace("\\", "/") for p in rec.transcript_suites],
            "gauntlet_suites": [p.replace("\\", "/") for p in rec.gauntlet_suites],
            "evaluator_suites": [p.replace("\\", "/") for p in rec.evaluator_suites],
            "downstream_consumer_suites": [p.replace("\\", "/") for p in rec.downstream_consumer_suites],
            "compatibility_residue_suites": [p.replace("\\", "/") for p in rec.compatibility_residue_suites],
        }
    roles_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for gid in sorted(groups):
        row = groups[gid]
        d = str(row["direct_owner"])
        roles_by_path[d].append({"group_id": gid, "role": "direct_owner"})
        for p in row["smoke_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "smoke_suite"})
        for p in row["transcript_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "transcript_suite"})
        for p in row["gauntlet_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "gauntlet_suite"})
        for p in row["evaluator_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "evaluator_suite"})
        for p in row["downstream_consumer_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "downstream_consumer_suite"})
        for p in row["compatibility_residue_suites"]:
            roles_by_path[str(p)].append({"group_id": gid, "role": "compatibility_residue_suite"})
    files_roles = {
        path: sorted(entries, key=lambda e: (e["role"], e["group_id"]))
        for path, entries in sorted(roles_by_path.items())
    }
    return {
        "available": True,
        "groups": groups,
        "files_roles": files_roles,
    }


def gate_magnet_guard_paths(
    registry: Mapping[str, ResponsibilityRecord] | None = None,
) -> tuple[str, ...]:
    """Gate-layer direct owners that must not accumulate replay read-side projection ownership."""
    reg = RESPONSIBILITY_REGISTRY if registry is None else registry
    paths: list[str] = []
    for gid, rec in reg.items():
        if gid in _GATE_MAGNET_GUARD_EXCLUDED_GROUP_IDS:
            continue
        if rec.declared_architecture_layer != "gate":
            continue
        rel = rec.direct_owner.replace("\\", "/")
        if rel in _GATE_MAGNET_GUARD_EXCLUDED_PATHS:
            continue
        paths.append(rel)
    return tuple(sorted(paths))


def _collect_import_module_paths(source: str) -> set[str]:
    tree = ast.parse(source)
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def _module_all_exports(source: str) -> frozenset[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        assert isinstance(value, tuple), "__all__ must be a literal tuple"
        assert all(isinstance(item, str) for item in value), "__all__ entries must be strings"
        return frozenset(value)
    raise AssertionError("module must define literal __all__")


def _import_matches_forbidden_prefix(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def collect_gate_magnet_guard_import_violations(
    rel_path: str,
    source: str,
    *,
    forbidden_prefixes: tuple[str, ...] = _FORBIDDEN_REPLAY_READ_SIDE_IMPORT_PREFIXES,
) -> list[str]:
    """Return import violations when a gate direct-owner suite pulls replay read-side projection helpers."""
    violations: list[str] = []
    for mod in sorted(_collect_import_module_paths(source)):
        for prefix in forbidden_prefixes:
            if _import_matches_forbidden_prefix(mod, prefix):
                violations.append(
                    f"{rel_path}: forbidden import {mod!r} "
                    f"(replay/dashboard/classifier read-side projection; owner is "
                    f"tests/test_final_emission_meta.py, tests/test_golden_replay.py, or classifier/dashboard suites)",
                )
    return violations


def collect_gate_magnet_guard_source_fragment_violations(
    rel_path: str,
    source: str,
    *,
    forbidden_fragments: tuple[str, ...] = _FORBIDDEN_GATE_READ_SIDE_SOURCE_FRAGMENTS,
) -> list[str]:
    """Return source-fragment violations for read-side projection assertion creep in gate owners."""
    return [
        f"{rel_path}: forbidden read-side projection fragment {fragment!r} "
        f"(move replay/dashboard/classifier contracts to meta projection or gauntlet/classifier owners)"
        for fragment in forbidden_fragments
        if fragment in source
    ]


def _normalize_test_rel_path(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def _bd6_is_forbidden_owner_bucket_symbol(module: str, symbol: str) -> bool:
    if module not in _BD6_COMPRESSED_OWNER_MODULES:
        return False
    if symbol == "FINAL_EMISSION_META_KEY":
        return True
    return any(symbol.startswith(prefix) for prefix in _BD6_FORBIDDEN_OWNER_BUCKET_PREFIXES)


def _bd6_facade_replacement(module: str, symbol: str) -> str:
    if module == "game.final_emission_gate" and symbol == "apply_final_emission_gate":
        return f"{_BD6_SMOKE_FACADE}::apply_final_emission_gate_consumer"
    if module == "game.final_emission_meta" and symbol in _BD6_FORBIDDEN_FEM_READ_SYMBOLS:
        return (
            f"{_BD6_SMOKE_FACADE}::final_emission_meta_from_output "
            f"(integration/smoke) or {_BD6_GOLDEN_REPLAY_FACADE}::read_fem_meta_from_gate_output "
            f"(golden/replay observation)"
        )
    if module == "game.final_emission_replay_projection":
        return (
            f"{_BD6_GOLDEN_REPLAY_FACADE} "
            f"(e.g. build_runtime_lineage_events_from_fem, SEALED_REPLACEMENT_SUBKINDS)"
        )
    if _bd6_is_forbidden_owner_bucket_symbol(module, symbol):
        if symbol.startswith("OPENING_FALLBACK_OWNER_"):
            return f"{_BD6_OPENING_FACADE} (opening bucket/route constants)"
        return f"{_BD6_GOLDEN_REPLAY_FACADE} (sealed/visibility bucket constants)"
    return "tests.helpers emission/golden/opening facades per BD-2–BD-5"


def collect_gate_dependency_compression_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST,
) -> list[str]:
    """Return import violations when a non-owner test reintroduces compressed gate-owned imports."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module
            for alias in node.names:
                symbol = alias.name
                forbidden = False
                if module == "game.final_emission_gate" and symbol == "apply_final_emission_gate":
                    forbidden = True
                elif module == "game.final_emission_meta" and symbol in _BD6_FORBIDDEN_FEM_READ_SYMBOLS:
                    forbidden = True
                elif module == "game.final_emission_replay_projection":
                    forbidden = True
                elif _bd6_is_forbidden_owner_bucket_symbol(module, symbol):
                    forbidden = True
                if not forbidden:
                    continue
                key = (module, symbol)
                if key in seen:
                    continue
                seen.add(key)
                imported = f"{module}.{symbol}"
                replacement = _bd6_facade_replacement(module, symbol)
                violations.append(
                    f"{norm}: forbidden compressed gate import {imported!r} "
                    f"(use facade replacement: {replacement})",
                )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                if module != "game.final_emission_replay_projection" and not module.startswith(
                    "game.final_emission_replay_projection.",
                ):
                    continue
                key = (module, "")
                if key in seen:
                    continue
                seen.add(key)
                replacement = _bd6_facade_replacement("game.final_emission_replay_projection", module.rsplit(".", 1)[-1] or module)
                violations.append(
                    f"{norm}: forbidden compressed gate import {module!r} "
                    f"(use facade replacement: {replacement})",
                )
    return violations


def iter_gate_dependency_compression_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST,
) -> tuple[str, ...]:
    """All tests/**/*.py paths subject to BD-6 import guard (excluding allowlisted paths)."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for path in sorted((root / "tests").rglob("*.py")):
        rel = _normalize_test_rel_path(path.relative_to(root))
        if rel in allowlist:
            continue
        paths.append(rel)
    return tuple(paths)


def _load_inventory() -> dict:
    if not _INVENTORY_PATH.is_file():
        pytest.fail(f"missing inventory: {_INVENTORY_PATH} (run py -3 tools/test_audit.py)")
    return json.loads(_INVENTORY_PATH.read_text(encoding="utf-8"))


def _inventory_paths(data: dict) -> dict[str, dict]:
    files = data.get("files")
    assert isinstance(files, list), "inventory.files must be a list"
    out: dict[str, dict] = {}
    for row in files:
        assert isinstance(row, dict) and "path" in row
        out[str(row["path"]).replace("\\", "/")] = row
    return out


def _full_inventory_by_path(full_inventory: dict) -> dict[str, dict]:
    """Index full diagnostic ``files[]`` rows by normalized path."""
    out: dict[str, dict] = {}
    for row in full_inventory.get("files", ()):
        if isinstance(row, dict) and "path" in row:
            out[str(row["path"]).replace("\\", "/")] = row
    return out


@pytest.fixture(scope="module")
def inventory() -> dict:
    return _load_inventory()


@pytest.fixture(scope="module")
def inventory_by_path(inventory: dict) -> dict[str, dict]:
    return _inventory_paths(inventory)


@pytest.fixture(scope="module")
def test_audit_module() -> types.ModuleType:
    """Load ``tools/test_audit.py`` once per module (BF1: avoid repeated importlib loads)."""
    spec = importlib.util.spec_from_file_location("_inv_audit", _TEST_AUDIT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def full_inventory(test_audit_module: types.ModuleType) -> dict:
    """Fresh full audit payload once per module (BF1: single pytest collect-only per run)."""
    return test_audit_module.build_inventory_payload()


def test_registry_defines_all_required_groups() -> None:
    assert set(RESPONSIBILITY_REGISTRY) == _REQUIRED_GROUP_IDS


def test_inventory_schema_version_matches_audit_tool(
    test_audit_module: types.ModuleType,
    inventory: dict,
) -> None:
    """Block A: inventory generator and governance tests agree on schema generation."""
    assert inventory.get("summary", {}).get("inventory_schema_version") == test_audit_module.INVENTORY_SCHEMA_VERSION


def test_governance_inventory_contains_required_fields(inventory: dict) -> None:
    """AQ9: committed artifact retains stable governance sections only."""
    for key in (
        "summary",
        "files",
    ):
        assert key in inventory, f"missing governance inventory key {key!r}"
    assert "cross_file_duplicate_test_names" not in inventory, (
        "governance JSON must not store cross_file_duplicate_test_names; derive via tools/test_audit.py --check"
    )
    assert "tests" not in inventory, (
        "governance JSON must not store tests[]; derive per-test marker coverage via tools/test_audit.py --check"
    )
    assert "block_b_overlap_clusters" not in inventory, (
        "governance JSON must not store block_b_overlap_clusters; use --full diagnostic output"
    )
    assert "import_hub_modules" not in inventory, (
        "governance JSON must not store import_hub_modules; use --full diagnostic output"
    )
    assert "ownership_registry_index" not in inventory, (
        "governance JSON must not embed ownership_registry_index; derive via build_ownership_registry_index()"
    )
    assert inventory.get("summary", {}).get("inventory_kind") == "governance"
    sample = inventory["files"][0]
    for key in ("path",):
        assert key in sample, f"missing governance file row key {key!r}"
    assert "marker_set" not in sample, (
        "governance file rows must not store marker_set; derive via tools/test_audit.py --check"
    )
    assert "likely_architecture_layer" not in sample, (
        "governance file rows must not store likely_architecture_layer; derive via tools/test_audit.py --check"
    )
    assert "pytest_collected" not in sample, (
        "governance file rows must not store pytest_collected; derive via tools/test_audit.py --check"
    )
    assert "collected_duplicate_base_names" not in sample, (
        "governance file rows must not store collected_duplicate_base_names; derive via tools/test_audit.py --check"
    )
    assert "ownership_registry_positions" not in sample, (
        "governance file rows must not store ownership_registry_positions; derive via build_ownership_registry_index()"
    )


def test_governance_summary_contains_stable_metadata_only(inventory: dict) -> None:
    """AQ9: committed summary retains stable metadata; counts are derived at --check."""
    summary = inventory.get("summary")
    assert isinstance(summary, dict)
    assert set(summary) == {
        "inventory_schema_version",
        "inventory_kind",
        "declared_pytest_markers",
    }
    assert summary.get("inventory_kind") == "governance"


def test_governance_omits_cross_file_duplicate_test_names(inventory: dict) -> None:
    """AQ9: cross-file duplicate rows are derived from full audit, not committed."""
    assert "cross_file_duplicate_test_names" not in inventory


def test_governance_rejects_stored_cross_file_duplicate_test_names(
    inventory: dict,
    inventory_by_path: dict[str, dict],
) -> None:
    """AQ9: committed governance must not embed derived duplicate-name rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted["cross_file_duplicate_test_names"] = [{"base_name": "test_x", "files": ["tests/test_a.py"]}]
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store cross_file_duplicate_test_names" in e for e in errs)


def test_governance_file_rows_omit_committed_per_test_rows(inventory: dict) -> None:
    """AQ6: per-test marker rows are derived at check time, not committed."""
    assert "tests" not in inventory


def test_governance_rejects_stored_per_test_rows(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ6: committed governance must not embed derived per-test marker rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted["tests"] = [{"nodeid": "tests/test_x.py::test_y", "marker_set": ["unit"]}]
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store tests[]" in e for e in errs)


def test_governance_file_rows_omit_marker_set(inventory: dict) -> None:
    """BF7: per-file marker sets are derived at check time, not committed."""
    with_markers = [
        row.get("path")
        for row in inventory.get("files", [])
        if isinstance(row, dict) and "marker_set" in row
    ]
    assert not with_markers, f"governance files must not store marker_set: {with_markers[:3]!r}"


def test_governance_rejects_stored_marker_set(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF7: committed governance must not embed derived per-file marker sets."""
    polluted = json.loads(json.dumps(inventory))
    polluted["files"][0]["marker_set"] = ["unit"]
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store marker_set" in e for e in errs)


def test_governance_file_rows_omit_likely_architecture_layer(inventory: dict) -> None:
    """BF6: architecture-layer heuristics are derived at check time, not committed."""
    with_layers = [
        row.get("path")
        for row in inventory.get("files", [])
        if isinstance(row, dict) and "likely_architecture_layer" in row
    ]
    assert not with_layers, f"governance files must not store likely_architecture_layer: {with_layers[:3]!r}"


def test_governance_rejects_stored_likely_architecture_layer(
    inventory: dict,
    inventory_by_path: dict[str, dict],
) -> None:
    """BF6: committed governance must not embed derived architecture-layer heuristics."""
    polluted = json.loads(json.dumps(inventory))
    polluted["files"][0]["likely_architecture_layer"] = "gate"
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store likely_architecture_layer" in e for e in errs)


def test_governance_file_rows_omit_collected_duplicate_base_names(inventory: dict) -> None:
    """BF5: in-file duplicate base names are derived at check time, not committed."""
    with_dups = [
        row.get("path")
        for row in inventory.get("files", [])
        if isinstance(row, dict) and "collected_duplicate_base_names" in row
    ]
    assert not with_dups, (
        f"governance files must not store collected_duplicate_base_names: {with_dups[:3]!r}"
    )


def test_governance_rejects_stored_collected_duplicate_base_names(
    inventory: dict,
    inventory_by_path: dict[str, dict],
) -> None:
    """BF5: committed governance must not embed derived in-file duplicate-base-name lists."""
    polluted = json.loads(json.dumps(inventory))
    polluted["files"][0]["collected_duplicate_base_names"] = ["test_dup"]
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store collected_duplicate_base_names" in e for e in errs)


def test_governance_file_rows_omit_pytest_collected(inventory: dict) -> None:
    """BF4: per-file collect counts are derived at check time, not committed."""
    with_counts = [
        row.get("path")
        for row in inventory.get("files", [])
        if isinstance(row, dict) and "pytest_collected" in row
    ]
    assert not with_counts, f"governance files must not store pytest_collected: {with_counts[:3]!r}"


def test_governance_rejects_stored_pytest_collected(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """BF4: committed governance must not embed derived per-file collect counts."""
    polluted = json.loads(json.dumps(inventory))
    polluted["files"][0]["pytest_collected"] = 99
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store pytest_collected" in e for e in errs)


def test_governance_file_rows_omit_registry_positions(inventory: dict) -> None:
    """AQ5: per-file registry positions are derived, not committed."""
    with_positions = [
        row.get("path")
        for row in inventory.get("files", [])
        if isinstance(row, dict) and "ownership_registry_positions" in row
    ]
    assert not with_positions, f"governance files must not store ownership_registry_positions: {with_positions[:3]!r}"


def test_governance_committed_files_exclude_non_registry_paths(
    inventory: dict,
    full_inventory: dict,
    test_audit_module: types.ModuleType,
) -> None:
    """AQ8: committed governance files[] retains registry-owned paths only (+ cross-file dup files)."""
    allowed = test_audit_module.governance_committed_file_paths(full_inventory)
    committed = {str(row["path"]).replace("\\", "/") for row in inventory.get("files", []) if isinstance(row, dict)}
    extra = sorted(committed - allowed)
    assert not extra, f"governance files[] includes non-governance paths: {extra[:5]!r}"


def test_governance_committed_files_include_all_registry_paths(inventory_by_path: dict[str, dict]) -> None:
    """AQ8: every registry-owned path appears in committed governance files[]."""
    files_roles = build_ownership_registry_index().get("files_roles", {})
    assert isinstance(files_roles, dict) and files_roles
    missing = sorted(fp for fp in files_roles if fp not in inventory_by_path)
    assert not missing, f"registry-owned paths missing from committed governance: {missing[:5]!r}"


def test_governance_rejects_non_registry_committed_file_row(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ8: committed governance must not embed non-registry file rows."""
    polluted = json.loads(json.dumps(inventory))
    polluted["files"] = list(polluted.get("files", [])) + [
        {
            "path": "tests/test_non_registry_module.py",
        }
    ]
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store non-governance path" in e for e in errs)


def test_derived_registry_paths_present_in_inventory(
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    """AQ5: derived files_roles paths remain inventory-backed for direct-owner/neighbor checks."""
    files_roles = build_ownership_registry_index().get("files_roles", {})
    assert isinstance(files_roles, dict) and files_roles
    missing = sorted(fp for fp in files_roles if fp not in inventory_by_path)
    assert not missing, f"derived registry paths missing from inventory: {missing[:5]!r}"
    gate = "tests/test_final_emission_gate.py"
    assert gate in files_roles
    assert files_roles[gate] == [{"group_id": "final_emission_gate_orchestration", "role": "direct_owner"}]
    full_by_path = _full_inventory_by_path(full_inventory)
    assert full_by_path[gate].get("likely_architecture_layer") == "gate"


def test_derived_registry_index_matches_live_registry() -> None:
    """AQ4: neighbor/group maps are derived from Python registry, not committed JSON."""
    idx = build_ownership_registry_index()
    assert idx.get("available") is True
    groups = idx.get("groups")
    roles = idx.get("files_roles")
    assert isinstance(groups, dict) and isinstance(roles, dict)
    assert set(groups) == _REQUIRED_GROUP_IDS
    assert "final_emission_gate_orchestration" in groups
    gate = groups["final_emission_gate_orchestration"]
    assert isinstance(gate, dict)
    assert gate.get("direct_owner") == "tests/test_final_emission_gate.py"
    assert isinstance(gate.get("transcript_suites"), list)
    for key in (
        "smoke_suites",
        "transcript_suites",
        "gauntlet_suites",
        "evaluator_suites",
        "downstream_consumer_suites",
        "compatibility_residue_suites",
    ):
        assert key in gate, f"missing derived registry groups field {key!r}"


def test_governance_omits_triage_aggregates(inventory: dict) -> None:
    """AQ7: diagnostic triage aggregates are full-only, not committed."""
    assert "block_b_overlap_clusters" not in inventory
    assert "import_hub_modules" not in inventory


def test_governance_rejects_stored_triage_aggregates(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ7: committed governance must not embed full-only triage aggregates."""
    polluted = json.loads(json.dumps(inventory))
    polluted["block_b_overlap_clusters"] = [{"kind": "dense_ownership_theme_by_architecture_layer", "cells": []}]
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store block_b_overlap_clusters" in e for e in errs)


def test_inventory_block_b_schema_v2_coherence(
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    """AQ7: triage aggregates and registry paths are validated; clusters/hubs derived from full audit."""
    clusters = full_inventory.get("block_b_overlap_clusters")
    assert isinstance(clusters, list) and clusters, "block_b_overlap_clusters must be a non-empty list in full output"
    kinds = {c.get("kind") for c in clusters if isinstance(c, dict)}
    assert "dense_ownership_theme_by_architecture_layer" in kinds
    hubs = full_inventory.get("import_hub_modules")
    assert isinstance(hubs, list)
    files_roles = build_ownership_registry_index().get("files_roles", {})
    assert isinstance(files_roles, dict)
    for fp, roles in files_roles.items():
        assert fp in inventory_by_path, f"derived registry path not in inventory: {fp}"
        assert isinstance(roles, list) and roles


def test_evaluator_neighbor_may_have_general_inventory_layer(
    inventory: dict,
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    """Heuristic ``general`` is allowed for non-owner paths; governance only sharpens direct owners."""
    p = "tests/test_player_agency_evaluator.py"
    assert p in inventory_by_path
    full_row = _full_inventory_by_path(full_inventory).get(p)
    assert full_row is not None and full_row.get("likely_architecture_layer") == "general"
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=_LIVE_LEGALITY_GROUP_IDS,
        full_inventory_by_path=_full_inventory_by_path(full_inventory),
    )
    assert not any(p in e for e in errs)


def test_governance_rejects_stored_registry_positions(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    """AQ5: committed governance rows must not embed derived registry positions."""
    polluted = json.loads(json.dumps(inventory))
    polluted["files"][0]["ownership_registry_positions"] = [{"group_id": "x", "role": "direct_owner"}]
    polluted_by_path = _inventory_paths(polluted)
    errs = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        polluted,
        polluted_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("must not store ownership_registry_positions" in e for e in errs)


def test_governance_rejects_duplicate_direct_owner(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    owner = "tests/test_save_load.py"
    reg = {
        "a": replace(RESPONSIBILITY_REGISTRY["engine_truth_persistence_mechanics"], direct_owner=owner),
        "b": replace(RESPONSIBILITY_REGISTRY["planner_prompt_bundle_shipped_contract"], direct_owner=owner),
    }
    errs = collect_ownership_governance_errors(
        reg,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("duplicate direct_owner" in e for e in errs)


def test_governance_rejects_missing_inventory_path(inventory: dict, inventory_by_path: dict[str, dict]) -> None:
    reg = {
        "__missing__": ResponsibilityRecord(
            human_title="Synthetic",
            declared_architecture_layer="engine",
            direct_owner="tests/__this_file_should_not_exist__.py",
        ),
    }
    errs = collect_ownership_governance_errors(
        reg,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
    )
    assert any("not in inventory" in e for e in errs)


def test_direct_owner_general_disallowed_when_declared_layer_set() -> None:
    assert not _direct_owner_inventory_layer_ok("engine", "general")
    assert not _direct_owner_inventory_layer_ok("gate", "General")
    assert _direct_owner_inventory_layer_ok(None, "general")
    assert _direct_owner_inventory_layer_ok("engine", "smoke")
    assert _direct_owner_inventory_layer_ok("engine", "engine")


def test_governance_rejects_sharp_direct_owner_layer_mismatch(
    inventory: dict,
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    reg = {
        "__layer__": ResponsibilityRecord(
            human_title="Synthetic layer mismatch",
            declared_architecture_layer="gate",
            direct_owner="tests/test_save_load.py",
        ),
    }
    errs = collect_ownership_governance_errors(
        reg,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=frozenset(),
        full_inventory_by_path=_full_inventory_by_path(full_inventory),
    )
    assert any("inventory layer incompatible" in e for e in errs)


def test_inventory_per_test_rows_include_marker_set(
    test_audit_module: types.ModuleType,
    full_inventory: dict,
) -> None:
    """AQ6: per-test marker_set is derived from fresh audit output, not committed JSON."""
    rows = test_audit_module.derive_per_test_marker_rows(full_inventory)
    assert rows, "expected derived per-test marker rows from fresh inventory"
    missing = [r.get("nodeid") for r in rows if not isinstance(r, dict) or "marker_set" not in r]
    assert not missing, f"missing marker_set on {len(missing)} derived rows (first: {missing[:3]!r})"


def test_governance_registry_paths_have_derived_marker_sets(
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    """BF7: registry-owned paths retain marker_set data in derived full audit."""
    full_by_path = _full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f"{fp} missing from full inventory"
        marker_set = frow.get("marker_set")
        assert isinstance(marker_set, list)


def test_governance_registry_paths_have_derived_architecture_layers(
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    """BF6: registry-owned paths retain architecture-layer heuristics in derived full audit."""
    full_by_path = _full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f"{fp} missing from full inventory"
        layer = frow.get("likely_architecture_layer")
        assert isinstance(layer, str) and layer.strip()


def test_governance_registry_paths_have_derived_duplicate_base_names(
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    """BF5: registry-owned paths retain in-file duplicate-base-name data in derived full audit."""
    full_by_path = _full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f"{fp} missing from full inventory"
        dup_bases = frow.get("collected_duplicate_base_names")
        assert isinstance(dup_bases, list)


def test_governance_registry_paths_have_live_collected_counts(
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    """BF4: registry-owned paths retain live per-file collect counts in derived full audit."""
    full_by_path = _full_inventory_by_path(full_inventory)
    for fp in inventory_by_path:
        frow = full_by_path.get(fp)
        assert frow is not None, f"{fp} missing from full inventory"
        collected = frow.get("pytest_collected")
        nodeids = frow.get("collected_nodeids")
        assert isinstance(collected, int) and collected >= 0
        assert isinstance(nodeids, list)
        assert collected == len(nodeids), f"{fp}: pytest_collected mismatch vs collected_nodeids"


def test_cross_file_duplicate_allowlist_from_derived_full_audit(
    test_audit_module: types.ModuleType,
    full_inventory: dict,
) -> None:
    """AQ9: duplicate allowlist enforcement uses derived full audit output."""
    dups = full_inventory.get("cross_file_duplicate_test_names")
    assert isinstance(dups, list)
    errs = test_audit_module.collect_cross_file_duplicate_governance_errors(
        dups,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
    )
    assert not errs, "derived cross-file duplicate allowlist failures:\n" + "\n".join(errs)


def test_canonical_validation_layers_importable() -> None:
    assert vlc is not None, "game.validation_layer_contracts must import for layer alignment"
    assert set(vlc.CANONICAL_VALIDATION_LAYERS) == _CANONICAL


def _allowed_governance_committed_paths(
    registry: Mapping[str, ResponsibilityRecord],
    inventory: dict,
    *,
    cross_file_duplicate_test_names: list | None = None,
) -> set[str]:
    """Paths permitted in committed governance ``files[]`` (registry + cross-file dup files)."""
    paths: set[str] = set()
    files_roles = build_ownership_registry_index(registry).get("files_roles", {})
    if isinstance(files_roles, dict):
        paths.update(str(fp).replace("\\", "/") for fp in files_roles)
    dups = cross_file_duplicate_test_names
    if dups is None:
        dups = inventory.get("cross_file_duplicate_test_names")
    if isinstance(dups, list):
        for block in dups:
            if not isinstance(block, dict):
                continue
            files = block.get("files")
            if isinstance(files, list):
                paths.update(str(fp).replace("\\", "/") for fp in files)
    return paths


def collect_ownership_governance_errors(
    registry: Mapping[str, ResponsibilityRecord],
    inventory: dict,
    inventory_by_path: dict[str, dict],
    *,
    cross_file_allowlist: Mapping[str, str],
    live_legality_group_ids: AbstractSet[str],
    cross_file_duplicate_test_names: list | None = None,
    full_inventory_by_path: Mapping[str, dict] | None = None,
) -> list[str]:
    """Pure governance checks for tests and unit tests with synthetic registries."""
    errors: list[str] = []
    seen_owners: dict[str, str] = {}

    if "tests" in inventory:
        errors.append(
            "governance inventory must not store tests[] "
            "(derive per-test marker coverage via tools/test_audit.py --check)",
        )
    if "block_b_overlap_clusters" in inventory:
        errors.append(
            "governance inventory must not store block_b_overlap_clusters "
            "(use py -3 tools/test_audit.py --full for triage aggregates)",
        )
    if "import_hub_modules" in inventory:
        errors.append(
            "governance inventory must not store import_hub_modules "
            "(use py -3 tools/test_audit.py --full for triage aggregates)",
        )
    if "cross_file_duplicate_test_names" in inventory:
        errors.append(
            "governance inventory must not store cross_file_duplicate_test_names "
            "(derive via tools/test_audit.py --check)",
        )

    allowed_paths = _allowed_governance_committed_paths(
        registry,
        inventory,
        cross_file_duplicate_test_names=cross_file_duplicate_test_names,
    )
    for fp in inventory_by_path:
        if fp not in allowed_paths:
            errors.append(
                f"governance files[] must not store non-governance path {fp!r} "
                f"(registry-owned and cross-file duplicate paths only)",
            )

    for _fp, row in inventory_by_path.items():
        if not isinstance(row, dict):
            errors.append(f"inventory row for {_fp!r} is not an object")
            continue
        if "marker_set" in row:
            errors.append(
                f"{_fp}: governance inventory must not store marker_set "
                f"(derive via tools/test_audit.py --check)",
            )
        if "ownership_registry_positions" in row:
            errors.append(
                f"{_fp}: governance inventory must not store ownership_registry_positions "
                f"(derive via build_ownership_registry_index())",
            )
        if "pytest_collected" in row:
            errors.append(
                f"{_fp}: governance inventory must not store pytest_collected "
                f"(derive via tools/test_audit.py --check)",
            )
        if "collected_duplicate_base_names" in row:
            errors.append(
                f"{_fp}: governance inventory must not store collected_duplicate_base_names "
                f"(derive via tools/test_audit.py --check)",
            )
        if "likely_architecture_layer" in row:
            errors.append(
                f"{_fp}: governance inventory must not store likely_architecture_layer "
                f"(derive via tools/test_audit.py --check)",
            )

    derived_roles = build_ownership_registry_index(registry).get("files_roles", {})
    if isinstance(derived_roles, dict):
        for fp in derived_roles:
            if fp not in inventory_by_path:
                errors.append(f"derived registry path not in inventory: {fp}")

    for gid, rec in registry.items():
        neighbors = _neighbor_paths_for_group(rec)
        seen_neighbor: dict[str, str] = {}
        for npath, field in neighbors:
            if npath in seen_neighbor and seen_neighbor[npath] != field:
                errors.append(
                    f"{gid}: neighbor path {npath!r} listed under both {seen_neighbor[npath]!r} and {field!r}",
                )
            seen_neighbor[npath] = field

        for rel, field in _paths_for_group(rec):
            key = rel.replace("\\", "/")
            if key not in inventory_by_path:
                errors.append(f"{gid}: {field} not in inventory: {key}")

        if rec.direct_owner:
            dkey = rec.direct_owner.replace("\\", "/")
            if dkey in seen_owners and seen_owners[dkey] != gid:
                errors.append(
                    f"duplicate direct_owner claim: {dkey!r} used by {seen_owners[dkey]!r} and {gid!r}",
                )
            seen_owners[dkey] = gid
            if dkey in _DOWNSTREAM_INTEGRATION_SMOKE_ONLY:
                errors.append(
                    f"{gid}: direct_owner {rec.direct_owner!r} is AD-registered downstream "
                    f"integration smoke only; assign a gate/unit owner instead.",
                )

        if gid in live_legality_group_ids and _path_is_disallowed_live_legality_owner(rec.direct_owner):
            errors.append(
                f"{gid}: direct_owner {rec.direct_owner!r} looks like transcript/gauntlet/"
                f"playability/evaluator suite; pick a unit/integration gate owner instead.",
            )

        row = None
        if full_inventory_by_path is not None:
            row = full_inventory_by_path.get(rec.direct_owner.replace("\\", "/"))
        if row is not None:
            likely = row.get("likely_architecture_layer")
            if isinstance(likely, str) and not _direct_owner_inventory_layer_ok(rec.declared_architecture_layer, likely):
                if _normalize_layer(likely) == "general" and rec.declared_architecture_layer is not None:
                    detail = "direct owners may not rest on heuristic `general` when a declared validation layer is set"
                else:
                    detail = "tighten tools/test_audit.py heuristics or adjust declared_architecture_layer in the registry"
                errors.append(
                    f"{gid}: direct owner inventory layer incompatible with declared "
                    f"{rec.declared_architecture_layer!r}: likely_architecture_layer {likely!r} "
                    f"for {rec.direct_owner} ({detail}).",
                )

    dups = cross_file_duplicate_test_names
    if dups is None:
        dups = inventory.get("cross_file_duplicate_test_names")
    if isinstance(dups, list):
        for block in dups:
            if not isinstance(block, dict):
                continue
            base = block.get("base_name")
            if not isinstance(base, str):
                continue
            if base in cross_file_allowlist:
                continue
            files = block.get("files")
            fl = ", ".join(files) if isinstance(files, list) else "?"
            errors.append(
                f"cross-file duplicate test name {base!r} not allowlisted "
                f"(files: {fl}); rename tests or extend allowlist with a reason.",
            )

    return errors


def test_ownership_registry_governance(
    inventory: dict,
    inventory_by_path: dict[str, dict],
    full_inventory: dict,
) -> None:
    derived_dups = full_inventory.get("cross_file_duplicate_test_names")
    errors = collect_ownership_governance_errors(
        RESPONSIBILITY_REGISTRY,
        inventory,
        inventory_by_path,
        cross_file_allowlist=_CROSS_FILE_DUPLICATE_ALLOWLIST,
        live_legality_group_ids=_LIVE_LEGALITY_GROUP_IDS,
        cross_file_duplicate_test_names=derived_dups if isinstance(derived_dups, list) else None,
        full_inventory_by_path=_full_inventory_by_path(full_inventory),
    )
    assert not errors, "ownership governance failures:\n" + "\n".join(errors)


def test_allowlist_entries_have_non_empty_reasons() -> None:
    for name, reason in _CROSS_FILE_DUPLICATE_ALLOWLIST.items():
        assert name.startswith("test_"), name
        assert reason.strip(), f"empty allowlist reason for {name!r}"


def test_final_emission_meta_projection_read_side_ownership_boundaries() -> None:
    """Cycle AE4: read-side lineage/projection edits stay in meta projection ownership."""
    meta_proj = RESPONSIBILITY_REGISTRY["final_emission_meta_projection"]
    gate_orch = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]

    assert meta_proj.direct_owner == "tests/test_final_emission_meta.py"
    assert gate_orch.direct_owner == "tests/test_final_emission_gate.py"
    assert meta_proj.direct_owner != gate_orch.direct_owner

    gate_path = "tests/test_final_emission_gate.py"
    assert gate_path not in meta_proj.downstream_consumer_suites
    assert gate_path not in meta_proj.smoke_suites
    assert gate_path not in meta_proj.transcript_suites
    assert gate_path not in meta_proj.gauntlet_suites
    assert gate_path not in meta_proj.evaluator_suites
    assert gate_path not in meta_proj.compatibility_residue_suites

    title = meta_proj.human_title.lower()
    assert "read path" in title or "replay read path" in title
    assert "projection" in title
    assert "gate orchestration" not in title


def test_ba7_gate_magnet_guard_paths_cover_gate_orchestration_owners() -> None:
    """BA-7: magnet guard spans gate-layer direct owners except meta projection and gauntlet."""
    guarded = gate_magnet_guard_paths()
    assert "tests/test_final_emission_gate.py" in guarded
    assert "tests/test_final_emission_validators.py" in guarded
    assert "tests/test_output_sanitizer.py" in guarded
    assert "tests/test_final_emission_meta.py" not in guarded
    assert "tests/test_gauntlet_regressions.py" not in guarded


def test_ba7_gate_direct_owners_do_not_import_replay_read_side_projection_helpers() -> None:
    """BA-7 / AG-10: gate direct-owner suites must not import replay/dashboard/classifier projection helpers."""
    violations: list[str] = []
    for rel in gate_magnet_guard_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f"missing gate magnet-guard path: {rel}"
        source = path.read_text(encoding="utf-8")
        violations.extend(collect_gate_magnet_guard_import_violations(rel, source))
    assert not violations, "gate magnet-guard import violations:\n" + "\n".join(violations)


def test_ba7_gate_direct_owners_do_not_accumulate_read_side_projection_assertions() -> None:
    """BA-7 / AG-10: gate direct-owner suites must not re-own replay/dashboard/classifier projection contracts."""
    violations: list[str] = []
    for rel in gate_magnet_guard_paths():
        path = _REPO_ROOT / rel
        source = path.read_text(encoding="utf-8")
        violations.extend(collect_gate_magnet_guard_source_fragment_violations(rel, source))
    assert not violations, "gate magnet-guard source-fragment violations:\n" + "\n".join(violations)


def test_final_emission_gate_does_not_accumulate_read_side_projection_assertions() -> None:
    """AG-10: primary gate owner stays free of replay read-side projection assertion creep."""
    rel = "tests/test_final_emission_gate.py"
    source = (_REPO_ROOT / rel).read_text(encoding="utf-8")
    violations = collect_gate_magnet_guard_source_fragment_violations(rel, source)
    assert not violations, (
        "tests/test_final_emission_gate.py owns gate orchestration/wrappers, not read-side "
        "replay projection assertions. Move these contracts to tests/test_final_emission_meta.py:\n"
        + "\n".join(violations)
    )


def test_bd6_gate_dependency_compression_allowlist_entries_have_non_empty_reasons() -> None:
    """BD-6: every compression-guard allowlist path documents why it may import compressed gate symbols."""
    for path, reason in _BD6_GATE_DEPENDENCY_COMPRESSION_ALLOWLIST.items():
        assert path.startswith("tests/"), path
        assert reason.strip(), f"empty BD-6 allowlist reason for {path!r}"


def test_bd6_gate_dependency_compression_guard_detects_synthetic_violation() -> None:
    """BD-6: guard flags representative compressed imports with facade guidance."""
    synthetic = (
        "from game.final_emission_gate import apply_final_emission_gate\n"
        "from game.final_emission_meta import read_final_emission_meta_dict, OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED\n"
        "import game.final_emission_replay_projection as replay\n"
    )
    rel = "tests/test_synthetic_bd6_violation.py"
    violations = collect_gate_dependency_compression_guard_violations(rel, synthetic)
    joined = "\n".join(violations)
    assert any("apply_final_emission_gate" in v for v in violations)
    assert any("read_final_emission_meta_dict" in v for v in violations)
    assert any("OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED" in v for v in violations)
    assert any("final_emission_replay_projection" in v for v in violations)
    assert "apply_final_emission_gate_consumer" in joined
    assert "final_emission_meta_from_output" in joined
    assert "opening_fallback_evidence" in joined
    assert "golden_replay_projection" in joined


def test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports() -> None:
    """BD-6: non-owner tests must not reintroduce direct imports compressed during BD-2–BD-5."""
    violations: list[str] = []
    for rel in iter_gate_dependency_compression_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f"missing BD-6 scan path: {rel}"
        source = path.read_text(encoding="utf-8")
        violations.extend(collect_gate_dependency_compression_guard_violations(rel, source))
    assert not violations, "gate dependency compression-guard import violations:\n" + "\n".join(violations)


def test_ad3_gate_orchestration_direct_owner_is_final_emission_gate() -> None:
    """Cycle AD-3: gate orchestration normative owner stays on the gate module."""
    rec = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]
    assert rec.direct_owner.replace("\\", "/") == "tests/test_final_emission_gate.py"


def test_ad3_downstream_integration_smoke_suites_registered_as_neighbors() -> None:
    """Cycle AD-3: AD-thinned suites are downstream neighbors, never direct owners."""
    gate = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]
    sanitizer = RESPONSIBILITY_REGISTRY["output_sanitizer_final_string_cleanup"]
    visibility = RESPONSIBILITY_REGISTRY["final_emission_visibility_semantics"]
    social = RESPONSIBILITY_REGISTRY["social_emission_legality_surface"]

    gate_downstream = frozenset(p.replace("\\", "/") for p in gate.downstream_consumer_suites)
    assert _DOWNSTREAM_INTEGRATION_SMOKE_ONLY.issubset(gate_downstream)

    turn_pipeline = "tests/test_turn_pipeline_shared.py"
    assert turn_pipeline in gate_downstream
    assert turn_pipeline in frozenset(
        p.replace("\\", "/") for p in sanitizer.downstream_consumer_suites
    )
    assert turn_pipeline in frozenset(
        p.replace("\\", "/") for p in visibility.downstream_consumer_suites
    )

    ac_rd = frozenset(
        {
            "tests/test_answer_completeness_rules.py",
            "tests/test_response_delta_requirement.py",
        }
    )
    assert ac_rd.issubset(gate_downstream)
    assert ac_rd.issubset(
        frozenset(p.replace("\\", "/") for p in social.downstream_consumer_suites)
    )

    for gid, rec in RESPONSIBILITY_REGISTRY.items():
        owner = rec.direct_owner.replace("\\", "/")
        assert owner not in _DOWNSTREAM_INTEGRATION_SMOKE_ONLY, (
            f"{gid} must not list {owner!r} as direct_owner "
            f"(downstream integration smoke only)."
        )


def test_ad3_golden_replay_is_gauntlet_neighbor_not_gate_direct_owner() -> None:
    """Cycle AD-3: replay observation locks live under gauntlet neighbor, not gate orchestration."""
    gate = RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"]
    gauntlet = RESPONSIBILITY_REGISTRY["gauntlet_playability_validation"]
    golden = "tests/test_golden_replay.py"

    assert golden in frozenset(p.replace("\\", "/") for p in gauntlet.gauntlet_suites)
    assert gauntlet.direct_owner.replace("\\", "/") != gate.direct_owner.replace("\\", "/")
    assert golden not in frozenset(p.replace("\\", "/") for p in gate.downstream_consumer_suites)


def test_bi8_golden_replay_ownership_boundary_is_locked() -> None:
    """Cycle BI-8: replay remains an orchestration/observation bridge, not a subsystem owner."""
    target_sources = {
        rel_path: (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for rel_path in _BI8_GOLDEN_REPLAY_TARGETS
    }
    combined_docs = "\n".join(target_sources.values()).lower()
    for phrase in (
        "replay orchestration",
        "observation consumption",
        "protected assertion bridge diagnostics",
        "long-session",
        "speaker legality",
        "route enum legality",
        "final emission gate orchestration",
        "opening/fallback owner-bucket semantics",
        "sanitizer phrase legality",
        "dashboard/classifier",
        "stability/taxonomy threshold",
    ):
        assert phrase in combined_docs, f"BI-8 golden replay ownership note missing {phrase!r}"

    api_exports = _module_all_exports(target_sources["tests/helpers/golden_replay_api.py"])
    assert _BI8_GOLDEN_REPLAY_OWNED_EXPORTS <= api_exports
    forbidden_exports = _BI8_GOLDEN_REPLAY_FORBIDDEN_EXPORTS & api_exports
    assert not forbidden_exports, (
        "golden replay API must not export subsystem legality helper presets: "
        f"{sorted(forbidden_exports)!r}"
    )

    helper_api_source = "\n".join(
        (
            target_sources["tests/helpers/golden_replay.py"],
            target_sources["tests/helpers/golden_replay_api.py"],
        )
    )
    helper_api_forbidden = {
        fragment: reason
        for fragment, reason in _BI8_GOLDEN_REPLAY_FORBIDDEN_SOURCE_FRAGMENTS.items()
        if fragment in helper_api_source
    }
    assert not helper_api_forbidden, (
        "golden replay helper/API must not re-own subsystem legality details: "
        f"{helper_api_forbidden!r}"
    )


def test_bg1_protected_replay_manifest_registry_parity() -> None:
    """Cycle BG-1: manifest generation stays registry-backed and parity-checked."""
    import importlib.util

    import tests.helpers.golden_replay_projection as acceptance_projection

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "refresh_protected_replay_manifest",
        root / "tools" / "refresh_protected_replay_manifest.py",
    )
    assert spec is not None and spec.loader is not None
    refresh_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_mod)

    manifest_text = refresh_mod.MANIFEST_PATH.read_text(encoding="utf-8")
    assert acceptance_projection.protected_observation_manifest_registry_parity_errors(
        manifest_text
    ) == []
    assert acceptance_projection.protected_observation_manifest_section_is_current(manifest_text)
    assert refresh_mod.manifest_section_is_current(manifest_text)

    registry_paths = {
        field.path for field in acceptance_projection.protected_observation_field_registry()
    }
    assert registry_paths == set(acceptance_projection.protected_observation_field_paths())
    assert tuple(
        path for path, _bucket in acceptance_projection.protected_observation_manifest_field_rows()
    ) == acceptance_projection.protected_observation_field_paths()

    registry_buckets = {
        field.path: field.drift_bucket
        for field in acceptance_projection.protected_observation_field_registry()
    }
    assert refresh_mod._registry_fields_by_path() == {
        path: acceptance_projection.protected_observation_drift_bucket(path)
        for path in acceptance_projection.protected_observation_field_paths()
    }
    for path, bucket in registry_buckets.items():
        assert acceptance_projection.protected_observation_drift_bucket(path) == bucket


def test_ao5_runtime_and_acceptance_projection_modules_remain_separate() -> None:
    """Cycle AO5: runtime lineage projection and acceptance observation projection stay split."""
    import game.final_emission_replay_projection as runtime_projection
    import tests.helpers.golden_replay_projection as acceptance_projection

    runtime_doc = (runtime_projection.__doc__ or "").lower()
    acceptance_doc = (acceptance_projection.__doc__ or "").lower()

    assert "do not merge" in runtime_doc
    assert "do not merge" in acceptance_doc
    assert "golden_replay_projection" in runtime_doc
    assert "final_emission_replay_projection" in acceptance_doc
    assert runtime_projection.__name__ == "game.final_emission_replay_projection"
    assert acceptance_projection.__name__ == "tests.helpers.golden_replay_projection"

    lineage_surface = runtime_projection.read_side_lineage_projection_surface()
    assert lineage_surface["mutation_lineage_key"] == "final_emission_mutation_lineage"
    assert len(acceptance_projection.protected_observation_field_registry()) == len(
        acceptance_projection.protected_observation_field_paths()
    )

    meta_proj = RESPONSIBILITY_REGISTRY["final_emission_meta_projection"]
    gauntlet = RESPONSIBILITY_REGISTRY["gauntlet_playability_validation"]
    assert "tests/test_golden_replay.py" in frozenset(
        p.replace("\\", "/") for p in gauntlet.gauntlet_suites
    )
    assert meta_proj.direct_owner.replace("\\", "/") == "tests/test_final_emission_meta.py"
    assert "game.final_emission_replay_projection" not in frozenset(
        p.replace("\\", "/") for p in meta_proj.downstream_consumer_suites
    )


def test_al4_legality_owners_and_smoke_facade_locked() -> None:
    """Cycle AL4: AL1–AL3 convergence boundaries stay aligned with registry direct owners."""
    assert RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"].direct_owner.replace(
        "\\", "/",
    ) == _AL4_LEGALITY_OWNER_PATHS["final_emission_gate"]
    assert RESPONSIBILITY_REGISTRY["final_emission_meta_projection"].direct_owner.replace(
        "\\", "/",
    ) == _AL4_LEGALITY_OWNER_PATHS["final_emission_meta"]
    assert RESPONSIBILITY_REGISTRY["output_sanitizer_final_string_cleanup"].direct_owner.replace(
        "\\", "/",
    ) == _AL4_LEGALITY_OWNER_PATHS["output_sanitizer"]
    assert RESPONSIBILITY_REGISTRY["social_emission_legality_surface"].direct_owner.replace(
        "\\", "/",
    ) == _AL4_LEGALITY_OWNER_PATHS["social_exchange_emission"]

    turn_pipeline = _AL4_LEGALITY_OWNER_PATHS["turn_pipeline_http_smoke"]
    gate_downstream = frozenset(
        p.replace("\\", "/")
        for p in RESPONSIBILITY_REGISTRY["final_emission_gate_orchestration"].downstream_consumer_suites
    )
    assert turn_pipeline in gate_downstream
    assert turn_pipeline in _DOWNSTREAM_INTEGRATION_SMOKE_ONLY

    facade_path = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).resolve()
    assert facade_path.is_file(), f"missing downstream smoke facade: {_DOWNSTREAM_SMOKE_FACADE}"

    route_owner = (_REPO_ROOT / _AL4_LEGALITY_OWNER_PATHS["dialogue_route_classification"]).resolve()
    assert route_owner.is_file(), (
        "dialogue route legality owner must remain tests/test_dialogue_routing_lock.py"
    )


def test_bj4_emission_smoke_facade_stays_weak_consumer_bridge() -> None:
    """Cycle BJ-4: emission_smoke_assertions remains smoke/bridge, not a hidden legality owner."""
    facade_path = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).resolve()
    source = facade_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    public_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    for expected_bridge in (
        _BJ4_SMOKE_FACADE_ALLOWED_GATE_BRIDGES
        | _BJ4_SMOKE_FACADE_ALLOWED_REPAIR_BRIDGES
    ):
        assert expected_bridge in public_functions

    public_names = set(public_functions)
    public_table_lengths: dict[str, int] = {}
    for node in tree.body:
        target_name: str | None = None
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target_name = node.targets[0].id
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        if not target_name or target_name.startswith("_"):
            continue
        public_names.add(target_name)
        if target_name.isupper() and isinstance(value, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            public_table_lengths[target_name] = len(value.keys if isinstance(value, ast.Dict) else value.elts)

    forbidden_public_names = {
        name: reason
        for name in public_names
        for fragment, reason in _BJ4_SMOKE_FACADE_FORBIDDEN_PUBLIC_NAME_FRAGMENTS.items()
        if fragment in name.lower()
    }
    assert not forbidden_public_names, (
        "emission_smoke_assertions.py must not grow public legality-owner helpers/constants: "
        f"{forbidden_public_names!r}"
    )

    oversized_public_tables = {
        name: size
        for name, size in public_table_lengths.items()
        if size > 8
    }
    assert not oversized_public_tables, (
        "emission_smoke_assertions.py must not grow large public phrase/route/repair tables; "
        f"move legality matrices to owner suites: {oversized_public_tables!r}"
    )

    low = source.lower()
    assert "ownership note" in low
    assert "weak downstream smoke/consumer bridges" in low
    assert "must not become the owner" in low
    assert "full gate legality matrices" in low
    assert "route enum tables" in low
    assert "sanitizer phrase legality" in low
    assert "ac/rd repair semantics" in low


def test_be6_scaffold_phrase_triple_layer_split_locked() -> None:
    """Cycle BE6: sanitizer legality, HTTP smoke phrases, and replay scaffold projection stay separate."""
    for label, rel_path in _BE6_SCAFFOLD_PHRASE_LAYER_OWNERS.items():
        path = (_REPO_ROOT / rel_path).resolve()
        assert path.is_file(), f"BE6 layer {label!r} missing owner path: {rel_path}"

    smoke_doc = (_REPO_ROOT / _DOWNSTREAM_SMOKE_FACADE).read_text(encoding="utf-8")
    assert "BE6" in smoke_doc, "emission_smoke_assertions must document Cycle BE6 triple-layer split"
    assert "do not merge" in smoke_doc.lower(), (
        "emission_smoke_assertions must warn against merging phrase matrices"
    )
    assert "tests/test_output_sanitizer.py" in smoke_doc
    assert "golden_replay_projection" in smoke_doc
    assert "final_text_has_scaffold_leakage" in smoke_doc

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BE6" in registry_doc, "ownership registry must document Cycle BE6 triple-layer split"
    assert "do not merge" in registry_doc.lower()
