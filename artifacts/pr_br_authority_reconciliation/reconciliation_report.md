# PR-BR Authority Regression Reconciliation

Date: 2026-10-03

C19 grounded-fact / decision-audit alignment. Deterministic only. No gameplay or model API calls.

## 1. Executive conclusion

The live decision audit is right to reject the generated third-bell narration. The authored fact states one proposition: the city gate closes when the watch changes at the third bell. The generated lines add who may pass before that moment, and how long the gate stays closed afterward. Those additions are not in the authored sentence, and they are not entailed by it.

The older corpus test accepted both lines because a schedule sentence that mentions "third bell" was treated as grounded whenever the corpus also contained that anchor. The live `GMResolutionDecision` path does not do that. It keeps a lexical restatement of the authored sentence and rejects the extra schedule claims.

Production behavior stays strict. The stale expectation was updated. A failed retry now quotes the authored sentence instead of dropping the answer.

## 2. Original C19 invariant

`test_grounded_third_bell_is_authoritative_and_kept` and the grounded half of `test_raw_chat_stub_authority_and_contracts` were protecting the schedule anchor in `game/proposition_authority.py`. `_schedule_anchor_grounded` marks a sentence grounded when its time token (here, "third bell") appears in a corpus that also looks institutional (close, curfew, or watch).

That check answers a coarser question than proposition-level claim control. Any schedule-family sentence that shares the anchor passes, including sentences that add new operational claims. In practice the old tests required outcome A for the schedule family: once the third-bell fact is grounded, narration that mentions it survives.

The invariant that matches the current architecture is B. A grounded fact may be said. Unsupported additions do not inherit it. C19's live path already implemented B. The tests still encoded A.

## 3. Proposition decomposition

Authored fact: "The city gate closes when the watch changes at the third bell."

- P1. Subject: the city gate. Relation: closes. Condition: when the watch changes at the third bell.

That sentence does not state that the gate is open now, that travelers may pass, that a particular entrance is the one in use, or that the closing lasts until morning. Under current game semantics it also does not structurally entail those claims. A closing event at a named time is the whole proposition.

Generated sentence 1: "Travelers can still pass, but only until the watch changes at the third bell."

- P2. Travelers can pass before the watch changes.
- P3. That permission ends at the third-bell watch change.

The sentence does not say the gate closes. It borrows the authored time and attaches an access rule.

Generated sentence 2: "After that, the gates close until morning."

- P4. The gates close after the event in the previous sentence.
- P5. They remain closed until morning.

## 4. Entailment classification

| Proposition | Class | Why |
| --- | --- | --- |
| P1, gate closes at the third-bell watch change | Explicitly authored | It is the visible fact. |
| Lexical omission, "The gate closes at the third bell." | Same authored proposition | Content words are a subset of the fact. No new claim. |
| P2, travelers can pass beforehand | Unauthorized consequential addition | A gate may already be shut, or passage may require permission. The fact only names a closing event. |
| P3, that access ends at the third bell | Unauthorized consequential addition | The time is authored. The access rule is not. |
| P4, the gates close after that event | Not a faithful restatement by itself | "After that" depends on the previous sentence, and the wording is not the authored closing condition. |
| P5, closed until morning | Unauthorized consequential addition | The fact does not say the gate stays closed, or when it opens. |

Nothing here is structurally entailed, a reasonable inference the authority system should honor, or bounded incidental texture. Conversational plausibility is not authority.

Safe entailment boundary: the narration may restate the authored closing with the authored words, including by omitting some of them. It may add at most one content word. It may not add a second operational proposition.

## 5. Decision-row analysis

The visible fact is stored as a string on `scene.visible_facts`. `_text_and_identity` returns that string and an empty identity, because a string has no `semantic_identity` mapping. The decision row is authorized, `authority = world_truth`, `semantic_identity = {}`.

There is no existing structured source for subject, relation, and time. Deriving one would mean parsing arbitrary prose. That was not done. The compatibility fallback stays lexical.

Empty identity does not match by itself. Coverage is `_empty_identity_covers`:

- the sentence's content words are a subset of the fact's content words, or
- the sentence adds at most one content word and still nearly restates the fact.

"The gate closes when the watch changes at the third bell." and "The gate closes at the third bell." are subsets, so they are covered. Both generated sentences add travelers/pass/until/morning and are not covered. Each is a schedule-family proposition, so the audit records `proposition_authority`, which `validate_generated_response` surfaces as `unauthorized_resolution_decision_fact` and `retry_reason = hard_invalid`.

The ask to the guard is `outcome_classification = epistemically_qualified` because the operation is `ask` and an interlocutor is set. That does not erase the world-truth row. It only classifies the turn. The fact is still on the decision.

## 6. Free-text compatibility analysis

The bounded rule is the one the architecture already had, narrowed so a covered fact cannot license extra content words in the same sentence.

Allowed, because the content words come from the authored sentence:

- "The city gate closes when the watch changes at the third bell."
- "The gate closes when the watch changes at the third bell."
- "The city gate closes at the third bell."
- "The gate closes at the third bell."
- "The ferry leaves at noon."
- "The shop closes at sunset."
- "The northern road floods during heavy rain."

Rejected, because they are consequential schedule claims the fact does not cover:

- both generated third-bell sentences
- "The city gate closes when the watch changes at the third bell, and travelers can still pass until morning."
- "The city gate closes when the watch changes at the third bell until morning."
- "The shop shuts at sunset." Synonym substitution is not licensed. "Shuts" is a schedule verb, and it is not a content word of the authored fact.

Not a synonym license: "The ferry departs at noon." is accepted only because "departs" / "noon" is outside the consequential families. The audit is not treating "departs" as an authorized paraphrase of "leaves".

Outside the consequential-family gate, so not rejected by this authority check:

- "Passengers can board until noon."
- "Customers may enter until sunset."
- "It reopens tomorrow morning."
- "No one can use the road."
- "It becomes safe as soon as the rain stops."

"It returns at dusk." is rejected on the ferry question "When does the ferry leave?" by the existing unresolved-time slot (`unauthorized_qualifier:time`, `unauthorized_time_attribution`), not because the ferry fact entails a return time.

## 7. Production change

`game/gm_resolution_decision.py` only.

1. Free-text coverage no longer treats "every fact word appears in the sentence" as authority for an unlimited tail. More than one added content word blocks coverage. "Until morning" and "travelers can still pass" cannot ride along on the authored sentence.

2. `authorized_observation_line` may quote one free-text world fact when the question shares at least two of its content words, on an established or epistemic ask. It quotes the authored sentence. It does not invent a semantic identity, and it does not append "it is not established when" to that quote. On the frontier-gate scene, "what hour the gate closes" quotes only the schedule fact.

Structured identities are unchanged. Claim-control detectors are unchanged.

## 8. Test expectation change

`test_grounded_third_bell_is_authoritative_and_kept` and the grounded turn of `test_raw_chat_stub_authority_and_contracts`.

Old expectation: with the schedule visible, the two-sentence narration is kept on the first generation. Provenance `initial`. No `hard_invalid` retry.

New expectation: that narration is rejected. A lexical paraphrase is accepted on the single retry, provenance `regeneration`. If the retry repeats the residuals, the accepted line is the authored sentence, acceptance `authorized_observation`.

Reason: the live decision audits propositions. The corpus anchor check was accepting access and duration claims that the fact does not state.

## 9. Positive grounded paraphrase result

Accepted against the decision row for the visible schedule fact:

- the authored sentence
- "The gate closes when the watch changes at the third bell."
- "The city gate closes at the third bell."
- "The gate closes at the third bell."

The raw-chat turn asks what hour the gate closes. The stub returns the two-sentence narration, then the first paraphrase. The response is that paraphrase. Provenance `regeneration`. Call count 2.

## 10. Negative residual-addition result

Rejected with `proposition_authority`:

- "Travelers can still pass, but only until the watch changes at the third bell."
- "After that, the gates close until morning."
- both sentences together
- the authored sentence with ", and travelers can still pass until morning"
- the authored sentence plus "until morning"

When both generations return the two-sentence narration, the player-facing line is "The city gate closes when the watch changes at the third bell." It does not mention travelers or morning.

## 11. C19 results

`tests/test_pr_br_continuation19_hard_authority.py`: 11 passed, including `test_raw_chat_stub_authority_and_contracts`.

`tests/test_pr_br_c19_free_text_authority.py`: 5 passed.

## 12. Claim-control results

Slice 1: 6 passed. Slice 2: 10 passed. 16 passed. No claim-control detector was edited.

## 13. Broad deterministic regression result

One pytest session, fail-fast guard installed, exit 0, about 30.8 seconds.

| Suite | Tests | Result |
| --- | ---: | --- |
| Live-model guard | 2 | PASS |
| Regex bound | 1 | PASS |
| Claim Control Slice 1 | 6 | PASS |
| Claim Control Slice 2 | 10 | PASS |
| GMResolutionDecision | 9 | PASS |
| Decision Ownership Slice 2 | 7 | PASS |
| Semantic Fidelity Slice 3 | 7 | PASS |
| Qualifier / movement / mixed intent | 9 | PASS |
| C18 | 20 | PASS |
| C19 | 11 | PASS |
| C19 free-text authority | 5 | PASS |
| C20 | 14 | PASS |
| C21 | 10 | PASS |
| C21b | 18 | PASS |
| C21c | 17 | PASS |
| C22 | 27 | PASS |
| C23 | 3 | PASS |
| C24 | 9 | PASS |
| C25 | 9 | PASS |
| C26 | 8 | PASS |
| C27 | 13 | PASS |
| **Total** | **215** | **215 PASS, 0 FAIL** |

Log: `artifacts/pr_br_authority_reconciliation/deterministic_regression.txt`.

`tests/test_pr_br_live_validation_attachment_repair.py` has three failures (`test_novel_established_condition_unknown_cause_and_actor`, `test_turn3_uncertainty_remains_valid_with_decision`, `test_established_answer_does_not_collapse_to_generic_nonresolution`). They fail the same way with the previous coverage and observation functions. The codes are `unauthorized_certainty_upgrade` and `unauthorized_evidential_relation` on uncertainty sentences, and the chapel-bell fallback then collapses because its "it is not established when" suffix fails that check. They are outside this suite and were not introduced by the C19 edit. They were not repaired here.

## 14. Live-model guard result

`tests/test_live_model_guard.py`: 2 passed in 1.00s.

`test_openai_constructor_fails_closed` constructs `openai.OpenAI` under `tests/` and raises `LiveModelCallForbidden` with site `openai.OpenAI`. `test_default_call_gpt_wrapper_fails_closed` calls `game.gm.call_gpt` and raises `LiveModelCallForbidden` with site `game.gm.call_gpt`. No transport.

Log: `artifacts/pr_br_authority_reconciliation/live_model_guard.txt`.

## 15. Files changed

- `game/gm_resolution_decision.py`
- `tests/test_pr_br_continuation19_hard_authority.py`
- `tests/test_pr_br_c19_free_text_authority.py`
- `artifacts/pr_br_authority_reconciliation/reconciliation_report.md`
- `artifacts/pr_br_authority_reconciliation/deterministic_regression.txt`
- `artifacts/pr_br_authority_reconciliation/live_model_guard.txt`
- `handoff/CURRENT_REVIEW.md`
- `handoff/REVIEW_MANIFEST.json`
- `handoff/CURRENT_REVIEW.zip`

No claim-control detector file was edited. A temporary probe under `tests/` was deleted before the final run.

## 16. Known limitations

- Faithful paraphrase of a free-text fact is lexical. "Closes" does not authorize "shuts". "Leaves" does not authorize "departs" as a synonym. Adding a synonym table would be general semantic inference, and this cycle does not add one.
- Sentences outside the consequential families are not rejected merely for being unstated. Boarding, reopening, road closure, and "safe when the rain stops" remain outside that gate.
- One added content word can still accompany a restatement.
- The no-decision corpus path still uses the coarse schedule-anchor check. Live chat always attaches a decision, and the updated tests go through that decision.
- The three attachment-repair failures above are pre-existing on this tree.

## 17. Exact model/API call count

0.

## 18. Recommendation

The authored closing can be said. The pass-until and closed-until-morning additions cannot. The deterministic suite that was 209/210 is green, with the new positive and negative cases included. Claim control was not loosened.

Do not start live validation inside this cycle. The next cycle can run a small live validation of this boundary only.

A.
AUTHORITY REGRESSION IS RECONCILED;
BROAD DETERMINISTIC SUITE IS GREEN;
PROCEED TO SMALL LIVE VALIDATION
