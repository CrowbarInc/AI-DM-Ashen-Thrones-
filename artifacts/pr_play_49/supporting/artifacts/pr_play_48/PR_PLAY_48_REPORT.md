# PR-PLAY-48 — Narrative Freedom Architecture Decision

## 1. Executive summary and verdict

**A — PASS for the architecture decision and bounded offline plan. No live-readiness claim.** Select **hybrid authority-bounded narration**: engine-owned outcomes and exact disclosure anchors, generated descriptive realization under a small set of context profiles, and a capability boundary preventing prose from entering state-adoption paths. Keep the PR-PLAY-47 controlled renderer for strict results and as the experimental comparator. Do not expand its template menu.

This decision guarantees neither truthful unrestricted English nor automatic detection of every invented consequence. It separates three obligations: engine state remains authoritative; selected information is delivered; surrounding prose is semantically faithful. The first two admit structural enforcement. The third remains partly heuristic and requires offline human review before any live recommendation. Calling a string `atmosphere` does not constrain its meaning.

PR-PLAY-49 should build one **offline-only, explicitly invoked, successful investigation preview**, using saved resolver results, immutable discovery sentences and one free-form prelude. No API routing, provider adapter, campaign writes, generalized memory, or production activation. The stopping point is a review packet establishing whether this small free-text surface improves expression enough to justify its semantic risk. Do not begin PR-PLAY-49 from this pass.

All examples newly written in this report and the adversarial corpus are **human-authored illustrative candidates**, not model output. Historical quotations and measured results are identified separately. Real provider requests/tokens in PR-PLAY-48: **0 / 0**. No application import or gameplay run is needed for this design pass.

## 2. Historical evidence reconciliation

Repository-relative paths in this packet identify retained sources. Raw evidence is copied into `supporting/` with hashes; `historical_extract.json` extracts the five recorded turns without changing the source.

| Pass | Confirmed artifact findings | Limits and corrections |
|---|---|---|
| 43 | `artifacts/pr_play_43/live_result.json` and `artifacts/pr_play_44/PR_PLAY_43_review.md`: one accepted AI opening; four gameplay interpretation calls; **zero gameplay narration calls**. Social, two investigations and authored travel resolved; scene/state coherent. Notice-board knowledge stored but omitted from reply. Five total requests, 37,326 input + 2,478 output = 39,804 tokens; provider latency 25.47 s; run 40.00 s; gameplay HTTP mean 3.20 s, max 4.999 s. | The sequence was mechanically functional, not uniformly successful player communication: T3 PARTIAL. State consistency scored 10/10; narrative subtotal 5/10. These are retained implementing-agent judgments, not independent ratings. Opening dominates input usage (26,714 tokens); do not attribute all cost to gameplay narration. |
| 44 | `PR_PLAY_44_REPORT.md`, `before_notice.json`, `after_notice.json`: earliest lossy step was prepared action-outcome repair; clue text replaced by generic acknowledgment. Repair preserves selected disclosures through fallback/final sealing. Synthetic actual context and unsupported coins/key probes expose gaps. | The old broad SECRET-canary test alone was confounded by scene replacement/instruction wording; PR45 corrected the interpretation using independent raw synthetic replay. Do not use that lone assertion as proof of exposure. |
| 45 | `PR_PLAY_45_REPORT.md`, `summary.json`, context evidence: public/known/revealed projection applied in context construction and before transport. Recognized unsupported changes reject whole drafts; fallback keeps clues. | Indirect possession/resulting-state claims still accepted. Public-field misclassification, semantic attribution and legacy adoption paths are not certified safe. |
| 46 | `metrics.json`, `corpus_after.json`, `residual_failures.json`: 69 cases, four ambiguous excluded from headline metrics; TP27/TN30/FP1/FN7, precision 96.43%, recall 79.41%. Seven residuals: indirect healing, condition removal, arrival, quest completion, allegiance, unfamiliar possession, wealth synonym. Harmless dust-in-pack falsely rejected. | Hand-labelled adversarial corpus, not population accuracy. Report recommends stopping phrase-recognizer expansion and moving to structural boundaries. Historical focused 83 passed; final selected regression 617 passed/23 failed; no changed baseline results. |
| 47 | `summary.json`, `expressive_range.json`, `NARRATIVE_COMPARISON.md`, renderer source: opt-in **offline preview only**, eight enum controls, no free-text selector field. 30 matrix outputs and ten stress outputs preserve tested anchors; ten stress outputs form only three recognizable structural families. | Narrative gains modest, strongest in clarity/completeness. Unblinded editorial scores, not measured player preference or live model creativity. Historical final selected tests: 675 passed, 23 existing failures, 58 new passes, zero changed existing outcomes. |

All five passes have retained reports and machine-readable evidence. The original PR43 centralized report is retained as a copy under PR44 rather than as a report in PR43. We did not re-run past providers or independently re-rate every output. Full historical campaign snapshots remain in `artifacts/atgb/pr_play_43/live/20261102T225835Z-b91e96381683`; selected raw HTTP/resolver records and usage are packaged where available, while their complete inventory/hashes remain in the repository. No missing source is replaced with invented results.

## 3. Current architecture and authority map

Existing flow: original player input → interpretation/grounding/admission → authoritative resolver and state/tick changes → existing plan/context → host speech or deterministic provider skip, otherwise GM narration → projection/structured and semantic checks → prepared policy repair/disclosure supplementation → immutable seal → final response. Narration is frequently skipped intentionally; eligibility, not budget exhaustion, explains PR43.

`game/exploration.py::resolve_exploration_action` and `process_investigation_discovery` own investigation results and discovery persistence. `game/models.py::ExplorationEngineResult` describes the resolver return. `authorized_information.revealed_information` selects successful, non-repeated discoveries; it does not query undiscovered clues and does not cover social `question` outcomes. `mechanical_claims.mechanical_outcome` derives effects, not a second state store. Social speech must use its existing separate authority contract.

`narration_authorization.project_narration_payload` detaches data, projects public/known/revealed information, excludes private NPC/faction mutations, and strips private extensions. `prompt_context.build_narration_context` and `gm.build_messages` apply the current boundary. This is stronger than PR44 but assumes authored public fields really are public and cannot prevent a model independently guessing a secret. Experimental input should use an explicit final allowlist, not inherit every surviving top-level planner structure.

`api.deterministic_provider_skip_line` and `api_turn_support._authoritative_resolution_fact_text` supply outcomes; `dialogue_authority.select_host_speech` supplies authorized NPC speech. `immutable_valid_response.validate_generated_response` includes the mechanical audit. `run_preserve_if_valid`, `seal_host_speech`, `seal_accepted_response`, `commit_text`, and API finalization preserve accepted text. Sealing protects bytes after acceptance, not the truth of an accepted semantic claim.

Important post-narration sinks remain: `api._apply_post_gm_updates` invokes bounded improvisation promotion, discourse claims and legacy scene/world adoption; validators `_validate_gm_scene_update_for_legacy_adoption` and `_validate_gm_world_updates_for_legacy_adoption` sanitize proposals. `world.apply_resolution_world_updates` and `apply_normalized_world_updates` are state owners. `gm.remember_recent_contextual_leads` extracts text into scene-runtime leads. A new narration string must not simply become a normal `gm` proposal object with empty-looking update fields and then traverse these sinks.

## 4. Narrative authority taxonomy

| Category | Representation and origin | Generation/validation/display | Retention |
|---|---|---|---|
| A: authoritative mechanical outcome | Transient immutable view of engine result: status, success, typed effects, source action/resolution reference. Delta distinguished from total balance. | Engine renders exact effects. AI may describe surrounding action only; schema rejects effect/update fields. Validate engine slot coverage and existing effect checks; display clear result sentence. | Existing resolver/state owner persists once. Narration never reapplies effects. |
| B: authoritative world fact | Existing authored/state facts with source ID, public/known visibility and scene scope. Private B stays absent from narrator input. | Engine selects public subset; AI realizes within it. Check known consistency heuristically, with unknown claims unresolved; never infer canonical truth from prose. | Existing scene/world owners; prose repetition cannot establish identity, history, faction or route. |
| C: authorized discovery | Exact selected disclosure text plus source, status, qualifier/uncertainty, optional speaker; engine sequence IDs. | Immutable source sentence assembled independently of generation. Preserve every selected fact and all uncertainty. Paraphrase can surround it but cannot replace it in the minimum experiment. | Existing discovery/topic resolver owns knowledge. Display exact anchor even on generation failure. |
| D: incidental texture | Descriptive candidate with turn/scene provenance, `incidental`, no consequence grant. No universal registry required. | AI can improvise compatible sensation, rhythm, gesture, mundane detail; schema cannot prove harmlessness. Existing checks plus offline review; observed expression is not allegiance. | Ephemeral by default. Transcript retention records what was said, not a world fact. Limited continuity reference permitted; explicit promotion authority needed for consequences. |
| E: provisional assertion | Attributed observation/belief with source speaker, epistemic status and scope, separate from canonical B and C. | Preserve “seems”, “heard”, “might” and provenance. No privileged NPC knowledge; uncertainty words do not legalize new clues. Human semantic review for ambiguity. | Conversation history may retain as claim, never silently promote to truth. Revalidation required before action/state use. |

Persistence is orthogonal to truth: a stored rumor is still a rumor; an ephemeral sentence can still falsely claim damage. A typed field, label or UI badge is not a semantic firewall.

## 5. Persistence, continuity and the chipped cup

Every narrated detail need not become state. Rain cadence, dust motion and a pause may remain turn-local. Repeated reference can use bounded recent transcript context tagged as narrated detail. The default is not to extract every noun into an object record. An object, apparent hazard or suspicious gesture becomes consequential when a player tries to acquire/use it, when it supplies evidence or access, or when later reasoning would rely on its existence, ownership, utility or causal effect.

Current implementation already has more than plain transcript memory. `bounded_improvisation.py` has an accepted/promoted ledger with kind, category, epistemic status, turn/scene/session scope, and lexical consequence checks. `incidental_entity.py` binds canonical or bounded incidental **people**, not a generalized cup inventory. `gm.remember_recent_contextual_leads` extracts and merges subjects/positions from emitted prose into runtime history; `_known_fact_from_recent_leads` can later answer from it. `prompt_context` selects a bounded conversational-memory window and derives `recent_log`. `_apply_post_gm_updates` promotes proposals and adopts structured updates. These are possible authority-laundering routes; existing semantic/lexical checks are useful controls, not proof that every promotion is safe.

Practical cup policy for a future continuity lane: retain “a chipped ceramic cup sits beside the innkeeper” as a scene-local narrated detail with transcript provenance, no item ID, value, contents or capabilities. When “I pick up the cup” arrives, admission resolves the reference to that mention, not to an inventory entry. An engine-owned mundane-interaction decision may permit handling a cup in place if scene/ownership/reach permit; it may ask about permission or deny access. This can establish an engine-approved temporary prop/handling fact. Taking it away, selling it, filling it with poison, using it as equipment, or gaining a bonus requires the appropriate inventory/resource/action resolver and separately approved object properties. A cup need not be pre-authored, but mention alone awards nothing.

If that authority pathway cannot represent the action, retain the reference and give a bounded unresolved response; do not pretend possession occurred or erase the earlier mention. Consequential promotion requires a validated engine decision (or explicit GM authoring approval), source link, scope and supported properties. Do not automatically promote E because the player repeats it. Consistent reference to a remembered cup is possible without awarding inventory. Scene departure expires incidental continuity unless independently adopted. PR49 will implement none of this memory machinery: it previews text only, stores provenance in evidence, and disables all adoption/extraction paths.

## 6. Architecture A — Controlled renderer

PR47 structurally excludes arbitrary selector prose: enum-only schema, detached immutable view, engine composition, exact facts, deterministic fallback. Useful for currency/inventory transactions, HP changes, conditions, resource spending, explicit quest transitions and outcome summaries. No semantic classifier is needed to constrain the selector's vocabulary. Safety still depends on correct engine/public input and trusted authored strings.

Its eight controls and three recognizable families demonstrate why a universal template expansion is poor value. It cannot supply flexible character voice or surprising but coherent descriptive connections; extended forms often delay the same result. Keep it unchanged as baseline and as strict profile option. A strict outcome need not spend a provider call choosing enums.

## 7. Architecture B — Anchored free-form narration

An anchor is an engine-created record `{id, source, status, text, epistemic_status, order}` derived from an existing result, not AI-authored JSON. `text` is an immutable display sentence. C paraphrase can be faithful but proving equivalence for all constructions is the same semantic problem; PR49 therefore inserts the original sentence verbatim. The model cannot select a subset or edit qualifiers. IDs/order are engine-local, with stale/unknown references rejected if references are ever introduced.

Anchors alone guarantee **presence**, not consistency. “The patrol took the northwest track. Actually it went southeast” contains a complete anchor and a contradiction. “You pocket a reward” after an accurate discovery invents a consequence. “Only two soldiers left those prints” defeats an uncertain clue without changing its bytes. Secret names can be invented or leaked through mislabeled memory. Free text cannot inherit a mechanical-safety guarantee from adjacent trusted text.

Project hidden inputs away; assemble anchors outside model output; reject malformed shapes and recognized forbidden assertions; reject the complete generated field on semantic failure and use deterministic narration. No automatic retries or arbitrary sentence deletion. Unknown semantic violations remain unknown. Universal anchored free form is not selected because it exposes strict transactions and combat to unnecessary risk and still needs profile-specific restrictions in practice.

## 8. Architecture C — Selected hybrid

Use engine control where outcomes require it and free realization where it adds value. Final text consists of engine-owned facts and separately generated descriptive material, with their provenance retained in diagnostics even if presented as a cohesive paragraph. Strict mechanics never becomes a generated claim schema. Narrative generation receives detached, minimal authorized inputs and has no state-write tools or normal GM-proposal adapter.

A small profile selector depends on resolved action class, disclosure/speaker authority and risk, not on words such as “notice board” or a scenario ID. Most restrictive applicable profile wins; combat injury plus dialogue stays strict. Unresolved/unknown authority falls back to strict existing host text. Travel uses strict destination/no-transition and effect anchors, with optional atmospheric realization later. Failed actions keep engine-owned failure/no-success text and allow no inferred rewards or new exits. Discovery anchors may describe uncertainty even on successful investigation.

This yields expressive freedom in sentence rhythm, sensory focus, descriptive connections and low-stakes personality beyond enum selection. It does not prove the model will use that freedom well. Explicitly reject the false choice of either unrestricted prose safety or a universal template. State capability isolation and candid semantic limits permit a controlled offline comparison.

## 9. Four profiles

Three could merge discovery and conversation, but that hides speaker-knowledge/attribution obligations. Two would hide disclosure completeness. Four keep distinct authorities visible without a policy per action. Shared validation, transport, assembly and fallback remain one pipeline.

| Profile | Use and creative freedom | Required anchors / prohibited assertions | Incidental invention and retention | Checks / fallback |
|---|---|---|---|---|
| Strict mechanical | Transactions, injury/healing/conditions/resources/quests, resolved or failed travel, high-stakes mixed actions. Engine outcome sentence; optional later descriptive action field. | Exact supported effects/status/destination. No extra gains, totals, immunity, arrival, success or status changes. | No new usable objects/hazards; compatible movement/texture only. No prose-derived state. | Typed effects/coverage structurally checked; free description still heuristic. Existing controlled/host outcome on any failure. |
| Anchored discovery | Investigation/knowledge/partial observation. Free action prelude and pacing. | Every selected disclosure, exact qualification and failure/known status as applicable. No new clue, count, identity, causality, quest or reward. | Sensory framing without evidentiary features. Transcript only; clue persistence by resolver. | Exact anchor coverage + schema; whole assembled text existing validation + offline review. Complete deterministic discovery fallback. |
| Conversational | Casual NPC exchange or authorized information dialogue. Flexible voice/manner, within existing personality/knowledge. | Existing selected speech/disclosure, grounded speaker and uncertainty. Social mechanical effects force strict. No secrets, invented commitments, facts or relationship grants. | Low-stakes opinions/gestures; claim provenance, no canonical promotion. | Speaker/knowledge authority + attribution checks; semantic truth unresolved. Existing authorized host speech/failure text. |
| Atmospheric | Low-stakes exploration/scene descriptions with no mechanics/discovery owed. Greatest freedom within known scene. | Public context must remain consistent; any owed result escalates profile. No routes, threat removal, clue/hazard/resource establishment. | Compatible local color or mundane props, ephemeral; interacting triggers separate engine decision. | Projected input, schema, semantic guardrails, offline review. Existing public description fallback. |

## 10. Canonical five-turn comparison

Historical results/baselines below come from PR43 `live_result.json`. Full unabridged original responses, engine records, state before/after and usage are retained in `historical_extract.json`. Every controlled/hybrid example below is illustrative unless explicitly identified as retained PR47 output. PR47 only supports investigations; **it has no implemented renderer for T1/T2/T4**. Their A examples describe possible engine composition, not tested PR47 coverage.

### T1 — “What is available here?”

Actual: `conversational_answer`, no authoritative mutation, scene `frontier_gate`, turn/time_pressure remain 1. Authorized: Cinderwatch Gate District public scene, notice board, serjeant, runner, authored exits Enter Cinderwatch / Follow the missing patrol rumor. Hidden: unselected clue contents, private motives, faction agendas, locked exits. Profile atmospheric with mandatory public affordance coverage for this question.

Historical deterministic baseline begins “You are at Cinderwatch Gate District…” and lists interests/exits, then repeats the opening in full. A illustrative: “At Cinderwatch Gate District: Notice board. Known exits: Enter Cinderwatch; Follow the missing patrol rumor.” Hybrid illustrative: “Rain and the press of traffic crowd the gate. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A tavern runner trades hot stew and rumors near the rain barrel. Known exits: Enter Cinderwatch; Follow the missing patrol rumor.”

Risks: claiming a move occurred, opening a new route, inventing a vendor inventory, converting the watching figure into a named spy. Freedom is high in scene focus/rhythm, but public options cannot disappear behind atmosphere. No claim that illustrative brevity preserves every detail in the historical answer; full mandatory public subset must be selected by the engine for any implementation.

### T2 — “Have you heard any interesting rumors lately?”

Actual: social `question`, `tavern_runner`, `patrol_rumor`, success without check, `muddy_footprints_northwest` plus existing minimum exit lead `minlead_exit_frontier_gate_old_milestone`; no new exit. Turn/time_pressure become 2. Authorized hearsay: “The runner heard the patrol vanished near muddy footprints northwest of the crates.” Hidden: actual perpetrators, reliability/motive internals and off-screen pressure event. Profile conversational with authorized hearsay anchor.

Historical baseline: `Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."` A illustrative uses that same engine sentence. Hybrid illustrative: `The Tavern Runner pauses between calls for hot stew. "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."` Hearsay remains hearsay; no claim of a route being newly unlocked. Gesture is incidental, not recorded behavior/personality history.

Risks: authoritative confirmation instead of rumor, knowledge of a culprit, bribe payment, trust/allegiance grant. Freedom is dialogue delivery and personality, bounded by speaker authority. The generic `revealed_information` helper must not be assumed to cover this social kind.

### T3 — “I examine the notice board.”

Actual: exploration success, `notice_board`, new `notice_patrol_route`, no skill check; turn/time_pressure 3, same scene. Authorized anchor: “The missing patrol was last seen taking the northwest mud track past the crates.” Hidden: all unselected clues, future destination revelations, private ticks/motives. Profile anchored discovery.

Historical baseline: “You examine the notice board, and you turn up a concrete clue.” This is incomplete and is not the proposed fallback. Repaired PR44 baseline: “You examine the notice board. The missing patrol was last seen taking the northwest mud track past the crates.” Retained PR47 concise example: “You examine the evidence. The missing patrol was last seen taking the northwest mud track past the crates.” Hybrid illustrative: “Taxes and curfew rules compete for your attention; you focus on the missing patrol warning. The missing patrol was last seen taking the northwest mud track past the crates.”

Risks: a reward attached to the notice, exact patrol fate, added secret writing or a southeast contradiction. Free descriptive prelude can improve focus and naturalness, but inventing evidentiary features is prohibited. Anchor assembly structurally repairs the historical omission.

### T4 — “I want to follow the trail connected to the missing patrol.”

Actual: deterministic travel, authored exit `leave_for_follow_the_missing_patrol_rumor`, origin `frontier_gate`, destination `old_milestone`, successful resolved transition; turn/time_pressure 4. Authorized arrival at Old Milestone. Previously learned clue remains known. Hidden: undiscovered prints interpretation, en-route encounters, faction operations/private agendas. Profile strict mechanical, future optional journey atmosphere.

Historical baseline and A illustrative: “You arrive at Old Milestone.” Hybrid illustrative: “You leave the gate traffic behind. You arrive at Old Milestone.” The connective refers to the established origin; it does not invent travel duration or hazards.

Risks: extra time/resource spending, injury, free encounter loot, claiming tracking identified a culprit or unlocking another route. Expressive room exists but destination and actual completion belong to the engine. No narration should reinterpret the internal summary as a conversation with the runner.

### T5 — “I examine the footprints.”

Actual: exploration success at `old_milestone`, target `prints`, `milestone_mud_prints`, no skill check; turn/time_pressure 5. Authorized anchor: “Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.” Hidden: any true count/origin/direction, unselected clues and off-screen operation completions. Profile anchored discovery with uncertainty.

Historical baseline: “You inspect prints. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.” A illustrative: “You examine the evidence. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.” Hybrid illustrative: “Your attention settles on the marks in the mud. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.”

Risks: confident direction/count, “fresh military boots”, guaranteed trail-following success or quest completion. A successful discovery can deliver uncertainty; it does not establish a successful deduction. Freedom is narrower than T1 because descriptive adjectives can themselves become evidence.

Across all turns HP stays 8/8 and inventory stays spellbook. Other clocks remain zero; faction ticks occur privately and do not become narration permissions. Four mechanical resolver calls and zero gameplay AI narration calls explain why live mechanical success gives no evidence of expressive-model performance.

## 11. Eight unfamiliar scenarios

These fixtures are synthetic design comparisons, not canonical campaign events or executed benchmarks. Ratings are qualitative; complexity means incremental integration work. Shared fallback rule: retain the successful engine action, discard all generated prose on recognized failure, assemble engine facts, no retry.

| Scenario / authoritative fixture | A: controlled | B: anchored free form | C: hybrid; persistence/failure/complexity |
|---|---|---|---|
| Merchant buys cloak; -5 coins, +1 cloak, no bonus | High mechanical safety/completeness; low expressive flexibility, serviceable naturalness. | Exact transaction complete but surrounding “a ruby too” unsafe; natural dialogue/free range high. | Strict result; optional harmless merchant gesture later. Only engine deltas persist once. Reject bonus and keep transaction fallback. Low strict-profile work; full trade subsystem excluded. |
| Combat injury; engine -3 HP | Clear damage; limited action imagery. | Anchor protects amount's presence, not “the pain fades and you're unharmed.” | Strict damage with optional non-causal motion description, no extra bleeding condition. Combat owns HP. Fallback never reapply damage. Medium later integration due actor/time alignment. |
| Failed travel; no transition, no authorized extra costs | Deterministic blocked result natural enough but repetitive. | Flexible journey prose easily implies arrival/new detour. | Strict failure anchor plus atmospheric field only later. Persist no location change; do not imply zero engine tick unless recorded. Reject arrival; medium integration, existing admission retained. |
| NPC casual conversation; no disclosed quest fact/effect | Safe but stiff repeated voice. | Best naturalness/range; fabricated history/commitments possible. | Conversational voice, no privileged lore; gesture ephemeral. Host reply fallback, no memory promotion. Medium/high speaker-authority work deferred. |
| NPC uncertainty/deception; authorized “I heard the bridge may be unsafe”, actual safety withheld | Strong exact attribution, weak personality. | May turn rumor into fact or tell player NPC is lying. | Conversational source/uncertainty anchor, no hidden motive input. Retain attributed claim only. Reject truth upgrade; high semantic difficulty, deferred. |
| Partial clue; “a mark resembles a crest, identity unclear” | Complete uncertainty, little sensory range. | Rich description may name house/confirm crest. | Anchored discovery; framing may describe attention, not new evidence. Resolver clue persists; candidate prose does not. Fallback exact qualifier. Medium work, useful offline PR49 fixture. |
| Mundane room exploration; public room, no hidden result owed | Overconstrains texture; safe/comprehensible. | Natural, flexible; may create valuable objects, hazards or exits. | Atmospheric profile permits low-stakes local detail, no mechanical grant; no automatic state record. Fallback public description. Medium semantic risk; not in first slice. |
| Interact with previously narrated cup; no inventory authority | Cannot represent arbitrary prior object using enums alone. | Can falsely award cup, gold value or potion. | Resolve mention separately, engine adjudicates handling/acquisition. Reference survives as narration provenance; properties require authority. If unsupported, unresolved host response. High continuity integration; explicitly excluded from PR49. |

Hybrid has a meaningful advantage: it retains A for consequence-heavy cases while permitting B's naturalness where useful. It does not make ambiguous speculation easier to classify. No scenario name or item-specific rule is proposed.

## 12. Adversarial corpus and findings

`adversarial_corpus.json` and `.md` contain at least 30 hand-authored cases, each with profile, authorized outcome, candidate, expected handling, reasoning and enforcement status. These are **expectations, not measured classifier results**. Cases distinguish rejected schema capabilities from ordinary English claims that evade structural checks. Ambiguity, harmless figurative language and previously mentioned objects are retained, not relabelled to inflate safety.

The key finding is architectural: arbitrary strings can contradict anchors, imply new possessions, leak secrets, upgrade suspicion to fact or claim social authority without update fields. Schema validates shape only; input isolation reduces disclosure opportunity but cannot prevent guessing. Existing recognizers remain defense in depth, with PR46's residuals carried forward. No claimed precision/recall for the proposed system and no synonym expansion. An offline human reviewer must treat a missed harmful claim as a missed harmful claim, even if state remains unchanged.

## 13. Failure handling

| Failure | Handling and diagnostic |
|---|---|
| Missing anchor in AI output | Not requested from model; engine assembles all selected anchors. Missing engine anchor/invalid selection aborts preview to existing deterministic source response, flag adapter/coverage error. |
| Contradiction or invented consequence | Existing checks may detect; reject entire generated field on detection or reviewer finding. Render exact engine result, retain raw candidate/reason. Unknown phrasing remains unresolved; no silent guarantee. |
| Hidden information | Never supply hidden catalog; reject known canary/leak, record projected input provenance. Reviewer flags guessed/mislabeled disclosures. No attempt to erase leaked information after display can undo it. |
| Consequential world fact / uncertainty upgrade | Reject complete generated field when recognized; exact discovery/status fallback. Never promote candidate to fact or use it as resolver evidence. |
| Malformed JSON, extra fields, duplicate keys, wrong type, oversized input | Structural rejection before text assembly. No coercion, no extracted “best” sentence. |
| Timeout, exception, empty/whitespace output | One attempt only; deterministic outcome/discovery response, exception class/elapsed stage. No provider retry. |
| Mixed valid/invalid field | Reject generated field as a whole. Engine anchors remain independently valid. No arbitrary sentence surgery or provider rewrite. |

Partial acceptance means accepting **engine-owned anchors independently of a rejected descriptive field**, never selecting apparently safe sentences from an untrusted paragraph. Final exact-once anchor coverage and immutable sealing follow whole-candidate checks. Fallback is derived from the same saved result, not re-resolution. Narration failure cannot undo or repeat committed mechanics. Offline preview diagnostics store action/resolution reference, profile, authorized input hash, anchor IDs/text hash, candidate, schema/semantic verdicts, review status, assembly/fallback source, latency and zero-transport status. Diagnostics are review evidence, not player-facing facts or future campaign memory.

## 14. Source-level implementation map

| Boundary | Reuse / minimal proposed change for PR49 |
|---|---|
| Action authority | Existing exploration result and discovery runtime unchanged. Read saved successful INSPECT result only, with full exact selected disclosure list. |
| Profile selection | New `game/anchored_investigation_preview.py` supports one `anchored_discovery` profile only. All other kinds, repeated, failed or side-effect-bearing results return ineligible/fallback; do not add routing in api. Broader selector is design only. |
| Authorized envelope | Reuse `project_narration_payload` then build explicit immutable allowlisted view using successful result, selected facts/public target label. Reuse/adapt PR47 `authorize_investigation` concepts without changing its public schema. No duplicated knowledge ledger/effect authority. |
| Anchors | `authorized_information.revealed_information` supplies text; existing source ID plus engine-local sequential anchor IDs, exact order. Full anchor text validated on engine side, not returned by selector. |
| Generated description | New offline protocol/stub taking detached view, returning only `{prelude: string}`. No normal GM parse/update object, provider client, tools or application import. Free text makes meaningful range possible; not an enum expansion. |
| Validation | Local exact schema, size/duplicate-key checks; reuse `mechanical_claims.audit_mechanical_claims` and existing `validate_generated_response` only with full authoritative contract supplied. No fabricated decision IDs to satisfy gates. Human review marks unresolved semantics. |
| Assembly/fallback | Engine prelude + source sentences with fixed order and paragraph boundary. Adapt existing deterministic host text/PR47 fallback; keep required clues in every failure. Reuse existing sealing concept, without fabricating a gameplay-accepted object or calling commit/adoption. |
| Diagnostics | `artifacts/pr_play_49/evaluate.py` (proposed) records raw fixtures/candidates/verdicts and editorial comparisons with PR47. No campaign/session logger. |
| Tests | Proposed `tests/test_pr_play_49_anchored_preview.py` in disposable copied workspace; use existing live-model guard and instrument all relevant sinks. |
| Future production seam | If separately approved later: `api.deterministic_provider_skip_line`, `_build_gpt_narration_from_authoritative_state`, `api_turn_support` finalization, `gm.build_messages` and existing provider-budget admission. Explicit profile gate and complete bypass of `_apply_post_gm_updates`, contextual-lead extraction, discourse claims and improvisation promotion for generated fields. This is NOT PR49 scope. |

Exact current source locations are in `source_map.json` and included source snapshots, so line numbers refer to the reviewed working tree rather than an assumed clean commit. Broad orchestrator changes, host-speech replacement and production schema changes are unnecessary for the first experiment.

## 15. Provider cost and latency

Measured historical context: PR43 five requests, 39,804 tokens, 25.47 s provider time; gameplay narration zero. Opening 26,714/1,649 tokens and 15.75 s provider time. Four interpretation calls total 10,612 input /829 output, about 9.72 s provider time. End-to-end gameplay HTTP mean 3.20 s is not a narrator benchmark.

Projected envelopes below are **planning ranges**, not tokenized prompts, prices, measured performance or budget changes. Existing configured limits always win; if a proposed request does not fit, skip generation. No web pricing lookup or dollar estimate is needed; price-independent token formulas avoid assuming current provider rates.

| Architecture | Potential narration dispatch / approximate incremental tokens per eligible turn | Latency and local work |
|---|---|---|
| A controlled | 0 with local/default selector; if AI selector later used, one request, roughly 300–900 input and 60–160 output. | Local schema/render inexpensive (PR47 `evidence_performance.json` gives measured historical Python microbenchmarks). AI enum selection adds a serial network request with limited creative return. |
| B anchored free form | Up to one post-resolution request; roughly 500–1,500 input and 80–250 output, including instructions/public context/exact anchors/schema. | Adds one serial generation after interpretation/resolution, provisionally 1–5 s with an adverse tail bounded only by existing timeout. Larger contexts can exceed this; no deployment promise. Semantic checks do not certify truth. |
| C hybrid | Strict turns 0; selected descriptive turns at most one, same roughly 500–1,500 input and 80–250 output as B; no automatic retries. | Avoids universal generation; local assembly/checks plus eligible-turn network latency. Offline PR49 has 0 actual dispatches, hence 0 provider latency. |

For N eligible free-text turns: projected extra input 500N–1,500N and output 80N–250N; monetary increment = (input × applicable input rate + output × output rate)/1,000,000. N=1 (notice inspection only) adds 580–1,750 total tokens, about 1.5–4.4% of PR43's total, **not** measured savings. N=5 adds 2,900–8,750, about 7.3–22.0%; hybrid should not indiscriminately choose N=5. Prompt/schema bounds for PR49 are byte/field limits, not actual tokenizer measurements. Proposed descriptive output is capped locally; configured provider budgets remain unchanged. Recheck tokenization and admission before any later live trial.

Do not combine interpretation and narration to claim a free call: narration needs the resolved outcome unavailable before interpretation. A pre-resolution draft can predict incorrectly and needs post-resolution verification or replacement. No extra judging-model call is proposed. Local semantic auditing has heuristic cost and gaps; full existing context construction can dominate even if assembly is cheap. No new measured latency is asserted in PR48.

## 16. Architecture decision matrix

Scores are design judgments, not test measurements; 5 is best, including simplicity (low implementation complexity), efficiency and low latency. They assume correct public inputs and the boundaries described above. A's safety ratings refer to enum-controlled output; C's state authority can be strong while semantic safety remains lower.

| Criterion | A controlled | B anchored free form | C hybrid | Rationale |
|---|---:|---:|---:|---|
| Mechanical authority | 5 | 3 | 4 | A constrains generated content; B prose can invent results; C isolates state and retains strict paths but descriptive strings can lie. |
| Hidden-information protection | 4 | 3 | 4 | Same projected inputs; A has bounded output, C restricts contexts; none cures mislabeled public facts. |
| Narrative expressiveness | 2 | 5 | 4 | A demonstrated limited families; B broadest; C intentionally limits consequence-heavy contexts. |
| Information completeness | 5 | 5 | 5 | Engine inserts every anchor; all depend on correct source selection. |
| World-state consistency | 5 | 2 | 3 | A permits little invention; free text/continuity can contradict B facts. C caps exposure, no universal semantic proof. |
| Incidental improvisation | 1 | 5 | 4 | A deliberately lacks free text; C permits it in chosen profiles under persistence limits. |
| Implementation simplicity | 5 | 3 | 2 | A exists; B needs anchors/prose checks; C adds small policy choice and explicit adoption isolation. |
| Maintainability | 3 | 2 | 4 | A template growth becomes expensive; B invites regex repairs; C stable responsibilities, though profile drift is a risk. |
| Token efficiency | 5 | 2 | 4 | A can run locally; C skips strict calls; B universal generation costly. |
| Latency | 5 | 2 | 4 | Same call-count distinction; C's eligible free turns still incur B-like latency. |
| Failure recovery | 5 | 4 | 5 | Independent anchors and existing fallback preserve committed effects; C explicitly rejects whole generated field. |
| Existing-code compatibility | 5 | 3 | 4 | A already isolated; C reuses projection/results/host speech, requires bypassing adoption sinks. |
| Eventual live suitability | 2 | 2 | 4 | A lacks desired storytelling; B universal semantics unresolved; C best practical incremental route, subject to gates. |

No aggregate score: simplicity favors A, expressive breadth favors B, pragmatic context choice favors C. Select C for the intended direction. Reject universal A as insufficiently expressive and universal B as exposing every outcome to unnecessary semantic risk. C is not a proof of safe arbitrary prose; that stronger requirement would remain PARTIAL.

## 17. PR-PLAY-49 minimum viable plan

**Exact initial action:** already-resolved successful `INSPECT`, exploration `kind=discover_clue`, `success=true`, selected disclosure nonempty, not already searched, no item/currency/HP/condition/travel/NPC/faction/quest effects. Use saved PR43 T3 as first fixture, plus unfamiliar partial/uncertain successful discovery fixtures. No scenario-ID or notice-board hardcoding. Reject ambiguous/unknown effect shapes rather than treating them as absent. Existing clock/world tick changes stay engine-owned and private; they are neither regenerated nor interpreted as narrator effects.

**Inputs:** original player action; engine result/authority contract; authorized public scene/target wording; all selected exact clue texts and status; relevant already-known public text only when needed. Detached/frozen engine view, no scene catalog, raw world, NPC secrets, tools, provider object or mutable session. Use explicit allowlist after PR45 projection. Maximum public context 4,096 UTF-8 bytes and one descriptive field; if exact required anchors alone exceed a proposed context cap, fallback without truncating them. All limits are experiment design choices, not changed configured provider budgets.

**Anchor format:** engine-owned immutable tuple of `{id: resolution-local ordinal, source: resolved_action, status: newly_revealed, text: exact selected text, epistemic_status: source_preserved}`; source ID/order only from engine. Avoid pretending inferred certainty is authoritative: `source_preserved` means retain the complete text, not classify it automatically. No model-selected references or paraphrase-only delivery in first slice.

**Output:** stub returns JSON object/string with exact sole key `prelude`, nonempty string, <=768 UTF-8 bytes, duplicate keys rejected. Prelude must describe attention/action/compatible public atmosphere only; no new physical evidence, entities, objects, NPC knowledge, route, success, reward or effect. It can vary rhythm, perspective and sensory framing in ways not enumerable in PR47. Engine returns a distinct `NarrationPreview` artifact with text, immutable anchor records, diagnostics and `review_required=true`; never a gameplay `gm` dictionary.

**Assembly:** prelude paragraph followed by exact anchor sentences in engine order. Fixed boundary makes provenance auditable; naturalness is judged on the combined text. Model does not wrap anchors in invented quotation/document form or prepend “but actually” corrections. Do not place untrusted trailing prose after anchors in this slice. A prelude can still contradict them; layout reduces ambiguity, not semantic risk.

**Validation:** hard schema/size/type checks, detached-input integrity, exact-once anchor coverage, no mutation/proposal fields, existing whole-text semantic checks with real source contract. No expanded regex lists. Every offline candidate receives explicit human-authored expected labels and reviewer result, including unknown outcomes. A passing detector is insufficient for acceptance into gameplay. Recognized failures reject full prelude; unresolved semantic review cases block live recommendation. No automatic repair, retries or second judging provider.

**Fallback:** exact complete existing deterministic discovery narration; preserve source uncertainty/all selected texts; zero re-resolution/effect application. Failure can replace descriptive field only because anchors were independently produced; no sentence salvage.

**Offline tests/evaluation:** (1) T3 full saved outcome and T5 uncertainty; (2) unfamiliar generic target, multiple disclosures, partial clue; (3) exclude failed/repeated/side-effect/unknown action types; (4) malformed, duplicate, wrong types, oversized, empty, exception/timeout; (5) unknown fields and attempted scene/world/inventory proposals; (6) nested secret canaries through actual final input; (7) detached input mutation attempt; (8) instrument state/world/scene/inventory/lead/promotion/discourse sinks and assert no calls; compare all source/data fixtures before/after; (9) preserve anchors in fallback and exact final text; (10) run 30+ adversarial candidates with expected vs actual decisions, explicitly retaining misses; (11) ten fixed-outcome free-text candidates versus PR47, score information/mechanics separately from naturalness/range/continuity. Target at least six recognizably different sentence structures across ten illustrative candidates without accepting harmful labels; this is an offline expressive-capacity criterion, not proof of model variety. Stubbed variants demonstrate allowed surface only. No demand to widen templates if target fails.

**Stop:** package that comparison and tests. If free text adds little quality, keep baseline; if semantics remain unsafe, document misses and recommend no live dispatch. Do not implement other profiles, generalized cup memory, social deception, combat, travel, production transport, API integration, configuration/model/budget changes, automated activation, generalized fact promotion or a renderer migration.

## 18. Decision gates and live readiness

| Gate | Current decision evidence / PR49 exit requirement |
|---|---|
| Engine-controlled outcomes | Existing resolver authority confirmed; PR49 must show no state references/capabilities and no calls to any adoption sink. |
| Reliable discoveries | Exact source assembly design; PR49 tests all selected texts/qualifiers including failure fallback. |
| Hidden inputs excluded | Reuse PR45 plus explicit experiment allowlist/canaries; author misclassification and model guessing remain risks. |
| No prose-to-state writes | Separate preview type, no GM adapter; sink instrumentation required, including remembered leads/discourse. |
| Incidental persistence | Transcript provenance only in offline preview; future action requires engine promotion. No memory subsystem needed for first slice. |
| Meaningful freedom | Free string surface offers more capacity; quality is **unproven**, PR49 comparison required. |
| Failure preserves gameplay | Independent anchors/fallback design; no re-resolution, retries or effects. Verify offline. |
| Bounded provider cost | Zero PR49 transport; later one optional post-resolution call within existing admission/timeout, actual tokenizer check required. |
| Narrow independent test | One successful no-side-effect investigation preview. No production integration. |
| Semantic risks acknowledged | No unrestricted prose theorem; heuristic misses retained. Human offline review required. |

**No live-provider experiment is recommended now.** The smallest missing investigation is the PR49 offline prelude-and-anchor preview, its adversarial semantic review and expressive comparison. Even after implementation, live readiness needs explicit review of semantic misses, demonstrated improvement, final allowlisted payload/token count, state-sink isolation and a separately authorized opt-in transport experiment. If zero unsupported player-facing claims must be guaranteed for all possible English, the free-text profile cannot meet that standard; use the controlled baseline for that deployment requirement.

## 19. Risks, limitations and verification scope

Free prose may lie without mutating state; a disclaimer cannot restore player trust. A correct clue beside a false consequence still misleads. Invented weather can contradict a sealed room; an incidental cup can become an unintended clue; a speculative NPC line can reveal a secret by implication. Historical/public prose and contextual-lead retrieval can launder claims. Existing projection uses structural allowlists/private filtering but trusts public authoring. Exact anchors can sound pasted in or repeat faithful paraphrases. Extra post-resolution calls add latency and cost. Profile proliferation, over-conservative rejection and full-context prompt overhead are maintenance risks.

No complete architecture, renderer rewrite, phrase dictionary, generalized memory, provider adapter, gameplay run or campaign edit is implemented here. No app regression suite is rerun for a documentation/evidence-only pass: some existing tests write evidence, and rerunning them in-place would threaten retained artifacts. Historical 23 failing tests are not claimed fixed or revalidated. Fresh checks verify report coverage/corpus fields, source existence/locations, raw extraction, unchanged protected files, archive CRC and manifest hashes. `verification.json` reports actual results. Standard-library packaging code sets `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` before any potential application import; it imports no application or provider modules.

## 20. Packaging, preferred architecture and final verdict

Preferred architecture: hybrid authority-bounded narration. Final verdict: **A — PASS for PR48's design/evidence mission**, with **live readiness deferred**. Authority taxonomy, persistence decisions, four profiles, five recorded turns, eight unfamiliar scenarios, adversarial expectations, failure behavior, source map and narrow PR49 plan are complete. This verdict is not a safety certification of generated prose.

`handoff/CURRENT_REVIEW.zip` is the established stable archive; a timestamped sibling is preserved. The prior CURRENT_REVIEW report/archive are copied locally under `predecessor/` before replacement; older evidence is unchanged. This archive contains this report, corpus, historical extraction, selected raw evidence, reviewed source snapshots, constraints/provider-use record, source map and SHA-256 manifest. Archive verification is recorded separately alongside it to avoid self-referential hashes. Full historical raw campaign stores remain at their retained repository paths; inventory/hash records identify sources. No push or PR49 work follows packaging.

Recommended next step: review this decision, then separately authorize PR49's offline discovery preview if desired. Stop here.
