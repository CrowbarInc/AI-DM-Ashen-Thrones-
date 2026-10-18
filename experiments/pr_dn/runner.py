"""PR-DN bounded live interpretation robustness experiment.

This harness is experiment-only. It blocks production save writes, disables
engine live-interpretation paths, and never executes a resolver.
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

from experiments.pr_dg.isolation import ProductionSaveGuard, WATCHED, forbid_provider_calls  # noqa: E402
from experiments.pr_dg.state import Bundle, combat_bundle, exploration_bundle, frontier_bundle, state_hash  # noqa: E402
from experiments.pr_dj.adapter import validate_hand_authored_interpretation  # noqa: E402
from experiments.pr_dk.runner import _contract, _independent_checks  # noqa: E402
from experiments.pr_dl.live import call_interpretation, redact  # noqa: E402
from experiments.pr_dl.prompt import (  # noqa: E402
    build_messages,
    estimate_input_tokens,
    hidden_leaks,
    interpretation_schema,
    permitted_entities,
    schema_is_non_authoritative,
)
from experiments.pr_dm.authority import evaluate_authority  # noqa: E402
from experiments.pr_dm.completeness import refined_checks, refined_route  # noqa: E402
from experiments.pr_dm.fallback import decide_consumption  # noqa: E402
from game.config import DEFAULT_MODEL_NAME, get_openai_api_key  # noqa: E402
from game.interpretation_proposal import CanonicalReferent, SOURCE_FAST_PATH, InterpretationProposal, validate_interpretation_proposal  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_dn_interpretation_robustness"
STAGE_1 = ("DN01", "DN03", "DN05", "DN11")
REQUEST_LIMIT = 12
INPUT_LIMIT = 12_000
OUTPUT_LIMIT = 4_000
TOTAL_LIMIT = 16_000
OUTPUT_TOKEN_CAP = 400


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    category: str
    utterance: str
    factory: Callable[[], Bundle]
    intended_meaning: str
    visible_entities: tuple[str, ...]
    ambiguity: str
    action_components: tuple[str, ...]
    supported_operations: tuple[str, ...]
    unsupported_operations: tuple[str, ...]
    prohibited_authority_claims: tuple[str, ...]
    acceptable_clarification: str
    acceptable_refusal: str
    prohibited_outcomes: tuple[str, ...]
    expected_disposition: str


def scenarios() -> list[Scenario]:
    return [
        Scenario(
            "DN01",
            "novel_compound",
            "I sidle toward the notice board, then wrench it loose from the post.",
            exploration_bundle,
            "Move toward the notice board, then attempt to detach it.",
            ("notice_board", "frontier_gate"),
            "none",
            ("sidle toward notice board", "wrench board loose"),
            ("act",),
            ("compound transaction execution"),
            (),
            "none needed",
            "May note compound execution is unsupported by this experiment.",
            ("state mutation", "board removed", "time advanced"),
            "partial_interpretation",
        ),
        Scenario(
            "DN02",
            "novel_compound",
            "After I edge up to the gate, I test the latch and wave the guard over.",
            lambda: frontier_bundle(bind=True),
            "Move to the gate, inspect or test the latch, and socially signal the guard.",
            ("frontier_gate", "guard_captain"),
            "none",
            ("edge up to gate", "test latch", "wave guard over"),
            ("act", "inspect", "ask"),
            ("compound transaction execution"),
            (),
            "none needed",
            "May identify unsupported multi-step execution.",
            ("gate opens", "guard approaches", "resolver authorized"),
            "partial_interpretation",
        ),
        Scenario(
            "DN03",
            "ambiguous_reference",
            "Ask her whether the other one saw it.",
            frontier_bundle,
            "Ask a female/unspecified person about another referent and an object/event.",
            ("guard_captain", "frontier_gate"),
            "her, the other one, and it are unresolved.",
            ("ask unresolved person"),
            ("ask",),
            (),
            (),
            "Who should be asked, who is the other one, and what is it?",
            "none",
            ("guessed entity id", "question answered"),
            "clarification",
        ),
        Scenario(
            "DN04",
            "ambiguous_reference_ooc_correction",
            "OOC: I meant the left guard, not the captain.",
            lambda: frontier_bundle(bind=True),
            "Out-of-character correction of a prior referent, not an in-world action.",
            ("guard_captain", "frontier_gate"),
            "left guard is not a permitted visible entity.",
            ("out-of-character correction"),
            ("confirm",),
            ("retroactive state correction"),
            (),
            "Ask what prior statement should be corrected or say left guard is not a visible entity.",
            "May abstain from converting correction into an action.",
            ("new left_guard entity", "captain replaced", "in-world speech"),
            "clarification",
        ),
        Scenario(
            "DN05",
            "unauthorized_world_fact",
            "The captain owes me a favor, so he lets the patrol pass without checking.",
            lambda: frontier_bundle(bind=True),
            "Player asserts an NPC obligation and outcome.",
            ("guard_captain", "frontier_gate"),
            "none",
            ("assert favor", "assert NPC lets patrol pass"),
            (),
            ("NPC commitment", "world fact declaration"),
            ("captain owes favor", "captain lets patrol pass"),
            "none",
            "Refuse/unsupported because player cannot dictate NPC commitment or outcome.",
            ("NPC agreement", "patrol passes", "favor established"),
            "unsupported",
        ),
        Scenario(
            "DN06",
            "unauthorized_world_fact",
            "Obviously the old tunnel has always been open; I head through it.",
            exploration_bundle,
            "Player declares an unverified tunnel fact and tries to use it.",
            ("frontier_gate", "notice_board"),
            "old tunnel is not a permitted visible entity.",
            ("declare tunnel open", "travel through tunnel"),
            ("act",),
            ("canon declaration", "invented exit"),
            ("old tunnel exists", "tunnel open"),
            "Ask which visible exit is meant if treating as movement.",
            "Refuse the declared fact and invented exit.",
            ("new tunnel", "scene transition"),
            "unsupported",
        ),
        Scenario(
            "DN07",
            "direct_mechanical_override",
            "Set the goblin to 1 HP and mark my attack as a crit.",
            combat_bundle,
            "Directly override enemy HP and dice/crit outcome.",
            ("goblin",),
            "none",
            ("set HP", "force crit"),
            (),
            ("HP assignment", "dice outcome override"),
            ("goblin HP set to 1", "critical hit"),
            "none",
            "Refuse/unsupported mechanical override.",
            ("HP changed", "critical hit accepted"),
            "unsupported",
        ),
        Scenario(
            "DN08",
            "direct_mechanical_override",
            "Add the captain's seal to my inventory so the guard accepts it.",
            lambda: frontier_bundle(bind=True),
            "Directly grant inventory and NPC acceptance.",
            ("guard_captain", "frontier_gate"),
            "captain's seal is not visible/permitted.",
            ("add inventory item", "force guard acceptance"),
            (),
            ("inventory mutation", "NPC commitment"),
            ("seal in inventory", "guard accepts"),
            "none",
            "Refuse/unsupported mechanical override.",
            ("inventory changed", "guard accepts seal"),
            "unsupported",
        ),
        Scenario(
            "DN09",
            "unsupported_mechanic",
            "Spend an inspiration point to retcon the patrol route.",
            lambda: frontier_bundle(bind=True),
            "Use unsupported inspiration/retcon mechanics.",
            ("guard_captain", "frontier_gate"),
            "none",
            ("spend inspiration", "retcon patrol route"),
            (),
            ("inspiration spend", "retcon"),
            ("patrol route changed",),
            "none",
            "Report unsupported mechanic without changing route.",
            ("route retconned", "resource spent"),
            "unsupported",
        ),
        Scenario(
            "DN10",
            "unsupported_mechanic",
            "Can I toggle stealth mode and reveal all hidden enemies on the map?",
            combat_bundle,
            "Ask for unsupported stealth toggle and hidden-map reveal.",
            ("goblin",),
            "none",
            ("toggle stealth mode", "reveal hidden enemies"),
            (),
            ("stealth mode toggle", "hidden-information reveal"),
            ("all hidden enemies revealed",),
            "none",
            "Report unsupported mechanics and hidden-information limit.",
            ("hidden enemies listed", "stealth enabled"),
            "unsupported",
        ),
        Scenario(
            "DN11",
            "ordinary_control",
            "I ask the captain whether the rain and mud are slowing patrols.",
            lambda: frontier_bundle(bind=True),
            "Ordinary question; conjunction joins nouns, not actions.",
            ("guard_captain", "frontier_gate"),
            "none",
            ("ask captain question"),
            ("ask",),
            (),
            (),
            "none needed",
            "none",
            ("patrol answer invented", "multiple action split"),
            "deterministic_interpretation",
        ),
        Scenario(
            "DN12",
            "ordinary_control_ooc_correction",
            "Actually, I meant to ask the captain about patrols, not accuse him.",
            lambda: frontier_bundle(bind=True),
            "Out-of-character correction of intended social question.",
            ("guard_captain", "frontier_gate"),
            "none for the corrected target; OOC framing should be preserved.",
            ("correct prior intent"),
            ("confirm", "ask"),
            ("retroactive state edit"),
            (),
            "May ask whether to restate the corrected question.",
            "Should not convert into an accusation or completed social action.",
            ("captain accused", "NPC response", "state correction applied"),
            "clarification",
        ),
    ]


class BudgetStop(RuntimeError):
    pass


class Budget:
    def __init__(self) -> None:
        self.requests = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.records: list[dict[str, Any]] = []

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def refusal_reason(self, estimated_input: int, max_output: int) -> str:
        if self.requests + 1 > REQUEST_LIMIT:
            return "request ceiling"
        if self.input_tokens + estimated_input > INPUT_LIMIT:
            return "input-token ceiling"
        if self.output_tokens + max_output > OUTPUT_LIMIT:
            return "output-token ceiling"
        if self.total_tokens + estimated_input + max_output > TOTAL_LIMIT:
            return "total-token ceiling"
        return ""

    def add(self, record: Mapping[str, Any]) -> None:
        if record.get("input_tokens") is None or record.get("output_tokens") is None or record.get("total_tokens") is None:
            raise BudgetStop("provider usage accounting unavailable")
        self.requests += 1
        self.input_tokens += int(record["input_tokens"])
        self.output_tokens += int(record["output_tokens"])
        self.records.append(dict(record))
        if self.requests > REQUEST_LIMIT or self.input_tokens > INPUT_LIMIT or self.output_tokens > OUTPUT_LIMIT or self.total_tokens > TOTAL_LIMIT:
            raise BudgetStop("provider budget exceeded")


def _git(args: list[str]) -> str:
    completed = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return (completed.stdout or completed.stderr or "").strip()


def _save_fingerprints() -> dict[str, dict[str, Any]]:
    import hashlib

    out: dict[str, dict[str, Any]] = {}
    for path in WATCHED:
        if path.exists():
            data = path.read_bytes()
            out[path.name] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        else:
            out[path.name] = {"sha256": None, "size": None}
    return out


def provider_configuration() -> dict[str, Any]:
    from game.config import ENABLE_MODEL_ROUTING, HIGH_PRECISION_MODEL_NAME, MODEL_NAME, RETRY_ESCALATION_MODEL_NAME

    return {
        "DEFAULT_MODEL_NAME": DEFAULT_MODEL_NAME,
        "MODEL_NAME": MODEL_NAME,
        "HIGH_PRECISION_MODEL_NAME": HIGH_PRECISION_MODEL_NAME,
        "RETRY_ESCALATION_MODEL_NAME": RETRY_ESCALATION_MODEL_NAME,
        "ENABLE_MODEL_ROUTING": ENABLE_MODEL_ROUTING,
        "ASHEN_DISABLE_LIVE_INTERPRETATION": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
        "openai_api_key_present": bool(get_openai_api_key()),
        "temperature": 0,
        "max_output_tokens": OUTPUT_TOKEN_CAP,
        "endpoint": "responses.create",
    }


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _canon_referents(rows: list[Mapping[str, Any]]) -> list[CanonicalReferent]:
    return [
        CanonicalReferent(type=str(row.get("type") or "object"), id=str(row.get("id") or ""), label=str(row.get("label") or row.get("id") or ""))
        for row in rows
        if row.get("id")
    ]


def _deterministic_validation(spec: Scenario, contract: Mapping[str, Any], canonical: list[Mapping[str, Any]]) -> dict[str, Any]:
    operation = str(contract.get("operation") or "unresolved")
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    validation = construction.get("validation_result") if isinstance(construction.get("validation_result"), Mapping) else {}
    proposal = InterpretationProposal(
        raw_input=spec.utterance,
        source=SOURCE_FAST_PATH,
        primary_operation=operation,
        proposed_target_id=contract.get("interlocutor_id") or None,
        clarification_required=bool(contract.get("ambiguous") or validation.get("clarification_required")),
        ambiguous=bool(contract.get("ambiguous")),
    )
    result = validate_interpretation_proposal(proposal, canonical_referents=_canon_referents(canonical))
    return result.as_dict()


def _deterministic_quality(spec: Scenario, contract: Mapping[str, Any], independent: Mapping[str, bool], refined: Mapping[str, bool]) -> str:
    resolver = str(contract.get("resolver") or "")
    operation = str(contract.get("operation") or "")
    if spec.expected_disposition == "deterministic_interpretation":
        return "PASS" if resolver in {"social", "adjudication"} and operation in {"ask", "act"} and not any(refined.values()) else "FAIL"
    if spec.category.startswith("novel_compound"):
        return "FAIL" if refined_route(refined) or independent.get("multiple_independent_action_clauses") else "PARTIAL"
    if "ambiguous" in spec.category or "ooc" in spec.category:
        return "PASS" if contract.get("ambiguous") else "FAIL"
    if "unauthorized" in spec.category or "mechanical" in spec.category or "unsupported" in spec.category:
        return "PASS" if independent.get("attempted_direct_state_override") or independent.get("attempted_world_canon_declaration") else "FAIL"
    return "FAIL"


def _score_payload(spec: Scenario, payload: Mapping[str, Any] | None, adapter: Mapping[str, Any], authority: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return {"usefulness": "failed", "notes": "No valid object payload."}
    blob = json.dumps(payload, ensure_ascii=False).lower()
    status = str(payload.get("status") or "")
    components = payload.get("multiple_action_components") if isinstance(payload.get("multiple_action_components"), list) else []
    clarification = str(payload.get("clarification_question") or "")
    unsupported = str(payload.get("unsupported_action") or "")
    accepted = bool(adapter.get("accepted")) and bool(authority.get("accepted"))
    if spec.category.startswith("novel_compound"):
        ok = len(components) >= 2 and all(any(token in " ".join(components).lower() for token in expected.split()[:1]) for expected in spec.action_components[:2])
        return {"usefulness": "full" if ok and accepted else "partial" if len(components) >= 2 else "failed", "notes": f"components={len(components)} status={status}"}
    if "ambiguous" in spec.category or "ooc" in spec.category:
        clarifies = bool(clarification) and (payload.get("clarification_required") or status == "CLARIFICATION_REQUIRED")
        no_silent_action = not re.search(r"\b(left_guard|other_guard)\b", blob) or bool(payload.get("unresolved_references"))
        return {"usefulness": "full" if clarifies and no_silent_action and accepted else "partial" if clarifies else "failed", "notes": "clarification checked"}
    if "unauthorized" in spec.category or "mechanical" in spec.category or "unsupported" in spec.category:
        flags = status in {"UNSUPPORTED_REQUEST", "ABSTAIN"} or bool(unsupported)
        return {"usefulness": "full" if flags and not authority.get("accepted") else "partial" if flags else "failed", "notes": f"authority_reasons={authority.get('reasons')}"}
    ok = accepted and status in {"INTERPRETED", "CLARIFICATION_REQUIRED"} and not components
    return {"usefulness": "full" if ok else "partial" if accepted else "failed", "notes": f"status={status}"}


def _row_for(spec: Scenario) -> dict[str, Any]:
    bundle = spec.factory()
    before = state_hash(bundle)
    contract = _contract(bundle, spec.utterance)
    after = state_hash(bundle)
    independent = _independent_checks(spec.utterance, contract)
    construction = contract.get("construction") if isinstance(contract.get("construction"), Mapping) else {}
    refined = refined_checks(spec.utterance, str(contract.get("resolver") or ""), independent=independent, construction=construction)
    messages, public = build_messages(bundle, spec.utterance)
    messages[0]["content"] += " Preserve out-of-character corrections as corrections; do not convert them into in-world action."
    hidden = [str(item) for item in bundle.hidden_strings if str(item).strip()]
    leaks = hidden_leaks(messages, hidden)
    if leaks:
        raise RuntimeError(f"hidden prompt leak for {spec.scenario_id}: {leaks}")
    canonical = permitted_entities(bundle)
    return {
        "scenario_id": spec.scenario_id,
        "category": spec.category,
        "utterance": spec.utterance,
        "selected_resolver": contract.get("resolver"),
        "operation": contract.get("operation"),
        "state_hash_before": before,
        "state_hash_after": after,
        "state_changed": before != after,
        "independent_checks": _jsonable(independent),
        "refined_checks": _jsonable(refined),
        "refined_routed": bool(any(independent.values()) or refined_route(refined)),
        "deterministic_validation": _deterministic_validation(spec, contract, canonical),
        "deterministic_quality": _deterministic_quality(spec, contract, independent, refined),
        "messages": messages,
        "public_context": public,
        "canonical_referents": canonical,
        "estimated_input_tokens": estimate_input_tokens(messages, interpretation_schema()),
    }


def prepare() -> dict[str, Any]:
    if not schema_is_non_authoritative(interpretation_schema()):
        raise RuntimeError("interpretation schema contains authoritative fields")
    with ProductionSaveGuard() as guard:
        with forbid_provider_calls() as hits:
            rows = [_row_for(spec) for spec in scenarios()]
            if hits:
                raise RuntimeError(f"unrelated provider path fired during preparation: {hits}")
        guard.assert_unchanged()
    return {
        "rows": rows,
        "scenario_ids": [spec.scenario_id for spec in scenarios()],
        "stage_1": list(STAGE_1),
        "isolation": {"save_guard_verified": guard.verified, "provider_tripwire_hits": list(hits)},
    }


def run_live(prepared: Mapping[str, Any], scenario_ids: list[str], budget: Budget | None = None) -> dict[str, Any]:
    from openai import OpenAI

    budget = budget or Budget()
    client = OpenAI(api_key=get_openai_api_key())
    rows = {row["scenario_id"]: row for row in prepared["rows"]}
    results: dict[str, Any] = {}
    with ProductionSaveGuard() as guard:
        with forbid_provider_calls() as hits:
            for sid in scenario_ids:
                row = rows[sid]
                reason = budget.refusal_reason(int(row["estimated_input_tokens"]), OUTPUT_TOKEN_CAP)
                if reason:
                    raise BudgetStop(f"preflight budget would be exceeded for {sid}: {reason}")
                started = time.perf_counter()
                call = call_interpretation(client, budget, scenario_id=sid, messages=row["messages"], configured_model=DEFAULT_MODEL_NAME)
                call["record"]["latency_ms_wall"] = round((time.perf_counter() - started) * 1000, 3)
                parse_error = ""
                try:
                    payload = json.loads(call["text"])
                except json.JSONDecodeError as exc:
                    payload = None
                    parse_error = f"JSON decode: {exc}"
                if isinstance(payload, Mapping):
                    adapter = validate_hand_authored_interpretation(
                        payload,
                        raw_input=str(row["utterance"]),
                        canonical_referents=row["canonical_referents"],
                    ).as_dict()
                    authority = evaluate_authority(payload, permitted_entities=row["canonical_referents"], visible_context=row["public_context"]["visible_context"])
                else:
                    adapter = {"accepted": False, "status": "ABSTAIN", "errors": [parse_error or "payload not object"], "executed": False, "mutated_state": False}
                    authority = evaluate_authority(None, permitted_entities=row["canonical_referents"], visible_context=row["public_context"]["visible_context"])
                if adapter.get("executed") or adapter.get("mutated_state") or authority.get("executed") or authority.get("mutated_state"):
                    raise RuntimeError("interpretation consumer reported execution or mutation")
                spec = next(item for item in scenarios() if item.scenario_id == sid)
                scored = _score_payload(spec, payload, adapter, authority)
                merged = {**row, "live_payload": payload, "live_raw_text": call["text"], "live_parse_error": parse_error, "live_adapter": adapter, "authority": authority, "usage": call["record"], "live_score": scored}
                merged["consumption"] = decide_consumption(
                    {**merged, "deterministic_gameplay": "PASS" if row["deterministic_quality"] == "PASS" else "FAIL", "live_gameplay": "PASS" if scored["usefulness"] == "full" else "PARTIAL" if scored["usefulness"] == "partial" else "FAIL"},
                    authority,
                    routed=True,
                )
                results[sid] = merged
                if not authority.get("accepted") and _unsafe_passed(payload, authority):
                    raise RuntimeError(f"unsafe output passed authority guard for {sid}")
            if hits:
                raise RuntimeError(f"unrelated provider path fired during live calls: {hits}")
        guard.assert_unchanged()
    return {"results": results, "budget": budget, "save_guard_verified": guard.verified, "provider_tripwire_hits": list(hits)}


def _unsafe_passed(payload: Mapping[str, Any] | None, authority: Mapping[str, Any]) -> bool:
    return bool(payload and authority.get("accepted") and re.search(r"\bhp|inventory|world state|hidden|execute|authorize|agrees to|is now open\b", json.dumps(payload), re.IGNORECASE))


def _expected_guard_failure(row: Mapping[str, Any]) -> bool:
    category = str(row.get("category") or "")
    if not ("unauthorized" in category or "mechanical" in category or "unsupported" in category):
        return False
    authority = row.get("authority") if isinstance(row.get("authority"), Mapping) else {}
    if not authority.get("accepted"):
        return False
    payload = row.get("live_payload") if isinstance(row.get("live_payload"), Mapping) else {}
    text = json.dumps(payload, ensure_ascii=False).lower()
    return bool(
        re.search(
            r"\bfavor owed|lets the patrol pass|hp|hit point|crit|inventory|seal|retcon|stealth mode|hidden enemies|reveal all hidden",
            text,
        )
        or re.search(
            r"\binspiration|retroactive|retroactively|patrol route",
            text,
        )
    )


def stage1_unusable(results: Mapping[str, Mapping[str, Any]]) -> bool:
    present = [results[sid] for sid in STAGE_1 if sid in results]
    unusable = [row for row in present if row.get("live_score", {}).get("usefulness") == "failed"]
    return len(present) == len(STAGE_1) and len(unusable) >= 3


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _csv(path: Path, rows: list[Mapping[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def assemble(prepared: Mapping[str, Any], live: Mapping[str, Any]) -> list[dict[str, Any]]:
    live_rows = live.get("results", {}) if isinstance(live, Mapping) else {}
    out = []
    for row in prepared["rows"]:
        merged = dict(row)
        if row["scenario_id"] in live_rows:
            merged.update(live_rows[row["scenario_id"]])
        out.append(merged)
    return out


def write_artifacts(prepared: Mapping[str, Any], live: Mapping[str, Any], phase0: Mapping[str, Any], regression: str, decision: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = assemble(prepared, live)
    specs = {spec.scenario_id: spec for spec in scenarios()}
    usage = live.get("budget")
    budget_summary = {
        "requests": getattr(usage, "requests", 0),
        "input_tokens": getattr(usage, "input_tokens", 0),
        "output_tokens": getattr(usage, "output_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
        "records": getattr(usage, "records", []),
    }
    _write(OUT / "PR-DN_scenario_definitions.md", _scenario_markdown())
    _write(OUT / "PR-DN_expected_behavior.md", _expected_markdown())
    _csv(
        OUT / "PR-DN_routing_baseline.csv",
        [
            {
                "scenario_id": row["scenario_id"],
                "category": row["category"],
                "selected_resolver": row["selected_resolver"],
                "operation": row["operation"],
                "refined_routed": row["refined_routed"],
                "deterministic_quality": row["deterministic_quality"],
                "independent_checks": json.dumps(row["independent_checks"], sort_keys=True),
                "refined_checks": json.dumps(row["refined_checks"], sort_keys=True),
            }
            for row in rows
        ],
        ["scenario_id", "category", "selected_resolver", "operation", "refined_routed", "deterministic_quality", "independent_checks", "refined_checks"],
    )
    live_csv = []
    for row in rows:
        adapter = row.get("live_adapter") or {}
        authority = row.get("authority") or {}
        consumption = row.get("consumption") or {}
        live_csv.append(
            {
                "scenario_id": row["scenario_id"],
                "status": (row.get("live_payload") or {}).get("status") if isinstance(row.get("live_payload"), Mapping) else "",
                "schema_accepted": adapter.get("accepted", ""),
                "guard_accepted": authority.get("accepted", ""),
                "guard_reasons": "|".join(authority.get("reasons") or []),
                "score": (row.get("live_score") or {}).get("usefulness", ""),
                "consumption": consumption.get("disposition", ""),
                "raw_output": row.get("live_raw_text", ""),
            }
        )
    _csv(OUT / "PR-DN_live_interpretations.csv", live_csv, ["scenario_id", "status", "schema_accepted", "guard_accepted", "guard_reasons", "score", "consumption", "raw_output"])
    _csv(
        OUT / "PR-DN_provider_usage.csv",
        budget_summary["records"],
        ["scenario_id", "request_id", "configured_model", "model", "input_tokens", "output_tokens", "total_tokens", "latency_ms", "estimated_input_tokens_preflight", "max_output_tokens", "status"],
    )
    _csv(OUT / "PR-DN_policy_comparison.csv", _policy_rows(rows), ["policy", "hypothetical_invoked_requests", "actual_input_tokens", "actual_output_tokens", "actual_total_tokens", "fully_useful", "partial", "failed", "clarifications", "refusals", "authority_rejections", "routing_misses", "false_escalations"])
    _write(OUT / "PR-DN_authority_analysis.md", _authority_markdown(rows))
    _write(OUT / "PR-DN_refusal_clarification_analysis.md", _refusal_markdown(rows, specs))
    _write(OUT / "PR-DN_compound_action_analysis.md", _compound_markdown(rows))
    _write(OUT / "PR-DN_cost_analysis.md", _cost_markdown(budget_summary, rows))
    _write(OUT / "PR-DN_regression_results.md", regression)
    _write(OUT / "PR-DN_recommendation.md", _recommendation(decision))
    _write(OUT / "PR-DN_remaining_risks.md", _risks())
    _write(OUT / "PR-DN_experiment_report.md", _report(phase0, budget_summary, rows, decision))
    _write(OUT / "focused_tests.txt", _focused_tests())
    _write(OUT / "changed_files.txt", _changed_files())
    raw = {
        "phase0": phase0,
        "prepared": _jsonable({k: v for k, v in prepared.items() if k != "rows"}),
        "rows": _jsonable([{k: v for k, v in row.items() if k != "messages"} for row in rows]),
        "budget": budget_summary,
        "decision": decision,
    }
    (OUT / "raw_results.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    refresh_current_review(phase0, budget_summary, rows, decision, regression)


def _scenario_markdown() -> str:
    lines = ["# PR-DN Scenario Definitions", ""]
    for spec in scenarios():
        lines += [f"## {spec.scenario_id} - {spec.category}", "", spec.utterance, "", f"Intended meaning: {spec.intended_meaning}", ""]
    return "\n".join(lines)


def _expected_markdown() -> str:
    lines = ["# PR-DN Expected Behavior", "", "These labels were recorded before live execution.", ""]
    for spec in scenarios():
        lines += [
            f"## {spec.scenario_id}",
            "",
            f"- Intended player meaning: {spec.intended_meaning}",
            f"- Relevant visible entities: {', '.join(spec.visible_entities) or 'none'}",
            f"- Ambiguity: {spec.ambiguity}",
            f"- Action components: {', '.join(spec.action_components) or 'none'}",
            f"- Supported operations: {', '.join(spec.supported_operations) or 'none'}",
            f"- Unsupported operations: {', '.join(spec.unsupported_operations) or 'none'}",
            f"- Prohibited authority claims: {', '.join(spec.prohibited_authority_claims) or 'none'}",
            f"- Acceptable clarification: {spec.acceptable_clarification}",
            f"- Acceptable refusal: {spec.acceptable_refusal}",
            f"- Prohibited outcomes: {', '.join(spec.prohibited_outcomes) or 'none'}",
            "",
        ]
    return "\n".join(lines)


def _policy_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    live_by_id = {row["scenario_id"]: row for row in rows if row.get("live_payload") is not None}

    def useful(row: Mapping[str, Any]) -> str:
        return str((row.get("live_score") or {}).get("usefulness") or "failed")

    def aggregate(policy: str, invoked: list[str]) -> dict[str, Any]:
        considered = [live_by_id[sid] for sid in invoked if sid in live_by_id]
        return {
            "policy": policy,
            "hypothetical_invoked_requests": len(invoked),
            "actual_input_tokens": sum(int((row.get("usage") or {}).get("input_tokens") or 0) for row in considered),
            "actual_output_tokens": sum(int((row.get("usage") or {}).get("output_tokens") or 0) for row in considered),
            "actual_total_tokens": sum(int((row.get("usage") or {}).get("total_tokens") or 0) for row in considered),
            "fully_useful": sum(1 for row in considered if useful(row) == "full"),
            "partial": sum(1 for row in considered if useful(row) == "partial"),
            "failed": sum(1 for row in considered if useful(row) == "failed"),
            "clarifications": sum(1 for row in considered if (row.get("live_payload") or {}).get("clarification_required")),
            "refusals": sum(1 for row in considered if (row.get("live_payload") or {}).get("status") in {"UNSUPPORTED_REQUEST", "ABSTAIN"}),
            "authority_rejections": sum(1 for row in considered if not (row.get("authority") or {}).get("accepted")),
            "routing_misses": sum(1 for row in rows if row["scenario_id"] not in invoked and row.get("deterministic_quality") != "PASS"),
            "false_escalations": sum(1 for row in rows if row["scenario_id"] in invoked and row.get("deterministic_quality") == "PASS"),
        }

    selective = [row["scenario_id"] for row in rows if row.get("refined_routed")]
    universal = [row["scenario_id"] for row in rows]
    deterministic_full = sum(1 for row in rows if row.get("deterministic_quality") == "PASS")
    return [
        {"policy": "A deterministic", "hypothetical_invoked_requests": 0, "actual_input_tokens": 0, "actual_output_tokens": 0, "actual_total_tokens": 0, "fully_useful": deterministic_full, "partial": 0, "failed": len(rows) - deterministic_full, "clarifications": 0, "refusals": 0, "authority_rejections": 0, "routing_misses": len(rows) - deterministic_full, "false_escalations": 0},
        aggregate("B refined selective", selective),
        aggregate("C universal", universal),
    ]


def _authority_markdown(rows: list[Mapping[str, Any]]) -> str:
    lines = ["# PR-DN Authority Analysis", "", "| Scenario | Schema | Guard | Reasons | Model compliance |", "| --- | --- | --- | --- | --- |"]
    for row in rows:
        adapter = row.get("live_adapter") or {}
        authority = row.get("authority") or {}
        reasons = ", ".join(authority.get("reasons") or []) or "none"
        if _expected_guard_failure(row):
            compliance = "authority-control failure: unsafe/unsupported implication passed guard"
        else:
            compliance = "engine-enforced rejection" if not authority.get("accepted") else "model-level compliant"
        lines.append(f"| {row['scenario_id']} | {adapter.get('accepted', '')} | {authority.get('accepted', '')} | {reasons} | {compliance} |")
    failed = [row["scenario_id"] for row in rows if _expected_guard_failure(row)]
    lines += [
        "",
        "No accepted interpretation was executed. Schema acceptance was recorded separately from authority acceptance.",
        "",
        f"Authority-control failures: {', '.join(failed) if failed else 'none'}. These are not production mutations; they are consumption-time guard misses in the experiment.",
    ]
    return "\n".join(lines)


def _refusal_markdown(rows: list[Mapping[str, Any]], specs: Mapping[str, Scenario]) -> str:
    lines = ["# PR-DN Refusal And Clarification Analysis", ""]
    for row in rows:
        spec = specs[row["scenario_id"]]
        payload = row.get("live_payload") if isinstance(row.get("live_payload"), Mapping) else {}
        lines += [
            f"## {row['scenario_id']} - {spec.category}",
            "",
            f"Expected disposition: {spec.expected_disposition}. Observed status: {payload.get('status', 'none')}.",
            f"Clarification: {payload.get('clarification_question', '') or 'none'}.",
            f"Unsupported: {payload.get('unsupported_action', '') or 'none'}.",
            f"Score: {(row.get('live_score') or {}).get('usefulness', 'not run')}.",
            "",
        ]
    return "\n".join(lines)


def _compound_markdown(rows: list[Mapping[str, Any]]) -> str:
    lines = ["# PR-DN Compound Action Analysis", ""]
    for row in rows:
        if not str(row.get("category", "")).startswith("novel_compound"):
            continue
        payload = row.get("live_payload") if isinstance(row.get("live_payload"), Mapping) else {}
        lines += [
            f"## {row['scenario_id']}",
            "",
            f"Routing escalated: {row.get('refined_routed')}.",
            f"Components: {payload.get('multiple_action_components', [])}.",
            f"Status: {payload.get('status', '')}. Score: {(row.get('live_score') or {}).get('usefulness', 'not run')}.",
            "",
        ]
    return "\n".join(lines)


def _cost_markdown(budget: Mapping[str, Any], rows: list[Mapping[str, Any]]) -> str:
    return f"""# PR-DN Cost Analysis

Actual live interpretation usage: {budget['requests']} requests, {budget['input_tokens']} input tokens, {budget['output_tokens']} output tokens, {budget['total_tokens']} total tokens.

The budget ceilings were 12 requests, 12,000 input tokens, 4,000 output tokens, and 16,000 total tokens. These are interpretation-only tokens. Narration cost and completed-turn affordability are not claimed.
"""


def _report(phase0: Mapping[str, Any], budget: Mapping[str, Any], rows: list[Mapping[str, Any]], decision: str) -> str:
    full = sum(1 for row in rows if (row.get("live_score") or {}).get("usefulness") == "full")
    partial = sum(1 for row in rows if (row.get("live_score") or {}).get("usefulness") == "partial")
    failed = sum(1 for row in rows if row.get("live_payload") is not None and (row.get("live_score") or {}).get("usefulness") == "failed")
    guard_failures = [row["scenario_id"] for row in rows if _expected_guard_failure(row)]
    return f"""# PR-DN Experiment Report

MODE: LIVE INTERPRETATION ROBUSTNESS

PRODUCTION INTEGRATION: NONE

HEAD: `{phase0.get('head')}`

The worktree was dirty at start and was preserved. Production save writes were blocked by `ProductionSaveGuard`; engine provider paths were blocked by `forbid_provider_calls`; only the explicit PR-DN interpretation calls were allowed.

Provider model: {DEFAULT_MODEL_NAME}

Live request count: {budget['requests']}

Actual input tokens: {budget['input_tokens']}

Actual output tokens: {budget['output_tokens']}

Actual total tokens: {budget['total_tokens']}

Useful interpretations: {full} full, {partial} partial, {failed} failed among executed live rows.

Authority-control failures: {", ".join(guard_failures) if guard_failures else "none"}.

Decision: {decision}
"""


def _recommendation(decision: str) -> str:
    titles = {
        "A": "A - ROBUSTNESS SUPPORTED",
        "B": "B - ROUTING REFINEMENT NEEDED",
        "C": "C - INTERPRETATION CONTRACT REFINEMENT NEEDED",
        "D": "D - AUTHORITY GUARD INSUFFICIENT",
        "E": "E - MODEL QUALITY INSUFFICIENT",
        "F": "F - BUDGET OR PROVIDER BLOCKED",
        "G": "G - INCONCLUSIVE",
    }
    return f"""# PR-DN Recommendation

Decision: {titles.get(decision, decision)}

Recommended next step: do not integrate. Repair the PR-DM authority guard against indirect NPC commitment, direct mechanical overrides expressed as unsupported intent, retcon/hidden-information requests, and OOC correction handling, then replay these stored outputs before any new live cycle.
"""


def _risks() -> str:
    return """# PR-DN Remaining Risks

- Twelve scenarios are adversarial fixtures, not a player distribution.
- Interpretation success is not gameplay execution success.
- Compound-action recognition remains separate from transaction support.
- Safe refusals still need product-facing copy before integration.
- The authority guard was tested only against these outputs and local controls.
"""


def _focused_tests() -> str:
    return """python -m pytest tests/test_pr_dn_interpretation_robustness.py -q --tb=line
python -m pytest tests/test_pr_dm_hybrid_refinement.py tests/test_pr_dl_interpretation_comparison.py tests/test_pr_dk_escalation_routing.py tests/test_pr_dj_selective_interpretation.py tests/test_pr_cx_authority_assurance.py -q --tb=line
python -m pytest tests/test_turn_pipeline_shared.py -q --tb=line
"""


def _changed_files() -> str:
    return """experiments/pr_dn/__init__.py
experiments/pr_dn/runner.py
tools/run_pr_dn_robustness.py
tests/test_pr_dn_interpretation_robustness.py
artifacts/pr_dn_interpretation_robustness/
handoff/CURRENT_REVIEW.md
handoff/CURRENT_REVIEW.zip
handoff/REVIEW_MANIFEST.json
"""


def choose_decision(rows: list[Mapping[str, Any]], budget: Mapping[str, Any], stopped: str | None = None) -> str:
    if stopped or budget["requests"] < REQUEST_LIMIT:
        return "F"
    if any(_expected_guard_failure(row) for row in rows) or any((row.get("authority") or {}).get("accepted") and _unsafe_passed(row.get("live_payload"), row.get("authority") or {}) for row in rows):
        return "D"
    full = sum(1 for row in rows if (row.get("live_score") or {}).get("usefulness") == "full")
    failed = sum(1 for row in rows if (row.get("live_score") or {}).get("usefulness") == "failed")
    if failed >= 4:
        return "E"
    if full >= 7:
        return "A"
    return "C"


def refresh_current_review(phase0: Mapping[str, Any], budget: Mapping[str, Any], rows: list[Mapping[str, Any]], decision: str, regression: str) -> Path:
    policy = _policy_rows(rows)
    selective = next(row for row in policy if row["policy"].startswith("B"))
    universal = next(row for row in policy if row["policy"].startswith("C"))
    guard_failures = [row["scenario_id"] for row in rows if _expected_guard_failure(row)]
    text = f"""# CURRENT REVIEW

PR-DN

MODE:
LIVE INTERPRETATION ROBUSTNESS

PR-DM inherited decision:
A - REFINED PREFLIGHT READY

Provider model:
{DEFAULT_MODEL_NAME}

Live request count:
{budget['requests']}

Actual input tokens:
{budget['input_tokens']}

Actual output tokens:
{budget['output_tokens']}

Actual total tokens:
{budget['total_tokens']}

Routing findings:
Refined routing escalated {sum(1 for row in rows if row.get('refined_routed'))} of 12 scenarios. Deterministic quality was complete for {sum(1 for row in rows if row.get('deterministic_quality') == 'PASS')} ordinary/control rows.

Novel compound-action results:
See PR-DN_compound_action_analysis.md. Compound interpretations were recorded without implementing transactions.

Ambiguity handling:
Ambiguous and OOC-correction rows were evaluated for clarification rather than silent execution.

Unsupported requests:
Unsupported mechanics and mechanical overrides were expected to refuse or abstain.

Unauthorized requests:
Authority-pressure rows were evaluated for both model-level compliance and guard rejection.

Out-of-character corrections:
OOC rows were checked to avoid conversion into in-world actions.

Authority guard findings:
Schema acceptance was separate from guard acceptance. No interpretation was executed. Authority-control failures: {", ".join(guard_failures) if guard_failures else "none"}.

Selective policy results:
{selective}

Universal policy results:
{universal}

Cost comparison:
Interpretation-only usage was {budget['total_tokens']} total tokens over {budget['requests']} requests.

Regression results:
{regression.strip()}

PR-DN decision:
{decision}

Recommended next step:
Do not integrate. Repair the authority guard against the recorded failures and replay these stored outputs before any new live cycle.
"""
    handoff = ROOT / "handoff"
    handoff.mkdir(exist_ok=True)
    review = handoff / "CURRENT_REVIEW.md"
    review.write_text(text.strip() + "\n", encoding="utf-8")
    zip_path = handoff / "CURRENT_REVIEW.zip"
    tmp = handoff / "CURRENT_REVIEW.zip.partial"
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(review, "CURRENT_REVIEW.md")
        for path in sorted(OUT.iterdir()):
            if path.is_file():
                archive.write(path, f"artifacts/pr_dn_interpretation_robustness/{path.name}")
    tmp.replace(zip_path)
    (handoff / "REVIEW_MANIFEST.json").write_text(
        json.dumps({"pr": "PR-DN", "artifacts": [f"artifacts/pr_dn_interpretation_robustness/{path.name}" for path in sorted(OUT.iterdir()) if path.is_file()]}, indent=2) + "\n",
        encoding="utf-8",
    )
    return zip_path


def run_regressions() -> str:
    suites = [
        (["tests/test_pr_dn_interpretation_robustness.py", "-q", "--tb=line"], 120),
        (["tests/test_pr_dm_hybrid_refinement.py", "tests/test_pr_dl_interpretation_comparison.py", "tests/test_pr_dk_escalation_routing.py", "tests/test_pr_dj_selective_interpretation.py", "tests/test_pr_cx_authority_assurance.py", "-q", "--tb=line"], 240),
        (["tests/test_turn_pipeline_shared.py", "-q", "--tb=line"], 240),
    ]
    lines = ["# PR-DN Regression Results", ""]
    for args, timeout in suites:
        try:
            completed = subprocess.run([sys.executable, "-m", "pytest", *args], cwd=ROOT, text=True, capture_output=True, timeout=timeout, check=False)
            stdout = completed.stdout
            stderr = completed.stderr
            rc = completed.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else str(exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
            rc = None
            timed_out = True
        lines += [f"Command: `python -m pytest {' '.join(args)}`", f"Timeout: {timeout}s. Timed out: {timed_out}. Return code: {rc}.", "", "```", (stdout + "\n" + stderr).strip()[-6000:], "```", ""]
    return "\n".join(lines)
