PR-DV Response Repairs

Files touched for PR-DV:

- `game/api_turn_support.py`
  - Added generic-output detection for `The action resolves`.
  - Added resolver-fact extraction for visible surfaces, clues, social topics, transitions, and failures.
  - Added a preservation pass with emission debug metadata.

- `game/api.py`
  - Added early stored-interpretation failure response.
  - Reused the prevalidated stored interpretation instead of calling the hook twice.
  - Reapplied resolver-fact preservation after late post-GM mutation/adoption.

- `tests/test_pr_du_player_pipeline.py`
  - Added PR-DV focused tests for generic final text and rejected interpretation fallback blocking.
