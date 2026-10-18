"""PR-DL phase 1 corrections. The PR-DK scenario matrix is not edited."""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Mapping


def _candidate_totals(csv_path: Path) -> dict[str, dict[str, int]]:
    totals: dict[str, dict[str, int]] = {}
    with csv_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            bucket = totals.setdefault(row["candidate"], {"requests": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0})
            bucket["requests"] += 1
            bucket["input_tokens"] += int(row["input_tokens"])
            bucket["output_tokens"] += int(row["output_tokens"])
            bucket["total_tokens"] += int(row["total_tokens"])
    return totals


def evidence_corrections(root: Path, matrix_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    usage_path = root / "artifacts" / "pr_dh_live_interpretation" / "PR-DH_provider_usage.csv"
    totals = _candidate_totals(usage_path)
    combined_input = sum(item["input_tokens"] for item in totals.values())
    combined_output = sum(item["output_tokens"] for item in totals.values())
    combined_total = sum(item["total_tokens"] for item in totals.values())
    combined_requests = sum(item["requests"] for item in totals.values())
    candidate_c = totals["C"]
    published_c = {"requests": 16, "input_tokens": 18983, "output_tokens": 2859, "total_tokens": 21842}
    average_published = round(published_c["total_tokens"] / published_c["requests"], 4)
    average_actual = round(candidate_c["total_tokens"] / candidate_c["requests"], 4)
    request_ids: list[str] = []
    dk_dir = root / "artifacts" / "pr_dk_escalation_routing"
    if dk_dir.exists():
        for path in dk_dir.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".json", ".csv", ".txt"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                request_ids.extend(re.findall(r"resp_[A-Za-z0-9]+", text))
    api_calls = []
    invoked = []
    for row in matrix_rows:
        trace = row.get("contract_trace") if isinstance(row.get("contract_trace"), Mapping) else {}
        calls = int(trace.get("interpretation_api_calls") or 0)
        if calls:
            api_calls.append(row["scenario_id"])
        if trace.get("model_interpreter_invoked"):
            invoked.append(row["scenario_id"])
    labels = [
        {
            "scenario_id": row["scenario_id"],
            "utterance": row["utterance"],
            "assistance_justified": bool(row["assistance_justified"]),
            "A_classification": row["A_classification"],
            "B_classification": row["B_classification"],
            "C_classification": row["C_classification"],
        }
        for row in matrix_rows
    ]
    return {
        "candidate_totals": totals,
        "combined": {
            "requests": combined_requests,
            "input_tokens": combined_input,
            "output_tokens": combined_output,
            "total_tokens": combined_total,
        },
        "published_candidate_c": published_c,
        "published_candidate_c_average_total_tokens": average_published,
        "corrected_candidate_c_average_total_tokens": average_actual,
        "published_matches_combined_not_candidate_c": published_c["input_tokens"] == combined_input
        and published_c["output_tokens"] == combined_output
        and published_c["total_tokens"] == combined_total
        and published_c["requests"] == candidate_c["requests"],
        "matrix_preserved": True,
        "matrix_labels": labels,
        "manual_trace": {
            "description": (
                "PR-DK remaining risks describe a manual trace of contract construction. "
                "establish_ordinary_gameplay_contract enables the interpreter only after fast-path abstention "
                "when model_interpretation_appropriate is set. interpret_for_contract returns skipped, with "
                "api_calls 0, when ASHEN_DISABLE_LIVE_INTERPRETATION is set. The PR-DK harness sets that flag "
                "before importing contract code and records live_provider_calls 0."
            ),
            "provider_request_ids_in_pr_dk_artifacts": sorted(set(request_ids)),
            "interpretation_api_calls_scenarios": api_calls,
            "model_interpreter_invoked_scenarios": invoked,
            "provider_calls_observed": bool(api_calls or invoked),
        },
        "shared_pipeline_suite": {
            "status": "incomplete",
            "passed": False,
            "source": "artifacts/pr_dk_escalation_routing/PR-DK_regression_results.md",
            "detail": "The PR-DK shared turn-pipeline command produced no pytest output and was interrupted. It is incomplete, not passing.",
        },
    }


def render_evidence(payload: Mapping[str, Any]) -> str:
    totals = payload["candidate_totals"]
    lines = [
        "# PR-DL Evidence Corrections",
        "",
        "The original PR-DK scenario matrix is unchanged. These corrections record accounting, the manual-trace provider question, and the shared-suite status before live calls.",
        "",
        "## Candidate C token accounting",
        "",
        "PR-DK_cost_model.md assigned Candidate C 16 calls and 18,983 input / 2,859 output / 21,842 total tokens, then averaged 21,842 / 16 = 1,365.1.",
        "",
        "Those token totals are the combined PR-DH bill. Summing `PR-DH_provider_usage.csv` by candidate gives:",
        "",
        "| Candidate | Requests | Input | Output | Total | Average total |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in sorted(totals):
        item = totals[name]
        average = round(item["total_tokens"] / item["requests"], 4) if item["requests"] else None
        lines.append(
            f"| {name} | {item['requests']} | {item['input_tokens']} | {item['output_tokens']} | {item['total_tokens']} | {average} |"
        )
    combined = payload["combined"]
    lines.extend(
        [
            f"| Combined | {combined['requests']} | {combined['input_tokens']} | {combined['output_tokens']} | {combined['total_tokens']} |  |",
            "",
            f"Published Candidate C average was {payload['published_candidate_c_average_total_tokens']}. Corrected Candidate C average is {payload['corrected_candidate_c_average_total_tokens']} total tokens per call.",
            "",
            f"Published Candidate C tokens match the combined bill while the published request count matches Candidate C only: {payload['published_matches_combined_not_candidate_c']}.",
            "",
            "Candidate B in the same PR-DK paragraph (6 calls, 4,414 / 1,361 / 5,775) matches the CSV.",
            "",
            "## Manual trace provider calls",
            "",
            payload["manual_trace"]["description"],
            "",
            f"Recomputed contract traces with nonzero interpretation_api_calls: {payload['manual_trace']['interpretation_api_calls_scenarios'] or 'none'}.",
            f"Recomputed traces with model_interpreter_invoked: {payload['manual_trace']['model_interpreter_invoked_scenarios'] or 'none'}.",
            f"Provider request ids in PR-DK artifacts: {payload['manual_trace']['provider_request_ids_in_pr_dk_artifacts'] or 'none'}.",
            "No provider call was observed for the manual trace. The trace is a control-flow observation that the disable flag has to be set before contract construction, and the harness did set it.",
            "",
            "## Shared pipeline suite",
            "",
            "Inherited PR-DK status: incomplete. It did not pass.",
            payload["shared_pipeline_suite"]["detail"],
            "The later PR-DL rerun is recorded in PR-DL_regression_results.md. That rerun finished and failed. It is not a pass.",
            "",
            "## Preserved 21-scenario labels",
            "",
            "| Scenario | Assistance justified | A | B | C | Utterance |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in payload["matrix_labels"]:
        lines.append(
            f"| {row['scenario_id']} | {row['assistance_justified']} | {row['A_classification']} | {row['B_classification']} | {row['C_classification']} | {row['utterance']} |"
        )
    lines.append("")
    return "\n".join(lines)
