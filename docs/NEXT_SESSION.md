# NEXT_SESSION

Start here:

```text
Read docs/DEVELOPMENT_CONSTITUTION.md, then docs/NEXT_SESSION.md and the
authoritative documents it identifies, before beginning substantive work.
```

## Project

Ashen Thrones

## Current Era

Product Realization

## Last Completed Cycle

`PR-BJ — AI Experience: Speaker Attribution Integrity and Lane Convergence Audit`

## Current Objective

The PR-AS through PR-BJ sibling-defect sequence is closed. `"The guard says"` does not reproduce as a player-facing semantic defect. Do not open another ordinary-play authority or paraphrase micro-cycle. Return to playtesting or to a gameplay capability.

## Established Facts

- Architecture Reconciliation Era completed; Campaign 6 chassis closed.
- Repository organization completed. Campaign reports live under
  `development/campaigns/`. Generated evidence stays in `artifacts/`.
  Disposable pytest/agent output goes to `development/tmp/`.
- Validation authority hierarchy is unchanged: structural PASS ≠ semantic
  playability; semantic calibration is the primary calibrated semantic
  authority.
- RC-10 = A and RC-21 = B + C remain implemented.
- PR-AD through PR-BJ remain as previously established. Do not reopen them
  without new causal evidence.
- PR-AQ remains settled: T16 walk+listen is existing `observe`; local walking
  is existing `custom`; listen is perception, not sound creation.
- PR-AR remains settled: visual presence ≠ speech; empty listen is valid
  grounded absence; perception may realize the world, not author it.
- PR-AS remains settled: authority determines what may be said; relevance
  determines what should be said now. Immediate untargeted reinspection may
  remain nothing-new. Existing observe fallback is still the owner.
- PR-AT remains settled: an `already_searched` outcome must realize a complete
  authored inspectable sentence. Repeated investigation does not mint a new
  discovery.
- PR-AU remains settled: a grounded social absence must survive live-model
  realization. Price, time, count, identity, and unauthorized-redirect
  inventions shared one realization failure. Existing authored-knowledge
  realization fail-closes invented concrete facts into the ownership-terminal
  catalog.
- PR-AV remains settled: a contextual refusal hook must refer to a meaningful
  asked subject. Movement, temporal, speaker, and other incidental leftovers
  are not topics. Empty/untrustworthy topic degrades to an unhooked refusal.
- PR-AW remains settled: intervening non-observation turns do not make
  unchanged visible facts newly relevant. Untargeted visual observe is the
  only stamp-eligible turn.
- PR-AX remains settled: off-scene known clues are historical, not
  present-here spatial authority. Distinctive prior-scene geography asserted
  as currently present fail-closes through existing perception grounding.
- PR-AY remains settled: a request to perceive/describe the player's
  authoritative current surroundings is existing `observe`, even when phrased
  as a question. Adjudication remains the owner of earshot, who/anyone nearby,
  distance, rules, and feasibility.
- PR-AZ remains settled: once an utterance is resolved and executed as
  observe, interrogative surface form must not transfer it to
  social/adjudication. Sole-NPC information-seeking bind must not attach
  untargeted local observation. `question_rule` remains valid and was not
  globally disabled.
- PR-BA remains settled: grammatical locality terms do not determine
  ownership alone. Subject + requested relation matter. Undirected
  place-existence is current-scene / current-exit adjudication.
- PR-BB remains settled: the leftover passive standpoint sentence is not a
  missing observation category. Ordinary look-around already reached observe.
  The local-observation classifier is converged enough for Product
  Realization.
- PR-BC remains settled: directed vocative / `ask X who …` stay social.
  Undirected `"Who last read the tally slate?"` remains accepted inspect
  residue. No last-reader fact was added.
- PR-BD remains settled: ordinary interactable names, aliases, and silent-e
  plurals resolve. `"posted notices"` remains accepted leading-modifier
  residue.
- PR-BE found no authoritative waiting / pass-time owner. Ordinary
  `"I wait."`, `"I wait a moment."`, and `"I pause for a moment."` resolve
  `kind=None` because the gameplay capability is absent.
- Nearby owners are not wait: `explicit_stay` is remain-here → `observe`;
  `passive_interruption_wait` is wait-out-a-disturbance → `observe`; `custom`
  is local walking/pacing and does not advance diegetic time; downtime/rest
  is `downtime_engine_not_wired`.
- `session.turn_counter` and `session.clocks.time_pressure` increment on
  every chat, including unparsed wait. `session.current_date` stays
  `"Day 1"`. Canonical `world.world_state.clocks` is empty. Those are not
  a wait-owned time system.
- `"I step back and wait."` fails because both clauses fail independently.
  `"I step back."` is outside the PR-AQ local-movement regex. Compound
  N-action execution remains deferred.
- `"I wait for the guard to leave."` leftover-matches travel on the word
  `leave`. That is not a wait owner.
- PR-BF recovered PR-AJ T6: `"I'll go chase that closed western cart road
  you mentioned."` parsed as unresolved `travel`. State stayed
  `frontier_gate`. Historical narration implied departure via scene-like
  stock and `"You set off."`
- PR-BF's first incorrect decision was realization treating travel *kind*
  as travel-success eligibility. The success signal is
  `resolved_transition is True` (or an equivalent scene-transition
  state-change flag).
- Destination-arrival and scene-emit integrity may emit scene stock after
  travel only when that success signal is present. Unresolved travel uses
  existing fail-closed terminals.
- PR-BG recovered PR-AI T2 `"What are you doing about the missing patrol?"`
  after a Thoran / watch-command answer as a topic switch, not lost
  continuity. The captain has no covering owned topic or landed clue.
- PR-BG's reproduced defect was recognized empty-subject follow-ups
  (`"Why is that?"`, `"How come?"`, `"Who is that?"`) losing
  `topic_pressure` last-answer because cover required leftover tokens and
  `normalize_topic` minted a new key.
- PR-BG repair: `is_valid_followup_question` plus empty subject tokens may
  reuse the current last-answer when speaker and dimension allow.
  `"Who is he?"` keeps the current topic-pressure key. `they` / `it` do
  not become last-answer authority.
- `"Why was it shut down?"`, `"Why did that happen?"`, `"Who did it?"`,
  and `"Where did they go?"` remain deferred richer discourse / synonym
  residue. Cause asks against facts that do not encode cause stay
  fail-closed.
- PR-BH recovered PR-AI T12 `"I turn to the Gate Serjeant. …"` binding
  `gate_guard` and voicing `watch_command`. `"Gate Serjeant"` is not an
  authored identity of `gate_guard`. The fixture authors a distinct
  `gate_serjeant` with aliases `serjeant` / `gate serjeant` and topic
  `route_change`.
- PR-BH's first incorrect decision was directed-prep first-roster short-
  token match (`gate` inside `to the Gate Serjeant`) without requiring
  leftover identity words to belong to that NPC. Sole-NPC information-
  seeking then cooperated for unresolved explicit addressees. Vocative
  `captain` was hardcoded as `guard`.
- PR-BH repair: an explicit addressee binds only when authored
  id/name/alias/role tokens cover the phrase. An unresolved explicit
  addressee is not the sole present NPC. Ordinary unique roles, aliases,
  and undirected sole-NPC questions remain.
- PR-BI recovered the repeated-interruption fixture. Turn 3 spoke the
  model cutoff as `Tavern Runner mutters, "Word is, the runner begins to respond..."`.
  The runner was addressed. The cutoff was not an answer.
- PR-BI's first incorrect decision was `_commit_topic_progress` storing
  interruption-breakoff narration as `topic_pressure.last_answer`.
  Realization then treated that last_answer as a structured fact.
  Overlap on `noise` in `ignore the noise` made the cutoff look relevant.
- PR-BI repair: a cutoff is not written as `last_answer` and is not
  selected as a structured fact. The owned patrol sentence stays eligible.
- Forced progression means the same interruption signature on the same
  NPC, repeat count at least 2, then a different strict-social line.
  The fixture never reached that threshold.
- Opening `I look around the gate.` no longer keeps `Gate Guard mutters`.
  Perception grounding replaces that speech with visible stock. A real
  watch-command question may still wrap the owned Thoran sentence in
  `Word is`. That envelope is aesthetic.
- PR-BJ recovered PR-AH T11: `"I look for signs of the patrol."` at
  `old_milestone`, no NPC present, historically
  `The guard says, "I do not know enough to answer that."`
- PR-BJ's current reproduction of that turn is `investigate` with no
  speaker and visible milestone stock. A model line that says
  `The guard says` is replaced by that stock.
- `speaker_label` / `npc_display_name_for_emission` in
  `game/social_exchange_policy.py` prefer authored `npc_name`, then a
  title-cased id, then the literal `The guard` when both are absent.
  The fallback catalog interpolates that label. It does not read `role`.
- Live no-speaker social turns use
  `neutral_reply_speaker_grounding_bridge_line`. Authorized speakers
  in the probe kept `Gate Serjeant`, `Guard Captain`, `Gate Guard`,
  and `Ward Sentry`. `secret_warden` was not shown.
- `"The guard says"` did not reach the player on the recovered turn or
  the identity matrix. The empty-identity helper string remains latent
  compatibility behind those owners.
- Speaker attribution is sufficiently converged. The PR-AS through
  PR-BJ sibling-defect sequence is closed.

## Decisions Pending

None. No user decision is required before the next slice.

## Decisions Made

- RC-10 = A. Evidence-only raw-token fence.
- RC-21 = B + C. Authored-scene follow-up plus canonical lead registry.
- PR-AC through PR-BJ decisions remain as previously recorded.
- PR-BE: ordinary simple waiting is a missing gameplay capability (C), not
  a routing defect (A), not a `custom` typing defect (B), and not accepted
  paraphrase residue around a working family (D).
- PR-BE: do not repair `kind=None` by recognizing `wait`, aliasing stay /
  rest / observe / listen / travel, inventing duration, or asking the LLM
  to narrate that time passed.
- PR-BE: no production code change. A future wait/time-passage feature
  needs an explicit unit, state-before-narration, and a quiet no-event
  contract. Duration, target-time, and conditional waiting are separate
  later capabilities.
- PR-BF: narration must not imply a spatial transition that authoritative
  gameplay state did not perform.
- PR-BF: travel kind is not a success signal. Scene stock is not eligible
  for travel narration unless `resolved_transition` (or an equivalent
  transition flag) is true.
- PR-BF: do not add a destination, route, travel duration, geography
  database, or second travel router to make unresolved travel feel
  successful.
- PR-BG: a recognized empty-subject immediate follow-up may continue the
  current last-answer thread. Noun-bearing questions still need overlap.
- PR-BG: do not add synonyms, embeddings, a discourse model, or a second
  topic router. Do not treat all pronouns as the last topic.
- PR-BG: ordinary deterministic follow-up continuity is sufficiently
  converged. Stop opening paraphrase cycles on this owner.
- PR-BH: explicit player identity evidence constrains NPC selection.
  Leftover title/name tokens are not optional.
- PR-BH: do not add rank synonym lists, embeddings, LLM identity
  inference, invented NPCs, or a second NPC router.
- PR-BH: addressed-NPC identity resolution is sufficiently converged.
  Stop opening NPC-name/title paraphrase cycles on this owner.
- PR-BI: interruption pressure does not create answer authority. A
  cutoff is not stored or selected as `last_answer`. Do not reopen
  PR-AI for the `Word is` envelope.
- PR-BI: do not delete `Word is`, blacklist `mutters`, or rewrite the
  strict-social forced-progression catalog in a prose cycle.
- PR-BJ: `"The guard says"` does not reproduce as a player-facing
  semantic defect. No production code change.
- PR-BJ: an authorized speaker is displayed from authored `name` or
  title-cased id. A turn with no authorized speaker uses the neutral
  bridge or perception/scene stock. Do not treat the latent helper
  default as a new cycle.
- PR-BJ: speaker attribution is sufficiently converged. The PR-AS
  through PR-BJ sibling-defect sequence is closed. Do not open PR-BK
  for evaluator wording, dialogue tags, or the latent `The guard`
  helper.
- The generalization principle (content may be specific; systems must be
  general) lives in `docs/product_realization_validation.md`.

## Current Known Defects

No remaining ordinary-play AI Experience semantic integrity defect is
recommended as a Product Realization sibling cycle. The PR-AS through
PR-BJ sequence is closed.

Validation residue, not game-behavior cycles:

- Evaluator lexical false negatives on quiet listen and nothing-new lines.
- `test_social_speaker_grounding.py` has two assertions that
  `resolution.success is True` and receive `None`
  (`test_transcript_runner_asks_about_aldric_followup_stays_runner`,
  `test_transcript_where_is_aldric_repeated_followups_stay_runner`).
  The failure hint still names Tavern Runner. Observed during PR-BJ.
  Not absorbed. Not a speaker-label failure.

`test_transcript_runner_repeated_interruption_beat_forces_progression`
passes. Authorized facts may still use the `Word is` / `mutters`
envelope. That wording is accepted aesthetic residue. The empty-identity
`speaker_label` default `The guard` remains latent and did not reach the
player on the PR-BJ chat probe.

A Windows `PermissionError` on shared pytest temp remains environmental.

Unrelated reds observed during PR-AU / PR-AV validation and not absorbed:

- `test_emission_quality_anyone_else_talk_to_manifests_preserves_redirect_not_fragment`
  still expects source `topic_pressure:last_answer:redirect` and receives
  `topic_pressure:last_answer`. Documented since PR-AO.
- `test_final_emission_passive_pressure_restores_recent_suspicious_figure_from_weak_atmosphere`
  failed on an unrelated social-pressure fixture.

## Authoritative Documents

1. `docs/DEVELOPMENT_CONSTITUTION.md`
2. `development/campaigns/product_realization/PR-BJ_speaker_attribution_integrity_lane_convergence_audit.md`
3. `development/campaigns/product_realization/PR-BI_interruption_progression_catalog_residue_reaudit.md`
4. `development/campaigns/product_realization/PR-BH_addressed_npc_identity_resolution_role_title_convergence.md`
5. `development/campaigns/product_realization/PR-BG_followup_topic_continuity_public_clue_paraphrase_convergence.md`
6. `development/campaigns/product_realization/PR-BF_unresolved_travel_narration_authority_scene_stock_integrity.md`
7. `development/campaigns/product_realization/PR-BE_wait_action_ownership_time_passage_capability_audit.md`
8. `development/campaigns/product_realization/PR-BD_interactable_reference_resolution_alias_convergence.md`
9. `development/campaigns/product_realization/PR-BC_agent_history_question_ownership_convergence.md`
10. `development/campaigns/product_realization/PR-BB_local_observation_classifier_boundary_convergence.md`
11. `development/campaigns/product_realization/PR-BA_nearby_place_existence_knowledge_ownership.md`
12. `development/campaigns/product_realization/PR-AZ_question_form_observe_realization_retry_ownership.md`
13. `development/campaigns/product_realization/PR-AY_local_presence_question_adjudication.md`
14. `development/campaigns/product_realization/PR-AX_post_return_observation_geographic_integrity.md`
15. `development/campaigns/product_realization/PR-AW_later_turn_untargeted_observation_restacking.md`
16. `development/campaigns/product_realization/PR-AV_grounded_refusal_topic_hook_integrity.md`
17. `development/campaigns/product_realization/PR-AU_grounded_social_absence_live_model_non_invention.md`
18. `development/campaigns/product_realization/PR-AT_already_searched_truncation.md`
19. `development/campaigns/product_realization/PR-AS_observe_fallback_relevance_stock_repetition.md`
20. `development/campaigns/product_realization/PR-AR_perception_narration_authority_audible_non_invention.md`
21. `development/campaigns/product_realization/PR-AQ_physical_action_typing_compound_perception_realization.md`
22. `docs/product_realization_validation.md`
23. `development/campaigns/product_realization/PR-AH_grounded_observation_non_invention.md`
24. `development/campaigns/product_realization/PR-AJ_authoritative_lead_provenance_social_prose_non_ingestion.md`
25. `development/campaigns/product_realization/PR-AO_investigation_result_provenance_non_invention.md`
26. `development/campaigns/product_realization/PR-AP_grounded_refusal_realization_grammar.md`
27. `development/campaigns/product_realization/PR-AN_question_dimension_answer_sufficiency.md`
28. `development/campaigns/product_realization/PR-AK_referenced_surface_grounding_inspection_resolution.md`
29. `docs/state_authority_model.md`
30. `docs/rc10_rc21_policy_implementation.md`
31. `docs/semantic_validation_calibration.md`
32. `development/campaigns/reconciliation/AR-AD_target_architecture_doctrine.md`
33. `docs/review_handoff_standard.md` (review export only; not this handoff)
34. `development/README.md` (directory taxonomy only)

## Validation Baseline

PR-BJ speaker probe:
`artifacts/prbj_speaker_attribution/probe/20260922T235900Z_probe.md`.
Recovered `old_milestone` investigate no longer emits `"The guard says"`.
Authorized names stay `Gate Serjeant`, `Guard Captain`, `Gate Guard`,
and `Ward Sentry`. No-speaker turns use the neutral bridge or scene stock.

PR-BJ preservation run: 75 passed, 2 failed. Passed:
`tests/test_addressed_npc_identity_resolution_role_title.py`,
`tests/test_perception_narration_authority_audible_non_invention.py`,
`tests/test_grounded_social_absence_live_model_non_invention.py`,
`tests/test_interruption_progression_catalog_residue.py`,
`tests/test_transcript_regression.py::test_transcript_runner_repeated_interruption_beat_forces_progression`,
and the rest of `tests/test_social_speaker_grounding.py`.
The two failures assert `success is True` and receive `None`. Not absorbed.

PR-BI interruption tests:
`tests/test_interruption_progression_catalog_residue.py`.
Fixture:
`tests/test_transcript_regression.py::test_transcript_runner_repeated_interruption_beat_forces_progression`
passes. After-repair trace:
`artifacts/prbi_interruption_progression/fixture_after.json`.
Opening look-around:
`artifacts/prbi_interruption_progression/opening_probe.json`.
The cutoff is not stored as `last_answer`. The owned patrol sentence
remains. Look-around does not keep Gate Guard speech.

PR-BH identity tests:
`tests/test_addressed_npc_identity_resolution_role_title.py`.
After-repair traces:
`artifacts/prbh_addressed_npc_identity/isolation/20260922T120000Z_after.md`.
Recovered Gate Serjeant binds `gate_serjeant`; unsupported Captain/Foreman/Clerk/Aldric stay unbound; ordinary guard/porter aliases and undirected sole-NPC questions remain.

PR-BG continuity tests:
`tests/test_followup_topic_continuity_public_clue_paraphrase.py`.
After-repair traces:
`artifacts/prbg_followup_topic_continuity/20260922T110500Z_after.md`.
Recognized empty-subject follow-ups reuse last-answer; missing-patrol
after watch still refuses; `shut down` / `who did it` remain unsupported;
topic switch and unrelated questions do not inherit.

PR-BF travel-authority tests:
`tests/test_unresolved_travel_narration_authority.py`. After-repair
traces: `artifacts/prbf_unresolved_travel/probe/20260922T103000Z_after.md`.
T6 / unknown dest stay unresolved; mossy pine-trail transitions; local
`step closer` remains `custom`; arrival stock requires a success signal.

PR-BE ownership probe: `artifacts/prbe_wait_action_ownership/probe_matrix.md`.
Ordinary simple wait → `None`. Stay → `observe`. Listen / look-around
preserved. Local `pace` / `step closer` remain `custom`.

PR-BD ownership tests remain passed
(`tests/test_interactable_reference_resolution_alias_convergence.py`).

After-repair matrix
`artifacts/prbd_interactable_reference/probe/20260922T084500Z_after.md`:
canonical / alias / `"the notices"` bind `notice_board`; silent-e plurals
bind hopper/slate/milestone; `"posted notices"` remains visible-feature
residue; incidental, unauthored, and off-scene objects stay unbound.

PR-BF re-ran destination-binding, scene-transition, arrival-realization,
PR-AQ physical-action, PR-AX geographic-integrity, and scene-emit
integrity suites. Those baselines were not weakened. One unresolved
named-place integrity contrast was tightened so it can no longer use
global scene-stock fallback. Do not treat a structural result as
semantic playability.

Authoritative full suite last recorded before later Product Realization
cycles: 6,450 collected, 6,351 passed, 0 failed, 99 skipped
(`artifacts/policy_implementation/post_implementation_suite.xml`).

Remaining known reds are BY3/BY4/BZ mutation-attribution generators,
frontier-gate long-session golden replay from intended player-facing
realization changes, and the unrelated social reds listed above.

## Deliberately Deferred Residue

Leave these deferred unless later evidence elevates them:

- Richer unknown-destination gameplay (routes, durations, NPC guidance).
  Safe unresolved-travel failure is now the correct terminal.
- Intentional waiting / in-place time passage as a future gameplay
  capability. Ordinary `"I wait."` remaining `kind=None` is fail-closed,
  not a recommended parser cycle.
- Duration wait, target-time wait, and conditional / event-driven wait.
- `"I step back."` remaining outside the PR-AQ local-movement regex.
- Comprehensive compound-intent / N-action execution
  (`"I step back and wait."`).
- Rest / camp / downtime engine (`downtime_engine_not_wired`).
- A diegetic world clock / date-time owner. `current_date` is static.
- Accepted `"posted notices"` / `"posted notice"` leading-modifier residue.
  `"I read the notices."` is the working ordinary plural.
- Leading-modifier leftovers (`wooden board`, `public notices`,
  `wooden hopper`, `muddy milestone`).
- `"What do the notices say?"` remaining untargeted; content-question
  recovery still keys on `what does`.
- Accepted undirected who-last-read inspect residue
  (`"Who last read the tally slate?"`, `"Who read the tally slate?"`,
  `"Has anyone read this?"`). Directed equivalents now reach social.
- Object last-reader / last-toucher / provenance / NPC activity history.
  Affirmative answers would need a future gameplay/world-state capability.
- Accepted local-observation residue: actorless passives
  (`"What can be perceived from where I stand?"`, `"What can be seen from
  here?"`), `"What is visible from here?"`, and `"Describe my
  surroundings."`. Working equivalents already reach observe.
- The empty-identity `speaker_label` default `The guard`. It did not
  reach the player on the PR-BJ probe. Do not open a cycle to rename it.
- Sole-runner dialogue where a beat sentence drops and the quote remains.
- `compat_pending_lead_needed` still keys off a scene target only.
- Intent parsing still reads `pending_leads` as the pursuit surface.
- Broader lead/clue overlap reduction (`docs/current_focus.md`).
- `_TEXT_LEAD_SPECS` compatibility text-hook library.
- House Verevin / rooftop invention.
- Remaining scene-transition Unicode / operator-encoding.
- PR-AB tooling / product-integrity concern.
- General prompt rewrite or NPC dialogue redesign.
- `"Word is,"` / `mutters` wording on an already authorized fact.
  That envelope is aesthetic. The repeated-interruption fixture now
  restates the owned fact instead of the cutoff.
- Strict-social forced-progression stock that can mention a ward clerk
  or the main gate when the interruption repeat guard actually fires.
  The repaired fixture never reached that threshold.
- New authoritative knowledge store.
- Project-wide State ↔ Narration campaign.
- Protected-replay baseline refresh.
- Filling other stub scenes (`eastern_square`, `wild_moors`, `alley`, …).
- Broad observation-variety work. Immediate restacking, later-turn restacking,
  post-return geographic bleed, local-presence classification,
  question-form observe retry ownership, nearby place-existence ownership,
  local-observation classifier convergence, agent-history question
  ownership, interactable-reference alias convergence, unresolved
  travel scene-stock integrity, ordinary follow-up topic continuity, and
  addressed-NPC identity resolution are closed. Do not start a seen-facts
  / salience / geography / object-history campaign, another who-read
  paraphrase cycle, another interactable-synonym cycle, a second travel
  router, another follow-up-paraphrase cycle, or another NPC-name/title
  paraphrase cycle.
- Automatically turning mentioned nouns into interactables.
- Adding a roster-board interactable that existing content does not justify.
- Adding a stew price or menu/economy simulation.
- Adding last-reader / board-history facts merely to answer T14.
- Adding patrol timing or personnel merely to answer T15.
- Adding canonical Frontier Gate sounds merely to make listen interesting.
- New conversation-state stack or second global router.
- Coordinate-level local movement or five-senses simulation.
- Deleting `remember_recent_contextual_leads`.
- Flattening all refusals to `"I don't know."`
- Universal grammar checker / prose-rewriting layer.
- New NLP / topic-model subsystem for refusal hooks.
- Fuzzy / embedding / LLM interactable selection.
- Fuzzy / embedding / LLM NPC identity inference or a rank/title ontology.
- Richer follow-up discourse (`Why did that happen?`, `Who did it?`,
  `Where did they go?`) and predicate synonymy (`shut down` vs
  `closed` / `barred`). Ordinary recognized ellipsis is closed.

Do not treat residual lead-system items as open RC-10/RC-21 questions.

## Do Not Reopen Without Evidence

- Validation-authority hierarchy
- RC-11 / RC-13 expectation maintenance
- GD-01 CO99 governance-context advance
- Confirmed baseline repair and validation cleanup
- Semantic calibration as semantic authority
- Protected replay as structural/runtime authority
- Architecture Reconciliation chassis doctrine
- RC-10 = A
- RC-21 = B + C
- Existing state/domain owners
- PR-AD through PR-BJ settled decisions listed in the prior handoff
- PR-AR's visual-presence ≠ speech-authority boundary
- PR-AR's treatment of empty listen as valid grounded absence
- PR-AR's decision not to add a new sound system, perception owner, or
  world-authority owner
- PR-AQ's local-movement ≠ scene-travel boundary
- PR-AQ's treatment of listen as perception attempt, not sound creation
- PR-AS's decision not to add a new observation system, salience engine,
  embeddings, or player-memory / seen-facts subsystem
- PR-AS's refusal to rotate leftover unused stock for variety
- PR-AS's treatment of nothing-new as a valid observation result
- PR-AT's decision not to add a seen-facts store, second router, or model
  padding layer
- PR-AT's treatment of `already_searched` as investigation realization owned
  by referenced-surface / perception fail-closed
- PR-AU's decision not to add a knowledge store, economy, or second social
  router
- PR-AU's treatment of grounded social absence as authored-knowledge
  realization's dual, using the existing ownership-terminal catalog
- PR-AV's decision not to add an NLP/topic-model, embeddings, or a second
  social router
- PR-AV's refusal to hardcode `step`/`night` or grow a replay-word blacklist
- PR-AV's treatment of empty/untrustworthy hooks as unhooked refusals rather
  than flattening all refusals
- PR-AW's decision not to add a seen-facts / salience / embeddings subsystem
- PR-AW's refusal to treat the visible-fact snapshot as consumed-memory
- PR-AW's treatment of social, investigate, and listen as one stamp-overwrite
  owner rather than separate observation systems
- PR-AX's decision not to add a second location/geography system
- PR-AX's refusal to globally clear conversation/history on scene transition
- PR-AX's treatment of off-scene known clues as historical, not present-here
  spatial authority
- PR-AY's decision not to add a nearby/locality subsystem or second
  observation router
- PR-AY's refusal to hardcode `"What's nearby?"` or enumerate paraphrases
- PR-AY's treatment of question-form local presence as existing observe
- PR-AY's refusal to convert all adjudication questions into observe
- PR-AZ's decision not to disable `question_rule` or scene-stall globally
- PR-AZ's refusal to add a conversation-state stack or second router
- PR-AZ's treatment of executed observe as semantically complete
- PR-BA's decision not to add a geography database, building list, or
  place-knowledge subsystem
- PR-BA's refusal to convert every `nearby` question into observe or
  earshot
- PR-BA's treatment of undirected place-existence as current-scene /
  current-exit adjudication
- PR-BA's treatment of executed adjudication as semantically complete
- PR-BB's decision not to support actorless passive perception questions
- PR-BB's refusal to hardcode the leftover standpoint sentence or enumerate
  observation paraphrases
- PR-BB's treatment of `can` + already-known visual perception verbs as
  existing observe
- PR-BB's judgment that the local-observation classifier is sufficiently
  converged
- PR-BC's decision not to add object-history / last-reader tracking
- PR-BC's refusal to hardcode `tally slate`, `read`, or `"who last read"`
- PR-BC's treatment of directed addressee + WH/ask as existing social
- PR-BC's treatment of undirected who-last-read inspect as accepted residue
- PR-BC's judgment that this family is sufficiently converged
- PR-BD's decision not to add a synonym dictionary, embeddings, or
  noun-to-interactable promotion
- PR-BD's refusal to hardcode `posted notices` or special-case `notice_board`
- PR-BD's treatment of authored aliases as the content extension point
- PR-BD's treatment of leading-modifier paraphrases as accepted residue
- PR-BD's judgment that interactable reference resolution is sufficiently
  converged
- PR-BE's decision not to add a wait / pass-time action, world clock,
  duration table, or parser recognition of `wait`
- PR-BE's refusal to alias wait to stay, rest, observe, listen, travel, or
  `custom`
- PR-BE's treatment of ordinary simple wait `kind=None` as missing-capability
  fail-closed, not a recommended Product Realization parser cycle
- PR-BE's refusal to reopen PR-AQ for `"I step back."` or to start
  comprehensive compound-intent execution from `"I step back and wait."`
- PR-BF's decision not to add a travel system, geography database, route
  planner, or destination synonym list
- PR-BF's refusal to treat travel kind as a success signal
- PR-BF's treatment of unresolved travel as ineligible for arrival /
  current-scene stock
- PR-BF's judgment that successful and unsuccessful spatial outcomes are
  now distinct enough for Product Realization
- PR-BG's decision not to add synonyms, embeddings, a discourse model, or
  a second topic router
- PR-BG's refusal to treat all pronouns as the last topic
- PR-BG's treatment of recognized empty-subject follow-ups as current
  last-answer continuation
- PR-BG's treatment of synonym / richer-discourse follow-ups as deferred
- PR-BG's judgment that ordinary deterministic follow-up continuity is
  sufficiently converged
- PR-BH's decision not to add rank synonym lists, embeddings, LLM
  identity inference, invented NPCs, or a second NPC router
- PR-BH's refusal to treat guard/serjeant/captain as interchangeable
- PR-BH's treatment of leftover identity tokens as a bind constraint
- PR-BH's treatment of unresolved explicit addressees as ineligible for
  sole-NPC substitution
- PR-BH's judgment that addressed-NPC identity resolution is
  sufficiently converged
- PR-BI's decision not to reopen PR-AI for the `Word is` envelope
- PR-BI's refusal to delete `Word is`, blacklist `mutters`, or rewrite
  the strict-social forced-progression catalog as a prose cycle
- PR-BI's treatment of an interruption cutoff as ineligible for
  `topic_pressure.last_answer`
- PR-BI's judgment that remaining `Word is` / `mutters` wording on an
  authorized fact is aesthetic
- PR-BJ's decision not to change production code for the latent
  `The guard` helper default
- PR-BJ's refusal to add names, a role synonym table, an
  identity-knowledge store, or LLM speaker inference
- PR-BJ's judgment that speaker attribution is sufficiently converged
- PR-BJ's judgment that the PR-AS through PR-BJ sibling-defect sequence
  is closed
- Repository file-placement taxonomy in the Constitution

## Recommended Next Action

The PR-AS through PR-BJ sibling-defect sequence is closed. Do not open
PR-BK. Do not start another paraphrase, speaker-label, evaluator, or
authority micro-cycle.

Return to Product Realization playtesting of the ordinary gate-and-road
loop, or to a gameplay capability already recorded as missing: wait /
time passage, richer travel, rest / downtime, object history, or a world
clock. Those are feature slices.

Do not reopen PR-BJ speaker display, PR-BI interruption-answer authority,
PR-BH identity resolution, PR-BG follow-up continuity, PR-BF
travel-success eligibility, PR-BE wait/time-passage, PR-BD
interactable-reference convergence, PR-BC agent-history ownership, PR-BB
classifier convergence, PR-BA place-existence ownership, PR-AZ retry
ownership, PR-AY local-observation semantics, PR-AX geographic
eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility,
PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison,
PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or
PR-AI speaker ownership unless new evidence shows a player-facing
semantic break.

No user decision is required. No next sibling-cycle identifier is
assigned.

## Minimum Files for the Next Agent

- `docs/DEVELOPMENT_CONSTITUTION.md`
- `development/README.md`
- `development/campaigns/product_realization/PR-BJ_speaker_attribution_integrity_lane_convergence_audit.md`
- `docs/product_realization_validation.md`
- the design note for whichever gameplay capability or playtest is chosen

## Git / Worktree Caveats

This remains one Git repository. No second repository was created.

The Product Realization checkpoint through PR-AR plus repository
organization remains committed on `feature/product-realization` (`4c0a454`).
PR-AS through PR-BJ production, tests, artifacts, reports, and this handoff
are uncommitted. Do not commit or push unless explicitly asked.

The PR-BE probe did not reset canonical `data/` documents.
`data/scenes/old_milestone.json` remains intentional PR-AF destination
content.

Future pytest/agent scratch goes to `development/tmp/` and is Git-ignored.

## Last Updated

2026-09-22 / PR-BJ speaker attribution integrity and lane convergence audit
