# 08 — Final Verdict and Handoff

## Verdict

**B — Conditional acceptance**

The opening acceptance and commit-integrity repair meets the bounded host requirements under deterministic stubs. Live generation and a clean-tree bisect of three rich-text length assertions remain unresolved. That is a limited validation concern, not a failed primary control.

## Evidence for the verdict

- Pre-change reproduction still showed the PR-PLAY-03 defects: missing envelope became `safe_nonresolution` and committed progression; a pipeline exception left pressure and faction ticks.
- Post-change standalone and 18 integration tests: invalid openings return HTTP 422 and match the baseline; a valid opening commits once; repeats and concurrent starts do not duplicate progression; budget rejection stays before dispatch.
- Structured validation, prompts, schemas, models, and token limits were not relaxed or changed.
- Ordinary non-opening `safe_nonresolution` is not treated as an opening.
- PR-PLAY-02 constructor and admission tests in the focused slice passed.
- Two legacy HTTP tests that complete an opening from `"[Narration]"` now receive the explicit failure. That is the repair, not a weakened contract.
- Three rich-opening HTTP tests still return 200 with gate text length 781. They were not bisected. They are not treated as a new acceptance hole.

## Remaining uncertainty

- The live model may still fail to produce a valid envelope. The original raw response is unknown.
- World persistence is best-effort restore, not crash-atomic.
- The accounting fingerprint test stays red on this dirty tree. It was not updated.
- The full suite was not run.

## Retain the implementation

Yes. Reverting would restore the false-success opening and the partial pressure commit.

## Live playtesting

May not resume. Await external review.

## Recommended next action

Review this package. Do not start a live playtest, and do not open a follow-on repair, until that review accepts or redirects the conditional items.

## Confirmations

- No live provider calls.
- No provider connectivity diagnostics.
- No prompt, schema, model, or output-token-limit changes.
- No additional provider operations.
- No new persistent gameplay structures.
- No experimental PR-EG integration.
- Frozen ATGB baseline unchanged.
- No unauthorized gameplay-state mutations beyond the opening commit rule above.
- No secrets included.
- No commit or push performed.
