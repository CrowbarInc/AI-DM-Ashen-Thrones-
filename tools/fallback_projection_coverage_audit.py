#!/usr/bin/env python3
"""Audit fallback projection coverage over canonical finalized FEM shapes.

The catalog is deliberately audit-only. It executes the existing read-side
projector without changing its rules, runtime behavior, or fallback taxonomy.
Coverage is shape-level completeness, not runtime incidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import game.final_emission_meta  # noqa: E402,F401 - establishes the repository's circular import order
from game.final_emission_replay_projection import build_fem_runtime_lineage_events  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUTPUT = ROOT / "artifacts" / "golden_replay" / "projection_coverage_report.json"
UNPROJECTED_BUCKET = "<unprojected>"
MISSING_BUCKET = "<none>"


@dataclass(frozen=True)
class EvidenceShape:
    shape_id: str
    fem: Mapping[str, Any]
    source: str
    rationale: str
    projection_source: str
    assessment: str = "projected"


PROJECTED_EVIDENCE_SHAPES: tuple[EvidenceShape, ...] = (
    EvidenceShape(
        "sanitizer_strict_social",
        {
            "sanitizer_strict_social_fallback_used": True,
            "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
            "fallback_family_used": "social",
            "realization_fallback_family": "strict_social_deterministic_fallback",
        },
        "game/output_sanitizer.py",
        "A finalized sanitizer trace says the strict-social fallback was used.",
        "sanitizer_strict_social_fallback_used is True",
    ),
    EvidenceShape(
        "sanitizer_empty_output",
        {
            "sanitizer_empty_fallback_used": True,
            "sanitizer_empty_fallback_source": "diegetic_uncertainty_fallback",
        },
        "game/output_sanitizer.py",
        "A finalized sanitizer trace says the empty-output fallback was used.",
        "sanitizer_empty_fallback_used or sanitizer_lineage_empty_fallback_used is True",
    ),
    EvidenceShape(
        "opening_failed_closed",
        {
            "opening_fallback_failed_closed": True,
            "final_emitted_source": "opening_fallback_failed_closed",
            "fallback_family_used": "scene_opening",
            "realization_fallback_family": "gate_terminal_repair",
        },
        "game/final_emission_opening_fallback.py",
        "Opening fallback construction failed closed at the terminal gate.",
        "opening_fallback_failed_closed or matching repair/source evidence",
    ),
    EvidenceShape(
        "scene_opening",
        {
            "final_route": "replaced",
            "final_emitted_source": "opening_deterministic_fallback",
            "opening_recovered_via_fallback": True,
            "opening_fallback_authorship_source": "upstream_prepared_opening_fallback",
            "fallback_family_used": "scene_opening",
            "realization_fallback_family": "upstream_prepared_emission",
        },
        "game/final_emission_opening_fallback.py",
        "Finalized opening metadata says fallback recovery supplied emitted text.",
        "opening_recovered_via_fallback is True or source is opening_deterministic_fallback",
    ),
    EvidenceShape(
        "response_type_prepared_emission",
        {
            "upstream_prepared_emission_used": True,
            "response_type_repair_used": True,
            "response_type_repair_kind": "answer_upstream_prepared_repair",
            "final_emitted_source": "upstream_prepared_answer",
            "realization_fallback_family": "upstream_prepared_emission",
        },
        "game/final_emission_response_type.py",
        "A supported response-type repair used upstream-prepared emission.",
        "upstream_prepared_emission_used plus supported answer/action repair kind",
    ),
    EvidenceShape(
        "minimal_social_emergency_fallback",
        {
            "final_route": "replaced",
            "final_emitted_source": "minimal_social_emergency_fallback",
            "fallback_family_used": "social",
            "realization_fallback_family": "strict_social_deterministic_fallback",
            "sealed_fallback_owner_bucket": "strict-social-sealed",
        },
        "game/social_exchange_emission.py",
        "The final emitted source is the minimal social emergency fallback.",
        "final_emitted_source is minimal_social_emergency_fallback",
    ),
    EvidenceShape(
        "strict_social_fallback",
        {
            "final_emitted_source": "strict_social_deterministic_fallback",
            "fallback_family_used": "social",
            "realization_fallback_family": "strict_social_deterministic_fallback",
        },
        "game/social_exchange_emission.py",
        "The final emitted source is a recognized strict-social fallback source.",
        "recognized strict-social source or strict_social_dialogue_repair",
    ),
    EvidenceShape(
        "visibility_or_scene_replacement",
        {
            "final_route": "replaced",
            "final_emitted_source": "narrative_safe_fallback",
            "visibility_replacement_applied": True,
            "visibility_fallback_pool": "global_scene_narrative",
            "visibility_fallback_kind": "narrative_safe_fallback",
            "visibility_fallback_owner_bucket": "sealed-gate",
            "fallback_family_used": "action",
            "realization_fallback_family": "gate_terminal_repair",
        },
        "game/final_emission_visibility_fallback.py",
        "Finalized visibility metadata says a hard replacement was applied.",
        "visibility, first-mention, or referential-clarity replacement flag is True",
    ),
    EvidenceShape(
        "upstream_fast_fallback",
        {
            "fallback_provenance_trace": {"source": "fallback", "stage": "api"},
            "realization_fallback_family": "retry_terminal_fallback",
        },
        "game/fallback_provenance_debug.py",
        "The finalized provenance trace proves API/retry fallback selection.",
        "fallback_provenance_trace.source is fallback",
    ),
    EvidenceShape(
        "sealed_social_interlocutor_fallback",
        {
            "final_route": "replaced",
            "final_emitted_source": "social_interlocutor_minimal_fallback",
            "sealed_fallback_owner_bucket": "strict-social-sealed",
            "fallback_family_used": "social",
            "realization_fallback_family": "strict_social_deterministic_fallback",
        },
        "game/final_emission_sealed_fallback.py",
        "A sealed terminal replacement emitted social-interlocutor fallback content.",
        "final_route replaced plus sealed social source",
    ),
    EvidenceShape(
        "sealed_passive_scene_pressure_fallback",
        {
            "final_route": "replaced",
            "final_emitted_source": "passive_scene_pressure_fallback",
            "sealed_fallback_owner_bucket": "sealed-gate",
            "fallback_family_used": "action",
            "realization_fallback_family": "gate_terminal_repair",
        },
        "game/final_emission_sealed_fallback.py",
        "A sealed terminal replacement emitted passive scene-pressure content.",
        "final_route replaced plus passive-pressure source/kind",
    ),
    EvidenceShape(
        "sealed_npc_pursuit_neutral_fallback",
        {
            "final_route": "replaced",
            "final_emitted_source": "npc_pursuit_neutral_fallback",
            "sealed_fallback_owner_bucket": "sealed-gate",
            "fallback_family_used": "action",
            "realization_fallback_family": "gate_terminal_repair",
        },
        "game/final_emission_sealed_fallback.py",
        "A sealed terminal replacement emitted neutral NPC-pursuit content.",
        "final_route replaced plus NPC-pursuit source/kind",
    ),
    EvidenceShape(
        "sealed_anti_reset_continuation_fallback",
        {
            "final_route": "replaced",
            "final_emitted_source": "anti_reset_local_continuation_fallback",
            "sealed_fallback_owner_bucket": "sealed-gate",
            "fallback_family_used": "action",
            "realization_fallback_family": "gate_terminal_repair",
        },
        "game/final_emission_sealed_fallback.py",
        "A sealed terminal replacement emitted anti-reset continuation content.",
        "final_route replaced plus anti-reset source/kind",
    ),
    EvidenceShape(
        "sealed_global_scene_fallback",
        {
            "final_route": "replaced",
            "final_emitted_source": "global_scene_fallback",
            "sealed_fallback_owner_bucket": "sealed-gate",
            "fallback_family_used": "observe",
            "realization_fallback_family": "gate_terminal_repair",
        },
        "game/final_emission_sealed_fallback.py",
        "A sealed terminal replacement emitted a global scene fallback.",
        "final_route replaced plus recognized global source/kind",
    ),
    EvidenceShape(
        "sealed_unknown_replacement",
        {
            "final_route": "replaced",
            "final_emitted_source": "unclassified_terminal_fallback",
            "sealed_fallback_owner_bucket": "sealed-gate",
            "realization_fallback_family": "gate_terminal_repair",
        },
        "game/final_emission_sealed_fallback.py",
        "Any otherwise-unrecognized final terminal replacement is conservatively projected.",
        "final_route replaced plus sealed unknown sub-kind fallback",
    ),
)

UNPROJECTED_EVIDENCE_SHAPES: tuple[EvidenceShape, ...] = (
    EvidenceShape(
        "forced_retry_terminal_route",
        {
            "final_route": "forced_retry_fallback",
            "fallback_kind": "retry_escape_hatch",
            "realization_fallback_family": "retry_terminal_fallback",
        },
        "game/gm_retry.py::force_terminal_retry_fallback",
        "The terminal route, fallback kind, and governed family all say retry fallback was emitted.",
        "no current _fem_selected_fallback_projection branch",
        "suspected_false_negative_if_present_on_finalized_fem",
    ),
    EvidenceShape(
        "social_minimal_retry_route",
        {
            "final_route": "social_fallback_minimal",
            "fallback_kind": "social_empty_resolution_repair",
            "realization_fallback_family": "retry_terminal_fallback",
        },
        "game/gm_retry.py::ensure_minimal_social_resolution",
        "The finalized route and retry family explicitly identify social fallback repair.",
        "no current _fem_selected_fallback_projection branch",
        "suspected_false_negative_if_present_on_finalized_fem",
    ),
    EvidenceShape(
        "nonsocial_minimal_retry_route",
        {
            "final_route": "nonsocial_fallback_minimal",
            "fallback_kind": "nonsocial_empty_resolution_repair",
            "realization_fallback_family": "retry_terminal_fallback",
        },
        "game/gm_retry.py::ensure_minimal_nonsocial_resolution",
        "The finalized route and retry family explicitly identify non-social fallback repair.",
        "no current _fem_selected_fallback_projection branch",
        "suspected_false_negative_if_present_on_finalized_fem",
    ),
    EvidenceShape(
        "provider_failure_family_without_trace",
        {"realization_fallback_family": "gpt_budget_or_provider_failure"},
        "game/api.py and game/gm.py",
        "The governed family explicitly denotes a budget/provider fallback, but no provenance trace proves selection.",
        "no current _fem_selected_fallback_projection branch",
        "ambiguous_gap_family_is_strong_but_trace_may_be_intentionally_required",
    ),
)

INTENTIONAL_OMISSION_SHAPES: tuple[EvidenceShape, ...] = (
    EvidenceShape(
        "diegetic_family_only",
        {"fallback_family_used": "observe"},
        "game/diegetic_fallback_narration.py",
        "Family metadata classifies content but does not prove that the candidate was emitted.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
    EvidenceShape(
        "prepared_emission_available_not_used",
        {"upstream_prepared_emission_valid": True, "upstream_prepared_emission_used": False},
        "game/final_emission_response_type.py",
        "Prepared payload availability is explicitly not selection evidence.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
    EvidenceShape(
        "opening_authorship_without_recovery",
        {
            "opening_fallback_authorship_source": "upstream_prepared_opening_fallback",
            "opening_recovered_via_fallback": False,
        },
        "game/final_emission_opening_fallback.py",
        "Authorship metadata may describe a prepared candidate without terminal use.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
    EvidenceShape(
        "visibility_candidate_not_applied",
        {
            "visibility_replacement_applied": False,
            "visibility_fallback_pool": "global_scene_narrative",
            "visibility_fallback_kind": "narrative_safe_fallback",
            "visibility_fallback_owner_bucket": "sealed-gate",
        },
        "game/final_emission_visibility_fallback.py",
        "Candidate routing metadata with replacement false does not prove emission.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
    EvidenceShape(
        "sealed_owner_bucket_only",
        {"sealed_fallback_owner_bucket": "sealed-gate"},
        "game/final_emission_sealed_fallback.py",
        "An attribution bucket alone does not prove a sealed replacement occurred.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
    EvidenceShape(
        "sanitizer_fallback_explicitly_not_used",
        {"sanitizer_empty_fallback_used": False},
        "game/output_sanitizer.py",
        "The finalized boolean explicitly says no sanitizer fallback was used.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
    EvidenceShape(
        "non_fallback_response_type_repair",
        {"response_type_repair_used": True, "response_type_repair_kind": "dialogue_minimal_repair"},
        "game/final_emission_response_type.py",
        "A local response-shape repair is not necessarily fallback content selection.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
    EvidenceShape(
        "fallback_behavior_policy_repair",
        {"fallback_behavior_checked": True, "fallback_behavior_repaired": True},
        "game/final_emission_repairs.py",
        "Fallback-behavior contract repair describes policy compliance, not fallback emission.",
        "intentionally excluded from selection projection",
        "intentional_non_proof",
    ),
)

PROJECTION_CANDIDATES = PROJECTED_EVIDENCE_SHAPES + UNPROJECTED_EVIDENCE_SHAPES


def _fallback_events(fem: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in build_fem_runtime_lineage_events(fem)
        if event.get("event_type") == "runtime_lineage" and event.get("event_kind") == "fallback_selected"
    ]


def _token(value: Any) -> str:
    normalized = str(value or "").strip()
    return normalized or MISSING_BUCKET


def _owner_bucket(fem: Mapping[str, Any], event: Mapping[str, Any] | None) -> str:
    values = (
        event.get("fallback_owner_bucket") if isinstance(event, Mapping) else None,
        fem.get("opening_fallback_owner_bucket"),
        fem.get("sealed_fallback_owner_bucket"),
        fem.get("visibility_fallback_owner_bucket"),
    )
    for value in values:
        token = str(value or "").strip()
        if token:
            return token
    return MISSING_BUCKET


def _coverage_by(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        value = _token(row.get(field))
        bucket = buckets.setdefault(value, {"projection_candidate_count": 0, "projected_fallback_count": 0})
        bucket["projection_candidate_count"] += 1
        bucket["projected_fallback_count"] += int(row["projected"])
    out: dict[str, dict[str, Any]] = {}
    for value in sorted(buckets):
        candidate_count = buckets[value]["projection_candidate_count"]
        projected_count = buckets[value]["projected_fallback_count"]
        out[value] = {
            "projection_candidate_count": candidate_count,
            "projected_fallback_count": projected_count,
            "unprojected_fallback_count": candidate_count - projected_count,
            "projection_coverage_rate": projected_count / candidate_count if candidate_count else 0.0,
        }
    return out


def build_projection_coverage_report() -> dict[str, Any]:
    """Evaluate the existing projector against the canonical audit catalog."""
    rows: list[dict[str, Any]] = []
    projected_shapes: list[dict[str, Any]] = []
    unprojected_shapes: list[dict[str, Any]] = []

    for shape in PROJECTION_CANDIDATES:
        fem = dict(shape.fem)
        events = _fallback_events(fem)
        event = events[0] if events else None
        projected = event is not None
        row = {
            "shape_id": shape.shape_id,
            "projected": projected,
            "fallback_kind": event.get("fallback_kind") if event else UNPROJECTED_BUCKET,
            "owner": event.get("owner") if event else None,
            "owner_bucket": _owner_bucket(fem, event),
            "diegetic_family": fem.get("fallback_family_used"),
            "realization_family": fem.get("realization_fallback_family"),
            "projection_source": shape.projection_source,
            "source": shape.source,
            "rationale": shape.rationale,
            "assessment": shape.assessment,
            "evidence_shape": {key: fem[key] for key in sorted(fem)},
        }
        rows.append(row)
        if projected:
            projected_shapes.append(row)
        else:
            unprojected_shapes.append(row)

    candidate_count = len(rows)
    projected_count = len(projected_shapes)
    intentional_omissions = [
        {
            "shape_id": shape.shape_id,
            "source": shape.source,
            "rationale": shape.rationale,
            "assessment": shape.assessment,
            "evidence_shape": {key: shape.fem[key] for key in sorted(shape.fem)},
        }
        for shape in INTENTIONAL_OMISSION_SHAPES
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_scope": "canonical_finalized_fem_evidence_shapes",
        "advisory_only": True,
        "projection_candidate_count": candidate_count,
        "projected_fallback_count": projected_count,
        "unprojected_fallback_count": candidate_count - projected_count,
        "projection_coverage_rate": projected_count / candidate_count if candidate_count else 0.0,
        "coverage_by": {
            "fallback_kind": _coverage_by(rows, "fallback_kind"),
            "owner_bucket": _coverage_by(rows, "owner_bucket"),
            "diegetic_family": _coverage_by(rows, "diegetic_family"),
            "realization_family": _coverage_by(rows, "realization_family"),
        },
        "projected_shapes": projected_shapes,
        "unprojected_shapes": unprojected_shapes,
        "intentional_omissions_excluded_from_denominator": intentional_omissions,
        "notes": [
            "Coverage is over canonical evidence shapes, not observed runtime incidence.",
            "The audit invokes build_fem_runtime_lineage_events without modifying projection rules.",
            "The <unprojected> bucket is an audit label, not a new runtime fallback classification.",
            "Family fields remain FEM evidence and are not copied into the runtime-lineage event envelope.",
        ],
    }


def write_projection_coverage_report(report: Mapping[str, Any], output: Path | str) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Deterministic JSON report path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = build_projection_coverage_report()
    output = write_projection_coverage_report(report, args.output)
    print(f"Wrote {output}")
    print(
        "Projection coverage: "
        f"{report['projected_fallback_count']}/{report['projection_candidate_count']} "
        f"({report['projection_coverage_rate']:.2%})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
