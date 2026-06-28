"""BS3 canonical semantic replacement attribution contract.

**Authority (CG-5):** attribution-contract-owned replacement paths, repair-kind
union/aliases, mutation-classification core union/aliases, normalization helpers,
and attribution record validation.

**Imports for validation (does not own):** repair-kind runtime/producer subsets,
emission sublayers, source-family tags, and owner-bucket mirrors from
``tests.failure_classification_contract`` (those subsets remain replay-contract-owned).

**Does not own:** failure categories, drift buckets, investigation routing,
dashboard evidence, recurrence key formula, or runtime FEM/lineage emission.

Registries:
``docs/audits/CG_attribution_contract_registry.md`` (attribution boundary),
``docs/audits/CG_failure_classification_authority_registry.md`` (failure vs runtime).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from tests.failure_classification_contract import (
    ALLOWED_EMISSION_SUBLAYERS,
    ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS,
    ALLOWED_PRODUCER_REPAIR_KINDS,
    ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS,
    ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS,
    ALLOWED_SOURCE_FAMILY_TAGS,
    ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS,
    LEGACY_RESPONSE_TYPE_REPAIR_KINDS,
)

# --- Canonical record shape ---

REQUIRED_ATTRIBUTION_FIELDS: tuple[str, ...] = (
    "owner_bucket",
    "source_family",
    "repair_kind",
    "recurrence_key",
    "mutation_classification",
)

REPLACEMENT_PATH_VISIBILITY: str = "visibility replacement"
REPLACEMENT_PATH_FIRST_MENTION: str = "first mention replacement"
REPLACEMENT_PATH_REFERENTIAL: str = "referential replacement"
REPLACEMENT_PATH_SEALED: str = "sealed replacement"
REPLACEMENT_PATH_RESPONSE_TYPE: str = "response type replacement"
REPLACEMENT_PATH_SANITIZER: str = "sanitizer replacement"
REPLACEMENT_PATH_REPAIR_MUTATION: str = "repair mutation"
REPLACEMENT_PATH_OPENING_FALLBACK: str = "opening fallback"
REPLACEMENT_PATH_STRICT_SOCIAL: str = "strict social replacement"

REPLACEMENT_PATHS: tuple[str, ...] = (
    REPLACEMENT_PATH_VISIBILITY,
    REPLACEMENT_PATH_FIRST_MENTION,
    REPLACEMENT_PATH_REFERENTIAL,
    REPLACEMENT_PATH_SEALED,
    REPLACEMENT_PATH_RESPONSE_TYPE,
    REPLACEMENT_PATH_SANITIZER,
    REPLACEMENT_PATH_REPAIR_MUTATION,
    REPLACEMENT_PATH_OPENING_FALLBACK,
    REPLACEMENT_PATH_STRICT_SOCIAL,
)

ATTRIBUTION_ORIGIN_DIRECT: str = "direct"
ATTRIBUTION_ORIGIN_PROJECTED: str = "projected"
ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED: str = "classifier_inferred"

ALLOWED_ATTRIBUTION_ORIGINS: frozenset[str] = frozenset(
    {
        ATTRIBUTION_ORIGIN_DIRECT,
        ATTRIBUTION_ORIGIN_PROJECTED,
        ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED,
    }
)

ALLOWED_OPENING_REPAIR_KINDS: frozenset[str] = frozenset(
    {
        "opening_deterministic_fallback",
        "opening_deterministic_fallback_failed_closed",
    }
)

ALLOWED_REPAIR_KINDS: frozenset[str] = (
    ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS
    | LEGACY_RESPONSE_TYPE_REPAIR_KINDS
    | ALLOWED_PRODUCER_REPAIR_KINDS
    | ALLOWED_OPENING_REPAIR_KINDS
)

ALLOWED_MUTATION_CLASSIFICATION_CORE: frozenset[str] = frozenset(
    {
        "fallback_mutation",
        "speaker_repair_mutation",
        "continuity_repair_mutation",
        "response_type_repair_mutation",
        "sanitizer_mutation",
        "final_emission_mutation",
        "repair_only_mutation",
        "visibility_replacement_mutation",
        "first_mention_replacement_mutation",
        "referential_clarity_replacement_mutation",
        "referential_clarity_local_substitution_mutation",
        "sealed_replacement_mutation",
        "fallback_behavior_repair_mutation",
        "answer_completeness_repair_mutation",
        "response_delta_repair_mutation",
        "social_response_structure_repair_mutation",
        "narrative_authenticity_repair_mutation",
        "tone_escalation_repair_mutation",
        "anti_railroading_repair_mutation",
        "context_separation_repair_mutation",
        "player_facing_narration_purity_repair_mutation",
        "answer_shape_primacy_repair_mutation",
        "narrative_authority_repair_mutation",
    }
)

ALLOWED_MUTATION_CLASSIFICATIONS: frozenset[str] = (
    ALLOWED_MUTATION_CLASSIFICATION_CORE | ALLOWED_EMISSION_SUBLAYERS
)

ALLOWED_OWNER_BUCKETS: frozenset[str] = (
    ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS
    | ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS
    | ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS
)

# --- Deprecated values, aliases, normalization ---

DEPRECATED_REPAIR_KINDS: frozenset[str] = frozenset(LEGACY_RESPONSE_TYPE_REPAIR_KINDS)

DEPRECATED_FALLBACK_KIND_ALIASES: dict[str, str] = {
    "visibility_or_scene_replacement": "visibility_hard_replacement",
}

REPAIR_KIND_ALIASES: dict[str, str] = {
    "response_type_contract_repair": "answer_upstream_prepared_repair",
}

MUTATION_CLASSIFICATION_ALIASES: dict[str, str] = {
    "strict_social_replacement": "strict_social_replacement",
}

# Values observed in lineage/speaker paths but outside repair_kind contract.
LINEAGE_ONLY_REPAIR_KINDS: frozenset[str] = frozenset(
    {
        "canonical_rewrite",
        "local_rebind",
        "dialogue_enforcement_skipped_due_to_social_suppression",
    }
)

RECURRENCE_KEY_MIN_LENGTH: int = 5

# --- Maturity snapshot baselines (BS1 / BS5 / BS4 frozen; BS3 computed live) ---

BS1_MATURITY_SNAPSHOT: dict[str, Any] = {
    "coverage_score_pct": 5.36,
    "contract_compliance_score_pct": 40.3,
    "taxonomy_consistency_score_pct": 72.0,
    "resolved_complete_records": 3,
    "total_records": 56,
}

BS5_MATURITY_SNAPSHOT: dict[str, Any] = {
    "coverage_score_pct": 85.71,
    "contract_compliance_score_pct": 100.0,
    "taxonomy_consistency_score_pct": 100.0,
    "resolved_complete_records": 48,
    "total_records": 56,
}

# --- CO96 attribution program closeout governance (policy only; no runtime effect) ---

ATTRIBUTION_MATURITY_PROGRAM_STATUS: str = "closed"

ATTRIBUTION_MATURITY_PRIMARY_KPI: str = "resolved_completeness_pct"

ATTRIBUTION_STRICT_COMPLETENESS_ROLE: str = "architectural_diagnostic"

ATTRIBUTION_GOVERNANCE_RULES: tuple[str, ...] = (
    "Resolved completeness is the primary production KPI.",
    "Strict completeness is an architectural diagnostic only.",
    "Replay-derived fields are not production-stamp candidates.",
    "Production stamps must never duplicate replay semantics solely to improve metrics.",
    "Read-side projection remains bounded by existing production evidence.",
)

ATTRIBUTION_PROGRAM_CLOSEOUT: dict[str, Any] = {
    "program_status": ATTRIBUTION_MATURITY_PROGRAM_STATUS,
    "primary_kpi": ATTRIBUTION_MATURITY_PRIMARY_KPI,
    "strict_completeness_role": ATTRIBUTION_STRICT_COMPLETENESS_ROLE,
    "resolved_completeness_pct": BS5_MATURITY_SNAPSHOT["coverage_score_pct"],
    "resolved_complete_records": BS5_MATURITY_SNAPSHOT["resolved_complete_records"],
    "total_records": BS5_MATURITY_SNAPSHOT["total_records"],
    "strict_completeness_pct": 0.0,
    "intentional_gap_mutation_classification_gate_outcome": 8,
    "closeout_audit": "docs/audits/CO96_attribution_program_closeout.md",
}

BS4_MATURITY_SNAPSHOT: dict[str, Any] = {
    "coverage_score_pct": 50.0,
    "contract_compliance_score_pct": 100.0,
    "taxonomy_consistency_score_pct": 100.0,
    "resolved_complete_records": 28,
    "total_records": 56,
}


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of a single attribution field validation."""

    field: str
    value: str | None
    valid: bool
    normalized: str | None
    reason: str | None = None


def normalize_token(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_repair_kind(value: Any) -> str | None:
    token = normalize_token(value)
    if token is None:
        return None
    lowered = token.lower()
    return REPAIR_KIND_ALIASES.get(lowered, lowered)


def normalize_mutation_classification(value: Any) -> str | None:
    token = normalize_token(value)
    if token is None:
        return None
    return MUTATION_CLASSIFICATION_ALIASES.get(token, token)


def normalize_fallback_kind(value: Any) -> str | None:
    token = normalize_token(value)
    if token is None:
        return None
    return DEPRECATED_FALLBACK_KIND_ALIASES.get(token, token)


def validate_owner_bucket(value: Any) -> ValidationResult:
    normalized = normalize_token(value)
    if normalized is None:
        return ValidationResult("owner_bucket", None, False, None, "empty")
    valid = normalized in ALLOWED_OWNER_BUCKETS
    return ValidationResult(
        "owner_bucket",
        normalized,
        valid,
        normalized if valid else None,
        None if valid else "not_in_allowed_owner_buckets",
    )


def validate_source_family(value: Any) -> ValidationResult:
    normalized = normalize_token(value)
    if normalized is None:
        return ValidationResult("source_family", None, False, None, "empty")
    valid = normalized in ALLOWED_SOURCE_FAMILY_TAGS
    return ValidationResult(
        "source_family",
        normalized,
        valid,
        normalized if valid else None,
        None if valid else "not_in_allowed_source_family_tags",
    )


def validate_repair_kind(value: Any) -> ValidationResult:
    normalized = normalize_repair_kind(value)
    if normalized is None:
        return ValidationResult("repair_kind", None, False, None, "empty")
    valid = normalized in ALLOWED_REPAIR_KINDS
    return ValidationResult(
        "repair_kind",
        normalized,
        valid,
        normalized if valid else None,
        None if valid else "not_in_allowed_repair_kinds",
    )


def validate_mutation_classification(value: Any) -> ValidationResult:
    normalized = normalize_mutation_classification(value)
    if normalized is None:
        return ValidationResult("mutation_classification", None, False, None, "empty")
    valid = normalized in ALLOWED_MUTATION_CLASSIFICATIONS
    return ValidationResult(
        "mutation_classification",
        normalized,
        valid,
        normalized if valid else None,
        None if valid else "not_in_allowed_mutation_classifications",
    )


def validate_recurrence_key(value: Any) -> ValidationResult:
    normalized = normalize_token(value)
    if normalized is None:
        return ValidationResult("recurrence_key", None, False, None, "empty")
    valid = ":" in normalized and len(normalized) >= RECURRENCE_KEY_MIN_LENGTH
    return ValidationResult(
        "recurrence_key",
        normalized,
        valid,
        normalized if valid else None,
        None if valid else "invalid_recurrence_key_shape",
    )


def validate_replacement_path(value: Any) -> ValidationResult:
    normalized = normalize_token(value)
    if normalized is None:
        return ValidationResult("replacement_path", None, False, None, "empty")
    valid = normalized in REPLACEMENT_PATHS
    return ValidationResult(
        "replacement_path",
        normalized,
        valid,
        normalized if valid else None,
        None if valid else "not_in_replacement_paths",
    )


def validate_attribution_origin(value: Any) -> ValidationResult:
    normalized = normalize_token(value)
    if normalized is None:
        return ValidationResult("attribution_origin", None, False, None, "empty")
    valid = normalized in ALLOWED_ATTRIBUTION_ORIGINS
    return ValidationResult(
        "attribution_origin",
        normalized,
        valid,
        normalized if valid else None,
        None if valid else "not_in_allowed_attribution_origins",
    )


def is_taxonomy_valid(field: str, value: str | None) -> bool:
    validators = {
        "owner_bucket": validate_owner_bucket,
        "source_family": validate_source_family,
        "repair_kind": validate_repair_kind,
        "mutation_classification": validate_mutation_classification,
        "recurrence_key": validate_recurrence_key,
    }
    validator = validators.get(field)
    if validator is None:
        return bool(value)
    return validator(value).valid


def validate_attribution_field(field: str, value: Any) -> ValidationResult:
    validators = {
        "owner_bucket": validate_owner_bucket,
        "source_family": validate_source_family,
        "repair_kind": validate_repair_kind,
        "mutation_classification": validate_mutation_classification,
        "recurrence_key": validate_recurrence_key,
        "replacement_path": validate_replacement_path,
    }
    validator = validators.get(field)
    if validator is None:
        token = normalize_token(value)
        return ValidationResult(field, token, token is not None, token, "unknown_field")
    return validator(value)


def audit_field_values(
    field: str,
    values: Sequence[Any],
) -> dict[str, Any]:
    """Return compliance counts for a sequence of raw field values."""
    compliant = 0
    non_compliant: list[str] = []
    deprecated_hits: list[str] = []
    for raw in values:
        token = normalize_token(raw)
        if token is None:
            continue
        if field == "repair_kind" and token in DEPRECATED_REPAIR_KINDS:
            deprecated_hits.append(token)
        result = validate_attribution_field(field, token)
        if result.valid:
            compliant += 1
        else:
            non_compliant.append(token)
    return {
        "field": field,
        "compliant": compliant,
        "non_compliant": sorted(set(non_compliant)),
        "deprecated": sorted(set(deprecated_hits)),
        "total_observed": compliant + len(set(non_compliant)),
    }


def _collect_corpus_field_values() -> dict[str, list[Any]]:
    from tests.helpers.replacement_attribution_inventory import build_baseline_attribution_corpus

    records = build_baseline_attribution_corpus()
    collected: dict[str, list[Any]] = {field: [] for field in REQUIRED_ATTRIBUTION_FIELDS}
    collected["replacement_path"] = []
    for record in records:
        for field in REQUIRED_ATTRIBUTION_FIELDS:
            collected[field].append(record.get(field))
        collected["replacement_path"].append(record.get("replacement_path"))
        for field, origin in (record.get("attribution_origin") or {}).items():
            collected.setdefault(f"origin:{field}", []).append(origin)
    return collected


def _collect_lineage_field_values() -> dict[str, list[Any]]:
    from game.final_emission_replay_projection import build_fem_runtime_lineage_events
    from tests.helpers.replacement_attribution_inventory import baseline_attribution_fem_fixtures

    collected: dict[str, list[Any]] = {
        "repair_kind": [],
        "recurrence_key": [],
        "mutation_classification": [],
        "owner_bucket": [],
        "fallback_kind": [],
    }
    for fem in baseline_attribution_fem_fixtures():
        for event in build_fem_runtime_lineage_events(fem):
            collected["repair_kind"].append(event.get("repair_kind"))
            collected["recurrence_key"].append(event.get("recurrence_key"))
            collected["mutation_classification"].append(event.get("mutation_kind"))
            collected["owner_bucket"].append(event.get("fallback_owner_bucket"))
            collected["fallback_kind"].append(event.get("fallback_kind"))
    return collected


def _collect_classifier_field_values() -> dict[str, list[Any]]:
    from tests.helpers.failure_classifier import classify_replay_failure
    from tests.helpers.replacement_attribution_inventory import baseline_attribution_classifier_inputs

    collected: dict[str, list[Any]] = {
        "source_family": [],
        "repair_kind": [],
        "owner_bucket": [],
        "mutation_classification": [],
    }
    for observed, drift_row in baseline_attribution_classifier_inputs():
        for row in classify_replay_failure(
            scenario_id="bs3_contract",
            turn_index=0,
            observed_turn=observed,
            drift_rows=[drift_row],
        ):
            collected["source_family"].append(row.get("source_family"))
            collected["repair_kind"].append(row.get("repair_kind"))
            for bucket_field in (
                "opening_fallback_owner_bucket",
                "sealed_fallback_owner_bucket",
                "visibility_fallback_owner_bucket",
            ):
                if row.get(bucket_field):
                    collected["owner_bucket"].append(row.get(bucket_field))
            mutation = row.get("mutation_source") or row.get("emission_sublayer")
            collected["mutation_classification"].append(mutation)
    return collected


def build_contract_compliance_audit() -> dict[str, Any]:
    """Audit attribution contract compliance across inventory layers."""
    corpus_values = _collect_corpus_field_values()
    lineage_values = _collect_lineage_field_values()
    classifier_values = _collect_classifier_field_values()

    layer_audits = {
        "inventory_corpus": {
            field: audit_field_values(field, corpus_values.get(field, []))
            for field in REQUIRED_ATTRIBUTION_FIELDS
        },
        "lineage_projection": {
            "repair_kind": audit_field_values("repair_kind", lineage_values["repair_kind"]),
            "recurrence_key": audit_field_values("recurrence_key", lineage_values["recurrence_key"]),
            "mutation_classification": audit_field_values(
                "mutation_classification", lineage_values["mutation_classification"]
            ),
            "owner_bucket": audit_field_values("owner_bucket", lineage_values["owner_bucket"]),
            "fallback_kind_normalization": {
                "deprecated_aliases": sorted(DEPRECATED_FALLBACK_KIND_ALIASES.keys()),
                "observed": sorted(
                    {
                        normalize_token(v)
                        for v in lineage_values["fallback_kind"]
                        if normalize_token(v)
                    }
                ),
            },
        },
        "failure_classifier": {
            field: audit_field_values(field, classifier_values.get(field, []))
            for field in ("source_family", "repair_kind", "owner_bucket", "mutation_classification")
        },
    }

    taxonomy_sources = {
        "owner_bucket": ["game.final_emission_meta", "tests.helpers.attribution_contract"],
        "source_family": ["tests.failure_classification_contract", "tests.helpers.attribution_contract"],
        "repair_kind": ["tests.failure_classification_contract", "tests.helpers.attribution_contract"],
        "mutation_classification": ["tests.helpers.attribution_contract", "tests.failure_classification_contract"],
        "replacement_path": ["tests.helpers.attribution_contract"],
    }

    return {
        "layers": layer_audits,
        "taxonomy_sources": taxonomy_sources,
        "deprecated": {
            "repair_kinds": sorted(DEPRECATED_REPAIR_KINDS),
            "fallback_kind_aliases": dict(DEPRECATED_FALLBACK_KIND_ALIASES),
            "lineage_only_repair_kinds": sorted(LINEAGE_ONLY_REPAIR_KINDS),
        },
        "normalization": {
            "repair_kind_aliases": dict(REPAIR_KIND_ALIASES),
            "mutation_classification_aliases": dict(MUTATION_CLASSIFICATION_ALIASES),
            "recurrence_key_min_length": RECURRENCE_KEY_MIN_LENGTH,
        },
    }


def calculate_attribution_maturity_scores(
    *,
    records: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute coverage, contract compliance, and taxonomy consistency scores."""
    from tests.helpers.replacement_attribution_inventory import (
        build_baseline_attribution_corpus,
        calculate_attribution_completeness,
    )

    if records is None:
        records = build_baseline_attribution_corpus()
    completeness = calculate_attribution_completeness(records)

    populated = 0
    compliant = 0
    for record in records:
        for field in REQUIRED_ATTRIBUTION_FIELDS:
            value = normalize_token(record.get(field))
            if value is None:
                continue
            populated += 1
            if is_taxonomy_valid(field, value):
                compliant += 1

    contract_compliance_pct = round(100.0 * compliant / populated, 2) if populated else 0.0

    # Taxonomy consistency: attribution contract owns unions; failure contract
    # owns imported subsets (repair kinds, emission sublayers, bucket mirrors).
    consistency_checks = [
        ALLOWED_OWNER_BUCKETS
        == (
            ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS
            | ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS
            | ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS
        ),
        ALLOWED_PRODUCER_REPAIR_KINDS <= ALLOWED_REPAIR_KINDS,
        ALLOWED_RUNTIME_RESPONSE_TYPE_REPAIR_KINDS <= ALLOWED_REPAIR_KINDS,
        ALLOWED_EMISSION_SUBLAYERS <= ALLOWED_MUTATION_CLASSIFICATIONS,
        len(REPLACEMENT_PATHS) == 9,
    ]
    taxonomy_consistency_pct = round(
        100.0 * sum(1 for ok in consistency_checks if ok) / len(consistency_checks),
        2,
    )

    resolved = sum(1 for record in records if not record.get("missing_fields"))

    return {
        "coverage_score_pct": completeness["resolved_completeness_pct"],
        "contract_compliance_score_pct": contract_compliance_pct,
        "taxonomy_consistency_score_pct": taxonomy_consistency_pct,
        "resolved_complete_records": resolved,
        "total_records": len(records),
        "strict_completeness_pct": completeness["strict_completeness_pct"],
        "populated_field_slots": populated,
        "compliant_field_slots": compliant,
    }


def render_bs3_contract_compliance_report_md(
    *,
    audit: Mapping[str, Any],
    maturity: Mapping[str, Any],
) -> str:
    lines = [
        "# BS3 Contract Compliance Report",
        "",
        "> Canonical attribution contract lock — validation and taxonomy audit only.",
        "",
        "## Attribution Maturity Scores",
        "",
        "| Cycle | Coverage | Contract compliance | Taxonomy consistency | Resolved complete |",
        "|---|---:|---:|---:|---:|",
    ]
    for label, snapshot in (
        ("BS1", BS1_MATURITY_SNAPSHOT),
        ("BS5", BS5_MATURITY_SNAPSHOT),
        ("BS4", BS4_MATURITY_SNAPSHOT),
        ("BS3 (live)", maturity),
    ):
        lines.append(
            "| {label} | {cov}% | {comp}% | {tax}% | {resolved}/{total} |".format(
                label=label,
                cov=snapshot["coverage_score_pct"],
                comp=snapshot["contract_compliance_score_pct"],
                tax=snapshot["taxonomy_consistency_score_pct"],
                resolved=snapshot["resolved_complete_records"],
                total=snapshot["total_records"],
            )
        )
    lines.extend(
        [
            "",
            "## Layer Compliance Summary",
            "",
        ]
    )
    for layer_name, layer_data in audit.get("layers", {}).items():
        lines.append(f"### {layer_name}")
        lines.append("")
        if layer_name == "lineage_projection" and "fallback_kind_normalization" in layer_data:
            norm = layer_data["fallback_kind_normalization"]
            lines.append(f"- Deprecated fallback kind aliases: `{norm.get('deprecated_aliases')}`")
            lines.append(f"- Observed normalized fallback kinds: `{norm.get('observed')}`")
            lines.append("")
        for field, stats in layer_data.items():
            if not isinstance(stats, dict) or "compliant" not in stats:
                continue
            lines.append(
                f"- `{stats['field']}`: {stats['compliant']} compliant, "
                f"{len(stats.get('non_compliant') or [])} non-compliant"
            )
            if stats.get("non_compliant"):
                lines.append(f"  - non-compliant values: `{stats['non_compliant']}`")
            if stats.get("deprecated"):
                lines.append(f"  - deprecated values: `{stats['deprecated']}`")
        lines.append("")

    deprecated = audit.get("deprecated") or {}
    lines.extend(
        [
            "## Deprecated Values",
            "",
            f"- Repair kinds (legacy): `{deprecated.get('repair_kinds', [])}`",
            f"- Fallback kind aliases: `{deprecated.get('fallback_kind_aliases', {})}`",
            f"- Lineage-only repair kinds (not in repair_kind contract): `{deprecated.get('lineage_only_repair_kinds', [])}`",
            "",
            "## Normalization Rules",
            "",
            f"- Repair kind aliases: `{ (audit.get('normalization') or {}).get('repair_kind_aliases', {}) }`",
            f"- Recurrence key: must contain `:` and length >= {(audit.get('normalization') or {}).get('recurrence_key_min_length')}",
            "",
            "## Taxonomy Source of Truth",
            "",
        ]
    )
    for field, sources in (audit.get("taxonomy_sources") or {}).items():
        lines.append(f"- `{field}`: {', '.join(sources)}")
    lines.append("")
    return "\n".join(lines)


def write_bs3_contract_compliance_report(
    output_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Generate BS3 contract compliance artifact."""
    audit = build_contract_compliance_audit()
    maturity = calculate_attribution_maturity_scores()
    markdown = render_bs3_contract_compliance_report_md(audit=audit, maturity=maturity)
    target = Path(output_path or "artifacts/bs3_contract_compliance_report.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return audit, maturity, markdown
