# ATGB-02 execution

The harness is `tools/run_atgb.py`. Library code is `tools/atgb/`. Fixtures are `data/validation/atgb/`. Nothing in this path is a gameplay authority.

## Fixtures

`corpus.json` records the benchmark version, rubric version, expected partition counts, the S07 discrepancy, and environment facts.

`visible/` contains S01–S06 (`development_visible`) and S08 (`related_variation`). `held_out/` contains S07, S09, and S10. Each scenario file keeps the catalog's behavioral criteria: communicative purpose, acceptable variation, and unacceptable outcomes. There is no exact GM string to match.

The loader checks counts against `expected_turns`. A mismatch is an error. Counts are not rewritten to force agreement.

Ordinary repair tests should not import `held_out/` in order to tune a change. The benchmark loader reads that directory when the run includes the held-out partition, including the infrastructure check that the adopted counts are intact.

## Modes

| Mode | What it does | What it may claim |
| --- | --- | --- |
| `provider_disabled_simulated` | Loads fixtures, checks isolation, builds the chat request, and stores a labeled test-double reply. It does not import the game and does not call `POST /api/chat`. | Infrastructure validation only. |
| `provider_disabled_host` | Copies the pinned benchmark baseline into a fresh directory, sets `ASHEN_DATA_DIR`, resets only that directory, validates preflight, and posts each player line to `POST /api/chat` with provider calls disabled. | Host behavior. Not conversational competence. |
| `live_provider` | The same chat path with providers left enabled. Refused unless `--confirm-live-provider`, `--max-provider-calls`, and `--max-elapsed-seconds` are all set. | A gameplay result only after a person reviews the three judgments. |

The default mode is `provider_disabled_simulated`.

Simulated replies are the sentence `[ATGB SIMULATED TEST DOUBLE] This is not an AI-DM response. Infrastructure validation only.` Host replies are whatever the current chat path returns. The result records `response_origin` and `simulated`. A simulated or host package sets `gameplay_performance_claim` to false.

```powershell
.\.venv\Scripts\python.exe tools\run_atgb.py --list
.\.venv\Scripts\python.exe tools\run_atgb.py --mode provider_disabled_simulated --output artifacts\atgb\example_simulated
.\.venv\Scripts\python.exe tools\run_atgb.py --mode provider_disabled_host --scenario S06 --output artifacts\atgb\example_host
```

A future live checkpoint, not run by this pass:

```powershell
.\.venv\Scripts\python.exe tools\run_atgb.py --mode live_provider --confirm-live-provider --max-provider-calls 80 --max-elapsed-seconds 1800 --output artifacts\atgb\live_trial_1
```

There is no default dollar ceiling. `--max-estimated-cost` is accepted only together with both `--price-per-million-input-tokens` and `--price-per-million-output-tokens`. If tokens are missing after a live call, the next turn is not started. Cost is `unavailable` when the price or the token counts are missing. The host's own null token totals stay null.

## Campaign data

`game.storage.DATA_DIR` is bound at import. The chat worker is a subprocess. It sets `ASHEN_DATA_DIR` before importing the game. The parent does not retarget its own process.

Before any copy or reset, the resolved directory is rejected when it is the repository `data/` directory, the active player campaign directory, a directory that already holds campaign files, or a store that was already used. Inside the repository, a store must be a new directory under `artifacts/atgb/` or `development/tmp/`. A temporary directory outside the repository is also accepted. Failure is an exception, not a warning.

ATGB-02A replaces the working-data source with `data/validation/atgb/baselines/frontier-gate-v1/`. This frozen authored snapshot comes from the existing `seed_frontier_gate_world` replay fixture and production defaults, not a playthrough. `manifest.json` records source revision, source-file hashes and all seven bootstrap-file hashes. `tools/atgb/baseline.py` pins the manifest digest and inventory. Missing or changed files, incompatible versions, and alternate sources fail without fallback. Changing a baseline requires a reviewed version and pin update.

The copy takes `campaign.json`, `character.json`, `conditions.json`, `world.json`, and three scene templates. It does not copy `session.json`, `combat.json`, or `session_log.jsonl`. Reset runs only after the imported data directory matches that store and copied files match the baseline. World playthrough fields are cleared by the existing production reset. No canonical campaign file supplies benchmark data. Disposable stores use `development/tmp/` to avoid Windows sandbox temporary-directory rename restrictions.

Each scenario gets a new directory. Stores are deleted after the run unless `--keep-stores` is set. Result files go to the output directory, not into a campaign save.

If the fresh scene id does not match the fixture's `location_id`, the worker submits no turns and does not switch scenes.

## Starting-state preflight (ATGB-02A)

Before host or live chat, the worker checks imported storage binding, baseline identity,
expected location and scene presence, all authored baseline content (including NPC ids,
locations, aliases and topics, clue text, investigation binding, addressables, visible,
opening and hidden facts), plus the existing fresh-runtime validator and empty history.
World dictionary defaults may add keys; authored values and list contents must match.
Critical failures produce `preflight_failed` and zero turns. A damaged source or copy
is refused before reset/import. These are setup failures, never conversational scores.
The run stops at the affected scenario; subsequent scenarios are not attempted.

Readiness inspection without chat:

```powershell
.\.venv\Scripts\python.exe tools\run_atgb.py --mode provider_disabled_host --preflight-only --output artifacts\atgb\readiness
```

This command disables providers, resets all ten isolated stores, records checks and a
normalized starting-state digest, then submits zero chat turns. Random session/run ids
and save timestamps are excluded from that digest. It is not a performance trial.
Simulated mode still does not reset or establish gameplay state; its preflight is
unverified. It records the selected baseline but cannot establish runtime readiness.

Each scenario record has `preflight.ok`, `critical_failures`, `runtime_violations`,
`baseline`, `starting_state_sha256`, and `unverified_conditions`. Narrative delivery,
continuity, clarifying questions and model restraint remain unverified. See the
scenario matrix in `development/reports/atgb_02a_readiness.md`.

## Results and review

A run writes `result.json`, `report.md`, `worksheet.json`, and `worksheet.md`.

The result records benchmark version, scenario version, rubric version, partition revision, git revision, worktree dirtiness, model configuration when the worker could read it, execution mode, trial number, player lines, replies, state evidence, the three judgments, severity, latency, provider calls, tokens, retries, and estimated cost. Missing telemetry uses `unavailable`. A null that the host actually returned uses `host_reported_null`. Sampling is `uncontrolled` because the client does not expose a temperature to this harness. API keys are not written.

The report lists critical failures, then major failures, then capability counts with raw pass/scored figures. Percentages in a gameplay sense are withheld unless the package is a human-reviewed live run. There is no score out of 100.

The worksheet leaves interpretation, response, and authority separate. Conversation quality is a checklist and a note, not a number. Reviewers may mark a judgment `uncertain`.

Human scores are a separate JSON file passed with `--scores`. Scoring a simulated transcript does not flip `gameplay_performance_claim`.

## Versions and comparison

Comparable runs share turn id, player line, fact list, and rubric version. The result header also carries benchmark version, scenario version, partition revision, git revision, model configuration, execution environment, and trial number. S07 must be compared by the partition stored in the result, because the ATGB-01 catalog table still calls it development-visible.

No adapter runs an older build. An older revision is `not comparable` when it cannot boot the same isolated directory and accept the same lines through chat.

## How to read a limitation

Infrastructure success means the fixtures load, isolation holds, requests are ordered, and outputs are labeled. It does not mean the AI-DM understood the player. Host success means the chat path returned text with providers disabled. The generic OOC acknowledgement and the sentence `Provider calls are disabled for this run, so no live narration was generated.` are host outputs. The catalog already says a generic acknowledgement can pass interpretation and fail response. This harness does not score that. Held-out results, even after a future live run, remain previously exposed until a new unexposed environment exists.
