# PR-BR Localized Live-Validation Repair

## 1. Executive conclusion

The four live-path defects were repaired without redesigning proposition-level claim control. Inspection-plus-interpretation now binds its explicit subject and authorizes qualified inference; negative epistemic status is valid speech; sealed accepted claims now reach temporal provenance and discourse focus; and preservation can no longer seal malformed or claim-incomplete dialogue.

Authority laundering remains blocked. Inference, player hypothesis, bounded incidental, rejected consequential proposal, and explicit establishment remain distinct.

## 2. A1 malformed-target root cause

The follow-up question did not overwrite the inspection target. `_EXPLICIT_TARGET_RE` correctly extracted `snapped counterweight chain and the roof-hatch mechanism`, but the generic malformed-span guard rejected that coordinated phrase because it exceeded six tokens. The referential phrase `the damage` then had no valid structural subject to bind to, so construction fell to clarification with `malformed_target_span`.

## 3. Inference-request repair

Resolution construction now recognizes a bounded interpretation dimension for forms such as `what does this suggest`, `what might this mean`, `what can I infer`, and `does this point to anything`. A structurally extracted inspection subject may exceed the old generic target bound only when the same input contains this inference follow-up. This preserves the existing unknown-noun abstention behavior elsewhere.

The resulting contract keeps `inspect` as the operation, the explicit object phrase as subject, `interpretation` as the requested dimension, and `answer` as the expected response. `GMResolutionDecision` adds an `INFER` epistemic act whose scope is qualified possibilities only. It does not add an unsupported `ESTABLISH`.

## 4. A3 reason-code root cause

The A3 uncertainty sentences activated three rules in the wrong direction:

- `unauthorized_certainty_upgrade`: the certainty expression matched `establish` inside negative phrases such as `not established`; detector activation was wrong because polarity was ignored.
- `unauthorized_evidential_relation`: the evidential expression matched negative limits using `establish`, `show`, or `suggest`; the detector found a relation-shaped phrase but classified an epistemic limit as a positive evidential claim.
- `unsupported_narrator_lead`: modal and uncertainty wording was interpreted as generated lead language because unresolved epistemic status had no structural claim class. This was wrong detector activation for status answers, while remaining correct for a generated suggestion to inspect an unrelated object.

Both the initial and retry paths used the same audit logic, which explains the duplicate rejection.

## 5. Uncertainty/epistemic-limit repair

The decision/audit boundary now represents unresolved cause, actor, event time, and inference-only explanation as epistemic-status claims. Negative forms such as `we do not know`, `not established`, `only a possibility`, `nothing here identifies`, `cannot tell from this`, and `remains unclear` are direction-aware.

`The damage does not identify who caused it` is accepted as a limit on the authorized observation. `The broken chain proves nobody touched it` remains an unauthorized evidential claim. Confidence questions bind the active claim when available, require an answer, and support a direct status answer without forcing a visible-fact preamble.

## 6. Unsupported-lead behavior

Object existence no longer grounds generated investigative utility. Hedging does not change authority: `Maybe the brass lamp contains a hidden message` and `You could inspect the brass lamp for evidence` are rejected when only the lamp's existence is known.

An authored relevant journal lead remains valid, and an NPC statement can remain an NPC claim/lead rather than world truth.

## 7. Temporal-provenance live-path root cause

The temporal ledger helpers and prompt projection existed, but production final emission never invoked the commit helper. Only deterministic tests called it. Consequently no sealed claim reached `gm_inferences`, `player_hypotheses`, `accepted_incidentals`, `rejected_consequential`, or `discourse_focus.active_claim`; raw transcript continuity was effectively the only live carrier.

## 8. Temporal-provenance repair

Production finalization now derives accepted claims from the exact sealed response, records rejected discarded proposals separately, commits typed temporal buckets, and records commit evidence in `metadata.emission_debug.temporal_provenance_commit`.

Accepted GM inference enters `gm_inferences`; materially tracked player supposition enters `player_hypotheses`; bounded texture enters `accepted_incidentals`; and blocked consequential proposals enter `rejected_consequential`. Rejected proposals are never written as accepted history.

The intended final pipeline is:

1. initial generation;
2. claim audit and hard validation;
3. retry if needed, followed by claim audit and hard validation;
4. if preservation is considered: construct candidate, check structural validity, re-audit the exact candidate, and hard-validate it;
5. choose one valid candidate and seal it;
6. commit temporal provenance from the sealed response;
7. commit state/discourse focus;
8. emit the exact sealed text.

No semantic mutation occurs after validation, preserving C18.

## 9. active_claim behavior

The finalizer sets `active_claim` only for a meaningful GM inference, player hypothesis, NPC claim, or unresolved proposition that supports continued discussion. Ordinary descriptive sentences do not automatically become focus. The production-path probe committed `Heavy strain is one possibility` as source `gm_inference`, status `inferred`.

## 10. repetition/promotion behavior

Repeated inference or player supposition retains its typed non-truth authority. Repetition never changes it to `world_truth`. A later resolver-authorized `ESTABLISH` may establish the matching proposition, while nearby or merely similar propositions remain unauthorized.

## 11. B3 preservation root cause

Preservation deleted regex-delimited sentences independently. A quoted turn could therefore lose an interior sentence while retaining a detached attribution or unmatched quote. The surviving text could be sealed using claim accounting derived before the material text change.

## 12. structural-preservation repair

Preservation now groups quoted speech and its attribution as structural narration units. Candidates are rejected if they contain unbalanced straight/curly quotation marks, an orphan terminal dialogue attribution, or a deletion-created fragment. The attribution check is deliberately narrow so ordinary hearsay such as `Someone said only guild members may enter` remains valid.

If no structurally valid preserved candidate exists, the path uses a valid retry or the existing small authority-safe fallback instead of broken prose.

## 13. post-preservation re-audit

Every materially changed preservation candidate is re-audited as exact text. Its accepted response metadata comes from that post-preservation audit. Tests assert that each accepted claim's text appears in the sealed candidate and that the exact candidate passes hard validation.

## 14. exact A1/A3/B3 deterministic results

- A1 exact/near-exact coordinated chain/mechanism request: PASS; validated `inspect`, subject preserved, `interpretation`, expected `answer`, not ambiguous.
- A1 `INFER` act: PASS; qualified possibilities allowed and unsupported saboteur explanation rejected.
- A3 direct `do we know` forms: PASS; active claim bound and direct answer requested.
- A3 unknown cause/actor/time: PASS; no certainty-upgrade or evidential-relation rejection.
- A3 epistemic limit: PASS; negative limit accepted while positive proof claim rejected.
- A3 unsupported hedged lead: PASS; rejected as `unsupported_narrator_lead`.
- B3 mixed quoted NPC answer: PASS; rejected history content removed only through a coherent structural unit.
- B3 split-quotation candidate: PASS; malformed candidate rejected.
- B3 exact candidate re-audit: PASS; accepted claim accounting matches emitted candidate.

## 15. novel generalization results

Fresh wheel, medicine, net, and banner inspection subjects all bind without production vocabulary additions. Fresh uncertainty questions all produce answer/confidence contracts. Fresh epistemic-limit statements validate. Brass-lamp generated leads remain rejected. Dialogue containing safe mundane material around a rejected history assertion either preserves coherently or falls back; it is never sealed malformed.

## 16. positive-control results

- Qualified heavy-strain inference: PASS.
- Authored maintenance-journal lead: PASS.
- NPC lead remains typed as an NPC claim rather than automatic truth: PASS in the broad NPC suites.
- Hemp-cord bounded incidental dialogue: PASS and persists with bounded authority.
- C19 free-text authority boundary: PASS.

## 17. older uncertainty-test results

The three known uncertainty-sensitive attachment-repair tests now pass through the generalized repair:

- `test_novel_established_condition_unknown_cause_and_actor`: PASS.
- `test_turn3_uncertainty_remains_valid_with_decision`: PASS.
- `test_established_answer_does_not_collapse_to_generic_nonresolution`: PASS.

None required a stale expectation change. They are included in the 51-test targeted baseline.

## 18. broad regression totals

Targeted session: 51/51 passed. This contains 12 localized repair tests, Claim Control Slice 1, Claim Control Slice 2, the regex bound, and all 22 attachment-repair tests.

Broad session: 333/333 passed. It covers C18-C27, `GMResolutionDecision`, decision ownership, semantic fidelity, qualifier/movement/mixed intent, C19 reconciliation, resolution/interpretation, NPC promotion and repeat suppression, and the live-model fail-fast guard.

The C18 fixture with three straight quote marks had a stale expectation under the new mandatory structural-emission invariant; it now correctly expects hard invalidity. The associated aggregate preservation/block counts were updated. No authority expectation was weakened.

Initial diagnostic failures from overbroad structural checks were repaired by narrowing unknown-subject admission to inference follow-ups and orphan-attribution detection to terminal attributions. Final reruns are fully green.

`git diff --check` passed; only pre-existing line-ending warnings outside this slice were reported.

## 19. files changed

Production:

- `game/interpretation_proposal.py`
- `game/resolution_contract.py`
- `game/gm_resolution_decision.py`
- `game/immutable_valid_response.py`
- `game/discourse_state.py`
- `game/api_turn_support.py`
- `game/prompt_context.py`

Tests and evidence:

- `tests/test_pr_br_localized_live_defects.py`
- `tests/test_pr_br_continuation18_immutable_boundary.py`
- `artifacts/pr_br_localized_live_repair/implementation_report.md`
- `artifacts/pr_br_localized_live_repair/handoff_config.json`
- `handoff/CURRENT_REVIEW.zip` and generated review surfaces.

## 20. known limitations

The repair is intentionally structural and bounded, not general NLI or a grammar checker. Inference phrasing and epistemic-limit phrasing outside the deterministic structural families may still require future vocabulary-neutral patterns. Structural preservation validates quote/attribution integrity and claim coverage, not literary quality. `active_claim` remains a single focused proposition, not a general knowledge base. No live-model behavior was measured in this repair cycle.

## 21. exact gameplay/model API call count

0 gameplay turns. 0 generation calls. 0 retry generation calls. 0 interpretation calls. 0 preflight calls. 0 other model calls. 0 total gameplay/model API calls.

All tests were deterministic. Any test fixture named `call_gpt` was monkeypatched and did not access an endpoint.

## 22. recommendation

The localized deterministic evidence satisfies the requested repair boundary. The next authorized step should be one final small live validation, not the 4x10 gate or PR-BS.

A.
LOCALIZED LIVE DEFECTS ARE REPAIRED;
PROCEED TO ONE FINAL SMALL LIVE VALIDATION
