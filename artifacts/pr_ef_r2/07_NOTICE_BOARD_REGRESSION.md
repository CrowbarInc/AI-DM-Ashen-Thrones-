# 07 — Notice-Board Regression

Category A: brittle exact wording in a context with adequate referential clarity. experiments/pr_dq/world.py authors NOTICE_TEXT as “The board names the north road past the waystation.” The player explicitly requests the notice board, the action_id remains notice_board, prior arrival introduces a notice board, and state records the inspected interactable/clue. No established contract requires repeating “notice board” in the clue.

The PR-DU test now requires canonical action_id=NOTICE_ID, board, north road and waystation plus its existing movement, turn count, resolved-interactable and log assertions. This checks successful grounded reading without rewriting authored content. The inherited failure resolves; no production text was changed for this assertion. Exact before/after signature is in regression_comparison.json.
