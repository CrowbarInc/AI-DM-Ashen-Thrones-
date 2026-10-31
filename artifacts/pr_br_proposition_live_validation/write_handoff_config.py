"""Build the review-handoff configuration for the six-turn live validation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAMP = ROOT / "artifacts" / "pr_br_proposition_live_validation" / "20261004T021456Z"


def main() -> None:
    supporting = []
    for path in sorted(STAMP.rglob("*")):
        if not path.is_file() or path.name == "validation_report.md":
            continue
        supporting.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "role": "live_validation_evidence",
                "why": "Exact initial state, turn trace, model-call record, committed state, or freeze evidence.",
                "behavioral_evidence": True,
                "human_review_required": True,
            }
        )
    supporting.append(
        {
            "path": "artifacts/pr_br_proposition_live_validation/run_validation.py",
            "role": "validation_harness",
            "why": "Exact fresh scenes, six player turns, call instrumentation, and capture procedure.",
            "behavioral_evidence": True,
            "human_review_required": True,
        }
    )
    config = {
        "campaign_id": "pr-br-proposition-level-live-validation",
        "campaign_name": "PR-BR Proposition-Level Claim Control Live Validation",
        "campaign_date": "2026-10-03",
        "purpose": (
            "Six-turn multi-turn live validation of authority laundering, epistemic continuity, "
            "free-text fact boundaries, and natural bounded GM speech."
        ),
        "primary_report": (
            "artifacts/pr_br_proposition_live_validation/20261004T021456Z/validation_report.md"
        ),
        "executive_summary": (
            "Six turns scored 3 PASS and 3 FAIL. Authority laundering did not recur: the A2 "
            "presupposition never became world truth, and B1-B2 preserved the C19 free-text "
            "boundary. A3 exposed a high-severity localized defect: correct unknown-cause, "
            "actor, and sequence sentences were rejected while an unsupported star-chart lead "
            "survived preservation. Temporal provenance stayed absent. B3 preserved mundane "
            "improvisation with bounded claim authority but emitted malformed quotation after "
            "preservation. Exact calls: 6 initial, 4 retry, 4 interpretation, 1 preflight, "
            "0 other, 15 total. Decision B: return to targeted implementation."
        ),
        "objective_status": "localized_high_severity_epistemic_defects_without_laundering",
        "changes": {
            "production": [],
            "validation": [
                "Ran exactly six gameplay turns across two fresh three-turn sequences.",
                "No turn reruns, exploratory gameplay, 4x10 gate, commit, or push.",
            ],
            "tooling": [
                "Added a measurement-only harness under artifacts/pr_br_proposition_live_validation/."
            ],
            "documentation": [
                "Added the required 19-section validation report and exact call accounting."
            ],
            "generated_artifacts": [
                "The stamped evidence directory contains complete per-turn states, contracts, decisions, generations, retries, audits, final responses, and provenance captures."
            ],
        },
        "testing": {
            "focused": "Not run; this cycle was live validation only.",
            "broader": "Not run.",
            "full_suite": "Not run.",
            "runtime_validation": (
                "6/6 HTTP gameplay turns completed once. Manual 3 PASS / 3 FAIL: "
                "A2, B1, B2 pass; A1, A3, B3 fail."
            ),
            "model_runtime_boundary": (
                "6 initial generation calls, 4 retry generation calls, 4 interpretation calls, "
                "1 preflight call, 0 other model calls, 15 total."
            ),
            "new_regressions": (
                "No production patch. Live defects are uncertainty rejection, missing temporal "
                "provenance, and malformed/incompletely audited preserved output."
            ),
            "pre_existing_failures": (
                "The original 8/40 gate and older uncertainty-sensitive attachment failures remain "
                "prior evidence; neither was rerun."
            ),
        },
        "self_contained_review_test": (
            "Bundle includes the report, exact initial states, all six API responses and turn traces, "
            "full generation/retry prompts and results, committed states, call manifest, production "
            "freeze hashes, and the harness."
        ),
        "decisions_requiring_human_review": [
            "B. LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.",
            "Confirm A3 as high severity because correct uncertainty was rejected while an unsupported lead survived.",
            "Do not start PR-BS or a broader release-candidate gate.",
        ],
        "known_problems": {
            "campaign_specific": [
                "A1 did not provide useful qualified inference.",
                "A3 rejected correct unknown-cause/actor/sequence text twice.",
                "Temporal provenance and active claim remained absent across Sequence A.",
                "B3 preservation emitted malformed quotation and incomplete final claim accounting.",
            ],
            "pre_existing": [
                "Original 8/40 gate failures remain historical comparison evidence.",
                "Known older uncertainty-sensitive failures were not repaired or rerun in this cycle.",
            ],
        },
        "missing_concepts": [
            "Uncertainty-safe evidential classification.",
            "Cross-turn persistence of GM inference and player hypothesis without promotion.",
            "Syntax- and claim-complete bounded sentence preservation.",
        ],
        "does_not_prove": [
            "Does not prove release-candidate readiness.",
            "Does not prove broad multi-turn playability beyond these six turns.",
            "Does not rerun the 4x10 gate.",
            "Does not authorize PR-BS.",
        ],
        "recommended_next_step": (
            "Target uncertainty/evidential validation, temporal provenance persistence, follow-up "
            "referent binding, and preservation completeness; then run focused deterministic tests."
        ),
        "supporting_files": supporting,
    }
    destination = ROOT / "artifacts" / "pr_br_proposition_live_validation" / "handoff_config.json"
    destination.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"wrote {destination} with {len(supporting)} supporting files")


if __name__ == "__main__":
    main()
