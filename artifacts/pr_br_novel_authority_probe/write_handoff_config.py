"""Build the explicit handoff config. No model calls."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAMP = ROOT / "artifacts" / "pr_br_novel_authority_probe" / "20261003T181221Z"


def main() -> None:
    files = [
        path.relative_to(ROOT).as_posix()
        for path in sorted(STAMP.rglob("*"))
        if path.is_file() and path.name != "validation_report.md"
    ]
    files.extend(
        [
            "artifacts/pr_br_novel_authority_probe/run_probes.py",
            "game/gm_resolution_decision.py",
            "game/live_resolution.py",
            "game/immutable_valid_response.py",
        ]
    )
    supporting = []
    for path in files:
        role = "turn_artifact"
        why = "Saved live-probe evidence for external review."
        if path.startswith("game/"):
            role = "production_code"
            why = "Production module that shows decision attachment or narration rejection for this run."
        elif path.endswith("run_probes.py"):
            role = "validation_harness"
            why = "Exact seeds, player lines, and capture path for the eight turns."
        elif path.endswith("run_manifest.json"):
            why = "Exact model-call counts and per-turn status."
        supporting.append(
            {
                "path": path,
                "role": role,
                "why": why,
                "behavioral_evidence": path.startswith("artifacts/"),
                "human_review_required": True,
            }
        )
    config = {
        "campaign_id": "pr-br-novel-authority-live-validation",
        "campaign_name": "PR-BR Novel Authority Live Validation",
        "campaign_date": "2026-10-03",
        "purpose": "Bounded 8-turn live probe of whether model generation behaves competently through the GM resolution decision architecture, in novel domains.",
        "primary_report": "artifacts/pr_br_novel_authority_probe/20261003T181221Z/validation_report.md",
        "executive_summary": (
            "Eight isolated novel-domain gameplay turns scored 4 PASS and 4 FAIL. "
            "When the decision was attached, it authorized the authored facts, and bounded incidental play plus authorized movement succeeded. "
            "The kiln, dye vat, and chapel bell generations were competent and were then replaced by the canned sentence "
            "\"No one here can answer that from what is settled here\" after semantic_identity_mismatch. "
            "Social and movement turns never received a GMResolutionDecision, because attachment returns once a contract already exists. "
            "On that path, Nessa stated an unauthored organization as known fact. "
            "Decision B: localized defects. Return to targeted implementation. "
            "No production edits, no reruns, no 4x10 gate, no human playtest, and no PR-BS."
        ),
        "objective_status": "measured_defects_for_targeted_implementation",
        "changes": {
            "production": [],
            "validation": [
                "Ran 8 isolated live gameplay turns. No production code was changed after the results."
            ],
            "tooling": [
                "Added a validation harness and local trace summarizers under artifacts/pr_br_novel_authority_probe/. These are not production."
            ],
            "documentation": [
                "Wrote the 18-section validation report beside the turn artifacts."
            ],
            "generated_artifacts": [
                "artifacts/pr_br_novel_authority_probe/20261003T181221Z/ holds initial states, contracts, decisions, generations, validation metadata, committed states, and the report."
            ],
        },
        "testing": {
            "focused": "Not run. This cycle was live measurement only.",
            "broader": "Not run.",
            "full_suite": "Not run.",
            "runtime_validation": "8 isolated POST /api/chat turns. Manual 4 PASS / 4 FAIL. Passes: turns 3, 5, 6, 8. Fails: turns 1, 2, 4, 7.",
            "model_runtime_boundary": "8 gameplay turns. 11 generation calls, including 3 retries. 1 interpretation call. 1 startup preflight. 0 evaluator-model calls. 0 reruns. 0 gate sessions.",
            "new_regressions": "No production patch. Live defects are semantic-identity rejection collapsing three competent answers, and missing decisions on prebuilt social and movement contracts.",
            "pre_existing_failures": "The 8/40 gate still stands as prior evidence of generic nonresolution and consequential invention. This probe did not rerun that gate. Location desync did not appear here.",
        },
        "self_contained_review_test": "Bundle contains the validation report, all 8 turn artifacts, call logs, and the three production modules that explain the observed attachment and validation behavior.",
        "decisions_requiring_human_review": [
            "B. LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.",
            "Next implementation should attach GMResolutionDecision when a contract already exists, and should stop sentence-level semantic_identity_mismatch from replacing a matched answer with the canned nonresolution line.",
            "Do not start PR-BS, a 4x10 gate, or a human playtest on this evidence.",
        ],
        "known_problems": {
            "campaign_specific": [
                "Turns 1, 4, and 7 generated competent answers, then semantic_identity_mismatch replaced them with one canned sentence.",
                "Turns 2, 3, 6, and 8 have no GMResolutionDecision because the contract already existed.",
                "Turn 2 states that the Violet Compact is known to gather at the docks or the market.",
                "Retry prompts on turns 1, 4, and 7 omitted the contract and the decision.",
            ],
            "pre_existing": [
                "The second full gate remained 8/40 with consequential invention and generic nonresolution. This cycle did not rerun it."
            ],
        },
        "missing_concepts": [
            "Decision attachment on routes that construct the Resolution Contract before attach_interaction_obligation.",
            "A realization rule that allows answering that something is not firing, or that no one knows who, without contradicting a positive cracked fact.",
            "Partial-response preservation so one mismatched sentence does not discard the authorized sentences.",
        ],
        "does_not_prove": [
            "Does not prove multi-turn continuity.",
            "Does not prove a release threshold.",
            "Does not rerun the 4x10 gate.",
            "Does not authorize a human playtest.",
            "Does not show that turns 3 and 8 were protected by the decision layer. That layer was absent on those routes.",
        ],
        "recommended_next_step": "Targeted implementation of decision attachment on prebuilt contracts, and of semantic-identity handling for negated answers and neighboring sentences. Remeasure after that. Do not open PR-BS.",
        "supporting_files": supporting,
    }
    destination = ROOT / "artifacts" / "pr_br_novel_authority_probe" / "handoff_config.json"
    destination.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(len(supporting))
    print(destination)


if __name__ == "__main__":
    main()
