# Verification budget

## Original mismatch

The F3 HTTP script, `artifacts/pr_play_79df3/http_acceptance.py`, set request limit 4, input 100,000, output 100,000, and total 200,000 before importing the app. Admission used those ceilings. The 3,000-token verification cap was never written into them.

## Corrected path

The script now calls `apply_verification_budget()` from `game/verification_budget.py` at that same point, before `game.api` is imported. The function writes the four `ASHEN_PROVIDER_*` variables that `provider_budget.limits` already reads, plus `ASHEN_VERIFICATION_BUDGET_SOURCE` and `ASHEN_VERIFICATION_BUDGET_TOTAL`.

A missing total installs 3,000. Input defaults to that total. Output defaults to the smaller of 600 and that total. A malformed value raises `VerificationBudgetRejected` before any write. Requesting total 200,000 without an override raises the same way, so the old ceiling cannot be selected by omission. `override=8000` or `override=200000` is applied and recorded as source `override`.

This profile is the verification entry point. It is not the production opening cap. `limits()` still returns nothing when `ASHEN_PROVIDER_REQUEST_LIMIT` is unset. The classification helper `tests/pr_play_79df3_harness.py` still passes explicit ceilings, including 200,000, when a test asks for them. Those tests are not the HTTP verification profile.

The script’s `continuation_advances` check still describes the historical publication. This cycle did not run the script.

## Runtime admission

`admit_request` is unchanged. It refuses on request count, input, output, or total before `RequestAttempt.dispatch` calls the provider function. A refusal raises `ProviderBudgetRefused` and leaves `dispatched` false.

An estimate of 28,000 input and 600 output against the 3,000 profile is refused as `input-token ceiling` because the profile’s input allowance is also 3,000. The fake invoke count stays 0. A 100-input, 40-output request is admitted and the fake boundary runs once. Two admitted requests that consume a 500-token total leave the next estimate refused as `total-token ceiling`.

A GM object tagged `provider_budget_refused` is stamped as an operational refusal. `note_completed_publication` does not advance `last_publication`, and `record_completed_publication` writes no gameplay event.

## Estimate uncertainty

Narration’s pre-dispatch estimate, when accounting is active, is `len(utf-8 json bytes) // 3 + 64`, and the attempt reserves the narration output cap (default 600). Interpretation uses the same bytes/3 shape and includes its schema. The check compares that estimate plus the reservation with the configured ceilings. The completed ledger stores the usage the provider function returns, which the tests keep distinct from the estimate (estimated 100, actual total 14).

The bytes/3 figure is a conservative stand-in for a bytes/4 count. It is not the provider tokenizer. A 3,000 configured total therefore guarantees that an estimate which does not fit is refused before dispatch. It does not guarantee that every admitted request’s actual provider total is under 3,000.
