# PR-CF Baseline Attribution

HEAD: d31beb7d73dd4fda0f22184a6a69b947b5f470ff

Preserved PR-CE evidence says the broad suite completed with 7431 passed, 202 failed, 99 skipped, and no timeout/interruption. The PR-CE JUnit XML was referenced as `artifacts/pr_ce_readiness_closeout/broad.xml` but is absent from both the working tree artifact directory and `handoff/CURRENT_REVIEW.zip`.

Attribution is therefore partial. PR-CE itself established that the four social relevance HTTP narration failures reproduced before the PR-CE subjective-classifier edit, so they are not introduced by PR-CE. PR-CE focused classification and authority controls passed after the social.py edit, which weakens the case that the subjective classifier caused the broad spread.

The worktree is heavily dirty across production, test, artifact, data, and handoff files, including many PR-BR through PR-CE additions. Several non-noise signatures are governance or expectation drift against newly added/renamed tests and tools. Those are most likely interaction with unrelated dirty worktree/test-suite evolution rather than PR-CE logic.

A current representative HTTP rerun reproduced the Windows TestClient/socketpair accept hang frame that PR-CE did not reproduce. That is an environment/infrastructure instability, not an application assertion regression, and it prevented safe fresh reproduction of HTTP-heavy clusters in this cycle.

Confirmed preexisting: 4 social relevance HTTP narration failures before PR-CE classifier edit.
Confirmed PR-CC regressions: 0.
Confirmed PR-CE regressions: 0.
Unattributed: remainder of the 202 broad failures.
