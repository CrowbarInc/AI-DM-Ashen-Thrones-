"""Build the review-handoff configuration for the final four-turn validation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAMP = ROOT / "artifacts" / "pr_br_final_live_validation" / "20261004T035044Z"


def main() -> None:
    supporting = []
    for path in sorted(STAMP.rglob("*")):
        if not path.is_file() or path.name == "validation_report.md":
            continue
        supporting.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "role": "live_validation_evidence",
                "why": (
                    "Exact initial state, four-turn production trace, contract, decision, "
                    "generation, audit, retry, sealed response, committed state, provenance, "
                    "manual adjudication, call count, or production-freeze evidence."
                ),
                "behavioral_evidence": True,
                "human_review_required": True,
            }
        )
    for path, role, why in (
        (
            ROOT / "artifacts" / "pr_br_final_live_validation" / "run_live.py",
            "validation_harness",
            "Exact fresh scene, four-turn cap, no-replay control, call instrumentation, and capture procedure.",
        ),
        (
            ROOT
            / "artifacts"
            / "pr_br_proposition_live_validation"
            / "20261004T021456Z"
            / "validation_report.md",
            "historical_comparison",
            "Previous 3/6 proposition-level live validation referenced by the final report.",
        ),
        (
            ROOT
            / "artifacts"
            / "pr_br_multiturn_provenance"
            / "20261003T223147Z"
            / "validation_report.md",
            "historical_comparison",
            "Original recursive A2-A4 failure referenced by the final report.",
        ),
    ):
        supporting.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "role": role,
                "why": why,
                "behavioral_evidence": True,
                "human_review_required": True,
            }
        )

    config = {
        "campaign_id": "pr-br-final-four-turn-live-validation",
        "campaign_name": "PR-BR Final Four-Turn Live Validation",
        "campaign_date": "2026-10-03",
        "purpose": (
            "Final focused production-path validation of inference, temporal provenance, "
            "player presupposition, epistemic correction, and incidental freedom."
        ),
        "primary_report": (
            "artifacts/pr_br_final_live_validation/20261004T035044Z/validation_report.md"
        ),
        "executive_summary": (
            "Four turns scored 0 PASS / 4 FAIL. The player hypothesis was typed and direct "
            "uncertainty survived, but Turn 1 omitted interpretation/INFER and persisted no "
            "gm_inference. Turn 3 laundered 'sudden, violent pressure seems a likely cause' "
            "into authored world_truth while admitting an unsupported recent-user/witness "
            "lead. Turn 4 remained natural but accepted_incidentals stayed empty. Exact calls: "
            "4 initial, 2 retry, 0 interpretation, 1 preflight, 0 other, 7 total. Decision C."
        ),
        "objective_status": "architectural_authority_laundering_and_temporal_provenance_failure",
        "changes": {
            "production": [],
            "validation": [
                "Ran exactly four gameplay turns in one fresh isolated scene.",
                "No turn reruns, exploratory gameplay, second scenario, 4x10 gate, commit, or push.",
            ],
            "tooling": [
                "Added a measurement-only four-turn harness with one-command-per-turn control."
            ],
            "documentation": [
                "Added the required twenty-section validation report and manual turn adjudications."
            ],
            "generated_artifacts": [
                "Stamped evidence includes exact state, contracts, decisions, generations, audits, retries, sealed responses, provenance snapshots, active claim, and call counts."
            ],
        },
        "testing": {
            "focused": "Not run; this cycle was live validation only.",
            "broader": "Not run.",
            "full_suite": "Not run.",
            "runtime_validation": "4/4 HTTP turns completed once; manual 0 PASS / 4 FAIL.",
            "model_runtime_boundary": (
                "4 initial generation calls, 2 retry generation calls, 0 interpretation "
                "calls, 1 preflight call, 0 other calls, 7 total."
            ),
            "new_regressions": (
                "No production patch. Live evidence exposed mixed-sentence authority laundering, "
                "missing gm_inference/accepted_incidental persistence, routing failure, and "
                "incomplete exact claim accounting."
            ),
            "pre_existing_failures": (
                "Prior 3/6 and recursive A2-A4 runs are historical comparison evidence only."
            ),
        },
        "self_contained_review_test": (
            "Bundle includes the report, exact initial state, all four API responses and traces, "
            "raw initial/retry calls, committed states, temporal ledgers, active claims, manual "
            "adjudications, production freeze, call manifest, harness, and comparison reports."
        ),
        "decisions_requiring_human_review": [
            "C. FINAL LIVE VALIDATION REPRODUCED AUTHORITY LAUNDERING OR TEMPORAL-PROVENANCE FAILURE; RETURN TO ARCHITECTURAL REVIEW.",
            "Do not begin PR-BS or run a broader release-candidate gate.",
        ],
        "known_problems": {
            "campaign_specific": [
                "Turn 1 omitted interpretation and INFER.",
                "Turn 2 misbound the player presupposition and emitted an irrelevant fallback.",
                "Turn 3 classified an unsupported likely cause as authored world truth.",
                "gm_inferences and accepted_incidentals remained empty.",
                "Exact accepted claim accounting omitted emitted content.",
            ],
            "pre_existing": [
                "Historical broad-gate failures were not rerun in this cycle."
            ],
        },
        "missing_concepts": [
            "Mixed-sentence proposition isolation before authority matching.",
            "Temporal-ledger authority over final accepted claim classification.",
            "Reliable narrator-versus-NPC epistemic routing.",
            "Exact emitted-text claim completeness.",
        ],
        "does_not_prove": [
            "Does not prove release-candidate readiness.",
            "Does not test broad playability or a second scenario.",
            "Does not rerun the 4x10 gate.",
            "Does not authorize PR-BS.",
        ],
        "recommended_next_step": (
            "Return to architectural review of proposition decomposition, temporal provenance "
            "ownership, and final claim audit before targeted implementation."
        ),
        "supporting_files": supporting,
    }
    destination = ROOT / "artifacts" / "pr_br_final_live_validation" / "handoff_config.json"
    destination.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"wrote {destination} with {len(supporting)} supporting files")


if __name__ == "__main__":
    main()
