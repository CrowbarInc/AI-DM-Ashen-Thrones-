# 16 — Feature-Gate Behavior

`unified_semantic_planning_enabled()` reads `ASHEN_UNIFIED_SEMANTIC_PLANNING` at call time. The default is off.

Off: the proposer is not called, and the legacy topic selector still answers "who manages the ferry schedules?" with the harbor bell when that is the overlapping topic.

On: only explicit-addressee information questions, and corrections or follow-ups after a stored plan, enter the new path. The two paths are not both executed in order to keep the nicer answer.
