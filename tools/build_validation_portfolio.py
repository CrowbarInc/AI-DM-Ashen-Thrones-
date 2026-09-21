from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "validation" / "validation_family_registry.json"
FAILURES_PATH = ROOT / "artifacts" / "validation_portfolio" / "current_failure_classification.json"
SUMMARY_PATH = ROOT / "artifacts" / "validation_portfolio" / "current_failure_summary.md"
REGISTRY_VIEW_PATH = ROOT / "docs" / "validation_family_registry.md"

REQUIRED_FAMILY_FIELDS = {
    "family_id", "name", "purpose", "implementation", "invocation",
    "approximate_case_count", "origin", "owner", "runtime_path",
    "production_code_exercised", "ai_output", "determinism", "test_doubles",
    "evidence", "pass_meaning", "fail_meaning", "claim_classes",
    "current_authority", "recommended_authority", "ci_status", "gates",
    "overlap", "reliability_issues", "maintenance_burden",
    "human_review", "evidence_standard", "health", "disposition",
    "confidence", "rationale",
}
DISPOSITIONS = {"RETAIN", "CONSOLIDATE", "MODERNIZE", "RECLASSIFY", "QUARANTINE", "RETIRE"}
AUTHORITIES = {
    "RELEASE_GATE", "CAMPAIGN_GATE", "SUPPORTING_EVIDENCE", "DIAGNOSTIC",
    "WARNING", "CALIBRATION_TOOL", "MANUAL_REVIEW", "DEVELOPMENT_UTILITY",
    "HISTORICAL_ONLY",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(registry: dict[str, Any], failures: dict[str, Any]) -> None:
    ids: set[str] = set()
    for family in registry["families"]:
        missing = REQUIRED_FAMILY_FIELDS - family.keys()
        if missing:
            raise ValueError(f"{family.get('family_id', '<unknown>')} missing {sorted(missing)}")
        family_id = family["family_id"]
        if family_id in ids:
            raise ValueError(f"duplicate family_id: {family_id}")
        ids.add(family_id)
        if family["disposition"] not in DISPOSITIONS:
            raise ValueError(f"invalid disposition for {family_id}")
        if family["current_authority"] not in AUTHORITIES or family["recommended_authority"] not in AUTHORITIES:
            raise ValueError(f"invalid authority for {family_id}")
        if not family["claim_classes"] or not family["rationale"]:
            raise ValueError(f"claim boundary/rationale missing for {family_id}")
        if family["disposition"] == "RETIRE" and not family.get("evidence_loss_risk"):
            raise ValueError(f"RETIRE family lacks evidence_loss_risk: {family_id}")
        if family["disposition"] == "CONSOLIDATE" and not family.get("surviving_authority"):
            raise ValueError(f"CONSOLIDATE family lacks surviving_authority: {family_id}")
        if family["disposition"] == "MODERNIZE" and not family.get("preserved_purpose"):
            raise ValueError(f"MODERNIZE family lacks preserved_purpose: {family_id}")
        if family["disposition"] == "QUARANTINE" and not family.get("unresolved_question"):
            raise ValueError(f"QUARANTINE family lacks unresolved_question: {family_id}")

    observed = failures["observed_failure_count"]
    rows = failures["failures"]
    if observed != len(rows):
        raise ValueError(f"failure count mismatch: observed={observed}, rows={len(rows)}")
    unknown = sorted({row["family_id"] for row in rows} - ids)
    if unknown:
        raise ValueError(f"failures mapped to unknown families: {unknown}")
    if any(not row.get("classification") or not row.get("confidence") for row in rows):
        raise ValueError("failure classification/confidence cannot be empty")

    architecture_ids = {layer_id for layer in registry["target_architecture"] for layer_id in layer["authorities"]}
    if architecture_ids - ids:
        raise ValueError(f"target architecture references unknown families: {sorted(architecture_ids - ids)}")


def render_registry(registry: dict[str, Any]) -> str:
    families = registry["families"]
    dispositions = Counter(family["disposition"] for family in families)
    lines = [
        "# Validation Family Registry",
        "",
        f"Generated from `data/validation/validation_family_registry.json`. Families: **{len(families)}**.",
        "",
        "## Disposition summary",
        "",
        "| Disposition | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {dispositions[name]} |" for name in sorted(DISPOSITIONS))
    lines += ["", "## Families", "", "| ID | Family | Claims | Current -> proposed authority | Disposition | Confidence |", "|---|---|---|---|---|---|"]
    for family in families:
        claims = ", ".join(family["claim_classes"])
        lines.append(
            f"| `{family['family_id']}` | {family['name']} | {claims} | "
            f"{family['current_authority']} -> {family['recommended_authority']} | "
            f"{family['disposition']} | {family['confidence']} |"
        )
    lines += ["", "The JSON registry is authoritative and contains complete claim boundaries, risks, overlaps, and rationale.", ""]
    return "\n".join(lines)


def render_failure_summary(failures: dict[str, Any]) -> str:
    rows = failures["failures"]
    classes = Counter(row["classification"] for row in rows)
    confidence = Counter(row["confidence"] for row in rows)
    families = Counter(row["family_id"] for row in rows)
    lines = [
        "# Current Failure Classification",
        "",
        f"Observed command: `{failures['command']}`",
        "",
        f"Observed result: **{len(rows)} failures** from **{failures['collected_cases']} collected cases**.",
        "",
        "## By likely cause",
        "",
        "| Classification | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {count} |" for name, count in sorted(classes.items()))
    lines += ["", "## By confidence", "", "| Confidence | Count |", "|---|---:|"]
    lines.extend(f"| {name} | {count} |" for name, count in sorted(confidence.items()))
    lines += ["", "## By validation family", "", "| Family | Count |", "|---|---:|"]
    lines.extend(f"| `{name}` | {count} |" for name, count in sorted(families.items()))
    lines += [
        "", "## Interpretation", "",
        failures["interpretation"], "",
        "This is an audit classification, not a waiver. No failing test was disabled, repaired, or silently downgraded.", "",
    ]
    return "\n".join(lines)


def build() -> None:
    registry = load_json(REGISTRY_PATH)
    failures = load_json(FAILURES_PATH)
    validate(registry, failures)
    REGISTRY_VIEW_PATH.write_text(render_registry(registry), encoding="utf-8")
    SUMMARY_PATH.write_text(render_failure_summary(failures), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and render the validation portfolio registry.")
    parser.parse_args()
    build()
    print(REGISTRY_VIEW_PATH.relative_to(ROOT))
    print(SUMMARY_PATH.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
