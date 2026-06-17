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
- **Runtime gate entry guard** (Cycle BN1): non-owner ``game/`` modules must not import
  ``apply_final_emission_gate`` from ``game.final_emission_gate``; runtime/API callers use
  ``game.final_emission_runtime.finalize_player_facing_emission``. Enforced by
  ``test_bn1_runtime_gate_entry_*``.
- **Lazy gate namespace guard** (Cycle BN2): ``final_emission_non_strict_stack`` and
  ``final_emission_terminal_pipeline`` must not lazy-import ``game.final_emission_gate as feg``
  or access ``feg.<symbol>``; layer owners are imported directly. Enforced by
  ``test_bn2_lazy_gate_namespace_*``.
- **Gate context preflight import guard** (Cycle BN3): ``final_emission_gate_context`` must not
  regrow direct layer-meta owner imports after preflight-defaults extraction; use
  ``final_emission_gate_preflight_defaults``. Enforced by ``test_bn3_gate_context_*``.
- **Gate context telemetry import guard** (Cycle BN4): ``final_emission_gate_context`` must not
  regrow direct telemetry/provenance imports after preflight-telemetry extraction; use
  ``final_emission_gate_preflight_telemetry``. Enforced by ``test_bn4_gate_context_*``.
- **Gate context upstream attach import guard** (Cycle BN5): ``final_emission_gate_context`` must
  not regrow direct upstream attach imports after preflight-upstream extraction; use
  ``final_emission_gate_preflight_upstream``. Enforced by ``test_bn5_gate_context_*``.
- **Gate context turn-packet import guard** (Cycle BN6): ``final_emission_gate_context`` must not
  regrow direct response-policy / turn-packet setup imports after preflight turn-packet extraction;
  use ``final_emission_gate_preflight_turn_packet``. Enforced by ``test_bn6_gate_context_*``.
- **Gate context interaction metadata import guard** (Cycle BN7): ``final_emission_gate_context``
  must not regrow direct interaction inspection imports after preflight interaction extraction; use
  ``final_emission_gate_preflight_interaction``. Enforced by ``test_bn7_gate_context_*``.
- **Gate context strict-social routing import guard** (Cycle BN8): ``final_emission_gate_context``
  must not regrow direct strict-social routing/sanitizer imports after preflight strict-social
  extraction; use ``final_emission_gate_preflight_strict_social``. Enforced by
  ``test_bn8_gate_context_*``.
- **Gate context pregate text import guard** (Cycle BN9): ``final_emission_gate_context`` must not
  regrow direct ``final_emission_text`` imports after preflight pregate-text extraction; use
  ``final_emission_gate_preflight_pregate_text``. Enforced by ``test_bn9_gate_context_*``.
- **Gate context branch-flag derivation guard** (Cycle BN10): branch flags must route through
  ``final_emission_gate_preflight_branch_flags``. Enforced by ``test_bn10_gate_context_*``.
- **Gate context preflight-only import allowlist** (Cycle BN11): ``final_emission_gate_context``
  may import only stdlib/typing plus ``final_emission_gate_preflight_*`` helpers. Enforced by
  ``test_bn11_gate_context_*``.

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
    "tests/test_final_emission_gate.py": "Gate orchestration owner (BD-2/BD-5/BJ-41/BJ-42/BJ-43/BJ-44/BJ-45/BJ-46/BJ-47/BJ-48/BJ-49/BJ-50/BJ-51/BJ-52/BJ-53/BJ-54/BJ-55/BJ-56/BJ-57/BJ-58/BJ-59/BJ-60/BJ-61/BJ-62/BJ-63/BJ-64/BJ-65/BJ-66/BJ-67/BJ-68/BJ-69/BJ-70/BJ-71/BJ-72/BJ-73/BJ-74/BJ-91/BJ-92/BJ-93/BJ-94/BJ-95/BJ-96/BJ-97/BJ-98/BJ-99/BJ-100/BJ-101/BJ-102/BJ-103/BJ-104/BJ-105/BJ-106/BJ-107/BJ-108/BJ-109/BJ-110/BJ-111/BJ-112/BJ-123/BJ-124/BJ-127/BJ-128/BJ-129 KEEP)",
    "tests/test_final_emission_meta.py": "FEM projection / runtime-lineage owner (BD-3/BD-4/BD-5 KEEP)",
    "tests/test_fallback_behavior_gate.py": "Gate-adjacent behavior owner (BD-2 KEEP)",
    "tests/test_final_emission_boundary_no_semantic_repair.py": "Gate boundary owner; terminal_pipeline visibility noop (BJ-123 KEEP)",
    "tests/test_block_s_speaker_local_rebind_equivalence.py": "Speaker equivalence / orchestration-order proof (BD-2 KEEP)",
    "tests/test_block_t_speaker_relocation_shadow_equivalence.py": "Speaker equivalence / orchestration-order proof (BD-2 KEEP)",
    "tests/test_block_u_finalize_stack_divergence.py": "Finalize-stack divergence proof (BD-2 KEEP)",
    "tests/test_social_exchange_emission.py": "Strict-social emission legality owner (BD-2 KEEP)",
    "tests/test_speaker_contract_enforcement.py": "Speaker contract enforcement owner (BJ-28 KEEP)",
    "tests/test_interaction_continuity_repair.py": "Interaction continuity emission owner (BJ-29 KEEP)",
    "tests/test_dialogue_social_plan.py": "Dialogue social plan + strict-social enforcement owner (BJ-30 KEEP)",
    "tests/test_tone_escalation_rules.py": "Tone escalation layer owner (BJ-31 KEEP)",
    "tests/test_narrative_authority_rules.py": "Narrative authority layer owner (BJ-32 KEEP)",
    "tests/test_anti_railroading.py": "Anti-railroading layer owner (BJ-33 KEEP)",
    "tests/test_context_separation.py": "Context separation layer owner (BJ-34 KEEP)",
    "tests/test_player_facing_narration_purity.py": "Player-facing narration purity layer owner (BJ-35 KEEP)",
    "tests/test_answer_shape_primacy.py": "Answer-shape primacy layer owner (BJ-36 KEEP)",
    "tests/test_final_emission_visibility.py": "Visibility semantics owner (BD-3 KEEP)",
    "tests/test_final_emission_channel_separation.py": "FEM channel packaging owner-adjacent (BD-3 KEEP)",
    "tests/test_opening_fallback_owner_bucket.py": "Opening fallback owner-bucket mapping owner (BD-5 KEEP)",
    "tests/test_final_emission_opening_fallback.py": "Opening fallback owner (BD-5 KEEP)",
    "tests/test_final_emission_sealed_fallback.py": "Sealed fallback owner (BD-5 KEEP)",
    "tests/test_final_emission_visibility_fallback.py": "Visibility fallback owner-adjacent (BD-5/BJ-27/BJ-73 KEEP)",
    "tests/test_final_emission_first_mention_composition.py": "First-mention composition owner (BJ-7 KEEP)",
    "tests/test_final_emission_fast_fallback_composition.py": "Fast-fallback composition owner (BJ-8 KEEP)",
    "tests/test_final_emission_passive_scene_pressure.py": "Passive scene pressure owner (BJ-9 KEEP)",
    "tests/test_final_emission_scene_emit_integrity.py": "Scene emit integrity owner (BJ-10 KEEP)",
    "tests/test_final_emission_scene_state_anchor.py": "Scene state anchor owner (BJ-11/BJ-37 KEEP)",
    "tests/test_final_emission_scene_facts.py": "Scene facts owner (BJ-12 KEEP)",
    "tests/test_final_emission_referential_clarity.py": "Referential clarity owner (BJ-13 KEEP)",
    "tests/test_final_emission_response_type.py": "Response-type contract helper + enforce owner (BJ-18/BJ-39 KEEP)",
    "tests/test_final_emission_narrative_mode_output.py": "Narrative mode output validation owner (BJ-19 KEEP)",
    "tests/test_final_emission_acceptance_quality.py": "Acceptance quality N4 helper + floor seam owner (BJ-20/BJ-40/BJ-74 KEEP)",
    _BD6_SMOKE_FACADE: "Downstream smoke facade delegate (BD-2/BD-3 internal imports)",
    _BD6_GOLDEN_REPLAY_FACADE: "Golden replay / replay-projection facade delegate (BD-3/BD-4/BD-5)",
    _BD6_OPENING_FACADE: "Opening fallback evidence facade delegate (BD-5)",
    "tests/helpers/gate_equivalence_monkeypatch.py": "Gate namespace monkeypatch equivalence helper (BD-2 KEEP)",
    "tests/helpers/opening_fallback_gate_harness.py": "Opening attach-then gate harness; response_type owner seams (BJ-123 KEEP)",
    "tests/helpers/post_speaker_finalize_probe.py": "Gate finalize-stack probe wrappers (BD-2 KEEP)",
    "tests/helpers/speaker_relocation_shadow_harness.py": "Speaker relocation shadow harness; feg namespace (BD-2 KEEP)",
    "tests/helpers/strict_social_harness.py": "Strict-social harness; feg monkeypatch + consumer entry (BD-2 KEEP)",
    "tests/test_architecture_audit_tool.py": "Audit fixture strings embed gate-import examples",
    "tests/test_validation_layer_audit_smoke.py": "Audit fixture strings embed gate-import examples",
    "tests/test_test_audit_tool.py": "Inventory audit fixture strings embed gate-import examples",
    "tests/test_realization_layer_audit.py": "Realization audit fixture strings embed gate-import examples",
    "tests/test_run_scenario_spine_validation.py": "Scenario-spine validation; canonical FEM/lineage read for opening attribution diagnostics (BL1)",
    "tests/test_ownership_registry.py": "Governance module; AO5 runtime vs acceptance boundary check imports replay projection",
}

# Cycle BN1: runtime/API modules may not import apply_final_emission_gate from the gate owner
# directly; use game.final_emission_runtime.finalize_player_facing_emission instead.
_BN1_RUNTIME_GATE_ENTRY_ALLOWLIST: Final[Mapping[str, str]] = {
    "game/final_emission_gate.py": "Orchestration owner defines apply_final_emission_gate (BN1 KEEP)",
    "game/final_emission_runtime.py": "Single production delegate seam (BN1 KEEP)",
}
_BN1_RUNTIME_GATE_ENTRY_REPLACEMENT: Final[str] = (
    "game.final_emission_runtime.finalize_player_facing_emission"
)
_BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT: Final[str] = (
    "tests.helpers.emission_smoke_assertions.apply_final_emission_gate_consumer"
)


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
            f"(integration/smoke) or game.final_emission_meta.read_final_emission_meta_dict "
            f"(gate-output FEM read)"
        )
    if module == "game.final_emission_replay_projection":
        return (
            f"game.final_emission_replay_projection "
            f"(e.g. build_fem_runtime_lineage_events, SEALED_REPLACEMENT_SUBKINDS)"
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


def collect_bn1_runtime_gate_entry_guard_violations(
    rel_path: str,
    source: str,
    *,
    allowlist: Mapping[str, str] = _BN1_RUNTIME_GATE_ENTRY_ALLOWLIST,
) -> list[str]:
    """Return violations when a non-owner game module imports gate entry directly."""
    norm = _normalize_test_rel_path(rel_path)
    if norm in allowlist:
        return []

    tree = ast.parse(source)
    violations: list[str] = []
    seen: set[tuple[str, str]] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "game.final_emission_gate":
            continue
        for alias in node.names:
            if alias.name != "apply_final_emission_gate":
                continue
            key = (node.module, alias.name)
            if key in seen:
                continue
            seen.add(key)
            violations.append(
                f"{norm}: forbidden direct runtime gate import "
                f"'game.final_emission_gate.apply_final_emission_gate' "
                f"(use {_BN1_RUNTIME_GATE_ENTRY_REPLACEMENT!r}; downstream tests: "
                f"{_BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT!r})",
            )
    return violations


def iter_bn1_runtime_gate_entry_guard_scan_paths(
    repo_root: Path | None = None,
    *,
    allowlist: Mapping[str, str] = _BN1_RUNTIME_GATE_ENTRY_ALLOWLIST,
) -> tuple[str, ...]:
    """All game/**/*.py paths subject to BN1 runtime gate-entry guard."""
    root = _REPO_ROOT if repo_root is None else repo_root
    paths: list[str] = []
    for path in sorted((root / "game").rglob("*.py")):
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
        "from game.final_emission_meta import read_final_emission_meta_from_turn_payload, OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED\n"
        "import game.final_emission_replay_projection as replay\n"
    )
    rel = "tests/test_synthetic_bd6_violation.py"
    violations = collect_gate_dependency_compression_guard_violations(rel, synthetic)
    joined = "\n".join(violations)
    assert any("apply_final_emission_gate" in v for v in violations)
    assert any("read_final_emission_meta_from_turn_payload" in v for v in violations)
    assert any("OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED" in v for v in violations)
    assert any("final_emission_replay_projection" in v for v in violations)
    assert "apply_final_emission_gate_consumer" in joined
    assert "final_emission_meta_from_output" in joined
    assert "opening_fallback_evidence" in joined
    assert "build_fem_runtime_lineage_events" in joined


def test_bd6_gate_dependency_compression_guard_non_owners_avoid_compressed_gate_imports() -> None:
    """BD-6: non-owner tests must not reintroduce direct imports compressed during BD-2–BD-5."""
    violations: list[str] = []
    for rel in iter_gate_dependency_compression_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f"missing BD-6 scan path: {rel}"
        source = path.read_text(encoding="utf-8")
        violations.extend(collect_gate_dependency_compression_guard_violations(rel, source))
    assert not violations, "gate dependency compression-guard import violations:\n" + "\n".join(violations)


def test_bn1_runtime_gate_entry_allowlist_entries_have_non_empty_reasons() -> None:
    """BN1: every runtime gate-entry allowlist path documents why it may import gate entry."""
    for path, reason in _BN1_RUNTIME_GATE_ENTRY_ALLOWLIST.items():
        assert path.startswith("game/"), path
        assert reason.strip(), f"empty BN1 allowlist reason for {path!r}"
    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN1" in registry_doc


def test_bn1_runtime_gate_entry_guard_detects_synthetic_violation() -> None:
    """BN1: guard flags direct gate entry imports in non-owner game modules."""
    synthetic = "from game.final_emission_gate import apply_final_emission_gate\n"
    rel = "game/synthetic_bn1_violation.py"
    violations = collect_bn1_runtime_gate_entry_guard_violations(rel, synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "apply_final_emission_gate" in joined
    assert _BN1_RUNTIME_GATE_ENTRY_REPLACEMENT in joined
    assert _BN1_DOWNSTREAM_TEST_GATE_ENTRY_REPLACEMENT in joined


def test_bn1_runtime_gate_entry_guard_non_owner_runtime_modules_avoid_direct_gate_import() -> None:
    """BN1: non-owner game modules must not import apply_final_emission_gate from the gate owner."""
    violations: list[str] = []
    for rel in iter_bn1_runtime_gate_entry_guard_scan_paths():
        path = _REPO_ROOT / rel
        assert path.is_file(), f"missing BN1 scan path: {rel}"
        source = path.read_text(encoding="utf-8")
        violations.extend(collect_bn1_runtime_gate_entry_guard_violations(rel, source))
    assert not violations, "BN1 runtime gate-entry import violations:\n" + "\n".join(violations)


def test_bn1_runtime_delegate_seam_remains_narrow() -> None:
    """BN1: final_emission_runtime stays a thin delegate with no policy imports."""
    import game.final_emission_runtime as runtime

    runtime_src = Path(runtime.__file__).read_text(encoding="utf-8")
    assert "def finalize_player_facing_emission" in runtime_src
    assert "from game.final_emission_gate import apply_final_emission_gate" in runtime_src
    assert "return apply_final_emission_gate(" in runtime_src
    forbidden_markers = (
        "from game.final_emission_meta import",
        "from game.final_emission_replay_projection import",
        "from game.output_sanitizer import",
        "from game.final_emission_validators import",
    )
    for marker in forbidden_markers:
        assert marker not in runtime_src, f"runtime seam must not import policy surface: {marker!r}"


def test_bn2_lazy_gate_namespace_allowlist_covers_scan_files() -> None:
    """BN2: retained-symbol map spans every lazy-namespace scan file."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN2_LAZY_GATE_NAMESPACE_FILES,
        BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE,
    )

    assert BN2_LAZY_GATE_NAMESPACE_FILES == frozenset(BN2_RETAINED_LAZY_GATE_SYMBOLS_BY_FILE)
    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN2" in registry_doc


def test_bn2_lazy_gate_namespace_guard_detects_synthetic_violation() -> None:
    """BN2: guard flags stale lazy feg namespace markers."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn2_lazy_gate_namespace_violations

    synthetic = (
        "def _gate_module():\n"
        "    import game.final_emission_gate as feg\n"
        "    return feg\n"
        "def run():\n"
        "    feg = _gate_module()\n"
        "    feg._apply_visibility_enforcement(out)\n"
    )
    rel = "game/final_emission_terminal_pipeline.py"
    violations = collect_bn2_lazy_gate_namespace_violations(rel, synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "def _gate_module(" in joined
    assert "import game.final_emission_gate" in joined
    assert "_apply_visibility_enforcement" in joined


def test_bn2_lazy_gate_namespace_guard_stack_modules_avoid_lazy_feg() -> None:
    """BN2: non_strict_stack and terminal_pipeline must not lazy-import gate namespace."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN2_LAZY_GATE_NAMESPACE_FILES,
        collect_bn2_lazy_gate_namespace_violations,
    )

    violations: list[str] = []
    for rel in sorted(BN2_LAZY_GATE_NAMESPACE_FILES):
        path = _REPO_ROOT / rel
        assert path.is_file(), f"missing BN2 scan path: {rel}"
        source = path.read_text(encoding="utf-8")
        violations.extend(collect_bn2_lazy_gate_namespace_violations(rel, source))
    assert not violations, "BN2 lazy gate namespace violations:\n" + "\n".join(violations)


def test_bn3_gate_context_preflight_defaults_owner_entrypoint_locked() -> None:
    """BN3: preflight layer-meta defaults live on dedicated helper owner."""
    import game.final_emission_gate_preflight_defaults as gpfd

    assert callable(getattr(gpfd, "initialize_gate_preflight_layer_meta_defaults", None))
    assert callable(getattr(gpfd, "GatePreflightLayerMetaDefaults", None))


def test_bn3_gate_context_preflight_defaults_guard_detects_synthetic_violation() -> None:
    """BN3: guard flags regrown direct layer-meta owner imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn3_gate_context_layer_meta_import_violations

    synthetic = (
        "from game.final_emission_tone_escalation import default_tone_escalation_meta\n"
        "def initialize_gate_execution_context():\n"
        "    return default_tone_escalation_meta()\n"
    )
    violations = collect_bn3_gate_context_layer_meta_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "final_emission_tone_escalation" in joined
    assert "preflight_defaults" in joined


def test_bn3_gate_context_avoids_direct_layer_meta_owner_imports() -> None:
    """BN3: gate_context routes layer-meta defaults through preflight_defaults helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN3_GATE_CONTEXT_OWNER_MODULE,
        BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE,
        collect_bn3_gate_context_layer_meta_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN3 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn3_gate_context_layer_meta_import_violations(source)
    assert not violations, "BN3 gate_context import violations:\n" + "\n".join(violations)

    defaults_path = _REPO_ROOT / BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE
    assert defaults_path.is_file(), f"missing BN3 helper: {BN3_GATE_CONTEXT_PREFLIGHT_DEFAULTS_MODULE}"

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN3" in registry_doc


def test_bn4_gate_context_preflight_telemetry_owner_entrypoint_locked() -> None:
    """BN4: preflight telemetry/containment lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_telemetry as gpft

    assert callable(getattr(gpft, "apply_gate_preflight_telemetry_and_containment", None))
    assert callable(getattr(gpft, "GatePreflightTelemetryResult", None))


def test_bn4_gate_context_preflight_telemetry_guard_detects_synthetic_violation() -> None:
    """BN4: guard flags regrown direct telemetry/provenance imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn4_gate_context_telemetry_import_violations

    synthetic = (
        "from game.stage_diff_telemetry import record_stage_snapshot\n"
        "def initialize_gate_execution_context():\n"
        "    record_stage_snapshot(out, 'final_emission_gate_entry')\n"
    )
    violations = collect_bn4_gate_context_telemetry_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "stage_diff_telemetry" in joined
    assert "preflight_telemetry" in joined


def test_bn4_gate_context_avoids_direct_telemetry_provenance_imports() -> None:
    """BN4: gate_context routes telemetry/containment through preflight_telemetry helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN3_GATE_CONTEXT_OWNER_MODULE,
        BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE,
        collect_bn4_gate_context_telemetry_import_violations,
        collect_bn4_preflight_telemetry_helper_gate_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN4 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn4_gate_context_telemetry_import_violations(source)
    assert not violations, "BN4 gate_context import violations:\n" + "\n".join(violations)

    telemetry_path = _REPO_ROOT / BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE
    assert telemetry_path.is_file(), f"missing BN4 helper: {BN4_GATE_CONTEXT_PREFLIGHT_TELEMETRY_MODULE}"
    telemetry_source = telemetry_path.read_text(encoding="utf-8")
    helper_violations = collect_bn4_preflight_telemetry_helper_gate_import_violations(telemetry_source)
    assert not helper_violations, "BN4 telemetry helper gate import violations:\n" + "\n".join(
        helper_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN4" in registry_doc


def test_bn5_gate_context_preflight_upstream_owner_entrypoint_locked() -> None:
    """BN5: preflight upstream attach lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_upstream as gpfu

    assert callable(getattr(gpfu, "apply_gate_preflight_upstream_attach", None))
    assert callable(getattr(gpfu, "upstream_prepared_emission_payload", None))


def test_bn5_gate_context_preflight_upstream_guard_detects_synthetic_violation() -> None:
    """BN5: guard flags regrown direct upstream attach imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn5_gate_context_upstream_import_violations

    synthetic = (
        "from game.upstream_response_repairs import merge_upstream_prepared_emission_into_gm_output\n"
        "def initialize_gate_execution_context():\n"
        "    merge_upstream_prepared_emission_into_gm_output(out)\n"
    )
    violations = collect_bn5_gate_context_upstream_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "upstream_response_repairs" in joined
    assert "preflight_upstream" in joined


def test_bn5_gate_context_avoids_direct_upstream_attach_imports() -> None:
    """BN5: gate_context routes upstream attach through preflight_upstream helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN3_GATE_CONTEXT_OWNER_MODULE,
        BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE,
        collect_bn5_gate_context_upstream_import_violations,
        collect_bn5_preflight_upstream_helper_gate_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN5 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn5_gate_context_upstream_import_violations(source)
    assert not violations, "BN5 gate_context import violations:\n" + "\n".join(violations)

    upstream_path = _REPO_ROOT / BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE
    assert upstream_path.is_file(), f"missing BN5 helper: {BN5_GATE_CONTEXT_PREFLIGHT_UPSTREAM_MODULE}"
    upstream_source = upstream_path.read_text(encoding="utf-8")
    helper_violations = collect_bn5_preflight_upstream_helper_gate_import_violations(upstream_source)
    assert not helper_violations, "BN5 upstream helper gate import violations:\n" + "\n".join(
        helper_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN5" in registry_doc


def test_bn6_gate_context_preflight_turn_packet_owner_entrypoint_locked() -> None:
    """BN6: preflight turn-packet/policy setup lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_turn_packet as gpfttp

    assert callable(getattr(gpfttp, "initialize_gate_preflight_turn_packet", None))


def test_bn6_gate_context_preflight_turn_packet_guard_detects_synthetic_violation() -> None:
    """BN6: guard flags regrown direct turn-packet/policy imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn6_gate_context_turn_packet_import_violations

    synthetic = (
        "from game.turn_packet import get_turn_packet\n"
        "def initialize_gate_execution_context():\n"
        "    out['_gate_turn_packet_cache'] = get_turn_packet(out)\n"
    )
    violations = collect_bn6_gate_context_turn_packet_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "turn_packet" in joined
    assert "preflight_turn_packet" in joined


def test_bn6_gate_context_avoids_direct_turn_packet_policy_imports() -> None:
    """BN6: gate_context routes turn-packet/policy setup through preflight_turn_packet helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN3_GATE_CONTEXT_OWNER_MODULE,
        BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE,
        collect_bn6_gate_context_turn_packet_import_violations,
        collect_bn6_preflight_turn_packet_helper_gate_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN6 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn6_gate_context_turn_packet_import_violations(source)
    assert not violations, "BN6 gate_context import violations:\n" + "\n".join(violations)

    turn_packet_path = _REPO_ROOT / BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE
    assert turn_packet_path.is_file(), f"missing BN6 helper: {BN6_GATE_CONTEXT_PREFLIGHT_TURN_PACKET_MODULE}"
    turn_packet_source = turn_packet_path.read_text(encoding="utf-8")
    helper_violations = collect_bn6_preflight_turn_packet_helper_gate_import_violations(turn_packet_source)
    assert not helper_violations, "BN6 turn-packet helper gate import violations:\n" + "\n".join(
        helper_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN6" in registry_doc


def test_bn7_gate_context_preflight_interaction_owner_entrypoint_locked() -> None:
    """BN7: preflight interaction metadata lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_interaction as gpfi

    assert callable(getattr(gpfi, "resolve_gate_preflight_interaction_metadata", None))
    assert callable(getattr(gpfi, "GatePreflightInteractionMetadata", None))


def test_bn7_gate_context_preflight_interaction_guard_detects_synthetic_violation() -> None:
    """BN7: guard flags regrown direct interaction inspection imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn7_gate_context_interaction_import_violations

    synthetic = (
        "from game.interaction_context import inspect as inspect_interaction_context\n"
        "def initialize_gate_execution_context():\n"
        "    return inspect_interaction_context(session)\n"
    )
    violations = collect_bn7_gate_context_interaction_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "interaction_context" in joined
    assert "preflight_interaction" in joined


def test_bn7_gate_context_avoids_direct_interaction_inspection_imports() -> None:
    """BN7: gate_context routes interaction metadata through preflight_interaction helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN3_GATE_CONTEXT_OWNER_MODULE,
        BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE,
        collect_bn7_gate_context_interaction_import_violations,
        collect_bn7_preflight_interaction_helper_gate_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN7 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn7_gate_context_interaction_import_violations(source)
    assert not violations, "BN7 gate_context import violations:\n" + "\n".join(violations)

    interaction_path = _REPO_ROOT / BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE
    assert interaction_path.is_file(), f"missing BN7 helper: {BN7_GATE_CONTEXT_PREFLIGHT_INTERACTION_MODULE}"
    interaction_source = interaction_path.read_text(encoding="utf-8")
    helper_violations = collect_bn7_preflight_interaction_helper_gate_import_violations(interaction_source)
    assert not helper_violations, "BN7 interaction helper gate import violations:\n" + "\n".join(
        helper_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN7" in registry_doc


def test_bn8_gate_context_preflight_strict_social_owner_entrypoint_locked() -> None:
    """BN8: preflight strict-social routing lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_strict_social as gpfs

    assert callable(getattr(gpfs, "resolve_gate_preflight_strict_social_routing", None))
    assert callable(getattr(gpfs, "GatePreflightStrictSocialRouting", None))


def test_bn8_gate_context_preflight_strict_social_guard_detects_synthetic_violation() -> None:
    """BN8: guard flags regrown direct strict-social routing imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn8_gate_context_strict_social_import_violations

    synthetic = (
        "from game.social_exchange_emission import strict_social_emission_will_apply\n"
        "def initialize_gate_execution_context():\n"
        "    return strict_social_emission_will_apply(None, None, None, '')\n"
    )
    violations = collect_bn8_gate_context_strict_social_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "social_exchange_emission" in joined
    assert "preflight_strict_social" in joined


def test_bn8_gate_context_avoids_direct_strict_social_routing_imports() -> None:
    """BN8: gate_context routes strict-social setup through preflight_strict_social helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN3_GATE_CONTEXT_OWNER_MODULE,
        BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE,
        collect_bn8_gate_context_strict_social_import_violations,
        collect_bn8_preflight_strict_social_helper_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN8 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn8_gate_context_strict_social_import_violations(source)
    assert not violations, "BN8 gate_context import violations:\n" + "\n".join(violations)

    strict_social_path = _REPO_ROOT / BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE
    assert strict_social_path.is_file(), f"missing BN8 helper: {BN8_GATE_CONTEXT_PREFLIGHT_STRICT_SOCIAL_MODULE}"
    strict_social_source = strict_social_path.read_text(encoding="utf-8")
    helper_violations = collect_bn8_preflight_strict_social_helper_import_violations(strict_social_source)
    assert not helper_violations, "BN8 strict-social helper import violations:\n" + "\n".join(
        helper_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN8" in registry_doc


def test_bn9_gate_context_preflight_pregate_text_owner_entrypoint_locked() -> None:
    """BN9: preflight pregate text/tag setup lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_pregate_text as gpfpt

    assert callable(getattr(gpfpt, "resolve_gate_preflight_pregate_text", None))
    assert callable(getattr(gpfpt, "GatePreflightPregateText", None))


def test_bn9_gate_context_preflight_pregate_text_guard_detects_synthetic_violation() -> None:
    """BN9: guard flags regrown direct pregate text imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn9_gate_context_pregate_text_import_violations

    synthetic = (
        "from game.final_emission_text import _normalize_text\n"
        "def initialize_gate_execution_context():\n"
        "    return _normalize_text(out.get('player_facing_text'))\n"
    )
    violations = collect_bn9_gate_context_pregate_text_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "final_emission_text" in joined
    assert "preflight_pregate_text" in joined


def test_bn9_gate_context_avoids_direct_pregate_text_imports() -> None:
    """BN9: gate_context routes pregate text/tag setup through preflight_pregate_text helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN3_GATE_CONTEXT_OWNER_MODULE,
        BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE,
        collect_bn9_gate_context_pregate_text_import_violations,
        collect_bn9_preflight_pregate_text_helper_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN9 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn9_gate_context_pregate_text_import_violations(source)
    assert not violations, "BN9 gate_context import violations:\n" + "\n".join(violations)

    pregate_text_path = _REPO_ROOT / BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE
    assert pregate_text_path.is_file(), f"missing BN9 helper: {BN9_GATE_CONTEXT_PREFLIGHT_PREGATE_TEXT_MODULE}"
    pregate_text_source = pregate_text_path.read_text(encoding="utf-8")
    helper_violations = collect_bn9_preflight_pregate_text_helper_import_violations(pregate_text_source)
    assert not helper_violations, "BN9 pregate text helper import violations:\n" + "\n".join(
        helper_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN9" in registry_doc


def test_bn10_gate_context_preflight_branch_flags_owner_entrypoint_locked() -> None:
    """BN10: preflight branch-flag derivation lives on dedicated helper owner."""
    import game.final_emission_gate_preflight_branch_flags as gpfb

    assert callable(getattr(gpfb, "resolve_gate_preflight_branch_flags", None))
    assert callable(getattr(gpfb, "GatePreflightBranchFlags", None))


def test_bn10_gate_context_preflight_branch_flags_guard_detects_synthetic_violation() -> None:
    """BN10: guard flags inline branch-flag derivation regrown on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import collect_bn10_gate_context_branch_flags_violations

    synthetic = (
        "def initialize_gate_execution_context():\n"
        "    retry_output = any('question_retry_fallback' in t for t in tag_list)\n"
    )
    violations = collect_bn10_gate_context_branch_flags_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "question_retry_fallback" in joined
    assert "preflight_branch_flags" in joined


def test_bn10_gate_context_routes_branch_flags_through_helper() -> None:
    """BN10: gate_context routes branch flags through preflight_branch_flags helper."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE,
        BN3_GATE_CONTEXT_OWNER_MODULE,
        collect_bn10_gate_context_branch_flags_violations,
        collect_bn10_preflight_branch_flags_helper_import_violations,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN10 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn10_gate_context_branch_flags_violations(source)
    assert not violations, "BN10 gate_context branch-flag violations:\n" + "\n".join(violations)

    branch_flags_path = _REPO_ROOT / BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE
    assert branch_flags_path.is_file(), f"missing BN10 helper: {BN10_GATE_CONTEXT_PREFLIGHT_BRANCH_FLAGS_MODULE}"
    branch_flags_source = branch_flags_path.read_text(encoding="utf-8")
    helper_violations = collect_bn10_preflight_branch_flags_helper_import_violations(branch_flags_source)
    assert not helper_violations, "BN10 branch-flags helper import violations:\n" + "\n".join(
        helper_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN10" in registry_doc


def test_bn11_gate_context_preflight_only_import_guard_detects_synthetic_violation() -> None:
    """BN11: guard flags non-preflight game imports on gate_context."""
    from tests.helpers.gate_thin_boundary_locks import (
        collect_bn11_gate_context_preflight_only_import_violations,
    )

    synthetic = (
        "from game.final_emission_gate import apply_final_emission_gate\n"
        "from game.final_emission_gate_preflight_defaults import initialize_gate_preflight_layer_meta_defaults\n"
        "def initialize_gate_execution_context():\n"
        "    return apply_final_emission_gate({})\n"
    )
    violations = collect_bn11_gate_context_preflight_only_import_violations(synthetic)
    joined = "\n".join(violations)
    assert violations
    assert "final_emission_gate" in joined
    assert "preflight" in joined


def test_bn11_gate_context_preflight_only_import_allowlist_locked() -> None:
    """BN11: live gate_context imports only stdlib/typing and preflight helper owners."""
    from tests.helpers.gate_thin_boundary_locks import (
        BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES,
        BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS,
        BN3_GATE_CONTEXT_OWNER_MODULE,
        collect_bn11_gate_context_preflight_only_import_violations,
        collect_bn11_scan_logic_runtime_gate_import_violations,
        gate_context_import_modules,
    )

    path = _REPO_ROOT / BN3_GATE_CONTEXT_OWNER_MODULE
    assert path.is_file(), f"missing BN11 scan path: {BN3_GATE_CONTEXT_OWNER_MODULE}"
    source = path.read_text(encoding="utf-8")
    violations = collect_bn11_gate_context_preflight_only_import_violations(source)
    assert not violations, "BN11 gate_context preflight-only import violations:\n" + "\n".join(
        violations
    )

    imported_game = {
        mod for mod in gate_context_import_modules(source) if mod.startswith("game.")
    }
    assert imported_game == BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES, (
        "BN11 gate_context game import set mismatch:\n"
        f"  imported: {sorted(imported_game)!r}\n"
        f"  allowed:  {sorted(BN11_GATE_CONTEXT_ALLOWED_GAME_IMPORT_MODULES)!r}"
    )

    for required in BN11_GATE_CONTEXT_REQUIRED_PREFLIGHT_IMPORTS:
        assert required in source, f"missing BN11 required preflight import: {required!r}"

    lock_path = _REPO_ROOT / "tests/helpers/gate_thin_boundary_locks.py"
    lock_source = lock_path.read_text(encoding="utf-8")
    scan_violations = collect_bn11_scan_logic_runtime_gate_import_violations(lock_source)
    assert not scan_violations, "BN11 scan-logic runtime gate import violations:\n" + "\n".join(
        scan_violations
    )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BN11" in registry_doc


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
    manifest_buckets = dict(acceptance_projection.protected_observation_manifest_field_rows())
    assert manifest_buckets == {
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


def test_bj27_referential_clarity_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-27/BJ-50: referential-clarity orchestration lives on visibility fallback owner."""
    import game.final_emission_visibility_fallback as visibility_fallback

    assert callable(getattr(visibility_fallback, "apply_referential_clarity_enforcement", None))


def test_bj50_visibility_enforcement_gate_wrapper_collapsed() -> None:
    """Cycle BJ-50/BJ-73: visibility enforcement lives on final_emission_visibility_fallback owner."""
    import game.final_emission_gate as feg
    import game.final_emission_visibility_fallback as visibility_fallback

    assert not hasattr(feg, "_apply_visibility_enforcement")
    assert not hasattr(feg, "_standard_visibility_safe_fallback")
    assert not hasattr(feg, "_apply_first_mention_enforcement")
    assert not hasattr(feg, "_apply_referential_clarity_enforcement")
    assert callable(getattr(visibility_fallback, "apply_visibility_enforcement", None))
    assert callable(getattr(visibility_fallback, "apply_first_mention_enforcement", None))
    assert callable(getattr(visibility_fallback, "apply_referential_clarity_enforcement", None))
    assert callable(getattr(visibility_fallback, "standard_visibility_safe_fallback", None))


def test_bj73_ownership_registry_terminal_pipeline_calls_visibility_owner_directly() -> None:
    """Cycle BJ-73: terminal pipeline calls visibility_fallback owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp
    import game.final_emission_visibility_fallback as visibility_fallback

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "apply_visibility_enforcement(" in tp_src
    assert "feg._apply_visibility_enforcement" not in tp_src
    assert not hasattr(feg, "_apply_visibility_enforcement")
    assert callable(getattr(visibility_fallback, "apply_visibility_enforcement", None))


def test_bj28_speaker_contract_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-28/BJ-77/BJ-78: speaker-contract orchestration lives on speaker_contract_enforcement owner."""
    import game.final_emission_gate as feg
    import game.speaker_contract_enforcement as sce

    assert callable(getattr(sce, "enforce_emitted_speaker_with_contract", None))
    assert callable(getattr(sce, "_sync_eff_social_to_resolution", None))
    assert not hasattr(feg, "enforce_emitted_speaker_with_contract")
    assert not hasattr(feg, "_sync_eff_social_to_resolution")
    assert feg.get_speaker_selection_contract is sce.get_speaker_selection_contract


def test_bj29_interaction_continuity_emission_owner_entrypoint_locked() -> None:
    """Cycle BJ-29/BJ-51/BJ-75/BJ-76: interaction-continuity orchestration lives on interaction_continuity owner."""
    import game.final_emission_gate as feg
    import game.interaction_continuity as ic

    assert callable(getattr(ic, "apply_interaction_continuity_emission_step", None))
    assert callable(getattr(ic, "attach_interaction_continuity_validation", None))
    assert not hasattr(feg, "_apply_interaction_continuity_emission_step")
    assert feg.apply_interaction_continuity_emission_step is ic.apply_interaction_continuity_emission_step
    assert feg.attach_interaction_continuity_validation is ic.attach_interaction_continuity_validation


def test_bj51_interaction_continuity_gate_wrappers_fully_collapsed() -> None:
    """Cycle BJ-51/BJ-75/BJ-76: all IC gate delegators removed; owners called from stack modules."""
    import game.final_emission_gate as feg
    import game.interaction_continuity as ic

    assert not hasattr(feg, "_apply_interaction_continuity_emission_step")
    assert not hasattr(feg, "_attach_interaction_continuity_validation")
    assert callable(getattr(ic, "apply_interaction_continuity_emission_step", None))
    assert callable(getattr(ic, "attach_interaction_continuity_validation", None))


def test_bj52_fallback_provenance_gate_wrappers_collapsed() -> None:
    """Cycle BJ-52/BN4: upstream fallback provenance containment wrappers removed from gate."""
    import game.fallback_provenance_debug as fpd
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    import game.final_emission_gate_context as gc
    import game.final_emission_gate_preflight_telemetry as gpft

    assert not hasattr(feg, "_upstream_fallback_canonical_provenance")
    assert not hasattr(feg, "_apply_upstream_fallback_pregate_containment")
    assert not hasattr(feg, "_finalize_upstream_fallback_overwrite_containment")
    assert callable(getattr(fpd, "upstream_fallback_canonical_provenance", None))
    assert callable(getattr(fpd, "apply_upstream_fallback_pregate_containment", None))
    assert callable(getattr(fpd, "finalize_upstream_fallback_overwrite_containment", None))
    assert not hasattr(gc, "apply_upstream_fallback_pregate_containment")
    assert callable(getattr(gpft, "apply_gate_preflight_telemetry_and_containment", None))
    assert callable(getattr(fin, "finalize_upstream_fallback_overwrite_containment", None))


def test_bj53_referent_clarity_pre_finalize_gate_wrapper_collapsed() -> None:
    """Cycle BJ-53: referent pre-finalize wrapper removed from gate; terminal pipeline owns the hook."""
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp

    assert not hasattr(feg, "_apply_referent_clarity_pre_finalize")
    assert callable(getattr(tp, "_apply_referent_clarity_pre_finalize", None))


def test_bj54_narration_constraint_debug_merge_gate_wrapper_collapsed() -> None:
    """Cycle BJ-54: narration-constraint debug merge wrapper removed from gate; terminal pipeline owns merge."""
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp

    assert not hasattr(feg, "_merge_narration_constraint_debug_into_outputs")
    assert callable(getattr(tp, "_merge_narration_constraint_debug_into_outputs", None))


def test_bj55_gate_fem_text_fingerprint_helper_collapsed() -> None:
    """Cycle BJ-55: dead gate FEM fingerprint helper removed; terminal pipeline owns fingerprint patch."""
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp

    assert not hasattr(feg, "_patch_gate_fem_text_fingerprint")
    assert callable(getattr(tp, "_patch_fem_text_fingerprint", None))


def test_bj56_scene_opening_finalize_delegators_collapsed() -> None:
    """Cycle BJ-56: scene-opening finalize wrappers removed from gate; finalize owner owns hooks."""
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg

    assert not hasattr(feg, "_patch_scene_opening_candidate_emission_debug")
    assert not hasattr(feg, "_reassert_scene_opening_accepted_candidate")
    assert callable(getattr(fin, "patch_scene_opening_candidate_emission_debug", None))
    assert callable(getattr(fin, "reassert_scene_opening_accepted_candidate", None))


def test_bj57_strip_appended_route_illegal_contamination_sentences_gate_wrapper_collapsed() -> None:
    """Cycle BJ-57: route-illegal strip wrapper removed from gate; finalize owner owns strip helper."""
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg

    assert not hasattr(feg, "_strip_appended_route_illegal_contamination_sentences")
    assert callable(getattr(fin, "strip_appended_route_illegal_contamination_sentences", None))


def test_bj30_dialogue_social_plan_strict_social_enforcement_owner_entrypoint_locked() -> None:
    """Cycle BJ-30: strict-social dialogue plan enforcement lives on dialogue_social_plan owner."""
    import game.dialogue_social_plan as dsp

    assert callable(getattr(dsp, "enforce_dialogue_plan_invariant_on_strict_social", None))
    assert callable(getattr(dsp, "strip_dialogue_from_text", None))
    assert callable(getattr(dsp, "strict_social_line_matches_terminal_emission_pool", None))
    assert callable(getattr(dsp, "is_bare_speech_attribution_shell_line", None))


def test_bj59_dialogue_social_plan_gate_delegators_collapsed() -> None:
    """Cycle BJ-59: dialogue-plan helpers removed from gate; strict-social stack calls owner directly."""
    import game.dialogue_social_plan as dsp
    import game.final_emission_gate as feg

    assert not hasattr(feg, "_enforce_dialogue_plan_invariant_on_strict_social")
    assert not hasattr(feg, "_strip_dialogue_from_text")
    assert not hasattr(feg, "_strict_social_line_matches_terminal_emission_pool")
    assert not hasattr(feg, "_is_bare_speech_attribution_shell_line")
    assert callable(getattr(dsp, "enforce_dialogue_plan_invariant_on_strict_social", None))
    assert callable(getattr(dsp, "strip_dialogue_from_text", None))


def test_bj60_sealed_fallback_selector_gate_delegator_collapsed() -> None:
    """Cycle BJ-60: non-strict sealed selector wrapper removed from gate; owner resolves opening provider."""
    import game.final_emission_gate as feg
    import game.final_emission_sealed_fallback as sf

    assert not hasattr(feg, "_select_non_strict_replace_path_terminal_sealed_fallback_selection")
    assert callable(getattr(sf, "select_non_strict_replace_path_terminal_sealed_fallback_selection", None))


def test_bj61_sealed_fallback_stamp_gate_delegators_collapsed() -> None:
    """Cycle BJ-61: sealed FEM stamp/route-meta import aliases removed from gate; generic_exit calls owner."""
    import game.final_emission_gate as feg
    import game.final_emission_sealed_fallback as sf

    for name in (
        "_stamp_sealed_fallback_realization_family",
        "_stamp_non_strict_sealed_replacement_realization_family",
        "_prepare_sealed_replacement_route_meta",
    ):
        assert not hasattr(feg, name), name
    for name in (
        "stamp_sealed_fallback_realization_family",
        "stamp_non_strict_sealed_replacement_realization_family",
        "prepare_sealed_replacement_route_meta",
    ):
        assert callable(getattr(sf, name, None)), name


def test_bj62_generic_exit_fem_assembly_calls_owner_directly() -> None:
    """Cycle BJ-62: generic exit calls FEM assembly owner directly."""
    import inspect

    import game.final_emission_fem_assembly as fa
    import game.final_emission_generic_exit as ge

    accept_src = inspect.getsource(ge.run_generic_accept_exit)
    replace_src = inspect.getsource(ge.run_generic_replace_exit)
    assert "fem_assembly.build_gate_accept_fem_base" in accept_src
    assert "fem_assembly.merge_gate_layer_metas_into_fem" in accept_src
    assert "_build_gate_accept_fem_base" not in accept_src
    assert "_merge_gate_layer_metas_into_fem" not in accept_src
    assert "fem_assembly.build_gate_replace_fem_base" in replace_src
    assert "fem_assembly.merge_gate_layer_metas_into_fem" in replace_src
    assert "_build_gate_replace_fem_base" not in replace_src
    assert "_merge_gate_layer_metas_into_fem" not in replace_src
    assert callable(getattr(fa, "build_gate_accept_fem_base", None))
    assert callable(getattr(fa, "build_gate_replace_fem_base", None))
    assert callable(getattr(fa, "merge_gate_layer_metas_into_fem", None))


def test_bj63_strict_social_stack_fem_assembly_calls_owner_directly() -> None:
    """Cycle BJ-63: strict-social stack calls FEM assembly owner; gate FEM delegators removed."""
    import inspect

    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss

    src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "fem_assembly.build_gate_accept_fem_base" in src
    assert "fem_assembly.build_gate_replace_fem_base" in src
    assert src.count("fem_assembly.merge_gate_layer_metas_into_fem") == 2
    assert "_build_gate_accept_fem_base" not in src
    assert "_build_gate_replace_fem_base" not in src
    assert "_merge_gate_layer_metas_into_fem" not in src
    for name in (
        "_build_gate_accept_fem_base",
        "_build_gate_replace_fem_base",
        "_merge_gate_layer_metas_into_fem",
    ):
        assert not hasattr(feg, name), name
    assert callable(getattr(fa, "build_gate_accept_fem_base", None))
    assert callable(getattr(fa, "build_gate_replace_fem_base", None))
    assert callable(getattr(fa, "merge_gate_layer_metas_into_fem", None))


def test_bj64_non_strict_stack_opening_rt_promotion_calls_owner_directly() -> None:
    """Cycle BJ-64: non-strict stack calls opening RT promotion owner; gate alias removed."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_opening_fallback as ob

    src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert "opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate" in src
    assert "_scene_opening_rt_contract_accept_path_promotes_candidate" not in src
    assert not hasattr(feg, "_scene_opening_rt_contract_accept_path_promotes_candidate")
    assert callable(getattr(ob, "scene_opening_rt_contract_accept_path_promotes_candidate", None))


def test_bj65_stacks_opening_upstream_prepare_observability_merge_calls_owner_directly() -> None:
    """Cycle BJ-65: stacks call response_type owner for opening upstream-prepare observability merge."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_response_type as rt
    import game.final_emission_strict_social_stack as ss

    marker = "response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug"
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in nss_src
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in ss_src
    assert not hasattr(feg, "_merge_opening_upstream_prepare_attach_observability_into_response_type_debug")
    assert callable(
        getattr(rt, "_merge_opening_upstream_prepare_attach_observability_into_response_type_debug", None)
    )


def test_bj31_tone_escalation_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-31/BJ-79: tone escalation layer lives on final_emission_tone_escalation owner."""
    import game.final_emission_gate as feg
    import game.final_emission_tone_escalation as te

    assert callable(getattr(te, "apply_tone_escalation_layer", None))
    assert callable(getattr(te, "resolve_tone_escalation_contract", None))
    assert not hasattr(feg, "_apply_tone_escalation_layer")


def test_bj79_ownership_registry_stacks_call_tone_escalation_owner_directly() -> None:
    """Cycle BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_tone_escalation as te

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_tone_escalation_layer(" in nss_src
    assert "apply_tone_escalation_layer(" in ss_src
    assert "feg._apply_tone_escalation_layer" not in nss_src
    assert "feg._apply_tone_escalation_layer" not in ss_src
    assert not hasattr(feg, "_apply_tone_escalation_layer")
    assert callable(getattr(te, "apply_tone_escalation_layer", None))


def test_bj32_narrative_authority_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-32/BJ-80: narrative authority layer lives on final_emission_narrative_authority owner."""
    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as na

    assert callable(getattr(na, "apply_narrative_authority_layer", None))
    assert callable(getattr(na, "resolve_narrative_authority_contract", None))
    assert not hasattr(feg, "_apply_narrative_authority_layer")


def test_bj80_ownership_registry_stacks_call_narrative_authority_owner_directly() -> None:
    """Cycle BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as na
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_narrative_authority_layer(" in nss_src
    assert "apply_narrative_authority_layer(" in ss_src
    assert "feg._apply_narrative_authority_layer" not in nss_src
    assert "feg._apply_narrative_authority_layer" not in ss_src
    assert not hasattr(feg, "_apply_narrative_authority_layer")
    assert callable(getattr(na, "apply_narrative_authority_layer", None))


def test_bj58_contract_resolver_gate_delegators_collapsed() -> None:
    """Cycle BJ-58: contract resolver wrappers removed from gate; tone/authority owners resolve directly."""
    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as na
    import game.final_emission_tone_escalation as te

    assert not hasattr(feg, "_resolve_tone_escalation_contract")
    assert not hasattr(feg, "_resolve_narrative_authority_contract")
    assert callable(getattr(te, "resolve_tone_escalation_contract", None))
    assert callable(getattr(na, "resolve_narrative_authority_contract", None))


def test_bj33_anti_railroading_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-33/BJ-81: anti-railroading layer lives on final_emission_anti_railroading owner."""
    import game.final_emission_anti_railroading as ar
    import game.final_emission_gate as feg

    assert callable(getattr(ar, "apply_anti_railroading_layer", None))
    assert callable(getattr(ar, "resolve_anti_railroading_contract", None))
    assert not hasattr(feg, "_apply_anti_railroading_layer")


def test_bj81_ownership_registry_stacks_call_anti_railroading_owner_directly() -> None:
    """Cycle BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    import inspect

    import game.final_emission_anti_railroading as ar
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_anti_railroading_layer(" in nss_src
    assert "apply_anti_railroading_layer(" in ss_src
    assert "feg._apply_anti_railroading_layer" not in nss_src
    assert "feg._apply_anti_railroading_layer" not in ss_src
    assert not hasattr(feg, "_apply_anti_railroading_layer")
    assert callable(getattr(ar, "apply_anti_railroading_layer", None))


def test_bj34_context_separation_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-34/BJ-82: context separation layer lives on final_emission_context_separation owner."""
    import game.final_emission_context_separation as cs
    import game.final_emission_gate as feg

    assert callable(getattr(cs, "apply_context_separation_layer", None))
    assert callable(getattr(cs, "resolve_context_separation_contract", None))
    assert not hasattr(feg, "_apply_context_separation_layer")


def test_bj82_ownership_registry_stacks_call_context_separation_owner_directly() -> None:
    """Cycle BJ-82: strict and non-strict stacks call context_separation owner directly."""
    import inspect

    import game.final_emission_context_separation as cs
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_context_separation_layer(" in nss_src
    assert "apply_context_separation_layer(" in ss_src
    assert "feg._apply_context_separation_layer" not in nss_src
    assert "feg._apply_context_separation_layer" not in ss_src
    assert not hasattr(feg, "_apply_context_separation_layer")
    assert callable(getattr(cs, "apply_context_separation_layer", None))


def test_bj35_player_facing_narration_purity_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-35/BJ-83: narration purity layer lives on final_emission_player_facing_narration_purity owner."""
    import game.final_emission_gate as feg
    import game.final_emission_player_facing_narration_purity as pfp

    assert callable(getattr(pfp, "apply_player_facing_narration_purity_layer", None))
    assert callable(getattr(pfp, "resolve_player_facing_narration_purity_contract", None))
    assert not hasattr(feg, "_apply_player_facing_narration_purity_layer")


def test_bj83_ownership_registry_stacks_call_narration_purity_owner_directly() -> None:
    """Cycle BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_player_facing_narration_purity as pfp
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_player_facing_narration_purity_layer(" in nss_src
    assert "apply_player_facing_narration_purity_layer(" in ss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in nss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in ss_src
    assert not hasattr(feg, "_apply_player_facing_narration_purity_layer")
    assert callable(getattr(pfp, "apply_player_facing_narration_purity_layer", None))


def test_bj36_answer_shape_primacy_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-36/BJ-84: answer-shape primacy layer lives on final_emission_answer_shape_primacy owner."""
    import game.final_emission_answer_shape_primacy as asp
    import game.final_emission_gate as feg

    assert callable(getattr(asp, "apply_answer_shape_primacy_layer", None))
    assert callable(getattr(asp, "validate_answer_shape_primacy", None))
    assert not hasattr(feg, "_apply_answer_shape_primacy_layer")


def test_bj84_ownership_registry_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """Cycle BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    import inspect

    import game.final_emission_answer_shape_primacy as asp
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_answer_shape_primacy_layer(" in nss_src
    assert "apply_answer_shape_primacy_layer(" in ss_src
    assert "feg._apply_answer_shape_primacy_layer" not in nss_src
    assert "feg._apply_answer_shape_primacy_layer" not in ss_src
    assert not hasattr(feg, "_apply_answer_shape_primacy_layer")
    assert callable(getattr(asp, "apply_answer_shape_primacy_layer", None))


def test_bj37_scene_state_anchor_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-37/BJ-85: scene state anchor apply layer lives on final_emission_scene_state_anchor owner."""
    import game.final_emission_gate as feg
    import game.final_emission_scene_state_anchor as ssa

    assert callable(getattr(ssa, "apply_scene_state_anchor_layer", None))
    assert not hasattr(feg, "_apply_scene_state_anchor_layer")


def test_bj85_ownership_registry_stacks_call_scene_state_anchor_owner_directly() -> None:
    """Cycle BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_scene_state_anchor as ssa
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_scene_state_anchor_layer(" in nss_src
    assert "apply_scene_state_anchor_layer(" in ss_src
    assert "feg._apply_scene_state_anchor_layer" not in nss_src
    assert "feg._apply_scene_state_anchor_layer" not in ss_src
    assert not hasattr(feg, "_apply_scene_state_anchor_layer")
    assert callable(getattr(ssa, "apply_scene_state_anchor_layer", None))


def test_bj42_terminal_enforcement_pipeline_owner_entrypoint_locked() -> None:
    """Cycle BJ-42/BJ-69: terminal enforcement pipeline lives on final_emission_terminal_pipeline owner."""
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp

    assert callable(getattr(tp, "run_gate_terminal_enforcement_pipeline", None))
    assert not hasattr(feg, "_run_gate_terminal_enforcement_pipeline")


def test_bj43_non_strict_layer_stack_owner_entrypoint_locked() -> None:
    """Cycle BJ-43/BJ-71: non-strict pre-fork layer stack lives on final_emission_non_strict_stack owner."""
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss

    assert callable(getattr(nss, "run_non_strict_layer_stack", None))
    assert not hasattr(feg, "_run_non_strict_layer_stack")


def test_bj71_ownership_registry_apply_gate_calls_non_strict_stack_owner_directly() -> None:
    """Cycle BJ-71: apply_final_emission_gate calls non_strict_stack owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss

    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_non_strict_layer_stack(" in gate_src
    assert "_run_non_strict_layer_stack" not in gate_src
    assert not hasattr(feg, "_run_non_strict_layer_stack")
    assert callable(getattr(nss, "run_non_strict_layer_stack", None))


def test_bj44_strict_social_composition_trunk_owner_entrypoint_locked() -> None:
    """Cycle BJ-44/BJ-70: strict-social composition trunk lives on final_emission_strict_social_stack owner."""
    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as sss

    assert callable(getattr(sss, "run_strict_social_composition_trunk", None))
    assert not hasattr(feg, "_run_strict_social_composition_trunk")


def test_bj70_ownership_registry_apply_gate_calls_exit_stack_owners_directly() -> None:
    """Cycle BJ-70: apply_final_emission_gate calls generic/strict-social exit owners directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as ge
    import game.final_emission_strict_social_stack as ss

    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_strict_social_composition_trunk(" in gate_src
    assert "run_generic_accept_exit(" in gate_src
    assert "run_generic_replace_exit(" in gate_src
    assert "_run_strict_social_composition_trunk" not in gate_src
    assert "_run_generic_accept_exit" not in gate_src
    assert "_run_generic_replace_exit" not in gate_src
    for name in (
        "_run_strict_social_composition_trunk",
        "_run_generic_accept_exit",
        "_run_generic_replace_exit",
    ):
        assert not hasattr(feg, name), name
    assert callable(getattr(ss, "run_strict_social_composition_trunk", None))
    assert callable(getattr(ge, "run_generic_accept_exit", None))
    assert callable(getattr(ge, "run_generic_replace_exit", None))


def test_bj69_ownership_registry_exit_stacks_call_terminal_finalize_owners_directly() -> None:
    """Cycle BJ-69: exit stacks call terminal pipeline and finalize owners directly."""
    import inspect

    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as ge
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_terminal_pipeline as tp

    ge_accept_src = inspect.getsource(ge.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(ge.run_generic_replace_exit)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    for src in (ge_accept_src, ge_replace_src, ss_src):
        assert "terminal_pipeline.run_gate_terminal_enforcement_pipeline" in src
        assert "emission_finalize.finalize_emission_output" in src
        assert "emission_finalize.final_emission_fast_path_eligible" in src
        assert "feg._run_gate_terminal_enforcement_pipeline" not in src
        assert "feg._finalize_emission_output" not in src
        assert "feg._final_emission_fast_path_eligible" not in src
    for name in (
        "_run_gate_terminal_enforcement_pipeline",
        "_finalize_emission_output",
        "_final_emission_fast_path_eligible",
    ):
        assert not hasattr(feg, name), name
    assert callable(getattr(tp, "run_gate_terminal_enforcement_pipeline", None))
    assert callable(getattr(fin, "finalize_emission_output", None))
    assert callable(getattr(fin, "final_emission_fast_path_eligible", None))


def test_bj45_generic_exit_owner_entrypoints_locked() -> None:
    """Cycle BJ-45/BJ-70: generic accept/replace exits live on final_emission_generic_exit owner."""
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as ge

    assert callable(getattr(ge, "run_generic_accept_exit", None))
    assert callable(getattr(ge, "run_generic_replace_exit", None))
    assert not hasattr(feg, "_run_generic_accept_exit")
    assert not hasattr(feg, "_run_generic_replace_exit")


def test_bj46_fem_assembly_owner_entrypoints_locked() -> None:
    """Cycle BJ-46/BJ-63: FEM accept/replace base assembly lives on final_emission_fem_assembly owner."""
    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg

    assert callable(getattr(fa, "build_gate_accept_fem_base", None))
    assert callable(getattr(fa, "build_gate_replace_fem_base", None))
    assert not hasattr(feg, "_build_gate_accept_fem_base")
    assert not hasattr(feg, "_build_gate_replace_fem_base")


def test_bj47_fem_assembly_merge_gate_layer_metas_owner_entrypoint_locked() -> None:
    """Cycle BJ-47/BJ-63: FEM layer-meta merge lives on final_emission_fem_assembly owner."""
    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg

    assert callable(getattr(fa, "merge_gate_layer_metas_into_fem", None))
    assert not hasattr(feg, "_merge_gate_layer_metas_into_fem")


def test_bj48_fast_fallback_neutral_composition_layer_owner_entrypoint_locked() -> None:
    """Cycle BJ-48/BJ-86: FFNC layer apply/default-meta live on final_emission_fast_fallback_composition owner."""
    import game.final_emission_fast_fallback_composition as ffnc
    import game.final_emission_gate as feg

    assert callable(getattr(ffnc, "default_fast_fallback_neutral_composition_meta", None))
    assert callable(getattr(ffnc, "apply_fast_fallback_neutral_composition_layer", None))
    assert not hasattr(feg, "_apply_fast_fallback_neutral_composition_layer")


def test_bj86_ownership_registry_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """Cycle BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    import inspect

    import game.final_emission_fast_fallback_composition as ffnc
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "apply_fast_fallback_neutral_composition_layer(" in nss_src
    assert "apply_fast_fallback_neutral_composition_layer(" in ss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in nss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in ss_src
    assert not hasattr(feg, "_apply_fast_fallback_neutral_composition_layer")
    assert callable(getattr(ffnc, "apply_fast_fallback_neutral_composition_layer", None))


def test_bj87_ownership_registry_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """Cycle BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_answer_completeness_layer(" in nss_src
    assert "feg._apply_answer_completeness_layer" not in nss_src
    assert "emission_repairs._apply_answer_completeness_layer(" in ss_src
    assert "feg._apply_answer_completeness_layer" not in ss_src
    assert not hasattr(feg, "_apply_answer_completeness_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_completeness_layer", None))


def test_bj88_ownership_registry_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """Cycle BJ-88: stacks call final_emission_repairs answer exposition plan directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss)
    assert "_apply_answer_exposition_plan_layer(" in nss_src
    assert "feg._apply_answer_exposition_plan_layer" not in nss_src
    assert ss_src.count("emission_repairs._apply_answer_exposition_plan_layer(") == 3
    assert "feg._apply_answer_exposition_plan_layer" not in ss_src
    assert not hasattr(feg, "_apply_answer_exposition_plan_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_exposition_plan_layer", None))


def test_bj89_ownership_registry_stacks_call_response_delta_repairs_owner_directly() -> None:
    """Cycle BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_response_delta_layer(" in nss_src
    assert "feg._apply_response_delta_layer" not in nss_src
    assert "emission_repairs._apply_response_delta_layer(" in ss_src
    assert "feg._apply_response_delta_layer" not in ss_src
    assert not hasattr(feg, "_apply_response_delta_layer")
    assert callable(getattr(emission_repairs, "_apply_response_delta_layer", None))


def test_bj90_ownership_registry_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """Cycle BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_social_response_structure_layer(" in nss_src
    assert "feg._apply_social_response_structure_layer" not in nss_src
    assert "emission_repairs._apply_social_response_structure_layer(" in ss_src
    assert "feg._apply_social_response_structure_layer" not in ss_src
    assert not hasattr(feg, "_apply_social_response_structure_layer")
    assert callable(getattr(emission_repairs, "_apply_social_response_structure_layer", None))


def test_bj91_ownership_registry_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """Cycle BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_apply_narrative_authenticity_layer(" in nss_src
    assert "feg._apply_narrative_authenticity_layer" not in nss_src
    assert "emission_repairs._apply_narrative_authenticity_layer(" in ss_src
    assert "feg._apply_narrative_authenticity_layer" not in ss_src
    assert not hasattr(feg, "_apply_narrative_authenticity_layer")
    assert callable(getattr(emission_repairs, "_apply_narrative_authenticity_layer", None))


def test_bj92_ownership_registry_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """Cycle BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "_apply_fallback_behavior_layer(" in nss_src
    assert "feg._apply_fallback_behavior_layer" not in nss_src
    assert "_apply_fallback_behavior_layer(" in tp_src
    assert "feg._apply_fallback_behavior_layer" not in tp_src
    assert not hasattr(feg, "_apply_fallback_behavior_layer")
    assert callable(getattr(emission_repairs, "_apply_fallback_behavior_layer", None))


def test_bj93_ownership_registry_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """Cycle BJ-93: stacks call final_emission_repairs fallback debug/meta merge helpers directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "merge_fallback_behavior_into_emission_debug(" in nss_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in nss_src
    assert "merge_fallback_behavior_into_emission_debug(" in tp_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in tp_src
    assert "_merge_fallback_behavior_meta(" in tp_src
    assert "feg._merge_fallback_behavior_meta" not in tp_src
    assert not hasattr(feg, "_merge_fallback_behavior_into_emission_debug")
    assert not hasattr(feg, "_merge_fallback_behavior_meta")
    assert callable(getattr(emission_repairs, "merge_fallback_behavior_into_emission_debug", None))
    assert callable(getattr(emission_repairs, "_merge_fallback_behavior_meta", None))


def test_bj94_ownership_registry_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """Cycle BJ-94: strict and non-strict stacks call repairs conversational memory debug merge directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_repairs as emission_repairs
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "merge_conversational_memory_inspection_into_emission_debug(" in nss_src
    assert "feg._merge_conversational_memory_inspection_into_emission_debug" not in nss_src
    assert "emission_repairs.merge_conversational_memory_inspection_into_emission_debug(" in ss_src
    assert "feg._merge_conversational_memory_inspection_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_conversational_memory_inspection_into_emission_debug")
    assert callable(
        getattr(emission_repairs, "merge_conversational_memory_inspection_into_emission_debug", None)
    )


def test_bj95_ownership_registry_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """Cycle BJ-95: strict and non-strict stacks call scene_state_anchor emission_debug merge directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_scene_state_anchor as scene_state_anchor
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_merge_scene_state_anchor_into_emission_debug(" in nss_src
    assert "feg._merge_scene_state_anchor_into_emission_debug" not in nss_src
    assert "_merge_scene_state_anchor_into_emission_debug(" in ss_src
    assert "feg._merge_scene_state_anchor_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_scene_state_anchor_into_emission_debug")
    assert callable(getattr(scene_state_anchor, "_merge_scene_state_anchor_into_emission_debug", None))


def test_bj96_ownership_registry_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """Cycle BJ-96: strict and non-strict stacks call tone_escalation emission_debug merge directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_tone_escalation as tone_escalation

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_merge_tone_escalation_into_emission_debug(" in nss_src
    assert "feg._merge_tone_escalation_into_emission_debug" not in nss_src
    assert "_merge_tone_escalation_into_emission_debug(" in ss_src
    assert "feg._merge_tone_escalation_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_tone_escalation_into_emission_debug")
    assert callable(getattr(tone_escalation, "merge_tone_escalation_into_emission_debug", None))


def test_bj97_ownership_registry_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """Cycle BJ-97: strict and non-strict stacks call narrative_authority emission_debug merge directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_narrative_authority as narrative_authority
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_merge_narrative_authority_into_emission_debug(" in nss_src
    assert "feg._merge_narrative_authority_into_emission_debug" not in nss_src
    assert "_merge_narrative_authority_into_emission_debug(" in ss_src
    assert "feg._merge_narrative_authority_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_narrative_authority_into_emission_debug")
    assert callable(getattr(narrative_authority, "merge_narrative_authority_into_emission_debug", None))


def test_bj98_ownership_registry_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """Cycle BJ-98: strict and non-strict stacks call anti_railroading emission_debug merge directly."""
    import inspect

    import game.final_emission_anti_railroading as anti_railroading
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_merge_anti_railroading_into_emission_debug(" in nss_src
    assert "feg._merge_anti_railroading_into_emission_debug" not in nss_src
    assert "_merge_anti_railroading_into_emission_debug(" in ss_src
    assert "feg._merge_anti_railroading_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_anti_railroading_into_emission_debug")
    assert callable(getattr(anti_railroading, "merge_anti_railroading_into_emission_debug", None))


def test_bj99_ownership_registry_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """Cycle BJ-99: strict and non-strict stacks call context_separation emission_debug merge directly."""
    import inspect

    import game.final_emission_context_separation as context_separation
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_merge_context_separation_into_emission_debug(" in nss_src
    assert "feg._merge_context_separation_into_emission_debug" not in nss_src
    assert "_merge_context_separation_into_emission_debug(" in ss_src
    assert "feg._merge_context_separation_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_context_separation_into_emission_debug")
    assert callable(getattr(context_separation, "merge_context_separation_into_emission_debug", None))


def test_bj100_ownership_registry_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """Cycle BJ-100: strict and non-strict stacks call narration_purity emission_debug merge directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_player_facing_narration_purity as narration_purity
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_merge_player_facing_narration_purity_into_emission_debug(" in nss_src
    assert "feg._merge_player_facing_narration_purity_into_emission_debug" not in nss_src
    assert "_merge_player_facing_narration_purity_into_emission_debug(" in ss_src
    assert "feg._merge_player_facing_narration_purity_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_player_facing_narration_purity_into_emission_debug")
    assert callable(
        getattr(narration_purity, "merge_player_facing_narration_purity_into_emission_debug", None)
    )


def test_bj101_ownership_registry_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """Cycle BJ-101: strict and non-strict stacks call answer_shape_primacy emission_debug merge directly."""
    import inspect

    import game.final_emission_answer_shape_primacy as answer_shape_primacy
    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_merge_answer_shape_primacy_into_emission_debug(" in nss_src
    assert "feg._merge_answer_shape_primacy_into_emission_debug" not in nss_src
    assert "_merge_answer_shape_primacy_into_emission_debug(" in ss_src
    assert "feg._merge_answer_shape_primacy_into_emission_debug" not in ss_src
    assert not hasattr(feg, "_merge_answer_shape_primacy_into_emission_debug")
    assert callable(getattr(answer_shape_primacy, "merge_answer_shape_primacy_into_emission_debug", None))


def test_bj102_ownership_registry_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """Cycle BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_tone_escalation as tone_escalation

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "flag_non_hostile_escalation_from_writer_pregate(" in ss_src
    assert "feg._flag_non_hostile_escalation_from_writer_pregate" not in ss_src
    assert not hasattr(feg, "_flag_non_hostile_escalation_from_writer_pregate")
    assert callable(getattr(tone_escalation, "flag_non_hostile_escalation_from_writer_pregate", None))


def test_bj103_ownership_registry_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """Cycle BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_scene_emit_integrity as scene_emit_integrity
    import game.final_emission_strict_social_stack as ss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_compute_scene_emit_integrity_assessment(" in nss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in nss_src
    assert "_compute_scene_emit_integrity_assessment(" in ss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in ss_src
    assert not hasattr(feg, "_compute_scene_emit_integrity_assessment")
    assert callable(getattr(scene_emit_integrity, "_compute_scene_emit_integrity_assessment", None))


def test_bj104_ownership_registry_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """Cycle BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_passive_scene_pressure as passive_scene_pressure

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert "_passive_scene_pressure_due_for_fallback(" in nss_src
    assert "feg._passive_scene_pressure_due_for_fallback" not in nss_src
    assert not hasattr(feg, "_passive_scene_pressure_due_for_fallback")
    assert callable(getattr(passive_scene_pressure, "_passive_scene_pressure_due_for_fallback", None))


def test_bj105_ownership_registry_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """Cycle BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_narrative_mode_output as narrative_mode_output
    import game.final_emission_non_strict_stack as nss

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert "_narrative_mode_output_legality_assessment(" in nss_src
    assert "feg._narrative_mode_output_legality_assessment" not in nss_src
    assert not hasattr(feg, "_narrative_mode_output_legality_assessment")
    assert callable(getattr(narrative_mode_output, "_narrative_mode_output_legality_assessment", None))


def test_bj106_ownership_registry_callers_use_response_type_decision_payload_owner_directly() -> None:
    """Cycle BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta
    import game.final_emission_strict_social_stack as ss

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "response_type_decision_payload(" in ss_src
    assert "feg._response_type_decision_payload" not in ss_src
    assert "response_type_decision_payload(" in ge_accept_src
    assert "feg._response_type_decision_payload" not in ge_accept_src
    assert "response_type_decision_payload(" in ge_replace_src
    assert "feg._response_type_decision_payload" not in ge_replace_src
    assert not hasattr(feg, "_response_type_decision_payload")
    assert callable(getattr(emission_meta, "response_type_decision_payload", None))


def test_bj107_ownership_registry_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """Cycle BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta
    import game.final_emission_strict_social_stack as ss

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    assert "infer_accept_path_final_emitted_source(" in ss_src
    assert "feg.infer_accept_path_final_emitted_source" not in ss_src
    assert "infer_accept_path_final_emitted_source(" in ge_accept_src
    assert "feg.infer_accept_path_final_emitted_source" not in ge_accept_src
    assert not hasattr(feg, "infer_accept_path_final_emitted_source")
    assert callable(getattr(emission_meta, "infer_accept_path_final_emitted_source", None))


def test_bj108_ownership_registry_generic_exit_uses_opening_fallback_projection_owner_directly() -> None:
    """Cycle BJ-108: generic_exit calls meta opening fallback projection helpers directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "apply_opening_fallback_projection_fields(" in ge_replace_src
    assert "feg.apply_opening_fallback_projection_fields" not in ge_replace_src
    assert "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" in ge_replace_src
    assert "feg.OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" not in ge_replace_src
    assert not hasattr(feg, "apply_opening_fallback_projection_fields")
    assert not hasattr(feg, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")
    assert callable(getattr(emission_meta, "apply_opening_fallback_projection_fields", None))
    assert hasattr(emission_meta, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")


def test_bj109_ownership_registry_callers_use_final_emission_meta_key_owner_directly() -> None:
    """Cycle BJ-109: generic_exit and strict_social_stack use meta FINAL_EMISSION_META_KEY directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_meta as emission_meta
    import game.final_emission_strict_social_stack as ss

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "FINAL_EMISSION_META_KEY" in ss_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ss_src
    assert "FINAL_EMISSION_META_KEY" in ge_accept_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_accept_src
    assert "FINAL_EMISSION_META_KEY" in ge_replace_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_replace_src
    assert not hasattr(feg, "FINAL_EMISSION_META_KEY")
    assert hasattr(emission_meta, "FINAL_EMISSION_META_KEY")


def test_bj110_ownership_registry_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly() -> None:
    """Cycle BJ-110: generic_exit calls boundary_contract mutation assertion owner directly."""
    import inspect

    import game.final_emission_boundary_contract as boundary_contract
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "assert_final_emission_mutation_allowed(" in ge_replace_src
    assert "feg.assert_final_emission_mutation_allowed" not in ge_replace_src
    assert not hasattr(feg, "assert_final_emission_mutation_allowed")
    assert callable(getattr(boundary_contract, "assert_final_emission_mutation_allowed", None))


def test_bj111_ownership_registry_callers_use_normalize_text_owner_directly() -> None:
    """Cycle BJ-111: stack/exit callers use final_emission_text._normalize_text directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_text as emission_text

    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "_normalize_text(" in nss_src
    assert "feg._normalize_text(" not in nss_src
    assert "_normalize_text(" in ss_src
    assert "feg._normalize_text(" not in ss_src
    assert "_normalize_text(" in ge_accept_src
    assert "feg._normalize_text(" not in ge_accept_src
    assert "_normalize_text(" in ge_replace_src
    assert "feg._normalize_text(" not in ge_replace_src
    assert not hasattr(feg, "_normalize_text")
    assert callable(getattr(emission_text, "_normalize_text", None))


def test_bj112_ownership_registry_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """Cycle BJ-112: strict_social_stack calls final_emission_text._normalize_text_preserve_paragraphs directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.final_emission_text as emission_text

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_normalize_text_preserve_paragraphs(" in ss_src
    assert "feg._normalize_text_preserve_paragraphs" not in ss_src
    assert not hasattr(feg, "_normalize_text_preserve_paragraphs")
    assert callable(getattr(emission_text, "_normalize_text_preserve_paragraphs", None))


def test_bj113_ownership_registry_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """Cycle BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    import inspect

    import game.diegetic_fallback_narration as diegetic_fallback_narration
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "diegetic_classified_fallback_meta(" in ge_replace_src
    assert "feg.diegetic_classified_fallback_meta" not in ge_replace_src
    assert not hasattr(feg, "diegetic_classified_fallback_meta")
    assert callable(getattr(diegetic_fallback_narration, "fallback_template_metadata", None))


def test_bj114_ownership_registry_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """Cycle BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    import inspect

    import game.anti_reset_emission_guard as anti_reset_emission_guard
    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit

    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "anti_reset_suppresses_intro_style_fallbacks(" in ge_replace_src
    assert "feg.anti_reset_suppresses_intro_style_fallbacks" not in ge_replace_src
    assert not hasattr(feg, "anti_reset_suppresses_intro_style_fallbacks")
    assert callable(getattr(anti_reset_emission_guard, "anti_reset_suppresses_intro_style_fallbacks", None))


def test_bj115_ownership_registry_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """Cycle BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_generic_exit as generic_exit
    import game.final_emission_strict_social_stack as ss
    import game.social_exchange_emission as social_exchange_emission

    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "log_final_emission_decision(" in ge_accept_src
    assert "log_final_emission_trace(" in ge_accept_src
    assert "feg.log_final_emission_decision" not in ge_accept_src
    assert "feg.log_final_emission_trace" not in ge_accept_src
    assert "log_final_emission_decision(" in ge_replace_src
    assert "log_final_emission_trace(" in ge_replace_src
    assert "feg.log_final_emission_decision" not in ge_replace_src
    assert "feg.log_final_emission_trace" not in ge_replace_src
    assert "log_final_emission_decision(" in ss_src
    assert "log_final_emission_trace(" in ss_src
    assert "feg.log_final_emission_decision" not in ss_src
    assert "feg.log_final_emission_trace" not in ss_src
    assert not hasattr(feg, "log_final_emission_decision")
    assert not hasattr(feg, "log_final_emission_trace")
    assert callable(getattr(social_exchange_emission, "log_final_emission_decision", None))
    assert callable(getattr(social_exchange_emission, "log_final_emission_trace", None))


def test_bj116_ownership_registry_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """Cycle BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.social_exchange_emission as social_exchange_emission

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "build_final_strict_social_response(" in ss_src
    assert "minimal_social_emergency_fallback_line(" in ss_src
    assert "strict_social_deterministic_fallback_family_token(" in ss_src
    assert "feg.build_final_strict_social_response" not in ss_src
    assert "feg.minimal_social_emergency_fallback_line" not in ss_src
    assert "feg.strict_social_deterministic_fallback_family_token" not in ss_src
    assert not hasattr(feg, "build_final_strict_social_response")
    assert not hasattr(feg, "minimal_social_emergency_fallback_line")
    assert not hasattr(feg, "strict_social_deterministic_fallback_family_token")
    assert callable(getattr(social_exchange_emission, "build_final_strict_social_response", None))
    assert callable(getattr(social_exchange_emission, "minimal_social_emergency_fallback_line", None))
    assert callable(getattr(social_exchange_emission, "strict_social_deterministic_fallback_family_token", None))


def test_bj117_ownership_registry_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """Cycle BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    import inspect

    import game.fallback_provenance_debug as fallback_provenance_debug
    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.stage_diff_telemetry as stage_diff_telemetry

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "record_stage_snapshot(" in ss_src
    assert "realign_fallback_provenance_selector_to_current_text(" in ss_src
    assert "feg.record_stage_snapshot" not in ss_src
    assert "feg.realign_fallback_provenance_selector_to_current_text" not in ss_src
    assert not hasattr(feg, "record_stage_snapshot")
    assert not hasattr(feg, "realign_fallback_provenance_selector_to_current_text")
    assert callable(getattr(stage_diff_telemetry, "record_stage_snapshot", None))
    assert callable(getattr(fallback_provenance_debug, "realign_fallback_provenance_selector_to_current_text", None))


def test_bj118_ownership_registry_should_replace_candidate_intro_fallback_not_on_gate() -> None:
    """Cycle BJ-118: should_replace_candidate_intro_fallback lives on anti_reset owner, not gate."""
    import game.anti_reset_emission_guard as anti_reset_emission_guard
    import game.final_emission_gate as feg

    assert not hasattr(feg, "should_replace_candidate_intro_fallback")
    assert callable(getattr(anti_reset_emission_guard, "should_replace_candidate_intro_fallback", None))


def test_bj119_ownership_registry_stage_diff_telemetry_not_on_gate() -> None:
    """Cycle BJ-119: stage_diff_telemetry helpers live on stage_diff owner, not gate."""
    import game.final_emission_gate as feg
    import game.stage_diff_telemetry as stage_diff_telemetry

    assert not hasattr(feg, "diff_turn_stage")
    assert not hasattr(feg, "record_stage_transition")
    assert not hasattr(feg, "snapshot_turn_stage")
    assert callable(getattr(stage_diff_telemetry, "diff_turn_stage", None))
    assert callable(getattr(stage_diff_telemetry, "record_stage_transition", None))
    assert callable(getattr(stage_diff_telemetry, "snapshot_turn_stage", None))


def test_bj120_ownership_registry_harness_patches_canonical_owner_seams() -> None:
    """Cycle BJ-120: harness helpers patch owner/stack seams, not removed gate re-exports."""
    import inspect

    import tests.helpers.gate_equivalence_monkeypatch as gate_mp
    import tests.test_turn_packet_stage_diff_integration as tp_stage_diff

    mp_src = inspect.getsource(gate_mp.patch_build_final_strict_social_response)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in mp_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in mp_src
    tp_src = inspect.getsource(tp_stage_diff.test_gate_exit_records_observability_before_cache_pop)
    assert 'monkeypatch.setattr(emission_finalize, "record_stage_snapshot"' in tp_src
    assert 'monkeypatch.setattr(feg, "record_stage_snapshot"' not in tp_src
    assert "import game.final_emission_gate as feg" not in inspect.getsource(tp_stage_diff)


def test_bj121_ownership_registry_strict_social_build_patches_use_stack_seam() -> None:
    """Cycle BJ-121: strict-social build monkeypatches target strict_social_stack, not gate."""
    import inspect
    import pathlib

    import tests.helpers.strict_social_harness as strict_social_harness

    harness_src = inspect.getsource(strict_social_harness.run_strict_social_motive_overclaim_gate_case)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in harness_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in harness_src

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    for rel in (
        "tests/test_fallback_behavior_gate.py",
        "tests/test_scene_state_anchoring.py",
        "tests/helpers/gate_equivalence_monkeypatch.py",
        "tests/helpers/strict_social_harness.py",
    ):
        text = (repo_root / rel).read_text(encoding="utf-8")
        assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in text
        assert 'monkeypatch.setattr(feg_module, "build_final_strict_social_response"' not in text


def test_bj122_ownership_registry_scene_state_anchoring_tests_use_ssa_owner_bindings() -> None:
    """Cycle BJ-122: scene_state_anchoring tests use final_emission_scene_state_anchor owner bindings."""
    import inspect

    import tests.test_scene_state_anchoring as scene_state_anchoring_tests

    module_src = inspect.getsource(scene_state_anchoring_tests)
    assert "import game.final_emission_gate as feg" not in module_src
    assert 'monkeypatch.setattr(feg, "_repair_location_opening"' not in module_src
    assert 'monkeypatch.setattr(feg, "validate_scene_state_anchoring"' not in module_src
    assert "feg._resolve_scene_state_anchor_contract" not in module_src
    assert "feg._merge_scene_state_anchor_meta" not in module_src


# Cycle BJ-123 — allowed ``feg.*`` test/harness patch seams (live gate re-exports only).
_BJ123_ALLOWED_FEG_PATCH_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "get_speaker_selection_contract",  # compatibility re-export; also patch sce owner
        "apply_final_emission_gate",  # orchestration entry — direct calls, not monkeypatch targets
    }
)
_BJ123_STALE_FEG_PATCH_FRAGMENTS: Final[tuple[str, ...]] = (
    'monkeypatch.setattr(feg, "_apply_visibility_enforcement"',
    'monkeypatch.setattr(_feg, "_apply_visibility_enforcement"',
    '"game.final_emission_gate._apply_visibility_enforcement"',
    'monkeypatch.setattr(feg, "minimal_social_emergency_fallback_line"',
    'monkeypatch.setattr(feg, "strict_social_emission_will_apply"',
    'monkeypatch.setattr(_feg, "strict_social_emission_will_apply"',
    "feg._finalize_emission_output(",
    "feg._final_emission_fast_path_eligible(",
    "feg._default_response_type_debug(",
    '"game.final_emission_gate.strict_social_emission_will_apply"',
    "final_emission_gate.validate_player_facing_referential_clarity",
    "final_emission_gate._try_strict_social_local_pronoun_substitution_repair",
    'monkeypatch.setattr(feg, "build_final_strict_social_response"',
    'monkeypatch.setattr(feg, "record_stage_snapshot"',
    'monkeypatch.setattr(feg, "_repair_location_opening"',
    'monkeypatch.setattr(feg, "validate_scene_state_anchoring"',
    "import game.final_emission_gate as _feg",
    "from game.final_emission_gate import _global_narrative_fallback_stock_line",
    "from game.final_emission_gate import validate_answer_completeness",
    "from game.final_emission_gate import inspect_answer_completeness_failure",
)
_BJ123_HARNESS_PATCH_SCAN_PATHS: Final[tuple[str, ...]] = (
    "tests/helpers/gate_equivalence_monkeypatch.py",
    "tests/helpers/post_speaker_finalize_probe.py",
    "tests/helpers/speaker_relocation_shadow_harness.py",
    "tests/helpers/strict_social_harness.py",
    "tests/helpers/emission_smoke_assertions.py",
    "tests/test_final_emission_boundary_convergence.py",
    "tests/test_final_emission_boundary_no_semantic_repair.py",
    "tests/test_anti_railroading_transcript_regressions.py",
    "tests/test_prompt_context.py",
    "tests/test_social_exchange_emission.py",
    "tests/test_final_emission_sealed_fallback.py",
    "tests/test_final_emission_visibility.py",
    "tests/test_manual_play_latency.py",
    "tests/test_tone_escalation_rules.py",
    "tests/test_referential_clarity_strict_social_local_repair.py",
    "tests/test_lead_npc_payoff_and_fallback.py",
    "tests/test_strict_social_answer_pressure_cashout.py",
    "tests/test_anti_reset_emission_guard.py",
    "tests/test_narration_transcript_regressions.py",
    "tests/test_answer_completeness_rules.py",
    "tests/test_interaction_continuity_repair.py",
    "tests/test_narrative_authority_rules.py",
    "tests/test_player_facing_narration_purity.py",
    "tests/test_context_separation.py",
    "tests/test_anti_railroading.py",
    "tests/test_fallback_behavior_gate.py",
    "tests/test_final_emission_opening_fallback.py",
    "tests/test_diegetic_fallback_block4.py",
)


def test_bj123_ownership_registry_harness_patches_no_stale_feg_seams() -> None:
    """Cycle BJ-123: tests/helpers patch canonical owner modules, not removed feg re-exports."""
    import inspect
    import pathlib

    import tests.helpers.gate_equivalence_monkeypatch as gate_mp

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    for rel in _BJ123_HARNESS_PATCH_SCAN_PATHS:
        text = (repo_root / rel).read_text(encoding="utf-8")
        for frag in _BJ123_STALE_FEG_PATCH_FRAGMENTS:
            assert frag not in text, f"{rel} still has stale feg seam fragment: {frag!r}"

    mp_src = inspect.getsource(gate_mp.patch_get_speaker_selection_contract)
    assert 'monkeypatch.setattr(feg, "get_speaker_selection_contract"' in mp_src
    assert 'monkeypatch.setattr(sce, "get_speaker_selection_contract"' in mp_src

    smoke_src = (repo_root / "tests/helpers/emission_smoke_assertions.py").read_text(encoding="utf-8")
    assert "game.social_exchange_emission.strict_social_emission_will_apply" in smoke_src
    assert "game.final_emission_gate.strict_social_emission_will_apply" not in smoke_src

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BJ-123" in registry_doc
    assert "get_speaker_selection_contract" in registry_doc


# Cycle BJ-124 — BJ-123-dead seams must not remain as gate-module imports/re-exports.
_BJ124_DEAD_GATE_REEXPORT_SYMBOLS: Final[frozenset[str]] = frozenset(
    {
        "_apply_visibility_enforcement",
        "strict_social_emission_will_apply",
        "minimal_social_emergency_fallback_line",
        "_finalize_emission_output",
        "_final_emission_fast_path_eligible",
        "_default_response_type_debug",
        "_default_response_delta_meta",
        "validate_player_facing_referential_clarity",
        "_try_strict_social_local_pronoun_substitution_repair",
    }
)
_BJ124_DEAD_GATE_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "strict_social_emission_will_apply",
    "_default_response_type_debug",
    "_default_response_delta_meta",
    "_apply_visibility_enforcement",
    "minimal_social_emergency_fallback_line",
    "_finalize_emission_output",
    "_final_emission_fast_path_eligible",
    "validate_player_facing_referential_clarity",
    "_try_strict_social_local_pronoun_substitution_repair",
)


def test_bj124_ownership_registry_gate_module_has_no_bj123_dead_reexports() -> None:
    """Cycle BJ-124: gate module must not re-export BJ-123-dead harness seams."""
    import game.final_emission_gate as feg

    gate_path = Path(feg.__file__)
    gate_src = gate_path.read_text(encoding="utf-8")

    for name in _BJ124_DEAD_GATE_REEXPORT_SYMBOLS:
        assert not hasattr(feg, name), f"gate still re-exports dead seam: {name!r}"

    for marker in _BJ124_DEAD_GATE_IMPORT_MARKERS:
        assert marker not in gate_src, f"gate source still imports dead seam marker: {marker!r}"

    assert callable(getattr(feg, "apply_final_emission_gate", None))
    assert callable(getattr(feg, "get_speaker_selection_contract", None))

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BJ-124" in registry_doc


def test_bj125_ownership_registry_anti_reset_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-125/BN8: anti-reset tests patch social_exchange_emission + preflight strict-social seam."""
    import inspect
    import pathlib

    import tests.test_anti_reset_emission_guard as anti_reset_tests

    module_src = inspect.getsource(anti_reset_tests)
    assert "import game.final_emission_gate as" not in module_src
    assert "from game.final_emission_gate import" not in module_src
    assert "feg." not in module_src
    assert "_feg" not in module_src
    assert 'monkeypatch.setattr(social_exchange_emission, "strict_social_emission_will_apply"' in module_src
    assert 'monkeypatch.setattr(gate_preflight_strict_social, "strict_social_emission_will_apply"' in module_src
    assert 'monkeypatch.setattr(feg, "strict_social_emission_will_apply"' not in module_src
    assert '"game.final_emission_gate.strict_social_emission_will_apply"' not in module_src

    rel = "tests/test_anti_reset_emission_guard.py"
    text = (pathlib.Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")
    for frag in (
        'monkeypatch.setattr(feg, "strict_social_emission_will_apply"',
        '"game.final_emission_gate.strict_social_emission_will_apply"',
        "import game.final_emission_gate as",
        "from game.final_emission_gate import",
    ):
        assert frag not in text, f"anti_reset test still uses stale gate seam: {frag!r}"
    assert "import game.final_emission_gate_preflight_strict_social as gate_preflight_strict_social" in text

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BJ-125" in registry_doc


def test_bj126_ownership_registry_narration_transcript_tests_patch_strict_social_owner_not_gate() -> None:
    """Cycle BJ-126/BN8: narration transcript tests patch owner + preflight strict-social seam."""
    import inspect
    import pathlib

    import tests.test_narration_transcript_regressions as narration_transcript_tests

    module_src = inspect.getsource(narration_transcript_tests)
    assert "import game.final_emission_gate as" not in module_src
    assert "from game.final_emission_gate import" not in module_src
    assert "_feg" not in module_src
    assert 'monkeypatch.setattr(feg, "strict_social_emission_will_apply"' not in module_src
    assert '"game.final_emission_gate.strict_social_emission_will_apply"' not in module_src
    assert "def patch_strict_social_emission_will_apply(" in module_src
    helper_src = inspect.getsource(narration_transcript_tests.patch_strict_social_emission_will_apply)
    assert 'monkeypatch.setattr(social_exchange_emission, "strict_social_emission_will_apply"' in helper_src
    assert 'monkeypatch.setattr(gate_preflight_strict_social, "strict_social_emission_will_apply"' in helper_src
    vis_src = inspect.getsource(narration_transcript_tests.patch_final_emission_helpers)
    assert 'monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement"' in vis_src
    assert 'monkeypatch.setattr(_feg, "_apply_visibility_enforcement"' not in vis_src

    rel = "tests/test_narration_transcript_regressions.py"
    text = (pathlib.Path(__file__).resolve().parents[1] / rel).read_text(encoding="utf-8")
    for frag in (
        'monkeypatch.setattr(_feg, "strict_social_emission_will_apply"',
        'monkeypatch.setattr(feg, "strict_social_emission_will_apply"',
        '"game.final_emission_gate.strict_social_emission_will_apply"',
        'monkeypatch.setattr(_feg, "_apply_visibility_enforcement"',
        "import game.final_emission_gate as",
    ):
        assert frag not in text, f"narration transcript test still uses stale gate seam: {frag!r}"

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BJ-126" in registry_doc


# Cycle BJ-127 — global stale gate harness scan (extends BJ-123 fragment/allowlist locks).
_BJ127_GLOBAL_SCAN_EXCLUDE: Final[frozenset[str]] = frozenset(
    {
        "tests/test_ownership_registry.py",
        "tests/test_final_emission_gate.py",
        "tests/test_architecture_audit_tool.py",
    }
)
_BJ127_FEG_ALIAS_IMPORT_ALLOWLIST: Final[frozenset[str]] = frozenset(
    {
        "tests/helpers/gate_equivalence_monkeypatch.py",
        "tests/test_final_emission_gate.py",
        "tests/test_ownership_registry.py",
        "tests/test_speaker_contract_enforcement_extraction.py",
        "tests/test_diegetic_fallback_narration.py",
        "tests/test_final_emission_acceptance_quality.py",
        "tests/test_final_emission_response_type.py",
        "tests/test_final_emission_scene_state_anchor.py",
        "tests/test_final_emission_visibility.py",
        "tests/test_final_emission_sealed_fallback.py",
        "tests/test_c4_narrative_mode_live_pipeline.py",
        "tests/test_answer_shape_primacy.py",
        "tests/test_final_emission_fast_fallback_composition.py",
        "tests/test_final_emission_visibility_fallback.py",
        "tests/test_dialogue_social_plan.py",
    }
)
_BJ127_FEG_ALIAS_IMPORT_MARKERS: Final[tuple[str, ...]] = (
    "import game.final_emission_gate as feg",
    "import game.final_emission_gate as _feg",
    "import game.final_emission_gate as feg_module",
)


def test_bj127_ownership_registry_global_stale_gate_harness_scan() -> None:
    """Cycle BJ-127: global scan — no stale feg monkeypatches or dead feg alias imports."""
    import pathlib

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    for path in sorted((repo_root / "tests").rglob("*.py")):
        rel = path.relative_to(repo_root).as_posix()
        if rel in _BJ127_GLOBAL_SCAN_EXCLUDE:
            continue
        text = path.read_text(encoding="utf-8")
        for frag in _BJ123_STALE_FEG_PATCH_FRAGMENTS:
            assert frag not in text, f"{rel} still has stale feg seam fragment: {frag!r}"

        if any(marker in text for marker in _BJ127_FEG_ALIAS_IMPORT_MARKERS):
            if rel not in _BJ127_FEG_ALIAS_IMPORT_ALLOWLIST:
                uses_alias = "feg." in text or "_feg." in text or "feg_module." in text
                assert uses_alias, (
                    f"{rel} imports final_emission_gate alias but never uses it "
                    f"(remove dead import or add to _BJ127_FEG_ALIAS_IMPORT_ALLOWLIST)"
                )

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BJ-127" in registry_doc


# Cycle BJ-128/BJ-129 — thin gate boundary locks (canonical constants in tests/helpers).
from tests.helpers.gate_thin_boundary_locks import (
    BJ128_DEAD_GATE_IMPORT_MARKERS as _BJ128_DEAD_GATE_IMPORT_MARKERS,
    BJ128_DEAD_GATE_REEXPORT_SYMBOLS as _BJ128_DEAD_GATE_REEXPORT_SYMBOLS,
    BJ128_LIVE_GATE_SEAM_SYMBOLS as _BJ128_LIVE_GATE_SEAM_SYMBOLS,
    BJ129_ALLOWED_GATE_IMPORT_MODULES as _BJ129_ALLOWED_GATE_IMPORT_MODULES,
    BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES as _BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES,
    assert_gate_bj128_no_dead_import_reexports,
    assert_gate_bj129_thin_boundary_shape,
    gate_import_modules,
)


def test_bj128_ownership_registry_gate_module_has_no_dead_import_only_reexports() -> None:
    """Cycle BJ-128: gate module keeps orchestration + live seams only; no import-only residue."""
    import game.final_emission_gate as feg

    assert_gate_bj128_no_dead_import_reexports(feg)

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BJ-128" in registry_doc


def test_bj129_ownership_registry_gate_module_thin_boundary_stabilization_locked() -> None:
    """Cycle BJ-129: gate module must not regrow beyond orchestration + documented live seams."""
    import game.final_emission_gate as feg

    assert_gate_bj129_thin_boundary_shape(feg)

    gate_src = Path(feg.__file__).read_text(encoding="utf-8")
    assert gate_import_modules(gate_src) == _BJ129_ALLOWED_GATE_IMPORT_MODULES

    registry_doc = Path(__file__).read_text(encoding="utf-8")
    assert "BJ-129" in registry_doc
    assert "_BJ129_ALLOWED_GATE_IMPORT_MODULES" in registry_doc
    assert "_BJ129_FORBIDDEN_GATE_IMPORT_CATEGORIES" in registry_doc


def test_bj49_gate_context_owner_entrypoint_locked() -> None:
    """Cycle BJ-49/BJ-72: gate entry/preflight context lives on final_emission_gate_context owner."""
    import game.final_emission_gate as feg
    import game.final_emission_gate_context as gc

    assert callable(getattr(gc, "initialize_gate_execution_context", None))
    assert callable(getattr(gc, "GateExecutionContext", None))
    assert not hasattr(feg, "_initialize_gate_execution_context")


def test_bj72_ownership_registry_apply_gate_calls_gate_context_owner_directly() -> None:
    """Cycle BJ-72: apply_final_emission_gate calls gate_context owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_gate_context as gc

    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "initialize_gate_execution_context(" in gate_src
    assert "_initialize_gate_execution_context" not in gate_src
    assert not hasattr(feg, "_initialize_gate_execution_context")
    assert callable(getattr(gc, "initialize_gate_execution_context", None))


def test_bj41_finalize_emission_output_owner_entrypoint_locked() -> None:
    """Cycle BJ-41/BJ-69: finalize packaging and fast-path eligibility live on final_emission_finalize owner."""
    import game.final_emission_finalize as fin
    import game.final_emission_gate as feg

    assert callable(getattr(fin, "finalize_emission_output", None))
    assert callable(getattr(fin, "final_emission_fast_path_eligible", None))
    assert not hasattr(feg, "_finalize_emission_output")
    assert not hasattr(feg, "_final_emission_fast_path_eligible")


def test_bj40_acceptance_quality_n4_floor_seam_owner_entrypoint_locked() -> None:
    """Cycle BJ-40/BJ-74: N4 floor seam lives on final_emission_acceptance_quality owner."""
    import game.final_emission_acceptance_quality as aq
    import game.final_emission_gate as feg

    assert callable(getattr(aq, "apply_acceptance_quality_n4_floor_seam", None))
    assert not hasattr(feg, "_apply_acceptance_quality_n4_floor_seam")


def test_bj74_ownership_registry_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """Cycle BJ-74: terminal pipeline calls acceptance_quality N4 floor seam owner directly."""
    import inspect

    import game.final_emission_acceptance_quality as aq
    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "apply_acceptance_quality_n4_floor_seam(" in tp_src
    assert "feg._apply_acceptance_quality_n4_floor_seam" not in tp_src
    assert not hasattr(feg, "_apply_acceptance_quality_n4_floor_seam")
    assert callable(getattr(aq, "apply_acceptance_quality_n4_floor_seam", None))


def test_bj75_ownership_registry_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """Cycle BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_terminal_pipeline as tp
    import game.interaction_continuity as ic

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "attach_interaction_continuity_validation(" in tp_src
    assert "feg._attach_interaction_continuity_validation" not in tp_src
    assert not hasattr(feg, "_attach_interaction_continuity_validation")
    assert callable(getattr(ic, "attach_interaction_continuity_validation", None))


def test_bj76_ownership_registry_stacks_call_ic_emission_step_owner_directly() -> None:
    """Cycle BJ-76: terminal pipeline and non_strict_stack call IC emission-step owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_terminal_pipeline as tp
    import game.interaction_continuity as ic

    tp_src = inspect.getsource(tp.run_gate_terminal_enforcement_pipeline)
    assert "apply_interaction_continuity_emission_step(" in tp_src
    assert "feg._apply_interaction_continuity_emission_step" not in tp_src
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    assert "apply_interaction_continuity_emission_step(" in nss_src
    assert "feg._apply_interaction_continuity_emission_step" not in nss_src
    assert not hasattr(feg, "_apply_interaction_continuity_emission_step")
    assert callable(getattr(ic, "apply_interaction_continuity_emission_step", None))


def test_bj77_ownership_registry_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """Cycle BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.speaker_contract_enforcement as sce

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "enforce_emitted_speaker_with_contract(" in ss_src
    assert "feg.enforce_emitted_speaker_with_contract" not in ss_src
    assert not hasattr(feg, "enforce_emitted_speaker_with_contract")
    assert callable(getattr(sce, "enforce_emitted_speaker_with_contract", None))


def test_bj78_ownership_registry_strict_social_stack_calls_sync_owner_directly() -> None:
    """Cycle BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_strict_social_stack as ss
    import game.speaker_contract_enforcement as sce

    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "_sync_eff_social_to_resolution(" in ss_src
    assert "feg._sync_eff_social_to_resolution" not in ss_src
    assert not hasattr(feg, "_sync_eff_social_to_resolution")
    assert callable(getattr(sce, "_sync_eff_social_to_resolution", None))


def test_bj39_response_type_contract_owner_entrypoint_locked() -> None:
    """Cycle BJ-39/BJ-67/BJ-68: response-type contract enforcement lives on final_emission_response_type owner."""
    import inspect

    import game.final_emission_gate as feg
    import game.final_emission_non_strict_stack as nss
    import game.final_emission_response_type as rt
    import game.final_emission_strict_social_stack as ss
    from tests.helpers import emission_smoke_assertions as smoke
    from tests.helpers import opening_fallback_gate_harness as ob_harness

    assert callable(getattr(rt, "enforce_response_type_contract", None))
    assert not hasattr(feg, "_enforce_response_type_contract")
    nss_src = inspect.getsource(nss.run_non_strict_layer_stack)
    ss_src = inspect.getsource(ss.run_strict_social_composition_trunk)
    assert "response_type.enforce_response_type_contract" in nss_src
    assert ss_src.count("response_type.enforce_response_type_contract") == 2
    assert "feg._enforce_response_type_contract" not in nss_src
    assert "feg._enforce_response_type_contract" not in ss_src
    ob_src = inspect.getsource(ob_harness)
    smoke_fn_src = inspect.getsource(smoke.enforce_response_type_contract_layer)
    assert "response_type.enforce_response_type_contract" in ob_src
    assert "final_emission_response_type" in smoke_fn_src


def test_bj38_fallback_debug_merge_helpers_live_on_repairs_owner() -> None:
    """Cycle BJ-38/BJ-93/BJ-94: fallback/conversational-memory emission_debug merges live on final_emission_repairs."""
    import game.final_emission_gate as feg
    import game.final_emission_repairs as fer

    assert callable(getattr(fer, "merge_fallback_behavior_into_emission_debug", None))
    assert callable(getattr(fer, "merge_conversational_memory_inspection_into_emission_debug", None))
    assert not hasattr(feg, "_merge_fallback_behavior_into_emission_debug")
    assert not hasattr(feg, "_merge_conversational_memory_inspection_into_emission_debug")
