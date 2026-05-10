#!/usr/bin/env python3
"""Run informational governance audits (local parity with convergence-checks.yml).

Exits with the maximum subprocess return code so advisory steps that fail still
surface locally. Does not run pytest or strict audits — use the workflow doc or
``docs/convergence_ci_inventory.md`` for the full hard-fail list.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (step label, argv after cwd=ROOT). Labels mirror .github/workflows/convergence-checks.yml.
_AUDITS: list[tuple[str, list[str]]] = [
    (
        "Architecture audit - print summary (informational)",
        [sys.executable, "tools/architecture_audit.py", "--print-summary"],
    ),
    ("Realization layer audit (informational)", [sys.executable, "tools/realization_layer_audit.py"]),
    (
        "Realization provenance audit (informational)",
        [sys.executable, "tools/realization_provenance_audit.py"],
    ),
    ("C1 narration seam audit (informational)", [sys.executable, "tools/c1_narration_seam_audit.py"]),
    ("UI mode separation audit (informational)", [sys.executable, "tools/ui_mode_separation_audit.py"]),
]


def _exit_code(returncode: int | None) -> int:
    return 0 if returncode is None else returncode


def main() -> int:
    rc = 0
    for label, argv in _AUDITS:
        cmd_display = " ".join(argv)
        print(f"\n== {label} ==\n$ {cmd_display}\n", file=sys.stderr, flush=True)
        r = subprocess.run(argv, cwd=ROOT, check=False)
        step_rc = _exit_code(r.returncode)
        rc = max(rc, step_rc)
        if step_rc != 0:
            print(f"(exit {step_rc})", file=sys.stderr, flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
