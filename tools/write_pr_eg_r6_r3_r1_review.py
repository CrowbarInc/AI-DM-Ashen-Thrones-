"""Package the PR-EG-R6-R3-R1 review from recorded production evidence."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts" / "pr_eg_r6_r3_r1"
VERDICT = "C — BELOW ACCEPTANCE"


def write(name, body):
    (OUT / name).write_text(body.strip() + "\n", encoding="utf-8")


def main():
    freeze = json.loads((OUT / "freeze.json").read_text(encoding="utf-8"))
    sections = {
        1: f"""
# 01 — Executive Summary

Host-constrained candidate selection is now a third routing mode. It is off unless `ASHEN_HOST_CONSTRAINED_CANDIDATES` is set, and it still ends in the existing source, disclosure, and sealed-response pipeline.

On 150 fresh `/api/chat` turns, integrity held: 0 unauthorized disclosures, 0 canonical mutations, 0 clue discoveries, and 0 final-response mismatches. Conversational gates did not. Independent labels scored operation classification 99/150, role preservation 83/150, answer success 70/150, corrections 13/25, and follow-ups 26/50. A 60-turn matched comparison did not beat the existing semantic planner.

Verdict: {VERDICT}. The gate stays off. Do not begin PR-EH.
""",
        2: """
# 02 — Repository Baseline

HEAD is `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`PR-BN bounded DM improvisational authority`). The working tree was already dirty with the uncommitted Product Realization history. Provider configuration comes from the repo `.env`: an OpenAI key is present and `MODEL_NAME` is set. Semantic planning remains `ASHEN_UNIFIED_SEMANTIC_PLANNING`, default off. Referents live in `game/conversational_referents.py`. Authorization, disclosure, and sealing remain `authorize_information_turn`, `game/dialogue_authority.py`, and `game/immutable_valid_response.py`.
""",
        3: """
# 03 — Architecture C Prototype Audit

`experiments/pr_eg_r6_r3/architecture_c.py` builds candidates from referent roles, asks the provider to pick one id, and rejects unknown ids. It does not call production bind, disclosure, or final adoption. Reused without importing the experiment harness: host-owned ids, no nearest-candidate repair, witness checks, and an explicit none/clarify choice. Not reused: the experiment's in-memory case shape, its grader, or its direct answer-class assignment.
""",
        4: """
# 04 — Production Integration Design

`game/host_constrained_candidates.py` generates candidates and compiles one selection into the existing plan schema. `propose_semantic_plan` uses that path only when the candidate gate is on. `authorize_information_turn` then performs referent bind, source coverage, disclosure, and the locked host line. A clarification shell uses conversational act `other` plus `clarification_needed`, and only while the candidate gate is on, so the semantic planner's rejection behavior is unchanged.
""",
        5: """
# 05 — Feature-Gate Strategy

Three modes, one new flag:

- Both flags off: legacy routing.
- `ASHEN_UNIFIED_SEMANTIC_PLANNING` on and the candidate flag off: existing R6 semantic planner.
- Both on: host-constrained candidates.

The candidate flag defaults off. Traces record `routing_mode`. Turning the flag off returns the next turn to the semantic planner. `plan_proposer` remains the test seam for that planner and is not consulted while candidate mode is on.
""",
        6: """
# 06 — Candidate Generation

`generate_candidates` reads durable referents, participant identities, and outstanding clarification. It does not read the player utterance. Every live referent can yield role replacement, a two-participant reversal, multi-role reassignment, predicate and requested-role changes, temporal and spatial changes, negation, and the six follow-up forms. `new`, `clarify`, and `none` are always present. Corrected referents and other conversations are omitted. The list is capped at 64.
""",
        7: """
# 07 — Candidate Representation

Each candidate has a host nonce, kind, referent id when needed, required fills, a constraint, and a description. Descriptions use proposition roles the player already supplied. Delivered NPC speech is not copied into the provider payload. Candidate ids are valid only for the turn that minted them.
""",
        8: """
# 08 — Provider Selection Contract

The provider returns one `candidate_id`, optional `ranked_ids`, witnessed fills, and up to four source interpretations. Ranking is stored and never repairs an invalid id. Raw output is appended to `ASHEN_SEMANTIC_TRACE_PATH`. The provider does not receive hidden topic text; permitted sources are the same non-secret rows the existing planner already shows.
""",
        9: """
# 09 — Host Validation

The host rejects unknown, forged, and cross-turn ids. A referent must belong to the current conversation and must not be a corrected record. Replacement values are kept only when the value occurs in the player utterance; a paraphrased evidence quote is narrowed to that value, and a value that does not occur is rejected. Unlisted roles are copied. Empty reversals that also fill new values are rejected (`reverse_must_be_empty`). Failed selections do not commit referents.
""",
        10: """
# 10 — New Questions

The `new` candidate is a fresh proposition. It does not copy an existing referent. Predicate, known roles, and the requested role are required. In the fresh run, the cistern question often compiled and returned the public fact as a partial answer. Other new questions frequently compiled and then found no matching source proposition.
""",
        11: """
# 11 — Corrections

Subject, object, relationship, requested-role, temporal, spatial, negation, single-role, and multi-role replacements are representable. Reversal is offered for whichever two roles name present participants, so a model that says `addressee` instead of `recipient` still gets a swap candidate. Fresh-run corrections succeeded on the independent label 13/25. Several failures were `reverse_must_be_empty`: the model selected reversal and also filled values, and the host refused to guess.
""",
        12: """
# 12 — Multi-Role Propositions

The Mara/Oren/road shape is covered by controlled tests: reversal changes speaker and recipient, leaves the topic, and leaves `message_content` requested. The fresh cistern turns used `speaker`, `addressee`, and `topic`. The known people and topic were often right. The requested role was often a generic name such as `value`, so strict role preservation still failed.
""",
        13: """
# 13 — Follow-Ups

Source attribution, explanation, evidence, temporal change, alternative argument, and speech clarification are separate candidates. They keep the target proposition and change only the requested slot. Follow-up operation success on the fresh run was 26/50. "Who told you?" after an unknown answer took the existing `referenced_answer_unknown` path and did not invent an informant.
""",
        14: """
# 14 — Genuine Ambiguity

If the same candidate kind exists on another live referent and the utterance does not mention a distinguishing argument, the host asks which question is meant instead of keeping the newest one. `clarify` with only one live referent is rejected as false ambiguity. The fresh run produced 41 clarification responses. 13 of those fell on turns that were not pre-labeled as ambiguity-tolerant (13/150). That is under a 10% share of all turns, but it is not a clean 80% measurement of genuine-clarification cases.
""",
        15: """
# 15 — Unsupported Transformations

`none` is an explicit unsupported result. It becomes conversational act `other` and does not commit a referent. Multi-role change has a `reassign` candidate that requires at least two witnessed roles. A single-role payload on that candidate is rejected rather than forced into a different operation. The provider is not given a free-form operation fallback.
""",
        16: """
# 16 — Open-World Generalization

Candidate kinds are derived from whatever role names are already on the referent. The controlled suite includes an unfamiliar `steward` / `instrument` question. Generation does not contain the pilot phrases "amber lens" or "countersign". The fresh cast uses Vesper, Cala, Brin, a cistern, and an amber lens, none of which are hard-coded in the generator. The fresh model still often failed to attach a usable source interpretation, so open-world questions were safe and frequently unanswered.
""",
        17: """
# 17 — Source Resolution

Accepted plans call the existing coverage path. Candidate mode does not grant a fact because a source id was mentioned. Source epistemic status is copied from the host topic record, so a rumor stays a rumor. A temporal follow-up whose source lacks the requested time is downgraded from partial to `related_but_nonanswer`, which stops the untimed fact from being spoken as the answer to "tomorrow".
""",
        18: """
# 18 — Disclosure Authorization

Secret topics are omitted from the provider payload. A source id that is not in that payload is dropped. Across the candidate-mode pilot, the 150 fresh turns, and the 60 planner turns, player-facing text never contained `gray-lantern`. Historical delivered speech is not re-sent to the candidate model. Controlled tests cover a direct secret, a paraphrased secret id, and a secret planted only in delivered speech.
""",
        19: """
# 19 — Answer Sufficiency

The fresh run returned 9 partial answers, 0 direct answers, 93 unknown, 41 clarification, 1 refusal, and 6 turns whose stored plan had no response kind. The cistern fact was sometimes delivered as a partial because the source proposition did not fill the requested role, even though the authorized sentence contained the public fact. The amber-lens fact was usually not delivered: the model selected `new` and sent no usable source proposition. Safe unknowns were not counted as answer success unless the operation and the topic also matched.
""",
        20: """
# 20 — Final-Response Integrity

All 150 fresh turns and all 60 matched planner turns passed `sealed`, `exact`, and `history_exact`. Adopted speech matched the API text, and that text matched stored history. Candidate rejection still returns a sealed host line rather than an unsealed provider draft.
""",
        21: """
# 21 — Referent Persistence

Referents commit only inside the existing delivery path, after the sealed exchange is recorded. Controlled tests show no commit before adoption, no focus change after a forged id, and a save/load round trip that keeps the corrected topic and the parent id. Every fresh turn's `reload` check passed, including the turns marked for a session reload.
""",
        22: """
# 22 — Legacy Regression Disposition

The 14 R6-R2-R2 identities were re-run. They still fail because the tests expect a player clarification and the host returns a safe unknown. That is the same intended fail-closed disposition recorded in `artifacts/pr_eg_r6_r2_r2/regression_comparison.json`. Assertions were not rewritten.

- Three `test_forged_authority_or_entity_rejected` cases: safety-preserving rejection.
- Two `test_bad_prior_target_cannot_launder_history` cases: safety-preserving rejection.
- Eight `test_untrusted_operations_fail_closed_without_losing_focus` cases: safety-preserving rejection. Focus is kept.
- `test_unqualified_historical_id_cannot_override_focus`: stricter than the no-silent-override rule. An unqualified historical id does not steal focus. Left for external review; not relaxed in this cycle.

Disclosure, provenance, semantic-planner, and operation suites passed apart from those 14.
""",
        23: """
# 23 — Controlled Tests

`tests/test_pr_eg_r6_r3_r1_candidates.py` contains 68 tests, including T01–T66 plus paraphrased-evidence grounding and participant-role reversal. `python -m pytest tests/test_pr_eg_r6_r3_r1_candidates.py -q` passed. The tests do not call the network. They drive the compiler and `authorize_information_turn` through the selector seam.
""",
        24: f"""
# 24 — Frozen Holdouts

Previous holdout files were not edited. Hashes recorded in `artifacts/pr_eg_r6_r3_r1/freeze.json`:

{json.dumps(freeze, indent=2)}

`frozen_production_holdouts.json` was written before the live pilots and names meanings rather than candidate ids. Its hash is in the same file. The fresh qualification uses a separate cast and is not a rewrite of those holdouts.
""",
        25: """
# 25 — Matched Production Comparison

The same 60 utterances, cast, and `/api/chat` path were run twice. Candidate mode: operation 41/60, roles 33/60, answers 29/60, corrections 5/10, follow-ups 12/20. Existing semantic planner: operation 46/60, roles 43/60, answers 37/60, corrections 4/10, follow-ups 14/20. Both leaked nothing and failed no integrity check. Candidate mode did not improve the matched production result. Corrections were the only family with a one-turn edge, 5 against 4.
""",
        26: """
# 26 — Fresh-Provider Qualification

`tools/qualify_pr_eg_r6_r3_r1.py` ran 10 conversations and 150 turns through production `/api/chat` with the real provider and the candidate gate on. Status is `completed`. Raw turns are `artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl`. The set includes new questions, reversals, follow-ups, a partial roster, uncertainty, a restricted countersign, reloads, and underspecified follow-ups. It is not padded with repeated identical successes.
""",
        27: """
# 27 — Independent Evaluation

`tools/score_pr_eg_r6_r3_r1.py` labels each utterance's intended operation and topic without reading `candidate_id`. A safe "I couldn't tell you" counts only when the operation and topic also match. Fresh totals: operation 99/150, roles 83/150, answers 70/150, corrections 13/25, follow-ups 26/50. Disclosure failures: 0/150. Integrity-check failures: 0/150.
""",
        28: """
# 28 — Dialogue Quality

The best fresh pattern is the public cistern fact, delivered as a hedged partial: the sentence contains the authorized fact and then says no more could be said. The common pattern is a compiled question followed by "I couldn't tell you" because no source proposition matched. Reversals were often rejected before an answer. Restricted questions stayed unanswered. That is safe play and poor play. I would not turn the gate on for a table.
""",
        29: """
# 29 — Performance

Fresh provider log, 220 calls: 145 `semantic_candidate`, 73 `expression`, 2 `interpretation`. Candidate-call input tokens: mean 4,788, p95 6,418, max 6,719. Expression calls are small (mean about 160 input tokens). Candidate-call latency mean is inside the mixed-call mean of 2.1 seconds; mixed p95 latency was 3.3 seconds and the maximum was 16.8 seconds. The interpretation target was mean input at or below 3,500 and p95 at or below 5,000. Candidate calls missed both. There was no retry storm: 145 candidate calls across 150 turns.
""",
        30: """
# 30 — Regression

Passed: the new 68-test module; `tests/test_pr_eg_r6_r3_harness.py`; `tests/test_pr_eg_r6_unified_semantic_planning.py`; `tests/test_pr_eg_r6_r2_r2_operations.py`; disclosure and provenance suites. Failed, all pre-existing and explained in section 22: 14 contract tests that still want a clarification where the host returns unknown. No new failing identity was found in those suites. The full repository suite was not run.
""",
        31: """
# 31 — Acceptance Gates

| Gate | Result |
| --- | --- |
| 1 Operation >=90% | Fail, 99/150 |
| 2 Referent/role binding >=90% | Fail, 83/150 |
| 3 Role preservation >=90% | Fail, 83/150 |
| 4 Corrections >=80% | Fail, 13/25 |
| 5 Follow-ups >=80% | Fail, 26/50 |
| 6 Genuine clarification >=80% | Not established |
| 7 False clarification <=10% of turns | 13/150 on non-tolerant turns; not a clean pass |
| 8 Relevance improves on the matched baseline | Fail, 29/60 answers against 37/60 |
| 9 Sufficiency, no systematic regression | Fail, matched answers were lower |
| 10 Disclosure | Pass, 0 leaks |
| 11 Canonical state | Pass, 0 mutations |
| 12 Discovery | Pass, 0 unauthorized clues |
| 13 Final delivery | Pass, 0 mismatches |
| 14 Save/load | Pass, reload checks held |
| 15 New critical regressions | Pass for the suites that were run |
| 16 Performance | Fail, candidate input p95 6,418 |
| 17 Frozen holdouts show improvement | Not shown; matched production did not improve |
| 18 Production /api/chat | Pass as a completed run, not as a quality pass |
""",
        32: """
# 32 — Failure Attribution

Representative fresh failures, earliest cause:

- "No, what did Brin tell Cala?" often died at host validation, reason `reverse_must_be_empty`. The model selected the reversal candidate and also filled values.
- "Vesper, who keeps the amber lens?" often compiled as a new question and then died at source resolution, reason `no_relevant_source`. The model did not supply a source proposition whose evidence survived the host check. The public sentence was available.
- "What about tomorrow?" was sometimes a real ambiguity among several live questions (`candidate_ambiguity`) and sometimes a temporal follow-up that correctly refused to repeat an untimed fact.
- "Which person exactly?" sometimes failed `unwitnessed_role` before a follow-up could bind.
- Restricted countersign turns failed closed at source resolution or as unknown. That is disclosure success, not interpretation success.

These are not one undifferentiated model failure. The host both prevented bad swaps and rejected repairs that would have answered public questions.
""",
        33: """
# 33 — Remaining Limitations

Candidate lists grow with every committed question, and input tokens already miss the budget. The provider often selects a legal candidate and then fills the wrong slots, especially reversal. Source interpretations are still required for a direct answer, and the model often omits them. Partial delivery can speak a whole public source when only some roles match. The 14 older contract tests remain red on purpose. Matched production play is slightly worse than the current planner.
""",
        34: """
# 34 — Recommended Next Action

Keep the candidate gate off. Do not start PR-EH. The next review should decide whether to continue this architecture at all. If it continues, the first problem is source interpretation and reversal fills, not another phrase list. If it stops, the existing semantic planner remains the gated production path.
""",
        35: f"""
# 35 — Final Verdict

{VERDICT}

Integrity gates passed on the production path. Conversational gates and the matched comparison did not. The result is not qualified, and it is not an authorization bypass.
""",
        36: """
# 36 — Source and Evidence Inventory

Production: `game/host_constrained_candidates.py`, the candidate branch in `game/unified_semantic_planning.py`.

Tests: `tests/test_pr_eg_r6_r3_r1_candidates.py`.

Qualification: `artifacts/pr_eg_r6_r3_r1/fresh/live_turns.jsonl`, `fresh/live_usage.jsonl`, `fresh/semantic_traces.jsonl`, `fresh/live_status.json`, `matched_planner/live_turns.jsonl`, `matched_candidate_60.jsonl`, `freeze.json`, `frozen_production_holdouts.json`.

Scoring: `tools/score_pr_eg_r6_r3_r1.py`, `tools/qualify_pr_eg_r6_r3_r1.py`.

Disposable session directories under `fresh/state` and `matched_planner/state` are local run state and are not part of the portable bundle.
""",
    }
    titles = {
        1: "EXECUTIVE_SUMMARY", 2: "REPOSITORY_BASELINE", 3: "ARCHITECTURE_C_PROTOTYPE_AUDIT",
        4: "PRODUCTION_INTEGRATION_DESIGN", 5: "FEATURE_GATE_STRATEGY", 6: "CANDIDATE_GENERATION",
        7: "CANDIDATE_REPRESENTATION", 8: "PROVIDER_SELECTION_CONTRACT", 9: "HOST_VALIDATION",
        10: "NEW_QUESTIONS", 11: "CORRECTIONS", 12: "MULTI_ROLE_PROPOSITIONS", 13: "FOLLOW_UPS",
        14: "GENUINE_AMBIGUITY", 15: "UNSUPPORTED_TRANSFORMATIONS", 16: "OPEN_WORLD_GENERALIZATION",
        17: "SOURCE_RESOLUTION", 18: "DISCLOSURE_AUTHORIZATION", 19: "ANSWER_SUFFICIENCY",
        20: "FINAL_RESPONSE_INTEGRITY", 21: "REFERENT_PERSISTENCE", 22: "LEGACY_REGRESSION_DISPOSITION",
        23: "CONTROLLED_TESTS", 24: "FROZEN_HOLDOUTS", 25: "MATCHED_PRODUCTION_COMPARISON",
        26: "FRESH_PROVIDER_QUALIFICATION", 27: "INDEPENDENT_EVALUATION", 28: "DIALOGUE_QUALITY",
        29: "PERFORMANCE", 30: "REGRESSION", 31: "ACCEPTANCE_GATES", 32: "FAILURE_ATTRIBUTION",
        33: "REMAINING_LIMITATIONS", 34: "RECOMMENDED_NEXT_ACTION", 35: "FINAL_VERDICT",
        36: "SOURCE_AND_EVIDENCE_INVENTORY",
    }
    for number, body in sections.items():
        write(f"{number:02}_{titles[number]}.md", body)
    config = {
        "campaign_id": "pr_eg_r6_r3_r1_candidate_integration_20261017",
        "campaign_name": "PR-EG-R6-R3-R1 — Host-Constrained Candidate Integration",
        "campaign_date": "2026-10-17",
        "purpose": "Integrate host-constrained candidate selection into the production conversational pipeline without bypassing authorization.",
        "objective_status": VERDICT,
        "executive_summary": sections[1].split("\n", 2)[-1].strip(),
        "self_contained_review_test": "Structural package verification only. This is not independent human review.",
        "changes": {
            "production": ["game/host_constrained_candidates.py", "game/unified_semantic_planning.py"],
            "validation": ["tests/test_pr_eg_r6_r3_r1_candidates.py"],
            "tooling": ["tools/qualify_pr_eg_r6_r3_r1.py", "tools/score_pr_eg_r6_r3_r1.py", "tools/write_pr_eg_r6_r3_r1_review.py"],
            "documentation": ["36 numbered review artifacts."],
        },
        "testing": {
            "focused": "68 candidate tests passed without network calls.",
            "broader": "Semantic planner, operation, disclosure, and provenance suites passed except the 14 previously explained contract failures.",
            "full_suite": "Not run.",
            "runtime_validation": "150 fresh /api/chat turns and 60 matched planner turns, real provider.",
            "model_runtime_boundary": "Configured repo model, temperature 0 for candidate selection.",
            "new_regressions": "[]",
            "pre_existing_failures": "14 R6-R2-R2 contract tests still expect clarification and receive unknown.",
        },
        "known_problems": {
            "campaign_specific": [
                "Matched production correctness did not improve.",
                "Candidate input tokens miss the p95 budget.",
                "Public facts are often dropped because source interpretations are missing.",
            ],
            "pre_existing": ["Fourteen red contract tests remain fail-closed unknowns."],
        },
        "decisions_requiring_human_review": [
            "Whether to keep developing candidate selection or leave the existing semantic planner as the only gated path.",
            "Whether the unqualified-historical-id test should stay stricter than silent-focus preservation.",
        ],
        "does_not_prove": ["Human playability, a 90% operation rate, or a cost reduction against the current planner."],
        "recommended_next_step": "Stop after PR-EG-R6-R3-R1. Leave the candidate gate off. Do not begin PR-EH.",
        "primary_report": "artifacts/pr_eg_r6_r3_r1/01_EXECUTIVE_SUMMARY.md",
        "supporting_files": [],
        "max_file_bytes": 50000000,
        "warn_bundle_bytes": 100000000,
    }
    supporting = []
    paths = [
        *sorted(OUT.glob("*.md")),
        OUT / "freeze.json",
        OUT / "frozen_production_holdouts.json",
        OUT / "fresh" / "live_turns.jsonl",
        OUT / "fresh" / "live_usage.jsonl",
        OUT / "fresh" / "live_status.json",
        OUT / "fresh" / "semantic_traces.jsonl",
        OUT / "matched_planner" / "live_turns.jsonl",
        OUT / "matched_planner" / "live_usage.jsonl",
        OUT / "matched_planner" / "live_status.json",
        OUT / "matched_candidate_60.jsonl",
        ROOT / "game" / "host_constrained_candidates.py",
        ROOT / "game" / "unified_semantic_planning.py",
        ROOT / "tests" / "test_pr_eg_r6_r3_r1_candidates.py",
        ROOT / "tools" / "qualify_pr_eg_r6_r3_r1.py",
        ROOT / "tools" / "score_pr_eg_r6_r3_r1.py",
    ]
    for path in paths:
        if not path.exists():
            continue
        supporting.append({
            "path": path.relative_to(ROOT).as_posix(),
            "role": "cycle_evidence",
            "why": "PR-EG-R6-R3-R1 integration and production-path evidence.",
            "behavioral_evidence": path.suffix == ".jsonl",
            "human_review_required": path.suffix in {".md", ".py"},
        })
    config["supporting_files"] = supporting
    (OUT / "handoff_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    from tools.build_review_handoff import build_handoff
    result = build_handoff(config, root=ROOT, output_dir=ROOT / "handoff")
    print(json.dumps({"verdict": VERDICT, "files": result.get("file_count"), "zip": result.get("zip_path")}, indent=2))


if __name__ == "__main__":
    main()
