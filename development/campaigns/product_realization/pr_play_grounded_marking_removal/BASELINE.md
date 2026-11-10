# Baseline

Recorded before this cycle edited `game/api.py`.

Branch: `feature/product-realization`. HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`. The worktree was already dirty. It was not reset, cleaned, stashed, or reverted.

Source hashes before the edit:

| File | SHA-256 |
|---|---|
| `game/api.py` | `98538F11C00B3464A77A76A29CB03E82C08823A9BC07F60114C3D54928B29014` |
| `game/storage.py` | `32EBDA69C998E9B463B6FEA6ED6C473B9F8B0C3E566EB9DBD6AB4960E95CB8E0` |
| `game/marking_action.py` | `59C1883A7C71BE4E8F0AC5E9BDFCA17ADE27556E4CCAA39A63C4F4E46E0C2CC2` |
| `game/marking_observation.py` | `2247A223144B0D5AF8AA2B7592637AF11D7294F4903B105313E04746C597EA23` |
| `game/object_marking.py` | `1828925D4B4A8591EE34CD34C284941B088F26F00A332AEE04F7F1C8A1CF98EE` |
| `game/object_observation.py` | `74EF7D12D7D3102192A1D9A5F5E7728AF7606418C9896C7BE399E909F5DEF95F` |
| `tests/test_grounded_marking_action.py` | `EE67ABC4F2DBB6167064990705F9A5E55C8DE95AAF192815B1931448118D2F88` |
| `tests/test_player_marking_observation.py` | `90615B9AFC519F00A191FE082A0FEAD9F6A85EC85EF190CD3994178368002496` |

Predecessor tests before the edit: `tests/test_player_marking_observation.py` and `tests/test_grounded_marking_action.py` — 22 passed / 0 failed. Junit: `artifacts/pr_play_grounded_marking_removal/before_new_junit.xml`.

Combined selection before the edit: 405 passed / 20 failed / 0 errors / 0 skipped (425 tests). Junit: `before_combined_junit.xml`. The 20 identities are listed in `REGRESSION_RESULTS.md`. Seventeen match the predecessor's combined run. Three classification tests in `tests/test_pr_play_79df3_classification.py` failed in this before run and had passed in the predecessor's before run. That flip was already present before `game/api.py` was edited.
