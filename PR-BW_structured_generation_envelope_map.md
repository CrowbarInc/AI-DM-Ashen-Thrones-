# PR-BW Structured Generation Envelope Map

MODE: STRUCTURED REALIZATION ENVELOPE COMPETENCE DISCOVERY.

MODEL/API CALLS: ZERO.

## Flow

```text
GMResolutionDecision
  Canonical authority. Owns realization_claims, permitted_state_mutations,
  epistemic_acts, persistence policy, and narration_constraints.
  P1 allows two visible bell facts plus a qualified observation-level inference.
  P2 allows baker presence/existence only; ordinary reply is claim-only narration.
  P3 allows the same visible bell facts and preserves the player hypothesis as
  hypothesis, not world truth.

Decision-Facing Answer Recipe / Turn Operation
  Projection only; authority_owner is gm_resolution_decision.
  P1: bounded_interpretation / optional_bounded_inference.
  P2: incidental_dialogue / reply_not_required.
  P3: player_hypothesis_discussion / hypothesis_discussion_not_required.

Provider Instructions
  System prompt gives a universal one-call realization envelope. It tells the
  model to return declared_claims, narration, player_facing_text, tags, optional
  improvisation, scene/world updates, suggested_action, and debug_notes.

Provider-Visible Schema
  Prompt-encoded JSON example, not a saved API response_format/json_schema object.
  No strict provider-side schema object appears in preserved provider requests.
  The declaration schema is always visible before narration.

Declaration Generation
  Model may emit zero or more declared_claims. Declarations expose intent but do
  not authorize themselves. Validation accepts realization of existing claims or
  bounded proposals when the decision allows inference.

Narration Generation
  Model writes player-facing narration in the same call. This is a second content
  surface where semantic content can be introduced, even after declarations are
  chosen.

Declaration Validation
  game.gm_resolution_decision.validate_declared_claims_against_decision validates
  declared claims against GMResolutionDecision. P2 attempt 1 failed here:
  unauthorized_declared_claim.

Narration Validation
  game.gm_resolution_decision.audit_realization_envelope_against_decision extends
  the decision with accepted declarations, audits narration, then adds undeclared
  consequential and premise-ceiling checks. P1 attempt 1 failed here:
  unsupported_narrator_lead.

Acceptance / Retry
  If hard validation fails, production retry sends the same envelope plus compact
  authoritative retry context. PR-BV invoked retries for P1 and P2.

Commit
  Accepted claims may be recorded according to persistence policy. Rejected
  consequential content is recorded as rejected, not world truth.

Emission
  C18 held in PR-BV: accepted == sealed == emitted for P1/P2/P3.
```

## Authority Boundaries

GMResolutionDecision is the authority boundary. The recipe and turn_operation are model-facing projection only. Declarations expose candidate semantics; accepted declarations can be used for validation and limited persistence, but they do not grant authority. Narration is final player-facing prose and is audited against the effective decision.

## Model Decision Points

1. Whether to emit declarations at all.
2. If declarations are emitted, which mode/provenance/status/relation to choose.
3. How to verbalize accepted or permitted semantics in narration.
4. Whether to add incidental dialogue, mannerism, sensory detail, or consequential/epistemic content while narrating.

## Semantic Introduction Points

Semantic content can enter through GMResolutionDecision, the turn recipe projection, model declarations, narration, and improvisation_proposals. Only GMResolutionDecision and validator-accepted claims are authoritative. P1 shows narration can add content after an acceptable declaration. P2 shows declaration generation can add unnecessary structured content before narration is evaluated.

## Rejection And Persistence Points

Declaration validation rejects unauthorized declarations before narration validation. Narration validation rejects unsupported consequential or epistemic content. Rejected content is tracked as rejected consequential material and should not persist as world truth. Accepted emitted prose is sealed and emitted after validation.

## Suspected Duplicate Semantic Decision Points

The model first chooses structured semantics in declared_claims, then composes narration from the whole context. P1 demonstrates a valid declared inference followed by a semantically expanded narration. P2 demonstrates narration was already playable, but an extra structured declaration created a rejection. These are distinct duplicated semantic decision surfaces.
