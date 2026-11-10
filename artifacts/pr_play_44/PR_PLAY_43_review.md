# PR-PLAY-43 — Live Gameplay Validation After Grounding Repair

Verdict: **B — PARTIAL**

The post-opening grounding audit passed. One fresh AI opening was accepted, and it did not store extra public facts or glue the authored facts together. All five prescribed turns were played on that same campaign. The rumor reached the Tavern Runner and the social resolver. The notice board reached the exploration resolver and revealed `notice_patrol_route`. The authored patrol exit reached `old_milestone`. The footprints at Old Milestone reached the exploration resolver and revealed `milestone_mud_prints`.

The notice-board reply did not tell the player what the notice said. The stored clue is "The missing patrol was last seen taking the northwest mud track past the crates." The player-facing line was "You examine the notice board, and you turn up a concrete clue." That is a narrative-realization gap, not a return of the PR-PLAY-41 person clarification.

No gameplay, prompt, provider, fixture, or user-campaign file was edited. The user campaign fingerprint is unchanged.

# 1. Executive Summary

PR-PLAY-41 stopped three legitimate actions because an accepted opening stored seven public facts without terminal punctuation, and grounding then treated those facts as one sentence. PR-PLAY-42 repaired evidence segmentation and action-type authority offline. This experiment asked whether a new live opening and the real provider would still let the same five actions play.

They did, with one degraded reply. The provider interpreted four gameplay turns and wrote the opening. It did not narrate any gameplay turn. Travel was deterministic and still arrived at Old Milestone. The pre-tick path did not turn that move into a conversation with the Tavern Runner, even though the internal summary "Go to Follow the missing patrol rumor." still uniquely matches that NPC.

Compared with PR-PLAY-38 and PR-PLAY-41, the player now gets a rumor, a real scene change, and a destination investigation. The notice inspection resolves and then withholds the clue text.

# 2. Configuration and Isolation

| Item | Value |
| --- | --- |
| Experiment | `PR-PLAY-43` / `20261102T225835Z-b91e96381683` |
| Revision | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Fixture | `frontier-gate-v1` |
| Fixture manifest SHA-256 | `9c390c78f3fcf7507793e1037eb0add59e5e373050d1996f29f0c26f3b7bf0ea` |
| Provider | Configured OpenAI client |
| Configured model | `gpt-4.1-mini` |
| Responding model | `gpt-4.1-mini-2025-04-14` |
| Request ceiling | 10 |
| Token ceilings | input 200000, output 20000, total 220000 |
| SDK retries | 0 |
| Host retries | disabled |
| Preflight | `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` |
| Health probe from the controller | none |
| Isolation directory | `artifacts/atgb/pr_play_43/live/20261102T225835Z-b91e96381683` |
| User campaign | `data/` |
| User campaign fingerprint | `2e006ba7e3387f32bf6180c2b335b5d208624a9ef5de3c4a67f32f946e3e9371` (150 files, same before and after) |
| Worker | PID 23188, parent PID 16044, base interpreter `pythoncore-3.14-64\python.exe` |
| Isolation gates | all true, including isolated directory distinct from the user campaign |

The working tree already had uncommitted gameplay edits from earlier repairs, including `public_evidence_units` and `addressee_authority_applies`. Source hashes for `game/`, `tools/playtest/`, and `tools/atgb/` were identical before and after the run. This experiment did not change them.

PR-PLAY-42 presence checks all passed: `public_evidence_units`, `addressee_authority_applies`, NPC blobs reading those units, and both the communication decision and the pre-tick gate calling the authority rule.

# 3. Campaign Initialization

Authoritative state before Start Campaign: not started, scene `frontier_gate`, Galinor at 8/8 HP with a spellbook, turn 0, `time_pressure` 0, other clocks 0, no clue knowledge, visited scenes `frontier_gate`, session log empty. Provider requests at that point: 0.

`POST /api/start_campaign` returned HTTP 200 in 16.996 seconds.

Classification: **A — AI opening accepted.**

- Opening source: `ai`
- Recovery eligibility: `ai_accepted`
- Fallback attempted: false
- Semantic classification: `candidate_valid`, then `accepted`
- `opening_accepted`: true
- Hard validation: true
- Provenance: `initial_generation`
- Provider: one `primary_turn` completion, model `gpt-4.1-mini-2025-04-14`, 26714 input tokens, 1649 output tokens, 15751.705 ms, SDK retries 0, host retries disabled
- No retry and no fallback

After initialization the campaign was started, the scene remained `frontier_gate`, the turn counter was 1, and `time_pressure` was 1. The other clocks stayed 0. Inventory and HP were unchanged. No clues were discovered by the opening.

Player-facing opening:

> Rain spatters soot-dark stone as frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach, pressing against the guards holding the choke point tight. Nearby, a gate serjeant keeps a sharp eye on the roster board while managing the anxious crowd. A notice board lists new taxes, imposed curfew rules, and a warning about a missing patrol, drawing furtive glances from passersby. Threadbare watchers and ragged strangers cluster along the muddy gate line, their eyes shifting uneasily. A tavern runner loudly trades hot stew and whispered rumors near a rain barrel, cutting through the damp air. Overlooking the square, a well-appointed townhouse flies noble colors, standing in quiet contrast to the clamorous, muddy scene below. Just beyond, Ash Compact census delays have tightened the eastern caravan choke point, worsening the crowd's congestion. One figure in threadbare clothes stands unnervingly still, watching faces and pack animals more than the gate line itself.

# 4. Post-Opening Grounding Audit

The audit ran after initialization and before any player turn. A separate process loaded the copied opening snapshot and called production grounding functions. It did not submit a turn, call a resolver, or import `game.api`. The live store, the snapshot, and `provider_usage.jsonl` were unchanged. The scratch data directory stayed empty. Provider requests remained 1.

## Public evidence

`visible_facts_add` was empty. This opening did not store the seven unpunctuated facts seen in PR-PLAY-41. The narration rephrases the scene, and those sentences were not appended as new public facts.

Nineteen evidence units remained distinct:

- Summary, location, and mode split as prose.
- Five authored visible facts, each its own unit.
- Six opening-seed facts, each its own unit.
- Five journal-seed facts, each its own unit.

No structured fact was missing from the unit list. No adjacent pair collapsed into one unit. No fact was attached to an NPC the fact does not name.

## Probes

| Probe | Result |
| --- | --- |
| "Have you heard any interesting rumors lately?" | Unique public candidate `tavern_runner`. Grounding executable for `tavern_runner`. No person clarification. |
| "I examine the notice board." | Catalog step `INSPECT` `notice_board`, supported. `addressee_authority_applies` false. Clarification would not fire. |
| "I want to follow the trail connected to the missing patrol." | Travel admission `EXECUTE` `MOVE` `leave_for_follow_the_missing_patrol_rumor`, target `old_milestone`, route status `available`. Authority does not apply. Clarification would not fire. |

The inspection sentence still has a unique public-candidate hit on `gate_serjeant`, from the authored "roster board" fact. That hit did not become a clarification because inspection is not an addressee operation. The internal travel summary "Go to Follow the missing patrol rumor." still grounds uniquely to `tavern_runner`. Authority stays on the original player line, so that summary does not replace the route.

Audit decision: **PASS**. The known PR-PLAY-41 defect was not reproduced.

A harness self-check of the same probe against the saved PR-PLAY-41 opening also returned PASS, with no provider call and no change to that saved store. The temporary self-check report was removed before packaging. It is not this campaign.

# 5. Full Gameplay Transcript

The same campaign continued. No restart. No retried turn.

## Turn 1 — "What is available here?"

Scene stayed `frontier_gate`.

> You are at Cinderwatch Gate District. Rain, choke traffic, a notice board, and gate watch pressure frame the missing patrol inquiry. Visible points of interest: Notice board. Known exits: Enter Cinderwatch, Follow the missing patrol rumor. The notice board lists taxes, curfew rules, and a warning about a missing patrol. A gate serjeant manages the crowd and keeps one eye on the roster board. A tavern runner trades hot stew and rumors near the rain barrel. Threadbare watchers and refugees cluster along the muddy gate line. Ash Compact census delays have tightened the eastern caravan choke point. Rain spatters soot-dark stone as frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach, pressing against the guards holding the choke point tight. Nearby, a gate serjeant keeps a sharp eye on the roster board while managing the anxious crowd. A notice board lists new taxes, imposed curfew rules, and a warning about a missing patrol, drawing furtive glances from passersby. Threadbare watchers and ragged strangers cluster along the muddy gate line, their eyes shifting uneasily. A tavern runner loudly trades hot stew and whispered rumors near a rain barrel, cutting through the damp air. Overlooking the square, a well-appointed townhouse flies noble colors, standing in quiet contrast to the clamorous, muddy scene below. Just beyond, Ash Compact census delays have tightened the eastern caravan choke point, worsening the crowd's congestion. One figure in threadbare clothes stands unnervingly still, watching faces and pack animals more than the gate line itself.

## Turn 2 — "Have you heard any interesting rumors lately?"

> Tavern Runner mutters, "Word is, the runner heard the patrol vanished near muddy footprints northwest of the crates."

## Turn 3 — "I examine the notice board."

> You examine the notice board, and you turn up a concrete clue.

## Turn 4 — "I want to follow the trail connected to the missing patrol."

> You arrive at Old Milestone.

The stored player input is the original sentence. The resolution prompt and the intent raw text are the internal summary "Go to Follow the missing patrol rumor."

## Turn 5 — "I examine the footprints."

Played because the scene was `old_milestone`.

> You inspect prints. Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

# 6. Per-Turn Interpretation and Admission

| Turn | Interpretation | Admission |
| --- | --- | --- |
| 1 | Provider interpretation, status `blocked`, reason `clarification_required`, no action components, empty clarification question, recipient GM. Host then answered. | Conversational answer. `authoritative_mutation` false. No bridge. |
| 2 | Provider accepted `ASK` `tavern_runner`. | Stored interpretation `ASK` `tavern_runner`. Contract interlocutor `tavern_runner`. No clarification. |
| 3 | Provider accepted `INSPECT` `notice_board`. | Contract operation `inspect`, discourse ref `notice_board`. No person clarification. |
| 4 | No provider interpretation. | Stored interpretation `MOVE` `leave_for_follow_the_missing_patrol_rumor`. Destination binding passed. `blocked_incompatible_scene_transition` false. Not reinterpreted as conversation. |
| 5 | Provider accepted `INSPECT` `prints`. | Contract operation `inspect`, discourse ref `prints`. No clarification. |

Raw interpretation records and HTTP bodies are in the live run under `turns/T1` through `turns/T5` and in `artifacts/pr_play_43/live_result.json`.

# 7. Mechanical Resolver Evidence

| Turn | Resolver | Outcome |
| --- | --- | --- |
| 1 | none | `conversational_answer`. Scene unchanged. Turn counter and clocks unchanged. |
| 2 | `social` | NPC `tavern_runner`, topic `patrol_rumor`, clue `muddy_footprints_northwest`. `requires_check` false. Success. |
| 3 | `exploration` | Interactable `notice_board`, clue `notice_patrol_route`. Success. No skill check recorded. |
| 4 | `travel` | Exit `leave_for_follow_the_missing_patrol_rumor`. `resolved_transition` true. Origin `frontier_gate`. Destination `old_milestone`. Success. |
| 5 | `exploration` | Interactable `prints`, clue `milestone_mud_prints`. Success. No skill check recorded. |

The rumor turn also recorded the existing minimum lead `minlead_exit_frontier_gate_old_milestone`. That did not add an exit. Travel later used the authored patrol exit that was already on the scene.

Resolver calls: social 1, exploration 2, travel 1.

# 8. Authoritative State Snapshots and Diffs

| Point | Scene | Visited | Turn | time_pressure | Clues |
| --- | --- | --- | --- | --- | --- |
| Initial | `frontier_gate` | frontier_gate | 0 | 0 | none |
| After opening | `frontier_gate` | frontier_gate | 1 | 1 | none |
| After Turn 1 | `frontier_gate` | frontier_gate | 1 | 1 | none |
| After Turn 2 | `frontier_gate` | frontier_gate | 2 | 2 | `muddy_footprints_northwest`, `minlead_exit_frontier_gate_old_milestone` |
| After Turn 3 | `frontier_gate` | frontier_gate | 3 | 3 | plus `notice_patrol_route` |
| After Turn 4 | `old_milestone` | frontier_gate, old_milestone | 4 | 4 | unchanged |
| After Turn 5 | `old_milestone` | frontier_gate, old_milestone | 5 | 5 | plus `milestone_mud_prints` |

Other clocks (`suspicion`, `unrest`, `danger`, `occult_instability`) stayed 0. Galinor remained 8/8 HP with inventory `spellbook`. NPC ids remained `gate_guard`, `gate_serjeant`, and `tavern_runner`. Scene exits were not extended. Session log grew from 0 to 6 entries, one per opening and turn.

`active_quests`, `known_clues`, and `character_resources` are absent fields, not empty values.

Faction pressure and agenda advanced through recorded world ticks. Turn 2 recorded "Ordo Pyric's pressure mounts." Turn 5 recorded off-screen operation completions for House Verevin, the Ash Cowl, and Ordo Pyric. Influence did not change. No faction was created. Full per-document snapshots are under the live run's `initial`, `baseline`, `opening`, `turns/*/before`, `turns/*/after`, and `after` directories.

# 9. Player-Experience Scoring

| Turn | Class | Response | Narrative | Mechanical | State | Continuity | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PASS | 2 | 1 | 2 | 2 | 2 | 9 |
| 2 | PASS | 2 | 1 | 2 | 2 | 2 | 9 |
| 3 | PARTIAL | 1 | 1 | 2 | 2 | 1 | 7 |
| 4 | PASS | 2 | 1 | 2 | 2 | 2 | 9 |
| 5 | PASS | 2 | 1 | 2 | 2 | 2 | 9 |

Total: **43 / 50**.

Narrative-quality subtotal: **5 / 10**. Every reply is understandable. Each one is also mechanical: Turn 1 repeats the opening after the briefing, Turn 2 wraps the clue in "Word is," Turn 3 withholds the clue, Turn 4 is only the arrival sentence, and Turn 5 opens with "You inspect prints."

State-consistency subtotal: **10 / 10**.

Mechanical pass count: **4** turns classified PASS. Turn 3's resolver was correct and the turn is still PARTIAL because the reply is incomplete.

Meaningful player-facing interactions: **4** (Turns 1, 2, 4, and 5). Turn 3 confirms that an examination happened and does not say what was found.

# 10. Deterministic Versus AI Contribution

| Turn | Interpretation | Narration |
| --- | --- | --- |
| Opening | Provider generation, accepted | Provider-generated narration |
| 1 | Hybrid. Provider interpretation was blocked with an empty clarification; the committed answer is host speech. | Deterministic host speech |
| 2 | AI interpretation | Deterministic host speech |
| 3 | AI interpretation | Deterministic host speech |
| 4 | Deterministic | Deterministic host speech |
| 5 | AI interpretation | Deterministic host speech |

Provider capabilities actually exercised: campaign opening, and gameplay interpretation on Turns 1, 2, 3, and 5. Gameplay narration was not a provider capability in this run. Turn 4 did not call the provider at all, and the move still resolved.

AI interpretation invocations during gameplay: **4**. AI narration invocations during gameplay: **0**. AI narration invocations for the opening: **1**.

# 11. Provider Usage and Latency

| Measure | Value |
| --- | --- |
| Total provider requests | 5 |
| Initialization | 1 `primary_turn` |
| Gameplay interpretation | 4 |
| Gameplay narration | 0 |
| Retries | 0 |
| Fallbacks | 0 |
| Input tokens | 37326 |
| Output tokens | 2478 |
| Total tokens | 39804 |
| Provider latency | 25.47 seconds |
| Experiment duration | 39.999 seconds |
| Average gameplay HTTP latency | 3.20 seconds |
| Longest gameplay HTTP latency | 4.999 seconds (Turn 5) |
| Longest provider call | 15.75 seconds (opening) |

Per completion: opening 26714/1649, Turn 1 2417/240, Turn 2 2746/188, Turn 3 2863/204, Turn 5 2586/197. Turn 4 dispatched nothing. The responding model was `gpt-4.1-mini-2025-04-14` on every completion. The budget stopped flag stayed false, with 5 requests remaining under the ceiling of 10.

# 12. Comparison with PR-PLAY-38 and PR-PLAY-41

| Run | Requests | Tokens | Provider latency | Duration | Meaningful replies | Resolver calls |
| --- | --- | --- | --- | --- | --- | --- |
| PR-PLAY-38 | 6 | 42113 | 28.86 s | 41.61 s | 1 of 5 | — |
| PR-PLAY-41 | 4 | 37427 | 22.34 s | 32.84 s | 1 of 4 attempted | 0 |
| PR-PLAY-43 | 5 | 39804 | 25.47 s | 40.00 s | 4 of 5 | 4 |

This run spent more requests and tokens than PR-PLAY-41 and took longer than that failed session. The extra cost produced the rumor, the move, and the footprint investigation, which those runs did not deliver. Lower cost is not the result being claimed.

# 13. Failure Analysis

## Turn 3 — confirmed, narrative realization

Earliest confirmed boundary: **9. Narrative realization.**

The provider selected `INSPECT` `notice_board`. Admission did not ask which person. The exploration resolver succeeded and stored `notice_patrol_route` with clue text "The missing patrol was last seen taking the northwest mud track past the crates." Provider narration was skipped. The emitted sentence matches the generic clue summary "you turn up a concrete clue," not that clue text. The reply does not contradict the stored state. It omits it.

This is not an AI-model failure and not a resolver failure. It is not the PR-PLAY-41 grounding defect.

## Observations that are not turn failures

- Turn 1's interpreter status is `clarification_required` with an empty question. The player did not receive a clarification. The host answered with the scene briefing.
- The read-only inspection probe still uniquely associates the word "board" with the gate serjeant. Live Turn 3 did not act on that association.
- The travel summary still grounds to the tavern runner. Live Turn 4 moved to `old_milestone` and did not open a conversation.
- Turn 5 tags include `visibility_violation:undiscovered_fact_assertion` and `final_emission_gate_replaced`. The emitted sentence is the authorized `milestone_mud_prints` text, including the statement that number, origin, and direction stay unclear. The player-facing line does not contradict the clue.
- This opening stored no AI-added public facts. The seven-fact corruption from PR-PLAY-41 was not regenerated. The audit still checked the facts that were stored, and the live actions exercised the repaired gates.

No infrastructure, transport, interpretation, grounding, admission, resolver, or state-persistence failure was confirmed on the five turns.

# 14. Change Manifest

Harness files added for this experiment:

- `artifacts/pr_play_43/execute.py` — isolated live controller copied from the PR-PLAY-41 controller, with the post-opening audit inserted before gameplay.
- `artifacts/pr_play_43/grounding_audit.py` — read-only probe. It sets no gameplay flags in the worker. The controller points its data directory at an empty scratch folder and requires the preflight skip before import.

No gameplay module, prompt, provider route, token ceiling, fixture, or user campaign file was modified by this run. `gameplay_sources_unchanged` is true.

# 15. Known Regression Baseline

The regression suite was not run. PR-PLAY-42 recorded 178 passed and 15 failed in the scoped suite, and judged those 15 failures pre-existing. That baseline was not rechecked here.

# 16. Final Verdict

**B — PARTIAL**

The grounding audit passed. Initialization accepted a fresh AI opening without corrupting public-fact boundaries. Five turns were attempted on one isolated campaign. NPC conversation, notice inspection, authored travel, and destination investigation all reached the appropriate resolver and updated authoritative state in line with the fixture. Narration did not contradict that state.

The result is partial because the notice-board reply does not report the clue the resolver just revealed. Arrival and rumor speech are also thin. Gameplay narration was host speech throughout, so this run does not show provider narration carrying a scene.

User campaign data is unchanged.

This review does not start another live experiment and does not repair the notice-board reply.
