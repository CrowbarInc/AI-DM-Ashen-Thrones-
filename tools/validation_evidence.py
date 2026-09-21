"""Shared packet model, deterministic selection, and rendering for behavioral evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "validation_evidence_packet.v1"
CLAIM_TYPES = (
    "structural_evidence",
    "runtime_evidence",
    "semantic_behavioral_evidence",
    "human_realism_evidence",
    "stress_test_evidence",
    "human_reviewed_evidence",
)
INPUT_CLASSIFICATIONS = (
    "representative_player_behavior",
    "boundary_case",
    "stress_probe",
    "synthetic_positive_control",
    "synthetic_negative_control",
    "human_captured",
    "runtime_discovered",
    "classification_uncertain_human_review",
)
REVIEW_STATUSES = ("UNREVIEWED", "HUMAN_ACCEPTED", "HUMAN_REJECTED", "HUMAN_AMBIGUOUS")
EVIDENCE_CATEGORIES = (
    "representative_success",
    "boundary_success",
    "representative_failure",
    "severe_worst_failure",
    "evaluator_disagreement",
    "unexpected_unclassified",
    "stress_probe",
)


def _diagnostic_score(example: Mapping[str, Any]) -> int:
    diagnostic = example.get("diagnostic_result")
    if isinstance(diagnostic, Mapping):
        try:
            return int(diagnostic.get("score") or 0)
        except (TypeError, ValueError):
            return 0
    automated = example.get("automated_evaluation")
    if isinstance(automated, Mapping):
        overall = automated.get("overall")
        if isinstance(overall, Mapping):
            try:
                return int(overall.get("score") or 0)
            except (TypeError, ValueError):
                return 0
    return 0


def _mandatory_failure_count(example: Mapping[str, Any]) -> int:
    gates = example.get("mandatory_gates")
    if not isinstance(gates, Mapping):
        return 0
    return sum(1 for gate in gates.values() if isinstance(gate, Mapping) and gate.get("status") == "FAIL")


def _has_input_class(example: Mapping[str, Any], value: str) -> bool:
    classes = example.get("player_input_classification")
    return isinstance(classes, list) and value in classes


def _is_automated_pass(example: Mapping[str, Any]) -> bool:
    semantic = example.get("semantic_result")
    if semantic is not None:
        return semantic == "PASS"
    automated = example.get("automated_evaluation")
    if isinstance(automated, Mapping):
        overall = automated.get("overall")
        return bool(overall.get("passed")) if isinstance(overall, Mapping) else False
    return False


def _is_failure(example: Mapping[str, Any]) -> bool:
    return example.get("semantic_result") in {"FAIL", "INVALID_RUN"} or example.get("human_review", {}).get(
        "status"
    ) == "HUMAN_REJECTED"


def _first(examples: Sequence[Mapping[str, Any]], predicate: Any) -> Mapping[str, Any] | None:
    return next((example for example in examples if predicate(example)), None)


def select_evidence(examples: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Apply stable documented selectors; input order is source run then turn index."""
    ordered = list(examples)
    selectors: dict[str, tuple[str, Mapping[str, Any] | None]] = {
        "representative_success": (
            "first automated PASS labeled representative_player_behavior and not HUMAN_REJECTED/HUMAN_AMBIGUOUS",
            _first(
                ordered,
                lambda e: _is_automated_pass(e)
                and _has_input_class(e, "representative_player_behavior")
                and e.get("human_review", {}).get("status") not in {"HUMAN_REJECTED", "HUMAN_AMBIGUOUS"},
            ),
        ),
        "boundary_success": (
            "first automated PASS or HUMAN_ACCEPTED example labeled boundary_case",
            _first(
                ordered,
                lambda e: _has_input_class(e, "boundary_case")
                and (_is_automated_pass(e) or e.get("human_review", {}).get("status") == "HUMAN_ACCEPTED")
                and e.get("human_review", {}).get("status") not in {"HUMAN_REJECTED", "HUMAN_AMBIGUOUS"},
            ),
        ),
        "representative_failure": (
            "first failure labeled representative_player_behavior",
            _first(ordered, lambda e: _is_failure(e) and _has_input_class(e, "representative_player_behavior")),
        ),
        "severe_worst_failure": (
            "maximum INVALID_RUN, mandatory-gate failure count, then lowest diagnostic score; source order breaks ties",
            max(
                (e for e in ordered if _is_failure(e)),
                key=lambda e: (
                    int(e.get("semantic_result") == "INVALID_RUN"),
                    _mandatory_failure_count(e),
                    -_diagnostic_score(e),
                    -ordered.index(e),
                ),
                default=None,
            ),
        ),
        "evaluator_disagreement": (
            "first example with explicit evaluator_disagreement.present=true",
            _first(ordered, lambda e: bool(e.get("evaluator_disagreement", {}).get("present"))),
        ),
        "unexpected_unclassified": (
            "first HUMAN_AMBIGUOUS or unexpected_behavior example",
            _first(
                ordered,
                lambda e: e.get("human_review", {}).get("status") == "HUMAN_AMBIGUOUS"
                or bool(e.get("unexpected_behavior")),
            ),
        ),
        "stress_probe": (
            "first example labeled stress_probe",
            _first(ordered, lambda e: _has_input_class(e, "stress_probe")),
        ),
    }
    selected: dict[str, dict[str, Any]] = {}
    for category in EVIDENCE_CATEGORIES:
        rule, example = selectors[category]
        selected[category] = {
            "selection_rule": rule,
            "status": "SELECTED" if example else "NO_EXAMPLE_OBSERVED",
            "example_id": example.get("example_id") if example else None,
            "statement": None if example else "No example observed in this campaign.",
        }
    return selected


def validate_packet(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be validation_evidence_packet.v1")
    if packet.get("evidence_scope") == "structural_only" and "semantic_behavioral_evidence" in (
        packet.get("claim_types") or []
    ):
        errors.append("structural-only packet cannot claim semantic behavioral evidence")
    for claim in packet.get("claim_types") or []:
        if claim not in CLAIM_TYPES:
            errors.append(f"unknown claim type: {claim}")
    examples = packet.get("examples")
    if not isinstance(examples, list):
        return errors + ["examples must be a list"]
    seen: set[str] = set()
    required = (
        "example_id",
        "scenario_run_id",
        "turn_index",
        "player_input",
        "player_input_classification",
        "exact_gm_output",
        "runtime_validity",
        "source_artifact_path",
        "human_review",
    )
    for idx, example in enumerate(examples):
        if not isinstance(example, Mapping):
            errors.append(f"examples[{idx}] must be an object")
            continue
        for key in required:
            if key not in example:
                errors.append(f"examples[{idx}] missing {key}")
        example_id = str(example.get("example_id") or "")
        if example_id in seen:
            errors.append(f"duplicate example_id: {example_id}")
        seen.add(example_id)
        for classification in example.get("player_input_classification") or []:
            if classification not in INPUT_CLASSIFICATIONS:
                errors.append(f"{example_id}: unknown input classification {classification}")
        review = example.get("human_review")
        if not isinstance(review, Mapping) or review.get("status") not in REVIEW_STATUSES:
            errors.append(f"{example_id}: invalid human review status")
    selected = packet.get("selected_evidence")
    if not isinstance(selected, Mapping):
        errors.append("selected_evidence must be an object")
    else:
        for category in EVIDENCE_CATEGORIES:
            if category not in selected:
                errors.append(f"selected_evidence missing {category}")
    return errors


def build_packet(
    *,
    campaign: Mapping[str, Any],
    claim_types: Sequence[str],
    examples: Sequence[Mapping[str, Any]],
    missing_concepts: Sequence[Mapping[str, Any]],
    limitations: Sequence[str],
    evidence_scope: str = "behavioral",
) -> dict[str, Any]:
    rows = [dict(example) for example in examples]
    packet = {
        "schema_version": SCHEMA_VERSION,
        "evidence_scope": evidence_scope,
        "campaign": dict(campaign),
        "claim_types": list(claim_types),
        "examples": rows,
        "selected_evidence": select_evidence(rows),
        "missing_concepts_future_capabilities": [dict(row) for row in missing_concepts],
        "limitations_and_unproven_claims": list(limitations),
    }
    errors = validate_packet(packet)
    if errors:
        raise ValueError("invalid evidence packet: " + "; ".join(errors))
    return packet


def render_summary(packet: Mapping[str, Any]) -> str:
    campaign = packet["campaign"]
    examples = {row["example_id"]: row for row in packet["examples"]}
    counts = Counter(str(row.get("semantic_result") or row.get("historical_result") or "UNAVAILABLE") for row in examples.values())
    lines = [
        f"# Validation Evidence: {campaign['campaign_id']}",
        "",
        "> **No important player-facing PASS without inspectable behavioral evidence.**",
        "",
        f"What was tested: {campaign['what_was_tested']}",
        f"Runtime path: {campaign['runtime_path']}",
        f"GM boundary: {campaign['gm_boundary']}",
        f"Player inputs: {campaign['player_input_mode']}",
        f"Runs / turns: {campaign['run_count']} / {campaign['turn_count']}",
        f"Automated conclusion: {campaign['automated_conclusion']}",
        f"Result counts: `{json.dumps(dict(sorted(counts.items())), sort_keys=True)}`",
        "",
        "## Selected Evidence",
        "",
    ]
    labels = {
        "representative_success": "Representative Success",
        "boundary_success": "Boundary Success",
        "representative_failure": "Representative Failure",
        "severe_worst_failure": "Severe / Worst Failure",
        "evaluator_disagreement": "Evaluator Disagreement",
        "unexpected_unclassified": "Unexpected / Unclassified Behavior",
        "stress_probe": "Stress Probe",
    }
    for category in EVIDENCE_CATEGORIES:
        selection = packet["selected_evidence"][category]
        lines.extend([f"### {labels[category]}", "", f"Selection: {selection['selection_rule']}", ""])
        if selection["status"] != "SELECTED":
            lines.extend(["No example observed in this campaign.", ""])
            continue
        example = examples[selection["example_id"]]
        lines.extend(
            [
                f"Example: `{example['example_id']}`",
                f"Source: `{example['source_artifact_path']}`",
                f"Run / turn: `{example['scenario_run_id']}` / `{example['turn_index']}`",
                f"Input classification: `{', '.join(example['player_input_classification'])}`",
                f"Selection rationale: {example.get('simulated_player_rationale') or 'Not applicable.'}",
                "",
                "Player input (exact):",
                "",
                f"> {str(example['player_input']).replace(chr(10), chr(10) + '> ')}",
                "",
                "GM output (exact):",
                "",
                f"> {str(example['exact_gm_output']).replace(chr(10), chr(10) + '> ')}",
                "",
                f"Automated result: `{example.get('semantic_result') or example.get('historical_result') or 'UNAVAILABLE'}`",
                f"Mandatory gates: `{json.dumps(example.get('mandatory_gates'), ensure_ascii=False, sort_keys=True)}`",
                f"Diagnostic result: `{json.dumps(example.get('diagnostic_result'), ensure_ascii=False, sort_keys=True)}`",
                f"Runtime validity: `{json.dumps(example.get('runtime_validity'), ensure_ascii=False, sort_keys=True)}`",
                f"Continuation: `{json.dumps(example.get('continuation_decision'), ensure_ascii=False, sort_keys=True)}`",
                f"Human review: `{example['human_review']['status']}` - {example['human_review'].get('rationale') or 'No rationale recorded.'}",
                f"Evaluator disagreement: `{json.dumps(example.get('evaluator_disagreement'), ensure_ascii=False, sort_keys=True)}`",
                "",
            ]
        )
    disagreements = [row for row in examples.values() if row.get("evaluator_disagreement", {}).get("present")]
    lines.extend(["## All Evaluator Disagreements", ""])
    if not disagreements:
        lines.extend(["No example observed in this campaign.", ""])
    for example in disagreements:
        lines.extend(
            [
                f"### {example['example_id']}",
                "",
                f"Source: `{example['source_artifact_path']}`",
                f"Player classification: `{', '.join(example['player_input_classification'])}`",
                f"Player (exact): {example['player_input']}",
                f"GM (exact): {example['exact_gm_output']}",
                f"Original automated result: `{example.get('semantic_result') or example.get('historical_result') or 'UNAVAILABLE'}`",
                f"Original gates: `{json.dumps(example.get('mandatory_gates'), ensure_ascii=False, sort_keys=True)}`",
                f"Human review: `{example['human_review']['status']}` - {example['human_review'].get('rationale')}",
                f"History: `{json.dumps(example.get('evaluator_disagreement'), ensure_ascii=False, sort_keys=True)}`",
                "",
            ]
        )
    lines.extend(["## Missing Concepts / Future Capabilities", ""])
    for concept in packet.get("missing_concepts_future_capabilities") or []:
        lines.append(f"- **{concept['name']}**: {concept['evidence']} Status: {concept['status']}.")
    lines.extend(["", "## What This Does Not Prove", ""])
    lines.extend(f"- {item}" for item in packet.get("limitations_and_unproven_claims") or [])
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "Human review is recorded beside automated evaluation and never rewrites the historical result.",
            "The manifest contains every exact exchange and full gate evidence; this summary exposes the deterministic selections.",
            "",
        ]
    )
    return "\n".join(lines)


def write_packet(output_dir: Path, packet: Mapping[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (output_dir / "evidence_summary.md").write_text(render_summary(packet), encoding="utf-8")
