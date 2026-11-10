# 02 — Final source baseline

| Item | Value |
| --- | --- |
| Revision | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Branch | `feature/product-realization` |
| Operating system | Windows 11 10.0.26300 |
| Python | 3.14.3 |
| Working tree | Dirty. PR-PLAY-55 through 71 and this verification stay uncommitted. |

`artifacts/pr_play_71v/baseline.json` is the 10:44 PM snapshot taken before `runtime_commit_scope` was added. It is historical. The frozen holdout and both lifecycles ran after that edit.

## Hashes under test

| File | Final SHA-256 | Matches 10:44 baseline |
| --- | --- | --- |
| `game/storage.py` | `3d05b61cdf8f266a2c266b00553cfe9cb9f0b56ed57aa89b62dfd7deed77f91f` | no |
| `game/api.py` | `0affcf3e552bd27f69675eb9f2a20bd8773415a2e51a7575a6a40acd7c1cf7f9` | no |
| `game/authored_consequences.py` | `e44e112f9bbc1e7389a40caca905a28613a596b03727828fea5b5f0c3e16351a` | yes |
| `game/campaign_reset.py` | `795e275b6d83b929879c513a1d34582d70cc233d4f7022fa5d67a5719d769bac` | yes |
| `game/quarantined_investigation_narration.py` | `0eaf4245a6c0336babf292c1203da737ec17a7eb3bfd47853bb44a4a49b696fe` | yes |
| `game/player_http_projection.py` | `1f7b0f3df32a9854d91f462eafab39692f7040dcc2613ab352d0e3af3ffec348` | yes |
| `static/app.js` | `db49e84816f7f4a5a16a8f2f3efe4fe9373f9ddf6bc577b501217aaf13816df9` | yes |

The 10:44 freeze hashes for `game/api.py` and `game/storage.py` were `457b37591e7d5edc963a88a33e1eae1d0c91cab79a30adbcf128e44c1151234d` and `3e39572d1364b98e2a5fb853086a1a790112e611e5777814173ff87f817293ae`.

Verification hosts set `ASHEN_EXPERIMENTAL_BRANCHING=1` and `ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS=1`, skipped upstream preflight, and disabled live provider calls. Product defaults for those flags were not changed.

No product file was edited after the holdout began.
