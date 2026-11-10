# PR-PLAY-38 — Five-Turn Live Gameplay Validation

Date: 2026-11-01
Identifier: `pr_play_38`
Run: `20261102T021036Z-943166c96646`

# 1. Executive Summary

The isolated live campaign started. The provider opening was semantically rejected and the deterministic opening recovery completed initialization with one provider request. Five prescribed player lines were then submitted, each returned HTTP 200, and none was retried.

Only the first gameplay exchange answered the player. It listed the gate's public offerings from host evidence and did not mutate inventory, quests, location, or clocks. The next four exchanges stopped in clarification. No gameplay turn invoked the mechanical resolver or a narration provider call. Rumors were not delivered, footprints were not investigated, and the party never left Cinderwatch Gate.

Authoritative location, character, clocks, and turn counter stayed at the post-opening values through turn 5. The user campaign fingerprint was unchanged. Gameplay source hashes did not drift during the run.

Final verdict: **C — FAIL**. Initialization and recovery worked. Ordinary play did not.

# 2. Experimental Configuration

| Item | Value |
| --- | --- |
| Repository revision | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Worktree | `game/` and `tools/playtest/` were already dirty before this run, including the PR-PLAY-33 through PR-PLAY-37 files. Hashes of those trees did not change during the run. |
| Provider | Configured OpenAI client. Credentials were present and were not recorded. |
| Configured model | `gpt-4.1-mini` |
| Responding model | `gpt-4.1-mini-2025-04-14` |
| Scenario id | `FiveTurnGameplay` |
| Fixture | `frontier-gate-v1` |
| Fixture manifest sha256 | `9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea` |
| Isolation | `tools.atgb.isolation.prepare_isolated_store` under `artifacts/atgb/pr_play_38/live/20261102T021036Z-943166c96646/data` |
| User campaign | `data/` — 150 files, fingerprint unchanged |
| Controller | `.venv` Python, base interpreter `Python312\python.exe` |
| Request ceiling | Mission 10. Scenario file 6. Effective worker ceiling 10. Token ceilings left at 200000 / 20000 / 220000. |
| Retries | SDK retries disabled. Host retries disabled. |
| Player lines | The five lines in the mission, not the different lines stored in `tools/playtest/scenarios/FiveTurnGameplay.json`. |

Preserved corrections, confirmed from source before launch:

- PR-PLAY-33 process launch uses the base interpreter and refuses a missing base executable.
- PR-PLAY-34 readiness test `test_non_interpreter_child_is_visible_but_not_an_ownership_failure` is present.
- PR-PLAY-36 `_REALIZATION_TEXTURE_TOKENS` still contains `nearby` and `tightly`.
- PR-PLAY-37 `apply_opening_initialization_recovery` is called from campaign start.

Process ownership at ready: controller pid 1732, worker pid 13600, parent 1732, worker image `Python312\python.exe`, only child `conhost.exe`. Isolation verified. Owned shutdown stopped pid 13600. Exit code 1 is the harness terminate.

Provider requests at the initial snapshot: 0. Campaign was not started. Turn counter was 0. Time pressure was 0. Scene was `frontier_gate`. Character Galinor had 8/8 hp and inventory `spellbook`.

# 3. Campaign Initialization Evidence

Opening source: **B — Deterministic Recovery**.

HTTP 200 in 14.063 seconds. One completed provider request. No second request. `narration_retry_count` 0. `model_retry_attempt` 0. `regeneration_invoked` false. `model_escalated` false.

Provider: `gpt-4.1-mini-2025-04-14`, 26714 input tokens, 1460 output tokens, latency 12344.281 ms. Structured response status: `accepted_structured_response`. Declaration count 7.

Semantic validation: `candidate_rejected` at `game.immutable_valid_response.run_preserve_if_valid._check`, reason `hard_validation_failed`, semantic reason `unauthorized_resolution_decision_fact`. The finish classification is `safe_nonresolution`. Recovery eligibility is `semantic_narration_rejection`. `fallback_attempted` true. `fallback_succeeded` true. `provider_requests_consumed` 1. `initialization_outcome` started. `state_integrity` `authorized_initialization_only`. Provenance on the committed opening is `deterministic_opening_recovery`.

The rejection reason and the rejected narration were kept in diagnostics and in `opening_response_evidence`. They are absent from the player-facing opening. Distinctive rejected wording (`pressed tightly`, `watchful eye`, `rainwater barrel`, `ragged strangers`, `prominently displays`, `hawks hot stew`) does not appear in the committed text.

Rejected provider narration:

> Rain spatters against soot-dark stone as frayed banners flutter atop Cinderwatch's eastern gate. Refugees, wagons, and foot traffic pile into the muddy approach, pressed tightly by guards holding the choke point. A gate serjeant keeps a watchful eye on the crowd while glancing periodically at a roster board. Nearby, a tavern runner hawks hot stew and paid rumors beside a rainwater barrel. Threadbare watchers and ragged strangers cluster along the muddy line near the gate. A notice board prominently displays new taxes, curfew rules, and a posted warning about a missing patrol. The Ash Compact's census delays have snarled traffic on the eastern caravan route, tightening this chokepoint further.

Final player-facing opening:

> Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A tavern runner shouts offers of hot stew and paid rumor. You can read the notice board, press the guards, or approach the tavern runner.

| Field | Before start | After start |
| --- | --- | --- |
| campaign_started | false | true |
| turn_counter | 0 | 1 |
| time_pressure | 0 | 1 |
| active_scene_id | frontier_gate | frontier_gate |
| log entries | 0 | 1 |
| character | Galinor, 8/8, spellbook | unchanged |
| suspicion, unrest, danger, occult_instability | 0 | 0 |

The opening world tick also advanced faction pressure and agenda once: House Verevin pressure 2→3, Ash Cowl 2→3, Ordo Pyric 1→2, and each agenda 0→1. Two `faction_pressure` event lines were appended. Combat payload was unchanged; only `saved_at` was rewritten. An empty `chat_history` key was removed. Gameplay turns did not tick the world again. This matches one existing world tick on the authorized opening time step, not a second recovery request.

The player HTTP body did not include `opening_recovery_debug`. The session log and the `opening_validation` diagnostic did.

# 4. Full Gameplay Transcript

## Turn 1

Player: What is available here?

AI-DM: You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line. Ash Compact census delays have tightened the eastern caravan choke point. Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A tavern runner shouts offers of hot stew and paid rumor. You can read the notice board, press the guards, or approach the tavern runner.

## Turn 2

Player: Have you heard any interesting rumors lately?

AI-DM: I cannot tell who that is addressed to. Nothing has been attempted.

## Turn 3

Player: I want to investigate the footprints.

AI-DM: Who or what do you want to investigate the footprints with, or how do you want to proceed?

## Turn 4

Player: I want to follow the trail connected to the missing patrol.

AI-DM: How do you want to follow the trail connected to the missing patrol? With whom or by what means?

## Turn 5

Player: I examine the footprints here more carefully.

AI-DM: How do you want to examine the footprints more carefully? With what means or assistance?

# 5. Per-Turn Evaluation

Scores are responsiveness, narrative quality, mechanical integrity, state consistency, and continuity. Each is 0–2.

| Turn | R | N | M | S | C | Total | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 Available offerings | 2 | 1 | 2 | 2 | 2 | 9 | PASS |
| 2 Local rumors | 0 | 1 | 0 | 2 | 1 | 4 | FAIL |
| 3 Investigate footprints | 1 | 1 | 0 | 2 | 1 | 5 | FAIL |
| 4 Follow the patrol lead | 1 | 1 | 0 | 2 | 1 | 5 | FAIL |
| 5 Examine footprints | 1 | 1 | 0 | 2 | 0 | 4 | FAIL |

Aggregate: **27 / 50**. PASS 1, PARTIAL 0, FAIL 4, BLOCKED 0.

Critical-failure rule: turns 2–5 fail to answer meaningfully, so they cannot be PASS. None invented a success, moved the party, or changed inventory.

### Turn 1 — PASS

The interpretation was `QUESTION` to the GM, status `INTERPRETED`. Processing outcome `conversational_answer`. Narration was not invoked. The resolver was not invoked. The host concatenated public scene evidence: notice board, serjeant, tavern runner, exits including `Follow the missing patrol rumor`, and the opening paragraph. That answers what is available at this location. The prose is a fact list, so narrative quality is 1. State delta is log length 1→2 only. Character, scene, clocks, and turn counter stayed put.

### Turn 2 — FAIL

The interpreter recognized an in-world `ASK` aimed at `tavern_runner`, with the premise that the runner trades rumors. The bridge then rejected that target. Recorded reason: `ungrounded_provider_target`. Missing information: `interlocutor`. `direct_address` false. `narration_invoked` false. `resolver_invoked` false. Outcome `conversational_clarify`. The stored choices were Gate Guard, Gate Serjeant, and Tavern Runner. The player was not shown those choices. The line says nothing was attempted. No rumor was produced. State delta is log length only. Continuity is partial because the opening had just named the rumor-seller and the reply does not use that fact.

### Turn 3 — FAIL

The interpreter returned `CLARIFICATION_REQUIRED`, recipient `AMBIGUOUS`, purpose `ACTION`, with empty evidence refs. The host asked who to investigate the footprints with. No check was resolved. No clue was added. The muddy gate is in the opening, but this reply does not examine it.

### Turn 4 — FAIL

Public evidence on earlier turns listed the exit `Follow the missing patrol rumor`. The interpreter still returned `CLARIFICATION_REQUIRED` and asked for method or companion. `resolved_transition` stayed false. Scene stayed `frontier_gate`. Visited scenes stayed `[frontier_gate]`. The reply does not claim that travel happened. The authorized exit was not taken.

### Turn 5 — FAIL

The party is still at the gate, so this is not an examination at a destination. The interpreter's footprint reference is `status: MISSING`, `explicit: true`, `candidates: []`, operation `INSPECT`. The host asked for means or assistance. It does not say that no footprint object is present and it does not say that the previous follow action did not happen. Continuity with the failed pursuit is lost. No mechanical discovery was committed.

# 6. State Transition Evidence

Initial isolated state, before `POST /api/new_campaign`: campaign not started, turn 0, time pressure 0, scene `frontier_gate`, Galinor 8/8, inventory `spellbook`, no discovered clues, provider requests 0.

Pre-opening baseline after new campaign: campaign not started, turn 0, time pressure 0, scene `frontier_gate`. Run id changed from `09bee2f04eb87749bc976e7e` to `93940d8e2321312dad4c7323` at new campaign.

Opening mutations are in section 3. Across turns 1–5 the compact delta on every turn is `log_entries` incrementing by one. Changed documents on every turn are `session.json` and `session_log.jsonl`.

From the post-opening snapshot through the final snapshot:

- `world.json` payload identical
- `character.json` identical
- `campaign.json` identical
- combat payload identical
- scene `frontier_gate`
- turn counter 1
- time pressure 1
- other clocks 0
- hp 8/8
- inventory `spellbook`
- discovered clues empty
- active quests remained absent (`observability_gaps` includes `active_quests`)
- `chat_history_len` remained 0 because the transcript is the session log

No gameplay turn changed location, inventory, resources, quests, clues, or clocks.

# 7. Provider Usage

| Call | Purpose | Model | Input | Output | Latency ms |
| --- | --- | --- | --- | --- | --- |
| Opening | `primary_turn` | gpt-4.1-mini-2025-04-14 | 26714 | 1460 | 12344.281 |
| Turn 1 | `interpretation` | gpt-4.1-mini-2025-04-14 | 2285 | 212 | 2600.494 |
| Turn 2 | `interpretation` | gpt-4.1-mini-2025-04-14 | 2564 | 200 | 2149.391 |
| Turn 3 | `interpretation` | gpt-4.1-mini-2025-04-14 | 2679 | 193 | 2360.078 |
| Turn 4 | `interpretation` | gpt-4.1-mini-2025-04-14 | 2678 | 268 | 3148.907 |
| Turn 5 | `interpretation` | gpt-4.1-mini-2025-04-14 | 2638 | 222 | 6259.228 |

- Dispatched requests: 6
- Completed requests: 6
- Input tokens: 39558
- Output tokens: 2555
- Total tokens: 42113
- Provider latency: 28862.379 ms
- Experiment duration: 41.609 s
- Average provider latency per completed gameplay turn: 3303.620 ms
- Budget ceiling: 10. Remaining after the run: 4. `stopped` false.
- SDK retries: 0. Host retries: disabled.
- Provider errors: none.
- Provider fallbacks: none.
- Deterministic opening recovery: one, after the single opening response. It did not call the provider again.

Turns 1–5 did not call the narration model. Their player-facing lines are host speech.

# 8. Failure Analysis

## Confirmed

The opening provider call succeeded structurally and failed the semantic narration check with `unauthorized_resolution_decision_fact`. Recovery discarded that prose, committed the deterministic opening, and did not send a second request.

Every gameplay turn made one interpretation call and then stopped. `resolver_invoked` is false and `narration_invoked` is false on all five.

Turn 2's interpreter selected `tavern_runner`. The engine rejected that selection as `ungrounded_provider_target` and told the player that nothing was attempted. The three NPC choices on the bridge were not in the player-facing line.

Turn 4 did not take the visible exit `Follow the missing patrol rumor`. Location evidence agrees: still `frontier_gate`.

Turn 5 records the footprint referent as missing, with no candidates.

Character, inventory, scene, and clocks did not change on any gameplay turn.

## Hypothesis

The faction pressure step is the ordinary world tick attached to the opening's authorized `time_pressure` increment. The code path is `_tick_advance_factions_one_step` with reason `world_tick`. The run shows exactly one such step and no further step on later turns. That is consistent with the existing opening tick. It is not evidence that recovery issued an extra provider call or a second tick.

## Not supported

These live failures are not the six persisted test failures from PR-PLAY-37. Those tests were not run here. The opening rejection is the same reason family as PR-PLAY-35, and recovery contained it.

## Classification

Primary: **AI-DM failure**. Ordinary lines were turned into clarification or non-answers, and no gameplay turn received narrative realization.

Contributing **engine failure**: turn 2 dropped a visible NPC target, and the orchestrator never reached the mechanical resolver on investigation, travel, or examination.

Contributing **scenario limitation**: the frontier-gate fixture has no footprint entity. The prescribed footprint lines therefore have no authored object. That does not explain the rumor refusal or the unused patrol exit.

Not an infrastructure failure. Ownership, isolation, startup, and owned shutdown held. The user campaign was not modified.

Not a provider failure. Six completed responses, no timeout, no malformed payload, no retry, budget not exhausted.

# 9. Change Manifest

No gameplay implementation file changed during the run. `gameplay_sources_unchanged` is true. `source_drift` is empty.

Files added for this experiment:

- `artifacts/pr_play_38/execute.py` — observational controller. It does not change prompts, routing, validation, recovery, or fixtures.
- Evidence under `artifacts/pr_play_38/` and `artifacts/atgb/pr_play_38/live/20261102T021036Z-943166c96646/`.
- This review, written to `handoff/CURRENT_REVIEW.md` after the run.
- `artifacts/pr_play_38/package_review.py` and the credential scan, manifest, and archive verification written when the review zip was built.

The pre-existing dirty worktree in `game/` and `tools/playtest/` was recorded in `phase1_baseline.json` and was not edited by the controller.

# 10. Known Regression Baseline

Carried forward from PR-PLAY-37 and not repaired:

1. `test_start_campaign_emits_opening_and_sets_started` — debug log route rejected by the privileged-mode policy.
2. `test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text` — post-gate text length 781.
3. `test_start_campaign_promotes_valid_upstream_prepared_scene_opening` — short model sentence kept.
4. `test_preference_gesture_is_not_an_undeclared_world_fact` — expected `dry watch`.
5. `test_authored_patrol_sentence_survives_and_extras_do_not` — `KeyError: 'decision_review'`.
6. `test_pr_cq_patrol_invalid_first_generation_projects_without_regeneration` — provenance `authorized_host_speech` versus `authored_answer_projection`.

No live turn failed in the shape of items 1–6. Item 6's provenance string also appears on these host replies, but the live defect is that the host stopped before rumors, travel, and investigation, not that a patrol sentence lost its provenance label.

The opening semantic rejection is the known matcher limit named in PR-PLAY-37. Recovery handled that case. It does not handle later turns, and later turns never produced a narration candidate.

# 11. Final Verdict

**C — FAIL**

Campaign initialization succeeded through deterministic recovery. Five gameplay exchanges were attempted and returned text. One was a useful location briefing. Four did not perform the requested play, and no mechanical resolution ran. Authoritative state stayed consistent by refusing the actions rather than by narrating false outcomes. That is not five meaningful turns of play.

Next investigation: determine why an interpreted ask to the visible tavern runner is `ungrounded_provider_target`, and why a request that names the authored exit `Follow the missing patrol rumor` is classified as clarification before travel resolution. Do not treat another full five-turn live run as useful until those two ordinary actions reach the resolver. Do not repair them in this experiment. PR-PLAY-39 was not started.
