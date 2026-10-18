# PR-DE Remaining Risks

## Unverified live behavior

The model now sees each removed contract once, inside `response_policy`. Deterministic validators still read that object. First-attempt acceptance and narration quality after the trim were not measured. A later live check belongs on an isolated save, using the benchmark's optional method, and only after an explicit request to call the provider.

## Measurement

`tiktoken` is not installed. Token figures are `ceil(chars/4)`.

N1's `clue_text_digest` uses Python's salted `hash()`. The PR-DE hash is stable only when `PYTHONHASHSEED=0`. It does not reproduce PR-DD's N1 hash. S2 and S3 reproduce the PR-DD hashes, not the PR-DC hashes, because the turn counter differs. Those anchors are fixture-local.

The API may still rewrite the user message with `ensure_ascii=True` after `build_messages`. Live HTTP bytes can differ from these hashes.

M1 still does not bind an exit. K1 and B1 are synthetic.

## Inherited failures

Authored-knowledge realization: 3 failed. Shared pipeline: 24 failed. Both sets match the pre-change run on this dirty worktree. They were not repaired.

`test_chat_begin_nonretryable_quota_repairs_malformed_opening_fast_fallback` fails with the omission function disabled. It is outside the required suite.

## Not done

Hidden facts are still sent. Instruction reinforcement was not compressed. The decision and the answer recipe were not compacted. History limits were not changed. Retry prompts were not rebuilt. No new provider profile was added.

## Worktree

HEAD `d31beb7d73dd4fda0f22184a6a69b947b5f470ff`. Pre-existing dirty files were preserved. Production saves were not modified.
