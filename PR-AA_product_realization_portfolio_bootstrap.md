# PR-AA - Product Realization Portfolio Bootstrap

Workspace: `C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm`

Report location decision: the repository has an established root-level campaign/report pattern (`AR-*`, `CQ*`, `CP*`, etc.) plus supporting documentation under `docs/`. Because PR-AA opens a new era-level portfolio rather than updating one subsystem guide, this report is placed at the repository root beside the prior campaign reports.

## 1. Executive Summary

The project can be imported and the FastAPI application object can be constructed locally with upstream preflight skipped. Focused product, contract, persistence, API, scenario-spine, synthetic, content-lint, and governance slices ran successfully. The documented fast lane (`pytest -m "not transcript and not slow"`) did not finish within 300 seconds and showed multiple failures before timeout, so the full fast lane is not a clean Product Realization gate right now.

The project currently runs as a local FastAPI/browser application through `run.py` and `game/api.py`, but normal campaign start/chat paths are live-AI-oriented and can be blocked by upstream preflight or credentials. Some engine-authored paths can produce player-facing output without GPT, especially invalid/blocked/pending-check outcomes and app-side combat control messages.

A meaningful complete gameplay loop exists architecturally and in tested pieces, but not yet as a narrow, AI-independent, repeatable operator slice that demonstrates two or more player decisions end to end through authoritative state mutation, event/log/trace evidence, and next-decision presentation. The strongest current product capabilities are state authority, action/affordance normalization, noncombat resolution contracts, combat mechanics, persistence envelopes/snapshots, final-emission/provenance machinery, scenario-spine and synthetic validation harnesses, and local UI/API projection.

The most important missing integration is an AI-independent deterministic playable transaction harness that exercises the runtime spine through existing owners instead of stopping at unit contracts or requiring live GPT. The recommended first implementation slice is:

`PR-AB - Gameplay: Deterministic Noncombat Action Loop`

Primary lane: Gameplay. Secondary lanes: Tooling & Developer Experience, Persistence & Reliability, Content & World, UX & Player Interface.

Implementation can proceed without additional user-supplied files or decisions. The slice should use existing scene action, noncombat resolution, state authority, CTIR/trace, persistence, and API projection boundaries. It should not require live AI.

## 2. Investigation Scope and Evidence

Key directories inspected:

| Area | Paths |
| --- | --- |
| Runtime source | `game/` |
| Browser UI | `static/index.html`, `static/app.js`, `static/styles.css` |
| Runtime/content data | `data/`, `data/scenes/` |
| Tests | `tests/` |
| Tools and scripts | `tools/`, `scripts/` |
| Authoritative docs | `docs/` |
| Root campaign reports | `AR-*`, `CQ*`, `CP*`, `CV*`, `CX*` |
| CI | `.github/workflows/` |

Key documents inspected:

| File | Evidence type | Use |
| --- | --- | --- |
| `docs/README.md` | Documentation evidence | Setup, runtime command, app purpose, current supported mechanics, doc index |
| `tests/README_TESTS.md` | Documentation evidence | Supported test lanes, ownership rules, command cheat sheet |
| `docs/system_overview.md` | Documentation evidence | Core loop and owner responsibilities |
| `docs/state_authority_model.md` | Documentation evidence | Runtime state domains and mutation ownership |
| `docs/ruleset_contract_registry.md` | Documentation evidence | Action, combat, noncombat, state, validation, realization contracts |
| `docs/backend_contract_registry.md` | Documentation evidence | Backend/model routing, preflight, diagnostics boundaries |
| `docs/runtime_persistence_envelope.md` | Documentation evidence | Runtime envelope, save/load, restore, compatibility |
| `docs/realization_cursor_handoff.md` | Documentation evidence | Realization/final-emission risk and stop-point guidance |
| `AR-CA_campaign6_chassis_strategy_closeout.md` | Documentation evidence | Reconciliation Era closeout and implementation-first posture |
| `AR-BZ_chassis_validation_and_future_evolution_assessment.md` | Documentation evidence | Chassis validation and remaining architectural horizon |
| `CQ_foundation_completion_assessment_discovery.md` | Documentation evidence | Prior foundation/feature readiness assessment |

Key source files inspected:

| File | Evidence type | Use |
| --- | --- | --- |
| `run.py` | Direct repository evidence | Runtime launch path |
| `game/api.py` | Direct repository evidence | FastAPI app, action/chat/start campaign, state projection, orchestration spine |
| `game/api_turn_support.py` | Direct repository evidence | Final player-facing turn support and trace append |
| `game/noncombat_resolution.py` | Direct repository evidence | Canonical noncombat classification, delegation, normalized contract |
| `game/scene_actions.py` | Direct repository evidence | Action normalization |
| `game/affordances.py` | Direct repository evidence | Available action generation |
| `game/combat.py` | Direct repository evidence | Initiative, attacks, spells, skills, turn advancement |
| `game/storage.py` | Direct repository evidence | Runtime I/O, envelopes, snapshots, data bootstrap |
| `game/persistence_contract.py` | Direct repository evidence | Envelope validation and failure categories |
| `static/index.html`, `static/app.js` | Direct repository evidence | Browser-facing play, action helper, affordances, start campaign |
| `data/session.json`, `data/combat.json`, `data/scenes/frontier_gate.json` | Runtime/content evidence | Current persisted runtime shape and initial content |

Commands executed:

| Command | Result | Evidence |
| --- | --- | --- |
| `git status --short` | Initial tracked files clean; pre-existing untracked docs/artifacts present | Runtime evidence |
| `git log --oneline -5` | Latest commit: `2729189 Merge Reconciliation Era` | Git history evidence |
| `python --version` | Failed: `python` not on PATH | Runtime evidence |
| `py -3 --version` | Failed: `py` not on PATH | Runtime evidence |
| Bundled `python.exe --version` | Passed: Python 3.12.13 | Runtime evidence |
| Import smoke with `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` | Passed: app title `Ashen Thrones AI GM`; composed state had scene; `campaign_can_start=False` in current state | Runtime evidence |
| `pytest --collect-only -m "not transcript and not slow"` | Passed collect-only; large fast-lane collection succeeded | Test evidence |
| `tools/run_content_lint.py` | Passed with `scenes_checked=58 errors=0 warnings=164` | Validation evidence |
| Product owner slice | Passed: 65 tests | Test evidence |
| Persistence slice | Passed: 28 tests | Test evidence |
| API/start/playability-tool slice | Passed: 18 tests | Test evidence |
| Scenario/synthetic harness slice | Passed: 79 tests | Test evidence |
| Split-owner matrix check | Passed: rows=16 dashboard=15 fem=15 legacy=1 sealed=6/6 | Validation evidence |
| Contract/authority/coverage registry slice | Passed: 58 tests | Test evidence |
| `tools/validation_coverage_audit.py --strict` | Passed registry validation; summary reports missing optional surfaces by feature | Validation evidence |
| Full fast lane | Timed out at 300 seconds; failures observed before timeout | Test evidence |

Areas not fully inspected:

| Area | Reason |
| --- | --- |
| Full test suite | Too large for this discovery pass; documented fast lane timed out at 300 seconds |
| Live `python run.py` server process | Would start a long-running dev server and trigger startup preflight behavior; import/API evidence was safer |
| Live OpenAI calls | Prohibited by cycle constraints and would require credentials/paid external service |
| Historical PDF/DOCX contents | Not required to determine current code/runtime ownership |
| All artifacts under `artifacts/` | Large generated/historical surface; sampled and used where relevant |

Conclusion evidence labels used below:

- Direct repository evidence: code, data, CI, docs present in the repository.
- Runtime evidence: commands executed in this pass.
- Test evidence: pytest/tool results from this pass.
- Documentation evidence: stated architecture or workflow doctrine.
- Inference: conservative conclusion from repository patterns when no direct runtime path was executed.

## 3. Current Build, Test, and Runtime State

Dependency installation:

| Command | Status |
| --- | --- |
| `python -m venv .venv` | Documented in `docs/README.md`; not executed |
| `.venv\Scripts\Activate.ps1` | Documented; not executed |
| `pip install -r requirements.txt` | Documented; not executed |

Dependency observations:

- `requirements.txt` lists `fastapi`, `uvicorn`, `openai`, `pydantic`, `python-multipart`, `python-dotenv`, and `pytest`.
- System `python`, `py`, and `pytest` were not available on PATH in this environment.
- Bundled Codex Python worked with `PYTHONPATH=.\.venv\Lib\site-packages`.

Build/type/lint:

| Category | Command | Result |
| --- | --- | --- |
| Build | No package build command identified | Not applicable for current Python/local static app |
| Type checking | No documented type-check command found | Not run |
| Lint | No general lint command found | Not run |
| Content lint | Bundled Python `tools\run_content_lint.py` | Passed with warnings |

Tests and validators:

| Command | Outcome | Notes |
| --- | --- | --- |
| `pytest --collect-only -m "not transcript and not slow" -q` | Passed | Fast-lane collection succeeded |
| Focused product slice | Passed 65 tests | Noncombat, combat, affordance, runtime schema |
| Focused persistence slice | Passed 28 tests | Envelope/save/load/snapshots |
| Focused API/start/playability-tool slice | Passed 18 tests | Startup path and validation runner tool tests |
| Focused scenario/synthetic slice | Passed 79 tests | Scenario spine and fake-GM synthetic harness |
| Focused contract/authority slice | Passed 58 tests | Contract registry, state authority, validation-layer, coverage registry |
| `scripts\check_split_owner_acceptance_matrix.py` | Passed | Governance contract OK |
| `tools\validation_coverage_audit.py --strict` | Passed | Registry schema OK |
| `pytest -m "not transcript and not slow" -q --tb=short` | Timed out after 300 seconds | Multiple failures appeared before timeout |

Known fast-lane failure identities from `.pytest_cache\v\cache\lastfailed` after the timed-out run included final-emission, scene-state anchoring, golden replay, recurrence/reporting, compatibility import governance, and ownership write-path tests. Because the command timed out, this is incomplete failure evidence and should not be treated as a full failure inventory.

Runtime launch:

| Path | Evidence |
| --- | --- |
| `python run.py` | Documented in `docs/README.md`; launches `game.api:app` on `127.0.0.1:8000` with reload by default |
| `game.api:app` import | Passed locally with upstream preflight skipped |
| Static UI | `app.mount('/static', StaticFiles(...))`; root route serves `static/index.html` |
| API state | `compose_state()` executed in import smoke |

Required environment variables and credentials:

| Variable | Role |
| --- | --- |
| `OPENAI_API_KEY` | Required for live OpenAI narration per docs |
| `MODEL_NAME`, `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, `RETRY_ESCALATION_MODEL_NAME` | Optional model routing configuration |
| `ENABLE_MODEL_ROUTING` | Optional model routing switch |
| `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT` | Test/local skip for startup preflight |
| `UVICORN_RELOAD` | Runtime reload control in `run.py` |

Successful execution paths:

- FastAPI app import.
- Client-visible state composition.
- Content lint validation with no errors.
- Focused owner tests for noncombat/combat/affordance/schema.
- Persistence envelope/save/load/snapshot tests.
- API/start campaign and playability-runner tests.
- Scenario-spine and synthetic fake-GM harness tests.
- Governance split-owner and contract registry checks.

Failed or blocked execution paths:

- System `python`, `py`, and `pytest` were unavailable on PATH.
- Full documented fast lane timed out at 300 seconds and had failures before timeout.
- Current persisted state reported `campaign_can_start=False`, meaning live campaign start is not currently available from the existing session/log state without reset/new campaign.
- Live `/api/start_campaign` can be blocked by upstream preflight when health is bad; the endpoint explicitly returns `503` if `manual_testing_blocked` is true.
- Live GPT calls were not executed by design.

Product Realization blockers:

- No blocker for a narrow, AI-independent implementation slice.
- Full fast-lane instability/time cost is a blocker to using the entire fast lane as the first Product Realization acceptance gate.
- Live AI dependency is a blocker for treating normal `/api/start_campaign` or `/api/chat` as the first deterministic product slice.

Obsolete or competing entry points:

- `run.py` and `game.api:app` are the primary runtime entry points.
- `tools/run_synthetic_session.py`, `tools/run_playability_validation.py`, and `tools/run_scenario_spine_validation.py` are validation/tooling entry points, not alternate product runtimes.
- Historical/generated artifacts under `artifacts/`, `audits/`, `history/`, and compatibility/test helper backups are evidence surfaces, not current runtime owners.

## 4. Product Capability Inventory

| Portfolio Lane | Capability | Status | Intended Owner | Primary Files | Runtime Evidence | Test Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Gameplay | Session initialization/loading | Operational | Storage/session/API | `game/storage.py`, `game/defaults.py`, `game/campaign_state.py`, `game/api.py` | `compose_state()` loaded session | Persistence/API slices passed | Runtime files are envelope-backed |
| Gameplay | Client-visible state composition | Operational | API projection | `game/api.py::compose_state`, `game/state_channels.py` | Import smoke composed state | API/UI tests passed | Publication view, not truth store |
| Gameplay | Action normalization | Operational | Scene/action owner | `game/scene_actions.py`, `game/schema_contracts.py` | Source inspected | Product slice passed | Legacy strings/dicts adapt to canonical shape |
| Gameplay | Available action discovery | Operational | Affordance owner | `game/affordances.py` | UI consumes `ui.affordances` | Affordance tests passed | Produces bounded/pruned action rows |
| Gameplay | Noncombat resolution contract | Operational | Noncombat resolution owner | `game/noncombat_resolution.py` | Source inspected | Noncombat and CTIR tests passed | Versioned framework `2026.04.noncombat.v1` |
| Gameplay | Exploration resolution | Partial | Exploration owner | `game/exploration.py`, `game/api.py` | API route delegates to noncombat seam | Exploration/noncombat tests passed | Normal live narration still goes through GPT unless pending/blocked path |
| Gameplay | Social resolution | Partial | Social/interaction owners | `game/social.py`, `game/interaction_context.py`, `game/api.py` | API route delegates | Social tests exist; focused social suite not run | Rich but coupled to final-emission/social validation surfaces |
| Gameplay | Combat initiative/attack/spell/skill/end turn | Operational | Combat owner | `game/combat.py`, `game/models.py`, `game/api.py` | Source inspected | Combat tests passed | App-side messages exist for initiative/end-turn cases |
| Gameplay | Turn sequencing | Partial | Combat/API | `game/combat.py`, `game/api.py` | Source inspected | Combat tests passed | Combat sequencing exists; general noncombat multi-decision loop not proven by runtime command |
| Gameplay | Consequence application | Partial | API/world/exploration/social/combat | `game/api.py`, `game/world.py`, `game/exploration.py`, `game/social.py` | Source inspected | Focused slices passed | Needs a narrow visible transaction harness |
| Gameplay | Continuation to next decision | Partial | API/UI/affordances | `game/api.py`, `static/app.js`, `game/affordances.py` | `compose_state()` exposes affordances | API/affordance tests passed | Not yet proven as AI-independent loop acceptance |
| AI Experience | Live GPT adapter | Implemented but not integrated | GM/model-call owner | `game/gm.py`, `game/model_routing.py` | Not called | Model routing tests exist; not run in focused set | Requires credentials for live success |
| AI Experience | Model routing/config | Operational | Model routing/config owner | `game/model_routing.py`, `game/config.py` | Source/docs inspected | Backend registry docs cite tests | Current provider only |
| AI Experience | Upstream preflight/run gate | Operational | Upstream preflight/run-gate owners | `game/api_upstream_preflight.py`, `game/upstream_dependent_run_gate.py` | Import smoke skipped preflight | API/start tests passed | Can block manual live start |
| AI Experience | Prompt/context assembly | Operational | Prompt/CTIR owners | `game/prompt_context.py`, `game/gm.py`, `game/ctir_runtime.py` | Source inspected | CTIR/prompt tests exist; CTIR focused tests passed | Consumer of truth, not mechanics owner |
| AI Experience | Deterministic/fake backend execution | Test-only | Test/synthetic harness | `tools/run_synthetic_session.py`, `tests/helpers` | Not manually run as CLI | Synthetic tests passed | Useful harness, not product runtime |
| AI Experience | Final realization/final emission | Operational but high-risk | Final Emission/realization owners | `game/final_emission_gate.py`, `game/api_turn_support.py`, `game/realization_provenance.py` | Source inspected | Many tests exist; full fast lane failures include this area | Strong infrastructure but current broad fast lane is not green |
| Content & World | Authored scenes | Partial | Content/schema/validation owners | `data/scenes/*.json`, `game/validation.py`, `game/content_lint.py` | `frontier_gate` inspected | Content lint passed with warnings | 58 scenes, many weak/unreachable warnings |
| Content & World | Starter scene | Operational | Content owner | `data/scenes/frontier_gate.json` | Inspected | Opening tests exist; some full-fast failures involve opening | Strong seed facts/addressables/interactable |
| Content & World | World state and progression | Partial | World/world_progression owners | `game/world.py`, `game/world_progression.py`, `data/world.json` | `compose_state()` loaded world | World tests exist; not all run | Progression backbone documented |
| Content & World | Content authoring workflow | Partial | Content lint/tooling owners | `tools/run_content_lint.py`, `docs/content_lint_pipeline.md` | Tool passed with warnings | Content-lint tests exist | Warnings should guide later content work |
| UX & Player Interface | Browser UI | Operational | UI/API projection | `static/index.html`, `static/app.js`, `static/styles.css` | Source inspected | UI mode tests passed | Local browser UI exists |
| UX & Player Interface | Player input/chat | Partial | UI/API | `static/app.js`, `game/api.py` | Source inspected | API tests passed | Normal chat may require GPT |
| UX & Player Interface | Suggested action buttons | Operational | UI/affordances/API | `static/app.js`, `game/affordances.py`, `game/api.py` | Source inspected | Affordance/API tests passed | Good candidate surface for deterministic loop |
| UX & Player Interface | Debug/trust surface | Partial | UI mode/debug trace owners | `static/app.js`, `game/api.py`, `game/state_channels.py` | Debug endpoint/source inspected | UI/debug tests passed | Operator-oriented, not player-polished |
| Tooling & DX | Test lane documentation | Operational | Test workflow docs | `tests/README_TESTS.md`, `docs/feature_lane_verification.md` | Docs inspected | Contract checks passed | Strong but large |
| Tooling & DX | Content lint | Operational | Content tooling owner | `tools/run_content_lint.py` | Tool passed | Tests exist | Warnings are actionable |
| Tooling & DX | Scenario-spine validation | Operational | Scenario-spine tooling owner | `tools/run_scenario_spine_validation.py`, `game/scenario_spine.py` | Not CLI-run | Scenario tests passed | Good validation substrate |
| Tooling & DX | Synthetic player harness | Operational | Synthetic tooling/tests | `tools/run_synthetic_session.py`, `tests/test_synthetic_*` | Not CLI-run | Synthetic tests passed | Fake-GM deterministic mode exists |
| Tooling & DX | Golden replay/projection | Partial | Replay/projection owners | `tests/test_golden_replay*.py`, `tests/helpers/golden_replay*` | Not fully run | Full fast failures include replay/projection | Valuable but currently noisy/risky |
| Persistence & Reliability | Runtime envelopes | Operational | Persistence/storage owners | `game/persistence_contract.py`, `game/storage.py` | Data inspected | Persistence tests passed | `session.json` and `combat.json` envelope shape |
| Persistence & Reliability | Save/load | Operational | Storage owner | `game/storage.py` | Source inspected | Save/load tests passed | Atomic runtime saves |
| Persistence & Reliability | Snapshots | Operational | Storage owner | `game/storage.py`, API snapshot endpoints | Source inspected | Snapshot tests passed | Validate-first restore documented |
| Persistence & Reliability | Debug trace persistence | Operational | API/storage | `game/api.py`, `game/api_turn_support.py`, `game/storage.py` | Source inspected | API tests passed | Existing traces can grow during runs |
| Persistence & Reliability | Replay/deterministic reproduction | Partial | Replay/scenario owners | `tests/test_golden_replay*.py`, `data/validation/` | Not fully run | Scenario/synthetic passed; fast lane replay failures observed | Use focused replay only for first slice |
| Performance & Scale | Latency tracking | Partial | API/tooling | `game/api.py`, `tests/test_manual_play_latency.py` | Source inspected | Not run | Latency buckets exist |
| Performance & Scale | Benchmarks/profiling | Missing | Not established | None found | None | None | No measured performance concern for PR-AB |
| Long-Term Evolution | Future providers | Contract or scaffold only | Backend contract/model routing | `docs/backend_contract_registry.md`, `game/model_routing.py` | Docs inspected | Not run | Current architecture ready; no second provider |
| Long-Term Evolution | Alternate rulesets | Contract or scaffold only | Ruleset contract/docs | `docs/ruleset_contract_registry.md` | Docs inspected | Not run | Current PF1e-inspired engine only |
| Long-Term Evolution | Hosted/multiplayer/public APIs | Missing | Not established | Docs mention future review | None | None | Dormant |

## 5. Intended Minimal Playable Loop

The loop implied by current architecture:

| Step | Responsibility | Owner | Contract | Status |
| --- | --- | --- | --- | --- |
| 1 | Start/load runtime session and authored content | `game.storage`, `game.api` | Persistence envelope, content validation | Confirmed |
| 2 | Compose current player-visible state and action choices | `game.api`, `game.affordances`, `game.journal` | State authority, affordance schema, UI mode projection | Confirmed |
| 3 | Receive player input or selected action | `static/app.js`, `game.api` | `ActionRequest`, `ChatRequest`, UI mode policy | Confirmed |
| 4 | Normalize/classify action | `game.scene_actions`, `game.intent_parser`, `game.interaction_routing` | Action normalization, route selection | Confirmed |
| 5 | Resolve mechanics through engine owner | `game.combat`, `game.noncombat_resolution`, `game.exploration`, `game.social` | Ruleset contract registry RCR-04/05/07 | Confirmed |
| 6 | Apply authoritative state mutation | `game.api` delegating to domain owners | State authority domains and cross-domain allow-list | Confirmed |
| 7 | Snapshot resolved-turn meaning | `game.ctir_runtime`, `game.ctir` | CTIR contract | Confirmed |
| 8 | Build prompt/narration context | `game.prompt_context`, `game.gm` | Backend contract BCR-04; prompt as consumer | Confirmed |
| 9 | Produce player-facing expression | `game.gm` live/fallback path or engine-authored prompt; `game.final_emission_gate` | Backend and realization contracts | Confirmed for pieces; tentative for deterministic product loop |
| 10 | Apply final-emission legality/packaging | `game.api_turn_support`, `game.final_emission_gate` | Final emission boundary, provenance | Confirmed |
| 11 | Apply post-GM adoption where allowed | `game.api`, domain owners | Transitional gateway traces/state authority | Confirmed but friction-bearing |
| 12 | Persist session/combat/world/log/debug trace | `game.storage`, `game.api` | Persistence envelope, append log/debug trace | Confirmed |
| 13 | Return projected state and next choices | `game.api`, `static/app.js` | UI mode projection and affordances | Strongly inferred from source and tests |

Ruleset participation:

- Combat rules live in `game/combat.py` and condition helpers.
- Noncombat rules are classified and normalized by `game/noncombat_resolution.py`, delegating to exploration/social owners.
- Current ruleset identity is PF1e-inspired and deterministic, not a pluggable ruleset loader.

AI participation:

- AI may generate expression and structured proposals.
- AI must not own authoritative state or mechanics.
- Live AI is used for normal narration, but engine-authored no-GPT responses exist for pending checks, offscene social targets, initiative, and some end-turn cases.

State mutation:

- Runtime truth is separated into `world_state`, `scene_state`, `interaction_state`, `player_visible_state`, and `hidden_state`.
- GPT-originated text must not back-write truth without validated gateway/adoption paths.

Event generation, diagnostics, and provenance:

- Debug traces are appended through `append_debug_trace`.
- Turn traces include `turn_stage_order`, normalized action, resolution, scenes before/after, clue/world updates, latency, and response status.
- Realization/fallback provenance is owned by realization/final-emission helpers.

Persistence:

- `session.json` and `combat.json` use versioned envelopes.
- `session_log.jsonl` records turns.
- Snapshots support save slots and restore.

Continuation:

- API responses and `compose_state()` expose current state plus affordances, enabling a next decision.
- This continuation is not yet packaged as a single deterministic product smoke that proves two or more decisions without live AI.

## 6. Minimal Playable Loop Gap Analysis

| Loop Step | Intended Owner | Current State | Missing Work | Blocking Dependencies | Relevant Lane | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| Load session/content | Storage/API | Operational | None for first slice | None | Gameplay/Persistence | High |
| Present valid action | Affordances/API/UI | Operational | Pick one known action fixture for a deterministic smoke | Minimal content choice | Gameplay/UX | High |
| Submit action | UI/API | Operational | Use existing `/api/action` or a narrow local harness | None | Gameplay/UX | High |
| Normalize action | Scene actions | Operational | None | None | Gameplay | High |
| Resolve deterministic noncombat action | Noncombat/exploration/social | Partial to operational | Choose action that resolves without GPT or live roll ambiguity | Need authored scene/interactable fixture | Gameplay/Content | High |
| Mutate authoritative state | API/domain owners | Partial | Exercise one mutation and assert state/log/trace evidence | Avoid post-GM text-derived adoption | Gameplay/Persistence | Moderate |
| Produce player-facing result | Engine or realization path | Partial | Use AI-independent output path for the slice | Avoid live GPT | Gameplay/AI Experience | High |
| Emit diagnostics/provenance | API/final emission/trace owners | Operational in pieces | Define acceptance fields for transaction trace | None | Tooling/Reliability | High |
| Persist and reload | Storage | Operational | Assert state survives reload/compose | None | Persistence | High |
| Continue to next decision | API/affordances/UI | Partial | Assert next `compose_state()` includes action options or explicit terminal reason | Minimal content | Gameplay/UX | Moderate |
| Run as repeatable command | Tooling/tests | Partial | Add focused smoke/CLI or pytest integration entry | None | Tooling | High |

Smallest missing links:

- A deterministic, AI-independent runtime slice that performs one selected authored action through the real transaction spine.
- Acceptance checks that prove state mutation, log/debug trace, next state projection, and no live GPT dependency.
- A clear operator command for that slice.

Architectural friction vs missing implementation:

- Missing implementation: deterministic end-to-end gameplay smoke around existing seams.
- Friction: normal narrative paths assume GPT for player-facing expression; first slice should avoid redesign by choosing an existing engine-authored or deterministic no-GPT path.
- Friction: post-GM adoption is trace-heavy and risk-classed; first slice should avoid relying on model text adoption.

## 7. Architectural Readiness by Area

| Area | Classification | Evidence |
| --- | --- | --- |
| Runtime orchestration | Ready with minor clarification | `game/api.py` owns transaction spine; docs confirm one runtime transaction spine; broad but usable |
| State ownership | Ready | `docs/state_authority_model.md`, `game/state_authority.py`, focused tests passed |
| Action ownership | Ready | `game/scene_actions.py`, `game/affordances.py`, ruleset registry RCR-02/RCR-03, tests passed |
| Ruleset integration | Ready with minor clarification | Combat/noncombat contracts exist; no formal alternate ruleset loader |
| AI backend integration | Partially ready | Current provider adapter/routing/preflight ready; live credentials/upstream not deterministic |
| Realization | Partially ready | Rich final-emission/provenance stack; full fast lane failures include this area |
| Event routing | Partially ready | Turn/debug traces and logs exist; first slice should define exact expected trace evidence |
| Content loading | Ready with minor clarification | Runtime validation/content lint works; many content warnings remain |
| Persistence | Ready | Envelope/save/load/snapshot tests passed |
| Versioning | Ready with minor clarification | Persistence version exists; ruleset/backend registries mostly manual/unversioned |
| Provenance | Partially ready | Realization provenance exists; some full-fast failures touch projection/provenance |
| Diagnostics | Ready | Debug trace endpoints, latency buckets, tooling exist |
| UI integration | Partially ready | Local browser UI exists; normal chat/start may need live AI; action helper/affordances usable |
| Testability | Ready with caveat | Focused slices pass; broad fast lane is not green/time-bounded |
| Low-context implementation | Ready | Feature-lane guide, registries, docs, tests provide handoff paths |
| Repository handoff | Ready | Prior AR closeouts and this report establish next slice |

## 8. Initial Product Realization Portfolio

| Lane | Current State | Strategic Role | Ready Opportunities | Dependencies | Recommended Status |
| --- | --- | --- | --- | --- | --- |
| Gameplay | Engine contracts and partial runtime loop exist | Create playable behavior and validate transaction spine | Deterministic noncombat action loop; deterministic combat round slice | Existing content, API, tests | Active |
| AI Experience | Strong backend/final-emission architecture but live path is credential/upstream dependent | Improve expression after engine loop is stable | Fake/deterministic backend smoke; AI-independent realization of engine results | Avoid live provider for first slice | Ready |
| Content & World | Starter content and 58 scenes exist; lint warnings remain | Supply minimum playable situations | Minimal content package for one action; scene graph anchor cleanup | Content lint warnings | Ready |
| UX & Player Interface | Browser UI exists with action helper and affordances | Make runtime behavior inspectable to player/operator | Surface deterministic outcome/trace in existing UI | API state shape | Ready |
| Tooling & Developer Experience | Strong docs/tests/tools but broad fast lane noisy | Provide repeatable product smoke | One deterministic gameplay transaction command/test | None | Active |
| Persistence & Reliability | Envelopes/snapshots/logs operational | Prove gameplay state survives runtime boundaries | Save/restore minimal session after action | Existing storage | Ready |
| Performance & Scale | Latency buckets exist; no measured bottleneck | Avoid premature optimization | None recommended | Need workload first | Dormant |
| Long-Term Evolution | Contracts for providers/rulesets exist; no immediate product need | Preserve future support without blocking product | None for first cycle | Product trigger needed | Dormant |

## 9. Candidate Implementation Backlog

| Candidate ID | Lane | Slice | Observable Outcome | Dependencies | Player Value | Architectural Coverage | Testability | Complexity | Risk | Readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GAME-01 | Gameplay/Tooling | Deterministic noncombat action loop | One authored action resolves through `/api/action` or a local runtime harness, mutates authoritative state, persists, logs trace, and presents next decision without live AI | Existing frontier_gate/interactable or small fixture | High | High: action, noncombat, state, persistence, UI projection | High | Medium | Low-medium | Ready |
| GAME-02 | Gameplay | Deterministic combat mini-round | Roll initiative, execute one attack or end-turn path, persist combat state, show result and next actor | Existing combat scene/enemy fixture | Medium | High: combat, conditions, API, persistence | High | Medium | Medium | Ready with content/fixture check |
| GAME-03 | Gameplay/Content | Scene transition transaction | Select a valid exit, activate scene through authoritative transition, clear/update context, persist, show new affordances | Reachable scene graph | Medium | Medium-high | High | Medium | Medium | Ready with graph warning caveat |
| TOOL-01 | Tooling/DX | Product smoke runner | Single command runs deterministic product loop and writes compact operator summary | GAME-01 decision | Medium | Medium | High | Low-medium | Low | Ready |
| PERSIST-01 | Persistence | Save/restore after gameplay action | Execute deterministic action, create snapshot, mutate again, restore, assert prior state | GAME-01 or GAME-02 | Medium | Medium-high | High | Medium | Low | Ready after first loop |
| AI-01 | AI Experience | Existing fake/deterministic backend through approved adapter | A local fake GM path feeds final-emission/provenance without live provider | Need identify current adapter-safe fake seam or add narrow test seam | Medium | Medium | High | Medium | Medium | Ready after gameplay loop or as parallel tooling |
| CONTENT-01 | Content & World | Minimal validated product scene package | One small scene pair with visible facts, one interactable, one exit, no lint errors/warnings for that package | Content conventions | Medium | Medium | High | Low | Low | Ready |
| UX-01 | UX | Display deterministic engine transaction evidence | Existing UI shows action result, state change, and next affordance without debug leakage | GAME-01 payload | Medium | Medium | Medium | Medium | Low | Ready after GAME-01 |
| PERF-01 | Performance | Establish baseline for deterministic product smoke | Report runtime duration for product smoke | TOOL-01 | Low | Low | High | Low | Low | Deferred |
| EVOLVE-01 | Long-Term Evolution | Ruleset identity publication | Publish explicit current ruleset identity in runtime payload | Product trigger for alternate rulesets | Low now | Medium | Medium | Medium | Medium | Dormant |

## 10. Dependency and Unlock Map

| Candidate | Depends On | Unlocks | Dependency Type | Notes |
| --- | --- | --- | --- | --- |
| GAME-01 | Existing API, noncombat, content, persistence | TOOL-01, PERSIST-01, UX-01, CONTENT-01 refinement | Hard | Best first integration proof |
| GAME-02 | Existing combat fixture/content | PERSIST-01, later combat UX | Content | Valuable but less representative of noncombat play |
| GAME-03 | Reachable scene graph/content | CONTENT-01, UX-01 | Content | Content lint graph warnings make this less first-ready |
| TOOL-01 | GAME-01 acceptance behavior | Future PR smoke gates | Hard | Turns product slice into repeatable operator command |
| PERSIST-01 | GAME-01 or GAME-02 | Reliability confidence for longer sessions | Hard | Needs a gameplay transaction first |
| AI-01 | Existing fake/deterministic backend seam or narrow adapter seam | AI quality iteration without credentials | Soft | Should not precede engine loop unless live narration blocks all visibility |
| CONTENT-01 | Content lint conventions | GAME-01/GAME-03 safer fixtures | Soft | Can proceed independently if small |
| UX-01 | GAME-01 response shape | Player-facing clarity | Hard | Should not invent UI before transaction shape settles |
| PERF-01 | TOOL-01 | Scale/perf decisions | Validation | Premature until meaningful workload exists |
| EVOLVE-01 | Product need for alternate rulesets | Future ruleset work | Design decision | Dormant by doctrine |

## 11. Recommended First Implementation Slice

### Proposed Cycle

`PR-AB - Gameplay: Deterministic Noncombat Action Loop`

### Portfolio Lane

Primary: Gameplay.

Secondary: Tooling & Developer Experience, Persistence & Reliability, Content & World, UX & Player Interface.

### Objective

Create one repeatable, AI-independent gameplay transaction that starts from current authored content or a minimal test fixture, presents/selects a valid noncombat action, resolves it through existing action/noncombat/domain owners, mutates authoritative state, emits log/debug/trace evidence, persists the result, and exposes the next decision state.

### Why This Slice Comes First

This slice has the highest current leverage because it proves the product transaction spine without requiring live AI, without redesigning architecture, and without waiting for broad test-suite cleanup. It gives a player/operator visible evidence that the game can do more than validate isolated contracts. It also unlocks persistence checks, UI polish, content work, fake-backend realization, and future multi-turn product smokes.

Compared with combat, noncombat better represents the intended solo GM loop: scene state, interaction/world context, content, player choices, and narration boundaries. Compared with AI work, it keeps model output non-authoritative and avoids credentials. Compared with content cleanup, it produces executable behavior rather than only readiness. Compared with persistence work, it supplies the gameplay transaction that persistence should protect.

### Player or Operator Flow

1. Load state for a known scene.
2. Inspect available affordances.
3. Submit one deterministic noncombat action, such as examining a known interactable or observing/investigating a scene.
4. Runtime normalizes the action and resolves it through the noncombat seam.
5. Runtime applies authoritative state changes and appends trace/log evidence.
6. Runtime returns a deterministic player-facing result or an explicit engine-authored prompt/blocker.
7. Reload/composed state shows the new state and next available decision.

### In Scope

- One deterministic noncombat action path.
- Existing action normalization.
- Existing noncombat classification/delegation.
- Existing state authority and domain-owner mutation.
- Existing persistence envelope/log/debug trace.
- Existing API projection or a minimal local product smoke command.
- Focused unit/integration tests around the selected transaction.
- Compact operator evidence of state before/action/result/state after.

### Out of Scope

- Live OpenAI calls.
- New AI provider.
- New UI framework.
- Broad combat system expansion.
- Broad content production.
- Full scene graph cleanup.
- Full fast-lane remediation.
- Final Emission redesign.
- Post-GM adoption policy redesign.
- Alternate ruleset identity/loading.
- Performance optimization.

### Architectural Path

Expected path:

`static/app.js` or product-smoke harness -> `game.api.action` / `/api/action` -> `game.scene_actions.normalize_scene_action` -> `game.api._resolve_engine_noncombat_seam` -> `game.noncombat_resolution.resolve_noncombat_action` -> `game.exploration` or `game.social` owner -> `game.api._apply_authoritative_resolution_state_mutation` -> `game.ctir_runtime` if narration path is used -> deterministic engine-authored result or approved no-live-AI realization path -> `game.api_turn_support._finalize_player_facing_for_turn` if needed -> `game.storage.save_session/save_combat/save_world/append_log/append_debug_trace` -> `game.api.compose_state`.

### Primary Files Likely to Change

- `game/api.py`: narrow wiring or test seam if existing paths cannot produce deterministic no-GPT result.
- `game/noncombat_resolution.py`: only if the existing contract cannot express the selected action; prefer no change.
- `game/exploration.py` or `game/social.py`: only for the selected domain-owned deterministic outcome.
- `tests/test_noncombat_runtime_integration.py` or a new focused product-smoke test file following local conventions.
- `tools/`: optional new smoke runner if tests alone do not provide operator visibility.
- `docs/` or this report follow-up: update only if acceptance command becomes a new product lane.

Do not invent exact filenames beyond repository conventions; implementer should inspect current test owners first.

### New Files That May Be Required

- A focused test module if no existing owner file is an appropriate home.
- Optional `tools/run_product_smoke.py` or similarly named local runner only if a CLI/operator command is justified by existing tooling patterns.
- Optional minimal fixture under `data/validation/` or test fixtures if current content is too stateful for deterministic acceptance.

### Contracts Exercised

- RCR-02 Action normalization.
- RCR-03 Affordance/action option contract.
- RCR-07 Noncombat resolution framework.
- RCR-08 State authority domains.
- RCR-09 Runtime schema normalization.
- RCR-10 Scene/content validation.
- RCR-12 Realization/final-emission boundary for mechanics outputs, if final-emission path is involved.
- Persistence envelope contract in `game/persistence_contract.py`.

### Authoritative State Changes

The slice should create or modify one of:

- `session["scene_runtime"]` or `session["scene_state"]` for scene/interactable progress.
- `session` clue/lead/publication fields through existing clue/journal seams.
- `world["world_state"]` only through existing world owner functions if the selected action has world consequences.

The owner must be the existing domain owner or `game.api` orchestration immediately delegating to that owner. No state may be inferred from emitted text.

### Ruleset Role

The ruleset participates through existing deterministic noncombat classification and the selected domain owner. The framework version remains `2026.04.noncombat.v1` unless evidence proves a versioned contract change is necessary. PR-AB should avoid changing ruleset identity.

### AI Role

PR-AB should not require a live AI backend. Preferred path: existing AI-independent engine-authored output. Acceptable fallback: existing fake/deterministic backend only if it passes through approved adapter/realization boundaries and does not become mechanics authority.

### Content Role

Use minimum content necessary: one known scene, one known action/interactable/exit, and any fixture state required for deterministic behavior. `frontier_gate` is a strong candidate because it has visible facts, addressables, exits, and `notice_board` with `reveals_clue`.

### Diagnostics and Provenance

Acceptance evidence should include:

- Normalized action.
- Noncombat resolution with `framework_version`, `kind`, `outcome_type`, `deterministic_resolved`, and `authoritative_outputs`.
- State mutation trace with owner/domain/operation.
- Persisted session/log evidence.
- Final player-facing text or explicit engine-authored blocker/prompt.
- Next state/affordance projection.
- Confirmation that no live GPT call was made.

### Acceptance Criteria

- A single local command or focused pytest slice runs without credentials.
- It starts from deterministic fixture/current-state setup without damaging user runtime data.
- It selects/submits one valid noncombat action.
- It returns `ok=True` or a documented deterministic pending/check/block outcome.
- It records normalized action and noncombat resolution.
- It mutates or records authoritative state through an existing owner.
- It persists and reloads the updated state.
- It exposes next decision state via `compose_state()` or API response.
- It emits trace/log/provenance evidence sufficient for operator review.
- It does not call live OpenAI.
- It does not change architecture, add a provider, or broaden content scope.

### Test Plan

- Unit tests: selected action normalization and noncombat classification if a new action shape is needed.
- Contract tests: noncombat resolution contract fields and state authority mutation trace.
- Integration tests: API/harness transaction from selected action through persistence and next-state projection.
- End-to-end/smoke tests: optional product smoke CLI with compact summary.
- Replay/deterministic tests: use focused scenario-spine or synthetic harness only if it materially proves the loop; avoid broad protected replay schema churn.
- Manual runtime validation: run app or TestClient path with `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1` and no `OPENAI_API_KEY`.

### Architectural Conformance

Implementation should prove:

- Mechanics truth remains in engine/domain owners.
- Prompt/GPT/final-emission layers do not author state.
- State mutation uses existing state authority domains and allowed cross-domain operations.
- Persistence remains storage, not mechanics.
- Diagnostics/provenance explain behavior without selecting behavior.
- Tests extend direct-owner or focused smoke surfaces, not duplicate broad legality matrices.

### Expected Implementation Sequence

1. Identify the exact current content/action fixture, preferably `frontier_gate` plus `notice_board`.
2. Write a failing focused test or smoke harness that runs the transaction without live AI.
3. Route the action through existing normalization and noncombat resolution.
4. Ensure the selected path produces an AI-independent player-facing result or explicit engine-authored pending/check/blocker.
5. Assert authoritative state/log/debug trace evidence.
6. Assert persistence/reload and next-state projection.
7. Add compact operator output if using a CLI.
8. Run focused product, persistence, API, and contract slices.
9. Record any friction instead of broadening scope.

## 12. Alternative Ready Slices

| Slice | Why Not First | What Would Make It First | Lane | Independent? |
| --- | --- | --- | --- | --- |
| GAME-02 Deterministic combat mini-round | Combat is narrower and less representative of the core solo GM noncombat loop | If noncombat AI-independent output proves blocked or combat is the immediate playtest priority | Gameplay | Mostly |
| TOOL-01 Product smoke runner | Needs a transaction to smoke; otherwise becomes tooling without product behavior | After GAME-01 behavior is defined or if existing behavior can be wrapped without code changes | Tooling/DX | No |
| CONTENT-01 Minimal validated product scene package | Content alone does not prove runtime execution | If current content cannot support deterministic GAME-01 safely | Content & World | Yes |
| AI-01 Deterministic/fake backend adapter smoke | Useful, but AI should not precede engine-authoritative loop | If all visible outputs require GM path and no engine-authored path is feasible | AI Experience | Partly |

## 13. Architectural Friction and Decision Log

| Friction Point | Evidence | Affected Candidate or Lane | Impact | Can Work Proceed? | Recommended Treatment |
| --- | --- | --- | --- | --- | --- |
| Normal campaign start/chat path is upstream-dependent | `docs/README.md`, `game/api.py::start_campaign`, import smoke skipped preflight | GAME-01, AI-01 | Live product loop is not deterministic without credentials | Yes | Proceed using existing AI-independent path |
| Full fast lane timed out and showed failures | Runtime command timed out at 300 seconds; `.pytest_cache` lastfailed populated | All candidates | Cannot use full fast lane as acceptance gate | Yes | Use focused owner slices; record broad failures as non-blocking |
| Content lint warnings are widespread | `tools/run_content_lint.py` passed with 164 warnings | GAME-03, CONTENT-01 | Scene graph/content polish risk | Yes | Use one minimal known content path; defer broad cleanup |
| Post-GM adoption gateway is transitional/high-risk in traces | `game/api.py` classifications and `docs/realization_cursor_handoff.md` | AI/realization-adjacent work | Avoid model-text-derived state adoption in first slice | Yes | Proceed using existing design; avoid dependency |
| Final Emission remains broad/high-risk | `docs/realization_cursor_handoff.md`; full-fast failures include final-emission tests | AI-01, UX-01 | Broad edits risky | Yes | Add narrow implementation behind existing contracts |
| Alternate ruleset/provider paths are documented but not implemented | Backend/ruleset registries | Long-Term Evolution | Future support exists as doctrine, not runtime capability | Yes | Defer until product trigger |
| Current runtime data is stateful | `data/session.json` envelope contains active interaction/debug traces | Runtime validation | Avoid mutating user play state in tests | Yes | Use temp fixtures/TestClient isolated temp dirs |

## 14. Existing Defects and Environmental Blockers

### Blocks the Recommended Slice

None identified. PR-AB can proceed without live AI if it uses a deterministic noncombat action and isolated runtime fixture.

### Relevant but Non-Blocking

- `python`, `py`, and `pytest` were not available on PATH; bundled Codex Python worked.
- Full fast lane timed out at 300 seconds and had failures before timeout.
- Content lint reports 164 warnings across 58 scenes.
- Current persisted runtime state has `campaign_can_start=False`.
- Live campaign start can be blocked by upstream preflight.
- `.pytest_cache` lastfailed includes several final-emission/replay/governance failures after the timed-out run; treat as incomplete evidence.

### Unrelated

- Pre-existing untracked files under `artifacts/docx_reconciliation_retrospective/` and `history/development_logs/` should remain untouched.
- Historical DOCX/PDF retrospectives are not required for PR-AB.
- Broad generated artifact cleanup should not be folded into Product Realization.

## 15. Required User-Supplied Information or Files

No additional user-supplied files or decisions are required to generate the PR-AB implementation block.

## 16. Portfolio Operating Procedure

1. Review current portfolio lane statuses.
2. Review incomplete and newly discovered candidates.
3. Select the highest-leverage ready slice.
4. Assign the next global PR cycle identifier.
5. Generate a bounded implementation block.
6. Implement through approved ownership boundaries.
7. Run focused owner tests, product smoke, and runtime validation.
8. Record architectural friction from concrete implementation evidence.
9. Update the portfolio backlog and dependency map.
10. Reassess which lane should receive the next cycle.

Operating rules:

- Lanes may switch, pause, resume, split, combine, or drop candidates based on evidence.
- Do not force a sequential lane order.
- Do not activate dormant long-term evolution without a product trigger.
- Use architectural review only when implementation evidence shows missing ownership, unusable contracts, contradictory state ownership, unavoidable hidden coupling, or a real product requirement the chassis cannot satisfy.

## 17. Milestone Position

| Milestone | Classification | Evidence |
| --- | --- | --- |
| Executable Chassis | Partially achieved | App imports, runtime API exists, focused slices pass; full fast lane not clean |
| Minimal Playable Loop | Not yet achieved | Pieces exist, but no repeatable AI-independent loop proves next decision after state mutation |
| Internal Prototype | Not yet achieved | Local UI and systems exist, but live loop depends on upstream and broad tests are unstable |
| Mechanically Complete Prototype | Not yet achieved | Combat/noncombat foundations exist; breadth and balance incomplete |
| Content-Capable Alpha | Partially achieved | 58 scenes and lint tooling exist; many warnings and graph issues |
| Player-Testable Alpha | Not yet achieved | Upstream dependency and deterministic loop gap remain |
| Feature-Complete Beta | Not yet achieved | Not in scope |
| Release Candidate | Not yet achieved | Not in scope |
| Version 1.0 | Not yet achieved | Not in scope |

Nearest meaningful milestone: Executable Chassis. Minimum capabilities still required: a repeatable deterministic product smoke proving one complete gameplay transaction, persisted state, observable outcome, and next-decision projection without live AI.

## 18. Handoff Package for External Instruction Generation

### Recommended Next Cycle

`PR-AB - Gameplay: Deterministic Noncombat Action Loop`

### Implementation Goal

Implement a narrow, deterministic, AI-independent gameplay transaction through existing runtime owners: select one valid noncombat action, resolve it through the noncombat/domain engine, mutate authoritative state, persist/log/trace the result, and expose the next decision state through existing API or a local product smoke command.

### Minimum Files to Provide Externally

- `PR-AA_product_realization_portfolio_bootstrap.md`
- `docs/system_overview.md`
- `docs/state_authority_model.md`
- `docs/ruleset_contract_registry.md`
- `docs/runtime_persistence_envelope.md`
- `docs/feature_lane_verification.md`
- `tests/README_TESTS.md`
- `game/api.py`
- `game/api_turn_support.py`
- `game/noncombat_resolution.py`
- `game/scene_actions.py`
- `game/affordances.py`
- `game/exploration.py`
- `game/social.py`
- `game/storage.py`
- `game/persistence_contract.py`
- `game/ctir_runtime.py`
- `data/scenes/frontier_gate.json`
- Relevant tests: `tests/test_noncombat_resolution.py`, `tests/test_noncombat_runtime_integration.py`, `tests/test_ctir_noncombat_consumption.py`, `tests/test_affordance_generation.py`, `tests/test_affordance_canonical_pipeline.py`, `tests/test_runtime_schema_boundaries.py`, `tests/test_save_load.py`, `tests/test_runtime_persistence_regression_suite_obj14.py`, `tests/test_start_campaign_api.py`
- Material failing-test output: the PR-AA report's fast-lane timeout summary and `.pytest_cache` lastfailed excerpt if broad-suite context is needed

### Suggested External Prompt

Here is what PR-AA discovered about the current product state, Product Realization portfolio, and recommended first implementation slice. Please generate the PR-AB Cursor implementation instruction block.

### Confidence

Moderate.

The recommendation is well supported by code, docs, and focused passing tests. Confidence is not High because the full fast lane timed out with failures, normal live start/chat remains upstream-dependent, and the exact no-GPT product transaction should be selected by the implementer after inspecting current fixture behavior in isolation.
