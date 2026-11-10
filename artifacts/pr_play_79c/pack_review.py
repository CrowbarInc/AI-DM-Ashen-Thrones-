import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REVIEW = OUT / "review"
MACHINE = REVIEW / "machine"
MACHINE.mkdir(exist_ok=True)
shots = REVIEW / "screenshots"
shots.mkdir(exist_ok=True)

http = json.loads((OUT / "live_http.json").read_text(encoding="utf-8"))
slim = []
for turn in http["integrated"]["transcript"]:
    slim.append({
        "input": turn.get("input"),
        "provenance": turn.get("provenance"),
        "elapsed_ms": turn.get("elapsed_ms"),
        "player_facing_text": turn.get("player_facing_text"),
        "dialogue_adopted": turn.get("dialogue_adopted"),
        "dialogue_published": turn.get("dialogue_published"),
        "dialogue_replaced": turn.get("dialogue_replaced"),
        "dialogue_text": turn.get("dialogue_text"),
        "dialogue_reasons": turn.get("dialogue_reasons"),
        "narration_adopted": turn.get("narration_adopted"),
        "narration_published": turn.get("narration_published"),
        "narration_reasons": turn.get("narration_reasons"),
        "primary_narration": turn.get("primary_narration"),
    })
(MACHINE / "http_transcript.json").write_text(json.dumps(slim, indent=2), encoding="utf-8")
for src, dest in (
    (OUT / "live_http.json", MACHINE / "live_http.json"),
    (OUT / "holdout_results.json", MACHINE / "holdout_results.json"),
    (OUT / "protected_after.json", MACHINE / "protected_after.json"),
    (OUT / "regression_results.json", MACHINE / "regression_results.json"),
    (OUT / "browser_data" / "provider_usage.jsonl", MACHINE / "browser_provider_usage.jsonl"),
    (ROOT / "tests" / "fixtures" / "pr_play_79c_holdout.json", MACHINE / "pr_play_79c_holdout.json"),
    (OUT / "browser_screenshots" / "browser_open.png", shots / "browser_open.png"),
    (OUT / "browser_screenshots" / "browser_dialogue.png", shots / "browser_dialogue.png"),
):
    if src.exists():
        shutil.copy2(src, dest)

browser = {
    "provenance": "restored initialized campaign; opening was not regenerated",
    "url": "http://127.0.0.1:8097/",
    "authored_buttons_clicked": False,
    "reload_preserved_speech": True,
    "provider_requests": 5,
    "provider_input_tokens": 1522,
    "provider_output_tokens": 129,
    "provider_total_tokens": 1651,
    "first_attempt": "Copied ledger blocked admission. Not counted.",
}
(MACHINE / "browser_transcript.json").write_text(json.dumps(browser, indent=2), encoding="utf-8")

stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
archive = ROOT / "handoff" / f"CURRENT_REVIEW({stamp}).zip"
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in REVIEW.rglob("*"):
        if path.is_file():
            zf.write(path, path.relative_to(REVIEW).as_posix())
(OUT / "archive_path.txt").write_text(str(archive), encoding="utf-8")
print(archive)
