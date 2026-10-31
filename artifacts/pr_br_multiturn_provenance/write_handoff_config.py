#!/usr/bin/env python3
"""Build the review handoff config for the multi-turn provenance validation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAMP = ROOT / "artifacts" / "pr_br_multiturn_provenance" / "20261003T223147Z"


def main() -> None:
    files = []
    for path in sorted(STAMP.rglob("*")):
        if not path.is_file() or path.name == "validation_report.md":
            continue
        files.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "role": "turn_artifact",
                "why": "Saved multi-turn live evidence: state, contract, decision, generation, or call log.",
                "behavioral_evidence": True,
                "human_review_required": True,
            }
        )
    files.append(
        {
            "path": "artifacts/pr_br_multiturn_provenance/run_live.py",
            "role": "validation_harness",
            "why": "Measurement harness. Fresh seeds, carried state, and capture path. Not production.",
            "behavioral_evidence": True,
            "human_review_required": True,
        }
    )
    for path, why in (
        (
            "game/gm_resolution_decision.py",
            "Narrated-fact classification, identity match, narrator-lead rejection, and movement decision reconciliation.",
        ),
        (
            "game/immutable_valid_response.py",
            "Bounded sentence preservation that kept the initial generation after retry failure on A2-A4.",
        ),
    ):
        files.append(
            {
                "path": path,
                "role": "production_code",
                "why": why,
                "behavioral_evidence": False,
                "human_review_required": True,
            }
        )
    config = {
        "campaign_id": "pr-br-multiturn-provenance",
        "campaign_name": "PR-BR Multi-turn Provenance and Recursive Authority",
        "campaign_date": "2026-10-03",
        "purpose": (
            "Small multi-turn live validation of provenance survival and recursive authority. "
            "Two isolated four-turn sequences. No production edits."
        ),
        "primary_report": "artifacts/pr_br_multiturn_provenance/20261003T223147Z/validation_report.md",
        "executive_summary": (
            "Eight gameplay turns, two isolated sequences, scored 4 PASS and 4 FAIL. "
            "Linden's brine-cask statement stayed hearsay through movement, the osier-rack transition "
            "was recorded on GMResolutionDecision, and a footprint sentence was rejected. "
            "Sequence A did not hold. An unfired-jar inference was audited as authored world truth, "
            "the next turn used it as the event, and the following turn said it was clear the jar was "
            "never fired in a kiln while validation rejected the uncertainty sentence. "
            "Scene JSON did not gain the kiln fact. Narration and the audit label did. "
            "Exact model/API calls: 15 (8 initial generations, 4 retries, 2 interpretations, 1 preflight). "
            "Decision C. Multi-turn validation reproduced recursive authority failure. Return to architectural review."
        ),
        "objective_status": "recursive_authority_failure_reproduced_return_to_architectural_review",
        "changes": {
            "production": [],
            "validation": [
                "Ran 8 gameplay turns in two isolated sequences. No failed turn was rerun. No production code was changed."
            ],
            "tooling": [
                "Added a measurement harness under artifacts/pr_br_multiturn_provenance/. It is not production."
            ],
            "documentation": ["Wrote the 22-section validation report beside the turn artifacts."],
            "generated_artifacts": [
                "artifacts/pr_br_multiturn_provenance/20261003T223147Z/ holds both initial states, all eight turn artifacts, call logs, and the report."
            ],
        },
        "testing": {
            "focused": "Not run. This cycle was live measurement only.",
            "broader": "Not run. The 4x10 gate was not run.",
            "full_suite": "Not run.",
            "runtime_validation": "8 POST /api/chat turns. Manual 4 PASS / 4 FAIL. Passes: A1, B1, B2, B4. Fails: A2, A3, A4, B3.",
            "model_runtime_boundary": "8 gameplay turns. 8 initial generation calls. 4 retry generation calls. 2 interpretation calls. 1 startup preflight. 0 other model calls. 15 total model/API calls. 0 reruns.",
            "new_regressions": "No production patch. Live finding: narrated-fact identity match labels causal add-ons as authored world truth, and preservation drops the hedged sentence.",
            "pre_existing_failures": "Split-quotation attributed testimony and guard_captain versus gate_guard were not repaired, not reinterpreted, and did not appear in these scenes.",
        },
        "self_contained_review_test": "Bundle contains the validation report, both initial states, all eight turn artifacts, call logs, the harness, and the production modules that classify narrated facts and preserve sentences.",
        "decisions_requiring_human_review": [
            "C. MULTI-TURN VALIDATION REPRODUCED RECURSIVE AUTHORITY FAILURE; RETURN TO ARCHITECTURAL REVIEW.",
            "Review classify_narrated_fact: a sentence that contains an authorized observation plus a new cause, certainty, or corroborating clue currently inherits world_truth when subject and value terms match.",
            "Review preservation: unsupported_narrator_lead removed the uncertainty sentences on A4 and kept the kiln certainty.",
            "B3 is a separate mixed-intent gap. Travel and the location mutation held. The thanks was not an obligation and was not spoken.",
            "Do not start a broader release-candidate gate, the 4x10 gate, or PR-BS on this evidence.",
        ],
        "known_problems": {
            "campaign_specific": [
                "A2 audited the unfired/process-disruption sentence as authored_world_fact world_truth.",
                "A3 used leave-the-jar-unfired as the event and recorded only an unresolved actor.",
                "A4 emitted that it was clear the jar was never fired in a kiln and that the coil-pots show no signs of firing. The uncertainty sentence was rejected.",
                "Scene visible facts did not gain those propositions. Narration and later prompts did.",
                "B3 committed osier_rack and recorded the location mutation. The thanks and both referents were unspoken. Supporting obligations were empty.",
                "Rejected proposals and B1 incidental lines were not written to the bounded ledger.",
            ],
            "pre_existing": [
                "Split quotation / attributed-testimony edge case remains unrepaired.",
                "guard_captain versus gate_guard addressability mismatch remains unrepaired.",
            ],
        },
        "missing_concepts": [
            "A narrated sentence needs a split between the authorized observation and any additional cause, certainty, or corroborating clue.",
            "Hedged unknown-cause or unknown-actor sentences should not be deleted as narrator leads while the assertive version of the same idea is kept.",
            "Rejected consequential proposals and accepted mundane incidental details need a ledger if later turns are to respect them as policy rather than as raw transcript.",
            "A mixed utterance still needs one supporting social obligation when travel is the primary act.",
        ],
        "does_not_prove": [
            "Does not prove the commit store will adopt the kiln sentence on a fifth turn. Scene JSON did not adopt it in four turns.",
            "Does not prove a rejected footprint would be blocked later. The rejection was not stored, and no fifth turn was run.",
            "Does not rerun the 4x10 gate.",
            "Does not show the two known deterministic failures are fixed.",
            "Does not authorize PR-BS or a broader release-candidate gate.",
        ],
        "recommended_next_step": "C. MULTI-TURN VALIDATION REPRODUCED RECURSIVE AUTHORITY FAILURE; RETURN TO ARCHITECTURAL REVIEW.",
        "supporting_files": files,
    }
    out = ROOT / "artifacts" / "pr_br_multiturn_provenance" / "handoff_config.json"
    out.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"wrote {out} with {len(files)} supporting files")


if __name__ == "__main__":
    main()
