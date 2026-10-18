# PR-CJ Reconciliation Report

MODE: BOUNDED DETERMINISTIC DIAGNOSTIC WITH CONDITIONAL MINIMAL REPAIR
LIVE CALLS: 0

PR-CI inherited decision: A — AUTHORED ANSWER FINALIZATION REPAIRED

## Worktree

HEAD `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. The worktree was already dirty. It was not reset. No unrelated modification was overwritten. No game or test file was edited.

## Inventory

`tests/test_turn_pipeline_shared.py`: 33 failed, 32 passed.

The failures group into nine clusters:

| Cluster | Tests | Confidence |
| --- | --- | --- |
| A. Non-social text selected as a social ask | 11 | CONFIRMED |
| B. Place adjudication preempts narration retry | 2 | CONFIRMED |
| C. Immutable retry prompt replaces validator-voice target | 1 | CONFIRMED |
| D. Chat returns a resolution shell instead of null | 2 | CONFIRMED |
| E. Stock and scaffold phrases survive emission | 4 | SUPPORTED |
| F. Speaker, reply kind, and progression repairs | 8 | SUPPORTED |
| G. Exploration selected, metadata assert not recovered | 3 | POSSIBLE |
| H. Owned contract drops embedded roll metadata | 1 | SUPPORTED |
| I. Referential follow-up becomes clarification | 1 | SUPPORTED |

## Confirmed mechanism for the largest cluster

Unmatched player text becomes `operation=ask`. Leftover asks become `resolution_subject=social`. The social resolver then refuses the exploration and passive-wait stages. "I investigate the desk." never reaches the exploration parser. "I wait." never arms scene-stall retry. Hard-valid atmosphere is replaced by "No one here can answer that from what is settled here."

`/api/action` with an explicit investigate payload still discovers the desk clue. The break is chat selection, not the clue resolver itself.

## Historical attribution

At HEAD, the same suite has 6 failures, not 33. Twenty-seven current failures pass on the committed tree. The six that already fail do so on different assertions, except the two pressure tests, which already lack concrete pressure.

PR-CC, PR-CE, and PR-CI are not separate commits. The 27 new failures are attributed to the uncommitted stack after PR-BN, not to one of those names. PR-CI's file list does not contain the selector, and PR-CI already recorded the 33 failures.

## Repair

Not implemented. The largest cluster needs a resolver-selection change. A verb-list patch would not cover the cluster, and rewriting the ask default would retarget ordinary gameplay. Tests were not weakened.

## Authority

No provider sentence was observed becoming clue or decision state. Chat investigation omits an authored clue. Immutable and authority suites passed.

## Focused regression

Social relevance 25 passed. PR-CC 11 passed. PR-CE 13 passed. PR-BY 22 passed. PR-BW 5 passed. Immutable 27 passed. Authority 107 passed. Shared pipeline remains 33 failed, 32 passed.

## Decision

C — MULTIPLE INDEPENDENT DEFECTS

## Recommended next step

One cycle for cluster A only: stop selecting the social resolver for non-addressed investigation, bare waits, and unmatched narration, without changing place adjudication, the HTTP null-resolution shape, the validator-voice prompt, stock-phrase sanitizing, or speaker repair.
