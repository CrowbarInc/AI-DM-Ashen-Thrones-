# 16 — Changed-File Inventory

No production gameplay file was modified. No test file was modified. No tool under `tools/` was modified. SHA-256 of the nine PR-EF-R2 hashed sources still matches. See `source_hash_comparison.json`.

HEAD remains `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. The working tree was already dirty before this cycle. Those pre-existing edits are not part of PR-EF-R3.

Created under `artifacts/pr_ef_r3/`:

| Path | Role |
|---|---|
| `01` through `16` markdown reports and `REVIEW.md` | Investigation report |
| `run_investigation.py` | Read-only replay, two-NPC contract probe, token join, fresh interpretation probes |
| `_extract_failures.py`, `_summarize_failures.py` | Helpers that read `behavior_1.json` |
| `captured_failure_replay.json` | Current-code replay of the four historical records |
| `two_npc_authority_replay.json` | Bridge and contract results with Corporal Bren added |
| `ambiguous_turn_state_mutation.json` | Turn counter, time pressure, faction before/after |
| `conversation_3_call_graph.json` | Per-turn token join |
| `fresh_interpretation_probes.json` | Ten interpretation-only probes |
| `fresh_probe_budget.json`, `fresh_probes.usage.jsonl` | Provider usage for those probes |
| `prompt_size_measurements.json` | Current system-prompt character counts |
| `source_hash_comparison.json` | Proof the R2 sources are unchanged |
| `failure_provenance.json`, `failure_summary.txt` | Working extracts. Large and redundant with the reports. Not required to regenerate the conclusion. |

`artifacts/pr_ef_r3/disposable_state/` was created as an empty data-directory redirect and holds no campaign.

`handoff/CURRENT_REVIEW.md`, `handoff/REVIEW_MANIFEST.json`, and `handoff/CURRENT_REVIEW.zip` are replaced by this package. The previous PR-EF-R2 handoff remains in `handoff/history/pr_ef_r2_social_authority_20261016/`.

No `.env`, credential, or active `data/` save was copied into the review.
