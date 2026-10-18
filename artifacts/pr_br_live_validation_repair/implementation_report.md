# PR-BR live-validation repair

Date: 2026-10-03

Exact model/API call count for this repair: **0**.

No gameplay turns, no generation calls, no interpretation calls, no preflight calls, no eight-probe rerun, no 4x10 gate, no human playtest.

## Root-cause confirmation

The live 4 PASS / 4 FAIL result matches two implementation defects plus the retry that followed them.

### Defect 1 — decision attachment gap

Turns 1, 4, 5, and 7 built the Resolution Contract inside `attach_interaction_obligation`, so `attach_gm_resolution_decision` ran.

Turns 2, 3, 6, and 8 already had an authoritative contract. `attach_interaction_obligation` returned as soon as `metadata.resolution_contract.contract_id` existed. That return skipped the decision.

Turn 2 is the consequence. Nessa’s denial of Violet Compact membership was available, and the narration also asserted that the Compact gathers at the docks or the market. With no `GMResolutionDecision`, there was no proposed-fact authority and no decision audit, so that unauthored organization/location claim was accepted.

### Defect 2 — sentence-local fidelity

Turns 1, 4, and 7 had decisions. Competent narration was rejected.

- Turn 1: authorized kiln state was cold and cracked. “The kiln is not currently firing” was treated as negating every positive fact about the kiln, including `condition = cracked`.
- Turn 4: pale crust and stiff wool were authorized. A sentence that mentioned the vat or the wool was rejected unless that same sentence restated pale, crust, and stiff.
- Turn 7: the bell was authorized as cracked. “No one here knows who cracked it” was treated as negating `cracked`.

### Defect 3 — retry dropped the decision

The hard-invalid retry user message was the short regeneration note (about 422 characters on the live probes). That note contained neither the Resolution Contract nor the `GMResolutionDecision`. All three retries failed again, and the useful answer was replaced by the generic line “No one here can answer that from what is settled here.”

## Exact attachment-gap fix

`attach_interaction_obligation` still refuses to rebuild a contract that already has a `contract_id`.

After marking that contract `retry_preserved`, it now compares `metadata.gm_resolution_decision.contract_id` with the existing contract:

- matching decision: keep it
- missing or mismatched decision: `attach_gm_resolution_decision` consumes the existing contract

`carry_authoritative_contract` copies a decision onto a replacement resolution when the decision’s `contract_id` matches the carried contract and the destination lacks that decision.

When a fast path abstains and the contract is discarded for a rebuild, both `establish_ordinary_gameplay_contract` and the procedural interpretation rebuild now also drop `gm_resolution_decision`, so the rebuilt contract cannot keep a decision from the discarded contract.

Narration payload construction adds both the contract projection and a compact decision when a decision exists.

## Contract-entry paths audited

| Path | Contract | Decision |
| --- | --- | --- |
| Fresh construct inside `attach_interaction_obligation` | built here | attached at the end of the same call |
| Existing-contract return (social, movement, perception, clarification, retry) | kept, not rebuilt | attached if absent or mismatched; matching decision kept |
| `establish_ordinary_gameplay_contract` deterministic attach | built before resolver selection | attached with that contract |
| Fast-path abstain, then model-interpretation rebuild | old contract popped | old decision popped, then the new contract gets its own decision |
| `carry_authoritative_contract` after a resolver replaces the resolution object | copied | matching decision copied |
| `_run_resolved_turn_pipeline` attach (`game/api.py`) | existing contract kept | decision attached on that call |
| Procedural attach when no deterministic action matched | built or kept | attached by the same function |
| Procedural interpretation rebuild | rebuilt after pop | rebuilt after the decision pop |
| Scene opening | no ordinary contract | no decision; opening is not a generated fictional resolution |

Resolver selection is unchanged. `select_ordinary_resolver` still chooses from the contract’s operation and subject. The decision is metadata on that contract.

## Decision-presence matrix

| Live turn / path | Before | After |
| --- | --- | --- |
| 1 kiln, fresh information contract | decision present | decision present; `contract_id` matches |
| 2 Violet Compact, prebuilt social contract | decision absent | decision attached to the existing contract |
| 3 Pell uncertainty, prebuilt social contract | decision absent | decision attached; uncertainty narration still valid |
| 4 dye vat, fresh/established observation | decision present | decision present |
| 5 incidental smell/clothing | decision present | decision present; incidental narration still valid |
| 6 movement to the reed drying loft | decision absent | decision attached; destination narration still valid |
| 7 chapel bell | decision present | decision present |
| 8 background NPC answer | decision absent | decision attached; answer stays unmarked |
| Retry of an existing contract | contract kept, decision skipped | same decision kept and sent in the retry note |
| Resolver replacement | contract carried, decision dropped | matching decision carried |

## Negation semantics

Before: a sentence containing “not”, “no”, “never”, or a similar cue failed every positive identity whose subject the sentence mentioned.

After: negation is scored only on the clause that contains the authorized value, and only when the cue sits immediately on that value (adverbs such as “currently” or “still” may intervene). “No one knows who cracked it” negates knowledge of the actor. It does not negate `cracked`. “The kiln is not firing” negates `firing`. It does not negate `cracked`. “The cistern is not split” still fails a positive `split` identity.

## Entity reference

A sentence that only names an authorized subject is an entity reference. It is not scored as a restatement of every authorized attribute. “You lean over the vat” does not have to repeat pale, crust, or stiff. “What happened to the wool is unclear” does not contradict `wool = stiff`.

A sentence that substitutes a stronger or opposite value still fails. “The eastern bridge collapsed” against authorized `damaged` remains `semantic_strengthening`. “Unlocked” against `locked` remains a polarity failure. Token overlap with the subject is not authorization.

## Multi-sentence fidelity

Authorized value terms may be realized across neighboring sentences. The vat answer can put “pale crust” in one sentence and “stiff” in the next. Schedule grounding classifies each sentence with the full reply as context, so a later clause can complete an authored schedule anchor that a sibling sentence already stated.

Sentence-level audit remains. One unauthorized consequential sentence inside an otherwise valid reply is still a violation. Bounded repair can drop that sentence after validation.

## Unknown cause, actor, and time

Questions that ask who, when, or what caused an established condition record unresolved qualifiers (`actor`, `time`, `cause`) unless the identity already covers that slot.

Valid: the condition is stated, and the reply says the actor, time, or cause is unknown. “The bell is cracked, but no one here knows who damaged it” is valid.

Invalid: a concrete fill of an unresolved slot. A named agent immediately on a damage verb, a concrete time expression, a because/caused-by/halted/fouled cause, or an event-site claim is `unauthorized_qualifier`. An unauthored “known to gather / meet / based at” place claim is `unauthorized_social_world_fact`. An unauthored splash/spill/stain residue claim is `unauthorized_physical_residue`.

These checks are structural patterns. They do not add kiln, vat, bell, or Violet Compact vocabulary.

## Derived-answer handling

No inference engine was added.

For a polar question whose subject matches an authorized identity:

- if the asked predicate is an authorized value, the decision records `direct_authorized_fact` with positive polarity
- if the asked predicate is not an authorized value, the decision records `derived_denial` with negative polarity

Denying that asked predicate is valid. Asserting it is `unsupported_consequential_inference`.

“The kiln is not currently firing” is the negative answer to “Is the kiln still firing?”, because `firing` is not the authorized value `cracked` / `cold`. “The kiln is firing pots today” stays invalid. This does not authorize arbitrary entailments from cold or cracked.

## Retry context

Before: the last user message on a hard-invalid retry was the short regeneration note. Original messages were reused, but the repair instruction itself omitted the contract and the decision.

After: `regeneration_feedback` appends `AUTHORITATIVE RETRY CONTEXT` JSON containing:

- `resolution_contract`
- `gm_resolution_decision`
- `validation_failure` (reason codes and the violating sentence records)

The note also tells the model to keep sentences that already match the decision and to repair the rejected sentence. A direct feedback call with no resolution still omits that JSON, so an ungrounded-rule note does not echo a rejected sentence by itself.

## Bounded repair

One semantic mismatch used to reject the whole generation, retry once, and then replace the reply with the generic no-answer line.

After a failed check, the pipeline still retries once when a regenerator is provided. If the retry is hard-valid, that text is sealed as `regeneration`.

If the retry is also invalid, the pipeline drops only the sentences named in the decision-audit violations, revalidates the remainder, and seals it when that remainder is hard-valid (`bounded_sentence_preservation`). Attempt 1 is tried before attempt 2.

If nothing safe remains, and the failure includes `unauthorized_resolution_decision_fact` with a usable established observation whose subject overlaps the question, the sealed line is that observation (`authorized_observation`). The generic no-answer line is used only when that observation is absent.

Every accepted string still passes validation and `seal_accepted_response` before emission. C18’s immutable accepted-response record is intact. Safe provenance is still used for the terminal fallback, and the rejection audit is retained on that record.

## Fallback

“No one here can answer that from what is settled here.” remains the safe line when no usable established observation answers the question.

An `established_or_retrieved` outcome with a usable authorized observation no longer collapses to that line solely because sentence-local fidelity repair failed. The deterministic invariant is the kiln/bell preservation tests: the emitted text states the established condition and is not the generic line.

## Four failure regressions

All four passed with zero model calls.

| Turn | Result |
| --- | --- |
| 1 kiln | “cold and cracked” plus “not currently firing” is valid. “The kiln is firing pots today” is `unsupported_consequential_inference`. |
| 2 Violet Compact | Prebuilt social contract gets a decision. Membership denial is valid. “Known to gather at the docks or the market” is `unauthorized_social_world_fact`. |
| 4 dye vat | Pale crust, stiff wool, and unknown cause may be split across sentences. “Halted and fouled” and “no obvious splashes” stay invalid. |
| 7 chapel bell | Cracked plus unknown actor/time is valid. “Brother Hal cracked the bell yesterday” is unauthorized for actor and time. “No one” does not negate the crack. |

## Four pass preservations

All four passed, and each now runs with a decision whose `contract_id` matches the contract.

| Turn | Result |
| --- | --- |
| 3 | NPC uncertainty remains valid. |
| 5 | Bounded incidental smell and clothing remain valid. |
| 6 | Movement narration agrees with the destination. A hidden trail to another place stays invalid. |
| 8 | A background NPC can answer without an importance marker. |

## Novel-domain results

Passed, with no production vocabulary added for the fixtures:

- granary door warped, unknown who and unknown cause, valid
- a named agent plus a because-cause on that door, invalid
- cistern split, with “not holding” valid and “not split” invalid
- “You lean over the loom” is not a new proposition about a threaded loom

## Slice 1–3

Passed on the final tree: Slice 1 (9), Slice 2 (7), Slice 3 (7). Strengthening, polarity, and qualifier contradictions still fail. The mention-only path still records value overreach when a sentence substitutes a stronger state.

## C18–C27 and related suites

Final combined run of the required files: **365 tests, 359 passed, 6 failed**.

Passed:

- C18 immutable boundary (20)
- C19 hard authority (11), including the grounded third-bell reply. The morning sentence is classified with the full reply, so the sibling “third bell” anchor can ground it. An ungrounded third-bell reply with no schedule in the corpus still regenerates.
- C20–C27
- resolution contract (72), including retry preservation of the existing contract
- bounded improvisation authority (5)
- realization authority and provenance
- state authority
- unparsed movement narration integrity
- unresolved travel narration authority
- attachment repair file (22)

The 6 failures are all in `tests/test_scene_transition_authority.py`:

- `test_chat_mixed_farewell_and_declared_travel_overrides_dialogue_lock`
- `test_actionable_lead_declared_travel_authoritative_arrival_and_lead_metadata`
- `test_declared_travel_unresolved_movement_no_social_no_scene_change`
- `test_declared_travel_eastern_square_disambiguates_against_prior_milestone_lead`
- `test_combined_prior_lead_affirmed_waste_gpt_scene_proposal_non_authoritative`
- `test_unresolved_alternate_destination_with_prior_old_milestone_lead_no_substitution`

They fail at `resolution.kind` / `active_scene_id` (`social_probe` or the current scene, where the test expects `travel` and a destination change). `select_ordinary_resolver` still returns `social` when the contract operation is `ask` or the subject is social, and the travel stage is then not permitted. This repair does not change that selection. The decision is attached to whatever contract the owner already built. Seven other tests in that file passed. Turn 6’s movement-contract regression passed with a decision attached.

## Files changed

- `game/live_resolution.py`
- `game/ordinary_semantic_ownership.py`
- `game/api.py`
- `game/prompt_context.py`
- `game/gm_resolution_decision.py`
- `game/immutable_valid_response.py`
- `tests/test_pr_br_live_validation_attachment_repair.py`

## Known limitations

- Negation scope is clause-local with an immediate adverb window. It is not a general English parser.
- Derived denial covers the asked polar predicate. It does not derive physical consequences beyond that polarity.
- Actor, time, cause, meeting-place, and residue checks are small structural patterns. A novel phrasing outside those patterns can still slip through, and a coincidental match can still be rejected.
- Bounded repair removes whole violating sentences. It does not rewrite a clause inside a sentence.
- Historical saved-gate turns still lack reconstructable decision identities.
- The six scene-transition failures above remain. They are resolver-ownership outcomes of the existing contract, not a second decision owner.

## Recommendation

The live failures were an unattached decision and a validator that discarded competent answers. Both are repaired on the targeted paths, with deterministic coverage and C18 still sealing accepted text. The scene-transition failures do not show that decision attachment took ownership away from the resolver.

A. LOCALIZED LIVE-VALIDATION DEFECTS ARE REPAIRED; PROCEED TO A SECOND LIMITED LIVE VALIDATION
