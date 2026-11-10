# 09 — Final Verdict and Handoff

**B — Conditionally ready for controlled live validation.**

Authority, opening integrity, compatibility, and the provider budget hold. The remaining limits are the small reviewed-variant set, the unmeasured live token effect, and the preexisting prompt exposure of GM-only context that this pass does not publish. Those are not publication holes. They are reasons to review a live opening before treating the wording as the product default.

## Implemented

- Default-off `ASHEN_OPENING_RENDERER`.
- Engine public catalog, closed presentation plan, and traceable renderer.
- Opening publication that uses the trace and drops model narration and model updates.
- Harness selection and a deterministic five-turn run that accepts the opening, plays four turns, and stops at six synthetic requests.

## Source

- `game/opening_presentation_renderer.py`
- `game/gm.py`
- `game/api.py`
- `tools/playtest/worker.py`
- `tools/playtest/runner.py`
- `tests/test_pr_play_13_opening_renderer.py`

## Tests

30 focused tests passed. Legacy opening and claim-authority suites passed. The PR-PLAY-12 selection reported 871 passed, 19 failed, and 2 errors in the busy batch. Fourteen failures are the preexisting baseline. Seven were Windows file races and passed in isolation. No relevant new regression remains.

## Flag

Leave `ASHEN_OPENING_RENDERER` unset for production behavior. Set it to `1` only for a controlled opening trial. Do not change the model, output cap, or retry settings for that trial.

## Next action

External review of this archive. Do not start the live validation from this pass.

## Closeout

- No live provider calls.
- No provider connectivity tests.
- No provider-model changes.
- No output-budget increases.
- No automatic provider retries.
- No global semantic-validator relaxation.
- No unrestricted model narration in renderer mode.
- No hidden-information relaxation.
- No state-authority relaxation.
- No ordinary gameplay rule changes.
- No new persistent gameplay structures.
- No experimental PR-EG integration.
- Frozen ATGB baseline unchanged.
- No commit or push.
