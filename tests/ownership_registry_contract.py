"""Canonical test-responsibility registry contract (import-light; no pytest).

Answers: *which test module is the direct owner for each governed responsibility slice?*
Registry data and lookup helpers live here; enforcement tests remain in
``tests/test_ownership_registry.py``.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import AbstractSet, Final, Mapping, Tuple

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
            "tests/test_golden_replay_protected_bridge.py",
            "tests/test_golden_replay_structural_invariants.py",
            "tests/test_golden_replay_long_session.py",
            "tests/test_golden_replay_direct_seam.py",
            "tests/test_golden_replay_scenario_spine.py",
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
    "test_build_report_from_inputs": (
        "Parallel CA corrective-report tool contract probes (absence vs availability); "
        "distinct modules disambiguate report surface."
    ),
    "test_closeout_doc_states_six_scenario_protected_corpus": (
        "Parallel BW/BZ protected-replay trend-window closeout doc locks; "
        "distinct cycle closeout modules."
    ),
    "test_concentration_calculations": (
        "Parallel CA corrective-prevention vs embedded-attribution report math smoke; "
        "distinct audit modules."
    ),
    "test_deterministic_ordering": (
        "Shared fallback portfolio report contract shape across economics/recurrence/ROI suites; "
        "distinct modules disambiguate pytest -k."
    ),
    "test_empty_history": (
        "Parallel empty-history edge probes in fallback maintenance economics vs remediation queue."
    ),
    "test_report_generation": (
        "Parallel report-writer contract smoke across CA corrective and fallback portfolio audit modules."
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
