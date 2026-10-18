# PR-DY authority validation

Production saves were unchanged after the cycle. The hashes are in the implementation report. All live writes went to `artifacts/pr_dy_live_gameplay/disposable_data`.

## Boundaries that held

- Explicit OOC in the browser did not change turn, time_pressure, scene, or the discovered clue, and it did not call a provider.
- Automatic OOC stopped on disposition `OUT_OF_CHARACTER` even though the payload contained an ASK component with a null target. That component did not run.
- Accepted inspect and ask each committed once. Narration refusal happened after resolution and did not write a second action.
- Requested outcomes in the interpretation records are marked `UNADJUDICATED`. The clue text matches the scene definition.
- The connector does not execute from narration text.
- Hidden-information probes in the interpretation contract block the turn, except probes that already appear in recent player-visible text.

## Unit checks with providers stubbed

`tests/test_pr_dy_live_gameplay.py` (included in the 99 passing focused tests):

- Unsupported operation does not call narration and does not advance the turn.
- Malformed JSON does not execute.
- Clarification does not mutate.
- Asking a perceive-only object as the wrong operation is bridge-rejected and does not execute.
- Explicit OOC does not call the interpreter.

## Limitation

`test_pr_dy_repeated_submission_commits_a_second_turn` shows that submitting the same inspect text again commits a second turn (`turn_counter` 2). Identical resubmission is not collapsed. That was recorded rather than blocked, because a second deliberate attempt can be a real action. No duplicate was observed in the live browser sequence: each gameplay sentence was different and each advanced the counter by one.

## Pre-commit and post-commit

Blocked interpretation returns before the turn increment. That is pre-commit: the disposable OOC turns left the counter at 3.

Inspect and ask incremented the counter and persisted the clue or the question result before narration was refused. The refusal did not roll the committed action back and did not commit it again.
