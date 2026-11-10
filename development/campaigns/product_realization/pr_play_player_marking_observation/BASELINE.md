# Baseline

Recorded before production edits in this cycle.

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- Worktree: dirty. `git status --short` listed 868 lines. That work was left in place. No reset, clean, stash, checkout, commit, or push.

Entry hashes (SHA-256):

| File | SHA-256 |
|---|---|
| `game/api.py` | `910BDEACB23973B6F1D284B83E8921BD97C096B47F834E605B5F41324FB276D3` |
| `game/marking_action.py` | `59C1883A7C71BE4E8F0AC5E9BDFCA17ADE27556E4CCAA39A63C4F4E46E0C2CC2` |
| `game/object_observation.py` | `74EF7D12D7D3102192A1D9A5F5E7728AF7606418C9896C7BE399E909F5DEF95F` |
| `game/object_marking.py` | `1828925D4B4A8591EE34CD34C284941B088F26F00A332AEE04F7F1C8A1CF98EE` |
| `game/immutable_valid_response.py` | `F6A317ED44693CEC3A06BEA3BE2EF889760004DE26150A5CB02FAEA3D3430FC4` |
| `game/storage.py` | `5B9171956EA62ADEF2C9B6C66A3B0C27560BDEF633A787126CA3FBCFA4D725F5` |

`game/marking_observation.py` did not exist.

Combined selection before edits: 408 passed / 17 failed / 0 errors / 0 skipped (425 tests). Junit: `artifacts/pr_play_player_marking_observation/before_combined_junit.xml`. The 17 identities match the immediate predecessor. They are listed in `REGRESSION_RESULTS.md`.

The publication mismatch was still present in `_publish_committed_marking`: after `seal_host_speech`, a different sentence was stored and `publication_matches_commit` was `sealed == text`. A sealer exception left the turn and `runtime_commit_scope` restored the pre-turn character.
