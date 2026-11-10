# PR-PLAY-14 Preflight

**PREFLIGHT PASS** — read-only inspection consumed no provider tokens.

Repository: C:\Users\Master Mandalcio\Documents\Tabletop Gaming\AI Dungeon Master\ashen_thrones_ai_gm
Branch: feature/product-realization; revision d40f1ed198236c604085f1c842ead267a8104ce2.
Working tree dirty before validation; full status retained in working_tree_before.txt. Existing implementation changes preserved. No root or inspected ancestor AGENTS.md found.

Provider: OpenAI Responses API. All configured model routes: gpt-4.1-mini. Credentials present (existence only); no credential values collected. Dependencies available in .venv. Scenario FiveTurnGameplay v1.0.0 available; pinned frontier-gate-v1 grounding verified.

Effective configuration: Live; explicit authorization; response capture enabled; ASHEN_OPENING_RENDERER=1. Six request maximum, SDK retries=0, host provider retries=0, no judge or probe calls. Aggregate input/output/total limits: 200000/20000/220000 tokens, unchanged from scenario. Per-request caps: opening 3000, ordinary narration 600, live interpretation 320. See preflight_configuration.json.

Inspected scripts/run_live_playtest.ps1, tools/playtest/{runner,worker,gameplay}.py, scenario JSON, game/{provider_budget,config,model_routing,live_chat_interpretation,opening_presentation_renderer,gm,api}.py. PowerShell accepts the requested switches. Runner rejects unauthorized Live or FiveTurnGameplay without capture. child_environment merges .env and inherited environment, clamps budgets downward, disables both retries, skips upstream preflight. Renderer flag inherited from isolated launcher to runner to owned worker through explicit subprocess env; dotenv does not override existing environment. Worker reports renderer mode in ready.json; gm.call_gpt selects the renderer for opening only. Worker binds a fresh loopback socket; existing servers are not used. No architectural changes needed.

Provider admission is atomic under lock, durably reserves request and token allowances before dispatch, refuses duplicate dispatch and budget overrun, stops after unknown accounting. Interpretation and narration use shared admission. SDK constructors receive max_retries=0. Host retry attempts return without dispatch when suppression enabled. Local deterministic fallbacks do not dispatch; any ordinary interpretation plus expression calls share the six-request allowance. No model route differs from gpt-4.1-mini. Worker forbids connectivity probes; no additional judge path in runner. Controller stops on rejected opening, failed turn, authority checks, budget or deadline. Five turns may require more than six requests; partial completion is anticipated, not automatically a defect.

Snapshots: baseline, opening, per-turn before/after, final; persistent files and API state retained. Overlay comparisons and state diffs recorded. Shared journal records admissions, dispatch, completion, usage and latency. Bounded opt-in opening response capture copied into diagnostics; ordinary provider/parser metadata recorded where supported. Raw ordinary provider text may be unavailable and must not be reconstructed.

Previous result inventory inspected: historical Live artifacts predate renderer implementation or are blocked zero-dispatch tests; no existing renderer-enabled Live FiveTurnGameplay execution found. PR-PLAY-13 synthetic results will not count as live evidence.

Authorization permits exactly one invocation. Proceed once using isolated process environment. Do not rerun, change settings, repair code, commit, or push. Runtime readiness will confirm actual worker activation; any failure remains evidence.
