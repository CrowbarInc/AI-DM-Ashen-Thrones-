"""Extract identical-vs-changed policy objects and ungrounded tokens. No model calls."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from game.gm_resolution_decision import _DEFINITE_PHRASE_RE, _DEFINITE_STOP, _decision_ground

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def load_user(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.loads(data["provider_input"][1]["content"])


def ungrounded(sentence, ground):
    hits = []
    for match in _DEFINITE_PHRASE_RE.finditer(sentence):
        tokens = []
        for raw in __import__("re").findall(r"[a-z']+", match.group(1).lower()):
            token = raw.replace("'s", "").replace("'", "")
            if len(token) < 5 or token in _DEFINITE_STOP:
                continue
            tokens.append({"token": token, "in_ground": token in ground})
        hits.append({"phrase": match.group(0), "tokens": tokens})
    return hits


def main():
    bs = load_user(ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/provider_request_attempt_generation_1.json")
    bt = load_user(ROOT / "artifacts/pr_bt_provider_deduplication_micro_live/evidence/P1/provider_request_attempt_generation_1.json")
    policy_keys = [
        "response_policy",
        "fallback_behavior",
        "decision_facing_answer_recipe",
        "gm_resolution_decision",
        "resolution_contract",
    ]
    # response policy may be nested
    rp_bs = bs.get("response_policy")
    rp_bt = bt.get("response_policy")
    print("response_policy equal", rp_bs == rp_bt)
    if isinstance(rp_bs, dict):
        print("response_policy keys", sorted(rp_bs))
        for key in ("narrative_authority", "uncertainty", "fallback_behavior", "answer_completeness", "response_delta"):
            left = rp_bs.get(key)
            right = rp_bt.get(key)
            print(key, "equal", left == right, "chars", len(json.dumps(left, ensure_ascii=False)) if left is not None else 0)
            (OUT / f"policy_{key}.json").write_text(json.dumps(left, indent=2, ensure_ascii=False), encoding="utf-8")

    decision = json.loads((ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/gm_resolution_decision.json").read_text(encoding="utf-8"))
    keep = {
        "epistemic_acts": decision.get("epistemic_acts"),
        "unresolved_qualifiers": decision.get("unresolved_qualifiers"),
        "narration_constraints": decision.get("narration_constraints"),
        "answer_relations": decision.get("answer_relations"),
        "realization_claims_texts": [
            {
                "text": row.get("text"),
                "epistemic_status": row.get("epistemic_status"),
                "provenance": row.get("provenance"),
                "relation_kind": row.get("relation_kind"),
                "realization_role": row.get("realization_role"),
            }
            for row in (decision.get("realization_claims") or [])
            if isinstance(row, dict)
        ],
    }
    (OUT / "P1_decision_epistemic_slice.json").write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("P1 epistemic acts", json.dumps(keep["epistemic_acts"], ensure_ascii=False)[:800])
    print("P1 unresolved", keep["unresolved_qualifiers"])
    print("P1 constraints", keep["narration_constraints"])

    decision3 = json.loads((ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/gm_resolution_decision.json").read_text(encoding="utf-8"))
    keep3 = {
        "epistemic_acts": decision3.get("epistemic_acts"),
        "unresolved_qualifiers": decision3.get("unresolved_qualifiers"),
        "narration_constraints": decision3.get("narration_constraints"),
        "player_hypothesis": decision3.get("player_hypotheses") or decision3.get("hypotheses"),
        "realization_claims_texts": [
            {
                "text": row.get("text"),
                "epistemic_status": row.get("epistemic_status"),
                "provenance": row.get("provenance"),
                "relation_kind": row.get("relation_kind"),
                "realization_role": row.get("realization_role"),
            }
            for row in (decision3.get("realization_claims") or [])
            if isinstance(row, dict)
        ],
    }
    # search hypothesis-like keys
    hypo_keys = [k for k in decision3.keys() if "hypo" in k.lower() or "epistem" in k.lower() or "discourse" in k.lower()]
    print("P3 decision interesting keys", hypo_keys)
    print("P3 epistemic", json.dumps(keep3["epistemic_acts"], ensure_ascii=False)[:800])
    print("P3 unresolved", keep3["unresolved_qualifiers"])
    print("P3 constraints", keep3["narration_constraints"])
    (OUT / "P3_decision_epistemic_slice.json").write_text(json.dumps({"keys": list(decision3.keys()), **keep3}, indent=2, ensure_ascii=False), encoding="utf-8")

    contract1 = json.loads((ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P1/resolution_contract.json").read_text(encoding="utf-8"))
    contract3 = json.loads((ROOT / "artifacts/pr_bs_cooperative_gm_micro_live/evidence/P3/resolution_contract.json").read_text(encoding="utf-8"))
    for label, contract in (("P1", contract1), ("P3", contract3)):
        slim = {k: contract.get(k) for k in ("request_kind", "operation", "target", "expected_resolution", "authority", "subject", "dimension") if k in contract}
        print(label, "contract top", list(contract.keys())[:40])
        print(label, slim)

    sentences = [
        "This damage could suggest gradual wear from frequent use or recent stress that strained these components, though exactly when or how this happened remains unclear.",
        "This damage could suggest that the bell has endured significant stress, possibly from frequent ringing or exposure to the elements, leading to wear and weakening of its support structure.",
        "Given these visible signs, it might be possible that the bell has been under considerable strain, but the exact cause or history of this damage is not clear from observation alone.",
        "Given these visible signs, it might be possible that the bell has been under considerable strain, but the exact cause or history of this damage remains unclear from observation alone.",
    ]
    ground = _decision_ground("", decision)
    print("GROUND LEN", len(ground))
    print(ground[:500])
    for sentence in sentences:
        print("---")
        print(sentence[:100])
        print(json.dumps(ungrounded(sentence, ground), ensure_ascii=False))


if __name__ == "__main__":
    main()
