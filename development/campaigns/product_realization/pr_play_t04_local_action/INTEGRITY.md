# Integrity

| Item | Value |
|---|---|
| Branch | `feature/product-realization` |
| HEAD | `d40f1ed198236c604085f1c842ead267a8104ce2` |
| Dirty status lines | 812, preserved. No reset, clean, stash, revert, or checkout. |
| Commits / pushes | none |

## Production diff

Compared with the predecessor manifest (1,296 paths, matched before edits) the only changed tracked source paths are:

- `game/api.py`
- `game/conversational_orchestration.py`
- `game/local_interaction.py`
- `tests/test_pr_play_post_npc_handoff.py`

Added: `tests/test_pr_play_t04_local_action.py`. Missing: none. Frozen scene and baseline files checked: 70. Frozen changes: none. `data/scenes/frontier_gate.json` remains `d9b3ec634f71cb13c6a77be637a984f2889a82ca9301300ebcfd86115a05d0a9`.

Logical diff, newline-normalized against the source snapshot whose bytes match the predecessor hashes: `artifacts/pr_play_t04_local_action/production.diff`.

## Source hashes

| Path | Before | After |
|---|---|---|
| `game/local_interaction.py` | `e3468ef346989cd5fc8a44b4c100f0f76d6bea0c5734477f7c2db67db27712b2` | `4db93c2d17ca93434c503e1f5daf35366a5ccd6ce3e5c0edae408f3ce57a8580` |
| `game/conversational_orchestration.py` | `f991c3ac8386cd5704736245cae3e5c5745e062790b1fdeb166e932bfe28d8f5` | `2bd6c31fcd2c44c305ebfe07b0f520f3b4c58314694f9cb20f20c8c2f17668d8` |
| `game/api.py` | `c74933294c97d44e840531a12b96a524d727c7c556d3a94c04b033cfada684c7` | `2dc9c853bcdbb159d1475978722ef71548c5580fff22049a4055b52e3ec18dd2` |
| `tests/test_pr_play_post_npc_handoff.py` | `b86f17f469595119cc2085a908dc5d84b6d650bdd0c3a926c55281c6b3c16a98` | `7484052936459db0915a807c6c5938be5e30019aa5d7377846c25ee1f2a24e94` |
| `tests/test_pr_play_t04_local_action.py` | absent | `8c261b8ca7c40cb90b56141f3c0a098ab5e424c39c77cc0e713aaa1ba4d36bfe` |

## Handoff

`docs/NEXT_SESSION.md` is prepended. The previous bytes are kept as `artifacts/pr_play_t04_local_action/entry/docs/NEXT_SESSION.md` and remain the suffix of the updated file. Archive path and SHA-256 are in `archive_sha256.txt` after the seal.

## Evidence

`artifacts/pr_play_t04_local_action/` holds the before T04 trace, after T04 trace, twelve-turn summary, source manifests, production diff, and junit.
