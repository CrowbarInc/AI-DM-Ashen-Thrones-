"""Same saved survey state and same investigation through text and structured action."""
import os
os.environ["PR72_NETWORK"] = "latency_network.jsonl"
from runtime import OUT, storage, snapshot
import json
import statistics
from artifacts.pr_play_67.http_harness import server


def main():
    summary = json.loads((OUT / "http_summary.json").read_text())
    saved = next(c["snapshot_id"] for c in summary["campaigns"] if c["branch"] == "survey")
    rows = []
    with server() as request:
        for method in ("natural", "structured"):
            for repetition in range(2):
                assert request("/api/snapshots/load", {"snapshot_id": saved})["status"] == 200
                before = snapshot()
                if method == "natural":
                    response = request("/api/chat", {"text": "I examine the mud prints again."})
                else:
                    response = request("/api/action", {"action_type": "exploration", "intent": "Examine the mud prints again", "exploration_action": {"id": "prints", "type": "investigate", "label": "Mud prints", "prompt": "Examine the mud prints again"}})
                row = json.loads((OUT / "latency_network.jsonl").read_text().splitlines()[-1])
                resolution = storage.load_log()[-1]["resolution"]
                assert response["status"] == 200 and not response["hidden_exposures"]
                rows.append(dict(method=method, repetition=repetition+1, http_ms=response["http_ms"], stages=row["stages"], resolution={k:resolution.get(k) for k in ("kind", "action_id", "success")}, world_unchanged=before["world"]==snapshot()["world"], response=response["body"]))
    result = dict(rows=rows, provider_requests=0, provider_tokens=0, browser_visible_ms=None,
                  notes="Two samples per entry path, same saved scene and target; instrumentation and concurrent verification add overhead.")
    for method in ("natural", "structured"):
        values = [r["http_ms"] for r in rows if r["method"] == method]
        result[method + "_ms"] = dict(mean=statistics.mean(values), median=statistics.median(values), maximum=max(values))
    (OUT / "latency_comparison.json").write_text(json.dumps(result, indent=2));print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
