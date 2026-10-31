"""Generate review artifacts from the completed observation; no gameplay imports."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
HANDOFF = ROOT / "handoff"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


turns = read("turns.json")
calls = read("model_calls.json")
http = read("http_attempts.json")
assert len(turns) == 2 and [t["turn"] for t in turns] == ["A1", "A2"]
assert len(calls) == len(http) == 5
assert all(t["sealed"] == t["emitted"] for t in turns)
assert all(h["status"] == 200 for h in http)
summary = {
    "decision": "C", "stop_condition": 5,
    "stop_reason": "Recursive semantic authority-laundering chain begins: undeclared emitted A1 speculation, A2 player repetition, accepted A2 presupposition",
    "gameplay_turns": 2, "initial_generation_calls": 2, "retry_generation_calls": 2,
    "interpretation_calls": 0, "preflight_calls": 1, "other_model_api_calls": 0,
    "total_model_api_calls": 5, "http_attempts": 5, "sdk_transport_retries": 0,
    "planned_turns": 6, "unrun_turns": ["A3", "B1", "B2", "B3"],
    "first_attempt_structured_compliance": {"count": 2, "observed_denominator": 2, "planned_denominator": 6},
    "first_attempt_hard_valid": 0, "turns_with_retry": 2, "safe_fallback_turns": 0,
    "bounded_preservation_turns": ["A1"], "manual_undeclared_content_turns": ["A1", "A2"],
    "rejected_declarations": 2, "stored_world_truth_promotion_observed": False,
    "semantic_presupposition_strengthening_observed": True,
    "exact_sealed_emitted_matches": 2,
    "input_tokens": sum(c["response"]["usage"]["input_tokens"] for c in calls),
    "output_tokens": sum(c["response"]["usage"]["output_tokens"] for c in calls),
}
save(OUT / "summary.json", summary)
for turn in summary["unrun_turns"]:
    save(OUT / f"{turn}_full_trace.json", {"turn": turn, "status": "NOT_RUN", "reason": summary["stop_reason"],
                                           "calls": [], "payload": None, "emitted": None})

audits = []
transcript = ["# Complete attempted live transcript", "", "Stopped after A2; A3/B1/B2/B3 were not run.", ""]
for turn in turns:
    name = turn["turn"]
    gm = turn["payload"]["gm_output"]
    metadata = gm["metadata"]
    review = metadata.get("decision_review", {})
    accepted = metadata["accepted_response"]
    audit = {"turn": name, "attempt_1": review.get("attempt_1"), "attempt_2": review.get("attempt_2"),
             "accepted": accepted, "retry_context": review.get("retry_context"),
             "temporal_commit": metadata.get("emission_debug", {}).get("temporal_provenance_commit"),
             "before_temporal": turn["before"]["session"].get("narration_temporal_provenance"),
             "after_temporal": turn["after"]["session"].get("narration_temporal_provenance"),
             "before_active_claim": turn["before"]["session"].get("discourse_focus", {}).get("active_claim"),
             "after_active_claim": turn["after"]["session"].get("discourse_focus", {}).get("active_claim"),
             "exact_sealed": turn["sealed"], "exact_emitted": turn["emitted"]}
    audits.append(audit)
    transcript.extend([f"## {name}", "", "Player: " + turn["player"], ""])
    for n, call in enumerate([c for c in turn["calls"] if c["kind"] == "generation"], 1):
        raw = call["raw_output"]
        (OUT / f"{name}_raw_envelope_attempt_{n}.json").write_text(raw, encoding="utf-8")
        transcript.extend([f"### Raw attempt {n}", "", "```json", raw, "```", ""])
    transcript.extend(["### Exact sealed / emitted", "", turn["emitted"], "", "### Full validation and temporal evidence", "",
                       "```json", json.dumps(audit, indent=2, ensure_ascii=False), "```", ""])
save(OUT / "declaration_narration_temporal_audits.json", audits)
(OUT / "FULL_TRACE.md").write_text("\n".join(transcript), encoding="utf-8")

manual = {"A1": {"authority": "FAIL", "epistemic": "BORDERLINE", "responsive": "PASS", "useful": "PASS", "natural": "PASS", "state_consistent": "FAIL", "overall": "FAIL"},
          "A2": {"authority": "FAIL", "epistemic": "FAIL", "responsive": "BORDERLINE", "useful": "BORDERLINE", "natural": "PASS", "state_consistent": "BORDERLINE", "overall": "FAIL"}}
save(OUT / "manual_verdicts.json", manual)

history = HANDOFF / "history" / "pr-br-before-small-structured-live-validation"
history.mkdir(parents=True, exist_ok=True)
for name in ("CURRENT_REVIEW.zip", "CURRENT_REVIEW.md", "REVIEW_MANIFEST.json"):
    source = HANDOFF / name
    target = history / name
    if source.exists() and not target.exists():
        shutil.copy2(source, target)
shutil.copy2(OUT / "REPORT.md", HANDOFF / "CURRENT_REVIEW.md")
request = Path(r"C:\Users\Master Mandalcio\.codex\attachments\71d42b80-43c7-4180-b4a7-b7ca25588ee9\Pasted text.txt")
shutil.copy2(request, OUT / "USER_REQUEST.txt")

support = ["game/api.py", "game/api_turn_support.py", "game/gm.py", "game/gm_retry.py",
           "game/gm_resolution_decision.py", "game/immutable_valid_response.py", "game/resolution_contract.py",
           "game/semantic_interpreter.py", "game/structured_player_output.py", "game/interpretation_proposal.py",
           "game/storage.py", "game/defaults.py"]
files = {"CURRENT_REVIEW.md": HANDOFF / "CURRENT_REVIEW.md"}
for path in OUT.rglob("*"):
    if path.is_file() and "__pycache__" not in path.parts:
        files["evidence/" + path.relative_to(OUT).as_posix()] = path
for name in support:
    files["support/" + name] = ROOT / name
manifest = {"validation": "PR-BR Small Live Validation", "generated_utc": datetime.now(timezone.utc).isoformat(),
            **summary, "files": [{"path": name, "bytes": p.stat().st_size,
                                     "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for name, p in sorted(files.items())]}
save(HANDOFF / "REVIEW_MANIFEST.json", manifest)
files["REVIEW_MANIFEST.json"] = HANDOFF / "REVIEW_MANIFEST.json"
zip_path = HANDOFF / "CURRENT_REVIEW.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for name, path in sorted(files.items()):
        archive.write(path, name)
with zipfile.ZipFile(zip_path) as archive:
    assert archive.testzip() is None
    for row in manifest["files"]:
        assert hashlib.sha256(archive.read(row["path"])).hexdigest() == row["sha256"]
print(json.dumps({"zip": str(zip_path), "entries": len(files), "crc_and_sha256": "PASS", "summary": summary}, indent=2))
