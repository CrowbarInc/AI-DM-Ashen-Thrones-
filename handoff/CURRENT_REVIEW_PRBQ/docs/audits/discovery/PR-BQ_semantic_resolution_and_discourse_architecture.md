# PR-BQ - Semantic Resolution and Discourse Architecture Discovery

Date: 2026-09-27

Type: discovery / architecture reconciliation only.

No production gameplay changes were made. No new synthetic campaign or live gameplay/model turn was run for this audit.

## 1. Executive Summary

PR-BP improved the live pipeline, but V3.6 still failed 13 of 40 synthetic turns. This audit confirms 11 of those 13 as genuine player-facing semantic failures and classifies 2 as useful partial answers / evaluator-boundary false positives. The failures are not many unrelated edge cases. They concentrate around four architectural deficiencies:

1. Perception specificity is not structurally represented. The engine records "inspection" or "bounded sensory detail" at best, but not sound vs smell vs wear vs use vs changed-state as a first-class request contract.
2. Cross-turn referents have fragmented ownership. Social target continuity, referent-tracking artifacts, pending leads, bounded NPC claims, and recent transcript memory each hold pieces, but no single structure owns "that lead", "them", "that place", or "what they said" as a resolved discourse object.
3. The interaction obligation contract is too coarse. It preserves kind/target/subject/requested_outcome, but the requested_outcome is prose and does not encode source, confidence, location, time, perceptual dimension, action outcome, or epistemic mode.
4. Generation, final emission, and evaluation do not share the same semantic contract. The prompt receives broad hard rules and narration obligations, final emission validates legal/safe/provenance properties, and the evaluator re-infers intent from raw text and surface token overlap.

Recommended minimum architecture: introduce a small typed resolution contract owned upstream of narration and carried through obligation, generation, retry/final emission, and evaluator. Pair it with lightweight discourse referent slots for active interlocutor, active claim, active actionable lead, and active scene target. Do not build a large semantic framework yet.

## 2. PR-BP V3.6 Baseline

Primary evidence:

- `docs/audits/PR-BP_live_resolution_and_synthetic_gate.md`
- `artifacts/pr_bp_synthetic_gate/20260927T220411Z/campaign_summary.json`
- `artifacts/pr_bp_synthetic_gate/20260927T220411Z/failure_clusters.md`
- `artifacts/pr_bp_synthetic_gate/20260927T220411Z/*/run.json`
- `artifacts/pr_bp_synthetic_gate/20260927T220411Z/*/transcript.md`

Final V3.6 totals:

| Metric | Value |
|---|---:|
| Sessions | 4 |
| Turns | 40 |
| Semantic failures | 13 |
| Fallback repeat flags | 1 |
| Turns with incidental entries | 19 |
| Turns with NPC-claim entries | 8 |
| Synthetic gate | FAIL |
| Human playtest recommendation | Not recommended |

PR-BP added live PR-BN routing, accepted-content delivery, interaction obligations, interlocutor continuity, speaker grounding/repair, retry preservation, and evaluator hardening. Its own final note says further repair requires a broader decision about cross-turn referent ownership, dimension-specific perception resolution, and final-emission length/quality boundaries.

## 3. 13-Failure Inventory

Legend: "Confirmed" means a genuine player-facing problem. "Boundary" means the evaluator is defensible but over-strict, or the answer is useful enough that a human DM would likely accept it with caveats.

| # | Session / turn | Player input | Visible context | Intended interaction | Target / referent | Requested semantic dimension | DM response | Runtime resolution / obligation | PR-BN / final route | Assessment |
|---:|---|---|---|---|---|---|---|---|---|---|
| 1 | `goal_oriented` T2 | "I approach that person and ask what I need to do to enter safely." | Prior ask: "Who seems to be in charge here?" GM: guard cannot verify talk. | Approach identified person and ask entry procedure. | "that person" should likely bind to prior guard / authority figure. | Action plus procedural information. | "No reliable source here can verify the requested information; another source is needed." | `question`; obligation `kind=question`, target "what i need to do to enter safely", no interlocutor. | No visible PR-BN involvement; final metadata empty in runner. | Confirmed. Referent/interlocutor not preserved; action portion lost. |
| 2 | `goal_oriented` T8 | "I follow the best lead toward shelter or work." | Prior ask: sleep without trouble; GM: guard cannot verify. | Act on a previously offered lead, or clarify no lead exists. | "best lead" should bind to shelter/work lead if one exists. | Action outcome / lead pursuit. | Guard says, "I do not know enough to answer that." | No resolution / no obligation captured. | No PR-BN; no final metadata. | Confirmed. Obligation absent; referential action became generic nonanswer. |
| 3 | `goal_oriented` T9 | "I ask for one concrete next step I can act on immediately." | Prior T8 generic nonanswer. | Ask for actionable next step. | Current interlocutor / local source. | Requested actionability. | "No reliable source here can verify the requested information; another source is needed." | `question`; obligation target truncated "for one concrete next step..." no interlocutor. | No PR-BN; final metadata present but generic. | Confirmed. Shape preserved as question, specificity/actionability lost. |
| 4 | `curious_explorer` T3 | "What ordinary sounds and smells stand out where I am?" | Prior nearby-question got guard uncertainty. | Inspect current scene for sound and smell. | Current scene. | Sound + smell. | Generic visual scene: watchers/refugees/gate serjeant/roster board. | `observe`; obligation `kind=inspection`, subject raw question. | No live-resolution metadata in extracted turn; no PR-BN counters. | Confirmed. Perception dimension lost. |
| 5 | `curious_explorer` T5 | "What can I learn from its wear, marks, or use?" | Prior inspected nearby door/sign/stall/fixture; GM redirected to notice board. | Inspect referred object for wear/marks/use. | "its" should bind to prior inspected surface / notice board. | Wear, marks, use. | Same generic visual scene summary. | `observe`; obligation `kind=inspection`, subject raw question, no resolved referent. | No PR-BN counters. | Confirmed. Referent plus requested property lost. |
| 6 | `social_persistent` T3 | "How certain are you, and who would know more?" | Prior: "Who told you that?" GM: cannot verify source/certainty. | Ask confidence and better source. | Active claim `bi_c62cd758bc22`; guard captain. | Confidence + source / next source. | Guard repeats cannot verify source or certainty. | `question`; obligation `kind=follow_up`, claim id present, subject is long/truncated claim text. | NPC claim id present. | Confirmed partial failure. Certainty/source addressed, "who would know more" not answered. |
| 7 | `social_persistent` T4 | "Can you introduce me or point me to them?" | Prior asks who would know more; GM cannot verify. | Request action from guard: introduce/point. | "them" = the better source / knowledgeable people. | Requested action. | Guard: "I will not carry out that request; you will need another route." | `question`; obligation `kind=action_request`, target guard, claim id present. | NPC claim id present. | Confirmed. Contract can say action_request but not "introduce/point to source"; fallback too abstract. |
| 8 | `social_persistent` T6 | "I ask about food, lodging, or a safe place to wait." | Prior: if cannot help directly, what useful thing can you do? GM: guard cannot verify. | Ask for practical services / safe place. | Local service/shelter topic. | Food, lodging, safe waiting. | "If you're looking for a safer spot or a warm meal, the tavern runner near the rain barrel knows the best places to go..." | `question`; obligation target about food/lodging/safe place; no interlocutor. | No PR-BN counters. | Boundary false positive / useful partial. It does redirect to a concrete source and location, though it does not name the actual place. |
| 9 | `social_persistent` T7 | "What does that place look like from here?" | Prior answer points to tavern runner near rain barrel / best places. | Resolve "that place" and visually describe it from current vantage. | "that place" unclear but likely tavern runner / rain barrel / safe place. | Appearance and spatial visibility. | Long generic Cinderwatch gate description, truncated mid-sentence. | `investigate`; obligation `kind=inspection`, resolution_mode `bounded_improvisable_request`. | Likely bounded route, but no extracted live-resolution metadata; final text truncated. | Confirmed. Referent unresolved; final-emission/delivery quality also implicated. |
| 10 | `social_persistent` T8 | "I thank them and ask for one final warning before I move." | Prior was truncated generic scene description. | Social thanks plus final warning. | "them" has weak referent; warning request is clear. | Warning / actionable caution. | "If you value your freedom, keep to the rules and avoid drawing undue attention..." | `question`; obligation target final warning, no interlocutor. | No PR-BN counters. | Boundary false positive / useful partial. It gives a warning; speaker/referent grounding is weak. |
| 11 | `mundane_actor` T5 | "I take the next safe step they suggested." | Prior inspected suggested place/object; GM says nothing matches; notice board lists taxes/curfew/missing patrol. | Execute suggested next step or clarify none exists. | "they suggested" unresolved. | Referential action. | "The requested action cannot be completed here; another route is needed." | `custom`; obligation `kind=action_request`, target `referenced_next_step`. | No PR-BN counters. | Confirmed. It detects action shape but lacks referent/action semantics. |
| 12 | `mundane_actor` T6 | "What changes around me when I do that?" | Prior action could not be completed. | Ask changed-state consequence of attempted action. | "that" = prior attempted next step. | Change/state delta. | Generic visual scene summary. | `observe`; obligation `kind=inspection`, raw question as subject. | No PR-BN counters. | Confirmed. Changed-state dimension lost; should report no action/no change or a specific consequence. |
| 13 | `mundane_actor` T9 | "I confirm the immediate next action before I move on." | Prior chose cautious route; GM says patrol route changed after census choke. | Confirm next action. | Current route / missing patrol lead. | Action confirmation. | Atmospheric route/path description without confirming an action. | No resolution / no obligation captured. | No PR-BN; no final metadata. | Confirmed. Actionability contract absent at final boundary. |

## 4. Independent Validation of Evaluator Classifications

Confirmed genuine failures: 11 / 13.

Evaluator-boundary / useful partial cases: 2 / 13.

- `social_persistent` T6 is a useful partial answer: it gives "tavern runner near the rain barrel" as a concrete source for food/warm meal/safe spot. It should probably pass as a redirect unless the stricter product bar requires the actual place.
- `social_persistent` T8 gives a direct warning. It is weakly grounded because "them" has drifted, but the requested warning is visible.

Evaluator false negatives are also possible outside the 13 because the evaluator remains surface-text driven. This audit did not re-score all passing turns.

## 5. Failure Clustering

| Cluster | Confirmed failures | Sessions | Representative turns | Likely mechanism |
|---|---:|---|---|---|
| Perception specificity | 3 | `curious_explorer`, `mundane_actor` | CE T3, CE T5, MA T6 | Requested perceptual/property dimension is not typed; generic observe fallback satisfies only scene relevance. |
| Cross-turn referent / discourse ownership | 4 | `goal_oriented`, `curious_explorer`, `social_persistent`, `mundane_actor` | GO T2, GO T8, SP T7, MA T5 | Pronouns and discourse phrases are split across interaction context, referent tracking, pending leads, claim ledger, and transcript memory. |
| Resolution specificity / actionability | 4 | `goal_oriented`, `social_persistent`, `mundane_actor` | GO T9, SP T3, SP T4, MA T9 | Obligation knows "question/action/inspection" but not the exact satisfaction condition. |
| Final-emission / delivery quality | 1 primary, overlaps others | `social_persistent` | SP T7 | Accepted or generated content can become truncated/generic; final emission lacks the same semantic satisfaction contract. |
| Evaluator mismatch | 2 | `social_persistent` | SP T6, SP T8 | Evaluator re-infers from raw text and tokens, not shared production semantics; useful partials can fail. |

Conclusion: the failures represent a small number of architectural deficiencies, not 13 unrelated bugs.

## 6. Semantic Information Lifecycle

Actual production lifecycle inferred from code and artifacts:

`raw player text -> intent/parser/social routing -> resolution -> live resolution mode -> interaction obligation -> prompt/narration obligations -> model candidate -> PR-BN proposal validation/promotion -> retry/final emission -> evaluator`

| Concept | Parser / routing | Resolution | Live resolution mode | Interaction obligation | Prompt / generation | Retry / final emission | Evaluator |
|---|---|---|---|---|---|---|---|
| Action type | Exists as action `type` / social route | Exists as `resolution.kind` | Partially mapped to mode | Partially exists as `kind` | Partially via prompt rules | Partially via response type/fallbacks | Re-inferred |
| Target | Partially exists (`target_id`, active target) | Partially exists | Exists as compact string | Exists but often raw/truncated | Prompt has target hints and referent artifact | Validates visibility/speaker, not target satisfaction | Re-inferred tokens |
| Interlocutor | Exists in interaction context/social resolver | Exists for social result | Partially as `speaker_id` | Exists when bound | Prompt has active target rules | Strict social validates speaker | Re-inferred |
| Conversational subject | Partial transcript/topic anchor | Partial social metadata | Partial `topic` | Partial `subject`, often raw text or long claim | Broad hard rules | Not a satisfaction contract | Re-inferred |
| Requested property | Does not exist structurally | Does not exist | Does not exist beyond regex category | Does not exist; only raw `subject` | Broad "answer concretely" rule | Not validated | Some hard-coded evaluator regex |
| Perceptual dimension | Does not exist structurally | Does not exist | Collapsed to `sensory_detail` | Does not exist except raw text | Broad perception rule; no dimension field | Perception grounding can replace with generic visible fact | Hard-coded smell/sound/look/color snippets |
| Desired outcome | Partial action kind | Partial success/failure/hint | Partial completeness boolean | Exists as prose `requested_outcome` | Prompt rules ask for direct answer | Fallback line chooses generic shape | Re-inferred |
| Question type | Partial regex | Partial `question` kind | Partial | Coarse | Broad prompt rule | Not semantic | Re-inferred |
| Source/confidence/time/location | Does not exist as fields | Sometimes in prose/claim content | NPC claim category only | Claim id may exist; dimensions do not | Prompt asks for concrete person/place/fact | No typed validation | Source has limited regex |
| Prior-turn referent | Fragmented | Fragmented | Reads active target/claim opportunistically | Sometimes claim id/target | Referent artifact for entity ambiguity, not discourse objects | Referent clarity repairs pronouns, not semantic binding | Re-inferred |
| Epistemic requirement | Partial `epistemic_status` for NPC claims | Partial success/hint | NPC claim has hearsay | Not general | Prompt uncertainty rules | Generic refusal/nonanswer fallback | Hard-coded nonanswer rules |
| Success/refusal/unknown/clarification | Exists in resolution/fallback prose | Exists but uneven | Completeness boolean | Prose outcome | Prompt rules | Fallback lines | Re-inferred |

## 7. Existing Representation Inventory

| Structure | Source | Fields | Producer | Consumers | Lifetime | Cross-turn | Model-generated? | Authoritative? | Used by final emission / evaluator | Finding |
|---|---|---|---|---|---|---|---|---|---|---|
| `ResolutionModeDecision` | `game/live_resolution.py` lines 97-104 | mode, reason_codes, target, speaker_id, topic, proposal kind/category, epistemic_status | `select_resolution_mode` | live proposal synthesis, metadata | Turn | No | Deterministic | Routing helper | Metadata; not evaluator | Useful but lossy. `sensory_detail` is not sound/smell/wear/use. |
| `InteractionObligation` | `game/live_resolution.py` lines 107-114 | kind, target, interlocutor_id, subject, requested_outcome, claim_id, resolution_mode, turn_index | `derive_interaction_obligation` / `attach_interaction_obligation` | terminal fallback, metadata, synthetic artifacts | Turn metadata | Claim id may bridge | Deterministic | Partial | Some final-emission preservation; evaluator not shared | Exists, but too coarse and often absent. |
| Response type contract | `game/response_type_gating.py`, `game/api.py` | required_response_type, source_route, strict flags, debug | API turn pipeline | final emission validators | Turn | No | Deterministic | Yes for response shape | Final emission yes; evaluator no | Owns answer/action shape, not requested semantic dimension. |
| Narration obligations | `game/prompt_context.py`, `game/api_turn_support.py` | active_npc_reply, scene momentum, reply kind, opening etc. | prompt context helpers | model prompt | Turn | Some session context | Deterministic | Prompt contract | Prompt only | Broad output requirements, not resolution semantics. |
| Interaction context | `game/interaction_context.py` | active_interaction_target_id, mode, kind, topic-ish state, emergent addressables | social routing/context APIs | social, prompt, referent tracking | Session | Yes | Deterministic | Yes for social target | Final emission speaker checks; evaluator no | Owns social target, not claims/leads/discourse referents. |
| Referent tracking artifact | `game/referent_tracking.py` lines 936-1295 | active entities, active_interaction_target, continuity_subject/object, pronoun strategy, ambiguity, clause plan | prompt context | prompt, final emission referent clarity | Turn artifact | Uses continuity inputs | Deterministic | Visibility/referent clarity | Final emission yes; evaluator no | Excellent entity/pronoun artifact, not a discourse object resolver. |
| Bounded improvisation ledger | `game/bounded_improvisation.py` | entries, kind, category, content, status, source, speaker, epistemic_status | PR-BN evaluation/promotion | prompt projection, final emission recognition | Session | Yes | Model proposal + deterministic validation | Yes for bounded facts/claims | Final emission partially; evaluator no | PR-BN authority exists, but entries are not bound to requested resolution dimensions. |
| Intent parser actions | `game/intent_parser.py` | id, label, type, prompt, target ids, metadata lanes | parser | API/exploration | Turn | Sometimes through leads | Deterministic | Yes for action route | Indirect | Captures route and target, not semantic inquiry dimensions. |
| Playability evaluator | `game/playability_eval.py` lines 613-725 | request kind, token terms, hard-coded patterns | evaluator | synthetic scoring | Offline/turn | Prior text only | Deterministic | Evaluation only | No production use | Separate interpretation; not shared with production. |

Classification: the needed representation exists redundantly in several incompatible/lossy forms, and the missing piece is a shared typed resolution contract. Some referent machinery exists but is scoped to entities/pronouns, not discourse claims/leads/actions.

## 8. Perception-Specificity Analysis

Representative failures:

- CE T3 asks for ordinary sounds and smells. Runtime obligation: `kind=inspection`, target/subject raw question. Response: generic visible scene.
- CE T5 asks what can be learned from wear/marks/use. Runtime obligation: `kind=inspection`, no resolved "its". Response: same generic visible scene.
- MA T6 asks what changes around me when I do that. Runtime obligation: `kind=inspection`, raw question. Response: same generic visible scene.

Where specificity is preserved:

- Raw player text preserves sound/smell/wear/use/change.
- `obligation_preserving_fallback_line` has regex branches for sounds/smells and wear/marks/use (`game/live_resolution.py` lines 325-352), but this is fallback prose logic, not a general contract.
- Evaluator has hard-coded sound/source/look/color checks (`game/playability_eval.py` lines 613-659).

Where specificity is generalized or lost:

- `select_resolution_mode` maps all incidental description to `proposal_category="sensory_detail"` (`game/live_resolution.py` lines 431-439).
- `derive_interaction_obligation` maps observe/investigate/incidental description to `kind=inspection` and a prose outcome (`game/live_resolution.py` lines 251-252).
- Prompt rules say answer questions and handle behavioral perception but do not receive `requested_dimension=sound` or `requested_property=wear`.
- Perception grounding can replace unsupported perception with visible-scene fallback; it protects non-invention but cannot satisfy dimensions it never receives.

Likely cause: parser/obligation loss plus prompt/final-emission lack of a dimension-specific contract. This is not only evaluator weakness.

## 9. Cross-Turn Referent Analysis

Current owners:

- `interaction_context.py` owns social active target and scene-addressable interlocutors.
- `referent_tracking.py` owns visible entity / pronoun risk artifacts for prompt and final emission.
- Bounded improvisation ledger owns accepted NPC claims and incidental content.
- Lead registry/pending leads own actionable lead rows.
- Prompt context and conversational memory expose recent transcript slices.
- Playability evaluator uses raw prior player/GM text only.

Answers to requested questions:

1. Explicit discourse state: partially. There is interaction context and referent tracking, but no unified discourse object state.
2. Recent transcript sufficiency: the system often relies on it, especially prompt/evaluator, but V3.6 shows it is insufficient.
3. Stable entity IDs: yes for scene/NPC/visible entities.
4. Stable claim IDs: yes for PR-BN NPC claims, e.g. `bi_c62cd758bc22`.
5. Obligations can reference prior claims: yes via `claim_id`, but not source/confidence/location/action dimensions.
6. Model can resolve referent and fail to persist: likely, because accepted/generated text can mention leads/places without creating a typed discourse referent.
7. Retries can lose resolved referents: yes in effect; final turns with empty obligations show no contract survives.
8. Final emission can receive less referential context than generation: yes; final emission has referent artifacts and response contracts but not a typed "that lead means X" contract.
9. Cross-turn conversational focus owner: fragmented between interaction context, social continuity, prompt memory, and bounded claims.
10. Ownership fragmented: yes.

## 10. Resolution-Contract Analysis

Current interaction obligations can distinguish:

- `question`
- `action_request`
- `inspection`
- `social_request`
- `follow_up`
- `clarification`

They cannot structurally distinguish:

- inspect object vs inspect object for wear
- listen through object vs look at object
- determine whether object was recently used
- ask source of rumor vs ask confidence in rumor vs ask location/time associated with rumor
- ask NPC to act on rumor vs ask NPC to explain rumor

`requested_outcome` is human-readable prose. It is useful for fallback shaping, but insufficient as a validation contract.

Verdict: current obligation structure is structurally too coarse, not merely underused.

## 11. Generation-Contract Analysis

The prompt receives strong generic rules:

- answer direct questions explicitly;
- give concrete names/places/facts/directions;
- use active interlocutor as default counterpart;
- follow narration obligations;
- preserve NPC reply expectations.

See `game/prompt_context.py` around lines 1970-1997.

It does not receive a shared typed contract such as:

- `operation=perceive`
- `target=notice_board`
- `dimension=wear/use`
- `referent=claim#...`
- `question_dimension=confidence`
- `required_answer_shape=confidence_plus_next_source`

Therefore the model is often asked to reconstruct semantic intent from raw player text after the engine has already interpreted it. That duplication contributes to failures because downstream validation does not know the exact reconstruction it wanted.

## 12. Final-Emission Analysis

Final emission is intentionally conservative. PR-BM correctly describes it as expression/legal/safety/provenance enforcement, not semantic invention. It validates speaker grounding, response type, referential clarity, visibility, narrative authority, context separation, and acceptance quality.

Lossy boundaries observed:

- Empty obligations in GO T8, MA T9 leave final emission without a semantic satisfaction target.
- Generic observe text can survive for sound/smell/wear/change questions because final emission checks grounding, not dimension satisfaction.
- SP T7 shows a likely final/delivery quality issue: a bounded-improvable inspection response is truncated mid-sentence.
- Accepted-content delivery is improved by PR-BP, but delivery recognition is content/provenance oriented rather than contract-satisfaction oriented.

Final emission knows "grounded", "speaker-valid", "response-type-valid", and "accepted bounded text available" better than it knows "this answers requested dimension X."

## 13. Evaluator-Contract Analysis

The evaluator does not use production obligations or live-resolution contracts. It re-infers request kind and satisfaction from raw player text, GM text, token overlap, and hard-coded regex patterns. Examples:

- color/look/source/action/sound rules are in `game/playability_eval.py` around lines 613-659;
- generic nonanswer and player-intent gates are around lines 661-725.

Risks:

- Product can fail when a response is topically relevant but dimension-wrong.
- Product can pass when token overlap hides a missing semantic dimension.
- Useful partial redirects can fail because evaluator lacks the production/DM notion of acceptable partial resolution.
- Production and evaluator can disagree because they do not share a contract object.

## 14. Shared Root Causes

1. Semantic request specificity is captured as raw text/prose, not typed fields.
2. Discourse referents are not unified across entities, claims, leads, places, actions, and prior utterances.
3. Obligation preservation improves shape but not satisfaction conditions.
4. Generation receives generic rules instead of a compact typed resolution target.
5. Final emission validates safety/grounding/shape more than semantic fulfillment.
6. Evaluator independently reconstructs intent instead of checking the same contract production used.

## 15. Architectural Options

### Option A - Extend Existing Interaction Obligation

Add fields to `InteractionObligation`: `operation`, `requested_dimension`, `requested_property`, `question_axis`, `referent_type`, `referent_id`, `expected_resolution_shape`, `epistemic_mode`.

Scope: `game/live_resolution.py`, API attachment points, prompt projection, final-emission preservation, evaluator bridge, focused tests.

Benefits: smallest change; builds on PR-BP. Risks: obligation object may become an overloaded dumping ground. Migration moderate. Compatible with PR-BN/PR-BP if fields are additive.

### Option B - Introduce Typed Resolution Contract

Create a separate `ResolutionContract` adjacent to obligation. Obligation remains delivery/shape; contract owns target, operation, dimension, property, referent, epistemic mode, action-vs-inquiry, and satisfaction criteria.

Scope: new small module, live resolution, parser/social/adjudication bridge, prompt context, final emission validators/read-only checks, evaluator.

Benefits: clean ownership; allows evaluator and production to share contract. Risks: more plumbing. Migration moderate-high but controlled if read-only at first.

### Option C - Lightweight Discourse Referent State

Add session-level discourse slots: active_interlocutor, active_claim, active_service_or_place, active_actionable_lead, active_inspected_object, last_attempted_action. Each slot stores stable id/type/source/confidence/expiry.

Scope: interaction context or new discourse module; parser/social/lead/BN promotion hooks; prompt/referent tracking inputs.

Benefits: directly addresses "that lead", "them", "that place", "what they said". Risks: state staleness and ownership conflicts if too broad. Migration moderate.

### Option D - Connect Existing Fragmented Structures

Without new schemas, project existing interaction context, referent tracking, claim ids, and leads into prompt/evaluator/final emission more consistently.

Benefits: fastest. Risks: does not solve perception dimensions or evaluator/production contract mismatch. Likely insufficient alone.

## 16. Recommended Minimum Architecture

Use a combination of B and C, narrowly scoped:

1. Add a small typed resolution contract, not a giant semantic framework.
2. Add lightweight discourse slots only for the dominant failure referents: active claim, active actionable lead, active inspected object/place, and last attempted action.
3. Keep interaction obligations, but make them reference the typed contract.
4. Feed the same contract to prompt, final-emission semantic preservation, and evaluator.

Required fields for first implementation:

- `contract_id`
- `turn_index`
- `request_kind`: `inquiry`, `action`, `social_action`, `clarification`
- `operation`: `perceive`, `inspect`, `ask`, `confirm`, `follow`, `act`
- `target_ref`: `{type, id_or_text, source}`
- `discourse_ref`: optional `{type=claim|lead|place|action|object, id, source_turn}`
- `dimension`: optional `sound|smell|appearance|wear|use|change|source|confidence|location|time|next_step`
- `expected_resolution`: `answer|partial|refusal|clarification|action_outcome`
- `epistemic_mode`: `authoritative|bounded_incidental|npc_claim|unknown_allowed`

## 17. Proposed Information Lifecycle

Recommended lifecycle:

`PLAYER TEXT`
-> parser/social/adjudication extracts candidate action/target
-> discourse resolver binds pronouns/claims/leads/objects when possible
-> typed resolution contract is created
-> interaction obligation references contract id and delivery shape
-> prompt receives compact contract plus discourse slot labels
-> PR-BN proposals, if any, record the contract id/dimension they satisfy
-> retry/final emission checks whether final text satisfies or safely refuses the same contract
-> evaluator scores against the same contract, not a separate raw-text interpretation

## 18. Future Implementation Boundary

Change:

- Add typed resolution contract creation for perception dimensions, source/confidence follow-ups, next-step/action confirmations, and referential action.
- Add discourse slots for active claim, active actionable lead, active inspected object/place, and last attempted action.
- Project contract into prompt context and evaluator artifacts.
- Add final-emission read-only check/metadata for contract satisfaction; do not let final emission invent missing semantic content.

Do not change:

- PR-BN authority rules or safety thresholds.
- Broad final-emission semantic repair policy.
- Full affordance registry.
- Large NLP/discourse engine.
- Synthetic player policy or full gate budget during implementation inner loop.

Migration strategy:

1. Create contract in parallel with existing obligation.
2. Record in metadata and synthetic artifacts first.
3. Use it for prompt hints and evaluator checks.
4. Only then add minimal final-emission preservation/refusal checks.

## 19. Synthetic-Test Funnel

Level 1: deterministic/focused tests; run freely.

Level 2: focused live-model probes; 5-10 total turns.

Level 3: synthetic smoke gate; 2 personas, 6-8 turns each.

Level 4: full synthetic gate; 4 personas, 10 turns each.

Autonomous full-gate retry limit: maximum one repair plus one additional full-gate rerun. If the second full gate still fails, stop, package evidence, and request review.

## 20. Token/Compute Budget

PR-BQ used existing artifacts and static code analysis only.

Live gameplay/model turns used: 0.

New synthetic campaigns run: 0.

No autonomous repair loop was started.

## 21. Open Questions

- Should useful partial redirects like "ask the tavern runner near the rain barrel" pass food/lodging/safe-place requests, or must they identify the actual place?
- Should final emission be allowed to replace dimension-wrong generic scene text with a non-inventive refusal, or only mark failure?
- Should active discourse slots live inside `interaction_context.py`, a new `discourse_context.py`, or the existing lead/social-memory structures?
- What is the minimal persistence lifetime for active inspected object/place in a scene with no stable authored object id?
- Should PR-BN entries carry `satisfies_contract_id` to make accepted-content delivery contract-aware?

## 22. Implicated Files / Subsystems

- `game/live_resolution.py` - live resolution mode, interaction obligation, fallback preservation.
- `game/intent_parser.py` - action/target parsing, perception/action lanes, qualified lead pursuit.
- `game/interaction_context.py` - active social target and interaction state owner.
- `game/referent_tracking.py` - entity/pronoun referent artifact; useful input but not discourse owner.
- `game/bounded_improvisation.py` - PR-BN accepted entries and NPC claims.
- `game/prompt_context.py` - prompt rules, narration obligations, referent artifact projection.
- `game/api.py` / `game/api_turn_support.py` - pipeline attachment points, PR-BN promotion, finalization.
- `game/perception_grounding.py` - non-invention perception replacement/fallback.
- `game/final_emission_gate.py` and `game/final_emission_*` - final validation, repairs, terminal fallback.
- `game/playability_eval.py` - evaluator intent/satisfaction inference.
- `tools/run_pr_bp_synthetic_gate.py` - synthetic artifact extraction and future contract capture.
- `tests/test_pr_bp_live_resolution_routing.py` - focused PR-BP coverage to extend for contract lifecycle.
