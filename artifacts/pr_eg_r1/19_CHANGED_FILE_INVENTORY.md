# 19 — Changed-File Inventory

## Production

| File | Purpose |
| --- | --- |
| `game/conversational_continuity.py` | Delivered-exchange store, reference precedence, quote and decline lines, personal-ignorance test, commitment reuse lookup. |
| `game/conversational_orchestration.py` | Turns a continuity directive into the existing decision. An ordinary question to the active NPC is not answered with the empty-evidence GM line. |
| `game/dialogue_authority.py` | Quotes a delivered clarification. Reuses a preference. Treats "maker" questions as determined unknowns. Rejects `emitted_<hex>` as internal voice. |
| `game/ordinary_semantic_ownership.py` | Skips narration when the authority record is reusing a delivered line. |
| `game/immutable_valid_response.py` | Replaces an ignorant preference without a retry. Does not interpolate an internal token into an inspection fallback. |
| `game/api.py` | Records the sealed line. Replaces a final ignorant preference before that record. Declines store a withheld commitment. |
| `game/prompt_context.py` | Tells a permitted preference not to claim ignorance and not to add a patrol, payment, or hidden fact. |

## Tests

| File | Purpose |
| --- | --- |
| `tests/fixtures/pr_eg_r1_continuity_holdouts.json` | Twenty frozen cases. Expectations were not rewritten after results. |
| `tests/test_pr_eg_r1_continuity.py` | Scores those cases, recovery, and the zero-call quote. |
| `tests/fixtures/pr_eg_r1_live_expectations.json` | Frozen live checks for both conversations. Not edited after provider output. |

## Tooling

| File | Purpose |
| --- | --- |
| `tools/validate_pr_eg_r1.py` | Two disposable `/api/chat` conversations. Writes `artifacts/pr_eg_r1/live_qualification.json`. |

## Evidence

- `artifacts/pr_eg_r1/baseline_junit.xml`
- `artifacts/pr_eg_r1/regression_junit.xml`
- `artifacts/pr_eg_r1/live_qualification.json`
- `artifacts/pr_eg_r1/live.usage.jsonl`
- Reports 01–19

PR-EF-R4 authorization tests and PR-EG dialogue-quality tests were run and pass. They were not rewritten.
