"""BY4 — semantic mutation attribution closeout (tests only).

Aggregates BY1 synthetic fixture coverage, BY2 protected corpus measurement,
and BY3 strict-social gap closure into a stable closeout artifact.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from tests.helpers.golden_replay_trend import write_deterministic_json
from tests.helpers.protected_semantic_mutation_measurement import (
    assert_probe_non_interference,
    measure_strict_social_semantic_mutation_corpus,
)
from tests.helpers.semantic_mutation_attribution import (
    CHECKPOINT_FALLBACK_SELECTION_OUTPUT,
    CHECKPOINT_FINAL_EMISSION_EXIT,
    CHECKPOINT_POLICY_OUTPUT,
    CHECKPOINT_SANITIZER_OUTPUT,
    SemanticMutationTraceEntry,
    build_semantic_mutation_trace_record,
    compute_first_source_attribution_rate,
    mutation_text_hash,
    normalize_mutation_text,
)

BY4_REPORT_SCHEMA_VERSION = 1

BY1_FIXTURE_SOURCE = (
    "tests/helpers/semantic_mutation_attribution_closeout.py::build_by1_synthetic_fixture_corpus"
)


def _fixture_entry(
    sequence: int,
    checkpoint_id: str,
    bucket: str,
    source: str,
    before: str,
    after: str,
) -> SemanticMutationTraceEntry:
    before_norm = normalize_mutation_text(before)
    after_norm = normalize_mutation_text(after)
    return SemanticMutationTraceEntry(
        sequence=sequence,
        checkpoint_id=checkpoint_id,
        bucket=bucket,  # type: ignore[arg-type]
        source=source,
        before_normalized=before_norm,
        after_normalized=after_norm,
        before_hash=mutation_text_hash(before_norm),
        after_hash=mutation_text_hash(after_norm),
        normalized_changed=before_norm != after_norm,
    )


def build_by1_synthetic_fixture_corpus() -> list[dict[str, Any]]:
    """Representative BY1 synthetic trace records covering all canonical buckets."""
    return [
        build_semantic_mutation_trace_record(
            [_fixture_entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.enforce", "a", "b")]
        ),
        build_semantic_mutation_trace_record(
            [_fixture_entry(1, CHECKPOINT_SANITIZER_OUTPUT, "sanitizer", "sanitizer.strip", "a", "b")]
        ),
        build_semantic_mutation_trace_record(
            [
                _fixture_entry(
                    1,
                    CHECKPOINT_FALLBACK_SELECTION_OUTPUT,
                    "fallback",
                    "visibility.replace",
                    "a",
                    "b",
                )
            ]
        ),
        build_semantic_mutation_trace_record(
            [
                _fixture_entry(
                    1,
                    "dialogue_plan_subtractive_strip",
                    "repair",
                    "repair.strip",
                    "a",
                    "b",
                )
            ]
        ),
        build_semantic_mutation_trace_record(
            [
                _fixture_entry(
                    1,
                    CHECKPOINT_FINAL_EMISSION_EXIT,
                    "final_emission",
                    "finalize.exit",
                    "a",
                    "b",
                )
            ]
        ),
        build_semantic_mutation_trace_record(
            [
                _fixture_entry(1, CHECKPOINT_POLICY_OUTPUT, "policy", "policy.enforce", "a", "b"),
                _fixture_entry(
                    2,
                    CHECKPOINT_SANITIZER_OUTPUT,
                    "sanitizer",
                    "sanitizer.noop",
                    "b",
                    "b",
                ),
            ]
        ),
        build_semantic_mutation_trace_record([]),
    ]


def measure_by1_synthetic_fixture_coverage() -> dict[str, Any]:
    """Compute BY1 synthetic fixture first-source coverage."""
    corpus = build_by1_synthetic_fixture_corpus()
    agg = compute_first_source_attribution_rate(corpus)
    return {
        "fixture_source": BY1_FIXTURE_SOURCE,
        "total_turns": agg["total_turns"],
        "mutated_turns": agg["mutated_turns"],
        "attributable_first_mutations": agg["attributable_first_mutations"],
        "first_source_coverage_rate": agg["first_source_coverage_rate"],
        "bucket_frequencies": agg["bucket_frequencies"],
        "buckets_covered": sorted(agg["bucket_frequencies"]),
    }


def _remaining_risks(
    *,
    by3_report: Mapping[str, Any],
    by1_coverage: Mapping[str, Any],
) -> list[str]:
    summary = by3_report.get("summary") if isinstance(by3_report.get("summary"), Mapping) else {}
    risks: list[str] = []

    if int(summary.get("semantic_mutation_risk_max") or 0) >= 40:
        risks.append(
            "Representative high-risk turns remain in protected corpus "
            f"(max risk score {summary.get('semantic_mutation_risk_max')})."
        )

    gaps = by3_report.get("attribution_gaps")
    if isinstance(gaps, list) and gaps:
        risks.append(f"{len(gaps)} attribution gap(s) remain in protected replay corpus.")

    remaining = by3_report.get("remaining_by4_candidates")
    if isinstance(remaining, list) and remaining:
        risks.append(f"{len(remaining)} turn(s) flagged for future instrumentation.")

    if float(by1_coverage.get("first_source_coverage_rate") or 0) < 1.0:
        risks.append("BY1 synthetic fixture corpus does not achieve full first-source coverage.")

    risks.extend(
        [
            "Semantic mutation probes are test/replay-only; production runtime does not stamp ordered checkpoints.",
            "Protected replay corpus covers 8 turns across 6 scenarios; live campaign paths may diverge.",
            "Risk score measures attribution completeness, not semantic equivalence of before/after text.",
        ]
    )
    return risks


def _schema_promotion_recommendation(
    *,
    final_summary: Mapping[str, Any],
    by3_report: Mapping[str, Any],
) -> dict[str, Any]:
    gaps = by3_report.get("attribution_gaps")
    gap_count = len(gaps) if isinstance(gaps, list) else 0
    coverage = float(final_summary.get("first_source_coverage_rate") or 0)
    unknown = int(final_summary.get("unknown_first_source_count") or 0)

    promote_now = coverage >= 1.0 and unknown == 0 and gap_count == 0
    return {
        "promote_to_protected_replay_schema_now": False,
        "rationale": (
            "Attribution measurement is stable on the protected corpus with zero gaps and "
            "full first-source coverage, but BY fields remain test-only diagnostics. "
            "Do not promote trace checkpoints or risk scores into protected golden replay "
            "schema until a dedicated cycle validates long-term non-interference, corpus "
            "breadth, and operational need for replay diffs."
        ),
        "measurement_ready_for_future_promotion": promote_now,
        "candidate_fields_if_promoted_later": [
            "first_semantic_mutation_bucket",
            "first_semantic_mutation_source",
            "semantic_mutation_changed_count",
            "semantic_mutation_risk_score",
            "semantic_mutation_risk_band",
        ],
        "defer_fields": [
            "semantic_mutation_trace",
            "first_semantic_mutation_before_hash",
            "first_semantic_mutation_after_hash",
        ],
    }


def build_semantic_mutation_attribution_closeout_report(
    *,
    by1_coverage: Mapping[str, Any],
    by2_report: Mapping[str, Any],
    by3_report: Mapping[str, Any],
    non_interference_verified: bool,
) -> dict[str, Any]:
    """Build stable BY4 closeout JSON payload."""
    by2_summary = by2_report.get("summary") if isinstance(by2_report.get("summary"), Mapping) else {}
    by3_summary = by3_report.get("summary") if isinstance(by3_report.get("summary"), Mapping) else {}
    coverage = (
        by3_report.get("before_after_coverage")
        if isinstance(by3_report.get("before_after_coverage"), Mapping)
        else {}
    )

    final_summary = dict(by3_summary)
    attribution_gaps = by3_report.get("attribution_gaps")
    if not isinstance(attribution_gaps, list):
        attribution_gaps = []

    return {
        "schema_version": BY4_REPORT_SCHEMA_VERSION,
        "closeout": "by4_semantic_mutation_attribution",
        "by1_synthetic_fixture_coverage": dict(by1_coverage),
        "by2_protected_corpus_measurement": {
            "corpus": by2_report.get("corpus"),
            "corpus_scenario_ids": by2_report.get("corpus_scenario_ids"),
            "summary": dict(by2_summary),
            "attribution_gap_count": len(
                by2_report.get("attribution_gaps")
                if isinstance(by2_report.get("attribution_gaps"), list)
                else []
            ),
        },
        "by3_strict_social_gap_closure": {
            "target_turn": coverage.get("target_turn"),
            "gap_closed": coverage.get("gap_closed"),
            "before_by2": coverage.get("before_by2"),
            "after_by3": coverage.get("after_by3"),
            "checkpoints_added": (
                (by3_report.get("by3_instrumentation") or {}).get("checkpoints_added")
                if isinstance(by3_report.get("by3_instrumentation"), Mapping)
                else []
            ),
            "remaining_by4_candidates": by3_report.get("remaining_by4_candidates") or [],
        },
        "final_measurement": {
            "first_source_coverage_rate": final_summary.get("first_source_coverage_rate"),
            "unknown_first_source_count": final_summary.get("unknown_first_source_count"),
            "mutated_turns": final_summary.get("mutated_turns"),
            "attributable_first_mutations": final_summary.get("attributable_first_mutations"),
            "total_turns": final_summary.get("total_turns"),
            "bucket_distribution": final_summary.get("bucket_distribution"),
            "top_mutation_sources": final_summary.get("top_mutation_sources"),
            "semantic_mutation_risk_mean": final_summary.get("semantic_mutation_risk_mean"),
            "semantic_mutation_risk_max": final_summary.get("semantic_mutation_risk_max"),
            "attribution_gaps": attribution_gaps,
            "attribution_gap_count": len(attribution_gaps),
        },
        "protected_replay_non_interference": {
            "verified": non_interference_verified,
            "final_text_hash_stable": non_interference_verified,
            "protected_fields_stable": non_interference_verified,
        },
        "remaining_risks": _remaining_risks(by3_report=by3_report, by1_coverage=by1_coverage),
        "schema_promotion_recommendation": _schema_promotion_recommendation(
            final_summary=final_summary,
            by3_report=by3_report,
        ),
    }


def render_semantic_mutation_attribution_closeout_markdown(report: Mapping[str, Any]) -> str:
    """Render human-readable BY4 closeout report."""
    by1 = report.get("by1_synthetic_fixture_coverage")
    by1 = by1 if isinstance(by1, Mapping) else {}
    by2 = report.get("by2_protected_corpus_measurement")
    by2 = by2 if isinstance(by2, Mapping) else {}
    by2_summary = by2.get("summary") if isinstance(by2.get("summary"), Mapping) else {}
    by3 = report.get("by3_strict_social_gap_closure")
    by3 = by3 if isinstance(by3, Mapping) else {}
    final = report.get("final_measurement")
    final = final if isinstance(final, Mapping) else {}
    non_int = report.get("protected_replay_non_interference")
    non_int = non_int if isinstance(non_int, Mapping) else {}
    promo = report.get("schema_promotion_recommendation")
    promo = promo if isinstance(promo, Mapping) else {}
    risks = report.get("remaining_risks")
    risks = risks if isinstance(risks, list) else []

    lines = [
        "# Semantic Mutation Attribution Closeout (BY4)",
        "",
        f"- schema version: {report.get('schema_version')}",
        f"- closeout: {report.get('closeout')}",
        "",
        "## Final measurement",
        "",
        f"- total turns: {final.get('total_turns')}",
        f"- mutated turns: {final.get('mutated_turns')}",
        f"- attributable first mutations: {final.get('attributable_first_mutations')}",
        f"- first-source coverage rate: {float(final.get('first_source_coverage_rate') or 0):.2%}",
        f"- unknown first-source count: {final.get('unknown_first_source_count')}",
        f"- attribution gap count: {final.get('attribution_gap_count')}",
        f"- semantic mutation risk (mean / max): {final.get('semantic_mutation_risk_mean')} / {final.get('semantic_mutation_risk_max')}",
        "",
        "## BY1 synthetic fixture coverage",
        "",
        f"- fixture source: {by1.get('fixture_source')}",
        f"- total turns: {by1.get('total_turns')}",
        f"- mutated turns: {by1.get('mutated_turns')}",
        f"- first-source coverage rate: {float(by1.get('first_source_coverage_rate') or 0):.2%}",
        f"- buckets covered: {', '.join(str(b) for b in (by1.get('buckets_covered') or []))}",
        "",
        "## BY2 protected corpus measurement",
        "",
        f"- corpus: {by2.get('corpus')}",
        f"- first-source coverage rate: {float(by2_summary.get('first_source_coverage_rate') or 0):.2%}",
        f"- unknown first-source count: {by2_summary.get('unknown_first_source_count')}",
        f"- attribution gap count: {by2.get('attribution_gap_count')}",
        "",
        "## BY3 strict-social gap closure",
        "",
        f"- target turn: {by3.get('target_turn')}",
        f"- gap closed: {by3.get('gap_closed')}",
        "",
        "## Bucket distribution (final)",
        "",
    ]

    bucket_distribution = final.get("bucket_distribution")
    if isinstance(bucket_distribution, Mapping) and bucket_distribution:
        for bucket, count in sorted(bucket_distribution.items()):
            lines.append(f"- {bucket}: {count}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Top mutation sources (final)", ""])
    top_sources = final.get("top_mutation_sources")
    if isinstance(top_sources, list) and top_sources:
        for item in top_sources:
            if isinstance(item, Mapping):
                lines.append(f"- {item.get('source')}: {item.get('count')}")
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "",
            "## Protected replay non-interference",
            "",
            f"- verified: {non_int.get('verified')}",
            f"- final_text_hash stable (probe-on vs probe-off): {non_int.get('final_text_hash_stable')}",
            f"- protected fields stable: {non_int.get('protected_fields_stable')}",
            "",
            "## Remaining risks",
            "",
        ]
    )
    if risks:
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- (none)")

    lines.extend(
        [
            "",
            "## Schema promotion recommendation",
            "",
            f"- promote to protected replay schema now: {promo.get('promote_to_protected_replay_schema_now')}",
            f"- measurement ready for future promotion: {promo.get('measurement_ready_for_future_promotion')}",
            f"- rationale: {promo.get('rationale')}",
            "",
            "## How to rerun BY measurement",
            "",
            "Run the closeout regression guard (refreshes `artifacts/by4/` when using the repo artifact test):",
            "",
            "```bash",
            "python -m pytest tests/test_by4_semantic_mutation_attribution_closeout.py -q",
            "```",
            "",
            "Refresh individual deliverables:",
            "",
            "```bash",
            "python -m pytest tests/test_by_first_semantic_mutation_attribution.py -q",
            "python -m pytest tests/test_by2_protected_semantic_mutation_measurement.py::test_by2_generate_repo_corpus_report_artifacts -q",
            "python -m pytest tests/test_by3_strict_social_semantic_mutation.py::test_by3_generate_repo_artifacts -q",
            "python -m pytest tests/test_by4_semantic_mutation_attribution_closeout.py::test_by4_generate_repo_artifacts -q",
            "```",
            "",
            "BY2/BY3 artifact tests write to `artifacts/by2/` and `artifacts/by3/`. "
            "The BY4 artifact test writes to `artifacts/by4/`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_semantic_mutation_attribution_closeout_reports(
    report: Mapping[str, Any],
    out_dir: Path,
) -> dict[str, str]:
    """Write BY4 JSON and Markdown closeout reports."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "semantic_mutation_attribution_closeout.json"
    md_path = out_dir / "semantic_mutation_attribution_closeout.md"
    write_deterministic_json(json_path, report)
    md_path.write_text(render_semantic_mutation_attribution_closeout_markdown(report), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(md_path),
    }


def measure_semantic_mutation_attribution_closeout(
    *,
    storage_root: Path,
    monkeypatch: Any | None = None,
    out_dir: Path | None = None,
    by2_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run BY4 closeout measurement: corpus probe, non-interference, aggregate reports."""
    by1_coverage = measure_by1_synthetic_fixture_coverage()

    measurement = measure_strict_social_semantic_mutation_corpus(
        storage_root=storage_root,
        monkeypatch=monkeypatch,
        out_dir=None,
        by2_baseline=by2_baseline,
    )

    baseline = measurement["baseline_turns"]
    probed = measurement["probed_turns"]
    assert_probe_non_interference(baseline, probed)

    by2_report = measurement["by2_report"]
    by3_report = measurement["by3_report"]

    closeout_report = build_semantic_mutation_attribution_closeout_report(
        by1_coverage=by1_coverage,
        by2_report=by2_report,
        by3_report=by3_report,
        non_interference_verified=True,
    )

    written: dict[str, str] = {}
    if out_dir is not None:
        written = write_semantic_mutation_attribution_closeout_reports(closeout_report, out_dir)

    return {
        "baseline_turns": baseline,
        "probed_turns": probed,
        "turn_rows": measurement["turn_rows"],
        "by1_coverage": by1_coverage,
        "by2_report": by2_report,
        "by3_report": by3_report,
        "closeout_report": closeout_report,
        "written_artifacts": written,
    }


__all__ = [
    "BY4_REPORT_SCHEMA_VERSION",
    "build_by1_synthetic_fixture_corpus",
    "build_semantic_mutation_attribution_closeout_report",
    "measure_by1_synthetic_fixture_coverage",
    "measure_semantic_mutation_attribution_closeout",
    "render_semantic_mutation_attribution_closeout_markdown",
    "write_semantic_mutation_attribution_closeout_reports",
]
