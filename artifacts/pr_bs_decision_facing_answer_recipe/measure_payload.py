"""Deterministic before/after char counts for the PR-BS authority slice.

Does not call a model or a tokenizer. Uses json.dumps(..., ensure_ascii=False).
The slice is the provider-facing authority projection this change touches:
system prompt, authority instructions, compact contract, decision projection,
answer recipe, and the nested mechanical-resolution authority metadata.
Response policy, turn packet, scene, and world bytes are unchanged and are
not rebuilt here.
"""
import json
from pathlib import Path

from game.gm import SYSTEM_PROMPT
from game.gm_resolution_decision import narration_authority_fields
from game.prompt_context import _provider_mechanical_resolution

ROOT = Path("artifacts/pr_bs_decision_facing_answer_recipe")
EVIDENCE = Path("artifacts/pr_br_closeout_live_revalidation")


def chars(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str))


def measure(label: str, filename: str) -> dict:
    saved = json.loads((EVIDENCE / filename).read_text(encoding="utf-8"))
    resolution = {
        "kind": saved["contract"].get("operation"),
        "metadata": {
            "resolution_contract": saved["contract"],
            "gm_resolution_decision": saved["decision"],
            "emission_debug": {"trace_only": True},
        },
    }
    fields = narration_authority_fields(resolution)
    mechanical = _provider_mechanical_resolution(resolution)
    instructions = [
        "ANSWER RECIPE: Follow decision_facing_answer_recipe for this turn. "
        "It projects gm_resolution_decision and does not add authority. "
        "The decision wins if they disagree."
    ]
    recipe = fields["decision_facing_answer_recipe"]
    user = {
        "instructions": instructions,
        "resolution_contract": fields["resolution_contract"],
        "gm_resolution_decision": fields["gm_resolution_decision"],
        "decision_facing_answer_recipe": recipe,
        "mechanical_resolution": {"metadata": mechanical.get("metadata")},
    }
    (ROOT / f"{label.lower()}_recipe.json").write_text(
        json.dumps(recipe, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {
        "label": label,
        "system_prompt_chars": len(SYSTEM_PROMPT),
        "instructions_chars": chars(instructions),
        "response_policy_chars": "unchanged_not_rebuilt",
        "turn_packet_chars": "unchanged_not_rebuilt",
        "decision_contract_claim_projection_chars": chars(
            {
                "resolution_contract": fields["resolution_contract"],
                "gm_resolution_decision": fields["gm_resolution_decision"],
            }
        ),
        "answer_recipe_chars": chars(recipe),
        "mechanical_resolution_chars": chars({"metadata": mechanical.get("metadata")}),
        "user_authority_slice_chars": chars(user),
        "total_provider_facing_chars": len(SYSTEM_PROMPT) + chars(user),
    }


before = json.loads((ROOT / "payload_before.json").read_text(encoding="utf-8"))
after_cases = [
    measure("A1", "A1_decision_1.json"),
    measure("B1", "B1_decision_4.json"),
]
comparison = []
before_by = {row["label"]: row for row in before["cases"]}
for row in after_cases:
    prior = before_by[row["label"]]
    comparison.append(
        {
            "label": row["label"],
            "before_total_provider_facing_chars": prior["total_provider_facing_chars"],
            "after_total_provider_facing_chars": row["total_provider_facing_chars"],
            "delta_total_provider_facing_chars": row["total_provider_facing_chars"] - prior["total_provider_facing_chars"],
            "before_user_authority_slice_chars": prior["user_authority_slice_chars"],
            "after_user_authority_slice_chars": row["user_authority_slice_chars"],
            "delta_user_authority_slice_chars": row["user_authority_slice_chars"] - prior["user_authority_slice_chars"],
            "before_system_prompt_chars": prior["system_prompt_chars"],
            "after_system_prompt_chars": row["system_prompt_chars"],
            "before_instructions_chars": prior["instructions_chars"],
            "after_instructions_chars": row["instructions_chars"],
            "before_decision_contract_claim_projection_chars": prior["decision_contract_claim_projection_chars"],
            "after_decision_contract_claim_projection_chars": row["decision_contract_claim_projection_chars"],
            "before_answer_recipe_chars": prior["answer_recipe_chars"],
            "after_answer_recipe_chars": row["answer_recipe_chars"],
            "before_mechanical_resolution_chars": prior["mechanical_resolution_chars"],
            "after_mechanical_resolution_chars": row["mechanical_resolution_chars"],
        }
    )
out = {
    "method": before["method"],
    "model_or_tokenizer_calls": 0,
    "cases": after_cases,
    "comparison": comparison,
}
(ROOT / "payload_after.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(json.dumps(comparison, indent=2))
