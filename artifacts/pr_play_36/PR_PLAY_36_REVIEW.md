# PR-PLAY-36 — Opening Semantic Rejection

Verdict: **A — PASS**

The PR-PLAY-35 opening was rejected for two narration sentences. Both restate facts the opening decision had already authorized. The nine declarations were valid. The repair accepts that kind of realization and still rejects added history, actors, items, travel, and other consequential claims.

Provider requests: 0. Provider tokens: 0. Live gameplay turns: 0.

## 1. Executive summary

Campaign initialization failed after a structurally valid provider response. `validate_generated_response` aggregated the failure as `unauthorized_resolution_decision_fact`. Offline replay of the captured envelope against the isolated baseline decision reproduced that code deterministically.

Declaration validation passed for all nine claims. Each `source_claim_id` matched an authorized `authored_world_fact`, and each declared text was identical to that fact. Narration validation then rejected two sentences:

1. `A notice board nearby lists new taxes, curfew rules, and a posted warning about a missing patrol.` Reason: `notice_roster_history`.
2. `Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke tightly as the crowd presses in.` Reason: `undeclared_consequential_claim`.

The first blends two authorized notice-board statements and adds the locative word "nearby". The authorized opening seed already contains "a posted warning about a missing patrol". The second is the authorized choke-point sentence with "while" replaced by "tightly as". The word "tightly" is manner, not a new outcome.

The validator was right to require declarations and right to reject genuine additions. It was wrong to treat these two realizations as new authoritative state. The repair is confined to that gap.

## 2. Opening reconstruction

Evidence run: `artifacts/atgb/pr_play_35/live/20261102T011549Z-bd0c88693cd0`

Opening attempt `e97b9ce72d9b494db77178582be66ceb`. Provider attempt `648cd2d0041a4ed8a7b8d5a891ce1150`. Captured payload: `opening_response_evidence/e97b9ce72d9b494db77178582be66ceb-1.json`.

HTTP `POST /api/start_campaign` returned 422 in 13.047 seconds. Player-facing text was the generic start failure, not the narration. `opening_failure_reason` was `safe_nonresolution`. `campaign_started` stayed false. `gameplay_committed` stayed false.

### Validation sequence

1. Provider completion. Model `gpt-4.1-mini-2025-04-14`. 26714 input tokens, 1667 output tokens, 28381 total, 12.105 seconds. No provider error.
2. Structured extraction succeeded. Diagnostic classification `accepted_structured_response`. Narration length 945. Declaration count 9. `activate_scene_id` `frontier_gate`.
3. `run_preserve_if_valid._check` called `validate_generated_response`.
4. `audit_realization_envelope_against_decision` accepted every declaration.
5. Narration audit rejected the notice sentence. The undeclared-consequential pass rejected the choke sentence.
6. The aggregate reason was `unauthorized_resolution_decision_fact`. `hard_validation_failed`.
7. The host sealed `safe_nonresolution`. `game.api._opening_response_rejection` returned that reason. The API responded 422 and did not start the campaign.

The rejection was deterministic. Two identical offline audits matched. It happened before campaign start. PR-PLAY-35 recorded bookkeeping writes to `session.json` and `combat.json` that did not set `campaign_started` and did not change clocks, scene, character, or turn counter.

### Narration

Rain spatters the soot-dark stone, while frayed banners flutter above Cinderwatch's eastern gate. A well-appointed townhouse overlooking the square flies noble colors, providing a quiet contrast to the mud and clamor around it. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke tightly as the crowd presses in. Threadbare watchers and ragged strangers linger along the muddy gate line, watching quietly. A notice board nearby lists new taxes, curfew rules, and a posted warning about a missing patrol. The rain barrel by the gate hosts a tavern runner loudly hawking hot stew and paid rumor. A gate serjeant maintains control over the crowd, keeping a vigilant eye on the roster board as the ash compact census delays tighten the eastern caravan choke point. Among the gathered figures, one in threadbare clothes stands uncannily still, their gaze flicking over packs and faces more than to the gate queue itself.

### Declarations

| ID | Source claim | Authorized source | Text equals authorized fact |
| --- | --- | --- | --- |
| dc_1 | rc_a83c5bcfc65e | scene.visible_facts.0 | yes |
| dc_2 | rc_d40a1efdddb3 | scene.visible_facts.1 | yes |
| dc_3 | rc_3b26b521977b | scene.visible_facts.2 | yes |
| dc_4 | rc_b59727e13c62 | scene.visible_facts.3 | yes |
| dc_5 | rc_be348e85a5e6 | scene.visible_facts.4 | yes |
| dc_6 | rc_31feab1dcf72 | scene.opening_seed_facts.0 | yes |
| dc_7 | rc_a0201a45af25 | scene.opening_seed_facts.1 | yes |
| dc_8 | rc_819bf0e987bb | scene.opening_seed_facts.4 | yes |
| dc_9 | rc_6c31b34a1529 | scene.opening_seed_facts.5 | yes |

All nine requested `provenance_requested: authored_world_fact`, `declaration_mode: realize`, `realization_role: MUST_STATE`.

### Authorization context

Rebuilt from the isolated baseline with model interpretation disabled. The decision method was `scene_opening`. Outcome classification was `state_mutation` because the opening resolution carries `opening_scene_turn`, `arrived_at_scene`, and `new_scene_context_available`. The decision contained 22 proposed facts and 22 realization claims. Every cited claim id was present. The notice and choke facts were in that set.

## 3. Rejected proposition report

Two propositions. No others.

### Proposition 1

Exact text: `A notice board nearby lists new taxes, curfew rules, and a posted warning about a missing patrol.`

Source: narration sentence. It is not itself a declaration. Declaration `dc_1` is the exact visible fact and was accepted.

Rule: `_CONSEQUENTIAL_PATTERNS` code `notice_roster_history`, applied by `_unlicensed_consequential_reasons`. A pattern already true of an authorized statement was licensed only when `_proposition_restates_statement` saw no added content word.

Authorized wording already present:

- Visible fact: `The notice board lists taxes, curfew rules, and a warning about a missing patrol.`
- Opening seed: `A notice board lists new taxes, curfews, and a posted warning about a missing patrol.`

The sentence uses "new taxes" and "posted warning" from the seed and "curfew rules" from the visible fact. The only token in neither statement is `nearby`. The strict restatement test failed against each statement individually, so the pattern was treated as a new notice history.

### Proposition 2

Exact text: `Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke tightly as the crowd presses in.`

Source: narration sentence. Declaration `dc_7` is the exact seed sentence and was accepted. Narration coverage recorded `source_ref: scene.opening_seed_facts.1`.

Authorized fact: `Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in.`

The only added content token is `tightly`. `_empty_identity_covers` already allows one added content word, so coverage treated the sentence as that fact. `_undeclared_consequential_violations` then required a zero-extra-word restatement and demoted the covered fact to `undeclared_consequential_claim`.

## 4. Authorization classification

Both propositions are **C — Authorized fact expressed differently**.

"nearby" and "tightly" are descriptive texture on those facts. They do not move the party, transfer an item, complete a quest, arrest an NPC, or assert a posting time, seal, roster, or actor.

They are not A. The posted warning and the choke are authored. They are not D. Both facts were on the decision. They are not E. The declarations that carried the facts were accepted; the failure was the narration wording around those declarations.

The other six narration sentences did not produce violations. Several are also paraphrases. They passed because they neither tripped a consequential pattern nor were close enough for coverage to mark them as world-authority claims. That asymmetry is why the choke sentence, which coverage did recognize, was the one demoted.

## 5. Root cause

Confirmed:

- The captured envelope is structurally valid.
- All nine declarations match authorized facts by claim id and exact text.
- The aggregate code is produced only when `audit_realization_envelope_against_decision` returns `hard_valid: false`.
- That audit failed on the two sentences above and on no other sentence.
- The notice failure is the pattern license requiring a single-statement restatement, so a blend of two authorized notice statements plus "nearby" stayed unlicensed.
- The choke failure is the undeclared gate using a stricter restatement test than the coverage rule that had just authorized the sentence.

Not the cause:

- Provider failure, malformed JSON, or a missing claim id.
- A declaration asking for world truth the decision did not list.
- Missing scene facts. The seed and visible facts were in the decision.
- Campaign mutation during the audit. The audit does not write state. Start remained false.

## 6. Repair manifest

File: `game/gm_resolution_decision.py`. Diff: `artifacts/pr_play_36/repair.diff`.

`_pattern_licensed_by_authorized_blend` licenses a consequential pattern when an authorized statement already matches that pattern, other pooled statements are near-duplicates of the same subject, and at most one residual token is in `{nearby, tightly}`. A second pattern, a stateful act, a lead, or movement that the pooled statements do not already contain stays unlicensed.

`_accepted_declaration_texture_realization` lets a declared fact be narrated with that same one texture token. Any other extra content word still counts as undeclared consequential wording.

The captured fixture was not rewritten. Declaration validation is unchanged. The texture set is the two words this opening demonstrated, not a general adjective allowlist. "quietly", "yesterday", and a second texture word remain rejected.

Checked against the risks named for this pass:

- Quest completion, item transfer ("gives you a sealed letter"), hidden cache, bootprints, route change, gate-opening orders, posted-yesterday history, grim notice paraphrase, and Thoran murdering the patrol stay rejected.
- Sentences such as "You take the serjeant's coin purse", "has been arrested", and "the quest is complete" still produce no claim. The repair does not authorize them. They were already outside the detector. That gap is recorded under remaining risks and was not widened.

## 7. Regression results

No retries. No skipped tests in the focused run. No provider calls. `data/session.json` SHA-256 was unchanged before and after.

```
python -m pytest tests/test_pr_play_36_opening_rejection.py tests/test_pr_br_gm_resolution_decision.py tests/test_pr_br_structured_realization_envelope.py tests/test_pr_br_authority_reconciliation.py tests/test_pr_play_11_claim_authority.py tests/test_opening_start_seam_regressions.py::test_failed_start_leaves_turn_counter_and_log_clean tests/test_opening_visible_fact_selection.py -q --tb=line
```

Result: 81 passed, exit 0.

| File | Tests |
| --- | --- |
| tests/test_pr_play_36_opening_rejection.py | 8 |
| tests/test_pr_br_gm_resolution_decision.py | 9 |
| tests/test_pr_br_structured_realization_envelope.py | 11 |
| tests/test_pr_br_authority_reconciliation.py | 11 |
| tests/test_pr_play_11_claim_authority.py | 22 |
| tests/test_opening_start_seam_regressions.py::test_failed_start_leaves_turn_counter_and_log_clean | 1 |
| tests/test_opening_visible_fact_selection.py | 19 |

The new tests use the captured response and the isolated baseline. They check the two original sentences, claim-id identity, deterministic acceptance, decision immutability, and the unauthorized cases above.

Three tests in `tests/test_pr_cp_authorized_finalization.py` failed both with this repair and with the repair stashed: `test_preference_gesture_is_not_an_undeclared_world_fact`, `test_authored_patrol_sentence_survives_and_extras_do_not`, and `test_pr_cq_patrol_invalid_first_generation_projects_without_regeneration`. They are pre-existing and were not changed here.

## 8. Recovery strategy assessment

No recovery subsystem was added.

**Strategy A — deterministic authorized fallback.** `game.opening_deterministic_fallback.deterministic_opening_fallback_text_and_meta` can already compose an opening from curated authorized facts. The start path does not use that text to complete initialization after a semantic rejection. `_opening_response_rejection` treats `safe_nonresolution` as a failed opening. Using the composer as the committed opening would avoid a second provider call and would add no new facts, but it needs its own pass to prove the composed text satisfies the opening contract and does not smuggle selector wording past authorization.

**Strategy B — safe partial acceptance.** Not safe on this architecture. The two rejected sentences are in the same narration as the other sentences. The audit does not prove the remaining sentences are independent of the rejected claims. Several other sentences are paraphrases that passed only because they missed the pattern and coverage gates. Keeping them while dropping two sentences would be a new acceptance mode.

**Strategy C — explicit failure.** This is what the engine did. The player saw the generic failure. The campaign did not start. That is the right behavior when the opening asserts unauthorized state. It was the wrong final outcome only because these particular sentences were authorized realizations.

Preferred next design: keep Strategy C for real authorization failures. In a separate pass, consider Strategy A so an authorized-fact opening can still start when the model only misses realization wording. Do not implement Strategy B.

## 9. Provider usage

- Provider requests: 0
- Provider tokens: 0
- Live gameplay turns: 0

The captured PR-PLAY-35 response was the fixture. It was not sent again.

## 10. Remaining risks

The consequential-pattern and stateful-assertion detectors still miss some sentences that read like state changes, including taking a coin purse, arresting the serjeant, and completing a quest. This repair does not classify those sentences and does not authorize them. Closing that gap is a separate detector change, not a reason to loosen realization further.

A live opening can still fail on a different sentence. This pass did not call the provider, so it does not show that a fresh opening will initialize.

The texture set is intentionally two words. A later opening that says "quietly" or "slowly" where this one said "tightly" will still be rejected until that word is justified by evidence.

Pre-existing `test_pr_cp_authorized_finalization.py` failures remain.

## Final verdict

**A — PASS**

The rejected propositions are known, the cause is the realization test rather than missing authority, the repair accepts the captured opening for that reason, and unauthorized additions used in the new tests stay rejected.
