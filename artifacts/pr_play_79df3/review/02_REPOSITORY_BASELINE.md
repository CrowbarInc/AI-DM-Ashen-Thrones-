# Repository Baseline

Recorded at the start of PR-PLAY-79D-F3 and confirmed at freeze.

- Branch: `feature/product-realization`
- HEAD: `d40f1ed198236c604085f1c842ead267a8104ce2`
- Prior cycle: PR-PLAY-79D-F2, verdict B/PARTIAL
- Worktree: already dirty from earlier cycles. This cycle did not revert or commit that dirt.
- `game/api.py` and `game/live_chat_interpretation.py` were already modified.
- `game/publication_contract.py` and `game/player_http_boundary.py` are untracked files introduced by earlier publication work.
- `static/app.js` is modified from earlier work. This cycle did not edit it.

## Entry source hashes, before this cycle’s edits

| File | SHA-256 |
| --- | --- |
| `game/publication_contract.py` | `36f8416c168ea456412fd4e2fec8aefc1898f552a223e16f338fb31774ed54ba` |
| `game/player_http_boundary.py` | `03208c26c8c7c3ff27fc885d1802e725611b06492ca5462f9bc8e43ce487c74c` |
| `game/api.py` | `767c3a68469effe5` prefix, 371,497 bytes |
| `game/live_chat_interpretation.py` | `91c982111216a0ee` prefix, 30,573 bytes |
| `game/provider_budget.py` | `5a273cfc427ea17b814beafb051c4348a323c758e378746f933cab60b1d9a37b` |
| `game/player_http_projection.py` | `1f7b0f3df32a9854d91f462eafab39692f7040dcc2613ab352d0e3af3ffec348` |

Provider budget, HTTP projection, and the HTTP boundary were not edited. Their freeze hashes match these entry hashes.

## Test and provider configuration

- Pytest isolation: `tests/conftest.py` disables live interpretation and expression generation and installs storage isolation.
- Refusal tests clear the interpretation-disable flag and do not set `ASHEN_DISABLE_PROVIDER_CALLS`.
- Historical child pytest sets `ASHEN_DISABLE_PROVIDER_CALLS=1` and an isolated evidence directory.
- No new campaign opening was generated.
- Automatic retries were not enabled for this cycle’s acceptance hosts.
- Protected entry: `artifacts/pr_play_79df3/protected_entry.json`, 150 files, all matching the PR-PLAY-79D-F2 hashes.
