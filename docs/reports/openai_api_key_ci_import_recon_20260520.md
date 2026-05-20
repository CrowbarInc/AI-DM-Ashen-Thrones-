# OPENAI_API_KEY CI Import Recon - 2026-05-20

## Summary

GitHub Actions is failing during pytest collection because importing `tests/test_dead_turn_evaluation_threading.py` imports a helper that pulls in the live API stack at module import time. That stack imports `game.gm`, which imports `OPENAI_API_KEY` from `game.config`; `game.config` validates `OPENAI_API_KEY` immediately at module import.

This is primarily a production config design issue plus a helper/test boundary issue. It is not a true live-API test requirement for `tests/test_dead_turn_evaluation_threading.py`, and it is not only a CI missing-env issue. CI exposes the problem because it does not have the local repo `.env` file.

## Failure Cause

The target test only uses `snapshot_from_chat_payload` from `tests.helpers.transcript_runner`, but importing that helper module also imports `chat` from `game.api` for unrelated transcript execution helpers. That import is top-level and happens during collection, before any test body runs.

Relevant import-time path:

```text
tests/test_dead_turn_evaluation_threading.py
-> tests/helpers/transcript_runner.py
-> game/api.py
-> game/gm.py
-> game/config.py
-> _getenv_required("OPENAI_API_KEY")
```

The key import-time secret requirement is:

```text
game/config.py:53: OPENAI_API_KEY = _getenv_required("OPENAI_API_KEY")
```

That means any import of `game.gm`, `game.api`, or modules importing `OPENAI_API_KEY` from `game.config` can fail before pytest collects tests.

## Import Chain Evidence

Line evidence:

```text
tests/test_dead_turn_evaluation_threading.py:16: from tests.helpers.transcript_runner import snapshot_from_chat_payload
tests/helpers/transcript_runner.py:13: from game.api import chat
game/api.py:103: from game.gm import (
game/gm.py:6: from game.config import OPENAI_API_KEY
game/config.py:53: OPENAI_API_KEY = _getenv_required("OPENAI_API_KEY")
game/gm.py:4945: def call_gpt(
game/gm.py:4967: client = OpenAI(api_key=OPENAI_API_KEY)
tests/conftest.py:11: os.environ.setdefault("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
```

`tests/conftest.py` suppresses upstream API preflight, but it does not provide `OPENAI_API_KEY` or prevent import-time validation in `game.config`.

The helper design issue is specific: `snapshot_from_chat_payload` itself only needs snapshot assembly utilities, but it lives in a module that eagerly imports `game.api.chat` for `run_transcript_turns` and `run_transcript`.

## Local vs CI Behavior

Local environment findings:

```text
OPENAI_API_KEY present in .env
OPENAI_API_KEY absent from shell environment
```

Because `game/config.py` calls `load_dotenv(dotenv_path=ENV_PATH)` at import time, local tests pass when the repo-root `.env` contains `OPENAI_API_KEY`. CI does not have that `.env`, so import-time validation raises during collection.

Requested command results:

```text
python -m pytest tests/test_dead_turn_evaluation_threading.py -q
```

Result in this PowerShell environment:

```text
python : The term 'python' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Using the available bundled Python with `.venv` site-packages:

```text
$env:PYTHONPATH='.\\.venv\\Lib\\site-packages'
python.exe -m pytest tests\\test_dead_turn_evaluation_threading.py -q
........                                                                 [100%]
```

Requested collect-only command:

```text
python -m pytest tests/test_dead_turn_evaluation_threading.py --collect-only -q
```

Result in this PowerShell environment:

```text
python : The term 'python' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Using the available bundled Python with `.venv` site-packages:

```text
tests/test_dead_turn_evaluation_threading.py: 8
```

CI-like simulation with dotenv disabled and no shell `OPENAI_API_KEY`:

```text
ERROR collecting tests/test_dead_turn_evaluation_threading.py
tests/test_dead_turn_evaluation_threading.py:16: in <module>
    from tests.helpers.transcript_runner import snapshot_from_chat_payload
tests/helpers/transcript_runner.py:13: in <module>
    from game.api import chat
game/api.py:103: in <module>
    from game.gm import (
game/gm.py:6: in <module>
    from game.config import OPENAI_API_KEY
game/config.py:53: in <module>
    OPENAI_API_KEY = _getenv_required("OPENAI_API_KEY")
game/config.py:34: in _getenv_required
    raise RuntimeError(f"Missing required environment variable: {name}")
E   RuntimeError: Missing required environment variable: OPENAI_API_KEY
```

Requested grep command:

```text
grep -R "OPENAI_API_KEY\|_getenv_required\|from game.api import\|import game.api\|from game.gm import\|import game.gm" game tests -n
```

Result in this PowerShell environment:

```text
grep : The term 'grep' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Equivalent `rg` search found the relevant import-time sites, including:

```text
game/config.py:31:def _getenv_required(name: str):
game/config.py:53:OPENAI_API_KEY = _getenv_required("OPENAI_API_KEY")
game/api_upstream_preflight.py:17:from game.config import DEFAULT_MODEL_NAME, OPENAI_API_KEY
game/api.py:103:from game.gm import (
game/gm.py:6:from game.config import OPENAI_API_KEY
game/gm.py:4967:        client = OpenAI(api_key=OPENAI_API_KEY)
tests/helpers/transcript_runner.py:13:from game.api import chat
tests/test_dead_turn_evaluation_threading.py:16:from tests.helpers.transcript_runner import snapshot_from_chat_payload
tests/conftest.py:11:os.environ.setdefault("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
```

The broader search also shows many tests import `game.api` or `game.gm`; these are all potentially sensitive to import-time config validation unless CI provides a key or config becomes lazy.

## Fix Options Compared

### A. Add dummy `OPENAI_API_KEY` in GitHub Actions env

Files touched:

- `.github/workflows/convergence-checks.yml`
- Possibly `.github/workflows/content-lint.yml` if any imported stack can collect there

Blast radius:

- Low operationally; affects CI environment only.

Evaluator boundary purity:

- Does not preserve purity. Evaluator tests still import the runtime API/GPT stack during collection.

Hides architecture problem:

- Yes. It masks import-time secret validation and helper over-importing.

Short-term vs proper:

- Good emergency unblock if the team wants CI green immediately.
- Not a proper fix.

### B. Make `game/config.py` lazy-load required secrets only when API/client code is invoked

Files touched:

- `game/config.py`
- `game/gm.py`
- `game/api_upstream_preflight.py`
- Tests for model/config behavior, likely `tests/test_model_routing_config.py` and preflight tests

Blast radius:

- Medium to high. Many modules import `game.gm` and `game.api`; changing config shape can affect runtime and tests.

Evaluator boundary purity:

- Improves collection robustness, but does not by itself stop evaluator tests from importing the runtime stack.

Hides architecture problem:

- No. It fixes the production design issue: importing a config module should not require secrets unless the secret-backed client is actually being created or called.

Short-term vs proper:

- Strong proper fix, but needs careful testing.

### C. Split `tests/helpers/transcript_runner.py` so snapshot fixture helpers do not import `game.api` or chat

Files touched:

- `tests/helpers/transcript_runner.py`, or a new helper such as `tests/helpers/transcript_snapshots.py`
- `tests/test_dead_turn_evaluation_threading.py`
- Any other tests that only need snapshot helpers

Blast radius:

- Low to medium. The change can be targeted around helper imports.

Evaluator boundary purity:

- Best option for this specific failing boundary. The dead-turn evaluator test would no longer import chat/API just to assemble a snapshot.

Hides architecture problem:

- No for test architecture; yes partially for production import-time config if done alone. It avoids the bad import path for this test but does not eliminate import-time secret validation elsewhere.

Short-term vs proper:

- Best proper fix for the immediate evaluator-boundary failure.
- Should be paired later with lazy config for broader robustness.

### D. Patch/mock env in pytest/conftest before imports

Files touched:

- `tests/conftest.py`

Blast radius:

- Medium. It silently affects every test process and can make tests believe a key exists.

Evaluator boundary purity:

- Does not preserve purity. Evaluator tests still import runtime API/GPT stack.

Hides architecture problem:

- Yes. It masks import-time secret validation across the whole suite.

Short-term vs proper:

- Viable short-term CI unblock, but weaker than workflow env because it pollutes test assumptions globally.
- Not a proper fix.

### E. Mark/skip live-API tests unless explicitly enabled

Files touched:

- Tests that truly perform upstream calls
- Possibly `tests/conftest.py`
- Possibly pytest markers/config

Blast radius:

- Medium. Requires classifying live vs non-live tests.

Evaluator boundary purity:

- Helps if live tests are accurately marked, but does not fix collection if importing the module fails before marks can matter.

Hides architecture problem:

- Partially. It is appropriate for live API tests, but this specific test is not live API and should not need the API stack at collection.

Short-term vs proper:

- Good proper policy for real upstream tests.
- Not sufficient for this failure unless combined with lazy imports/config.

## Recommended Fix

Recommended immediate implementation: Option C.

Split snapshot-only helpers away from `tests/helpers/transcript_runner.py` or make the `game.api.chat` import lazy inside `run_transcript_turns`. Then update `tests/test_dead_turn_evaluation_threading.py` to import the snapshot helper from a module that does not import `game.api` or `game.gm`.

This preserves evaluator boundary purity and directly addresses why a dead-turn evaluator test imports live chat/API code during collection.

Recommended follow-up: Option B.

Change production config so `OPENAI_API_KEY` is retrieved and validated only when upstream client code actually needs it. This removes a fragile import-time secret requirement across the codebase.

Avoid as primary fixes:

- Option A and D unblock CI but hide the architectural smell.
- Option E is useful for true live API tests, but this target test is not live API and should collect without secrets.

## Recommended Next Implementation Block

1. Create a snapshot-only helper module, for example `tests/helpers/transcript_snapshots.py`, containing:
   - `snapshot_from_chat_payload`
   - `_journal_summary`
   - `_world_summary`
   - `_compact_resolution`
   - `compact_snapshot_summary`
   - `latest_target_id`
   - `latest_target_source`
   - `format_turn_debug`

2. Keep transcript execution helpers in `tests/helpers/transcript_runner.py`, and have that module import `game.api.chat` only for functions that actually run chat turns.

3. Update `tests/test_dead_turn_evaluation_threading.py` to import `snapshot_from_chat_payload` from the snapshot-only helper.

4. Verify with a CI-like collection command where dotenv is disabled and `OPENAI_API_KEY` is absent:

```text
python -m pytest tests/test_dead_turn_evaluation_threading.py --collect-only -q
```

5. Add or update a boundary/import test that asserts the dead-turn evaluator test path can import snapshot helpers without importing `game.api` or `game.gm`.
