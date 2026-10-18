# 02 — Baseline and Environment

## Repository

- Revision: `d31beb7d73dd4fda0f22184a6a69b947b5f470ff` (“PR-BN bounded DM improvisational authority”).
- The working tree was already dirty relative to that revision before this cycle. This cycle did not revert unrelated files and did not create a commit.
- `game/api.py` is modified. The other cycle files are untracked in git because those modules were already untracked on this tree.

## Provider

- Configured model: `gpt-4.1-mini` (`experiments/pr_dp/__init__.py`).
- Observed live model: `gpt-4.1-mini-2025-04-14`.
- The key was loaded from the local `.env` by the app’s dotenv load. It is not recorded in the artifacts.
- Live transport: FastAPI `TestClient` posting to `/api/chat?ui_mode=player` with storage patched to a temporary directory. In-process ASGI, not a separately hosted server.
- Budget for the qualification process: 160 requests, not exhausted. The completed run sent 49 requests.

## Interpretation flag

Importing `experiments.pr_dq` sets `ASHEN_DISABLE_LIVE_INTERPRETATION=1`. An initial qualification attempt left that flag on, so the legacy parser handled the turns and a GM description ticked the world. That attempt is not the qualification. It is saved as `live_qualification_interpretation_disabled.json`. The reported run sets the flag back to `0` after those imports. Every reported turn has an interpretation call where the production path asks for one, except deterministic moves and the conditional, which correctly make no provider call.

## Test baseline

PR-EF-R3 did not re-run the family. The last historical measurement remains PR-EF-R2: **321 passed / 20 failed**. This cycle did not re-establish that count on unmodified code before the edit. The post-implementation measurement is the current one.

Post-implementation family (the R2 file list plus `test_pr_ef_r2_social_authority.py` and `test_pr_ef_r4_authorization.py`):

- **349 passed / 20 failed**
- The 20 failure identities are exactly the PR-EF-R2 historical twenty.
- `tests/test_pr_ef_r4_authorization.py`: 28 passed, 0 failed, including the 25 frozen cases under scripted providers.

Command and junit: `artifacts/pr_ef_r4/regression_junit.xml`.
