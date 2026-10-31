"""Read-only C26 Turn 3 / Turn 4 forensic replay. Does not modify production code."""
from __future__ import annotations

import json
import re
from pathlib import Path

from game.contract_adjudication_bridge import (
    _FEASIBILITY_RE,
    _PLACE_RE,
    _PRESENCE_RE,
    _ROLL_RE,
    _STATE_RE,
    _explicit_social_address,
    derive_resolution_subject,
    select_resolver_family,
)
from game.interaction_context import _looks_like_place_existence_question
from game.interpretation_proposal import (
    _quoted_spans,
    _strong_addressed_ask,
    fast_path_operation_families,
)
from game.ordinary_semantic_ownership import select_ordinary_resolver
from game.player_commitment import EXECUTED_NOW, commitment_status
from game.resolution_contract import _clean, construct_resolution_contract

ROOT = Path(__file__).resolve().parents[2]
TURNS = ROOT / "artifacts" / "pr_br_continuation26" / "live" / "20261003T134953Z" / "turns.json"
OUT = Path(__file__).resolve().parent / "forensic_pre_change.json"


def _clauses(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part for part in parts if part.strip()]


def _trace_subject(text: str, operation: str, proposed: str, commitment: str) -> dict:
    raw = str(text or "")
    steps = []
    social = _explicit_social_address(raw)
    steps.append({"check": "explicit_social_address", "matched": social})
    if social:
        chosen = "social"
        reason = "explicit_social_address"
    else:
        uncommitted = commitment != EXECUTED_NOW and "?" not in raw
        steps.append({"check": "uncommitted_non_question", "matched": uncommitted, "commitment": commitment})
        place = bool(_PLACE_RE.search(raw))
        existence = _looks_like_place_existence_question(raw)
        steps.append(
            {
                "check": "place_vocabulary_or_existence",
                "place_re": place,
                "place_match": _PLACE_RE.search(raw).group(0) if _PLACE_RE.search(raw) else None,
                "existence_question": existence,
                "operation_is_ask": operation == "ask",
            }
        )
        chosen = derive_resolution_subject(
            raw,
            operation=operation,
            proposed_operation=proposed,
            commitment=commitment,
        )
        if operation == "ask" and (place or existence) and not social:
            reason = "topic_place_vocabulary_outranks_unmatched_social_frame"
        else:
            reason = "derive_resolution_subject"
    return {
        "derived": chosen,
        "reason": reason,
        "steps": steps,
        "strong_addressed_ask": _strong_addressed_ask(raw),
        "quoted_spans": _quoted_spans(raw),
        "families": list(fast_path_operation_families(raw)),
        "presence": bool(_PRESENCE_RE.search(raw)),
        "roll": bool(_ROLL_RE.search(raw)),
        "state": bool(_STATE_RE.search(raw)),
        "feasibility": bool(_FEASIBILITY_RE.search(raw)),
    }


def _replay(label: str, raw: str, interpreter=None) -> dict:
    full = " ".join(raw.split())
    truncated = _clean(raw, limit=240)
    contract = construct_resolution_contract(player_text=raw, model_interpreter=interpreter).as_dict()
    construction = contract["construction"]
    operation = str(contract["operation"])
    commitment = str(construction.get("commitment_status") or "")
    proposed = str(construction.get("proposed_operation") or "")
    resolver, family = select_ordinary_resolver(contract)
    full_subject = _trace_subject(full, operation, proposed, commitment)
    trunc_subject = _trace_subject(truncated, operation, proposed, commitment_status(truncated))
    boundary = 240
    return {
        "label": label,
        "full_length": len(full),
        "raw": full,
        "truncated_length": len(truncated),
        "truncated": truncated,
        "truncation_boundary": boundary if len(full) > boundary else None,
        "dropped_suffix": full[len(truncated):] if full.startswith(truncated) else None,
        "clauses_full": _clauses(full),
        "clauses_truncated": _clauses(truncated),
        "operation": operation,
        "commitment": commitment,
        "proposed_operation": proposed,
        "resolution_subject": construction.get("resolution_subject"),
        "interlocutor_id": contract.get("interlocutor_id"),
        "target_ref": contract.get("target_ref"),
        "raw_input_stored": contract.get("raw_input"),
        "raw_input_length": len(str(contract.get("raw_input") or "")),
        "validation_status": construction.get("validation_status"),
        "proposal_source": construction.get("proposal_source"),
        "model_interpreter_invoked": construction.get("model_interpreter_invoked"),
        "selected_resolver": resolver,
        "resolver_family": family,
        "select_resolver_family": select_resolver_family(contract),
        "subject_on_truncated_semantic_input": trunc_subject,
        "subject_if_full_text_were_used_with_same_operation": full_subject,
    }


def main() -> None:
    turns = json.loads(TURNS.read_text(encoding="utf-8"))
    by_turn = {row["turn"]: row["raw_player_input"] for row in turns}

    def stub_inspect(_payload):
        return {
            "status": "proposed",
            "api_calls": 0,
            "proposal": {"primary_operation": "inspect", "dimension": "content"},
        }

    report = {
        "turn_3_deterministic": _replay("c26_turn_3", by_turn[3]),
        "turn_4_deterministic": _replay("c26_turn_4", by_turn[4]),
        "turn_4_stubbed_inspect_proposal": _replay("c26_turn_4_stub_inspect", by_turn[4], stub_inspect),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(OUT)
    for key, row in report.items():
        print(
            key,
            "len",
            row["full_length"],
            "stored",
            row["raw_input_length"],
            "op",
            row["operation"],
            "subject",
            row["resolution_subject"],
            "resolver",
            row["selected_resolver"],
            row["resolver_family"],
            "dropped",
            repr((row["dropped_suffix"] or "")[:80]),
        )


if __name__ == "__main__":
    main()
