"""Replay saved narration against current validators. No model calls."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from game.gm_resolution_decision import (
    _CAUSAL_RELATION_RE,
    _CERTAINTY_UPGRADE_RE,
    _DEFINITE_PHRASE_RE,
    _EPISTEMIC_LIMIT_RE,
    _EPISTEMIC_PARENT_REALIZATION_RE,
    _EVIDENTIAL_RELATION_RE,
    _GENERATED_LEAD_RE,
    _NARRATOR_MODAL_RE,
    _QUALIFIED_INFERENCE_RE,
    _SPECIFIC_LEAD_RE,
    _UNCERTAIN_FRAME_RE,
    _UNKNOWN_SLOT_RE,
    _authorized_epistemic_limit,
    _decision_allows_epistemic_limit,
    _decision_allows_inference,
    _decision_ground,
    _has_ungrounded_definite,
    _unsupported_narrator_lead,
    audit_narration_against_decision,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

CASES = [
    ("BS_P1", ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1", "initial"),
    ("BT_P1_initial", ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P1", "initial"),
    ("BT_P1_retry", ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P1", "retry"),
    ("BS_P3", ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3", "initial"),
    ("BT_P3_initial", ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P3", "initial"),
    ("BT_P3_retry", ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P3", "retry"),
    ("BS_P2", ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P2", "initial"),
    ("BT_P2", ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P2", "initial"),
]

LEXICAL = [
    "This damage could suggest gradual wear from frequent use or recent stress that strained these components, though exactly when or how this happened remains unclear.",
    "This damage could suggest that the bell has endured significant stress, possibly from frequent ringing or exposure to the elements, leading to wear and weakening of its support structure.",
    "Given these visible signs, it might be possible that the bell has been under considerable strain, but the exact cause or history of this damage is not clear from observation alone.",
    "Given these visible signs, it might be possible that the bell has been under considerable strain, but the exact cause or history of this damage remains unclear from observation alone.",
    "The exact cause or history of this damage is not clear from observation alone.",
    "The exact cause or history of this damage remains unclear from observation alone.",
    "The exact cause remains unclear.",
    "The exact cause is not clear.",
    "Whether these damages were caused deliberately is uncertain from the visible evidence alone.",
    "These damages are clearly visible, though whether they were caused deliberately remains uncertain from appearance alone.",
    "These damages are visible, though whether they were caused deliberately remains uncertain from appearance alone.",
    "While these damages are clearly visible, whether they were caused deliberately is not something that can be determined from the appearance alone.",
    "While these damages are visible, whether they were caused deliberately cannot be determined from the appearance alone.",
    "Whether they were caused deliberately cannot be determined from the appearance alone.",
    "Whether they were caused deliberately is not something that can be determined from the appearance alone.",
]


def load_decision(folder: Path):
    return json.loads((folder / "gm_resolution_decision.json").read_text(encoding="utf-8"))


def load_text(folder: Path, which: str) -> str:
    digest = json.loads((folder / "digest.json").read_text(encoding="utf-8"))
    if which == "retry":
        return digest.get("retry_player_facing_text") or ""
    return digest.get("initial_player_facing_text") or digest.get("emitted") or ""


def flags(sentence: str, decision, corpus: str) -> dict:
    return {
        "unknown_slot": bool(_UNKNOWN_SLOT_RE.search(sentence)),
        "epistemic_limit": bool(_EPISTEMIC_LIMIT_RE.search(sentence)),
        "epistemic_parent": bool(_EPISTEMIC_PARENT_REALIZATION_RE.search(sentence)),
        "authorized_epistemic_limit": _authorized_epistemic_limit(sentence, decision),
        "decision_allows_epistemic_limit": _decision_allows_epistemic_limit(decision),
        "decision_allows_inference": _decision_allows_inference(decision),
        "qualified_inference": bool(_QUALIFIED_INFERENCE_RE.search(sentence)),
        "uncertain_frame": bool(_UNCERTAIN_FRAME_RE.search(sentence)),
        "narrator_modal": bool(_NARRATOR_MODAL_RE.search(sentence)),
        "generated_lead": bool(_GENERATED_LEAD_RE.search(sentence)),
        "specific_lead": bool(_SPECIFIC_LEAD_RE.search(sentence)),
        "causal": bool(_CAUSAL_RELATION_RE.search(sentence)),
        "evidential": bool(_EVIDENTIAL_RELATION_RE.search(sentence)),
        "certainty_upgrade": bool(_CERTAINTY_UPGRADE_RE.search(sentence)),
        "unsupported_lead": _unsupported_narrator_lead(sentence, corpus, decision, sentence),
        "ungrounded_definite": _has_ungrounded_definite(sentence, _decision_ground(corpus, decision)),
        "definite_phrases": [m.group(0) for m in _DEFINITE_PHRASE_RE.finditer(sentence)],
    }


def main():
    report = {"cases": [], "lexical_on_p1_decision": [], "lexical_on_p3_decision": []}
    p1_decision = load_decision(ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1")
    p3_decision = load_decision(ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3")
    # decisions should match BT; record a hash-like equality later
    for label, folder, which in CASES:
        decision = load_decision(folder)
        text = load_text(folder, which)
        audit = audit_narration_against_decision(text, decision=decision, authored_corpus="")
        sentences = []
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip()
            if not sentence:
                continue
            sentences.append({"text": sentence, "flags": flags(sentence, decision, "")})
        report["cases"].append(
            {
                "label": label,
                "text": text,
                "hard_valid": audit["hard_valid"],
                "violations": [
                    {"text": row.get("text"), "reasons": row.get("reason_codes")}
                    for row in audit.get("violations") or []
                ],
                "claim_results": [
                    {
                        "text": row.get("text"),
                        "authorized": row.get("authorized"),
                        "reasons": row.get("reason_codes"),
                        "relation": row.get("relation_kind"),
                        "status": row.get("epistemic_status"),
                    }
                    for row in audit.get("claim_results") or []
                ],
                "sentences": sentences,
                "epistemic_acts": decision.get("epistemic_acts"),
                "unresolved_qualifiers": decision.get("unresolved_qualifiers"),
                "narration_constraints": decision.get("narration_constraints"),
                "answer_relations": decision.get("answer_relations"),
            }
        )
        print("\n==", label, "hard_valid", audit["hard_valid"])
        for row in audit.get("violations") or []:
            print("  VIOL", row.get("reason_codes"), "|", (row.get("text") or "")[:160])
        for sent in sentences:
            interesting = {k: v for k, v in sent["flags"].items() if v not in (False, [], None)}
            print("  SENT", sent["text"][:110])
            print("   ", interesting)

    for sentence in LEXICAL:
        for name, decision in (("P1", p1_decision), ("P3", p3_decision)):
            audit = audit_narration_against_decision(sentence, decision=decision, authored_corpus="")
            reasons = [row.get("reason_codes") for row in audit.get("violations") or []]
            bucket = report["lexical_on_p1_decision"] if name == "P1" else report["lexical_on_p3_decision"]
            bucket.append({"text": sentence, "hard_valid": audit["hard_valid"], "reasons": reasons, "flags": flags(sentence, decision, "")})
            print(f"LEX {name} valid={audit['hard_valid']} reasons={reasons} :: {sentence[:90]}")

    # decision equality BS vs BT
    for probe in ("P1", "P2", "P3"):
        a = json.loads((ROOT / f"artifacts/pr_bs_cooperative_gm_micro_live/evidence/{probe}/gm_resolution_decision.json").read_text(encoding="utf-8"))
        b = json.loads((ROOT / f"artifacts/pr_bt_provider_deduplication_micro_live/evidence/{probe}/gm_resolution_decision.json").read_text(encoding="utf-8"))
        print(probe, "decision equal", a == b)
        ra = json.loads((ROOT / f"artifacts/pr_bs_cooperative_gm_micro_live/evidence/{probe}/resolution_contract.json").read_text(encoding="utf-8"))
        rb = json.loads((ROOT / f"artifacts/pr_bt_provider_deduplication_micro_live/evidence/{probe}/resolution_contract.json").read_text(encoding="utf-8"))
        print(probe, "contract equal", ra == rb)
        qa = json.loads((ROOT / f"artifacts/pr_bs_cooperative_gm_micro_live/evidence/{probe}/decision_facing_answer_recipe.json").read_text(encoding="utf-8"))
        qb = json.loads((ROOT / f"artifacts/pr_bt_provider_deduplication_micro_live/evidence/{probe}/decision_facing_answer_recipe.json").read_text(encoding="utf-8"))
        print(probe, "recipe equal", qa == qb)

    (OUT / "forensic_validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
