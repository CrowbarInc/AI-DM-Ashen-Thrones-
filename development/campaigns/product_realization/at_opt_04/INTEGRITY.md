# AT-OPT-04 Integrity

| Item | Value |
| --- | --- |
| Branch | `feature/product-realization` |
| HEAD | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Worktree at entry | Already dirty. `git status --short` was 757 lines. Not reset, cleaned, committed, or pushed |
| `game/prompt_context.py` | Unchanged. SHA-256 `ccf21b03150566d4439b48c2e4e53a0563be74636087c0ee0a8fa6479414996f` |
| `game/gm.py` before | SHA-256 `1f31510377adb072750bc187effffcf6c45387373a86594732601d88fe185614` |
| `game/gm.py` after | SHA-256 `f16073aff66ab861847f44d7573356e9244c4ec8de298dabbe70c166bf4b5f3b` |
| Production edit | `omit_duplicate_turn_packet_policy` only. The file was already dirty; `artifacts/at_opt_04/implementation.diff` is that function |
| Live provider calls | 0. Measurement constructions 0. Holdout non-local connections 0 |
| Campaign openings | 0 |
| Commits or pushes | 0 |

## Files this cycle adds or edits

- `game/gm.py` — mixed-key drop inside the existing helper.
- `tests/test_at_opt_04_mixed_key_policy.py` — matrix and the F3 `build_messages` check.
- Reports under `development/campaigns/product_realization/at_opt_04/`.
- Evidence under `artifacts/at_opt_04/`.
- `docs/NEXT_SESSION.md` — AT-OPT-04 prepended. Prior sections remain.

Protected campaign files: 150 compared, 0 changed. Historical holdout results were not rewritten.
