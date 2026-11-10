"""Offline replay of the PR-PLAY-35 opening against the semantic validator.

Reads the captured provider response and the isolated baseline store.
Does not call a provider and does not write campaign state.
ASHEN_DATA_DIR must already point at a disposable copy of that baseline.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "artifacts"
    / "atgb"
    / "pr_play_35"
    / "live"
    / "20261102T011549Z-bd0c88693cd0"
    / "opening_response_evidence"
    / "e97b9ce72d9b494db77178582be66ceb-1.json"
)
OUT = ROOT / "artifacts" / "pr_play_36" / "replay_audit.json"


def _shrink(value, limit: int = 500):
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + "…"
    if isinstance(value, dict):
        return {str(k): _shrink(v, limit) for k, v in value.items()}
    if isinstance(value, list):
        return [_shrink(item, limit) for item in value]
    return value


def main() -> None:
    data_dir = os.environ.get("ASHEN_DATA_DIR")
    if not data_dir:
        raise SystemExit("ASHEN_DATA_DIR is required and must be a disposable copy")
    if Path(data_dir).resolve() == (ROOT / "data").resolve():
        raise SystemExit("refusing to run against the user campaign data directory")

    captured = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    parsed = captured["parsed_response"]
    declared = parsed["declared_claims"]
    narration = parsed["narration"]

    from game.api import _opening_scene_normalized_action_and_resolution
    from game.clocks import advance_clock, get_or_init_clocks
    from game.gm_resolution_decision import (
        _CONSEQUENTIAL_PATTERNS,
        _SENTENCE_RE,
        _proposition_restates_statement,
        _sentences,
        _token_set,
        _unlicensed_consequential_reasons,
        audit_realization_envelope_against_decision,
        decision_from_resolution,
    )
    from game.immutable_valid_response import validate_generated_response
    from game.interaction_context import synchronize_scene_addressability
    from game.live_resolution import attach_interaction_obligation
    from game.storage import load_active_scene, load_campaign, load_session, load_world
    from game.world import advance_world_tick

    session = load_session()
    world = load_world()
    scene = load_active_scene()
    campaign = load_campaign()
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    session["turn_counter"] = int(session.get("turn_counter") or 0) + 1
    tick = advance_world_tick(world, campaign)
    get_or_init_clocks(session)
    advance_clock(session, "time_pressure", 1)

    normalized, resolution = _opening_scene_normalized_action_and_resolution(
        scene=scene,
        player_text=None,
        internal_bootstrap=True,
    )
    attach_interaction_obligation(
        resolution,
        player_text=resolution.get("prompt") or "",
        session=session,
        normalized_action=normalized,
        scene_id=str(scene["scene"]["id"]),
        scene=scene,
        world=world,
        visible_turns=[],
        enable_model_interpretation=False,
    )
    decision = decision_from_resolution(resolution)
    claims = [row for row in (decision.get("realization_claims") or []) if isinstance(row, dict)]
    by_id = {str(row.get("claim_id") or ""): row for row in claims}

    cited = []
    for item in declared:
        source_id = str(item.get("source_claim_id") or "")
        match = by_id.get(source_id)
        cited.append(
            {
                "declaration_id": item.get("declaration_id"),
                "source_claim_id": source_id,
                "declared_text": item.get("text"),
                "claim_id_present": match is not None,
                "authorized_text": None if match is None else match.get("text"),
                "texts_equal": None if match is None else match.get("text") == item.get("text"),
                "authorized_source_ref": None if match is None else match.get("source_ref"),
                "authorized_provenance": None if match is None else match.get("provenance"),
                "authorized_role": None if match is None else match.get("realization_role"),
            }
        )

    audit_a = audit_realization_envelope_against_decision(
        narration=narration,
        declared_claims=declared,
        decision=decision,
        authored_corpus="",
    )
    audit_b = audit_realization_envelope_against_decision(
        narration=narration,
        declared_claims=declared,
        decision=decision,
        authored_corpus="",
    )

    from game.immutable_valid_response import _authored_corpus as response_corpus

    corpus = response_corpus(scene)
    verdict_a = validate_generated_response(
        narration,
        decision=decision,
        declared_claims=declared,
        player_text="",
        resolution=resolution,
        authored_corpus=corpus,
    )
    verdict_b = validate_generated_response(
        narration,
        decision=decision,
        declared_claims=declared,
        player_text="",
        resolution=resolution,
        authored_corpus=corpus,
    )

    sentence_rows = []
    for sentence in _sentences(narration):
        pattern_hits = [code for code, pattern in _CONSEQUENTIAL_PATTERNS if pattern.search(sentence)]
        restatements = []
        for row in decision.get("proposed_facts") or []:
            if not isinstance(row, dict) or not row.get("authorized"):
                continue
            statement = str(row.get("text") or "")
            if statement and _proposition_restates_statement(sentence, statement):
                restatements.append(
                    {
                        "source_ref": row.get("source_ref"),
                        "text": statement,
                        "sentence_tokens": sorted(_token_set(sentence)),
                        "statement_tokens": sorted(_token_set(statement)),
                    }
                )
        sentence_rows.append(
            {
                "text": sentence,
                "consequential_pattern_hits": pattern_hits,
                "unlicensed_consequential_reasons": _unlicensed_consequential_reasons(sentence, decision),
                "restates_authorized_statements": restatements,
            }
        )

    declaration = audit_a.get("declaration_validation") or {}
    report = {
        "data_dir": str(Path(data_dir).resolve()),
        "opening_attempt_id": captured.get("opening_attempt_id"),
        "provider_attempt_id": captured.get("provider_attempt_id"),
        "narration": narration,
        "narration_length": len(narration),
        "declaration_count": len(declared),
        "decision_contract_id": decision.get("contract_id"),
        "decision_resolution_method": decision.get("resolution_method"),
        "decision_outcome": decision.get("outcome_classification"),
        "decision_fact_count": len(decision.get("proposed_facts") or []),
        "decision_claim_count": len(claims),
        "world_tick_event_count": len((tick or {}).get("events") or []),
        "cited_claims": cited,
        "unmatched_source_claim_ids": [row["source_claim_id"] for row in cited if not row["claim_id_present"]],
        "declaration_hard_valid": declaration.get("hard_valid"),
        "declaration_rejected": _shrink(declaration.get("rejected_claims") or []),
        "declaration_violations": _shrink(declaration.get("violations") or []),
        "audit_hard_valid": audit_a.get("hard_valid"),
        "audit_deterministic": audit_a == audit_b,
        "audit_violations": _shrink(audit_a.get("violations") or []),
        "narration_hard_valid": (audit_a.get("narration_validation") or {}).get("hard_valid"),
        "sentences": sentence_rows,
        "validate_generated_response": {
            "hard_valid": verdict_a.get("hard_valid"),
            "reasons": verdict_a.get("reasons"),
            "deterministic": (
                verdict_a.get("hard_valid") == verdict_b.get("hard_valid")
                and verdict_a.get("reasons") == verdict_b.get("reasons")
            ),
            "audit_hard_valid": (verdict_a.get("gm_resolution_decision_audit") or {}).get("hard_valid"),
        },
        "model_interpretation": False,
        "provider_requests": 0,
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "audit_hard_valid": report["audit_hard_valid"],
                "declaration_hard_valid": report["declaration_hard_valid"],
                "narration_hard_valid": report["narration_hard_valid"],
                "unmatched_source_claim_ids": report["unmatched_source_claim_ids"],
                "reasons": report["validate_generated_response"]["reasons"],
                "violation_count": len(report["audit_violations"]),
                "deterministic": report["audit_deterministic"],
                "out": str(OUT),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
