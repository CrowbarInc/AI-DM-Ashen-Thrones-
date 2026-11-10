# Grounded fallback publication

Deterministic HTTP coverage in `tests/test_pr_play_79df2_publication.py` forces a rejected NPC expression. The invalid line is not published. The grounded fallback is published. The publication event's validation is `engine_or_grounded_fallback`. `dialogue_accepted` is false. The pointer's visible text is the fallback, not the earlier accepted line. No accepted-expression reference is attached.

On the superseded fingerprint, a live question `Gate Guard, who was on the missing patrol?` was rejected (`unsupported_addition`, `uncertainty_not_expressed`, `asserted_unknown`). The published sentence was `Gate Guard says, "I couldn't tell you."` The pointer matched that sentence and `dialogue_accepted` was false. That process is not the final source. The final source did not repeat a live rejection. The controlled test on the repaired source is the fallback evidence for this verdict.

The two `Good day, Gate Guard.` turns on the final source are admission refusals, not grounded NPC fallbacks. They are described in the limitations note.
