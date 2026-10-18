"""One-shot regression driver for PR-DO. Not part of the contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITES = (
    ("PR-DO", ["tests/test_pr_do_authority_separation.py"], 120),
    ("PR-DN", ["tests/test_pr_dn_interpretation_robustness.py"], 120),
    ("PR-DM", ["tests/test_pr_dm_hybrid_refinement.py"], 180),
    ("PR-DL", ["tests/test_pr_dl_interpretation_comparison.py"], 180),
    ("PR-DK", ["tests/test_pr_dk_escalation_routing.py"], 180),
    ("PR-DJ", ["tests/test_pr_dj_selective_interpretation.py"], 180),
    ("authority", ["tests/test_pr_cx_authority_assurance.py"], 180),
    ("turn-pipeline", ["tests/test_turn_pipeline_shared.py"], 300),
)


def main() -> None:
    out = ROOT / "artifacts" / "pr_do_authority_separation" / "regression_stdout.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[str] = []
    for name, args, timeout in SUITES:
        command = [sys.executable, "-m", "pytest", *args, "-q", "--tb=line"]
        header = f"SUITE {name} timeout={timeout}s command={' '.join(command[1:])}"
        print(header, flush=True)
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            body = (completed.stdout + "\n" + completed.stderr).strip()
            block = f"{header}\nreturncode={completed.returncode}\ntimed_out=False\n{body}\n"
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            block = f"{header}\nreturncode=None\ntimed_out=True\n{stdout}\n{stderr}\n"
        chunks.append(block)
        print(block[-500:], flush=True)
    out.write_text("\n\n".join(chunks), encoding="utf-8")


if __name__ == "__main__":
    main()
