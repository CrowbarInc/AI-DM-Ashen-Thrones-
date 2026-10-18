#!/usr/bin/env python3
"""PR-BT selective epistemic restoration provider measurement.

Reconstructs P1/P2/P3 with the same build_messages path as the PR-BT
deduplication measurement. No model or API calls.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.measure_pr_bt_policy_instruction_payloads import BEFORE, PROBES, reconstruct_probe

OUT = ROOT / "artifacts" / "pr_bt_selective_epistemic_guidance"
OPTIMIZED = {"P1": 97260, "P2": 109853, "P3": 99200}
OPTIMIZED_SYSTEM_PROMPT_CHARS = 9012


def _provider(probe_id: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    path = OUT / "evidence" / probe_id / "provider_request_generation_1.json"
    request = json.loads(path.read_text(encoding="utf-8"))
    messages = request["provider_input"]
    system = ""
    payload: dict[str, Any] = {}
    for msg in messages:
        if msg.get("role") == "system":
            system = str(msg.get("content") or "")
        elif msg.get("role") == "user":
            parsed = json.loads(str(msg.get("content") or "{}"))
            if isinstance(parsed, dict):
                payload = parsed
    return system, payload, request["measurements"]


def main() -> int:
    from game.gm import EPISTEMIC_REALIZATION_PROTOCOL

    OUT.mkdir(parents=True, exist_ok=True)
    rows = [reconstruct_probe(probe_id, player, out_dir=OUT) for probe_id, _scene, player in PROBES]
    probes: dict[str, Any] = {}
    restored_costs: list[int] = []
    for row in rows:
        probe = row["probe"]
        system, payload, counts = _provider(probe)
        recipe = payload.get("decision_facing_answer_recipe")
        recipe_text = json.dumps(recipe, ensure_ascii=False, default=str) if isinstance(recipe, dict) else ""
        instructions = payload.get("instructions") if isinstance(payload.get("instructions"), list) else []
        instruction_text = "\n".join(str(item) for item in instructions)
        protocol_in_system = system.count(EPISTEMIC_REALIZATION_PROTOCOL)
        original = BEFORE[probe]["total"]
        optimized = OPTIMIZED[probe]
        restored = counts["total_provider_chars"]
        chars_restored_vs_optimized = restored - optimized
        chars_still_removed = original - restored
        previous_reduction = original - optimized
        restored_costs.append(chars_restored_vs_optimized)
        guidance_presence = {
            "P1": {
                "visible_evidence_grounds_the_answer": "state the authorized observations first" in system,
                "permitted_inference_is_useful": "add one possibility tied to those observations" in system,
                "inference_stays_explicitly_qualified": "say explicitly that cause, actor, time, and history stay unresolved" in system,
                "cause_and_history_stay_unresolved": "cause, actor, time, and history stay unresolved" in system,
                "unsupported_history_is_not_encouraged": "Do not add a mechanism, setting, maintenance history, or causal chain" in system,
                "uncertainty_is_not_a_refusal": "Prefer partial truth over refusal" in system,
            },
            "P3": {
                "player_hypotheses_may_be_discussed": "when the player offers a hypothesis" in system,
                "hypotheses_remain_conditional": "A player hypothesis stays hypothetical" in system,
                "fit_is_evaluated_against_evidence": "the visible facts may be compatible with it" in system,
                "proposal_does_not_become_truth": "observation alone does not settle it" in system,
                "certainty_language_stays_inside_epistemic_status": "Do not use certainty wording for inferred or hypothetical material" in system,
                "useful_discussion_is_permitted": "the visible facts may be compatible with it" in system,
            },
            "P2": {
                "protocol_scoped_to_interpretation_or_hypothesis": "On an interpretation, or when the player offers a hypothesis" in system,
                "mundane_npc_dialogue_remains_incidental": "Mundane NPC dialogue and low-stakes texture may be bounded incidental realization" in system,
                "refusal_hesitation_mannerism_remain_plain_narration": "ordinary NPC dialogue, refusal, hesitation, and mannerism" in system,
                "recipe_allows_ordinary_dialogue": "ordinary dialogue" in recipe_text,
                "recipe_names_refusal_hesitation_mannerism_phrasing": all(
                    token in recipe_text for token in ("refusal", "hesitation", "mannerism", "phrasing")
                ),
            },
        }[probe]
        probes[probe] = {
            "total_provider_chars": counts["total_provider_chars"],
            "system_prompt_chars": counts["system_prompt_chars"],
            "instructions_chars": counts["instructions_chars"],
            "instructions_count": counts["instructions_count"],
            "response_policy_chars": counts["response_policy_chars"],
            "turn_packet_chars": counts["turn_packet_chars"],
            "answer_recipe_chars": counts["decision_facing_answer_recipe_chars"],
            "restored_protocol_chars": len(EPISTEMIC_REALIZATION_PROTOCOL) if protocol_in_system else 0,
            "protocol_occurrences_in_system": protocol_in_system,
            "protocol_occurrences_in_instructions": instruction_text.count(EPISTEMIC_REALIZATION_PROTOCOL),
            "protocol_occurrences_in_answer_recipe": recipe_text.count("EPISTEMIC REALIZATION"),
            "abstract_sentence_present": "strongest grounded partial answer" in system,
            "original_total_chars": original,
            "optimized_total_chars": optimized,
            "chars_restored_vs_optimized": chars_restored_vs_optimized,
            "chars_still_removed_vs_original": chars_still_removed,
            "previous_reduction_chars": previous_reduction,
            "percentage_of_previous_reduction_retained": round(
                chars_still_removed / previous_reduction * 100, 2
            ),
            "percentage_reduction_vs_original": round(chars_still_removed / original * 100, 2),
            "rule_presence": row["rule_presence"],
            "guidance_presence": guidance_presence,
        }
    summary = {
        "method": "game.gm.build_messages on saved PR-BS isolated probe state. Zero model/API calls.",
        "protocol_chars": len(EPISTEMIC_REALIZATION_PROTOCOL),
        "optimized_system_prompt_chars": OPTIMIZED_SYSTEM_PROMPT_CHARS,
        "system_prompt_chars": probes["P1"]["system_prompt_chars"],
        "system_prompt_chars_restored": probes["P1"]["system_prompt_chars"] - OPTIMIZED_SYSTEM_PROMPT_CHARS,
        "fixed_restored_cost_chars": min(restored_costs),
        "probe_specific_restored_cost_chars": {probe: probes[probe]["chars_restored_vs_optimized"] for probe in probes},
        "original": {probe: BEFORE[probe]["total"] for probe in ("P1", "P2", "P3")},
        "optimized": OPTIMIZED,
        "probes": probes,
    }
    (OUT / "p1_p2_p3_measurements.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
