"""One-shot holdout. Expected labels were frozen before the validator edit."""
from __future__ import annotations

import json
from pathlib import Path

from tests.pr_play_55_evaluate import (
    repeated_development_latency,
    score_development,
    score_holdout,
    score_previous,
)

OUT = Path(__file__).resolve().parents[1] / "artifacts" / "pr_play_55"


def test_frozen_holdout_matches_expected_decisions():
    OUT.mkdir(parents=True, exist_ok=True)
    holdout = score_holdout()
    development = score_development()
    previous = score_previous()
    latency = repeated_development_latency()
    payload = {
        "holdout": {key: value for key, value in holdout.items() if key != "rows"},
        "holdout_rows": holdout["rows"],
        "development": {key: value for key, value in development.items() if key != "rows"},
        "development_rows": development["rows"],
        "previous_scored_corpus": previous,
        "repeated_development_latency": latency,
    }
    (OUT / "evaluation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    assert holdout["manifest_sha256"] == "24ff35e8f4096e865dcf3ffd6f98a92d18a208e1329c445c33525e5e5fed1495"
    assert holdout["critical_false_negative_ids"] == []
    assert holdout["mismatch_ids"] == []
    assert holdout["provider_requests"] == 0
    assert previous["critical_false_negatives"] == []
    assert previous["fabrication_fail"] == 49
