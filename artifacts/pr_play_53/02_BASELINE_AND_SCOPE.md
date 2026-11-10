# Baseline and scope

## Repository

- Commit: `d40f1ed198236c604085f1c842ead267a8104ce2`
- Working tree: already dirty with unrelated tracked and untracked files. Those files were left in place. This pass did not commit or push.
- PR-PLAY-52 verdict on that tree: A — PASS / READY. Real provider requests in that pass: 0. Local hook work, excluding evidence writing, averaged about 3.8 ms. That figure is not a live-provider latency.

## What was reused

PR-PLAY-52 already calls `observe_completed_investigation` from `_run_resolved_turn_pipeline` after authoritative mutation and after the player-facing object exists. The hook's return value is discarded. `game/api.py` was not edited.

The default quarantine path is unchanged. It replays a saved prelude or the stub when `ASHEN_QUARANTINE_INVESTIGATION_NARRATION` is exactly `1`. A second flag, `ASHEN_QUARANTINE_NARRATION_LIVE=1`, is required before the hook calls the existing expression adapter. A fault injection suppresses that call.

The provider message is the PR-PLAY-50 prelude prompt plus the existing allowlisted projection from `prelude_request`. The projection carries the player action, public observations, authorized discovery text, and the descriptive constraints. It does not carry the scene catalog, hidden facts, GM notes, clue ids, hints, or skill-check rolls.

## What was not changed

- Canonical campaign fixtures and `data/` files. Hash comparison before and after the live run found no campaign-file changes and no `.env` change.
- Player-facing narration. `ASHEN_DISABLE_PROVIDER_CALLS` stayed set for the chat turn. The hook clears it only around its own adapter call, then restores it.
- Validator rules, token ceilings, and model configuration. The expression adapter's output cap remains 80 tokens.
- Ordinary play. Both flags default off. With the gate off, the quarantine module is not imported by the chat path.

## Source files for this pass

- `game/quarantined_investigation_narration.py` — live opt-in added to the existing hook.
- `tests/test_pr_play_53_quarantined_live.py` — fake-provider isolation, ceilings, and fabrication corpus.
- `artifacts/pr_play_53/` — experiment, regression, and this package.

`game/api.py` still must not name the anchored narration module, and it still must not assign the quarantine result to the player response. The PR-PLAY-49 and PR-PLAY-52 tests that enforce that were re-run.
