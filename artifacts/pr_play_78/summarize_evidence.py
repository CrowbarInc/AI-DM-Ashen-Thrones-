"""Summarize PR-PLAY-78 evidence already on disk. Does not call the provider."""
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
before = json.loads((OUT / "protected_before.json").read_text(encoding="utf-8"))
paths = [row["path"] for row in before["files"]]
before_hashes = {row["path"]: row["sha256"] for row in before["files"]}
changed, missing, same = [], [], 0
for rel in paths:
    file = ROOT / rel
    if not file.exists():
        missing.append(rel)
        continue
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    old = before_hashes.get(rel) or before_hashes.get(str(rel))
    if old == digest:
        same += 1
    else:
        changed.append({"path": rel, "before": old, "after": digest})

turns = json.loads((OUT / "extended_play.json").read_text(encoding="utf-8"))["turns"]
lat = [t["elapsed_ms"] for t in turns]
unsupported_marks = ("not supported", "not established", "not resolved", "cannot be taken", "not an established")
clarify_marks = ("which available", "which person")
rows = []
for t in turns:
    text = t["player_facing_text"]
    kind = "resolved"
    if any(m in text.lower() for m in unsupported_marks):
        kind = "unsupported"
    elif any(m in text.lower() for m in clarify_marks):
        kind = "clarification"
    rows.append({**{k: t[k] for k in ("turn", "input", "provenance", "elapsed_ms", "live_requested", "adopted")}, "class": kind})

live = json.loads((OUT / "live_gate.json").read_text(encoding="utf-8"))
# Sticky session flags are not independent accepts. Count a turn only when latency shows a provider call.
published_dialogue = []
published_narration = []
rejected_narration = []
for turn in live["turns"]:
    if turn["elapsed_ms"] < 200:
        continue
    spoken = turn["player_facing_text"].lower()
    if turn.get("speech_adopted") and turn.get("speech_reasons") == [] and ("says" in spoken or "saying" in spoken):
        published_dialogue.append(turn["input"])
    if turn.get("narration_reasons") == [] and turn["elapsed_ms"] >= 200:
        published_narration.append(turn["input"])
    elif turn.get("narration_reasons"):
        rejected_narration.append({"input": turn["input"], "reasons": turn["narration_reasons"]})

summary = {
    "protected_same": same,
    "protected_changed": changed,
    "protected_missing": missing,
    "protected_total": len(paths),
    "extended_turns": len(turns),
    "extended_classes": {k: sum(r["class"] == k for r in rows) for k in ("resolved", "unsupported", "clarification")},
    "extended_live_requested": sum(bool(t["live_requested"]) for t in turns),
    "extended_adopted_flag": sum(bool(t["adopted"]) for t in turns),
    "extended_latency_ms": {
        "mean": round(statistics.mean(lat), 1),
        "median": round(statistics.median(lat), 1),
        "p95": round(sorted(lat)[max(0, int(len(lat) * 0.95) - 1)], 1),
        "max": round(max(lat), 1),
    },
    "live_gate_published_dialogue_inputs": published_dialogue,
    "live_gate_published_narration_inputs": published_narration,
    "live_gate_rejected_narration": rejected_narration,
    "note": "Who-are-you at 35.6 ms is a clarification. narration_adopted is sticky and is not used as the accept count.",
}
(OUT / "evidence_summary.json").write_text(json.dumps({"turns": rows, "summary": summary}, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
