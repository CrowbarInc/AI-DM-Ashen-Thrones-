"""Extra lexical probes. No model calls."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from game.gm_resolution_decision import audit_narration_against_decision

ROOT = Path(__file__).resolve().parents[2]
p1 = json.loads((ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/gm_resolution_decision.json").read_text(encoding="utf-8"))
p3 = json.loads((ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/gm_resolution_decision.json").read_text(encoding="utf-8"))

obs = "The bell's wooden yoke is split, and its leather hanger is torn. "
probes = [
    obs + "This damage could suggest that the bell has endured significant stress, possibly from frequent ringing or exposure to the elements, leading to wear and weakening of its support structure, though exactly when or how this happened remains unclear.",
    obs + "This damage could suggest significant stress from frequent ringing or exposure to the elements, though exactly when or how this happened remains unclear.",
    obs + "This damage could suggest strain, though the cause remains unclear.",
    obs + "This damage could suggest gradual wear, though the cause is not clear.",
    obs + "This damage might indicate wear or strain. The cause remains unclear.",
    obs + "The split is clearly visible.",
    obs + "These damages are clearly visible.",
    "The bell's wooden yoke is indeed split, and its leather hanger is torn. Whether someone cut it deliberately remains uncertain from the visible evidence alone.",
    "The bell's wooden yoke is indeed split, and its leather hanger is torn. Whether someone cut it deliberately is not clear from the visible evidence alone.",
    "The bell's wooden yoke is indeed split, and its leather hanger is torn. Whether someone cut it deliberately is unclear from the visible evidence alone.",
]

for decision, name in ((p1, "P1"), (p3, "P3")):
    print("\n##", name)
    for text in probes:
        audit = audit_narration_against_decision(text, decision=decision, authored_corpus="")
        reasons = [row.get("reason_codes") for row in audit.get("violations") or []]
        print(audit["hard_valid"], reasons, "::", text[len(obs):][:140] if text.startswith(obs.strip()[:20]) or text.startswith("The bell") else text[:140])

# contract epistemic modes
for probe in ("P1", "P2", "P3"):
    contract = json.loads((ROOT / f"artifacts/pr_bs_cooperative_gm_micro_live/evidence/{probe}/resolution_contract.json").read_text(encoding="utf-8"))
    print(probe, "epistemic_mode", contract.get("epistemic_mode"), "operation", contract.get("operation"), "dimension", contract.get("dimension"), "request", contract.get("request_kind"))
    construction = contract.get("construction") or {}
    print("  construction keys", list(construction)[:30])
