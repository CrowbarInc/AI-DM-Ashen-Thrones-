"""Offline assembly and validator pass. No provider calls."""
from __future__ import annotations

import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_50"
spec = importlib.util.spec_from_file_location("pr50_experiment", OUT / "run_experiment.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)

from game.anchored_investigation_narration import (
    assemble,
    authorize_anchored_investigation,
    fallback,
    validate_prelude,
)


def main() -> None:
    requests = json.loads((OUT / "requests.json").read_text(encoding="utf-8"))
    review = json.loads((OUT / "narrative_review.json").read_text(encoding="utf-8"))
    judgments = {row["request_id"]: row for row in review["samples"]}
    results = []
    for record in requests:
        row = experiment.load_fixture(record["fixture"])
        contract = authorize_anchored_investigation(row["resolution"], experiment.narration_payload(row))
        raw = record["extracted_narration_text"]
        anchor = " ".join(anchor.text for anchor in contract.anchors)
        if anchor != record["authoritative_discovery"]:
            raise RuntimeError("anchor bytes drifted")
        audit = {}
        try:
            prelude, audit = validate_prelude(contract, raw)
            if not audit["hard_valid"]:
                preview = fallback(contract)
                used_fallback = True
                diagnostic = "semantic_rejection"
            else:
                preview = assemble(contract, prelude)
                used_fallback = False
                diagnostic = "heuristic_pass_pending_review"
                if any(preview.count(item.text) != 1 for item in contract.anchors):
                    raise RuntimeError("anchor_integrity")
        except (ValueError, UnicodeError) as exc:
            prelude = ""
            preview = fallback(contract)
            used_fallback = True
            diagnostic = "invalid_prelude:" + str(exc)
        independent_safe = judgments[record["request_id"]]["mechanical_consistency"]["supported"] and not judgments[record["request_id"]]["hidden_information"]["leak"] and not judgments[record["request_id"]]["incidental_invention"]["consequential"]
        validator_pass = (not used_fallback) and bool(audit.get("hard_valid"))
        if validator_pass and independent_safe:
            disagreement = "correct_acceptance"
        elif (not validator_pass) and (not independent_safe):
            disagreement = "correct_rejection"
        elif validator_pass and not independent_safe:
            disagreement = "false_acceptance"
        else:
            disagreement = "false_rejection"
        results.append({
            "request_id": record["request_id"],
            "word_count": len(raw.split()),
            "diagnostic": diagnostic,
            "used_fallback": used_fallback,
            "validator_decision": "pass" if validator_pass else "reject",
            "hard_valid": audit.get("hard_valid"),
            "reasons": audit.get("reasons"),
            "soft_flags": audit.get("soft_flags"),
            "mechanical_claim_audit": audit.get("mechanical_claim_audit"),
            "unsupported_claims": (audit.get("mechanical_claim_audit") or {}).get("claims"),
            "hidden_information_reasons": [
                reason for reason in (audit.get("reasons") or [])
                if "hidden" in reason or "secret" in reason or "gm_only" in reason
            ],
            "fallback_output": fallback(contract),
            "assembled_preview": preview,
            "anchor_exact": anchor in preview and preview.count(anchor) == 1,
            "independent_mechanically_safe": independent_safe,
            "disagreement_class": disagreement,
            "review_required": True,
            "player_facing": False,
        })
    wall = [row["wall_clock_latency_ms"] for row in requests]
    summary = {
        "validator_results": results,
        "passes": sum(row["validator_decision"] == "pass" for row in results),
        "rejections": sum(row["validator_decision"] == "reject" for row in results),
        "disagreement_counts": {
            name: sum(row["disagreement_class"] == name for row in results)
            for name in ("correct_acceptance", "correct_rejection", "false_acceptance", "false_rejection")
        },
        "wall_clock_latency_ms": {
            "values": wall,
            "mean": round(statistics.fmean(wall), 3),
            "median": round(statistics.median(wall), 3),
            "min": min(wall),
            "max": max(wall),
        },
        "provider_requests_during_evaluation": 0,
    }
    (OUT / "validator_results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "passes": summary["passes"],
        "disagreement_counts": summary["disagreement_counts"],
        "words": {row["request_id"]: row["word_count"] for row in results},
        "anchors_exact": all(row["anchor_exact"] for row in results),
        "fallback_used": [row["request_id"] for row in results if row["used_fallback"]],
        "latency": summary["wall_clock_latency_ms"],
    }, indent=2))


if __name__ == "__main__":
    main()
