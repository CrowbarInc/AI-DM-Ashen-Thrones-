# PR-BS Decision-Facing Answer Recipe Implementation

Date: 2026-10-04.

MODE: bounded implementation plus deterministic validation.

MODEL/API CALLS: ZERO. Live gameplay validation: not run. No commit. No push.

## A. Executive result

The realization model now receives a compact `decision_facing_answer_recipe` for the current turn. The recipe is built from the existing Resolution Contract and `GMResolutionDecision` inside `game/gm_resolution_decision.py`, then attached by `narration_authority_fields` and shipped from `game/prompt_context.py`.

It tells the model what the player needs answered, which authorized claims must or may be stated, whether qualified inference is permitted and at which modality, what must stay unresolved, which upgrades are forbidden, which declaration lane to use, and a short positive answer strategy.

The recipe does not create authority. Validators still read the canonical decision. A1 now has an obvious useful bounded-inference path, and that path passes the existing validator. The original A1 overreach still fails. B1 now has an obvious mundane conversational path that passes with an empty declaration list. Declaring that speech, or a durable loaf preference, as `authored_world_fact` still fails.

Provider-facing authority payload for the measured slice is smaller: A1 23,452 to 17,329 characters (−6,123). B1 23,494 to 17,114 characters (−6,380).

## B. Final ownership model

```
ResolutionContract
        +
authoritative state
        |
        v
GMResolutionDecision          canonical runtime owner
        |
        +---- RealizationClaims
        |
        v
build_decision_facing_answer_recipe
        |
        v
narration_authority_fields -> prompt payload
        |
        v
realization model
```

`build_decision_facing_answer_recipe` lives beside `compact_decision_for_prompt` and `narration_authority_fields`. It reads decision rows and contract fields. It does not write claims, mutations, or provenance.

Each recipe sets `projection_only: true` and `authority_owner: "gm_resolution_decision"`. `audit_realization_envelope_against_decision` has no recipe parameter. A recipe dict that says to establish a cause does not change the audit.

Missing `contract_id` returns no recipe. A decision with no qualified-inference act and no `MAY_INFER` claim sets `permitted_inference.allowed` to false and `inference_modality` to `none`.

Retry resends the original provider messages, so the same recipe is present on a retry. `retry_authority_context` does not add a second recipe.

## C. Recipe schema/projection

Schema: `decision_facing_answer_recipe_v1`.

| Field | Role |
| --- | --- |
| `requested_answer` | Operation, target or interlocutor, and the clipped player question. |
| `required_content` | `MUST_STATE` claims: id, role, text, provenance, status, relation. |
| `permitted_content` | `MAY_STATE` claims, same short shape. |
| `permitted_inference` | `allowed`, qualified observation acts, and existing `MAY_INFER` claims. |
| `inference_modality` | `possible` for `qualified_possibilities_only`; `hypothetical` or `inferred` for an existing may-infer claim; otherwise `none`. |
| `unresolved_content` | Decision qualifiers, preserve-uncertainty claim text, and cause/actor/time/history when the infer scope is `qualified_possibilities_only`. |
| `forbidden_upgrades` | Tokens projected from that scope, unresolved slots, and the standing rule that generated content is not authored world truth. |
| `declaration_guidance` | Four lanes: realize an authorized claim, propose a bounded inference, preserve an epistemic premise, or leave ordinary speech as narration. |
| `incidental_improvisation_guidance` | When ordinary dialogue or texture may stay narration or incidental improvisation. |
| `answer_strategy` | One positive instruction for this turn. |

Qualified inference is projected only from an epistemic act whose scope is already `qualified_possibilities_only`. The recipe copies that act's authority, status, subject, and relation. It does not add a new fact.

Provider decision projection (`prompt_decision_projection`) still carries `realization_claims` with ids and text, plus outcome, answer relations, mutations, and obligations. It omits `narration_constraints`, `proposed_facts`, and `epistemic_acts`, because the recipe is the operational reading of those three and the claim rows still hold the authorized wording.

## D. A1 result

Previous operational ambiguity: the decision already contained an `infer` act with authority `observation`, status `inferred`, and scope `qualified_possibilities_only`, plus a prose constraint that qualified possibilities may be inferred and that cause, actor, and history are not established. That permission was one act inside a large decision object. The model answered with structural failure, neglect, and harsh conditions, then retried into a restatement of the two visible facts.

New recipe (`artifacts/pr_bs_decision_facing_answer_recipe/a1_recipe.json`):

- Requested answer names the interpretation of the chapel bell and the player question.
- Required content is the two authored observations: the split yoke and the torn hanger.
- Permitted inference is allowed, scope `qualified_possibilities_only`, status `inferred`, modality `possible`.
- Answer strategy: answer the interpretation with one qualified possibility grounded in those observations, using could, may, or might.
- Unresolved: cause, actor, time, history.
- Forbidden: exact cause, actor, time, history, neglect, harsh conditions, safety status, unseen damage, gameplay lead, evidential establishment, certainty upgrade, and marking the inference as authored world fact.
- Declaration lane for the inference: `propose`, provenance `gm_inference`, relation `epistemic_status`.

Valid useful bounded response, accepted by `audit_realization_envelope_against_decision` with empty declarations and again as a `propose` declaration:

> The split wooden yoke and the torn leather hanger could be consistent with significant stress or force.

That sentence uses the authorized observations and the existing qualified-inference recognizer (`could` plus grounded definite nouns). It does not name a cause, actor, time, or lead.

Preserved rejection boundary. The validator was not changed.

- The ungrounded variant "The visible support failures could be consistent with significant stress or force." still fails as `unsupported_narrator_lead`.
- The original A1 envelope (structural failure, unsafe status, neglect, harsh conditions) still fails, including `unauthorized_evidential_relation` and `unsupported_narrator_lead`.
- These narration attempts still fail: sudden-pull cause; "might point to neglect"; the original neglect/harsh-conditions sentence; "Someone cracked the wooden yoke"; "The hanger was torn last night"; "You might ask the sexton who saw what happened."

## E. B1 result

Previous declaration ambiguity: the model declared "The baker refuses to reveal which loaf they usually keep for themselves" as `authored_world_fact`. The retry passed by using ordinary quoted speech and an empty `declared_claims` list. The schema offered `authored_world_fact` on the same surface as ordinary speech.

New recipe (`artifacts/pr_bs_decision_facing_answer_recipe/b1_recipe.json`):

- Requested answer: answer the baker in ordinary speech, with the player's question.
- Required content is only the existing stall fact and the baker's existence.
- Inference is not permitted. Modality is `none`.
- Answer strategy: have the baker reply with a direct answer, a refusal, a hesitation, or an admission that they do not know.
- Incidental guidance: refusal, hesitation, mannerism, and phrasing may stay plain narration or bounded incidental improvisation. That speech is not authored world truth.
- Forbidden: a durable preference without an authorized claim, and generated dialogue marked as authored world fact.

Valid mundane path, empty `declared_claims`, accepted:

> "I'm not comfortable saying which loaf I keep for myself," the baker replies cautiously, their gaze flickering briefly away.

A shrug-and-flour mannerism plus a refusal also passes as narration.

Preserved consequential boundary:

- Realizing the refusal text as `authored_world_fact` fails with `unauthorized_declared_claim`.
- Realizing "The baker always keeps the rye loaf for herself" as `authored_world_fact` fails with `unauthorized_declared_claim`.

The system prompt declaration rule now says ordinary NPC dialogue, refusal, hesitation, and mannerism stay narration or incidental improvisation and are not authored world facts. NPC speech is not globally exempt. A declared durable preference still fails.

## F. Provider-context changes

| Change | Why redundant | Canonical owner retained | Validator / debug effect |
| --- | --- | --- | --- |
| Replaced the generic "RESOLUTION CONTRACT" and "GM RESOLUTION DECISION" instruction strings with one answer-recipe pointer. | Those strings restated the compact contract constraint and the decision's standing prohibitions. The recipe now states the turn's positive path, and `resolution_contract.constraint` remains on the payload. | `resolution_contract` generation projection and `GMResolutionDecision`. | Validators do not read instruction strings. |
| Omitted `narration_constraints`, `proposed_facts`, and `epistemic_acts` from the provider decision projection. | Constraints are generic prose the recipe operationalizes. Proposed-fact text is already on `realization_claims`. Qualified inference and unresolved acts are projected by the recipe; preserve-uncertainty claims remain on `realization_claims`. | Full decision on `resolution.metadata.gm_resolution_decision`, including constraints, facts, and acts. Retry feedback still uses `compact_decision_for_prompt`, which keeps those fields. | Audits use the metadata decision. |
| Removed `metadata.gm_resolution_decision` and `metadata.resolution_contract` from the provider copy of `mechanical_resolution`. | The same contract and decision were shipped again inside mechanical resolution. Top-level compact contract, decision projection, and recipe remain. | The live resolution object is deep-copied before the strip. Metadata on the canonical resolution is unchanged, including `emission_debug`. | Validators and traces keep reading the canonical resolution. |

Response policy, turn packet, narrative plan, and the static instruction list were left in place. They are not fully represented by the recipe, and this slice does not rewrite them.

## G. Payload comparison

Method: `json.dumps(..., ensure_ascii=False)` character counts. No tokenizer and no model call. Same A1 and B1 saved decisions. Before snapshot: `artifacts/pr_bs_decision_facing_answer_recipe/payload_before.json`, reconstructed with the pre-change instruction strings, `compact_decision_for_prompt`, and the nested contract/decision copies. After snapshot: `payload_after.json`.

Response policy and turn packet were not rebuilt. Discovery's live A1 sizes for those components (20,609 and 10,668) are unchanged by this slice. The table is the authority slice this change touches, plus the system prompt.

| Measure | A1 before | A1 after | B1 before | B1 after |
| --- | ---: | ---: | ---: | ---: |
| System prompt | 12,897 | 12,975 | 12,897 | 12,975 |
| Instructions | 449 | 169 | 449 | 169 |
| Response policy | unchanged | unchanged | unchanged | unchanged |
| Turn packet | unchanged | unchanged | unchanged | unchanged |
| Decision/contract/claim projection | 3,092 | 1,695 | 3,290 | 1,960 |
| Answer recipe | 0 | 2,356 | 0 | 1,876 |
| Nested mechanical authority metadata | 6,969 | 54 | 6,813 | 54 |
| User authority slice | 10,555 | 4,354 | 10,597 | 4,139 |
| Total provider-facing slice | 23,452 | 17,329 | 23,494 | 17,114 |

System prompt grew by 78 characters because the declaration rule now names ordinary NPC speech. The authority slice still shrank by 6,123 characters on A1 and 6,380 on B1.

The 54-character mechanical remainder is the existing `emission_debug` key left on the provider copy. Debug scrub is recorded below and was not done here.

## H. Test results

Zero model or gameplay calls.

```
python -m pytest tests/test_pr_bs_decision_facing_answer_recipe.py --override-ini="addopts=" -q --tb=short
9 passed in 1.04s
```

Broad deterministic regression, including every `tests/test_pr_br_*.py` file (469 tests, including `tests/test_pr_br_continuation18_immutable_boundary.py`), the 9 recipe tests, and `tests/test_prompt_and_guard.py`:

```
python -m pytest tests/test_pr_br_*.py tests/test_pr_bs_decision_facing_answer_recipe.py tests/test_prompt_and_guard.py --override-ini="addopts=" -q --tb=line
534 passed in 38.30s
```

No validator was loosened. No PR-BR regression failed.

## I. Architecture assessment

A — PR-BR REMAINS CLOSED.

The recipe is a read-only projection. Canonical decision ownership, realization-claim authority, provenance, epistemic ceilings, bounded improvisation, and the immutable valid-response boundary are unchanged. No accepted consequential state is created by the projection. No provenance or ceiling contradiction appeared.

## J. Live-validation recommendation

Ready for a 2–4 turn micro live validation. It was not run.

Smallest scenarios:

1. First-pass bounded interpretation. In the chapel belfry, examine the split wooden yoke and torn leather hanger and ask what the damage suggests. Success is a first-pass answer that offers one qualified possibility tied to those two observations, with modality that stays possible or inferred. Failure is establishing cause, actor, time, history, neglect, harsh conditions, safety, unseen damage, or a gameplay lead, or collapsing to a bare restatement with no interpretation.
2. Mundane NPC conversation. Ask the baker which loaf they usually keep. Success is a first-pass ordinary reply, refusal, or hesitation in dialogue, with no authored-world-fact declaration and no durable loaf preference. Failure is declaring the refusal or a preference as world truth.
3. Optional uncertainty. Offer a hypothesis about the damage, such as that it was cut on purpose. Success is a reply that keeps the hypothesis conditional and does not promote it to an established cause.

## K. Residual findings

Not implemented:

- Retry remaining-authorized-answer guidance. Retry still appends rejection findings to the original messages. The recipe is present because the base payload is resent. A later slice can point the retry at the still-authorized shape instead of teaching avoidance.
- Further payload canonicalization. Response policy, turn packet, narrative plan, and the long instruction list still overlap. They were left alone because the recipe does not fully represent them.
- Debug-only context scrub. `emission_debug` remains inside the provider mechanical-resolution copy.
- Narration-only phrasings that the current validator does not treat as consequential claims, such as some harsh-condition wordings that are not the original rejected A1 envelope. Those sentences do not become authorized world truth. Tightening that recognizer would be a validator change and was out of scope.
- Discovery candidates that remain open: long-session context growth, and the static system-prompt momentum rules that can still compete with a strict claim ceiling.

## Decision taxonomy

A — READY FOR MICRO LIVE.

Deterministic implementation succeeded. Authority boundaries used by the existing validators remain intact. The recipe is specific enough for a small real-model check of bounded interpretation and mundane NPC conversation.
