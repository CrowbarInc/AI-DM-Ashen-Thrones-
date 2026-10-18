# 02 — Environment and Baseline

Repository revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`d31beb7`). This is the same HEAD recorded by PR-EF-R2. The working tree was already dirty at investigation start (453 short-status lines, including earlier cycle edits under `game/`, `data/`, and `artifacts/`). PR-EF-R3 did not edit production gameplay, tests, or tools. SHA-256 of the nine files hashed at the end of PR-EF-R2 still matches `artifacts/pr_ef_r2/source_hashes.json`. Comparison is in `source_hash_comparison.json`.

No Git commit, reset, branch switch, active-campaign write, or dependency change was made. Investigation scripts set `ASHEN_DATA_DIR` to `artifacts/pr_ef_r3/disposable_state` before importing game modules. That directory was created empty and was not used to save a campaign. Fresh interpretation calls wrote only `artifacts/pr_ef_r3/fresh_probes.usage.jsonl`.

Provider configuration, from code and from the fresh calls:

- Configured model: `gpt-4.1-mini` (`experiments/pr_dp`).
- Observed model: `gpt-4.1-mini-2025-04-14`.
- Interpretation output cap: 320 tokens. No interpretation retry.
- Narration output cap used by the PR-EF-R2 harness: 1600. Default provider timeout in `game/gm.py` is 45 seconds unless `ASHEN_PROVIDER_TIMEOUT_SECONDS` is set. The R2 harness set 25 seconds. This cycle's fresh calls used the 45-second default.
- One narration retry is selected in `game/api.py` when validation fails: purpose `retry_escalation`. Manual narration budget is 6 `call_gpt` invocations per turn.

Regression baseline was not re-executed. The R2-touched production and test files are byte-identical to the R2 final hashes, so the last measured family result still applies: 321 passing / 20 failing on the eighteen-file family in `artifacts/pr_ef_r2/final5_command.json`, with no new failing identities introduced by R2. That family is not the full repository suite. Twenty inherited failures remain as classified in the R2 report. This cycle adds no test run and claims no new regression result.

PR-EF-R2 commands retained for traceability:

- Family: `.venv/Scripts/python.exe -m pytest` with the file list in `artifacts/pr_ef_r2/final5_command.json`.
- Holdouts and the eleven-turn conversation were produced by `tools/validate_pr_ef_r2.py`. This cycle did not rerun them.

This cycle's commands:

- `artifacts/pr_ef_r3/run_investigation.py` — replay captured records, two-NPC bridge/contract override, token graph, ten interpretation-only probes.
- Fresh-probe budget: 12 requests, 60,000 input tokens, 5,000 output tokens. Actual use: 10 requests, 16,530 input, 1,900 output, 18,430 total. No narration call was sent.

Recorded-provider fixtures used as evidence, not as new live play:

- `artifacts/pr_ef_r2/behavior_1.json` — fresh production holdouts, including the four failures and full before/after state for the ambiguous turn.
- `artifacts/pr_ef_r2/conversation_3.json` and `conversation_3.usage.jsonl` — the eleven-turn, 199,502-token conversation.
- `experiments/pr_dq/world.py` — in-memory courtyard scene. The behavior snapshot stores world and session but not the scene document. The fixture is the scene those turns used. Historical faction and clock numbers come from the snapshot, not from the fixture.
