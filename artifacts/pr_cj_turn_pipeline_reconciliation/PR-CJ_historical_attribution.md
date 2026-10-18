# PR-CJ Historical Attribution

Live provider calls: 0. The current worktree was not reset.

## Baseline

HEAD is `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (`PR-BN bounded DM improvisational authority`) on `feature/product-realization`.

`game/resolution_contract.py` and `game/ordinary_semantic_ownership.py` exist on disk and are absent from HEAD.

## Isolated HEAD run

A detached worktree at HEAD was created, the suite was run with the project virtualenv, and the worktree was removed.

HEAD result for `tests/test_turn_pipeline_shared.py`: 6 failures.

| Test | HEAD failure | Dirty-tree failure |
| --- | --- | --- |
| investigate both endpoints | `inv-desk` missing from `searched_targets` (clue text is present) | chat `resolution.kind` missing |
| direct NPC unknown fallback | `social_response_structure_checked` is false | `reply_kind` is not `unknown` |
| single wait pressure | concrete pressure absent | concrete pressure absent |
| repeated passive pressure | concrete pressure absent | concrete pressure absent |
| suspicious figure | atmosphere kept; "the tattered man" absent | safe nonresolution replaces atmosphere |
| recent suspicious figure | same atmosphere result | same safe nonresolution |

The other 27 dirty-tree failures pass at HEAD.

## What that does and does not show

- The 33-failure set does not predate the uncommitted work. It is not the committed PR-BN behavior.
- Four pressure tests already fail at HEAD. Two of them changed failure mode after HEAD: atmosphere preservation became safe nonresolution. The dirty test file was edited to expect the atmosphere line, and current output no longer matches that edit or the original "tattered man" expectation.
- Investigate and the direct-NPC test already fail at HEAD, on earlier assertions. The dirty tree fails them sooner and for different reasons.
- PR-CI's recorded change list is `game/immutable_valid_response.py`, `game/social.py`, and `tests/test_social_question_relevance_answer_selection.py`. PR-CI's own report already counted these 33 failures as present before that repair. The social-default selector is not in that change list.
- There is no commit between HEAD and the worktree that isolates PR-CC, PR-CE, or PR-CI. Those cycles are uncommitted. This run cannot assign the 27 new failures to one of those three names.

## Attribution labels

| Set | Label |
| --- | --- |
| 6 tests listed above | Present at HEAD. Failure mode for investigate, direct NPC, and the two atmosphere tests has since changed. |
| 27 tests that pass at HEAD | Introduced by the uncommitted stack after PR-BN. Not isolated to PR-CC, PR-CE, or PR-CI. |
| Cluster C retry wording | Consistent with the immutable regeneration path PR-CI edited, but the 33-count predates that edit, so this cycle does not claim PR-CI created the cluster. |
| Cluster A selector | Lives in untracked contract modules that are not in HEAD and are not the PR-CI file list. |
