"""Closeout doc checks for evaluator convergence boundaries."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_DOC = ROOT / "docs" / "evaluator_convergence_closeout.md"


def test_evaluator_convergence_closeout_doc_exists_and_freezes_invariants() -> None:
    assert CLOSEOUT_DOC.is_file()
    text = CLOSEOUT_DOC.read_text(encoding="utf-8").lower()

    for phrase in (
        "offline",
        "read-only",
        "no runtime repairs",
        "no gate legality authority",
        "no engine truth authority",
        "telemetry is observational only",
        "no policy by json",
    ):
        assert phrase in text
