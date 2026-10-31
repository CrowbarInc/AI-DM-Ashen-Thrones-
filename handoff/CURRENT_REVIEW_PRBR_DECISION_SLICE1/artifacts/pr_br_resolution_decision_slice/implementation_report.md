# PR-BR Decision-Owned Consequential Claims: Implementation Slice 1

## 1. Executive conclusion

Implemented the deterministic slice of the decision-owned consequential-claim boundary. `GMResolutionDecision` now carries `realization_claims` before narration, including authored facts, temporal player hypotheses, temporal GM inferences, bounded incidentals, and explicit unresolved-slot constraints. Narration validation now treats sentence-level matches as proposition coverage only; causal, actor, time, absence, and gameplay-lead residuals remain separate claims and can be rejected.

## 2. RealizationClaim design

Added `RealizationClaim` in `game/gm_resolution_decision.py` with `claim_id`, `semantic_identity`, `provenance`, `authority`, `epistemic_status`, `modality`, `realization_role`, `persistence`, `source_ref`, `text`, and `relation_kind`.

Roles implemented: `MUST_STATE`, `MAY_STATE`, `MAY_INFER`, `MUST_PRESERVE_UNCERTAINTY`, and `INCIDENTAL_TEXTURE`.

## 3. GMResolutionDecision integration

`GMResolutionDecision` now includes `realization_claims`. The builder derives these from accepted pre-narration facts and epistemic acts. `compact_decision_for_prompt` also exposes the claim set so the narration layer can see the semantic ceiling without becoming authority.

## 4. Inference ownership

Inference remains deterministic. Existing temporal GM inferences become `MAY_INFER` realization claims with non-world-truth authority. Explicit candidate inferences in tests can be authorized as possible causes. Narration may state them only with preserved modality.

## 5. Player-hypothesis integration

The decision builder now reads `narration_temporal_provenance.player_hypotheses` before narration. Player hypotheses enter as `player_hypothesis`, `MAY_INFER`, non-world-truth claims. Repetition or co-occurrence with authored facts does not promote them.

## 6. Monotonic-authority implementation

Authority promotion now requires an explicit authoritative fact in the decision. A prior hypothesis ceiling blocks repetition unless a later `world_truth` authored/resolver claim is also present. Tests cover hypothesis non-promotion and explicit promotion.

## 7. NarratedClaim responsibility after repair

`NarratedClaim` remains a realization/audit record. It is still sentence-shaped, so it may describe multiple claim rows for one sentence. It no longer creates semantic authority; authority derives from matched decision-owned claims or from explicitly unauthorized residuals.

## 8. Saved Turn-1 result

Saved Turn 1 from `artifacts/pr_br_final_live_validation/20261004T035044Z` is replayed deterministically. Authored pump observations are recognized, while the negative-evidence sentence (“no hint of recent disturbance around the pump”) is rejected unless owned. Uncertainty no longer makes consequential propositions disappear.

## 9. Saved Turn-3 result

Saved Turn 3 is replayed deterministically. Bowed handle and sheared pin observation coverage is recognized. The “sudden, violent pressure seems a likely cause” proposition is separately accounted as an unauthorized causal relation. Specific leads about recent pump users/nearby witnesses are rejected unless explicitly owned as gameplay leads.

## 10. Negative-evidence handling

Added structural negative-evidence detection for absence claims such as no disturbance, no footprints/tracks/blood/evidence, nothing moved/disturbed, or nobody reacting/entering. `around` is no longer an epistemic hedge token in `game/proposition_authority.py`.

## 11. Gameplay-lead handling

Added structural detection for specific leads, including checking/asking specific groups, witnesses/users, and records/ledgers that may identify answers. Generic advice remains outside this detector; state-grounded or invented specific leads require decision ownership.

## 12. Temporal persistence

Temporal persistence still writes through the accepted sealed-response path. This slice adds decision input from temporal buckets and tests that accepted GM inferences/player hypotheses retain non-world-truth authority. It does not replace the existing state architecture.

## 13. Turn-4 NPC persistence

Saved Turn 4 is replayed. Lavender soap and lengthwise folding remain NPC claim / claim-only style conversational content and do not become `world_truth`.

## 14. Preservation/C18 interaction

C18 remains intact. Existing preservation revalidates the exact post-deletion candidate before sealing. This slice strengthens the decision audit that C18 calls; it does not add post-seal semantic mutation.

## 15. Novel-domain results

Novel domains pass without adding domain nouns: lantern impact cause rejected; orchard farmhand actor/history rejected; fountain basin during-night timing rejected; desk drawer negative evidence rejected; wagon wheel stable-hands lead rejected; possible excessive-load cause allowed only as possible; rain roof hypothesis does not promote until explicitly established.

## 16. Modality/consequence results

Tests show modality and consequence are independent. Possible/hypothetical causes remain consequential. A possible cause may be realized as possible, but “caused it” is rejected as modality strengthening unless explicitly established.

## 17. Static authority-path audit

Remaining sensitive paths:

- `game/gm_resolution_decision.py` still has legacy free-text authored compatibility (`_empty_identity_covers`, `_classify_narrated_fact_legacy`) as a backstop. It is now constrained by residual checks, but it is still a sentence-shaped compatibility path.
- `game/proposition_authority.py` remains sentence-family classification; grounded operational families can still yield authoritative rows when corpus-grounded.
- Older final-emission/fallback uncertainty validators still contain hedge/uncertainty handling outside this slice. They are not semantic authority owners for this decision boundary, but they remain audit targets for later cleanup.

Uncertainty skip audit: `around` was removed from hedge/speculative detection. Consequential uncertain claims are now accounted when they carry cause, absence, or lead structure.

## 18. Broad regression totals

Focused decision-owned slice: `31 passed`

Command: `pytest tests/test_pr_br_decision_owned_realization_claims.py tests/test_pr_br_gm_resolution_decision.py tests/test_pr_br_decision_ownership_slice2.py tests/test_pr_br_decision_semantic_fidelity_slice3.py -q --tb=short`

Claim-control / C19 / qualifier / live-model guard shard: `33 passed`

Command: `pytest tests/test_pr_br_claim_control_slice1.py tests/test_pr_br_claim_control_slice2.py tests/test_pr_br_claim_control_regex_bound.py tests/test_pr_br_qualifier_movement_mixed_intent.py tests/test_pr_br_c19_free_text_authority.py tests/test_live_model_guard.py -q --tb=short`

Continuation broad shard: started, emitted 15 passing dots, then went silent for over 90 seconds and was interrupted to avoid leaving a stuck pytest process. No failure output was emitted before interruption. Classified as environment/runtime stall, not a regression signal.

## 19. Files changed

Production:

- `game/gm_resolution_decision.py`
- `game/proposition_authority.py`

Tests:

- `tests/test_pr_br_decision_owned_realization_claims.py`

Handoff:

- `handoff/CURRENT_REVIEW_PRBR_DECISION_SLICE1/artifacts/pr_br_resolution_decision_slice/implementation_report.md`
- refreshed `handoff/CURRENT_REVIEW.zip`

## 20. Known limitations

- This is not general English NLI.
- The specific residual detectors are structural and bounded, not a giant ontology.
- Legacy free-text compatibility remains as a backstop.
- Some older final-emission/fallback uncertainty logic remains outside this slice.
- The broad continuation shard stalled under this local runtime and should be rerun in smaller batches later.
- Turn-2 routing is documented as a local routing defect and was not repaired.

## 21. Exact gameplay/model API call count

`0`

No gameplay, generation, interpretation, preflight, live validation, or 4x10 gate was run.

## 22. Recommendation

B. CLAIM OWNERSHIP IS ESTABLISHED BUT LOCALLY INCOMPLETE;
ANOTHER DETERMINISTIC SLICE IS REQUIRED
