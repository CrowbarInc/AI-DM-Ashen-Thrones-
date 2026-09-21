# PR-AM — Gameplay / AI Experience: Explicit World-Action Override of Social Lock

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Replay artifacts: `artifacts/pram_explicit_world_action/`

---

## 1. Executive Summary

PR-AM repaired the highest-leverage ordinary-play failure after PR-AL: after a repaired no-answer social turn with the tavern runner, `"I glance back at the notice board after that."` stayed captured as `social_probe` instead of inspecting the authored notice board.

The recovered contract is:

```text
EXPLICIT GROUNDED WORLD ACTION
    > STALE SOCIAL CAPTURE

AMBIGUOUS CONTINUATION
    + ACTIVE SOCIAL CONTEXT
    → SOCIAL CONTEXT MAY RESOLVE IT
```

Conversation provides context. Conversation does not own the player.

PR-AE already owned this precedence for stay/leave/pursuit. PR-AM generalized the same seams to inspect / examine / look-at / glance-at / read. No second router, conversation stack, or interaction-authority registry was added. No stew price or economics system was added. Harbor-wharf fixtures prove the contract with unrelated vocabulary.

---

## 2. Starting Failure

PR-AL extended replay T13:

> Player: I glance back at the notice board after that.
> GM: Tavern Runner mutters, "Word is, the missing patrol was last seen taking the northwest mud track past the crates."
> `resolution.kind`: `social_probe`
> Interlocutor after: `tavern_runner` / social / engaged

The stew-cost no-answer turn was intact. The next ordinary world-directed action was not executed.

---

## 3. T13 End-to-End Trace

Traced before production changes against live `frontier_gate` content with `tavern_runner` bound.

| Stage | Result before PR-AM |
| --- | --- |
| Active/bound interlocutor | `tavern_runner`, `interaction_mode=social`, `engagement_level=engaged` |
| Previous social action | T12 `question`; grounded no-answer; binding retained |
| Exact player wording | `I glance back at the notice board after that.` |
| Parsed intent | `observe` (untargeted). Bare `glance` matched `OBSERVE_PATTERNS` before investigate. |
| Extracted target | none |
| `notice_board` authority | authored interactable exists; classify without a glance-at tail was `untargeted` |
| Inspect/read/observe/investigate detected? | glance treated as untargeted look-around, not investigate |
| `"after that"` | **not** an ambiguous dialogue follow-up; not information-seeking |
| `is_world_action` | false (`glance`/`look at`/`read` missing from PR-AE strong patterns) |
| Continuity escape | false (`glance around` existed; `glance at` / `glance back at` did not) |
| Social continuation | `resolve_authoritative_social_target` source `continuity` because the runner was still bound |
| `social_probe` eligibility | `_turn_plausibly_addressed_spoken_npc_exchange` accepts `continuity` / `active_interlocutor` unconditionally |
| Route | `dialogue` |
| Dialogue-first | `social_probe` targeted at `tavern_runner` |
| PR-AE recover | none (movement-only) |
| PR-AK surface resolution | never reached |
| State mutation | runner binding retained |
| Narration | runner restated the patrol notice |

`"after that"` did not cause the failure. It is a conversational sequencing tail. The explicit glance-at-surface was already a world action.

---

## 4. First Incorrect Routing Decision

**Confirmed:** `detect_explicit_non_social_continuity_escape` / `_WORLD_ACTION_DIALOGUE_BLOCKERS` did not treat directed glance-at / read as an explicit world action.

That is the first point where notice-board intent lost. After that miss:

1. `_should_break_social_continuity_for_world_action` stayed false.
2. `resolve_authoritative_social_target` kept `tavern_runner` via continuity.
3. `should_route_social` became true (`active_interlocutor_followup`).
4. `_build_dialogue_first_action` emitted `social_probe`.

A cooperating parser defect would still have lost the board even if routing had yielded: `OBSERVE_PATTERNS` treated any `glance` as untargeted observe.

Do not merely suppress `social_probe` downstream. The repair is at world-action recognition, then target parse.

---

## 5. Existing Social-Lock Lifecycle

Recovered; not replaced.

| Concern | Existing owner |
| --- | --- |
| Binding storage | `session['interaction_context']` via `game.interaction_context` |
| Persistence | remains until a continuity-break owner or a non-social resolved action updates it |
| Social continuation | information-seeking / ambiguous follow-up / continuity source while bound |
| Override | explicit non-social escape, world-action blockers, stay/leave/pursuit recover, declared travel |
| Clear | `set_non_social_activity` / `clear_for_scene_change` / successful inspect-family resolution |
| Preserve | genuine questions and short continuations (`Why?`, `What else?`) |

Being bound to an NPC does not mean every later turn belongs to that NPC until goodbye.

World action does not permanently destroy conversational availability. Existing inspect already moves the frame to `activity`. Explicit re-address recovers conversation through identity/binding contracts. PR-AM did not invent a persistent conversation stack.

---

## 6. PR-AE Existing Override Contract

PR-AE proved:

```text
social engagement is context, not movement authority
```

Mechanism:

- `_WORLD_ACTION_STRONG_PATTERNS` / `is_world_action`
- `_WORLD_ACTION_DIALOGUE_BLOCKERS`
- `_EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES`
- `recover_actionable_stay_leave_or_pursuit` as dialogue-first yield

That override was **movement-specific at the recover seam**, and **partially general** at escape/blockers (`inspect` / `examine` / `check` / `look at` / `glance around`). `I'll check the roster board` already escaped (T10). `I glance back at the notice board` and `I read the notice board` did not.

PR-AM extended those same seams. It did not add a parallel routing authority.

---

## 7. Existing World-Action Detection

Before PR-AM, strong world-action verbs were search/sneak/attack/follow/inspect/examine/check/investigate plus leave/pursuit families.

Missing from that family, despite being ordinary inspect/read language:

- `look at`
- `glance at` / `glance back at`
- `read the/a/an/this/that`

`look at` already escaped social lock via `_EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES`, but `is_world_action` was false so the coarse route was `undecided`. `read` parsed as investigate and still lost to `social_probe` because it was not an escape/blocker.

---

## 8. Existing Social-Continuation Detection

Active interlocutor follow-up is used when:

- a speaker is bound and addressable;
- there is no explicit new addressee;
- the line looks information-seeking, matches a short follow-up phrase, **or** the continuity resolver still owns the bound NPC.

The last path is why a non-question glance-at-board became `active_interlocutor_followup`. Continuity is useful for `Why?`. It must yield when the line is an explicit world action.

---

## 9. Root Cause

**G. Multiple cooperating causes, with a confirmed first owner.**

| Cause | Role |
| --- | --- |
| A. Explicit world action not recognized | `glance at` / `read` missing from blockers, escape, and `is_world_action` |
| C. Social continuation evaluated too early | continuity kept the runner after the escape miss |
| E. PR-AE recover limited to movement | dialogue-first could not yield inspect/read |
| Parser | bare `glance` stole `glance at X` as untargeted observe |
| D. `social_probe` too permissive | downstream of the miss; not the first decision |
| `"after that"` | **rejected** as the cause |

---

## 10. Recovered Routing-Precedence Contract

```text
explicit actionable world intent
    → authoritative world-action owner

explicit social action
    → social owner

ambiguous continuation
    + active social context
    → social context may resolve it
```

World-action routing ≠ world-target authorization. PR-AM decides who owns the turn. PR-AK still decides whether the target is grounded.

No new global router.

---

## 11. Implementation

Generic engine only.

1. `game/interaction_context.py`
   - `_WORLD_ACTION_DIALOGUE_BLOCKERS` and `_EXPLICIT_NON_SOCIAL_CONTINUITY_ESCAPE_RES` now include directed look/glance-at and `read the/a/an/this/that`.
2. `game/interaction_routing.py`
   - `is_world_action` includes the same family.
   - Dialogue-first yields to `recover_actionable_explicit_world_action`.
3. `game/intent_parser.py`
   - Untargeted `glance` no longer steals `glance at X`.
   - Directed glance-at is investigate, same family as `look at`.
   - `recover_actionable_explicit_world_action` wraps stay/leave/pursuit and then explicit inspect/read/look-at/glance-at.
4. `game/api.py`
   - Chat classification uses the generalized recover on the same seam as PR-AE.
5. `game/referenced_surface.py`
   - Inspect-tail extractor recognizes glance-at so PR-AK classification matches the parser.

Canonical scene/world content was not modified. No stew price was added.

---

## 12. Inspect / Examine Behavior

Bound NPC + `"I inspect B."` / glance-at / look-at / check:

- B interaction executes;
- NPC does not steal the turn;
- action is not `social_probe`.

---

## 13. Readable-Surface Behavior

Bound NPC + `"I read C."`:

- read/inspect route wins;
- authored contents are communicated;
- social context does not answer on behalf of the object.

---

## 14. PR-AK Class B Surface Behavior

Bound NPC + examine of an authored visible non-interactable:

- PR-AK Class B line executes;
- `social_probe` does not swallow it;
- no unsupported detail is invented;
- no new interactable is created.

---

## 15. Movement / PR-AE Preservation

Bound NPC + explicit leave/travel via authored exit still transitions. Harbor-wharf `"I'll climb the quay stair."` and Frontier Gate pursuit remain intact. PR-AE recover still runs first inside the generalized recover.

---

## 16. Legitimate Social Continuation

`"Why?"` / `"What else?"` while bound remain dialogue / question. World-action override does not steal them.

---

## 17. Explicit Same-NPC Follow-Up

An explicit new question to the bound speaker stays social.

---

## 18. Explicit Different-NPC Addressing

Bound to NPC A, `"I turn to the Tide Clerk. …"` binds NPC B under existing declared-switch / identity contracts. `Gate Serjeant` alias work was not opened.

---

## 19. Unsupported World-Target Behavior

`"I inspect the glass orrery."` / silver obelisk:

- inspect intent overrides social capture;
- target is not instantiated;
- PR-AK `unsupported` fail-closed remains;
- the bound NPC does not invent information about it.

---

## 20. World-Action → Social-Return Lifecycle

Inspect/read/glance-at clears the active social frame to `activity` / `investigate` (existing inspect lifecycle, same as T10 roster inspect).

Explicit later address (`"I ask the Lamp Warden…"`, `"I step back to the tavern runner…"`) rebinds through existing identity contracts.

World action does not permanently destroy conversational availability. PR-AM did not add a conversation stack to keep the NPC "still talking" during the inspect.

---

## 21. Social-State Mutation Audit

| Class | Bound after | Notes |
| --- | --- | --- |
| Explicit social continuation | retained | `Why?`, same-NPC question |
| Explicit world action | cleared to activity | inspect/read/glance-at |
| Ambiguous social continuation | retained | `Why?` / `What else?` |
| Movement override | cleared | scene change / none |
| Unsupported world target | activity, not social | no fake target |
| World action then social return | rebound on explicit address | existing identity path |

No erased NPC memory, duplicated conversation, fake leads, or fake world targets in the PR-AM fixtures.

---

## 22. Economics / Barter Deferral Confirmation

Confirmed:

- no stew price added;
- no menu / shop / barter / supply-demand / willingness-to-pay system;
- live `data/world.json` still has no stew-price topic;
- T12 remains Class C grounded absence (`"No. I cannot answer that from what."`);
- live-model invented prices remain deferred, not patched as a price-specific fix.

---

## 23. Frontier Gate Before / After

| Turn | Before | After |
| --- | --- | --- |
| T12 stew-cost | grounded no-answer; runner bound | unchanged |
| T13 glance back at notice board | `social_probe`; runner restates patrol rumor | `already_searched` notice-board inspect; runner binding cleared |
| T14 step back to runner | not reached as a repaired T13 continuation | `question`; runner rebound |

T13 after (`artifacts/pram_explicit_world_action/extended_replay/runs/20260920T150031Z_R2-MT01-AM/transcript.md`):

- interlocutor before: `tavern_runner`
- parsed/selected route: notice-board investigate / `already_searched`
- `social_probe` does **not** win
- notice-board action executes
- runner binding cleared (`interaction_mode=activity`) because that is existing inspect lifecycle
- narration describes the board, not the runner

---

## 24. Scenario-Independent Generalization Fixtures

Hard gate. Vocabulary is harbor wharf / lamp warden / tide clerk / tide marker / brass plaque / salt-stained piling / quay stair / lantern cut / glass orrery. Scene `harbor_wharf`.

| Test | Result |
| --- | --- |
| 1. Social → authored interactable | PASS — `tide_marker` wins |
| 2. Social → readable surface | PASS — plaque silt contents |
| 3. Social → visible non-interactable | PASS — PR-AK Class B piling |
| 4. Social → movement | PASS — quay stair → `lantern_cut` |
| 5. Ambiguous follow-up | PASS — `Why?` stays social |
| 6. Explicit same-NPC question | PASS — warden remains target |
| 7. Explicit different-NPC address | PASS — tide clerk binds |
| 8. Unsupported object | PASS — orrery not instantiated |
| 9. World action then social return | PASS — inspect then ask warden |
| 10. Stale topic does not mutate world action | PASS — lamp topic does not leak into inspect |
| 11. Conversational tail | PASS — `"after that"` does not grant social ownership |
| 12. Genuinely ambiguous turn | PASS — `Why?` remains useful |

HTTP tests exercise `/api/chat` with stubbed GPT.

---

## 25. Anti-Overfitting Audit

Inspected PR-AM generic production changes.

| Term | In new recover / world-object helpers? |
| --- | --- |
| notice_board / tavern_runner / stew | no |
| roster_board / guard_captain / Captain Thoran | no |
| frontier_gate / Cinderwatch / patrol / old_milestone | no |

No disguised overfitting found:

- no special `"after that"` handler;
- no phrase-specific `"glance back"` whitelist (optional adverb between glance and at);
- no notice-board-only social escape;
- no runner-specific lock clearing;
- no "clear social after every inspect" beyond existing inspect lifecycle;
- no "every noun is a world action";
- no "every non-question is non-social";
- PR-AE movement recover remains the first branch of the generalized recover.

`tests/test_explicit_world_action_social_lock_override.py::test_anti_overfitting_generic_helpers_have_no_calibration_special_case` enforces this.

Calibration identifiers appear only in the allowed Frontier Gate regression test, the campaign report, and replay artifacts.

---

## 26. Tests Added or Updated

Added: `tests/test_explicit_world_action_social_lock_override.py` (22 tests).

No existing stay/leave, dialogue-lock, inspect, social-relevance, or PR-AD–PR-AL expectations were weakened.

---

## 27. Continued Multi-Turn Replay

Scenario: `data/validation/pram_explicit_world_action/scenarios.json` (`R2-MT01-AM`)

After: `artifacts/pram_explicit_world_action/extended_replay/runs/20260920T150031Z_R2-MT01-AM/transcript.md`

Ordinary-play chain through observe, notice, travel, milestone, return, captain first-ask, PR-AK roster inspect, look-around, stew-cost, **T13 notice-board glance**, then T14 social return.

T13: notice-board world action. Not `social_probe`.

T14: `"I step back to the tavern runner and ask who last checked that board."` rebinds the runner. The spoken answer was the patrol/notice fact rather than a grounded no-answer about board readers. That is the next ordinary-play residue, not a lock regression.

---

## 28. Freeform Routing Probe

`artifacts/pram_explicit_world_action/freeform_probe/20260920T150209Z_probe.md`

| Turn | Player | Result |
| --- | --- | --- |
| 1 | ask runner stew cost | `question`; runner bound; no price invented by engine |
| 2 | inspect the notice board now | `discover_clue`; social cleared |
| 3 | read the notice again | `already_searched` |
| 4 | look at roster board the serjeant keeps watching | Class B investigate |
| 5 | follow northwest track | `scene_transition`; lock cleared |
| 6 | Why? (no active interlocutor) | not social; no lock to continue |
| 8 | inspect silver obelisk | unsupported fail-closed |
| 9 | head back | return to gate |
| 10 | ask runner who last checked that board | social rebound |
| 11 | glance at the notice board after that | `already_searched`; not `social_probe` |

---

## 29. Validation Results

| Suite | Result |
| --- | --- |
| PR-AM tests | 22 passed |
| PR-AE stay/leave | passed |
| Dialogue routing lock / continuity escape | passed |
| Intent parser | passed |
| PR-AK referenced surface | passed |
| PR-AL social relevance | passed |
| Social engine / destination / lead landing | passed |
| PR-AD authored knowledge | passed |
| PR-AF arrival | passed |
| PR-AG generalized exit | passed |
| PR-AH grounded observation | passed |
| PR-AI bound speaker | passed |
| PR-AJ provenance | passed |
| Directed social routing / world-action continuity break | passed |
| Clue / exploration / state-authority / narration-consistency | passed |
| Round #1 calibration | 13/13 (`artifacts/pram_explicit_world_action/round1_calibration/`) |
| Extended R2-MT01-AM replay | T13 repaired; T14 taken |
| Freeform routing probe | Diagnostic; glance/inspect/read override social |
| Full authoritative suite | not re-run |

Windows `PermissionError` on shared `codex_pytest_tmp` remains environmental; focused runs used `artifacts/pram_pytest_tmp*`.

Structural PASS is not semantic playability. Known protected-replay / mutation-attribution reds were not refreshed.

---

## 30. Remaining Semantic Failures

Dominant next: after repaired T13, asking who last checked the board can still emit the owned patrol/notice fact (replay T14) instead of a grounded no-answer about board readers.

Also remaining:

- Live model can invent a bowl price when the engine has no authored answer.
- Grounded-absence catalog grammar can be broken (`"I cannot answer that from what."`).
- Untargeted look-around can still repeat the same two-fact gate stock.
- Some natural paraphrases (`posted notices`) still miss `notice_board`.
- `Gate Serjeant` can resolve to `gate_guard`.
- Post-return observe can still bleed prior-scene geography.
- Authored `mutters` / `"Word is,"` envelope remains.

---

## 31. Deferred Findings

Unchanged from the handoff, plus:

- Do not add a stew price / menu / economy.
- Do not rewrite fallback grammar in this slice.
- Do not gag live-model invention with a new prompt architecture in this slice.
- Do not add a conversation-state stack.
- `Gate Serjeant` alias, `posted notices`, and look-around variety remain out of scope.

---

## 32. Recommended Next Product Slice

**Board-authorship / last-reader social question after a repaired notice-board inspect**, from continued ordinary-play T14:

> I step back to the tavern runner and ask who last checked that board.

Chosen from replay evidence immediately after repaired T13. Routing and lock were correct. The spoken answer was the patrol notice fact, not a grounded absence about who checked the board.

Do not start pricing/economics. Do not reopen PR-AK inspectability or PR-AM lock unless new evidence shows they cause that answer.

---

## 33. Git / Worktree State

The worktree is dirty and was dirty before PR-AM.

PR-AM generic production:

- `game/intent_parser.py`
- `game/interaction_routing.py`
- `game/interaction_context.py`
- `game/api.py`
- `game/referenced_surface.py`

Those files were already modified by PR-AD through PR-AL relative to HEAD. Do not treat `git diff --stat` against HEAD as a PR-AM-only footprint.

PR-AM tests/docs/tools:

- `tests/test_explicit_world_action_social_lock_override.py`
- `tools/run_pram_freeform_probe.py`
- `data/validation/pram_explicit_world_action/`
- `artifacts/pram_explicit_world_action/`
- `PR-AM_explicit_world_action_social_lock_override.md`
- `docs/NEXT_SESSION.md`

No canonical content change. Replay/probe reset `data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`.

Not committed.

---

## 34. Confidence

High on root cause, first incorrect routing decision, and T13 no longer becoming `social_probe`.

High that harbor-wharf fixtures plus live T13 prove the general contract.

High that `Why?` and explicit same-NPC questions remain social.

Medium that every natural glance/look paraphrase will bind the intended surface — short `board` still legally means the notice board, and richer wording can prefer the roster visible fact.

Medium-high that the next ordinary-play blocker is the T14 board-reader question, unless further play shows the broken no-answer grammar or look-around stock is more disruptive.
