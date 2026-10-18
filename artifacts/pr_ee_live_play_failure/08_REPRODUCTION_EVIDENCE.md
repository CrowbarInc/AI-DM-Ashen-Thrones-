# 08 — Reproduction Evidence and Limits

## Original production evidence

`original_session_log.json` preserves all six existing log rows. They span 2026-10-16 20:12:25–20:13:33 UTC (4:12–4:13 p.m. America/New_York). Original nested provider records identify five gpt-4.1-mini requests, actual returned model gpt-4.1-mini-2025-04-14, real request ids, tokens and latency; turn four has no provider call. These were available before investigation; they are not newly generated completions. `original_session.json` is the post-interaction persisted envelope, not the original initial state. No original raw HTTP capture, screenshot, exact provider prompts, process build fingerprint, startup flags, or per-turn prestate snapshots were available.

## Controlled current production-entry reproduction

Command: `.venv/Scripts/python.exe artifacts/pr_ee_live_play_failure/investigate.py`.

The runner copies campaign/character/world/combat/conditions/scene files to a disposable directory, sets ASHEN_DATA_DIR before game imports, seeds `create_fresh_session_document`, clears only the copied transcript, and posts the exact UI-shaped bodies to actual FastAPI `/api/chat?ui_mode=player` via TestClient. It does not replace `chat`, interpretation records, orchestrator, bridge, resolvers, storage, or rendering text. At `request_interpretation` only, it returns the ORIGINAL raw provider JSON for that turn. Thus the real production adapter/eligibility and blocked/accepted routing are exercised. It records reconstructed prompts before injection, before/after sessions and prior logs. It sends no external requests in this mode. Lifespan/preflight is not run. No real browser automation or remote deployment is claimed.

Result: six HTTP 200 responses, six byte-for-byte matches of the original logged player-facing strings. World documents unchanged; pending sequence updates and persistence timestamps are recorded. The seven-turn diagnostic including the separate recognized-fresh-start replay is a reproduction exercise, not an acceptance suite.

The extra fresh-start probe uses the exact turn-two sentence and recorded output on an empty transcript. Cue detection is true and structured start is available before posting, yet live interpretation intercepts before scene_opening. See `recognized_fresh_start_replay.json` and `lifecycle_gate_probes.json`.

Windows sandbox limitations: initial temp-file replacement failed with WinError 5 outside the workspace; disposable state was moved inside the artifact directory. Sandboxed TestClient also hung creating asyncio's socketpair before entering the endpoint. The no-network diagnostic then succeeded outside the sandbox after automatic review. These harness failures were not product-turn failures and were not repaired in production code.

## Six semantic alternatives

Fresh live-provider run command was prepared (`investigate.py --live`) but automatic approval review rejected execution before process launch: the requested run might transmit private campaign/world context to an external provider without payload-specific authorization. No fresh calls or alternative provider outputs exist. The rejection was not bypassed. `live_probe_access_limit.json` records this limitation.

All six requested alternatives were evaluated at the real deterministic decision function, in fresh context and in reconstructed post-turn-four rejection context (`semantic_alternatives_static_probes.json`):

| Input | Fresh deterministic result | After original rejection |
|---|---|---|
| Can we start playing? | No deterministic decision | Same; requires unmeasured provider interpretation |
| Describe the opening scene. | No deterministic decision | Same |
| What is happening around me? | No deterministic decision | Same |
| I'm speaking to you, the DM. | No deterministic decision | Same |
| Why can't you do that? | No deterministic decision | ANSWER/recent_visible_context_answer; repeats the previous refusal with a “From what has already been established” prefix, rather than explaining why |
| What should my character do next? | No deterministic decision | Same; narrower planning regex does not recognize this wording |

“No decision” is not a completed failing API response. It establishes lack of deterministic ownership, not the answer a new provider completion would give. Semantic robustness across fresh provider outputs remains unmeasured. The generality of the confirmed singleton/unsupported bug follows from the branch predicate and two different original component classes, not a guessed model completion for each phrase.

## Configuration and version

Current checkout HEAD is d31beb7d73dd4fda0f22184a6a69b947b5f470ff (“PR-BN bounded DM improvisational authority”), with extensive later modified/untracked files. Therefore HEAD alone cannot identify PR-EA–ED code. `git_status_at_review.txt`, `source_hashes.json`, and source_snapshot preserve the inspected implementation. Current effective default/high-precision/interpreter model is gpt-4.1-mini and model routing is enabled. The original returned model matches that configured family. All original responses and decision reasons match current source/replay. This supports current implementation compatibility; it does not prove the production process loaded these exact bytes, used identical flags, or was freshly reloaded. Process inspection was unavailable (CIM denied), and no deployment/source fingerprint exists in the six log entries. No evidence warrants claiming a stale deployment as the cause, nor certifying intended deployment configuration.

Original provider call accounting is preserved separately from replay timing. Top-level performance stage/token fields are null on early exits; nested original usage contains the missing tokens and actual interpreter latencies. No raw credentials or .env file are packaged.
