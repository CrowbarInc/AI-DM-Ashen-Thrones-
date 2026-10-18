"""Deterministic PR-DJ routing preflight and controls."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

from experiments.pr_dg.isolation import ProductionSaveGuard, forbid_provider_calls
from experiments.pr_dg.resolve import select_contract
from experiments.pr_dg.scenarios import (
    AMBIGUOUS,
    C1,
    COMPOUND,
    DUMP,
    FACT,
    F1,
    O1,
    S1,
    scenario_table,
)
from experiments.pr_dg.state import combat_bundle, exploration_bundle, followup_bundle, frontier_bundle, state_hash
from experiments.pr_dj.adapter import (
    STATUS_ABSTAIN,
    STATUS_CLARIFICATION_REQUIRED,
    STATUS_INTERPRETED,
    STATUS_MULTI_ACTION,
    STATUS_UNSUPPORTED_REQUEST,
    validate_hand_authored_interpretation,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dj_selective_interpretation"


def _construction(selector: Mapping[str, Any]) -> Mapping[str, Any]:
    construction = selector.get("construction")
    return construction if isinstance(construction, Mapping) else {}


def _signals(selector: Mapping[str, Any], text: str) -> dict[str, bool]:
    construction = selector.get("construction") if isinstance(selector.get("construction"), Mapping) else {}
    binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), Mapping) else {}
    secondary = [str(item) for item in construction.get("secondary_operations") or []]
    executable = construction.get("executable_obligations") if isinstance(construction.get("executable_obligations"), Mapping) else {}
    low = text.lower()
    return {
        "explicit_abstention": bool(construction.get("fast_path_abstained")),
        "unsupported_resolver_outcome": False,
        "missing_required_entity": binding.get("status") in {"unresolved", "rejected_consequential"},
        "unresolved_pronoun": bool(selector.get("ambiguous") and any(word in low.split() for word in ("him", "her", "them", "it"))),
        "multiple_possible_referents": bool(selector.get("ambiguous") or binding.get("status") == "ambiguous"),
        "compound_action": len(secondary) > 1 or sum(1 for value in executable.values() if value) > 1,
        "resolver_disagreement": bool(selector.get("resolver") == "generation" and construction.get("resolution_subject") in {"social", "travel", "combat", "world_action"}),
        "unsupported_mechanic": any(term in low for term in ("hit points", " hp", "inventory", "roll", "world flags")),
        "attempted_direct_state_override": any(term in low for term in ("set ", "give me ", "update the world", "hit points to zero")),
        "attempted_world_canon_declaration": any(term in low for term in ("that is a fact", "secretly agrees", "the tunnel is now open")),
    }


def _request_assistance(signals: Mapping[str, bool], selector: Mapping[str, Any]) -> bool:
    pre_execution = [
        "explicit_abstention",
        "missing_required_entity",
        "unresolved_pronoun",
        "multiple_possible_referents",
        "compound_action",
        "resolver_disagreement",
        "unsupported_mechanic",
        "attempted_direct_state_override",
        "attempted_world_canon_declaration",
    ]
    if any(signals.get(key) for key in pre_execution):
        return True
    construction = selector.get("construction") if isinstance(selector.get("construction"), Mapping) else {}
    return bool(construction.get("model_interpretation_appropriate"))


def _classify(*, requested: bool, justified: bool) -> str:
    if requested and justified:
        return "CORRECT_TRIGGER"
    if requested and not justified:
        return "FALSE_TRIGGER"
    if not requested and justified:
        return "MISSED_TRIGGER"
    return "NO_TRIGGER_NEEDED"


def _scenario_specs() -> list[dict[str, Any]]:
    selected = {row["scenario_id"]: row for row in scenario_table() if row["scenario_id"] in {"S1", "C1", "compound", "ambiguous", "declared_canon", "mechanical_dump"}}
    controls = [
        {"scenario_id": "control_movement", "utterance": "I walk closer to the notice board.", "factory": exploration_bundle, "justified": False},
        {"scenario_id": "control_combat", "utterance": "I attack the goblin with my quarterstaff.", "factory": combat_bundle, "justified": False},
        {"scenario_id": "control_observation", "utterance": O1, "factory": exploration_bundle, "justified": False},
        {"scenario_id": "control_authored_fact", "utterance": F1, "factory": lambda: frontier_bundle(bind=True), "justified": False},
        {"scenario_id": "control_followup", "utterance": "Does the rain make it harder to keep watch?", "factory": followup_bundle, "justified": False},
    ]
    required = [
        ("S1", S1, False),
        ("C1", C1, True),
        ("compound", COMPOUND, True),
        ("ambiguous", AMBIGUOUS, True),
        ("declared_canon", FACT, True),
        ("mechanical_dump", DUMP, True),
    ]
    specs: list[dict[str, Any]] = []
    for sid, utterance, justified in required:
        row = selected[sid]
        specs.append(
            {
                "scenario_id": sid,
                "utterance": utterance,
                "factory": row["factory"],
                "justified": justified,
            }
        )
    specs.extend(controls)
    return specs


def run_routing_preflight() -> dict[str, Any]:
    with ProductionSaveGuard() as guard:
        with forbid_provider_calls() as provider_hits:
            rows = []
            for spec in _scenario_specs():
                bundle = spec["factory"]()
                before_hash = state_hash(bundle)
                selector = select_contract(bundle, spec["utterance"])
                after_hash = state_hash(bundle)
                signals = _signals(selector, spec["utterance"])
                requested = _request_assistance(signals, selector)
                rows.append(
                    {
                        "scenario_id": spec["scenario_id"],
                        "utterance": spec["utterance"],
                        "selected_resolver": selector.get("resolver"),
                        "routing_signals": signals,
                        "interpretation_assistance_requested": requested,
                        "assistance_justified": bool(spec["justified"]),
                        "pre_mutation_signal": before_hash == after_hash,
                        "state_changed": before_hash != after_hash,
                        "classification": _classify(requested=requested, justified=bool(spec["justified"])),
                    }
                )
        guard.assert_unchanged()
    if provider_hits:
        raise RuntimeError(f"provider calls: {provider_hits}")
    return {
        "live_provider_calls": 0,
        "rows": rows,
        "precision_recall": _precision_recall(rows),
    }


def _precision_recall(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    labeled = [row for row in rows if isinstance(row.get("assistance_justified"), bool)]
    tp = sum(1 for row in labeled if row["interpretation_assistance_requested"] and row["assistance_justified"])
    fp = sum(1 for row in labeled if row["interpretation_assistance_requested"] and not row["assistance_justified"])
    fn = sum(1 for row in labeled if not row["interpretation_assistance_requested"] and row["assistance_justified"])
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {"labeled_rows": len(labeled), "true_positive": tp, "false_positive": fp, "false_negative": fn, "precision": precision, "recall": recall}


def _referents() -> list[dict[str, str]]:
    return [
        {"type": "interlocutor", "id": "guard_captain", "label": "Guard Captain", "source": "scene"},
        {"type": "object", "id": "notice_board", "label": "notice board", "source": "scene"},
        {"type": "enemy", "id": "goblin_1", "label": "goblin", "source": "scene"},
    ]


def run_adapter_controls() -> dict[str, Any]:
    controls = {
        "positive_simple_social_intent": (
            S1,
            {
                "status": STATUS_INTERPRETED,
                "interpreted_intent": "Ask the guard captain about a preference.",
                "referenced_entities": [{"type": "interlocutor", "id": "guard_captain", "label": "Guard Captain"}],
                "primary_operation": "ask",
                "interlocutor_id": "guard_captain",
                "confidence": "high",
                "non_authoritative_explanation": "Intent only; no outcome.",
            },
        ),
        "positive_unresolved_pronouns": (
            AMBIGUOUS,
            {
                "status": STATUS_CLARIFICATION_REQUIRED,
                "clarification_required": True,
                "clarification_question": "Who do you mean by him, and who is the other one?",
                "unresolved_references": ["him", "the other one"],
                "primary_operation": "unresolved",
                "ambiguous": True,
                "confidence": "low",
            },
        ),
        "positive_multi_action": (
            COMPOUND,
            {
                "status": STATUS_MULTI_ACTION,
                "interpreted_intent": "Approach the board, then try to pry it loose.",
                "multiple_action_components": ["approach the notice board", "pry the notice board off the post"],
                "primary_operation": "act",
                "supporting_operations": ["act", "act"],
                "raw_target_text": "notice board",
                "proposed_target_id": "notice_board",
            },
        ),
        "positive_unsupported_mechanic": (
            DUMP,
            {
                "status": STATUS_UNSUPPORTED_REQUEST,
                "unsupported_action": "Direct HP assignment and inventory grant are not interpretation.",
                "primary_operation": "unresolved",
                "confidence": "high",
            },
        ),
        "negative_direct_hp_assignment": (DUMP, {"status": STATUS_INTERPRETED, "hit_points": {"goblin_1": 0}, "primary_operation": "act"}),
        "negative_world_flags": (FACT, {"status": STATUS_INTERPRETED, "world_flags": {"tunnel_open": True}, "primary_operation": "act"}),
        "negative_unauthorized_npc_commitment": (FACT, {"status": STATUS_INTERPRETED, "npc_commitments": {"guard_captain": "betrays watch"}, "primary_operation": "ask"}),
        "negative_hidden_information": (DUMP, {"status": STATUS_INTERPRETED, "hidden_facts": ["secret tunnel"], "primary_operation": "ask"}),
        "negative_fabricated_dice": (DUMP, {"status": STATUS_INTERPRETED, "dice_result": 20, "primary_operation": "act"}),
        "negative_invented_entity_id": (S1, {"status": STATUS_INTERPRETED, "referenced_entities": [{"type": "interlocutor", "id": "invented_guard"}], "primary_operation": "ask", "interlocutor_id": "invented_guard"}),
        "negative_unsupported_resolver": (S1, {"status": STATUS_INTERPRETED, "resolver": "freeform_magic", "primary_operation": "ask"}),
        "negative_execution_request": (COMPOUND, {"status": STATUS_INTERPRETED, "execute_action": True, "primary_operation": "act"}),
        "negative_silent_ambiguous_guess": (
            AMBIGUOUS,
            {
                "status": STATUS_INTERPRETED,
                "interpreted_intent": "Ask him about the other one.",
                "primary_operation": "ask",
                "interlocutor_id": "guard_captain",
                "confidence": "high",
            },
        ),
        "negative_malformed_output": (S1, ["not", "an", "object"]),
    }
    rows = []
    for name, (raw, payload) in controls.items():
        result = validate_hand_authored_interpretation(payload, raw_input=raw, canonical_referents=_referents())
        expected_accept = name.startswith("positive_")
        rows.append(
            {
                "name": name,
                "expected_accept": expected_accept,
                "accepted": result.accepted,
                "passed": result.accepted is expected_accept,
                "status": result.status,
                "errors": list(result.errors),
                "executed": result.executed,
                "mutated_state": result.mutated_state,
            }
        )
    return {"rows": rows, "passed": all(row["passed"] for row in rows)}


def write_routing_csv(payload: Mapping[str, Any], path: Path | None = None) -> Path:
    path = path or OUT / "PR-DJ_routing_results.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "scenario_id",
        "selected_resolver",
        "interpretation_assistance_requested",
        "assistance_justified",
        "pre_mutation_signal",
        "state_changed",
        "classification",
        "signals",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in payload["rows"]:
            writer.writerow(
                {
                    "scenario_id": row["scenario_id"],
                    "selected_resolver": row["selected_resolver"],
                    "interpretation_assistance_requested": row["interpretation_assistance_requested"],
                    "assistance_justified": row["assistance_justified"],
                    "pre_mutation_signal": row["pre_mutation_signal"],
                    "state_changed": row["state_changed"],
                    "classification": row["classification"],
                    "signals": json.dumps(row["routing_signals"], sort_keys=True),
                }
            )
    return path
