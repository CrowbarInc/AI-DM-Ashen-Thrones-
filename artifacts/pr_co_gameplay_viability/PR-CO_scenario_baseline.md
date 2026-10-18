# PR-CO Scenario Baseline

Mode: controlled live gameplay viability probe. No application code was modified. The dirty worktree was left in place. Production `data/` mtimes were unchanged after the run (`production_mtime_drift.json` is `[]`).

## Git

- HEAD: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`
- Subject: `PR-BN bounded DM improvisational authority`
- Worktree: dirty before this probe. Tracked edits include game modules, tests, `handoff/CURRENT_REVIEW.md`, and production session files (`data/session.json`, `data/world.json`, `data/combat.json`, `data/session_log.jsonl`). Many PR artifact paths are untracked.
- This cycle added files only under `artifacts/pr_co_gameplay_viability/` and refreshed `handoff/CURRENT_REVIEW.md`, `handoff/CURRENT_REVIEW.zip`, and `handoff/REVIEW_MANIFEST.json`.

## Provider And Cost

Verified before gameplay calls.

- Provider: OpenAI.
- Billing path: official OpenAI Python SDK, `client.responses.create`. No `OPENAI_BASE_URL` or `OPENAI_API_BASE` in the environment. Endpoint used by the SDK default is `https://api.openai.com/v1/responses`.
- API key: present in repo `.env` (prefix `sk-`, length 164). The key was not copied into artifacts.
- `MODEL_NAME=gpt-4.1-mini`. `DEFAULT_MODEL_NAME`, `HIGH_PRECISION_MODEL_NAME`, and `RETRY_ESCALATION_MODEL_NAME` are unset, so `game.config` resolves all three to `gpt-4.1-mini`.
- `ENABLE_MODEL_ROUTING` is unset and therefore defaults to true. Every route still selects `gpt-4.1-mini`.
- Live response model: `gpt-4.1-mini-2025-04-14`.
- Published prices used for the estimate, from <https://developers.openai.com/api/docs/pricing.md> and the GPT-4.1 mini model page: input $0.40 / 1M, cached input $0.10 / 1M, output $1.60 / 1M.
- Ceiling estimate before calls: 300,000 tokens as 95% input and 5% output on `gpt-4.1-mini`, no cache, about $0.14. Cached input would cost less.

Startup preflight was the first provider request. It returned usage and `health_class=healthy`. Gameplay calls started only after that.

## Test Environment

- In-process FastAPI `TestClient` against `game.api.app`.
- Storage retargeted to `artifacts/pr_co_gameplay_viability/evidence/isolated_session/`.
- Interpreter left enabled. Provider responses were not mocked.
- Hard stop: 8 completed turns, 12 provider requests, 300,000 combined tokens. The runner raises before request 13 and before any further call once usage is missing.

## Known Regression Baseline

Inherited from PR-CN, decision B — partial repair. Shared turn pipeline 41 passed / 24 failed. Focused PR-CN 14 passed. Contextual leads 56 passed. Resolver selection 30 passed. Prompt context 115 passed. Persistence 13 passed. Immutable/GM decision 30 passed.

Residual failures left open by PR-CN:

- grounded observation inventing confrontation
- examination retaining an invented inscription
- repeated quiet-wait narration
- `initial_generation` vs `regeneration` provenance
- other shared turn-pipeline contract failures

Those residuals were not re-run as pytest in this cycle.

## Scenario

Identity: authored default opening from `game.defaults.default_scene("frontier_gate")` and `default_world()`, seeded into the isolated directory together with `market_quarter` and `old_milestone`.

This is the product default exercised as background geography by the PR-BX through PR-CA live seeds. The active scene in those dialogue probes was the bread stall. This probe uses the default gate as the active scene because that one authored package contains a conversational NPC, an explorable visible feature, a discoverable topic, a waitable crowd, and a stable continuity fact. The dirty production `data/scenes/frontier_gate.json` was not loaded. That file adds a notice-board interactable and a structured clue the default scene does not have.

Initial session:

- Active scene: `frontier_gate`
- Location: Cinderwatch Gate District
- Turn counter: 1
- Mode: social
- Character: Galinor, wizard, HP 8/8, inventory spellbook only
- Interlocutor: none

Initial scene summary: rain, choked eastern gate, guards, rotting banners.

Relevant NPCs:

- Guard Captain (`guard_captain`), location `frontier_gate`, agenda `patrol_gate`. Authorized topic `patrol`: "A patrol went missing near the old milestone."
- Tavern Runner (`tavern_runner`), topic `stew`: "Hot stew and rumors for coin."
- Scene addressables also include the ragged stranger and the threadbare watcher. They have no authored topics.

Authored visible facts include the notice board (taxes, curfews, missing-patrol warning), the tavern runner's shout, the noble townhouse, and the threadbare watcher. Discoverable clue strings exist on the scene, including closer reading of who posted the notice. Hidden facts exist (noble watcher, Ash Cowl scout, threadbare signal, spotter with a list) and were not player-visible at start. The default notice board is a visible fact, not an interactable, so inspection has no `reveals_clue` binding.

World progression mechanism: three faction clocks (House Verevin pressure 2, Ash Cowl pressure 2, Ordo Pyric pressure 1), each with agenda progress 0. Prior probes established that ordinary turns advance these clocks.

Continuity fact used for the planned turn 7, if the sequence had reached it: the Guard Captain's patrol topic, or the preference answer if that topic was not established in play.
