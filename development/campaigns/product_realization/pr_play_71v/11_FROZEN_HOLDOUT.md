# 11 — Frozen holdout

A new developer-authored holdout was frozen before it was executed. Manifest SHA-256: `84da3f7b288fac85a10b3c7b7b8b2a6f872276a9a2f1ef27833033736f45358e`. Sixty cases: 15 atomic, 10 rollback, 10 chat, 10 lifecycle, 5 transcript, 5 disclosure, 5 projection.

It was executed once against the source that includes `runtime_commit_scope`. Result: 59 passed, 1 failed. The failure is W12, a missing `expect_delays` key in the frozen case. The product assertions before that lookup passed. The case was not changed and the holdout was not run again.

This holdout is not independent external validation. The historical PR-PLAY-71 holdout of 46/50 was not rerun and was not edited.

W13 is the real Windows exclusive-lock case and passed.
