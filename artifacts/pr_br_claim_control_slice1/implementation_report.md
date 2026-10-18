# PR-BR Claim Control Slice 1 Implementation Report

## Executive conclusion

Implemented a bounded proposition-level claim-control layer in `game/gm_resolution_decision.py`. Sentence-level compatibility remains, but hard validation now records and evaluates `NarratedClaim` rows so one authorized observation cannot license a causal, evidential, temporal, actor, history, certainty, or other consequential residual in the same sentence.

## Files changed

- `game/gm_resolution_decision.py`
- `tests/test_pr_br_claim_control_slice1.py`
- `tests/test_pr_br_decision_ownership_slice2.py`
- `artifacts/pr_br_claim_control_slice1/implementation_report.md`

## Claim representation

Added `NarratedClaim`, carrying `semantic_identity`, `provenance`, `authority`, `epistemic_status`, `relation_kind`, `persistence`, `authorized`, `source_ref`, `source_turn`, and `source_scene`. It reuses the existing semantic-identity shape rather than creating a second ontology.

## Sentence to multi-claim audit behavior

`audit_narration_against_decision()` now returns `claim_results` in addition to legacy `proposed_facts`. `classify_narrated_fact()` remains as a compatibility summary, but it summarizes claim-level results and reports the sentence invalid if any claim is unauthorized.

## Coverage vs residual behavior

Authorized semantic-identity matches are recorded as coverage claims only. Generic residual detectors separately audit causal, evidential, certainty-upgrade, unresolved slot-fill, movement, stateful, and structured consequential claims.

## Epistemic-act representation

`GMResolutionDecision` now carries `epistemic_acts`. Established rows map to `establish`; unresolved qualifier/status permissions map to `leave_unresolved`; non-world-truth provenance can map to `infer`.

## GM-inference behavior

Added explicit `gm_inference` provenance and temporal persistence support. It remains non-world-truth and is available as typed context rather than raw transcript authority.

## Player-hypothesis behavior

Added explicit `player_hypothesis` provenance and temporal persistence support. It survives across turns as hypothesis/status, not established fact.

## Causal/evidential relationship behavior

Generic relation detection rejects unsupported causal/evidential/certainty-upgrade claims. Positive authorization is allowed when the decision explicitly contains a matching relation-kind identity.

## Temporal provenance structure

Added capped `narration_temporal_provenance` buckets:

- `gm_inferences`
- `player_hypotheses`
- `accepted_incidentals`
- `rejected_consequential`

Raw transcript text is not used as an authority source.

## Accepted-incidental persistence

Accepted incidental claims can be recorded into the temporal provenance bucket with `authority = bounded_incidental`; existing bounded-improvisation behavior remains intact.

## Rejected-consequential lifecycle

Rejected consequential claims can be recorded in capped memory with reason codes. The record is not permanent truth or permanent prohibition; later explicit `establish` decisions can authorize the same proposition.

## Raw-transcript authority handling

Prompt projection for temporal provenance labels typed buckets and states that raw transcript continuity is not authority.

## Preservation/sealing behavior

C18 sealing remains intact. Mixed sentences fail validation. If whole-sentence preservation can keep only valid sentences, it may do so; otherwise the existing safe nonresolution/authorized-observation fallback applies. No word surgery is introduced.

## A2 regression result

PASS. Split/dried observation plus "indicate it was left unfired" is rejected as unsupported evidential/residual claim content.

## A3 regression result

PASS by deterministic coverage of the recursive premise path: rejected consequential proposals remain non-authoritative and can be recorded as rejected consequential provenance.

## A4 regression result

PASS. Intact pots plus "no signs of firing" and "makes it clear it was never fired in a kiln" are rejected as residual/certainty/evidential claims.

## Bridge/sheep/warehouse/ledger results

PASS. Authorized observations remain covered; sabotage, poisoned-water explanation, thieves/removal, owner/intent/fraud/certainty residuals are rejected.

## Positive-authority paired results

PASS. Explicitly authorized evidential relation permits confident natural narration.

## Sequence-B preservation results

PASS on exercised regressions: NPC claim, bounded incidental, movement, and incidental entity behavior remain intact in focused suites.

## C18-C27 regression results

PASS for focused deterministic C18-C20 non-API suites and PR-BR decision/qualifier suites. Full raw-chat API tests were attempted but interrupted after stalling; no gameplay/model API calls were made.

## Full relevant deterministic result

Executed:

- `pytest tests/test_pr_br_claim_control_slice1.py -q`
- `pytest tests/test_pr_br_gm_resolution_decision.py -q`
- `pytest tests/test_pr_br_decision_ownership_slice2.py -q`
- `pytest tests/test_pr_br_decision_semantic_fidelity_slice3.py -q`
- `pytest tests/test_pr_br_qualifier_movement_mixed_intent.py -q`
- `pytest tests/test_pr_br_continuation18_immutable_boundary.py -q -k "not raw_chat"`
- `pytest tests/test_pr_br_continuation19_hard_authority.py -q -k "not raw_chat"`
- `pytest tests/test_pr_br_continuation20_incidental_entity.py -q -k "not raw_chat"`

The combined focused deterministic collection passed 38 tests. C18/C19 raw-chat stubs were started but stalled and were interrupted.

## Known limitations

This is a bounded structural detector, not a general English parser. It intentionally recognizes generic high-risk relation/status patterns rather than domain nouns. It does not parse arbitrary propositions.

## Exact gameplay/model API call count

0.

## Recommendation

Proceed to a small live validation after review of the bounded claim-control implementation and the stalled raw-chat test behavior.

## Required decision

PROPOSITION-LEVEL CLAIM CONTROL IS IMPLEMENTED;
PROCEED TO A SMALL LIVE VALIDATION
