# PR-BE — Gameplay / AI Experience: Wait Action Ownership and Time-Passage Capability Audit

Date: 2026-09-22
Era: Product Realization
Primary lane: Gameplay
Secondary lane: AI Experience

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Probe artifacts: `artifacts/prbe_wait_action_ownership/`

---

## 1. Executive Summary

PR-BE was a capability audit. Production change was not presumed and was not made.

Ashen Thrones does **not** currently possess an authoritative waiting / in-place time-passage capability.

Ordinary simple waiting (`"I wait."`, `"I wait a moment."`, `"I pause for a moment."`) resolves `kind=None` because no gameplay owner exists for intentional passage of time. That `kind=None` is not a routing miss onto an existing wait action. It is evidence that the capability itself is absent.

Nearby owners are not substitutes:

* `explicit_stay` is remain-in-place versus travel, realized as `observe`.
* `passive_interruption_wait` is wait-out-a-disturbance, realized as `observe`.
* `custom` is the generic physical-action kind used for local walking/pacing. It does not advance diegetic time.
* Downtime / rest is explicitly `downtime_engine_not_wired`.

Existing clocks and counters advance on **every** chat turn, including unparsed ones. They are session bookkeeping and pressure meters, not hours, evening, or scheduled waiting.

Recognizing the word `wait` and asking the model to narrate that time passed would fake support. This cycle stops.

Capability classification: **C — missing gameplay capability.**

Recommended next work: **FUTURE GAMEPLAY CAPABILITY.** Do not open a parser cycle to make `"I wait a moment."` look typed.

---

## 2. Simple-Wait Reproduction

Primary diagnostic input: `"I wait a moment."` at Frontier Gate.

| Stage | Result |
| --- | --- |
| Raw input | `I wait a moment.` |
| Normalization | strip only |
| `looks_like_explicit_stay_intent` | false (`stay` / `remain` / `not leaving` only) |
| `_declared_matches_passive_interruption_wait` | false (disturbance / `to pass` / `holds position and waits` only) |
| HA family | `none` |
| Local physical movement | false |
| Travel dest intent | false |
| Observe / investigate / interact patterns | no match |
| `parse_freeform_to_action` | `None` |
| `parse_intent` fallback | `None` |
| Candidate owners | none |
| `custom` eligibility | not entered; wait is not local movement |
| Final kind | `None` via unparsed GPT (`chat_procedural_unparsed_freeform`) |
| State mutation unique to wait | none |
| Universal per-turn bookkeeping | `session.turn_counter += 1`; `session.clocks.time_pressure += 1`; `advance_world_tick` (projects / factions / mobile NPCs) |
| Diegetic date / hour | unchanged (`current_date` remains `"Day 1"`) |

`"I wait."` and the novel ordinary form `"I pause for a moment."` fail at the same first point.

The first point at which intentional waiting loses semantic ownership is **action typing / owner selection**: after stay, interruption-wait, perception, local movement, travel, and inspect lanes, no remaining owner represents in-place time passage. The parser then correctly returns `None`.

That is not a late execution or narration defect. There is no later wait resolver to reach.

---

## 3. Compound-Wait Reproduction

Input: `"I step back and wait."`

| Check | Result |
| --- | --- |
| Wait recognized | no |
| Local movement captures utterance | no |
| `"I step back."` alone | also `None` |
| Stay / interruption-wait / HA / travel dest | all false |
| Final kind | `None` |

This is **not** uniquely a compound-intent failure.

PR-AQ local movement requires `step/walk/move` plus `a few steps` / `along` / `beside` / `closer`, or bare `pace`. `"I step back."` is outside that family. `"I step closer."` and `"I pace."` already reach `custom`.

Both clauses fail independently. Comprehensive `and`-split execution remains deferred. PR-BE does not treat the compound example as a reason to start an N-action project, and does not reopen PR-AQ to add `step back`.

---

## 4. Existing Time-Authority Inventory

Runtime evidence only. Names and comments are not treated as capabilities.

| Surface | Exists? | What it actually is | Diegetic time? |
| --- | --- | --- | --- |
| `session.turn_counter` | Yes | Integer incremented on every chat / start-campaign turn, including unparsed | No. Session turn index / seed / staleness. |
| `session.clocks.time_pressure` | Yes | 0–10 pressure meter; `advance_clock(..., 1)` on every chat | No. Not minutes or hours. |
| Other session clocks | Yes | `suspicion`, `unrest`, `danger`, `occult_instability` | No. Pressure meters. |
| `session.current_date` | Field exists | Initialized to `"Day 1"` in `create_fresh_session_document` | No mutation owner in `game/`. Never advances. |
| `world.world_state.clocks` | Schema exists | Canonical clock rows for CTIR / campaign progression | Current `data/world.json` is `{}`. Not a time-of-day clock. |
| `advance_world_clock` / world-progression clocks | Yes | Named campaign clocks, typically 0–10 | Not hours. Not player-wait owned. |
| `advance_world_tick` | Yes | Every chat advances active projects, faction pressure/agenda, and `availability=mobile` NPCs with a move target | Background campaign tick, not elapsed minutes. Same tick for look-around and unparsed wait. |
| Travel duration | No | Travel changes scene when an exit binds | No duration field is consumed. |
| Rest / camp / short_rest / long_rest | Declared, unwired | `classify_noncombat_kind` returns `downtime_engine_not_wired` | No. |
| Scene clock | No | — | — |
| Scheduled events / wait-until conditions | No | NPC move requires authored `agenda_move_to_scene_id` on tick, not player wait | — |
| `game/gm.py` downtime labels | Keyword tags only | `rest` / `sleep` / `make camp` label prompt text | Not execution. |
| API / GM `_PASSIVE_ACTION_CUES` `"wait"` | Marker only | Prompt / policy marker when text contains `wait` | Not an action kind. Tests often **force** `resolution.kind=observe` around `"I wait."`. |

Authoritative meaning of “time passes” in current runtime:

```text
A player turn happened.
session.turn_counter increased by 1.
session.clocks.time_pressure increased by 1 (clamped 0–10).
Campaign tick ran (projects / factions / eligible mobile NPCs).
```

That happens for `"I look around."`, `"I listen."`, `"I wait a moment."`, and any other chat. It does not mean a moment, an hour, or evening occurred.

Documentation/design intent (`noncombat` downtime vocabulary, `current_date`, world-clock schema) is ahead of runtime. The runtime does not implement those intents for player waiting.

---

## 5. Actions That Currently Consume or Advance Time

| Action | Owner | Time mutation | Contextual? | Before narration? | Downstream observers |
| --- | --- | --- | --- | --- | --- |
| Any completed chat, including `kind=None` | `game/api.py` chat | `turn_counter + 1`, `time_pressure + 1`, world tick | Fixed +1 | Yes, before parse | Skill-check seeds, social last-turn, lead touch, perception-turn stamps, prompt clock summary |
| `observe` / `investigate` / `interact` / `custom` | exploration | Same universal increment only | No extra wait duration | Resolution produces hint / scene state, not elapsed time | Perception / search stamps use turn index |
| `travel` / `scene_transition` | exploration + scene graph | Scene change if dest binds; optional authored `world_updates_on_transition` | Exit-authored flags/clocks, not minutes | Yes | Scene runtime, arrival |
| `explicit_stay` | parser → observe | Universal increment only | Remain here, do not travel | Observe hint | None for elapsed time |
| `passive_interruption_wait` | parser → observe | Universal increment only | Disturbance-easing observe hint | Yes | No clock |
| Rest / downtime | none | Unsupported | — | — | — |
| Forced wait type | does not exist | — | — | — | — |

No action advances a world clock, date, or hour **because the player waited**. Travel does not mint duration. Custom does not mint duration.

---

## 6. Does Waiting Already Have an Owner?

| Candidate | Verdict |
| --- | --- |
| A. Explicit `wait` / `pass_time` action | **No.** `ACTION_TYPES` / `EXPLORATION_KINDS` have no such kind. |
| B. Generic/custom physical action that legitimately owns wait | **No.** `custom` is local walking/pacing or authored scene-action fallback. Resolution hint: “Narrate outcome without simply restating the scene summary.” No time mutation. |
| C. Existing turn-advance usable as wait without new architecture | **No.** The increment is universal and already happens on unparsed wait. Using it as “a moment passed” would make look-around and wait identical, and would still not authorize “a few minutes” / “an hour” / “until evening.” |
| D. No gameplay owner | **Yes.** |

Existing wait-adjacent lanes:

```text
"I stay here."
    → observe / explicit_stay
    → "remain in this place; observe the scene"
    ≠ pass time

"I wait for the commotion to pass."
    → observe / passive_interruption_wait
    → "narrate the interruption easing"
    ≠ ordinary wait

"I pace." / "I step closer."
    → custom / local_physical_movement
    ≠ wait
```

`"I hold position and wait."` does **not** hit the interruption-wait lane. That pattern requires `waits`, not `wait`.

---

## 7. First Incorrect Decision

There is no incorrect routing decision onto an existing wait owner.

The first **insufficient** decision is architectural, not a missed regex:

```text
parse_freeform_to_action("I wait a moment.")
    → not stay
    → not passive_interruption_wait
    → not HA observe
    → not local_physical_movement
    → not travel / observe / investigate / interact
    → return None
    → API unparsed GPT
    → resolution.kind = None
```

The parser is fail-closed because no wait/pass-time owner exists. Teaching it the token `wait` would only change the label on the same missing capability.

A separate leftover, not used as the primary diagnosis: `"I wait for the guard to leave."` matches legacy `"leave" in text` and becomes unresolved `travel`. That is a travel-keyword false positive, not a wait owner.

---

## 8. Semantic Matrix

Diagnostic examples only. Scene: canonical Frontier Gate.
Evidence: `artifacts/prbe_wait_action_ownership/probe_matrix.md`.

| Input | Class | Result | Meaning |
| --- | --- | --- | --- |
| `"I wait."` | simple wait | `None` | Ordinary simple wait unowned |
| `"I wait a moment."` | simple wait | `None` | Known residue; same miss |
| `"I pause for a moment."` | novel simple wait | `None` | Not wording-specific |
| `"I stand here and wait."` | simple / compound-ish | `None` | Stay words absent; wait unowned |
| `"I stay here for a while."` | stay, not wait | `observe` / `explicit_stay` | Remain-here. Observe hint. No elapsed-time state |
| `"I stay here."` | stay contrast | `observe` / `explicit_stay` | Same stay owner |
| `"I wait until evening."` | target-time | `None` | Unsupported |
| `"I wait for an hour."` | explicit duration | `None` | Unsupported |
| `"I wait for the guard to leave."` | conditional | `travel`, dest unresolved | Leftover `leave`; not wait |
| `"I wait until someone arrives."` | conditional | `None` | Unsupported |
| `"I look around."` | observe contrast | `observe` | Preserved |
| `"I listen."` | listen contrast | `observe` / HA listen | Preserved |
| `"I rest."` | rest contrast | `None` | Downtime unwired |
| `"I step back."` | local-move contrast | `None` | Outside PR-AQ regex |
| `"I step closer."` | PR-AQ local move | `custom` | Preserved |
| `"I pace."` | PR-AQ local move | `custom` | Preserved |
| `"I step back and wait."` | compound | `None` | Both clauses fail independently |
| `"I go to the quay."` | scene travel | `travel`, dest unresolved | Travel owner preserved; quay is not a Frontier Gate exit |
| `"I wait for the commotion to pass."` | interruption wait | `observe` / `passive_interruption_wait` | Existing narrow observe lane |
| `"I hold position and wait."` | near-interruption | `None` | Pattern wants `waits` |

---

## 9. Simple vs Scheduled / Conditional Waiting

| Form | Example | Current | Future |
| --- | --- | --- | --- |
| Simple wait | `"I wait."` | Unowned | Would need a designed turn/time unit and a quiet no-event result |
| Explicit duration | `"I wait for an hour."` | Unowned | Requires duration semantics |
| Target time | `"I wait until evening."` | Unowned | Requires a world clock / date-time owner |
| Conditional | `"I wait until the guard leaves."` | Unowned; one leftover travel false positive | Requires event scheduling |

The latter three are different capabilities. This cycle does not implement them.

---

## 10. State-Before-Narration Authority

If the system said `"A few minutes pass."` today, no authoritative state would support that sentence.

| Claim | Authoritative state |
| --- | --- |
| A moment / a few minutes passed | None |
| An hour passed | None |
| Evening arrived | None (`current_date` stays `"Day 1"`) |
| A turn happened | `turn_counter` already increments for every chat |
| Time pressure rose | `time_pressure` already increments for every chat |
| Campaign backbone ticked | `advance_world_tick` already runs for every chat |

`custom` / `observe` resolution for stay or local movement produces a **hint**, not a time mutation. Downstream world progression does not see a wait-specific change.

Therefore: do not ask the LLM to narrate waiting. That would be prose pretending time passed.

---

## 11. Quiet / No-Event Waiting

A quiet completed wait is conceptually desirable. It is not implementable now without inventing the capability.

If a future owner exists, a quiet wait must be allowed to complete without minting:

* NPC arrival
* weather
* patrol
* conversation
* discovery
* threat
* an arbitrary number of elapsed minutes

That result is not authorized today. The unparsed path is worse: the model may invent those events because `kind=None` has no grounded wait contract.

---

## 12. Capability Classification

**C. Missing gameplay capability.**

Not A: no existing wait/pass-time runtime owner for ordinary language to reach.

Not B: `custom` can represent local physical doing, not intentional inaction that advances world time. Mapping wait to `custom` or `observe` would only produce narration.

Not D: ordinary simple waiting fails. This is not leftover unusual wording around a working family.

---

## 13. Repair-Threshold Decision

A production repair is **not** warranted.

The threshold fails because:

* there is no authoritative gameplay effect behind waiting;
* a parser success would be plausible narration only;
* duration, evening, and conditional forms would require new time/scheduling architecture;
* compound `"I step back and wait."` would still need deferred N-action execution even if simple wait existed;
* a new world-clock architecture is out of scope.

Forbidden repairs that were considered and rejected:

* hardcoding `"I wait a moment."`
* matching only the token `wait`
* treating stay / rest / listen / observe / travel as wait
* using the universal `turn_counter` increment as if it were a wait duration
* adding arbitrary elapsed minutes
* letting the LLM choose elapsed time
* inventing world events so waiting feels interesting

---

## 14. Production Changes

**None.**

No parser lane, action kind, clock, duration table, or narration template was added.

---

## 15. Authoritative Before / After State Evidence

No production change, so runtime state is unchanged.

For an unparsed simple wait on a live chat (current architecture, not executed as a live campaign in this cycle):

| Field | Before a chat | After any chat, including wait |
| --- | --- | --- |
| `resolution.kind` | — | `None` |
| `session.turn_counter` | *n* | *n* + 1 |
| `session.clocks.time_pressure` | *p* | min(10, *p* + 1) |
| `session.current_date` | `"Day 1"` | `"Day 1"` |
| `world.world_state.clocks` | `{}` in canonical world | still no wait-owned clock |
| Scene id | unchanged | unchanged |
| NPC roster / scheduled wait target | none | none |

Parser-level before/after is identical: `None`.

---

## 16. Narration / State Correspondence

Unparsed wait has no typed resolution. Final realization uses `_build_gpt_narration_from_authoritative_state(..., resolution=None)`.

Any narration that claims minutes passed, someone arrived, or the light changed would be model invention. That path is the same untyped GPT fallback PR-AQ documented for unrecognized physical language.

Stay (`"I stay here."`) is typed `observe` and is authorized to describe remaining in place / noticing the scene. It is **not** authorized to claim elapsed time.

---

## 17. Tests / Probes

| Artifact | Role |
| --- | --- |
| `development/tmp/prbe_wait_action_probe.py` | Disposable parser / helper / exploration matrix |
| `artifacts/prbe_wait_action_ownership/probe_matrix.json` | Machine-readable matrix |
| `artifacts/prbe_wait_action_ownership/probe_matrix.md` | Human-readable matrix |

No new production test file. Adding a test that asserts `"I wait." → None` would lock the gap as intended parser behavior; adding a test that asserts a typed wait would claim a capability that does not exist.

Existing suites that mention `"I wait."` are mostly fixtures that **inject** `resolution={"kind": "observe", "prompt": "I wait."}`. They are not evidence of a wait action.

PR-AQ local-movement tests remain the authority for `custom` walking. This cycle did not rerun them because production code did not change.

---

## 18. Generalization Evidence

The miss is the semantic family **ordinary simple in-place waiting**, not one replay phrase.

Forms that share the miss without using the known wording:

* `"I wait."`
* `"I pause for a moment."`
* `"I stand here and wait."`

A repair that only taught `"I wait a moment."` would have been too narrow. No such repair was made.

---

## 19. Regressions

None introduced. Production code was not changed.

Preserved by non-interference:

* PR-AQ local walking (`"I pace."`, `"I step closer."`) still `custom`
* PR-AQ / PR-AR listen (`"I listen."`) still `observe`
* Observe (`"I look around."`) still `observe`
* Stay still `observe` / `explicit_stay`
* Scene travel still `travel` / `scene_transition`
* Interruption-wait still the narrow observe lane
* Compound N-action execution still deferred
* PR-BD interactable-reference convergence not reopened

---

## 20. Validation Coverage Requested by the Cycle

| Item | Result |
| --- | --- |
| 1. `"I wait."` | `None` |
| 2. `"I wait a moment."` | `None` |
| 3. Novel ordinary simple wait | `"I pause for a moment."` → `None` |
| 4. `"I stand here and wait."` | `None` |
| 5. `"I step back."` | `None` (PR-AQ regex residue, not wait) |
| 6. `"I step back and wait."` | `None` (both clauses fail; compound deferred) |
| 7. `"I look around."` | `observe` |
| 8. `"I listen."` | `observe` / listen |
| 9. Rest | `"I rest."` → `None`; downtime unwired |
| 10. Scene travel | `"I go to the quay."` → `travel` |
| 11. Explicit-duration wait | `"I wait for an hour."` → `None` |
| 12. Target-time wait | `"I wait until evening."` → `None` |
| 13. Conditional wait | `"I wait until someone arrives."` → `None`; `"…guard to leave"` leftover travel |
| 14. State before/after supported simple wait | No supported wait. Universal per-turn increment only |
| 15. Narration ↔ state | No authorized wait prose |
| 16. Quiet / no-event wait | Not implementable without new capability |
| 17. No invented NPC/world event | Not enforceable on unparsed path; must not be faked by parser repair |
| 18. PR-AQ local-movement | `pace` / `step closer` remain `custom` |
| 19. PR-AR perception | `I listen.` remains observe |
| 20. Existing time/travel tests | Not re-run; no production diff |

Unsupported advanced forms remain unsupported.

---

## 21. Unsupported Advanced Wait Forms

Leave these unimplemented until a designed time system exists:

* Explicit duration (`an hour`, `a few minutes` as authoritative amounts)
* Target world time (`until evening`, `until dawn`)
* Conditional / event-driven waiting (`until the guard leaves`, `until someone arrives`)
* Compound wait after local movement (`step back and wait`)
* Rest / camp / sleep as wait aliases
* Using travel to fake elapsed time

---

## 22. Intentionally Accepted / Deferred Residue

Accepted on this audit:

* Ordinary simple wait remaining `kind=None` because the capability is missing
* `"I step back."` remaining outside the PR-AQ local-movement regex
* `"I hold position and wait."` missing the third-person `waits` interruption pattern
* `"I wait for the guard to leave."` leftover travel on the word `leave`
* Stay (`"I stay here."`) remaining observe, not time passage
* Tests that stub `"I wait."` as observe remaining fixture convention

Leave these sibling items deferred unless later evidence elevates them:

* Opening `Gate Guard mutters` / `"Word is,"`
* Follow-up paraphrases without owned-topic / public-clue overlap
* `"Gate Serjeant"` resolving to `gate_guard`
* Unresolved travel narrated as scene stock
* Evaluator lexical false negatives on quiet listen and nothing-new
* Generic `"The guard says"` absent-speaker label
* Accepted `"posted notices"` leading-modifier residue
* Accepted undirected who-last-read inspect residue
* Accepted local-observation passive residue
* Unrelated social-pressure test reds

Do not reopen PR-BD interactable-reference convergence, PR-BC agent-history ownership, PR-BB classifier convergence, PR-BA place-existence ownership, PR-AZ retry ownership, PR-AY local-observation semantics, PR-AX geographic eligibility, PR-AW stamp eligibility, PR-AV topic-hook eligibility, PR-AU absence fail-closed, PR-AT truncation, PR-AS relevance comparison, PR-AR grounding, PR-AQ typing, PR-AP grammar, PR-AO provenance, or PR-AI speaker ownership without new causal evidence.

---

## 23. Explicit Convergence Assessment

### A. Does Ashen Thrones currently possess an authoritative waiting capability?

**No.**

### B. What subsystem owns intentional passage of time?

**No such owner exists.**

`session.turn_counter` and `session.clocks.time_pressure` increment on every chat. `advance_world_tick` advances campaign backbone. `current_date` is a static label. World clocks are empty campaign-progression slots. None of these is a wait/pass-time owner.

### C. Is simple wait currently a routing bug or a missing gameplay feature?

**Missing gameplay feature.**

`kind=None` is the fail-closed parser result for an action the runtime cannot authorize.

### D. Was production code changed?

**No.**

### E. If changed, what general semantic family was repaired?

**Not applicable.**

### F. Does a successful wait mutate authoritative time/turn state?

**There is no successful wait.**

A chat that happens to say `"I wait."` mutates the same universal per-turn bookkeeping as `"I look around."`. It does not mutate date, hour, or a wait-owned clock.

### G. Which advanced forms remain unsupported?

* Duration: unsupported
* Target-time: unsupported
* Conditional / event-driven: unsupported (one leftover travel false positive)
* Compound wait-after-movement: unsupported; also deferred as N-action execution

### H. Is further work recommended?

**FUTURE GAMEPLAY CAPABILITY** — waiting / time passage requires deliberate implementation beyond this audit.

A future gameplay cycle would need, at minimum:

1. An explicit decision on the authoritative unit for simple wait (one session turn vs a named diegetic increment).
2. State mutation that precedes narration and is visible to downstream systems.
3. A quiet no-event completion contract.
4. A hard boundary against inventing duration, evening, NPC arrivals, or weather.
5. Separate later work for duration, target-time, and conditional waiting.
6. No aliasing of wait to rest, observe, listen, or travel.

Do not start that cycle as an intent-parser repair.

---

## 24. Recommended Next Action

Wait ownership is closed as a **missing capability**, not as a remaining parser defect.

Do not select another wait paraphrase as the next Product Realization cycle. Do not teach the parser the word `wait`. Do not add a world clock under the guise of clearing `kind=None`.

If the next slice stays in AI Experience / Gameplay, pick a **different** remaining sibling owner. Candidates of that kind, none automatically selected:

* Replay / opening `Gate Guard mutters` / `"Word is,"` (do not reopen PR-AI without new causal evidence)
* Follow-up paraphrases that miss owned-topic / public-clue overlap
* `"Gate Serjeant"` mapping
* Unresolved travel narrated as scene stock

No user decision is required.

---

## 25. Git / Worktree State

Branch: `feature/product-realization` at checkpoint `4c0a454`, plus uncommitted PR-AS through PR-BE work.

This cycle added only:

* this report
* `docs/NEXT_SESSION.md` handoff update
* disposable probe `development/tmp/prbe_wait_action_probe.py`
* generated evidence under `artifacts/prbe_wait_action_ownership/`

Canonical `data/` was not reset. Not committed. Not pushed.
