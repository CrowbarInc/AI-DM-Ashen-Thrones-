"""DTD3: test/manual report fields derived only from FEM ``dead_turn`` + ``summarize_gameplay_validation_for_turn``.

No classification or policy here — read paths documented in :mod:`game.final_emission_meta`.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, MutableMapping, Sequence

from game.final_emission_meta import (
    normalized_observational_telemetry_bundle,
    summarize_gameplay_validation_for_turn,
)

SCHEMA_VERSION = "dead_turn_report_visibility.v1"

INVALID_FOR_GAMEPLAY_QUALITY_EXPLAINER = (
    "This run hit upstream fallback / dead-turn policy and should not be used to judge gameplay quality."
)


def per_turn_dead_turn_visibility(record: Mapping[str, Any], *, turn_index: int) -> dict[str, Any]:
    """Single row: FEM → dead_turn fields + gameplay_validation summary (evaluation policy mirror)."""
    bundle = normalized_observational_telemetry_bundle(record)
    dt = bundle.get("dead_turn") if isinstance(bundle.get("dead_turn"), Mapping) else {}
    gv = summarize_gameplay_validation_for_turn(dt)
    return {
        "turn_index": int(turn_index),
        "turn_number_one_based": int(turn_index) + 1,
        "dead_turn_detected": bool(dt.get("is_dead_turn")),
        "dead_turn_class": dt.get("dead_turn_class"),
        "dead_turn_reason_codes": list(dt.get("dead_turn_reason_codes") or []),
        "manual_test_valid": bool(dt.get("manual_test_valid", True)),
        "validation_playable": bool(dt.get("validation_playable", True)),
        "excluded_from_scoring": bool(gv.get("excluded_from_scoring")),
        "invalidation_reason": gv.get("invalidation_reason"),
        "run_valid": bool(gv.get("run_valid", True)),
        "infra_failure_count": int(gv.get("infra_failure_count") or 0),
    }


def build_dead_turn_run_report(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate over transcript-style rows (``_final_emission_meta`` on each record)."""
    per_turn: list[dict[str, Any]] = []
    dead_turn_indexes: list[int] = []
    infra_failure_count = 0
    by_class: Counter[str] = Counter()

    for i, rec in enumerate(records):
        row = per_turn_dead_turn_visibility(rec, turn_index=i)
        per_turn.append(row)
        infra_failure_count += row["infra_failure_count"]
        if row["dead_turn_detected"]:
            dead_turn_indexes.append(i)
            cls = str(row.get("dead_turn_class") or "unknown").strip() or "unknown"
            by_class[cls] += 1

    dead_turn_count = len(dead_turn_indexes)
    run_valid = all(r["run_valid"] for r in per_turn) if per_turn else True
    excluded_any = any(r["excluded_from_scoring"] for r in per_turn)

    banner: str | None = None
    if dead_turn_count:
        first_cls = per_turn[dead_turn_indexes[0]].get("dead_turn_class") if dead_turn_indexes else None
        if isinstance(first_cls, str) and first_cls.strip():
            banner = f"DEAD TURN DETECTED — {first_cls.strip()}"
        else:
            banner = "DEAD TURN DETECTED"

    explainer: str | None = None
    if not run_valid or excluded_any:
        explainer = INVALID_FOR_GAMEPLAY_QUALITY_EXPLAINER

    chat_error_count = sum(1 for r in records if not bool(r.get("ok", True)))
    inv_reason: str | None = None
    for r in per_turn:
        ir = r.get("invalidation_reason")
        if isinstance(ir, str) and ir.strip():
            inv_reason = ir.strip()
            break

    return {
        "schema_version": SCHEMA_VERSION,
        "run_valid": bool(run_valid),
        "excluded_from_scoring": bool(excluded_any),
        "invalidation_reason": inv_reason,
        "dead_turn_count": dead_turn_count,
        "dead_turn_indexes": dead_turn_indexes,
        "dead_turn_turn_numbers_one_based": [i + 1 for i in dead_turn_indexes],
        "infra_failure_count": infra_failure_count,
        "dead_turn_by_class": dict(sorted(by_class.items())),
        "banner": banner,
        "invalid_for_gameplay_conclusions": bool(not run_valid or excluded_any),
        "invalid_run_explanation": explainer,
        "chat_error_count": chat_error_count,
        "per_turn": per_turn,
    }


def enrich_playability_rollup_dict(
    turns_out: Sequence[Mapping[str, Any]],
    rollup: MutableMapping[str, Any] | None,
) -> dict[str, Any]:
    """Copy *rollup* and add DTD3 index/class/banner fields (FEM via existing per-turn ``gameplay_validation``)."""
    base = dict(rollup or {})
    dead_indexes: list[int] = []
    by_class: Counter[str] = Counter()
    for i, row in enumerate(turns_out):
        pe = row.get("playability_eval") if isinstance(row.get("playability_eval"), Mapping) else {}
        gv = pe.get("gameplay_validation") if isinstance(pe.get("gameplay_validation"), Mapping) else {}
        nested = gv.get("dead_turn") if isinstance(gv.get("dead_turn"), Mapping) else {}
        if bool(nested.get("is_dead_turn")):
            dead_indexes.append(i)
            cls = str(nested.get("dead_turn_class") or "unknown").strip() or "unknown"
            by_class[cls] += 1
    base["dead_turn_indexes"] = dead_indexes
    base["dead_turn_turn_numbers_one_based"] = [i + 1 for i in dead_indexes]
    base["dead_turn_by_class"] = dict(sorted(by_class.items()))
    banner: str | None = None
    if dead_indexes:
        first = turns_out[dead_indexes[0]]
        pe0 = first.get("playability_eval") if isinstance(first.get("playability_eval"), Mapping) else {}
        gv0 = pe0.get("gameplay_validation") if isinstance(pe0.get("gameplay_validation"), Mapping) else {}
        nested0 = gv0.get("dead_turn") if isinstance(gv0.get("dead_turn"), Mapping) else {}
        c0 = nested0.get("dead_turn_class")
        if isinstance(c0, str) and c0.strip():
            banner = f"DEAD TURN DETECTED — {c0.strip()}"
        else:
            banner = "DEAD TURN DETECTED"
    base["dead_turn_banner"] = banner
    excluded = bool(base.get("excluded_from_scoring"))
    valid = bool(base.get("run_valid", True))
    if not valid or excluded:
        base["invalid_for_gameplay_conclusions"] = True
        base["invalid_run_explanation"] = INVALID_FOR_GAMEPLAY_QUALITY_EXPLAINER
    else:
        base["invalid_for_gameplay_conclusions"] = False
        base["invalid_run_explanation"] = None
    return base


def markdown_dead_turn_header_block(report: Mapping[str, Any]) -> str:
    """Tester-facing Markdown block (artifacts only — not player-facing runtime)."""
    if not report.get("banner"):
        lines = [
            "## Dead turn / run validity (test report)",
            "",
            "- **Dead turn detected:** no",
            "- **Run valid for gameplay conclusions:** "
            f"{'yes' if report.get('run_valid') else 'no'}",
        ]
        if report.get("invalid_for_gameplay_conclusions") and report.get("invalid_run_explanation"):
            lines.append(f"- **Invalid for gameplay conclusions:** yes")
            lines.append(f"- **Note:** {report['invalid_run_explanation']}")
        if int(report.get("chat_error_count") or 0):
            lines.append(f"- **Engine / chat errors:** {int(report['chat_error_count'])}")
        lines.append("")
        return "\n".join(lines)

    lines = [
        "## Dead turn / run validity (test report)",
        "",
        f"> **{report['banner']}**",
        "",
        f"- **Dead turn count:** {int(report.get('dead_turn_count') or 0)}",
        f"- **Dead turn indexes (0-based):** `{report.get('dead_turn_indexes')}`",
        f"- **Dead turn turn numbers (1-based):** `{report.get('dead_turn_turn_numbers_one_based')}`",
        f"- **By class:** `{report.get('dead_turn_by_class')}`",
        f"- **Infra failure count (rolled up):** {int(report.get('infra_failure_count') or 0)}",
        f"- **Run valid for gameplay conclusions:** {'no' if report.get('invalid_for_gameplay_conclusions') else 'yes'}",
    ]
    if report.get("invalid_run_explanation"):
        lines.append(f"- **Note:** {report['invalid_run_explanation']}")
    if int(report.get("chat_error_count") or 0):
        lines.append(f"- **Engine / chat errors:** {int(report['chat_error_count'])}")
    lines.append("")
    return "\n".join(lines)
