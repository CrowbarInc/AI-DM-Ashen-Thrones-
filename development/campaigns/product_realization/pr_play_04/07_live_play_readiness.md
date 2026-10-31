# 07 — Live-Play Readiness

## Deterministic host path

The campaign-opening host path is ready for review under controlled provider responses. A valid structured opening commits once. An invalid, empty, malformed, or exceptional opening fails explicitly and does not advance turn, time pressure, faction state, or `campaign_started`. A later explicit Start can still succeed when the admission budget allows.

## Remaining provider-generation uncertainty

The original live rejection was `missing_structured_envelope`. The raw provider body was not kept. This pass does not change prompts, schemas, models, or token limits, so it does not make the live model more likely to emit a valid envelope. A future live Start can still fail the opening. That failure should now be the explicit message, with gameplay left unstarted.

Stub results are not evidence that the live model will open correctly.

## Remaining persistence risk

Caught exceptions and a caught world-save error restore the pre-attempt baseline. `save_world` is not an atomic multi-file commit. A process kill during the success write can still tear `world.json`. Do not describe the opening as crash-transactional.

## Manual playtest

A new manual playtest is not justified until this review is accepted. Live play must not resume from this package alone.

If a later review authorizes a playtest, use the existing PR-PLAY-02 launch: one worker, no reload, a fresh disposable data directory, `ASHEN_PLAYTEST_DISABLE_SDK_RETRIES=1`, and the existing request limit. New Campaign and Start Campaign stay separate. Capture the opening response, the `opening_failure_reason` when present, session `campaign_started` and turn, clocks, faction rows, and the provider ledger. Do not restart a budget-stopped session to continue it.

## Stop conditions for that future playtest

Stop the session if any of these occur:

- The explicit opening failure is shown and turn, time pressure, or faction pressure still advanced.
- A second Start after success produces another opening or another faction tick.
- The UI shows the generic “No one here can answer that” line as a completed opening.
- The budget stop message appears and another provider call is still issued.
- Raw provider errors or secrets appear in the player message.

Do not run that playtest as part of this pass.
