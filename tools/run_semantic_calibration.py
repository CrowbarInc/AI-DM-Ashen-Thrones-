#!/usr/bin/env python3
"""Run the semantic calibration corpus through ``game.playability_eval``."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.playability_eval import evaluate_playability  # noqa: E402

DEFAULT_CORPUS = ROOT / "data" / "validation" / "semantic_calibration"
DEFAULT_OUT = ROOT / "artifacts" / "semantic_validation_calibration"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _gate_statuses(eval_out: Mapping[str, Any]) -> dict[str, str]:
    gates = eval_out.get("mandatory_gates")
    if not isinstance(gates, Mapping):
        return {}
    out: dict[str, str] = {}
    for name, gate in gates.items():
        if isinstance(gate, Mapping):
            out[str(name)] = str(gate.get("status") or "")
    return out


def _case_payload(case: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "player_prompt": case.get("player_input"),
        "gm_text": case.get("gm_response"),
    }
    prior_player = case.get("prior_player_input")
    prior_gm = case.get("prior_gm_output")
    if isinstance(prior_player, str) and prior_player.strip():
        payload["prior_player_prompt"] = prior_player
    if isinstance(prior_gm, str) and prior_gm.strip():
        payload["prior_gm_text"] = prior_gm
    return payload


def run_calibration(*, corpus_dir: Path, output_dir: Path) -> dict[str, Any]:
    manifest = _load_json(corpus_dir / "manifest.json")
    case_names = manifest.get("cases") if isinstance(manifest.get("cases"), list) else []
    rows: list[dict[str, Any]] = []

    for rel in case_names:
        case_path = corpus_dir / "cases" / str(rel)
        case = _load_json(case_path)
        eval_out = evaluate_playability(_case_payload(case))
        expected_result = str(case.get("expected_semantic_result") or "")
        actual_result = str(eval_out.get("semantic_result") or "")
        expected_gates = case.get("expected_mandatory_gates")
        expected_gate_statuses = dict(expected_gates) if isinstance(expected_gates, Mapping) else {}
        actual_gate_statuses = _gate_statuses(eval_out)
        gate_agreement = {
            name: actual_gate_statuses.get(name) == expected
            for name, expected in expected_gate_statuses.items()
        }
        agrees = actual_result == expected_result and all(gate_agreement.values())
        rows.append(
            {
                "case_id": case.get("case_id"),
                "category": case.get("category"),
                "case_path": str(case_path.relative_to(ROOT)),
                "expected_semantic_result": expected_result,
                "actual_semantic_result": actual_result,
                "expected_mandatory_gates": expected_gate_statuses,
                "actual_mandatory_gates": actual_gate_statuses,
                "gate_agreement": gate_agreement,
                "agreement": agrees,
                "rationale": case.get("rationale"),
                "provenance": case.get("provenance"),
                "diagnostic_quality": eval_out.get("diagnostic_quality"),
                "axes": eval_out.get("axes"),
                "mandatory_gates": eval_out.get("mandatory_gates"),
            }
        )

    disagreements = [row for row in rows if not row["agreement"]]
    generated_at = datetime.now(timezone.utc).isoformat()
    report = {
        "report_version": 1,
        "generated_at": generated_at,
        "corpus_id": manifest.get("corpus_id"),
        "case_count": len(rows),
        "agreement_count": len(rows) - len(disagreements),
        "disagreement_count": len(disagreements),
        "all_foundational_cases_agree": not disagreements,
        "rows": rows,
    }

    _write_json(output_dir / "calibration_report.json", report)
    _write_text(output_dir / "calibration_report.md", _markdown_report(report))
    return report


def _markdown_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# Semantic Calibration Report",
        "",
        f"Generated: {report.get('generated_at')}",
        f"Corpus: {report.get('corpus_id')}",
        f"Cases: {report.get('case_count')}",
        f"Agreements: {report.get('agreement_count')}",
        f"Disagreements: {report.get('disagreement_count')}",
        "",
        "| Case | Expected | Actual | Gates | Agreement |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        gates = ", ".join(
            f"{k}={v}" for k, v in (row.get("actual_mandatory_gates") or {}).items()
        )
        lines.append(
            "| {case} | {exp} | {act} | {gates} | {agree} |".format(
                case=row.get("case_id"),
                exp=row.get("expected_semantic_result"),
                act=row.get("actual_semantic_result"),
                gates=gates,
                agree="yes" if row.get("agreement") else "no",
            )
        )
    disagreements = [r for r in report.get("rows") or [] if isinstance(r, Mapping) and not r.get("agreement")]
    lines.extend(["", "## Disagreements", ""])
    if disagreements:
        for row in disagreements:
            lines.append(f"- {row.get('case_id')}: expected {row.get('expected_semantic_result')} but got {row.get('actual_semantic_result')}")
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run semantic calibration corpus.")
    p.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = run_calibration(corpus_dir=args.corpus_dir, output_dir=args.output_dir)
    print(f"Wrote {args.output_dir / 'calibration_report.json'}")
    print(f"Wrote {args.output_dir / 'calibration_report.md'}")
    return 0 if report.get("all_foundational_cases_agree") else 1


if __name__ == "__main__":
    raise SystemExit(main())
