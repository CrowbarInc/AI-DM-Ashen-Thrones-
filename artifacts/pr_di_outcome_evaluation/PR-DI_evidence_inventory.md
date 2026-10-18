# PR-DI Evidence Inventory

Mode: Architectural outcome evaluation. Implementation: none. Live calls: 0.

Git HEAD at start: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Worktree status was dirty before PR-DH and dirty at PR-DI start; existing modifications were preserved. PR-DH records `production_saves_changed=false`; PR-DI made no production save calls.

## Evidence Files

| file | bytes | use |
| --- | --- | --- |
| artifacts/pr_dh_live_interpretation/raw_results.json | 165096 | read |
| artifacts/pr_dh_live_interpretation/PR-DH_live_results.csv | 3029 | read |
| artifacts/pr_dh_live_interpretation/PR-DH_provider_usage.csv | 2832 | read |
| artifacts/pr_dh_live_interpretation/PR-DH_candidate_A_results.md | 550 | read |
| artifacts/pr_dh_live_interpretation/PR-DH_candidate_B_results.md | 486 | read |
| artifacts/pr_dh_live_interpretation/PR-DH_candidate_C_results.md | 435 | read |
| artifacts/pr_dg_architecture_preflight/results.json | 284686 | read |
| artifacts/pr_dg_architecture_preflight/PR-DG_scenario_comparison.csv | 12138 | read |
| artifacts/pr_df_architecture_comparison/PR-DF_experiment_scenarios.md | 12914 | read |
| artifacts/pr_df_architecture_comparison/PR-DF_decision_framework.md | 4613 | read |


## Evidence Recovered

- Original player utterances were recovered from `artifacts/pr_dg_architecture_preflight/results.json`.
- Candidate A selector, resolver, resolution, diffs, unsupported flags, and state snapshots were recovered from `raw_results.json`.
- Candidate B raw model outputs, parsed plans, validation errors, execution records, state diffs, and per-request usage were recovered from `raw_results.json` and `PR-DH_provider_usage.csv`.
- Candidate C tool transcripts, tool results, invalid-tool list, state diffs, and per-round usage were recovered from `raw_results.json` and `PR-DH_provider_usage.csv`.
- Narration tokens are not included; PR-DH measured interpretation/tool requests only.

## Unavailable Evidence

- Player-visible narration text was not generated for these PR-DH interpretation runs; `player_visible` is empty except clarification/refusal text returned by the experiment harness.
- Candidate C final responses are represented as model intent fields and absence of a tool call; there is no separate natural-language final message transcript.
- No monetary provider pricing is present in the evidence. Cost normalization therefore uses requests, latency, and tokens only.
