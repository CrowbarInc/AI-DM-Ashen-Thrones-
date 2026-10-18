# Four-turn proposition timeline

Source run: `artifacts/pr_br_final_live_validation/20261004T035044Z`
Workspace HEAD at run: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
Measurement only. This file reconstructs saved artifacts. It does not replay them.

Authoritative state at start established one consequential observation:

> The bathhouse pump's long iron handle is visibly bowed, and its pivot pin is sheared through.

Semantic identity: `kind=world_fact`, `subject=bathhouse_pump_handle`, `relation=observation`, `value=bowed handle and sheared pivot pin`, `polarity=positive`.
Subject aliases include `pump`, `pump handle`, `iron handle`, `pivot pin`.
Value aliases include the bare tokens `bowed` and `sheared`, plus `sheared pin`.
No cause, actor, time, history, witness, or recent-user fact was authored.

## P1 — The handle is bowed

| Field | Value |
| --- | --- |
| Proposition | The bathhouse pump handle is bowed. |
| First source | Authored `scene.visible_facts.0` |
| Source turn | Before turn 1 |
| Resolution Contract | Turn 1 subject retained: `bowed pump handle and the sheared pivot pin`. Dimension empty. |
| GMResolutionDecision | Proposed fact, `authored_world_fact`, `world_truth`, `ESTABLISH` |
| Epistemic act | `establish` |
| NarratedClaim | Turn 1 observation sentence carries this identity. Turn 3 causal sentence also carries this same identity. |
| Audit classification | `authored_world_fact` / `world_truth` / `established` |
| Temporal provenance | Not copied into the temporal ledger. It already lives in authored state. |
| Emitted | Turn 1 yes. Turn 3 yes, inside the causal sentence. |
| Committed | Authored state unchanged. No new world mutation. |
| Later reuse | Turn 3 alias overlap (`bowed`, `handle`, `sheared pin`) re-licenses the whole causal sentence. |
| Authority changes | None for P1 itself. P1's authority is copied onto other propositions. |

Why later authority changes around P1: `_semantic_identity_matches` treats value alias `bowed` plus the subject head `handle` as coverage of the observation. `_claim_from_row` then copies the observation's provenance onto the entire narration sentence.

## P2 — The pivot pin is sheared

| Field | Value |
| --- | --- |
| Proposition | The pivot pin is sheared through. |
| First source | Same authored fact as P1 |
| Source turn | Before turn 1 |
| Resolution Contract | Same inspection subject as P1 |
| GMResolutionDecision | Same proposed fact as P1. The authored record is one combined observation, not two claim objects. |
| Epistemic act | `establish` |
| NarratedClaim | Not a separate object. It rides inside the observation sentence and, on turn 3, inside the causal sentence. |
| Audit classification | Inherited `world_truth` |
| Temporal provenance | Authored state only |
| Emitted | Turns 1 and 3 |
| Committed | Unchanged authored state |
| Later reuse | Value alias `sheared pin` is sufficient, together with `handle`, to match the observation. |
| Authority changes | None for P2. The combined identity is what gets copied. |

Why: the authored semantic identity stores P1 and P2 as one value string plus loose aliases. The auditor never has two observation propositions to match independently.

## P3 — Excessive wear is possible

| Field | Value |
| --- | --- |
| Proposition | Excessive wear is a possible cause of the damage. |
| First source | Turn 1 narration |
| Source turn | 1 |
| Resolution Contract | Not represented. `dimension=null`, `dimensions=[]`. The interpretation pattern does not match `What does this damage suggest?` |
| GMResolutionDecision | No proposed fact. No `INFER` act. |
| Epistemic act | None |
| NarratedClaim | One sentence-level claim shared with P4: "Whether it was excessive wear or a sudden, violent pressure is unclear from the current evidence." |
| Audit classification | `speculation` / `observation` / `unresolved` / reason `unknown_cause_actor_or_time` / persistence `do_not_persist` |
| Temporal provenance | Not written to `gm_inferences`. Discourse `active_claim` stores the whole sentence, source `speculation`, status `unresolved`. |
| Emitted | Yes, after preservation deleted the stronger "suggests great force" sentence. |
| Committed | Discourse focus only |
| Later reuse | Turn 2 player treats the pressure branch as a hypothetical premise. |
| Authority changes | Created as unresolved speculation. Never promoted inside the ledger. Never stored as `gm_inference`. |

Why the authority is speculation rather than `gm_inference`: `remember_temporal_claims` writes `gm_inferences` only when `provenance == gm_inference`. This claim's provenance is `speculation`. `INFER` is appended by the decision builder only when the contract dimension set contains `interpretation`. That dimension was lost, so the act never existed, and the post-narration audit had nothing to type as an inference.

## P4 — Sudden violent pressure is possible

| Field | Value |
| --- | --- |
| Proposition | Sudden, violent pressure is a possible cause. |
| First source | Same Turn 1 sentence as P3 |
| Source turn | 1 |
| Resolution Contract | Not represented |
| GMResolutionDecision | Not represented |
| Epistemic act | None |
| NarratedClaim | Same single object as P3. Decomposition did not split wear from pressure. |
| Audit classification | Same unresolved speculation row |
| Temporal provenance | Same missing `gm_inference` |
| Emitted | Yes |
| Committed | As the Turn 1 active claim text, not as a typed inference |
| Later reuse | Turn 2 presupposes it. Turn 3 strengthens it. |
| Authority changes | Stays unresolved in the ledger. Turn 3 then classifies a stronger cousin as world truth through a different audit path. |

Why: one `NarratedClaim` was built for the sentence because `_UNKNOWN_SLOT_RE` matches `is unclear` and returns a single epistemic-status claim. The two alternatives inside the sentence are not objects.

## P5 — Sudden violent pressure is likely

| Field | Value |
| --- | --- |
| Proposition | Sudden, violent pressure is a likely cause. |
| First source | Turn 3 narration |
| Source turn | 3 |
| Resolution Contract | Confidence question bound to the Turn 2 player hypothesis. Dimension `confidence`. Interlocutor inherited as Nessa. Mode `npc_claim`. |
| GMResolutionDecision | Outcome `epistemically_qualified`. Proposed facts are only the authored corpus. Unresolved qualifier: `actor`. No cause fact. No likelihood fact. |
| Epistemic act | `establish` for authored rows, plus `leave_unresolved(actor)`. No `INFER`. |
| NarratedClaim | One object whose text is the whole first sentence and whose `semantic_identity` is the pump observation. |
| Audit classification | `authored_world_fact` / `world_truth` / `established` / `relation_kind=observation` / `scene.visible_facts.0` |
| Temporal provenance | `gm_inferences` stays empty. The Turn 2 `player_hypothesis` row is not updated. |
| Emitted | Yes. Initial generation accepted. No retry. |
| Committed | Accepted-claim metadata only. World state gains no cause field. |
| Later reuse | Still the active discourse claim after turn 4, still labeled as the player hypothesis, while the accepted audit says world truth. |
| Authority changes | From absent, to emitted likelihood, to authored world truth in the claim audit, without an establish event. |

Why: see the Turn 3 code path in the architecture report. Alias coverage copied P1/P2 authority onto this sentence. `likely cause` matches none of the causal, evidential, or cause-attribution detectors. `I can't swear` is a non-assertion for `epistemic_frame`, so the older proposition classifier drops the sentence instead of holding it as uncertainty.

## P6 — Sudden violent pressure caused the damage

| Field | Value |
| --- | --- |
| Proposition | Sudden, violent pressure caused the bowed handle and sheared pin. |
| First source | Turn 3 narration, entailed by "likely cause of" |
| Source turn | 3 |
| Resolution Contract | The player asked whether this is known or only possible. The contract binds confidence. It does not authorize a cause. |
| GMResolutionDecision | Cause is not a proposed fact. Constraint text says cause may be called unknown. |
| Epistemic act | `leave_unresolved` covers `actor` only. Cause was not even opened as a qualifier, because the decision's cause slot is added only for why/what-caused questions. |
| NarratedClaim | Not separate from P5. The causal relation has no identity of its own. |
| Audit classification | Inherited `world_truth` from the observation match |
| Temporal provenance | Not consulted. The player-hypothesis row already existed and was not read by `audit_narrated_claims`. |
| Emitted | Yes |
| Committed | As the sentence's accepted world-truth claim |
| Later reuse | None in turn 4 prose. The false classification remains in that turn's accepted audit. |
| Authority changes | Player hypothesis and GM likelihood become, in the audit record, an established authored cause. |

Why: there is no monotonicity check. Authorization does not load `narration_temporal_provenance`. A proposition gains `world_truth` because its sentence mentions an authorized observation.

## P7 — Some actor applied the pressure

| Field | Value |
| --- | --- |
| Proposition | Someone applied the force. |
| First source | Turn 2 player question, then Turn 3 narration ("who might have applied such force") |
| Source turn | Player: 2. Narration: 3. |
| Resolution Contract | Turn 2 did not bind the actor question to the active claim. Turn 3 leaves actor unresolved. |
| GMResolutionDecision | Turn 2 and Turn 3 include `LEAVE_UNRESOLVED(actor)`. |
| Epistemic act | `leave_unresolved` |
| NarratedClaim | Turn 3 sentence 2 was not given a decision claim row. |
| Audit classification | Older proposition classifier: `npc_claim` / `uncertain` / `consequential=false` |
| Temporal provenance | None |
| Emitted | Yes, inside "without ... knowing who might have applied such force" |
| Committed | No actor in world state |
| Later reuse | None |
| Authority changes | The decision correctly refuses an actor. Narration still speaks as if an applying-event is the thing being unknown, which presupposes the event. |

Why the presupposition survived: uncertainty exemptions in `_ordinary_residual_reasons` and `_structured_consequential_reasons` return no residual once `epistemic_frame` is `uncertain`. `might` makes that frame true. The sentence then produces an empty decision-claim list.

## P8 — Recent pump users may know something

| Field | Value |
| --- | --- |
| Proposition | People who used the pump recently exist and are an investigative source. |
| First source | Turn 3 narration |
| Source turn | 3 |
| Resolution Contract | Not represented. No lead slot. |
| GMResolutionDecision | No authorized lead, roster, or recent-user fact. |
| Epistemic act | None |
| NarratedClaim | None in `claim_results` |
| Audit classification | `npc_claim` / `uncertain` / `consequential=false` / `family=none` |
| Temporal provenance | `active_actionable_lead` stays null |
| Emitted | Yes |
| Committed | No |
| Later reuse | None in turn 4 |
| Authority changes | Invented, emitted, unaccounted by the decision audit. |

Why: `_GENERATED_LEAD_RE` requires a nearby token such as clue, evidence, useful, relevant, overlooked, answer, or detail. "Checking with those who used the pump recently ... could be a good next step" misses that list. `could` marks the sentence uncertain, which suppresses residual accounting.

## P9 — Nearby witnesses may know something

| Field | Value |
| --- | --- |
| Proposition | Nearby witnesses exist and may have seen the event. |
| First source | Turn 3 narration, same sentence as P8 |
| Source turn | 3 |
| Resolution Contract | Not represented |
| GMResolutionDecision | Not represented. Nessa exists; a witness class does not. |
| Epistemic act | None |
| NarratedClaim | None |
| Audit classification | Same non-consequential NPC-claim row as P8 |
| Temporal provenance | None |
| Emitted | Yes |
| Committed | No |
| Later reuse | None |
| Authority changes | Same as P8. One sentence, two invented leads, zero decision claims. |

## P10 — No hint of recent disturbance

| Field | Value |
| --- | --- |
| Proposition | Nothing around the pump shows a recent disturbance. |
| First source | Turn 1 narration |
| Source turn | 1 |
| Resolution Contract | Not represented |
| GMResolutionDecision | Not represented. Authored text establishes Nessa folding towels. It does not establish an absence of disturbance. |
| Epistemic act | None |
| NarratedClaim | None in the accepted decision audit |
| Audit classification | `npc_claim` / `uncertain` / `consequential=false`. The hedge list includes the token `around`, and this sentence says "around the pump". |
| Temporal provenance | None |
| Emitted | Yes. Preservation kept the sentence. |
| Committed | No absence fact |
| Later reuse | Not repeated |
| Authority changes | Created by narration and treated as safe uncertain texture. |

Why: `epistemic_frame` returns `uncertain` because `_HEDGE_RE` contains `around`. Family `none` plus an uncertain frame becomes a non-consequential NPC claim. The decision auditor also treats uncertainty as a reason to emit no residual. The absence proposition is never owned.

## P11 — The speaker saw the event

| Field | Value |
| --- | --- |
| Proposition | The speaker saw something from which the likely cause follows ("from what I saw"). |
| First source | Turn 3 narration |
| Source turn | 3 |
| Resolution Contract | Nessa is the interlocutor because Turn 2 social routing attached her. The contract does not authorize testimony about the damage. |
| GMResolutionDecision | Nessa's existence and towel-folding are established. No witnessed-event fact. |
| Epistemic act | None for testimony |
| NarratedClaim | Absorbed into the one world-truth observation claim |
| Audit classification | `world_truth` |
| Temporal provenance | None |
| Emitted | Yes |
| Committed | No testimony record |
| Later reuse | None |
| Authority changes | An unauthorized witness stance inherits the observation's authority because it shares the sentence. |

## P12 — Nessa looks up briefly while folding

| Field | Value |
| --- | --- |
| Proposition | Nessa looks up briefly from folding clean towels beside the cedar bench. |
| First source | Turn 4 narration. Folding beside the bench is authored. "Looks up briefly" is manner. |
| Source turn | 4 |
| Resolution Contract | `ask`, Nessa bound, dimension `smell`, mode `bounded_incidental` |
| GMResolutionDecision | Authored corpus only. No incidental proposal for the glance. |
| Epistemic act | `establish` for authored rows |
| NarratedClaim | The glance sentence is not its own claim row. The quoted reply is the claim row. |
| Audit classification | Omitted from `claim_results` |
| Temporal provenance | Not in `accepted_incidentals` |
| Emitted | Yes |
| Committed | No |
| Later reuse | None |
| Authority changes | Harmless manner emitted without a persistence record. |

## P13 — The soap by the washbasin is lavender-scented

| Field | Value |
| --- | --- |
| Proposition | Nessa uses a lavender-scented soap by the washbasin. |
| First source | Turn 4 quoted NPC speech |
| Source turn | 4 |
| Resolution Contract | Mundane smell question, correctly Nessa-addressed |
| GMResolutionDecision | No soap-scent fact. Outcome `epistemically_qualified`, persistence policy `claim_only`. |
| Epistemic act | No inference act |
| NarratedClaim | One combined quoted claim covering P13 and P14 |
| Audit classification | `npc_claim` / `claim_only` / `hearsay` / `epistemically_qualified` |
| Temporal provenance | `accepted_incidentals` empty. `bounded_improvisation.entries` empty. Promotion `accepted_count=0`. |
| Emitted | Yes |
| Committed | Towel topic marked discovered. Scent not stored. |
| Later reuse | None in this run |
| Authority changes | Correctly kept off world truth, then dropped by both persistence buckets. |

Why: `remember_temporal_claims` stores an authorized claim only for `bounded_incidental`, `gm_inference`, or `player_hypothesis`. `claim_only` falls through and is ignored. `promote_accepted_bounded_improvisation` reads improvisation proposals, not `claim_results`, and this turn had none.

## P14 — Nessa prefers folding towels lengthwise

| Field | Value |
| --- | --- |
| Proposition | Nessa finds lengthwise folding easier and uses it to keep towels neat. |
| First source | Same Turn 4 quotation as P13 |
| Source turn | 4 |
| Resolution Contract | The folding-preference half of the question is real; the contract dimension recorded is `smell` only. |
| GMResolutionDecision | Not a separate fact |
| Epistemic act | None |
| NarratedClaim | Same single quoted span as P13. The quote splitter did not finish the closing quote in the stored claim text. |
| Audit classification | Same hearsay NPC claim |
| Temporal provenance | Same empty buckets |
| Emitted | Yes |
| Committed | No preference record |
| Later reuse | None |
| Authority changes | Same as P13. Mundane NPC invention was recognized as a claim and then persisted nowhere. |

## Authority-change summary

| Transition | What changed | Why |
| --- | --- | --- |
| Authored observation -> Turn 1 narration | P1/P2 restated. P3/P4/P10 created. | Narration is unrestricted. The contract lost `interpretation`, so the decision authorized no inference. |
| Explicit "suggests great force" -> rejected | Strong evidential wording removed | `_EVIDENTIAL_RELATION_RE` matches `suggests`. That phrase was in the detector list. |
| P3/P4 kept -> speculation, not `gm_inference` | Epistemic status unresolved, persistence `do_not_persist` | `is unclear` matches the unknown-slot pattern. The temporal writer ignores `speculation`. |
| Turn 2 player sentence -> `player_hypothesis` | Typed and not promoted | `player_hypothesis_claims` matches `if` / `so ... bent`. This path does not read narration. |
| Turn 2 useful answers -> fallback | No new world claim | Speaker enforcement saw Nessa speech against a null interlocutor. Local routing. |
| Turn 3 P5/P6 -> `world_truth` | Unsupported cause inherits P1/P2 | Sentence-level identity coverage. Residual vocabulary misses `likely cause`. |
| Turn 3 P8/P9 emitted | Leads exist for the player and nowhere in the decision | Uncertainty plus a lead pattern that does not mention those words. |
| Turn 4 P13/P14 -> hearsay, then nowhere | Claim audit and persistence disagree | Temporal bucket and improvisation ledger do not consume `npc_claim` audit rows. |
