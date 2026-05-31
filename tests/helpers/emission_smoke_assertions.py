"""Downstream HTTP/pipeline emission smoke assertions (Cycle AE3 / AD-4).

Narrow, explicit checks for player-facing output hygiene and repair evidence.
These helpers are for downstream consumer/smoke tests — not final-emission gate
orchestration owners.

Helper boundary (Cycle AD-4):
- Gate harness fixtures (``runner_strict_bundle``, opening GM scaffold, owner-bucket
  asserts): ``tests/helpers/final_emission_gate_fixtures.py``
- Opening fallback FEM evidence dicts: ``tests/helpers/opening_fallback_evidence.py``
- FEM read from gate output dicts: ``final_emission_gate_fixtures.final_emission_meta_from_output``
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from game.final_emission_meta import read_debug_notes_from_turn_payload

_MISSING = object()

_DEFAULT_REPAIR_TAG_MARKERS: tuple[str, ...] = (
    "final_emission_gate_replaced",
    "question_retry_fallback",
    "social_exchange_retry_fallback",
)

_DEFAULT_REPAIR_DEBUG_MARKERS: tuple[str, ...] = (
    "retry_fallback",
    "final_emission_gate",
)


def gm_response_stub(
    text: str,
    *,
    tags: Sequence[str] | None = None,
    debug_notes: str = "",
) -> dict[str, Any]:
    """Minimal fake ``call_gpt`` return dict for HTTP/pipeline integration tests."""
    return {
        "player_facing_text": text,
        "tags": list(tags or []),
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": debug_notes,
    }


def _coerce_player_text(data_or_text: Any) -> str:
    if isinstance(data_or_text, str):
        return data_or_text
    if isinstance(data_or_text, Mapping):
        gm_output = data_or_text.get("gm_output")
        if isinstance(gm_output, Mapping):
            text = gm_output.get("player_facing_text")
            if text is not None:
                return str(text)
        text = data_or_text.get("player_facing_text")
        if text is not None:
            return str(text)
    return str(data_or_text or "")


def _normalized_low(text: Any) -> str:
    return str(text or "").lower()


def assert_player_text_present(data_or_text: Any) -> str:
    """Assert emitted player-facing text is non-empty; return the text."""
    text = _coerce_player_text(data_or_text)
    assert str(text).strip(), "expected non-empty player-facing text"
    return text


def assert_global_visibility_stock_absent(text: str) -> None:
    """HTTP smoke: canonical global visibility stock must not reach player-facing chat."""
    low = _normalized_low(text)
    assert "for a breath, the scene holds" not in low


def assert_no_internal_scaffold_labels(text: str) -> None:
    """HTTP smoke: procedural planner/router/validator labels must not leak."""
    low = _normalized_low(text)
    assert "planner:" not in low
    assert "router" not in low
    assert "validator:" not in low


def assert_no_advisory_prose(text: str) -> None:
    """HTTP smoke: second-person advisory coaching must not leak."""
    low = _normalized_low(text)
    assert "i'd suggest you" not in low
    assert "you should" not in low
    assert "you could" not in low


def assert_no_unresolved_stock_phrases(text: str) -> None:
    """HTTP smoke: unresolved-answer stock phrases must not leak."""
    low = _normalized_low(text)
    assert "truth is still buried beneath rumor and rain" not in low
    assert "answer has not formed yet" not in low
    assert "from here, no certain answer presents itself" not in low


def assert_emission_repair_evidence(
    data: Mapping[str, Any],
    *,
    debug_notes_reader: Callable[[Mapping[str, Any]], str] | None = None,
    tag_markers: Sequence[str] | None = None,
    debug_markers: Sequence[str] | None = None,
) -> None:
    """HTTP smoke: replacement/repair evidence appears via tags or debug notes."""
    gm_out = data.get("gm_output") if isinstance(data.get("gm_output"), Mapping) else {}
    tags = list((gm_out or {}).get("tags") or [])
    reader = debug_notes_reader or read_debug_notes_from_turn_payload
    dbg = _normalized_low(reader(data))
    tag_set = tuple(tag_markers if tag_markers is not None else _DEFAULT_REPAIR_TAG_MARKERS)
    debug_set = tuple(debug_markers if debug_markers is not None else _DEFAULT_REPAIR_DEBUG_MARKERS)
    assert any(marker in tags for marker in tag_set) or any(marker in dbg for marker in debug_set)


def assert_response_type_meta(
    meta: Mapping[str, Any],
    *,
    required: Any = None,
    candidate_ok: Any = None,
    repair_used: Any = None,
    repair_kinds: Sequence[str] | None = None,
) -> None:
    """Smoke-check selected response-type FEM fields when provided."""
    if required is not None:
        assert meta.get("response_type_required") == required
    if candidate_ok is not None:
        assert meta.get("response_type_candidate_ok") is candidate_ok
    if repair_used is not None:
        assert meta.get("response_type_repair_used") is repair_used
    if repair_kinds is not None:
        assert meta.get("response_type_repair_kind") in set(repair_kinds)


def assert_social_grounding_smoke(
    social: Mapping[str, Any],
    *,
    expected_npc_id: str,
    expected_npc_name: str | None = None,
    expected_authority_source: str | None = None,
    expected_fallback_applied: bool = False,
    require_proposed_speaker: bool = False,
) -> None:
    """Downstream smoke: social reply remains grounded without neutral bridge fallback."""
    assert social.get("npc_id") == expected_npc_id
    if expected_npc_name is not None:
        assert social.get("npc_name") == expected_npc_name
    assert social.get("grounded_speaker_id") == expected_npc_id
    assert social.get("reply_speaker_grounding_neutral_bridge") is not True
    assert social.get("authority_source_used")
    if expected_authority_source is not None:
        assert social.get("authority_source_used") == expected_authority_source
    assert social.get("grounding_reason_code")
    if require_proposed_speaker:
        assert social.get("proposed_reply_speaker_id") == expected_npc_id
    assert social.get("grounding_fallback_applied") is expected_fallback_applied


def assert_continuity_validation_failed_without_repair(emission_debug: Mapping[str, Any]) -> None:
    """Downstream smoke: continuity violation is recorded without applying structural repair."""
    validation = emission_debug.get("interaction_continuity_validation") or {}
    assert validation.get("ok") is False
    repair = emission_debug.get("interaction_continuity_repair") or {}
    assert repair.get("applied") is not True


def assert_open_social_solicitation_route(entry: Mapping[str, Any], *, phrase: str | None = None) -> None:
    """Route-class smoke: broadcast/open-call text is classified as open social solicitation."""
    assert entry.get("should_route_social") is True
    assert entry.get("reason") == "open_social_solicitation"
    assert entry.get("open_social_solicitation") is True
    assert entry.get("broadcast_social_open_call") is True
    if phrase is not None:
        assert entry.get("broad_address_phrase_matched") == phrase


def assert_final_route_replaced_or_not_accept(meta: Mapping[str, Any]) -> None:
    """Smoke: final route is not an accept path."""
    assert meta.get("final_route") not in (None, "", "accept_candidate")


def assert_no_boundary_reorder_repair(meta: Mapping[str, Any], reason: str) -> None:
    """Smoke: boundary validate-only reason appears in rejection sample."""
    sample = meta.get("rejection_reasons_sample") or []
    assert reason in sample


def assert_response_delta_boundary_validate_only(
    out: str,
    raw: str,
    meta: Mapping[str, Any],
    extra: Sequence[str],
    *,
    reason: str = "response_delta_unsatisfied_at_boundary_no_reorder",
    repair_mode: Any | object = _MISSING,
) -> None:
    """Smoke: response-delta boundary failed without reorder repair."""
    assert out == raw
    assert meta["response_delta_repaired"] is False
    assert meta["response_delta_failed"] is True
    if repair_mode is not _MISSING:
        assert meta["response_delta_repair_mode"] is repair_mode
    assert list(extra) == [reason]
