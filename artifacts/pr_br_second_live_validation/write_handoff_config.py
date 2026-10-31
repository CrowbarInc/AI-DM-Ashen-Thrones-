#!/usr/bin/env python3
"""Build the review handoff config for the second live validation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAMP = ROOT / "artifacts" / "pr_br_second_live_validation" / "20261003T190253Z"


def main() -> None:
    files = []
    for path in sorted(STAMP.rglob("*")):
        if path.is_file() and path.name != "validation_report.md":
            files.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "role": "turn_artifact",
                    "why": "Saved live-probe evidence for external review.",
                    "behavioral_evidence": True,
                    "human_review_required": True,
                }
            )
    files.append(
        {
            "path": "artifacts/pr_br_second_live_validation/run_probes.py",
            "role": "validation_harness",
            "why": "Exact fresh seeds, player lines, and capture path for the eight turns.",
            "behavioral_evidence": True,
            "human_review_required": True,
        }
    )
    modules = (
        (
            "game/gm_resolution_decision.py",
            "Event-site qualifier check and decision attachment used by these turns.",
        ),
        (
            "game/immutable_valid_response.py",
            "Retry context and bounded sentence preservation used on turn 1.",
        ),
        (
            "game/ordinary_semantic_ownership.py",
            "Resolver selection that followed contract subject on every turn, including probe 7.",
        ),
    )
    for path, why in modules:
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
        "campaign_id": "pr-br-second-live-validation",
        "campaign_name": "PR-BR Second Limited Live Validation",
        "campaign_date": "2026-10-03",
        "purpose": (
            "Fresh 8-turn live measurement of GMResolutionDecision attachment, "
            "semantic fidelity, retry context, and the known mixed social/travel resolver path."
        ),
        "primary_report": "artifacts/pr_br_second_live_validation/20261003T190253Z/validation_report.md",
        "executive_summary": (
            "Eight fresh isolated gameplay turns scored 5 PASS and 3 FAIL. Every Resolution Contract "
            "carried a GMResolutionDecision whose contract_id matched. The first validation's missing-decision "
            "gap and the sentence-local negation reject did not recur, and the generic no-answer line was not "
            "emitted. The sluice turn still rejected a correct unknown-cause sentence as an event-site location "
            "fill, then preservation removed that sentence and kept a missing-patrol lead. The sail-loft move "
            "committed, while the decision recorded no location mutation and narration added an upward stair. "
            "The mixed thanks-and-courtyard line selected travel and moved; it did not reproduce the six "
            "social-blocks-travel failures, and it dropped the thanks. Exact model/API calls: 11 "
            "(8 initial generations, 1 retry, 1 interpretation, 1 preflight). Recommendation: localized defects. "
            "Return to targeted implementation. The six scene-transition tests remain unrepaired."
        ),
        "objective_status": "measured_localized_defects_for_targeted_implementation",
        "changes": {
            "production": [],
            "validation": ["Ran 8 isolated live gameplay turns. No production code was changed."],
            "tooling": [
                "Added a measurement harness under artifacts/pr_br_second_live_validation/. It is not production."
            ],
            "documentation": ["Wrote the 20-section validation report beside the turn artifacts."],
            "generated_artifacts": [
                "artifacts/pr_br_second_live_validation/20261003T190253Z/ holds initial states, contracts, decisions, generations, validation metadata, committed states, and the report."
            ],
        },
        "testing": {
            "focused": "Not run. This cycle was live measurement only.",
            "broader": "Not run. The six scene-transition failures were not rerun and not patched.",
            "full_suite": "Not run.",
            "runtime_validation": "8 isolated POST /api/chat turns. Manual 5 PASS / 3 FAIL. Passes: turns 2, 3, 4, 5, 8. Fails: turns 1, 6, 7.",
            "model_runtime_boundary": "8 gameplay turns. 8 initial generation calls. 1 retry generation call. 1 interpretation call. 1 startup preflight. 11 total model/API calls. 0 reruns. 0 gate sessions.",
            "new_regressions": "No production patch. Live defects are an event-site false reject plus preservation of the wrong sentence, a movement decision with empty permitted mutations, and a mixed utterance contracted as travel only.",
            "pre_existing_failures": "Six failures remain in tests/test_scene_transition_authority.py. Probe 7 did not reproduce social-blocks-travel. It selected travel, committed the courtyard, and omitted the thanks. Those six tests were not repaired.",
        },
        "self_contained_review_test": "Bundle contains the validation report, all 8 turn artifacts, call logs, the harness, and the production modules that implement qualifier checks, preservation, and resolver selection.",
        "decisions_requiring_human_review": [
            "B. SECOND LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.",
            "Next implementation should stop the event-site pattern from rejecting an unknown cause, actor, and time, and should keep preservation from deleting that sentence while retaining an unrelated lead.",
            "Movement decisions should record the location mutation the travel resolver commits, so arrival narration is not steered by the departure stair.",
            "Mixed social-and-travel ownership remains a separate question. Probe 7 did not reproduce the six social-blocks-travel failures. Do not treat those tests as fixed.",
            "Do not start a multi-turn validation, the 4x10 gate, a human playtest, or PR-BS on this evidence.",
        ],
        "known_problems": {
            "campaign_specific": [
                "Turn 1 rejected the unseen-cause sentence as unauthorized_qualifier:location, then bounded preservation removed it and kept a missing-patrol lead.",
                "Turn 1 retry context included the contract and the decision. The retry generation was empty (malformed_or_truncated).",
                "Turns 6 and 7 record permitted_state_mutations as empty and outcome consequentially_unresolved after a committed scene_transition.",
                "Turn 6 narration adds a stair that leads upward after arrival in the sail loft.",
                "Turn 7 contract subject is travel. The thanks is not narrated. Social did not block the move.",
            ],
            "pre_existing": [
                "Six tests in tests/test_scene_transition_authority.py still fail when a social contract blocks travel. They were not rerun and not repaired.",
                "The second full gate remained 8/40. This cycle did not rerun it.",
            ],
        },
        "missing_concepts": [
            "Unknown-cause wording such as remain unseen must count as an unresolved slot, and happened-here must not match that wording.",
            "A committed scene_transition should be a permitted location mutation on the decision that narrates the arrival.",
            "A separate review of mixed-utterance ownership, using the six existing scene-transition failures as the social-blocks-travel evidence.",
        ],
        "does_not_prove": [
            "Does not prove multi-turn continuity.",
            "Does not prove the six scene-transition tests would pass.",
            "Does not rerun the 4x10 gate.",
            "Does not authorize a human playtest or PR-BS.",
            "Does not show that an empty retry can repair a false qualifier reject. Preservation edited the first generation instead.",
        ],
        "recommended_next_step": "B. SECOND LIVE VALIDATION EXPOSED LOCALIZED DEFECTS; RETURN TO TARGETED IMPLEMENTATION.",
        "supporting_files": files,
    }
    out = ROOT / "artifacts" / "pr_br_second_live_validation" / "handoff_config.json"
    out.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"wrote {out} with {len(files)} supporting files")


if __name__ == "__main__":
    main()
