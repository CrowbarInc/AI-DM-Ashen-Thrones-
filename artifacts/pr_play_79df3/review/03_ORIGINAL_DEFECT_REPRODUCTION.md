# Original Defect Reproduction

Reproduced on the real HTTP boundary before the product edit. The traces were not rerun after the repair, because the repaired source no longer shows the defect.

## Admission refusal

`artifacts/pr_play_79df3/reproduce_defect.py` wrote `reproduction_trace.json` and `reproduction_events.jsonl`.

Setup: a session with one completed gameplay publication. Playtest SDK retries enabled. Request limit 0, so admission refuses before dispatch.

Observed for “Good day, Gate Guard.” and the other recorded phrases:

- HTTP 200
- Player-visible playtest stop message
- 0 provider requests
- 0 tokens
- Turn stayed 4
- `session.last_publication` stayed on the preceding Gate Guard sentence
- World state unchanged
- Each refusal appended a publication event with `validation_outcome=engine_or_grounded_fallback`, `publication_owner=completed_runtime_response`, and `response_category=engine_response`

That is the disagreement: the HTTP event says a gameplay publication completed, and the session pointer says it did not.

## Interpretation refusal

`reproduce_interpretation.py` wrote `reproduction_interpretation.json`.

Without the playtest flag, both the input-token ceiling and accounting-unavailable paths returned “I couldn't interpret that just now, so no gameplay action was taken.” The pointer and turn stayed put. Requests and tokens stayed 0. The publication event was still `engine_or_grounded_fallback`.

The two paths differ in the player sentence only when the playtest gate is on. Both were misclassified the same way.
