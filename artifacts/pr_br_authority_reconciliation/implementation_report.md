# PR-BR structured claim reconciliation

Deterministic implementation only. Zero gameplay or model API calls. No live validation, no 4x10, no PR-BS, no commit, no push.

Decision: **A. KNOWN SYSTEMIC AUTHORITY BOUNDARIES ARE CLOSED; PROCEED TO FINAL SMALL LIVE PR-BR REVALIDATION.**

## 1. Executive conclusion

The three demonstrated escapes are closed without redesigning the Resolution Contract, `GMResolutionDecision`, the `RealizationClaim` concept, the one-call structured envelope, declaration validation, temporal provenance, C18, or bounded incidental authority.

- A structured candidate that fails validation is retried once as a structured envelope. If the retry also fails, the turn seals an authorized observation or the existing safe non-resolution. Prose-only `_bounded_keep` does not run on that path.
- An epistemic claim can name the propositions it depends on through `premise_claim_ids`. Parent uncertainty does not raise a premise above its own ceiling.
- "What does this damage suggest?" is an inspect plus interpretation request, and the decision permits qualified inference before generation.

Saved A1 hypotheses do not emit. Saved A2 nonconditional presupposition does not emit. A valid bounded inference can be declared, narrated, sealed, and stored in `gm_inferences` without becoming world truth.

## 2. Preservation repair

`candidate_entered_structured_envelope_path` is true when the candidate carries a structured-contract failure, or a non-legacy realization envelope whose `declared_claims` is a list (including empty) or whose envelope marks `structured_contract_present`.

`run_preserve_if_valid` calls `_bounded_keep` only when that predicate is false. A structured initial failure still requests one structured retry. After a failed retry, a structured turn skips sentence salvage and uses `authorized_observation_line` when that line is a real authored observation, otherwise `safe_nonresolution`.

Pre-structured callers with empty metadata, or a legacy fallback envelope, still use `_bounded_keep`. That function was not deleted.

A structured candidate with one valid authored sentence and one undeclared consequential sentence is rejected as a whole. The authored sentence is not salvaged.

## 3. C18 verification

C18 is unchanged. An accepted candidate is frozen, committed, and emitted exactly. The saved A1 fallback, the valid A1 inference, the incidental dust line, and the production-composition fallback all assert `accepted_record.text == player_facing_text` and `immutable is True`.

The safe fallback is the accepted candidate. It does not conflict with C18. Preservation is candidate construction, not the seal.

## 4. Premise-link representation

`RealizationClaim` and `DeclaredRealizationClaim` gained `premise_claim_ids: list[str]`. The one-call prompt schema and the retry schema ask for those ids. No general predicate logic was added.

Unresolved `LEAVE_UNRESOLVED` slots copy premise ids from the act identity, or, when the identity supplies none, from realization claims whose provenance is `player_hypothesis` or `gm_inference`. World facts are not auto-linked. A declaration must resolve every listed id against the decision catalog or a sibling declaration. An epistemic parent whose residual content is not covered by a linked premise is `embedded_premise_unlinked`. A missing id is `premise_claim_unresolved`.

## 5. Premise-ceiling enforcement

Each linked premise keeps its own status. `player_hypothesis`, `gm_inference`, speculation, and a provisional sibling declaration are below the established ceiling. Authored world truth and an authored established fact count as established.

A nonconditional epistemic parent that overlaps a below-ceiling premise is `premise_ceiling_exceeded`. A conditional marker (`if`, `assuming`, `suppose`, `whether`) placed before the overlapping premise terms is allowed. Parent uncertainty does not promote the premise.

Established premises may be realized nonconditionally because their content tokens are already authorized and are removed from the residual.

## 6. Player-hypothesis behavior

Player repetition and conditional formulation can create or retain `player_hypothesis`. They do not become `gm_inference` because the GM discusses them, and they do not become `world_truth` or authored fact through an epistemic parent.

The orchard case keeps animal damage as a player hypothesis while a qualified drought possibility is discussed. The next-turn confident repetition of a sealed inference stays `gm_inference` and a realize-as-established declaration of that inference is rejected.

## 7. GM-inference behavior

An accepted proposal is a `RealizationClaim` with provenance `gm_inference`, inference authority, and a bounded status. Sealed narration of that claim goes through `sealed_temporal_claims` into `remember_temporal_claims`, which stores authorized `gm_inference` rows in `gm_inferences`.

A subject-less proposal identity no longer applies modality strengthening to sentences that do not target it. That was rejecting the authored observation sentences beside a valid inference.

No consequential GM hypothesis from the saved A1 or A2 envelopes reaches the seal with an empty claim audit. Those envelopes are rejected and replaced by authorized observations.

## 8. Interpretation and INFER repair

The existing `_INTERPRETATION_RE` now allows a demonstrative (`this`, `that`, `it`) with an optional noun from the recognizer's existing category: damage, condition, observation. No loom vocabulary and no second interpretation architecture were added.

The live A1 input produces operation `inspect`, dimension `interpretation`, and `EPISTEMIC_ACT_INFER` with scope `qualified_possibilities_only` before generation. The previously supported phrases still match.

## 9. Saved A1 replay

Saved evidence only. Both raw envelopes were parsed as structured candidates.

- Attempt 1 rejected.
- Attempt 2 rejected.
- Acceptance reason: `authorized_observation`. Not `bounded_sentence_preservation`.
- Emitted text: "The wooden loom beam is cracked. The loom's iron brace is bent."
- Forceful impact, prolonged strain, wear, rough handling, and repair consequence are absent.
- `gm_inferences` is empty.
- The seal is exact.

A separate deterministic valid envelope, under the same contract and an INFER decision, declares the two authored facts plus "Prolonged strain is one possible reading of the damage." That narration seals as `initial_hard_valid`. The strain claim enters `gm_inferences` as `gm_inference` and is not world truth. A later confident player repetition does not promote it.

## 10. Saved A2 replay

The saved A2 player conditional is replayed with prolonged strain preloaded as `player_hypothesis`. Both saved envelopes are rejected. The emitted text does not contain "the precise cause of this prolonged strain" or "prolonged strain on the loom is not known."

Constructed case 1: premise remains `player_hypothesis`. "The precise cause of this prolonged strain is not known." is rejected. "If prolonged strain under heavy stress was involved, its cause is not known." is accepted.

Constructed case 2: an authored established premise ("An attack was ordered.") allows "Who ordered the attack is unknown."

## 11. Novel-domain results

No new domain recognizers. The same premise identity and status rules cover:

| Domain | Premise | Nonconditional uncertainty | Conditional uncertainty |
| --- | --- | --- | --- |
| Attack | hypothetical | rejected | accepted |
| Attack | authored established | accepted | — |
| Shipment theft | hypothetical | rejected | accepted |
| Bridge collapse | not established | rejected | accepted |
| Well poisoning | suspected | rejected | accepted |
| Orchard animal damage | player hypothesis | rejected | accepted, and a drought possibility does not promote the hypothesis |

## 12. Incidental-freedom result

"Dust hangs in the still air." with empty `declared_claims` seals as `initial_hard_valid`. Empty consequential claim audit remains valid for incidental texture.

A structured candidate that mixes one authored sentence with an undeclared consequential sentence does not seal the authored sentence through `_bounded_keep`.

## 13. Temporal ownership result

The valid A1 inference is committed with the production functions `sealed_temporal_claims` and `remember_temporal_claims` (the same pair `api_turn_support` calls after the seal). `gm_inferences` contains the prolonged-strain claim identity. The next decision, built from that session, still classifies it as `gm_inference`. Realizing it as an established authored fact is rejected.

## 14. Production-composition result

`test_production_composition_traverses_contract_decision_seal_and_temporal_commit` walks player input, Resolution Contract, `GMResolutionDecision`, a structured envelope stub, declaration and narration validation, one structured retry, authorized fallback, C18 seal, and temporal commit. Only the model transport is a stub returning the saved retry envelope. `gm_inferences` stays empty. Retry is invoked once.

## 15. Static audit

1. Structured candidate to `_bounded_keep`. Both call sites in `run_preserve_if_valid` are gated by `candidate_entered_structured_envelope_path`. The normal GM structured path does not invoke it. Pre-structured metadata and legacy fallback still may.

2. Epistemic claims without a premise identity. World observations do not need one. An unresolved slot with no `player_hypothesis` or `gm_inference` claim, and no identity-supplied ids, has an empty list. Nonconditional realization is then allowed only for content already covered by an established claim. A declaration that introduces an uncovered embedded proposition is rejected (`premise_claim_unresolved` or `embedded_premise_unlinked`).

3. Sealed consequential structured narration with an empty accepted claim set. Detector-positive undeclared consequential sentences become violations, so they do not seal. No production path was found that seals those sentences with empty accepted claims. Incidental texture remains the empty-audit exception.

4. `gm_inference` emitted but ineligible for temporal persistence. Accepted claims with provenance `gm_inference` and `authorized` true are the bucket written by `remember_temporal_claims`. No separate emit path bypasses that.

## 16. Broad regression totals

382 passed, 0 failed. About 40 seconds. Suites: new reconciliation 11, structured chat path 11, structured realization envelope 11, decision-owned claims 8, claim control slice 1 (6) and slice 2 (10), regex bound 1, decision ownership slice 2 (7), semantic fidelity slice 3 (7), GMResolutionDecision 9, resolution contract 72, qualifier/movement/mixed intent 9, C18 21, C19 hard authority 11, C19 free text 5, C20–C27 (14, 10, 18, 17, 27, 3, 9, 9, 8, 13), localized live defects 12, attachment repair 22, model interpretation 14, bounded improvisation 5, live-model fail-fast guard 2.

## 17. Token-cost TODO

Not optimized in this slice. See `prompt_payload_duplication_todo.md`. Discovery measurements stand: A1 initial about 24,750 input tokens, A1 retry about 26,010, A2 initial about 29,221, A2 retry about 30,917.

## 18. Files changed

This slice:

- `game/immutable_valid_response.py` — structured path cannot call `_bounded_keep`.
- `game/gm_resolution_decision.py` — `premise_claim_ids`, ceiling checks, epistemic-parent exemption from command/stateful/proposition hits, subject-less proposal identity no longer poisons unrelated sentences.
- `game/resolution_contract.py` — demonstrative plus existing semantic noun in `_INTERPRETATION_RE`.
- `game/gm.py` — prompt schema and one declaration instruction for `premise_claim_ids`.
- `tests/test_pr_br_authority_reconciliation.py` — replays, premise ceiling, novel domains, preservation, temporal ownership, composition path.

The working tree contains many older unrelated modifications. This slice did not make those.

## 19. Known remaining defects

- The existing evidential pattern `suggests?` does not match the participle "suggesting". The live A1 sentences that used it were rejected for undeclared consequential content and are no longer prose-salvaged. A future envelope whose only extra content is an undetected participle clause could still be treated as incidental texture. That is an isolated detector gap, not the preservation escape. Do not open another PR-BR cycle for it unless a live revalidation shows it authorizing a consequential claim.
- Epistemic-parent sentences are exempt from `command_authority`, stateful assertion, and proposition-authority so "Who ordered the attack is unknown" is judged by premise status rather than as a command. A single mixed sentence is not clause-split.
- Unresolved slots auto-link every current hypothesis and inference id. That is the minimum link, not a semantic chooser.
- Prompt duplication remains. See the token TODO.

## 20. Exact gameplay/model API call count

0.

## 21. Recommendation

Close this deterministic slice. The next live test should be a small PR-BR closeout revalidation of the same two-turn shape. If the authority and state boundary holds and any remaining failures are model quality, phrasing, isolated parsing, or GM judgment, do not create another PR-BR hardening cycle. Move those issues to the later gameplay, AI, or product campaigns.

A.
KNOWN SYSTEMIC AUTHORITY BOUNDARIES ARE CLOSED;
PROCEED TO FINAL SMALL LIVE PR-BR REVALIDATION
