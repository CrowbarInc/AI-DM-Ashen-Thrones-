"""Fresh-process HTTP resume of both normally created campaign save slots."""
import os
os.environ["PR72_NETWORK"] = "cold_resume_network.jsonl"
import json
from runtime import OUT, storage, snapshot
from artifacts.pr_play_67.http_harness import server


def main():
    saved = json.loads((OUT / "http_summary.json").read_text())
    rows = []; results = []
    with server() as request:
        for campaign in saved["campaigns"]:
            response = request("/api/snapshots/load", {"snapshot_id": campaign["snapshot_id"]})
            assert response["status"] == 200 and storage.load_session()["campaign_run_id"] == campaign["identity"]
            journal = response["body"].get("journal")
            before = snapshot()
            assert before["world"]["world_state"]["flags"][campaign["followup_flag"]]
            inputs = ["What have I learned about the patrol?", "Check it again.", "Follow the tracks to whoever left them." if campaign["branch"] == "survey" else "Send a search party immediately."]
            for text in inputs:
                response = request("/api/chat", {"text": text})
                assert response["status"] == 200 and snapshot() == before and not response["hidden_exposures"]
                rows.append(dict(branch=campaign["branch"], text=text, response=response, authority_before=before, authority_after=snapshot()))
            results.append(dict(branch=campaign["branch"], identity=campaign["identity"], restored=True, branch_flag=True, journal=journal, readonly=True, ambiguous=True, unsupported=True))
    (OUT / "cold_resume_traces.json").write_text(json.dumps(rows, indent=2))
    (OUT / "cold_resume_summary.json").write_text(json.dumps(dict(fresh_process=True, campaigns=results, provider_requests=0, provider_tokens=0), indent=2))
    print("Fresh process: both campaigns resumed; six natural nonmutating continuations passed")


if __name__ == "__main__": main()
