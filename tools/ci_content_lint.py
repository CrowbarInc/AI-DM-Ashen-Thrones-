#!/usr/bin/env python3
"""Thin CI entrypoint for author-time content lint.

Forwards to :func:`run_content_lint.main` with the same ``sys.argv``, exit codes, and
report semantics as ``tools/run_content_lint.py``. Prefer this path in automation so
workflows can depend on a single stable script name without duplicating flag logic.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_RUNNER = _ROOT / "tools" / "run_content_lint.py"


def _runner_main():
    spec = importlib.util.spec_from_file_location("_run_content_lint", _RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load content lint runner: {_RUNNER}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def main() -> int:
    return int(_runner_main()())


if __name__ == "__main__":
    raise SystemExit(main())
