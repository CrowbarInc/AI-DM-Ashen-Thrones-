"""Baseline provider-facing authority projection sizes before PR-BS recipe."""
import json
from pathlib import Path

from game.gm import SYSTEM_PROMPT
from game.gm_resolution_decision import compact_decision_for_prompt
from game.resolution_contract import generation_projection

ROOT = Path("artifacts/pr_bs_decision_facing_answer_recipe")


def chars(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str))


def measure(label, path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    contract = payload["contract"]
    decision = payload["decision"]
    compact_contract = generation_projection(contract)
    compact_decision = compact_decision_for_prompt(decision)
    instructions = [
        "RESOLUTION CONTRACT: Obey resolution_contract.constraint. It names the requested target and semantic point. "
        "Do not infer a different request from surrounding prose.",
        "GM RESOLUTION DECISION: Narrate only what gm_resolution_decision authorizes. "
        "Negation applies only to the predicate it negates. "
        "Unknown cause, actor, or time does not deny an established condition. "
        "Do not assert an asked predicate unless answer_relations permits that polarity.",
    ]
    mechanical = {
        "metadata": {
            "resolution_contract": contract,
            "gm_resolution_decision": decision,
        }
    }
    user = {
        "instructions": instructions,
        "resolution_contract": compact_contract,
        "gm_resolution_decision": compact_decision,
        "mechanical_resolution": mechanical,
    }
    return {
        "label": label,
        "system_prompt_chars": len(SYSTEM_PROMPT),
        "instructions_chars": chars(instructions),
        "response_policy_chars": 0,
        "turn_packet_chars": 0,
        "decision_contract_claim_projection_chars": chars(
            {
                "resolution_contract": compact_contract,
                "gm_resolution_decision": compact_decision,
            }
        ),
        "answer_recipe_chars": 0,
        "mechanical_resolution_chars": chars(mechanical),
        "user_authority_slice_chars": chars(user),
        "total_provider_facing_chars": len(SYSTEM_PROMPT) + chars(user),
    }


out = {
    "method": "deterministic json.dumps char counts of the authority slice the realization model receives from narration_authority_fields plus the nested mechanical_resolution contract/decision copies. Full scene/policy payload is unchanged by this slice and is not rebuilt.",
    "cases": [
        measure("A1", "artifacts/pr_br_closeout_live_revalidation/A1_decision_1.json"),
        measure("B1", "artifacts/pr_br_closeout_live_revalidation/B1_decision_4.json"),
    ],
}
(ROOT / "payload_before.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
