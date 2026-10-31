"""Deterministic extraction for PR-BV. Reads preserved payloads only. No model calls."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CURRENT = ROOT / "artifacts" / "pr_bu_pr_bt_final_repaired_chain_micro_live" / "evidence"
SELECTIVE = ROOT / "artifacts" / "pr_bt_selective_epistemic_restoration_final_micro_live" / "evidence"
RAW_BT = ROOT / "artifacts" / "pr_bt_provider_deduplication_micro_live" / "evidence"
PR_BS = ROOT / "artifacts" / "pr_bs_cooperative_gm_micro_live" / "evidence"

FAMILIES = {
    "authority_constraints": [
        "authoritative",
        "authority",
        "forbidden",
        "must not",
        "do not invent",
        "hidden fact",
        "world truth",
        "unauthorized",
        "visibility",
        "narration_visibility",
    ],
    "declaration_machinery": [
        "declared_claims",
        "declaration_mode",
        "declaration",
        "realize",
        "propose",
        "source_claim_id",
        "provenance_requested",
        "realization_claims",
        "MUST_STATE",
    ],
    "state_authorship": [
        "authored_world_fact",
        "world_truth",
        "established",
        "consequential",
        "persist",
        "world_updates",
        "scene_update",
    ],
    "incidental_narration": [
        "incidental",
        "mannerism",
        "ordinary npc",
        "ordinary dialogue",
        "plain narration",
        "refusal",
        "hesitation",
        "improvisation",
    ],
    "bounded_inference": [
        "qualified possibil",
        "could, may, or might",
        "gm_inference",
        "inferred",
        "inference",
        "interpretation",
        "qualified",
    ],
    "player_hypotheses": [
        "hypothesis",
        "hypothetical",
        "player hypothesis",
        "compatible",
    ],
    "response_quality": [
        "specificity",
        "scene momentum",
        "consequence_or_opportunity",
        "answer the player",
        "direct answer",
        "flavor",
        "polish",
        "new information",
    ],
    "natural_dialogue": [
        "dialogue",
        "spoken",
        "in-character",
        "cadence",
        "voice",
        "reply",
    ],
    "structured_output": [
        "json",
        "envelope",
        "narration",
        "player_facing_text",
        "improvisation_proposals",
        "debug_notes",
    ],
    "epistemic_expression": [
        "uncertain",
        "unresolved",
        "remains unclear",
        "could",
        "might",
        "may",
        "hedge",
        "known_edge",
        "unknown_edge",
    ],
    "operation_selection": [
        "answer_strategy",
        "ordinary dialogue",
        "qualified possibility",
        "realizing the required",
        "epistemic realization",
        "what kind",
    ],
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def provider_messages(doc: dict) -> list[dict]:
    return doc["provider_input"]


def system_text(doc: dict) -> str:
    return provider_messages(doc)[0]["content"]


def user_obj(doc: dict) -> dict:
    return json.loads(provider_messages(doc)[1]["content"])


def rough_tokens(chars: int) -> int:
    return max(1, round(chars / 4)) if chars else 0


def count_hits(text: str, needles: list[str]) -> dict:
    lowered = text.lower()
    hits = {}
    for needle in needles:
        hits[needle] = lowered.count(needle.lower())
    return hits


def family_chars(text: str) -> dict:
    """Approximate prominence: characters inside sentences that mention a family needle.

    A sentence can count toward more than one family. This is a salience proxy, not attention.
    """
    sentences = re.split(r"(?<=[.!?;])\s+|\n+", text)
    out = {}
    for family, needles in FAMILIES.items():
        total = 0
        for sentence in sentences:
            lowered = sentence.lower()
            if any(needle.lower() in lowered for needle in needles):
                total += len(sentence)
        out[family] = total
    return out


def instruction_delta(left: list[str], right: list[str]) -> dict:
    right_set = set(right)
    left_set = set(left)
    removed = [text for text in left if text not in right_set]
    added = [text for text in right if text not in left_set]
    return {
        "left_count": len(left),
        "right_count": len(right),
        "left_chars": sum(len(item) for item in left),
        "right_chars": sum(len(item) for item in right),
        "removed_count": len(removed),
        "added_count": len(added),
        "removed_chars": sum(len(item) for item in removed),
        "added_chars": sum(len(item) for item in added),
        "removed": [{"chars": len(text), "text": text} for text in removed],
        "added": [{"chars": len(text), "text": text} for text in added],
    }


def schema_slice(system: str) -> str:
    start = system.find("Return valid JSON")
    end = system.find("STRUCTURED CLAIM DECLARATION RULE")
    if start < 0 or end < 0:
        return ""
    return system[start:end]


def declaration_rule(system: str) -> str:
    start = system.find("STRUCTURED CLAIM DECLARATION RULE")
    end = system.find("BOUNDED IMPROVISATION AUTHORITY")
    if start < 0 or end < 0:
        return ""
    return system[start:end]


def probe_snapshot(doc: dict, raw: dict | None) -> dict:
    user = user_obj(doc)
    system = system_text(doc)
    recipe = user.get("decision_facing_answer_recipe") or {}
    decision = user.get("gm_resolution_decision") or {}
    contract = user.get("resolution_contract") or {}
    policy = user.get("response_policy") or {}
    packet = user.get("turn_packet") or {}
    parsed = {}
    if raw:
        try:
            parsed = json.loads(raw["parsed"]["raw_output"])
        except (KeyError, json.JSONDecodeError, TypeError):
            parsed = {}
    claims = parsed.get("declared_claims") or []
    return {
        "input_chars": doc["measurements"]["input_chars"],
        "system_chars": len(system),
        "system_sha": sha(system),
        "instruction_count": len(user.get("instructions") or []),
        "instruction_chars": sum(len(item) for item in (user.get("instructions") or [])),
        "user_top_keys": sorted(user.keys()),
        "player_input": user.get("player_input"),
        "turn_summary_raw": (user.get("turn_summary") or {}).get("raw_player_input"),
        "recipe_requested_answer": recipe.get("requested_answer"),
        "recipe_strategy": recipe.get("answer_strategy"),
        "recipe_inference_allowed": (recipe.get("permitted_inference") or {}).get("allowed"),
        "recipe_modality": recipe.get("inference_modality"),
        "recipe_unresolved": recipe.get("unresolved_content"),
        "recipe_forbidden": recipe.get("forbidden_upgrades"),
        "recipe_declaration_guidance": recipe.get("declaration_guidance"),
        "recipe_incidental": recipe.get("incidental_improvisation_guidance"),
        "contract_keys": sorted(contract.keys()),
        "contract_operation": contract.get("operation"),
        "contract_dimension": contract.get("dimension"),
        "contract_constraint": contract.get("constraint"),
        "decision_keys": sorted(decision.keys()),
        "decision_claim_count": len(decision.get("realization_claims") or []),
        "decision_has_epistemic_acts": "epistemic_acts" in decision,
        "decision_has_narration_constraints": "narration_constraints" in decision,
        "decision_unresolved_qualifiers": decision.get("unresolved_qualifiers"),
        "policy_answer_completeness_enabled": (policy.get("answer_completeness") or {}).get("enabled"),
        "policy_player_direct_question": (policy.get("answer_completeness") or {}).get("player_direct_question"),
        "policy_uncertainty_shape": (policy.get("uncertainty") or {}).get("answer_shape"),
        "policy_fallback_hedge": ((policy.get("fallback_behavior") or {}).get("allowed_behaviors") or {}).get(
            "hedge_appropriately"
        ),
        "policy_fallback_uncertainty_active": (policy.get("fallback_behavior") or {}).get("uncertainty_active"),
        "policy_require_unknown_edge": (policy.get("fallback_behavior") or {}).get(
            "require_partial_to_state_unknown_edge"
        ),
        "response_type": (policy.get("response_type_contract") or {}).get("required_response_type"),
        "narrative_mode": (user.get("narrative_plan") or {}).get("narrative_mode"),
        "role_allocation": (user.get("narrative_plan") or {}).get("role_allocation"),
        "scene_momentum_instruction_present": any(
            "SCENE MOMENTUM" in item for item in (user.get("instructions") or [])
        ),
        "must_advance_scene": (user.get("narration_obligations") or {}).get("must_advance_scene"),
        "schema_chars": len(schema_slice(system)),
        "declaration_rule_chars": len(declaration_rule(system)),
        "model_narration": parsed.get("narration"),
        "model_claims": [
            {
                "declaration_mode": row.get("declaration_mode"),
                "source_claim_id": row.get("source_claim_id"),
                "provenance_requested": row.get("provenance_requested"),
                "epistemic_status": row.get("epistemic_status"),
                "modality": row.get("modality"),
                "realization_role": row.get("realization_role"),
                "relation_kind": row.get("relation_kind"),
                "text": row.get("text"),
            }
            for row in claims
            if isinstance(row, dict)
        ],
        "model_improvisations": parsed.get("improvisation_proposals"),
        "packet_player_text": packet.get("player_text"),
        "salience_system": family_chars(system),
        "salience_instructions": family_chars("\n".join(user.get("instructions") or [])),
        "salience_recipe": family_chars(json.dumps(recipe, ensure_ascii=False)),
        "salience_policy": family_chars(json.dumps(policy, ensure_ascii=False)),
        "salience_schema": family_chars(schema_slice(system) + "\n" + declaration_rule(system)),
    }


def retry_prefix(doc: dict) -> str:
    messages = provider_messages(doc)
    if len(messages) < 3:
        return ""
    content = messages[2]["content"]
    marker = "AUTHORITATIVE RETRY CONTEXT"
    if marker in content:
        return content.split(marker, 1)[0].strip()
    return content[:1500]


def main() -> None:
    probes = ("P1", "P2", "P3")
    report: dict = {"probes": {}, "system_identity": {}, "instruction_deltas": {}}
    systems = {}
    for label, base in (
        ("current", CURRENT),
        ("selective", SELECTIVE),
        ("raw_bt", RAW_BT),
        ("pr_bs", PR_BS),
    ):
        systems[label] = {}
        for probe in probes:
            path = base / probe / "provider_request_attempt_generation_1.json"
            if not path.exists():
                continue
            doc = load(path)
            systems[label][probe] = system_text(doc)
            report["system_identity"].setdefault(label, {})[probe] = {
                "sha": sha(system_text(doc)),
                "chars": len(system_text(doc)),
                "request_chars": doc["measurements"]["input_chars"],
            }

    for probe in probes:
        current_doc = load(CURRENT / probe / "provider_request_attempt_generation_1.json")
        bs_doc = load(PR_BS / probe / "provider_request_attempt_generation_1.json")
        raw_path = CURRENT / probe / "raw_generation_attempt_1.json"
        bs_raw = load(PR_BS / probe / "raw_generation_attempt_1.json")
        current_raw = load(raw_path)
        current_user = user_obj(current_doc)
        bs_user = user_obj(bs_doc)
        delta = instruction_delta(bs_user["instructions"], current_user["instructions"])
        report["instruction_deltas"][probe] = {
            "removed_count": delta["removed_count"],
            "added_count": delta["added_count"],
            "removed_chars": delta["removed_chars"],
            "added_chars": delta["added_chars"],
            "removed_heads": [item["text"][:240] for item in delta["removed"]],
            "added_heads": [item["text"][:240] for item in delta["added"]],
        }
        (OUT / f"{probe}_removed_instructions.json").write_text(
            json.dumps(delta["removed"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (OUT / f"{probe}_added_instructions.json").write_text(
            json.dumps(delta["added"], indent=2, ensure_ascii=False), encoding="utf-8"
        )
        selective_doc = load(SELECTIVE / probe / "provider_request_attempt_generation_1.json")
        report["probes"][probe] = {
            "current": probe_snapshot(current_doc, current_raw),
            "pr_bs": probe_snapshot(bs_doc, bs_raw),
            "payload_sha_current": sha(provider_messages(current_doc)[1]["content"]),
            "payload_sha_selective": sha(system_text(selective_doc) + provider_messages(selective_doc)[1]["content"]),
            "payload_sha_current_full": sha(system_text(current_doc) + provider_messages(current_doc)[1]["content"]),
            "system_equal_selective": system_text(current_doc) == system_text(selective_doc),
            "user_equal_selective": provider_messages(current_doc)[1]["content"]
            == provider_messages(selective_doc)[1]["content"],
            "recipe_equal_pr_bs": current_user.get("decision_facing_answer_recipe")
            == bs_user.get("decision_facing_answer_recipe"),
            "decision_equal_pr_bs": current_user.get("gm_resolution_decision")
            == bs_user.get("gm_resolution_decision"),
            "contract_equal_pr_bs": current_user.get("resolution_contract") == bs_user.get("resolution_contract"),
            "policy_equal_pr_bs": current_user.get("response_policy") == bs_user.get("response_policy"),
        }
        retry_path = CURRENT / probe / "provider_request_attempt_generation_2.json"
        if retry_path.exists():
            report["probes"][probe]["retry_prefix"] = retry_prefix(load(retry_path))
            report["probes"][probe]["retry_message_count"] = len(provider_messages(load(retry_path)))

    # System prompt unique delta, using P1 as the shared prompt.
    bs_sys = systems["pr_bs"]["P1"]
    cur_sys = systems["current"]["P1"]
    (OUT / "P1_system_PR-BS.txt").write_text(bs_sys, encoding="utf-8")
    (OUT / "P1_system_current.txt").write_text(cur_sys, encoding="utf-8")
    report["system_prompt_delta"] = {
        "pr_bs_chars": len(bs_sys),
        "current_chars": len(cur_sys),
        "equal_across_current_probes": len({systems["current"][p] for p in probes}) == 1,
        "equal_across_pr_bs_probes": len({systems["pr_bs"][p] for p in probes}) == 1,
        "current_equals_selective_p1": systems["current"]["P1"] == systems["selective"]["P1"],
    }
    (OUT / "measurements.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT / "measurements.json")
    print("system", report["system_prompt_delta"])
    for probe in probes:
        row = report["probes"][probe]
        print(
            probe,
            "user_equal_selective",
            row["user_equal_selective"],
            "recipe_equal",
            row["recipe_equal_pr_bs"],
            "decision_keys",
            row["current"]["decision_keys"],
            "removed_chars",
            report["instruction_deltas"][probe]["removed_chars"],
            "added_chars",
            report["instruction_deltas"][probe]["added_chars"],
        )


if __name__ == "__main__":
    main()
