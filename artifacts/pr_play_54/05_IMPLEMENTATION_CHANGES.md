# Implementation changes

## Files

- `game/consequential_narration_validation.py` — authority snapshot, claim frames, and the four decisions. New.
- `game/anchored_investigation_narration.py` — `validate_prelude` applies the gate after the existing checker.
- `tests/pr_play_54_corpus.py` — 83 scored lines and the authority fixtures. New.
- `tests/test_pr_play_54_consequential_validation.py` — corpus, paraphrase, safety, and quarantine tests. New. 97 tests.
- `tests/test_pr_play_53_quarantined_live.py` — the key sentence is now a rejection that must stay off the player response. The fabrication table still locks the previous checker's pass/fail labels, and requires the new gate to reject consequential lines.
- `artifacts/pr_play_54/run_regression.py` — corpus measurement and the focused suite. Restores artifact files the suite rewrites.

## What did not change

`validate_generated_response` is unchanged. Player chat still returns the deterministic response. The live narration flag is unchanged. Campaign fixtures were not edited to satisfy the checker. No provider client was added.

## Gate behavior

A non-pass decision appends `consequential_fail`, `consequential_review_required`, or `consequential_validation_error` and forces `hard_valid` false. A pass from the new check does not delete an older rejection.

The source copies for review are under `source/` in this archive.
