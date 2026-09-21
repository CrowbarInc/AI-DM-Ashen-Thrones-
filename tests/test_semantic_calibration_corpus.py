"""Regression tests for the human-labeled semantic calibration corpus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.playability_eval import evaluate_playability

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "validation" / "semantic_calibration"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_semantic_calibration_corpus_matches_expected_labels() -> None:
    manifest = _load_json(CORPUS / "manifest.json")
    disagreements: list[str] = []

    for rel in manifest["cases"]:
        case = _load_json(CORPUS / "cases" / rel)
        out = evaluate_playability(
            {
                "player_prompt": case["player_input"],
                "gm_text": case["gm_response"],
            }
        )
        if out["semantic_result"] != case["expected_semantic_result"]:
            disagreements.append(
                f"{case['case_id']}: semantic expected {case['expected_semantic_result']} got {out['semantic_result']}"
            )
        for gate_name, expected_status in case["expected_mandatory_gates"].items():
            actual_status = out["mandatory_gates"][gate_name]["status"]
            if actual_status != expected_status:
                disagreements.append(
                    f"{case['case_id']}: {gate_name} expected {expected_status} got {actual_status}"
                )

    assert disagreements == []
