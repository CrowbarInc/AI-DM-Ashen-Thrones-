# PR-AB - Product Integrity & Playability Audit

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Audit date: 2026-09-16

Scope: bounded product-realization audit of the assembled FastAPI/browser application. This report does not reopen established architecture or ownership decisions.

## 1. Executive Summary

Ashen Thrones was not playable at the start of this audit because `static/app.js` could not be parsed. A duplicate function-scoped `const ui` stopped all frontend initialization before state hydration or event-handler execution. The audit applied the specifically authorized one-line repair: it removed only the later duplicate declaration and retained the original shared binding.

After that repair, the shipped page parsed and initialized in a real browser. `GET /api/state` hydrated Save Status, scene/mode, character, affordances, and campaign-start state; controls were present and bound; and the browser console contained no errors or warnings during initialization. Focused API/runtime tests also passed for campaign reset/start, noncombat, combat, continuation, save/load, snapshots, state projection, and UI-mode contracts.

The audit found:

- Confirmed Product Blockers: **1**, repaired during the audit (`PRAB-001`).
- Confirmed Serious defects: **0**.
- Other confirmed product defects: **0**.
- Test gaps: **6** high-value assembled-product gaps.

The confirmed failure was frontend integration, specifically an incorrect feature-block integration in one JavaScript function. No evidence justifies architectural review. Evidence supports a small implementation cycle that permanently gates JavaScript parse validity and proves one deterministic assembled browser/API gameplay loop. The previously proposed deterministic noncombat action loop remains the highest-leverage next slice, but it should include the missing frontend startup gate rather than treating frontend parseability as assumed.

The browser's real Start Campaign control reached the model-backed opening request, but the request remained at the live provider call in this network-restricted audit environment. This is recorded as an environment block, not a product defect: startup preflight was intentionally skipped for isolated testing, and the same start path passed under controlled upstream fixtures.

## 2. Known UI Failure Disposition

### Root cause

`renderPublicState(s)` contained two `const ui = s.ui || {};` declarations in the same function scope:

- Original/current binding: `static/app.js:204`, introduced by `427ee61` (`UI Mode Separation`).
- Later duplicate: pre-repair `static/app.js:250`, introduced by `19167c1` (`CQ: Foundation Completion Assessment`).

The later commit added a legitimate scene-NPC and interaction-rendering block but redeclared an already-live identifier. JavaScript rejected the entire file during parsing, so no top-level event handlers or initial `reloadAll()` call could execute.

This is a localized incomplete/incorrect integration, not a stale compatibility layer and not a duplicated whole implementation. The original declaration is the intended shared binding because it already serves `living_enemies` and later `scene_ids`/`affordances`; the newer scene-NPC/interaction block is also current because its fields are produced by `compose_state()` and its DOM targets exist in `static/index.html`.

### Repair performed

Removed only the later duplicate declaration. The current block begins:

```javascript
const sceneNpcs = ui.scene_npcs || [];
```

No surrounding frontend code was changed.

### Verification

`node --check static/app.js` failed before repair at the duplicate declaration and passed after repair. A real browser subsequently initialized the page with populated Save Status and scene state and no console errors. No additional parse-time error surfaced after removing the duplicate.

### Why tests missed it

`tests/test_frontend_ui_mode_hardening_objective15.py` and `tests/test_start_campaign_api.py::test_play_ui_bootstrap_copy_and_no_gm_ready_placeholder` read `app.js` as text and assert that selected strings exist. They never ask a JavaScript parser to parse the complete artifact and never load the page in a browser. Both conflicting declarations therefore satisfied source-presence expectations while the assembled artifact remained unusable.

Recommended protection: add a mandatory `node --check static/app.js` smoke test, plus one browser initialization smoke that fails unless state hydration replaces `Loading...` and binds a basic control.

## 3. Product Startup Path

| Stage | Status | Evidence |
| --- | --- | --- |
| Process startup | PASS | Isolated Uvicorn process started on `127.0.0.1:8765`. |
| FastAPI startup | PASS | Application lifespan completed with preflight intentionally skipped. |
| Static page | PASS | Browser loaded `/`; CSS and JavaScript were served. |
| JavaScript parse | PASS after repair | `node --check static/app.js`; browser console clean. |
| JavaScript initialization | PASS | Event handlers ran and dynamic UI-mode selector/composer rendered. |
| State hydration | PASS | Save Status changed from `Loading...`; character, scene, mode, and affordances populated. |
| Usable controls | PASS | Start Campaign click executed its handler and issued the backend request. |

Pre-repair disposition: JavaScript parse, initialization, state hydration, and usable controls were FAIL because `app.js` never evaluated.

## 4. Campaign Start Path

| Stage | Status | Evidence / limitation |
| --- | --- | --- |
| New Campaign | PASS | Focused API tests reset runtime state, rotate the run ID, clear log/runtime overlays, and project `campaign_can_start=true`. |
| Start Campaign handler | PASS | Real browser click entered busy state and displayed `Preparing opening...`. |
| Start Campaign backend | PASS under controlled upstream | `tests/test_start_campaign_api.py` covers successful opening, persistence, duplicate rejection, and failure rollback. |
| Live provider completion | BLOCKED | Audit runtime was network-restricted and preflight-skipped; request reached primary model routing and remained pending. |
| Initial state and scene | PASS under controlled upstream | Opening tests and state projection tests verify started state, opening output, active scene, and log. |
| First player decision | PASS structurally / controlled tests | State projection supplies affordances; browser rendered them. Live post-opening decision was not run because live opening was environment-blocked. |

No implementation defect was demonstrated in this path after `PRAB-001`. Live-AI availability remains an expected product gate.

## 5. Frontend/API Contract Audit

| UI control/function | Frontend handler | API endpoint | Backend owner | Contract status | Confirmed issue |
| --- | --- | --- | --- | --- | --- |
| Initial load | `loadState`, `loadLog` | `GET /api/state`, `GET /api/log` | `game/api.py` projection/log routes | PASS | None after repair |
| New Campaign | click handler | `POST /api/new_campaign` | campaign reset + API route | PASS | None |
| Start Campaign | click handler | `POST /api/start_campaign` | opening turn pipeline | PASS under fixture; live blocked | None confirmed |
| Send chat | `sendChat` | `POST /api/chat` | authoritative chat/turn pipeline | PASS under focused tests | None |
| Action helper | `submitAction`, `submitDirect` | `POST /api/action` | action/combat/noncombat pipeline | PASS | None |
| Suggested action | `submitExplorationAction` | `POST /api/action` | canonical affordance/action pipeline | PASS | None |
| Reset combat | click handler | `POST /api/reset_combat` | API/storage | PASS | None |
| Response mode | `setResponseMode` | `POST /api/response_mode` | API/session persistence | PASS | None |
| Snapshot create/load | click/delegated click | `POST /api/snapshots`, `/api/snapshots/load` | storage snapshot owner | PASS | None |
| Campaign/scene author forms | `saveCampaign`, `saveScene`, `activateScene` | `POST /api/campaign`, `/api/scene`, `/api/scene/activate` | API/storage | Contract-aligned | Not behaviorally exercised in this player-loop audit |
| Character import | `importSheet` | `POST /api/import_sheet` | API/storage | Contract-aligned | Not behaviorally exercised |

Static DOM checks found no duplicate HTML IDs. Every literal `$('<id>')` reference maps to a static element or an intentionally dynamic composer element; `uiModeSelect` is created by frontend initialization.

## 6. Representative Gameplay Audit

### Noncombat

PASS under focused integration tests. The tested HTTP/chat and action paths traverse normalization, exploration/social/noncombat resolution, authoritative state updates, player-facing emission, persistence, and subsequent state projection. `tests/test_exploration_resolution.py`, `tests/test_noncombat_runtime_integration.py`, and `tests/test_playability_smoke.py` passed.

This establishes representative behavior, not comprehensive narrative or rules correctness.

### Combat

PASS under focused integration tests. `POST /api/action` initiative reaches the canonical combat engine and returns the expected resolution shape; attack, spell, condition, and end-turn owners pass their focused checks in `tests/test_combat_resolution.py`. Browser controls and their handlers exist and align with the endpoint schema.

### Continuation / next decision

PASS under controlled tests. Successful action/chat handlers call `reloadAll()`, and authoritative `/api/state` plus `/api/log` become the next rendered source. Multi-turn playability smoke tests passed. A complete live browser sequence beyond Start Campaign was not demonstrated because the audit environment could not complete the live provider call.

## 7. Persistence Audit

Representative initialization, mutation persistence, active-scene save/load, clue/world/character persistence, snapshots, reset, and projection after reload passed focused tests.

User runtime data protection:

- Pytest cases used `tmp_path`/`--basetemp` and monkeypatched storage paths.
- The browser/Uvicorn smoke redirected every mutable runtime path to `codex_pr_ab_runtime`.
- Authored scene templates were read from the repository but not modified.
- Existing files under `data/` were not written by the audit.

No stale-schema or reload defect was reproduced.

## 8. Confirmed Defect Register

| ID | Severity | Area | Description | Evidence | Runtime impact | Owner | Existing coverage | Smallest repair boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PRAB-001 | PRODUCT BLOCKER | Frontend integration | Duplicate function-scoped `const ui` in `renderPublicState` made all of `app.js` unparsable. | Browser console; pre-repair `node --check`; git blame at original line 204 and duplicate line 250. | UI renders static HTML but never hydrates or accepts input. | `static/app.js` frontend integration | Source-text assertions only; no parser/browser gate | Delete only the later duplicate declaration. **Performed.** |

Confirmed Serious defects: none.

## 9. Suspected / Unconfirmed Findings

| Finding | Confidence | Why not confirmed | Follow-up |
| --- | --- | --- | --- |
| Runtime provider calls may leave `Preparing opening...` visible for a long time when the provider is unreachable. | SUSPECTED | The audit intentionally skipped preflight and ran in a network-restricted environment; this does not represent a supported healthy-preflight launch. | Exercise provider timeout/failure handling in a controlled test before classifying. |
| Author-mode campaign/scene editing and character import could contain assembled-browser defects. | SUSPECTED | URL/method/DOM contracts align, but these non-core player-loop controls were not behaviorally exercised. | Add only if those workflows become milestone-critical. |

## 10. Test Blind-Spot Register

| Behavior | Current coverage | Why insufficient | Smallest recommended regression test |
| --- | --- | --- | --- |
| JavaScript parses | String-presence tests | Conflicting valid snippets can make the whole artifact invalid. | Run `node --check static/app.js` in pytest/CI. |
| Browser initializes | None at assembled-page level | API and source tests do not execute top-level JS. | Load `/`; assert no console/page errors and hydrated Save Status. |
| Initial state hydration | Backend projection tests | They do not prove frontend field/DOM compatibility. | Browser assert scene/mode and character appear after `/api/state`. |
| Campaign reset/start UI | Endpoint tests plus source strings | They do not prove click -> request -> render. | Browser click New/Start with controlled upstream; assert opening and state transition. |
| One deterministic noncombat loop | Many owner/integration tests | No single mandatory product smoke proves browser input through next decision without live AI. | Controlled browser/API smoke using existing deterministic owners and fixtures. |
| Save/load after player mutation | Persistence tests | No assembled UI-to-persistence-to-reload assertion. | Mutate, snapshot/reload, then assert projected state and next decision. |

Combat has meaningful API integration coverage, but a future browser smoke could cheaply verify that initiative/action/end-turn controls remain wired. It is lower priority than the six gaps above.

## 11. Existing Test / Environment Status

| Command / check | Outcome |
| --- | --- |
| `git status --short` | Pre-existing modifications/untracked files observed in `docs/README.md`, `run.py`, `.venv-broken/`, PR-AA and historical artifacts/tests; preserved. |
| `node --check static/app.js` before repair | FAIL: duplicate `ui` at line 250. |
| `node --check static/app.js` after repair | PASS. |
| Focused campaign/combat/persistence/frontend-contract slice | PASS: 48 tests. |
| Focused noncombat/playability/opening/persistence slice | PASS: 101 tests. |
| Total focused tests in this audit | PASS: 149 tests; one Starlette/httpx deprecation warning per invocation. |
| Real browser initialization | PASS: state hydrated, controls/affordances rendered, console clean. |
| Real browser Start Campaign handler | PASS through primary model routing; live completion BLOCKED by restricted network/preflight-skipped environment. |

The PR-AA broad-fast-lane timeout remains existing evidence and was not rerun.

## 12. Architectural Friction

No architectural friction was demonstrated. The blocker arose from missing assembled-artifact validation, not from contradictory ownership, state authority, persistence, or realization contracts. Existing backend owners composed successfully in focused runtime tests.

## 13. Product Blocker Backlog

1. `PRAB-001` duplicate frontend declaration **(repaired)**
   -> unlocks JavaScript evaluation, event binding, state hydration, and all browser controls
   -> next blocked behavior was live provider completion, which is environment-gated rather than a confirmed implementation blocker.

There are no remaining confirmed Product Blockers from this audit.

## 14. Recommended PR-AC

Recommended cycle name: **PR-AC - Deterministic Product Loop and Frontend Startup Gate**

The deterministic noncombat action loop remains the highest-leverage next slice. PR-AC should pair it with the smallest catastrophic frontend regression gate discovered here:

1. Add mandatory JavaScript syntax validation for `static/app.js`.
2. Add one lightweight assembled-page initialization smoke using the existing application and controlled upstream behavior.
3. Demonstrate one deterministic noncombat player action from presented decision through authoritative mutation, persistence, refreshed projection, and next decision.
4. Include one save/reload assertion after the mutation.

Do not introduce a broad frontend framework, large browser suite, alternate provider, rules expansion, architecture redesign, or historical-test cleanup.

## 15. Milestone Position

| Milestone | Position | Advancement blocker |
| --- | --- | --- |
| Executable Chassis | ACHIEVED after `PRAB-001` repair | Permanent parse/startup regression gate is still missing. |
| Minimal Playable Loop | NOT YET EVIDENCED AS A REPEATABLE PRODUCT GATE | Need one deterministic assembled action -> mutation -> persistence -> next-decision proof independent of live provider availability. |
| Internal Prototype | NOT YET | Depends on a repeatable minimal playable loop and catastrophic browser regression protection. |
| Player-Testable Alpha | NOT YET | Depends on internal prototype evidence, broader resilience, and live-provider operational validation. |

## 16. Handoff Package

**Recommended cycle name:** PR-AC - Deterministic Product Loop and Frontend Startup Gate

**Objective:** establish a mandatory, repeatable product smoke proving that the shipped frontend parses and initializes and that one deterministic noncombat choice traverses existing runtime owners, mutates authoritative state, persists, reprojects, and presents the next decision.

**Confirmed defect addressed:** PRAB-001 should be retained exactly as repaired and protected against recurrence.

**Relevant files:**

- `static/app.js`
- `static/index.html`
- `game/api.py`
- `game/noncombat_resolution.py`
- `game/scene_actions.py`
- `game/affordances.py`
- `game/storage.py`
- `tests/test_frontend_ui_mode_hardening_objective15.py`
- `tests/test_start_campaign_api.py`
- `tests/test_exploration_resolution.py`
- `tests/test_noncombat_runtime_integration.py`
- `tests/test_save_load.py`

**Acceptance criteria:**

- `node --check static/app.js` is mandatory and passing.
- Browser load produces no parse/page error and replaces `Save Status: Loading...` with hydrated state.
- New Campaign and controlled Start Campaign reach an initial scene and first decision.
- One deterministic noncombat input reaches the current normalization/resolution owners.
- The action produces a player-visible result and an authoritative mutation.
- Reloaded state preserves the mutation and presents a next decision.
- Tests use isolated temporary runtime data and do not require a paid/live provider.

**Out of scope:** broad refactors, architecture reconciliation, Final Emission redesign, frontend replacement, new AI providers, rules/content expansion, historical report edits, broad suite cleanup, and comprehensive browser QA.

**Unresolved questions:** choose the smallest existing controlled upstream fixture or deterministic engine-owned action that can drive the browser smoke without introducing a parallel gameplay path. Confirm provider timeout/error UX separately before treating it as a defect.
