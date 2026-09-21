# PR-AC — AI Experience / Gameplay: Semantic Playability Calibration Round #2

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Report location: repository root, matching the established Product Realization report convention (`PR-AA`, `PR-AB`).

Calibration artifacts: `artifacts/semantic_playability_calibration_r2/`

---

## 1. Executive Summary

Calibration completed. The clean post-policy baseline was confirmed before live play: the authoritative full suite remains 6,450 collected, 6,351 passed, 0 failed, 99 skipped. Focused semantic, playability, RC-21, and state-authority tests passed 71/71. The Round #1 evaluator corpus still agrees 13/13.

The current system is structurally green and not semantically playable as an ordinary conversational AI-DM. A player can sometimes look around a scene. They cannot reliably read the notice, learn who commands the watch, follow the missing-patrol lead, keep an NPC conversation useful across several decisions, or stay where they said they would stay.

The most important change since Round #1 is not improved play. The measuring instrument remains stable, and the four short comparison scenarios reproduce the same player-visible failures. Longer arcs now show that those failures are not isolated prompt defects. They are the normal path through question and social realization: the live model is called, speaker-grounding validation rejects the first sentence, and deterministic fallbacks replace the turn with murmur-bridges, "I do not know enough," broken refusals, or dangling `mutters,`.

Most common failure class: authored-knowledge questions and object inspections collapsing into social emergency / speaker-grounding fallback.

Most severe failure classes: inverted travel ("stay at the gate" enters Cinderwatch), social lock blocking authored pursuit, dangling speech, and broken refusal fragments.

Dominant probable owning layers: social-exchange realization and speaker-grounding fallback, with contributing intent/object routing and a repeated State ↔ Narration pairing when clues/leads are written while speech denies them.

Multi-turn conversational gameplay is not currently credible.

Recommended next slice:

`PR-AD — Gameplay: Authored-Knowledge Question Realization`

State ↔ Narration Consistency is a major sibling, not the dominant bottleneck. The dominant bottleneck is the fallback that conceals knowledge the engine already owns.

---

## 2. Calibration Method

### Round #1 methodology recovered

Round #1 is the Semantic Validation Calibration campaign documented in `docs/semantic_validation_calibration.md`.

| Element | Round #1 |
| --- | --- |
| Purpose | Calibrate the playability evaluator, not the product loop |
| Scenarios | 13 labeled transcript cases plus 4 live `/api/chat` probes (`p1`–`p4`) |
| Rubric | Mandatory gates `malformed_output` and `player_intent_addressed`; diagnostic axes `direct_answer`, `player_intent`, `logical_escalation`, `immersion` |
| Result states | `PASS`, `FAIL`, `UNCHECKED`, `NOT_APPLICABLE`, `INVALID_RUN` |
| Scoring | `semantic_result` is authority; diagnostic quality cannot override a mandatory fail |
| Procedure | `tools/run_semantic_calibration.py` for the corpus; `tools/run_playability_validation.py` for live probes |
| Model | Live `/api/chat` when configured; corpus cases are fixed strings |
| Evidence | `artifacts/semantic_validation_calibration/` |
| Findings | Evaluator now fails unanswered questions, broken refusals, truncation, and unfulfilled observations. Live `p1`–`p3` still failed as product turns. |
| Taxonomy | Gate reason codes plus the four known-bad shapes |
| Later work | Reactive/adversarial players confirmed the same unanswered-question and malformed-refusal shapes. No gameplay repair. |

Round #1 did not use Critical/Major/Moderate/Minor severity and did not assign owning layers.

### Changes for Round #2

The product doctrine has changed: semantic calibration is now the primary authority for whether the player → runtime → AI-DM → realization → state → next-turn loop is playable. Reusing only the 13-case corpus would re-measure the instrument, not the product.

Round #2 therefore:

1. Re-ran the Round #1 corpus unchanged (comparability).
2. Re-ran the exact `p1`–`p4` player lines as `R2-P1`–`R2-P4` (comparability).
3. Added six short gameplay arcs (`R2-MT01`–`R2-MT06`) with scripted player lines only. No expected GM prose.
4. Kept automated `evaluate_playability` as supporting evidence.
5. Added human semantic judgment, playability severity, and probable owning-layer classification.

No competing taxonomy was created. Round #1 gate codes are retained. Narrow additions are documented in Section 7 only where Round #1 could not name the owning failure.

### Scenario selection

All live cases start from a hard campaign reset into current `frontier_gate` canon: notice board, Guard Captain / gate watch, tavern runner, ragged stranger, hidden rooftop/noble/Ash Cowl facts, RC-21 Lirael-not-authored rule, and the `old_milestone` / `market_quarter` exits.

### Model / configuration

- `.env` present; `OPENAI_API_KEY` nonempty.
- `DEFAULT_MODEL_NAME` / routed model: `gpt-4.1-mini`.
- Upstream preflight: healthy. `startup_run_valid=true`.
- Strict-social turns route `purpose=strict_social` / `high_precision`; retries use `retry_escalation`.

### Runtime path

`tools/run_prac_semantic_playability_calibration.py` → FastAPI `TestClient` → `POST /api/chat` → existing chat pipeline → `evaluate_playability`. Isolated fixtures live in `data/validation/semantic_playability_calibration_r2/scenarios.json`. Production gameplay modules were not modified.

### Volume

- Corpus: 13 offline cases.
- Live cases: 10.
- Live turns: 50.
- Evaluator: 25 PASS / 25 FAIL.

### Limitations

- Scripted player lines, not a live human.
- One model, one seedless live pass; GM output is nondeterministic.
- Compact evidence capture missed some `_final_emission_meta` values; console retry/fallback lines and state slices were used instead.
- One first MT03 attempt crashed on a Windows `cp1252` print of `→` during scene transition. Remaining cases were completed with `PYTHONIOENCODING=utf-8`. That is an operator-encoding blocker, not a gameplay finding.
- Automated PASS is not a human pass. Several canned "I don't know" turns are evaluator PASS and human FAIL.

---

## 3. Baseline Confirmation

PR-AC began from the clean post-policy baseline recorded in `docs/NEXT_SESSION.md` and `artifacts/policy_implementation/post_implementation_suite.xml`.

| Check | Result |
| --- | --- |
| Post-implementation suite XML | 6,450 tests, 0 failures, 0 errors, 99 skipped |
| Focused semantic / playability / RC-21 / state-authority / lead-registry | 71 passed, 0 failed (`artifacts/semantic_playability_calibration_r2/focused_baseline.xml`) |
| Round #1 corpus recheck | 13/13 agreement |
| Upstream preflight | healthy |

No validation cleanup was performed. A first attempt to include playability-smoke tests against the shared `codex_pytest_tmp` directory hit the known Windows `PermissionError`; rerunning with `--basetemp=codex_pytest_tmp_prac_focus` was clean. That matches the already-documented environmental lock, not a product defect.

---

## 4. Calibration Scenario Inventory

| Case ID | Scenario | Initial objective | Behaviors | Turns | Content / state | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R2-P1 | p1_direct_answer | Who commands the watch; chapel relic | Intent, knowledge, conversation | 2 | Opening questions | Completed |
| R2-P2 | p2_respect_intent | Thief, then dye vats | Intent, world, conversation | 2 | No thief in scene | Completed |
| R2-P3 | p3_logical_escalation | See the gate; press the notice | Grounding, continuity | 2 | Notice + `gate_guard` topic | Completed |
| R2-P4 | p4_immersion | Glance at the notice | Grounding, intent | 1 | `notice_board` interactable | Completed |
| R2-MT01 | notice_patrol_inquiry | Learn the patrol warning and decide whether to follow it | Grounding, NPC, continuity, agency | 8 | Notice, Captain, `old_milestone` | Completed |
| R2-MT02 | watch_command_continuity | Identify who commands the watch | NPC, continuity, knowledge | 8 | `gate_guard.topics.watch_command` | Completed |
| R2-MT03 | runner_rumor_decline_path | Talk to the runner; decline the patrol path | Agency, NPC, continuity | 7 | Tavern runner, stranger | Completed |
| R2-MT04 | lirael_redirect_lead_policy | Ask after Lirael; pursue only official follow-up | RC-21, invention, agency | 7 | Lirael not authored | Completed |
| R2-MT05 | unusual_and_impossible_actions | Sneak, bribe, climb, punch, fly | Agency, mechanics, grounding | 7 | Checkpoint, townhouse | Completed |
| R2-MT06 | hidden_fact_probe | Probe hidden facts without leakage | Knowledge, grounding | 6 | Hidden noble / Ash Cowl / list | Completed |

---

## 5. Turn-Level Findings

Successful routine looks-around are omitted unless they contrast a later failure.

### R2-P1 / R2-P2 — Round #1 comparison, unchanged product failure

Player: "Who commands the watch here?"
GM: "The murmur around you never tightens into a single clear voice on that point."
Resolution: `question` / `question_npc`. Interaction: social/engaged, `active_interaction_target_id=null`.
Console: live `gpt-4.1-mini` → `question_rule:social_exchange_first_sentence_not_speaker_grounded` → deterministic fallback → escape hatch.
Evaluator: FAIL. Human: Major.

The chapel-relic and dye-vat questions produce the same bridge family. "Tell me about the thief" dumps ungrammatical visible facts. No thief exists at `frontier_gate`.

### R2-P3 — authored knowledge written, speech denies it

"What do I see at the gate?" binds `gate_guard` and emits "I do not know enough to answer that." Simultaneously the registry gains `captain_thoran_watch` ("Captain Thoran commands the gate watch tonight.") from the guard's authored topic. Narration never says the name.

Pressing the notice emits `Gate Guard mutters,` (dangling speech). Round #1's second turn was a repeated ignorance line; Round #2 is worse.

### R2-P4 / R2-MT01 — the notice cannot be read

"I glance at the notice" and "I look around" describe the crowd. "I step closer and read the notice board carefully" and "I read the notice board" emit guard ignorance. Resolution kind is often `None` or leftover `observe`/`investigate` while speech is social fallback.

The interactable `notice_board` reveals `notice_patrol_route`. In MT01 that clue never appears. In MT04 T2 the lead is written, but the player is told about the serjeant and stew barrel instead.

Addressing the Guard Captain binds the interlocutor (`guard_captain`). Every follow-up about the posted patrol is "I don't know." "I'll follow the missing patrol rumor along that northwest mud track" is classified `social_probe` and does not leave `frontier_gate`.

### R2-MT02 — watch command is known to the engine

`data/world.json` `gate_guard.topics.watch_command` is "Captain Thoran commands the gate watch tonight." Asking the Captain who commands the watch still yields "I don't know" for five turns. On turn 6 the interlocutor swaps to `gate_guard`, the Thoran lead is written, and speech still denies it. Turn 7 is `Gate Guard mutters,`. Turn 8 finally names Thoran after a wait beat.

### R2-MT03 — conversation can work; fallback and travel invert it

Looking for food/gossip is a strong observe. Asking the runner about stew emits the known-bad fragment `No. I cannot answer that from what.` while `muddy_footprints_northwest` is written and never spoken. A later traveler-talk turn is actually good. Declining the notice board emits `Tavern Runner mutters,`. Asking about the ragged stranger repeats the broken refusal.

"I'll stay at the gate a bit longer instead of entering Cinderwatch" is `scene_transition` into `market_quarter`, with "You act on that move, and your position changes with that movement."

A narration-derived lead `narration_ctx_frontier_gate_travelers_around_here_mostly_grumble…` is created from the runner's prose.

### R2-MT04 — RC-21 state holds; official follow-up is unplayable

Asking for Lirael does not instantiate `emergent_town_crier` or add Lirael to `world.npcs`. That is the settled B+C state outcome.

Looking for Lirael in the crowd correctly finds nobody. Checking/reading the board and "pursuing official follow-up" still fail to tell the player the authored patrol-route clue.

### R2-MT05 — unusual physical actions are more playable than ordinary questions

Sneaking along wagons, climbing the townhouse, and attempting to fly produce diegetic attempts and refusals. Bribing a guard and punching the notice board become "I do not know enough." The climb invents House Verevin and rooftop sentries near hidden-fact territory. A later look-around is replaced by the forced fork "Board, runner, or road."

### R2-MT06 — hidden facts are not leaked; observation is hijacked

Hidden Ash Cowl / written-list facts are not stated as truth. The Captain's ignorance of smugglers is legitimate. But looking at rooftops invents an unnamed speaker who says "Walk with me if you want the next name." Watching the threadbare figure becomes the murmur bridge. "What have I confirmed with my own eyes" is answered by the Captain: "I don't know."

---

## 6. Semantic Quality Assessment

| Dimension | Assessment | What currently prevents ordinary play |
| --- | --- | --- |
| Scene grounding | Partial | Broad observe often works. Object-specific look/read does not. |
| Intent understanding | Weak | Natural questions and "read/follow/stay" are frequently normalized into untargeted social or inverted travel. |
| NPC interaction | Weak | Binding an interlocutor works. Useful answers usually do not. Personality collapses to one fallback line. |
| State ↔ narration | Weak, not dominant | Clues/leads are written while speech denies them, or crowd templates replace discovered notice text. |
| Mechanics ↔ narration | Thin | Few mechanical checks fired. Unusual actions were narrated without an authoritative check record. |
| Multi-turn continuity | Weak | Social lock and identical fallbacks erase the situation. Occasional later recovery (MT02 T8, MT03 T3/T6). |
| Player agency | Weak | Stay-vs-enter inverted. Patrol pursuit ignored. Forced forks. Bribe/punch refused as ignorance. |
| Knowledge boundaries | Mixed | Hidden list / Ash Cowl not leaked as fact. Invented unnamed speaker and Verevin/rooftop color overreach. |
| World coherence | Mixed | Locations and roster stay on `frontier_gate` until inverted travel. Watch-command identity is split across Guard Captain, Gate Guard, and Captain Thoran. |
| Conversational quality | Weak | Murmur bridges, broken refusals, dangling `mutters,`, fact-mash, template scene dumps. |

Dimensions that currently prevent credible ordinary play: intent understanding, NPC interaction, State ↔ narration pairing with fallback, multi-turn continuity, and player agency.

---

## 7. Failure Taxonomy

Round #1 codes are reused. Added categories are marked \*.

Evaluator-supporting counts over 50 live turns: 25 FAIL, 25 PASS.

Human material failures are more numerous than evaluator FAILs because canned ignorance is often a gate PASS.

| Class | Approx. human frequency | Typical symptom | Probable owner | Typical severity | Confidence |
| --- | --- | --- | --- | --- | --- |
| Social / speaker-grounding fallback \* | ~20 turns | Murmur bridge, "I do not know enough," identical Captain "I don't know" | Realization / `game.social` / `game.social_exchange_fallback_catalog` / speaker-grounding validator | Major | High |
| State ↔ narration inconsistency | 6–8 turns | Lead/clue written; speech denies or omits it | Realization vs clue/lead application | Major | High |
| Object-intent misroute \* | 5–7 turns | Read/glance/punch notice becomes social ignorance | Intent parsing / interaction routing | Major | High |
| Malformed output (Round #1) | 4 turns | `mutters,` or `cannot answer that from what.` | Final emission / social fallback | Critical | High |
| Player-agency inversion / social lock \* | 3 turns | Follow-patrol ignored; stay → `market_quarter`; forced fork | Intent + interaction routing | Critical / Major | High |
| Unsupported invention | 3–4 turns | Unnamed speaker; narration_ctx lead; Verevin/rooftop extras | Model / post-model adoption / lead extraction | Major / Moderate | Moderate–High |
| Unanswered intelligible question (Round #1) | Overlaps fallback | Question not addressed | Same as fallback | Major | High |
| Observation not fulfilled (Round #1) | 4–6 turns | Notice/eyes-confirmed requests unanswered | Routing + realization | Major | High |
| Knowledge leakage | 1–2 turns | Invented rooftop/noble color near hidden facts | Context / model | Moderate | Moderate |
| Content / identity split | Persistent | Guard Captain vs Gate Guard vs Captain Thoran | Content + realization | Moderate | High |

No new evaluator gates were added.

---

## 8. Round #1 → Round #2 Comparison

Methodology change is disclosed in Section 2. Quantitative comparison is valid for the corpus and the four live probes. Multi-turn arcs have no Round #1 numeric baseline.

| Prior class | Status |
| --- | --- |
| Evaluator false-PASS on unanswered questions / broken refusals | Resolved as instrument behavior. Corpus still 13/13. |
| Live unanswered watch-command | Persistent. Same murmur line as 2026-09-18 `p1`. |
| Live thief / dye-vat mismatch | Persistent. Same fact-mash and bridge. |
| Live "what do I see" → guard ignorance | Persistent, plus new State ↔ Narration (Thoran lead written). |
| Live notice glance describing the crowd | Persistent. |
| Dangling `mutters,` / broken refusal | Persistent and more visible in longer social lock. Round #1 `p3` T2 was repeated ignorance; Round #2 `p3` T2 is malformed. Treat as visible regression, not a new class. |
| Reactive-player concise-refusal false positive | Still present as a candidate (`I don't know` / `Not something I can say here` family). Not converted into a new corpus rule. |
| Multi-turn objective pursuit | Newly measured. Not sustainable. |
| RC-21 Lirael instantiation | Newly measured. State policy holds. Official follow-up remains unplayable. |

Previously dominant evaluator-visible failures have not been replaced by a deeper unrelated class. They are the same realization/fallback collapse, now shown to also block object investigation, NPC continuity, and travel.

The system cannot sustain longer coherent interactions than before. Isolated observe and occasional recovered social turns are better than the fallback path, but they are not the common path.

---

## 9. Representative Failure Traces

### Trace A — watch command (R2-P1 T1, R2-MT02 T2)

`Who commands the watch here?`

→ intent/action `question` / `question_npc`  
→ untargeted or Captain-bound social route; `strict_social` model call  
→ validator `question_rule:social_exchange_first_sentence_not_speaker_grounded`  
→ deterministic fallback / escape hatch  
→ player text: murmur bridge or `Guard Captain shakes their head. "I don't know."`  
→ authoritative topic already exists: `gate_guard.topics.watch_command` = Captain Thoran  
→ no player-visible answer

First divergence: after the model call, at speaker-grounding validation and social fallback. Context was not empty. The engine already knew the answer.

### Trace B — read the notice (R2-MT01 T2, R2-MT04 T3)

`I step closer and read the notice board carefully.` / `I read the notice board.`

→ not realized as interactable investigate of `notice_board`  
→ leftover observe/investigate kind or `None`  
→ social emergency line: "The guard says, 'I do not know enough to answer that.'"  
→ `notice_patrol_route` either never applied or already applied without being spoken

First divergence: intent/object routing, then the same fallback family. The interactable and clue are authored.

### Trace C — follow the patrol (R2-MT01 T7)

`Fine. I'll follow the missing patrol rumor along that northwest mud track.`

→ `social_probe` while still locked to Guard Captain  
→ same "I don't know"  
→ scene stays `frontier_gate`; exit `old_milestone` unused

First divergence: interaction routing / dialogue lock before movement resolution.

### Trace D — stay vs enter (R2-MT03 T7)

`I'll stay at the gate a bit longer instead of entering Cinderwatch.`

→ `scene_transition`  
→ scene `frontier_gate` → `market_quarter`  
→ "You act on that move, and your position changes with that movement."

First divergence: intent parsing / destination extraction treating a refusal-to-leave as the `Enter Cinderwatch` exit.

### Trace E — State ↔ Narration (R2-P3 T1, R2-MT02 T6, R2-MT03 T2, R2-MT04 T2)

Player asks a visible or topical question.

→ clue/lead applied (`captain_thoran_watch`, `muddy_footprints_northwest`, `notice_patrol_route`)  
→ speech is ignorance, crowd template, or broken refusal  
→ later a wait/repeat turn may finally mention the fact

First divergence: after authoritative mutation, at realization/final emission.

---

## 10. State ↔ Narration Consistency Assessment

Classification: **one of several major sources, not the dominant current semantic bottleneck.**

Evidence it is real:

- `captain_thoran_watch` written while the speaker says they do not know (R2-P3 T1, R2-MT02 T6).
- `muddy_footprints_northwest` written under a broken refusal (R2-MT03 T2).
- `notice_patrol_route` written under a crowd template (R2-MT04 T2) or scene-summary template (R2-MT05 T1).
- Narration ingested as a `narration_ctx_…` lead (R2-MT03 T3).

Evidence it is not dominant:

- The most frequent player-visible failure is a canned non-answer even when **no** state changed (R2-P1, R2-MT01 T2–T6, R2-MT02 T1–T5).
- Those turns fail before or without a state mutation. Fixing only "narrate what changed" would leave the murmur/ignorance path intact.
- The same fallback also swallows object inspection and ordinary questions that never reach a clue write.

A State ↔ Narration campaign that starts from written-but-unspoken clues would help the pairing cases. It would not restore ordinary question play.

---

## 11. Multi-Turn Playability Assessment

A player cannot currently pursue an opening objective through several decisions without developer intervention.

| Risk | Observed |
| --- | --- |
| Context collapse | Repeated identical fallbacks erase the difference between stew, patrol, census, and notice. |
| World contradiction | Stay-at-gate enters the market. Watch command is known in world data and denied in speech. |
| State contradiction | Leads/clues written against spoken ignorance. |
| NPC inconsistency | Captain/Guard swap; one-line ignorance personality; dangling speech. |
| Unsupported invention | Unnamed rooftop speaker; narration_ctx lead; Verevin/rooftop extras. |
| Mechanical contradiction | Few checks; bribe/punch treated as questions. |
| Developer intervention | Required to read the notice, learn the watch commander, or follow the patrol. |

MT03 shows that a bound NPC can produce a useful rumor turn. That is not enough to call the loop playable.

---

## 12. Root-Cause Distribution

| Layer | Player-visible weight | Notes |
| --- | --- | --- |
| Realization / social fallback / speaker grounding | Highest | Live model called; validator rejects; catalog lines replace the turn. |
| Intent parsing / action normalization | High | Read/follow/stay/bribe/punch misrouted. |
| Interaction routing / dialogue lock | High | Social engagement blocks investigation and travel. |
| State publication vs narration | Major | Clue/lead writes without speech. |
| Context / prompt construction | Medium | Thief/dye-vat and fact-mash; some invention. |
| Final emission | High for Criticals | `mutters,` and broken refusal fragments. |
| AI / model behavior | Lower than it appears | Several good observes and one good runner turn exist. Do not attribute fallback turns to the model when validation already discarded the model. |
| Content | Medium | Captain / Guard / Thoran split; Lirael not authored (settled). |
| UX | Low–medium | Forced "Board, runner, or road." |
| Persistence | Not implicated | |

Largest player-visible degradation comes from the realization/fallback stack, then intent/routing.

---

## 13. Recommended Next Implementation Slice

### `PR-AD — Gameplay: Authored-Knowledge Question Realization`

**Primary lane:** Gameplay  
**Secondary lanes:** AI Experience, Content & World

**Exact problem.** When the player asks about, inspects, or presses a fact the engine already owns — NPC topic, visible fact, or interactable clue — the turn is routed through strict-social realization, speaker-grounding validation rejects the live sentence, and deterministic fallback conceals that fact.

**Observable player improvement.** "Who commands the watch?" expresses Captain Thoran or a grounded speaker who can say that topic. "What is posted on the notice?" / "I read the notice" expresses `notice_patrol_route`. A bound Captain asked about the posted patrol does not answer with catalog ignorance while the lead is written.

**Evidence.** Traces A, B, and E; J01, J04, J07, J08, J10, J11, J14, J20, J21; Round #1 live `p1`/`p3` persistence; `data/world.json` `gate_guard.topics.watch_command`; `data/scenes/frontier_gate.json` `notice_board` → `notice_patrol_route`.

**Architectural owner.** Social-exchange realization and speaker-grounding, consuming existing NPC-topic and clue/interactable contracts. Intent/object routing only as required to reach those contracts. No new authority store. Narration still does not create state.

**Contracts exercised.** State authority (engine owns clues/topics); realization/final emission expresses outcomes; RC-21 unchanged; semantic calibration remains authority.

**Likely files.** `game/social.py`, `game/social_exchange_emission.py`, `game/social_exchange_fallback_catalog.py`, speaker-grounding / `question_rule` validation, clue/topic application used by `game/api.py`, focused tests around watch-command and notice investigation, plus R2-P1 / R2-P3 / R2-MT01 / R2-MT02 as calibration regression cases.

**In scope.**

- Emit authored NPC-topic or interactable-clue content when the player asks or inspects that fact.
- Prefer a grounded speaker or scene-fact realization over murmur / "I do not know enough" when the knowledge is already owned.
- Keep live-model output from being replaced by catalog ignorance in those cases.
- Narrate the clue/lead when the engine writes it on that turn.

**Out of scope.**

- Prompt rewrites across the project.
- General lead-system refactor or `pending_leads` migration.
- Reopening RC-10 / RC-21.
- Broad State ↔ Narration program beyond authored-knowledge turns.
- Simulated-player expansion.
- Restoring Lirael as authored content.
- Travel-inversion / dialogue-lock as the primary slice.

**Acceptance criteria.**

1. After reset, "Who commands the watch here?" yields a player-facing answer that includes the authored Thoran/watch-command fact or a grounded speaker stating it. Murmur-bridge-only is a fail.
2. "I read the notice board" / "What is posted on the notice?" yields `notice_patrol_route` text. Guard-ignorance-only is a fail.
3. If `captain_thoran_watch` or `notice_patrol_route` is written on the turn, narration mentions that fact.
4. No new NPC is instantiated from narration.
5. Focused structural tests stay green. Round #1 corpus remains 13/13.

**Regression tests.** Deterministic unit/integration around topic/clue realization and fallback suppression when authored knowledge exists. Do not gold-lock live prose.

**Calibration cases to protect.** R2-P1, R2-P3, R2-P4, R2-MT01 T2–T4, R2-MT02 T2, R2-MT04 T2–T3.

---

## 14. Alternative Ready Slices

### A. `PR-AD — Gameplay: Interactable Investigation Routing`

Make read/glance/examine of authored interactables resolve as investigate, not social fallback.

Become highest priority if PR-AD's first implementation spike shows speaker-grounding cannot emit topics without a prior object-route fix, or if notice-reading remains broken after question realization lands.

### B. `PR-AD — Gameplay: Stay/Leave Intent and Social-Lock Override`

Fix inverted "stay at the gate" travel and "follow the patrol" social lock.

Become highest priority if a human playtest shows players can get answers but cannot move, or if Trace D / J09 reproduce more often than unanswered questions.

### C. `PR-AD — AI Experience: State ↔ Narration for Discovery Turns`

Require player-facing text to mention clues/leads written on that turn.

Become highest priority if authored-knowledge answers start landing and the remaining failures are silent discoveries rather than catalog ignorance.

These are alternatives, not a mandatory sequence.

---

## 15. Architectural Friction

- **Speaker-grounding vs untargeted questions.** The validator requires a grounded first-sentence speaker. Ordinary "who commands the watch" has no bound interlocutor, so the architecture prefers a narrator-neutral bridge over a scene-fact answer. Existing ownership can represent the required behavior via NPC topics and visible facts; this is implementation friction, not a request to make the model authoritative.
- **Guard Captain vs Gate Guard vs Captain Thoran.** Scene addressable, world NPC, and topic text are three identities. Realization has no single watch-commander owner. Content alignment may be needed inside PR-AD, not a new domain.
- **Windows `cp1252` print of `→` in `game/api.py` scene-transition logging.** Operator-encoding crash during MT03's first attempt. Not a playability defect. Do not expand PR-AD into log encoding unless it blocks CI.
- **Dialogue lock.** Once social/engaged, later travel/investigate intents stay social. Existing interaction-context owners can represent an override; no new architecture.

No architectural evolution is proposed. Existing owners can express the required behavior.

---

## 16. Deferred Findings

Preserve these unless later evidence elevates them:

- `compat_pending_lead_needed` scene-target-only flag (`docs/NEXT_SESSION.md`).
- Intent parsing still reading `pending_leads` (`docs/NEXT_SESSION.md`).
- Broader lead/clue overlap reduction (`docs/current_focus.md`).
- Evaluator false-positive on concise diegetic refusal (reactive-player candidate C). Do not add a corpus rule in PR-AD unless that slice touches the gate.
- Narration_ctx lead extraction from prose (J18).
- House Verevin / rooftop invention (J26).
- Forced "Board, runner, or road" fork (J27).
- Travel inversion and social-lock (Alternatives B) unless chosen as PR-AD.
- Scene-transition Unicode print (Section 15).
- PR-AB's earlier recommended "Deterministic Product Loop and Frontend Startup Gate" remains a tooling/product-integrity concern, not this cycle's semantic bottleneck.

---

## 17. Required User Decisions

None.

RC-10 = A and RC-21 = B + C remain settled. Lirael stays unauthored. PR-AD can be generated from this report and the listed evidence. Calibration, not preference, selected authored-knowledge question realization over a general State ↔ Narration program.

---

## 18. Handoff Package

### Recommended Next Cycle

`PR-AD — Gameplay: Authored-Knowledge Question Realization`

### Implementation Goal

Make ordinary questions and inspections about facts the engine already owns — watch command, notice text, posted patrol — emerge as player-facing answers from existing topic/clue/interactable contracts, instead of speaker-grounding catalog fallbacks that conceal that knowledge.

### Evidence

- Round #1 live `p1`/`p3` reproduced as R2-P1 / R2-P3.
- 50 live turns; evaluator 25/25 PASS/FAIL; human failures concentrated on fallback + silent discovery.
- Console: model called, then `question_rule:social_exchange_first_sentence_not_speaker_grounded`, then deterministic fallback.
- `data/world.json` already stores the Thoran answer; `frontier_gate.json` already stores the notice clue.
- State ↔ Narration appears when those writes happen, but unanswered catalog lines are more frequent.

### Minimum Files for External Review

- `PR-AC_semantic_playability_calibration_round_2.md`
- `artifacts/semantic_playability_calibration_r2/human_judgments.md`
- `artifacts/semantic_playability_calibration_r2/campaign_index.json`
- `artifacts/semantic_playability_calibration_r2/round1_corpus/calibration_report.md`
- `artifacts/semantic_playability_calibration_r2/runs/20260919T215801Z_R2-P1/transcript.md`
- `artifacts/semantic_playability_calibration_r2/runs/20260919T215801Z_R2-P3/transcript.md`
- `artifacts/semantic_playability_calibration_r2/runs/20260919T215801Z_R2-MT01/transcript.md`
- `artifacts/semantic_playability_calibration_r2/runs/20260919T215801Z_R2-MT02/transcript.md`
- `artifacts/semantic_playability_calibration_r2/runs/20260919T220218Z_R2-MT03/transcript.md`
- `artifacts/semantic_playability_calibration_r2/runs/20260919T220218Z_R2-MT04/transcript.md`
- `data/validation/semantic_playability_calibration_r2/scenarios.json`
- `data/scenes/frontier_gate.json`
- `data/world.json` (gate_guard / tavern_runner topics)
- `game/social.py` (`neutral_reply_speaker_grounding_bridge_line`)
- `game/social_exchange_fallback_catalog.py`
- `game/social_exchange_emission.py`
- `docs/semantic_validation_calibration.md`
- `docs/state_authority_model.md`
- `docs/rc10_rc21_policy_implementation.md`

### Suggested External Prompt

> Here is the PR-AC Semantic Playability Calibration Round #2 report and its supporting evidence. Generate the bounded PR-AD Product Realization implementation block for the highest-leverage semantic playability failure identified by calibration.

### Confidence

**High.** Live `/api/chat` was exercised on the current baseline with a healthy upstream key. The same fallback family appears across comparison probes and multi-turn arcs. Authored knowledge for the two opening facts is in-repo. The main residual uncertainty is how much object-routing must be included inside PR-AD versus left as Alternative A.

---

## Appendix — Commands

```text
.\.venv\Scripts\python.exe -m pytest tests/test_playability_eval.py tests/test_semantic_calibration_corpus.py tests/test_run_playability_validation_tool.py tests/test_playability_smoke.py tests/test_social_destination_redirect_leads.py tests/test_state_authority.py tests/test_clue_lead_registry_integration.py -q --tb=line --junitxml=artifacts/semantic_playability_calibration_r2/focused_baseline.xml --basetemp=codex_pytest_tmp_prac_focus

.\.venv\Scripts\python.exe tools/run_semantic_calibration.py --output-dir artifacts/semantic_playability_calibration_r2/round1_corpus

$env:PYTHONUNBUFFERED='1'; .\.venv\Scripts\python.exe tools/run_prac_semantic_playability_calibration.py --artifact-dir artifacts/semantic_playability_calibration_r2

$env:PYTHONUNBUFFERED='1'; $env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe tools/run_prac_semantic_playability_calibration.py --artifact-dir artifacts/semantic_playability_calibration_r2 --case R2-MT03 --case R2-MT04 --case R2-MT05 --case R2-MT06
```

Production gameplay code was not changed during PR-AC. Added files are the isolated runner, fixtures, artifacts, and this report.
