# Campaign

Campaign: PR-BR Proposition-Level Narration Authority
Identifier: `pr-br-proposition-authority-review`
Date: 2026-10-03
Generated: 2026-10-03T23:30:00Z
Purpose: Architectural review of sentence-level authority inheritance and temporal provenance. Discovery only. No production edits and no model calls.

# Executive Summary

The pre-narration decision is sound and should be kept. Authority is still applied to a whole sentence: the first licensed subject and value stamp that sentence as world truth, and a sentence the classifier does not recognize is kept unlabeled. That is the A2 to A3 to A4 chain. A2's 'indicate it was left unfired' inherited the split-jar fact. The process-disruption sentence was never classified and was emitted anyway. A3 opened only an actor slot and treated the player's hypothesis as the event, because prior GM prose has no provenance tag. A4 labeled 'no signs of firing' as the intact-pots fact, left the kiln sentence unlabeled, and preservation deleted the uncertainty sentence. The salvage is claim-level control on the existing semantic identity, not a new narration stack and not a larger single identity. Decision A.

Objective status: `architecture_salvageable_by_proposition_level_claim_control`.

# Changes Made

## Production changes

- No changes in this category.

## Validation changes

- No changes in this category.

## Tooling changes

- No changes in this category.

## Documentation changes

- Wrote the architectural review at artifacts/pr_br_proposition_authority_review/ARCHITECTURAL_REVIEW.md. No production code was changed.

## Generated artifacts

- handoff/CURRENT_REVIEW.md, handoff/REVIEW_MANIFEST.json, and handoff/CURRENT_REVIEW.zip package this review with the A2-A4 and B1-B4 evidence and the current classifier, preservation, and provenance modules.

# What Was Tested

- **Focused tests:** Not run. This cycle is review only.
- **Broader relevant tests:** Not run. The 4x10 gate was not run.
- **Full suite:** Not run.
- **Runtime validation:** None. Zero gameplay turns and zero model calls in this cycle. Findings use the completed 20261003T223147Z multi-turn run.
- **Model/runtime boundary:** 0 gameplay turns. 0 generation calls. 0 interpretation calls. 0 preflight calls. 0 total model/API calls.
- **New regressions:** No production patch.
- **Pre-existing failures:** Split-quotation attributed testimony and guard_captain versus gate_guard were not repaired and were not reinterpreted.
- **Self-contained bundle review:** The bundle contains the architectural review, the prior validation report, A2-A4 and B1-B4 turn evidence, and the production modules that classify narrated facts, preserve sentences, store incidental and rejected proposals, and record NPC claims.

# Behavioral Evidence

No standardized behavioral evidence packet was supplied.

# Decisions Requiring Human Review

- A. CURRENT ARCHITECTURE IS SALVAGEABLE BY MOVING AUTHORITY FROM SENTENCE-LEVEL MATCHING TO PROPOSITION-LEVEL CLAIM CONTROL.

# Known Problems / Unresolved Findings

## Campaign-specific

- classify_narrated_fact copies the first matching semantic identity onto the entire sentence.
- A sentence that matches no identity and no consequential family returns None and preservation keeps it.
- unsupported_narrator_lead removed A4's uncertainty sentence while the kiln certainty remained.
- Prior GM prose enters the next prompt as unlabeled P|G text, so a player hypothesis becomes the event.
- Rejected consequential proposals and accepted incidental lines are not ledger records.
- B3's thanks was dropped because executable_obligations returns empty when 'head out to' is not a move span. Secondary.

## Pre-existing baseline

- Split quotation / attributed-testimony edge case remains unrepaired.
- guard_captain versus gate_guard addressability mismatch remains unrepaired.

# Missing Concepts / Future Capabilities

- Multiple claim units per narrated sentence, reusing semantic identity rather than replacing it.
- An epistemic act on the decision: establish, infer, or leave unresolved.
- A small typed record for GM inference, player hypothesis, accepted incidental, and rejected consequential identity.
- Preservation that refuses a mixed sentence instead of sealing it as the matched fact.

# What This Campaign Does NOT Prove

- Does not prove a post-hoc English parser can recover residual claims without NLI.
- Does not implement the claim record, the ledger, or a preservation change.
- Does not show the commit store would adopt the kiln sentence on a later turn.
- Does not rerun the multi-turn sequences or the 4x10 gate.
- Does not authorize PR-BS.

# Recommended Next Step

Implement only the minimum claim-control boundary in section 23 of the architectural review. Deterministic tests in section 24 come before any further live call.

# Review Bundle Contents

Bundle file count: `27`
Bundle ZIP size: `000000168815` bytes
Size warning threshold: `20971520` bytes
Size status: `WITHIN_THRESHOLD`

- `CURRENT_REVIEW.md`: generated orientation and decision surface.
- `REVIEW_MANIFEST.json`: generated provenance, inclusion, omission, and size record.
- `support/artifacts/pr_br_proposition_authority_review/ARCHITECTURAL_REVIEW.md`: Primary campaign standard/report used to orient the review. Canonical source: `artifacts/pr_br_proposition_authority_review/ARCHITECTURAL_REVIEW.md`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/validation_report.md`: The 4 PASS / 4 FAIL measurement this review explains. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/validation_report.md`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/turn_record.json`: A2 contract, decision, and emitted causal narration. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/generations.json`: A2 initial generation and empty retry. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/gm_output.json`: A2 audit: indicate-sentence stamped authored world truth; process sentence unlabeled; lead rejected. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A2/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/turn_record.json`: A3 decision with unresolved qualifier actor only. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/generations.json`: A3 narration treating the unfired leaving as the event. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/gm_output.json`: A3 audit and prompt history containing A2's unlabeled inference. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A3/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/turn_record.json`: A4 emitted kiln certainty and the player's known-versus-possible question. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/generations.json`: A4 initial certainty-plus-hedge and the rejected retry hedge. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/gm_output.json`: A4 audit: firing sentence inherits intact pots; kiln sentence unlabeled; hedge rejected; preservation seals the certainty. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_A/A4/gm_output.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/turn_record.json`: B1 ordinary talk. Incidental lines were not ledger entries. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/generations.json`: B1 emitted mundane improvisation. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B1/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/turn_record.json`: B2 brine-cask statement held as hearsay. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B2/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/turn_record.json`: B3 movement decision held. Supporting obligations empty. Secondary mixed-intent finding. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/generations.json`: B3 arrival narration omitting the thanks. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B3/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/turn_record.json`: B4 destination continuity. Footprint sentence not emitted. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/turn_record.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/generations.json`: B4 rejected footprint draft and accepted retry. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/generations.json`.
- `support/artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/gm_output.json`: B4 audit reason physical_investigative_evidence, and the rejection was not ledgered. Canonical source: `artifacts/pr_br_multiturn_provenance/20261003T223147Z/sequence_B/B4/gm_output.json`.
- `support/game/gm_resolution_decision.py`: Sentence classifier, semantic identity match, overreach, narrator-lead rejection, and decision structure. Canonical source: `game/gm_resolution_decision.py`.
- `support/game/proposition_authority.py`: Sentence-level proposition families and the default world-truth epistemic frame. Canonical source: `game/proposition_authority.py`.
- `support/game/immutable_valid_response.py`: Bounded sentence preservation and the immutable accepted-response seal. Canonical source: `game/immutable_valid_response.py`.
- `support/game/bounded_improvisation.py`: Incidental and rejected-proposal ledger. Decision-audit rejections do not enter it today. Canonical source: `game/bounded_improvisation.py`.
- `support/game/discourse_state.py`: NPC claim provenance. No equivalent record exists for a GM inference. Canonical source: `game/discourse_state.py`.
- `support/game/player_commitment.py`: Supporting-obligation construction. B3 thanks is discarded when the move span misses. Canonical source: `game/player_commitment.py`.

## Explicit omissions

No explicitly requested file was omitted.

The bundle intentionally excludes repository copies, dependency/cache directories, previous handoffs, unrelated artifacts, and sensitive configuration.
Canonical repository files remain authoritative; packaged copies are review conveniences with hashes and source paths.
