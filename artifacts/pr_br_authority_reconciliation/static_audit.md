# Static audit — structured preservation, premise identity, empty claims, temporal eligibility

Date: 2026-10-04. Production search after the reconciliation repair. No model calls.

## 1. Structured candidate to prose-only `_bounded_keep`

Search: `_bounded_keep` and `candidate_entered_structured_envelope_path` under `game/`.

Both call sites are in `game/immutable_valid_response.py` `run_preserve_if_valid`.

- `regenerate is None`: `_bounded_keep` runs only when `candidate_entered_structured_envelope_path` is false.
- After a failed retry: `_bounded_keep` runs only when neither the initial nor the retry candidate entered the structured path.

Expected for the normal GM structured path: none. Observed: none.

`_bounded_keep` remains for pre-structured metadata and for a legacy fallback envelope. That is intentional.

## 2. Epistemic realization claims and premise identity

`RealizationClaim.premise_claim_ids` is populated in `_realization_claims_from_decision_parts`.

- Fact claims copy ids only when the semantic identity already has them. Ordinary world observations correctly have an empty list.
- `LEAVE_UNRESOLVED` acts use identity-supplied ids, or else every current `player_hypothesis` and `gm_inference` claim id.

Remaining classified path: an unresolved slot with no hypothesis, no inference, and no supplied ids has an empty premise list. Nonconditional wording is then allowed only when the residual is covered by an established claim's text. A declaration that still embeds an uncovered proposition fails with `premise_claim_unresolved` or `embedded_premise_unlinked`. Narration that accommodates a below-ceiling premise fails with `premise_ceiling_exceeded`.

No second path emits an epistemic parent while skipping that check.

## 3. Sealed consequential narration with an empty accepted claim set

`_undeclared_consequential_violations` rejects detector-positive consequential sentences that are not owned by an accepted declaration. Those candidates are not hard-valid, so they do not seal.

Incidental texture with empty `declared_claims` remains valid. Covered by `test_incidental_structured_narration_can_seal_without_a_consequential_claim`.

Expected detector-positive empty seals: none. Observed: none.

Residual, not a seal bypass of a detected claim: `_EVIDENTIAL_RELATION_RE` uses `suggests?`, which does not match "suggesting". A participle clause the existing boundary does not classify as consequential can still be incidental. Documented. Not repaired with a new consequential list.

## 4. `gm_inference` and temporal persistence

`sealed_temporal_claims` reads authorized rows from the immutable seal audit. `remember_temporal_claims` writes a row to `gm_inferences` when it is authorized and its provenance is `gm_inference`. `api_turn_support` calls that pair after the seal.

Accepted proposals are stamped `provenance=gm_inference` in `_accepted_proposal_claim`. No emit path was found that narrates an accepted inference while leaving it out of that bucket.

Expected: none ineligible. Observed: none.
