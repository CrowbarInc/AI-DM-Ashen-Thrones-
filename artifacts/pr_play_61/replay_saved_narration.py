"""Replay the captured provider sentences through the corrected publication path.

No provider call. The original live capture remains experiment_results.json.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts" / "pr_play_61"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"

from game import integrated_investigation_narration as integrated
from game import quarantined_investigation_narration as q
from game import storage
from tests.test_pr_play_52_quarantined_integration import _seed

CAPTURE = json.loads((OUT / "experiment_results.json").read_text(encoding="utf-8"))
RAWS = [row["quarantine"]["raw_provider_text"] for row in CAPTURE["live"]["actions"]]
ACTIONS = [row["input"] for row in CAPTURE["live"]["actions"]]


class _Patch:
    def setattr(self, target, name, value):
        setattr(target, name, value)


def main() -> None:
    session_dir = OUT / "replay_session"
    _seed(session_dir, _Patch(), "frontier_gate")
    session_id = storage.load_session()["campaign_run_id"]
    os.environ[q.GATE_ENV] = "1"
    os.environ[q.MODE_ENV] = "integrated"
    os.environ[q.PUBLICATION_ENV] = "1"
    os.environ[q.PUBLICATION_SESSION_ENV] = session_id
    os.environ.pop(q.LIVE_ENV, None)
    os.environ.pop(q.FAULT_ENV, None)
    os.environ.pop(q.SAMPLE_ENV, None)
    q.clear_evidence()
    original = integrated.run_integrated_hook
    queue = list(RAWS)

    def generate(value):
        prose = queue.pop(0)
        return original(value, generator=q._Replay(prose, ""))

    integrated.run_integrated_hook = generate
    from artifacts.pr_play_61.run_experiment import authority, post_all
    try:
        rows = post_all(ACTIONS)
    finally:
        integrated.run_integrated_hook = original
    result = {
        "provider_requests": 0,
        "source": "saved raw provider text from experiment_results.json",
        "session_dir": str(session_dir / "data"),
        "actions": [
            {
                "input": row["input"],
                "facing": row["facing"],
                "marker": row["published_marker"],
                "decision": (row.get("quarantine") or {}).get("decision"),
                "used_fallback": (row.get("quarantine") or {}).get("used_fallback"),
                "rejected_text_published": (
                    (row.get("quarantine") or {}).get("raw_provider_text") == row["facing"]
                    and (row.get("quarantine") or {}).get("decision") != "PASS"
                ),
            }
            for row in rows
        ],
        "authority": authority(),
    }
    (OUT / "replay_results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["actions"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
