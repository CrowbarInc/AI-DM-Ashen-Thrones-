"""Downstream HTTP/pipeline emission smoke facade (Cycle AE3 / AD-4, AL2–AL4).

This module is the **intended downstream assertion surface** for integration and smoke
suites. Helpers here are **intentionally weaker** than owner legality tests — they prove
wiring, hygiene, and coarse repair evidence only.

What belongs here (downstream smoke):
- Non-empty player-facing text and obvious leakage bans (subset tuples, not full matrices)
- Repair/replacement evidence via tags or debug notes
- Consumer-layer meta smoke (``response_type_*``, continuity validate-only)
- Route **wiring** smoke (``final_route`` present / accept vs non-accept) — not gate route tables
- Broadcast / open-call routing smoke (``assert_open_social_solicitation_route``,
  ``assert_broadcast_open_call_rejected_smoke``, open-call retry exemption helpers)

What stays in owner suites (do not restate here):
- **Phrase legality matrices** → ``tests/test_output_sanitizer.py`` (procedural/scaffold),
  ``tests/test_social_exchange_emission.py`` (strict-social / source semantics),
  ``tests/test_final_emission_visibility.py`` (global visibility stock)
- **Final-route legality / enum tables** → ``tests/test_final_emission_gate.py`` (orchestration),
  ``tests/test_final_emission_meta.py`` (FEM projection / lineage),
  ``tests/test_dialogue_routing_lock.py`` (``choose_interaction_route`` classification table)

Intentionally separate (do not merge into this facade):
- Gate harness fixtures and owner-bucket asserts:
  ``tests/helpers/final_emission_gate_fixtures.py``
- Opening fallback FEM evidence dicts: ``tests/helpers/opening_fallback_evidence.py``
- Golden replay / classifier FEM bucket projection:
  ``tests/helpers/golden_replay_projection.py``, ``tests/helpers/failure_classifier.py``
- FEM read from gate output dicts:
  ``final_emission_gate_fixtures.final_emission_meta_from_output``

Registry reference: ``tests/test_ownership_registry.py`` (Cycle AL4 quick reference).
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

# Downstream smoke phrase tuples (subset of owner matrices — wiring/hygiene only).
SMOKE_PROCEDURAL_ADJUDICATION_PHRASES: tuple[str, ...] = (
    "resolve that procedurally",
    "state exactly what you do",
    "scene offers no clear answer yet",
    "adjudication:",
    "authoritative state",
)
SMOKE_VALIDATOR_VOICE_PHRASES: tuple[str, ...] = (
    "based on what's established",
    "we can determine",
    "i can't answer",
    "as an ai",
)
SMOKE_RETRY_COACHING_LEAK_PHRASES: tuple[str, ...] = (
    "answer the player",
    "rule priority",
)
SMOKE_SOCIAL_VISIBLE_INTRO_FILLER_PHRASES: tuple[str, ...] = ("stands nearby",)
SMOKE_UNCERTAINTY_FALLBACK_STOCK_PHRASES: tuple[str, ...] = ("blank scene awaiting definition",)

# Synthetic fake-GM follow-up hygiene (regex, word-bounded). Harness leaks stay here only.
SMOKE_SYNTHETIC_INTERNAL_LEAK_PATTERNS: tuple[str, ...] = (
    r"\brouter\b",
    r"\bplanner\b",
    r"\bvalidator\b",
    r"\bdecision_rationale\b",
    r"\bpolicy\b",
    r"\bsystem prompt\b",
    r"\bdebug_notes?\b",
    r"\bchain[- ]of[- ]thought\b",
)
SMOKE_SYNTHETIC_SCAFFOLD_LEAK_PATTERNS: tuple[str, ...] = (
    r"\bstate exactly what you do\b",
    r"\bstate the specific action\b",
    r"\bresolve that procedurally\b",
    r"\bcannot determine roll requirements\b",
    r"\bbased on (?:what'?s|what is) established\b",
    r"\bas an ai\b",
    r"\bi can't answer\b",
    r"\bi cannot answer\b",
)
SMOKE_SYNTHETIC_VAGUE_FILLER_PATTERNS: tuple[str, ...] = (
    r"\bfor a breath\b",
    r"\bthe scene holds\b",
    r"\bvoices shift around you\b",
    r"\bthese are dangerous times\b",
    r"\btrust is hard to come by\b",
)


def _assert_phrases_absent(text: str, phrases: Sequence[str], *, label: str) -> None:
    low = _normalized_low(text)
    for phrase in phrases:
        assert phrase not in low, f"{label}: unexpected player-facing phrase {phrase!r}"


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
    _assert_phrases_absent(
        text,
        ("for a breath, the scene holds",),
        label="global visibility stock",
    )


def assert_procedural_adjudication_smoke(text: str) -> None:
    """HTTP smoke: procedural/adjudication coaching must not leak to player-facing chat."""
    _assert_phrases_absent(
        text,
        SMOKE_PROCEDURAL_ADJUDICATION_PHRASES,
        label="procedural adjudication",
    )


def assert_no_validator_voice_smoke(text: str) -> None:
    """HTTP smoke: validator-voice stock must not reach player-facing chat after retry/repair."""
    _assert_phrases_absent(
        text,
        SMOKE_VALIDATOR_VOICE_PHRASES,
        label="validator voice",
    )


def assert_no_retry_coaching_leak_smoke(text: str) -> None:
    """HTTP smoke: retry-prompt coaching phrases must not leak into emitted player text."""
    _assert_phrases_absent(
        text,
        SMOKE_RETRY_COACHING_LEAK_PHRASES,
        label="retry coaching",
    )


def assert_no_social_visible_intro_filler_smoke(text: str) -> None:
    """HTTP smoke: generic NPC presence filler must not beat dialogue lock output."""
    _assert_phrases_absent(
        text,
        SMOKE_SOCIAL_VISIBLE_INTRO_FILLER_PHRASES,
        label="social visible-intro filler",
    )


def assert_no_uncertainty_fallback_stock_smoke(text: str) -> None:
    """HTTP smoke: blank-scene uncertainty fallback stock must not reach player-facing chat."""
    _assert_phrases_absent(
        text,
        SMOKE_UNCERTAINTY_FALLBACK_STOCK_PHRASES,
        label="uncertainty fallback stock",
    )


def assert_no_internal_scaffold_labels(text: str) -> None:
    """HTTP smoke: procedural planner/router/validator labels must not leak."""
    _assert_phrases_absent(
        text,
        ("planner:", "router", "validator:"),
        label="internal scaffold labels",
    )


def assert_no_advisory_prose(text: str) -> None:
    """HTTP smoke: second-person advisory coaching must not leak."""
    _assert_phrases_absent(
        text,
        ("i'd suggest you", "you should", "you could"),
        label="advisory prose",
    )


def assert_no_unresolved_stock_phrases(text: str) -> None:
    """HTTP smoke: unresolved-answer stock phrases must not leak."""
    _assert_phrases_absent(
        text,
        (
            "truth is still buried beneath rumor and rain",
            "answer has not formed yet",
            "from here, no certain answer presents itself",
        ),
        label="unresolved stock",
    )


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


def assert_open_social_solicitation_route(
    entry: Mapping[str, Any],
    *,
    phrase: str | None = None,
    require_broadcast_open_call: bool = True,
) -> None:
    """Route-class smoke: broadcast/open-call text is classified as open social solicitation."""
    assert entry.get("should_route_social") is True
    assert entry.get("reason") == "open_social_solicitation"
    assert entry.get("open_social_solicitation") is True
    if require_broadcast_open_call:
        assert entry.get("broadcast_social_open_call") is True
    if phrase is not None:
        assert entry.get("broad_address_phrase_matched") == phrase


def assert_broadcast_open_call_rejected_smoke(
    detector_result: Mapping[str, Any],
    *,
    reason: str | None = None,
) -> None:
    """Smoke: line is not classified as broadcast open-call (negative detector wiring)."""
    assert detector_result.get("is_broadcast_open_call") is False
    if reason is not None:
        assert detector_result.get("reason") == reason


def assert_open_call_crowd_reaction_wiring_smoke(question_check: Mapping[str, Any]) -> None:
    """Smoke: open-call crowd reactions skip strict question-resolution application."""
    assert question_check.get("applies") is False
    assert question_check.get("ok") is True


def assert_open_call_no_unresolved_retry_smoke(retry_failures: Sequence[Any]) -> None:
    """Smoke: open-call turns do not enqueue ``unresolved_question`` retry class."""
    assert not any(
        isinstance(f, Mapping) and f.get("failure_class") == "unresolved_question"
        for f in retry_failures
    )


def assert_final_route_present_smoke(meta: Mapping[str, Any]) -> None:
    """Smoke: ``final_route`` is present on FEM (wiring only)."""
    route = meta.get("final_route")
    assert route not in (None, ""), "expected final_route on final emission meta"


def assert_final_route_accept_candidate_smoke(meta: Mapping[str, Any]) -> None:
    """Smoke: gate took the accept-candidate path (not a full route-table owner check)."""
    assert meta.get("final_route") == "accept_candidate"


def assert_final_route_not_replaced_smoke(meta: Mapping[str, Any]) -> None:
    """Smoke: gate did not route through replacement (e.g. continuity validate-only)."""
    assert meta.get("final_route") != "replaced"


def assert_final_route_replaced_or_not_accept(meta: Mapping[str, Any]) -> None:
    """Smoke: final route is not an accept path (replacement or other non-accept wiring)."""
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
