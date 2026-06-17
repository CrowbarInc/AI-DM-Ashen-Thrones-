"""Downstream HTTP/pipeline emission smoke facade (Cycle AE3 / AD-4, AL2–AL4).

This module is the **intended downstream assertion surface** for integration and smoke
suites. Helpers here are **intentionally weaker** than owner legality tests — they prove
wiring, hygiene, and coarse repair evidence only.

What belongs here (downstream smoke):
- Non-empty player-facing text and obvious leakage bans (subset tuples, not full matrices)
- Repair/replacement evidence via tags or debug notes
- Consumer-layer meta smoke (``response_type_*``, continuity validate-only)
- Route **wiring** smoke (``final_route`` present / accept vs non-accept; dialogue-lock HTTP
  sentinels via ``assert_dialogue_lock_*``) — not ``choose_interaction_route`` tables
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
- Opening fallback scaffolds / owner-bucket asserts: ``tests/helpers/opening_fallback_evidence.py``
- Strict-social harness bundle: ``tests/helpers/strict_social_harness.py``
- Opening attach-then gate harness: ``tests/helpers/opening_fallback_gate_harness.py``
- Golden replay / classifier FEM bucket projection:
  ``tests/helpers/golden_replay_projection.py``, ``tests/helpers/failure_classifier.py``

Cycle BE6 — triple-layer scaffold / phrase split (**do not merge into one shared matrix**):

1. **Sanitizer legality owner** — ``tests/test_output_sanitizer.py`` owns the full
   procedural/scaffold/validator phrase **legality matrices** (post-process cleanup rules).
2. **HTTP smoke facade (this module)** — owns **weak** downstream phrase tuples only
   (``SMOKE_*_PHRASES``, ``assert_*_smoke`` helpers) for ``/api/chat`` / pipeline wiring.
3. **Replay scaffold projection** — ``tests/helpers/golden_replay_projection.py`` owns
   golden-replay **observation** of scaffold leakage (``final_text_has_scaffold_leakage``,
   protected ``scaffold_leakage`` path) — diagnostic drift, not HTTP smoke.

Future assertion-economy work must **not** collapse these layers into a single shared
phrase list or helper. Overlap in banned *words* is intentional; each layer guards a
different failure surface (legality vs integration smoke vs protected replay drift).

Registry lock: ``tests/test_ownership_registry.py`` (``test_be6_scaffold_phrase_triple_layer_split_locked``).

Cycle AS2 — downstream consumer suites should import gate integration and owned layer
seams from this module instead of ``game.final_emission_gate`` / ``read_final_emission_meta_dict``.

Cycle AS4 — downstream HTTP/pipeline/transcript smoke should use ``final_emission_meta_from_output``
and ``read_turn_debug_notes`` here; golden-replay FEM reads use ``golden_replay_projection``.

Registry reference: ``tests/test_ownership_registry.py`` (Cycle AL4 quick reference).

Normal full-emission consumer execution delegates through ``game.final_emission_runtime``.
Private layer seams below delegate to their narrower validator/repair owners while
keeping this downstream facade stable.

Ownership note: this facade provides weak downstream smoke/consumer bridges. It
must not become the owner of full gate legality matrices, route enum tables,
sanitizer phrase legality, or AC/RD repair semantics.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from game.final_emission_meta import read_debug_notes_from_turn_payload, read_final_emission_meta_dict

_MISSING = object()


# Core smoke helpers

def response_type_contract(required: str) -> dict:
    """Minimal response-type contract scaffold for downstream smoke and integration tests."""
    return {
        "required_response_type": required,
        "action_must_preserve_agency": required == "action_outcome",
    }


# FEM/read-side consumer bridge

def final_emission_meta_from_output(gm_output: Mapping[str, Any]) -> dict[str, Any]:
    """Read normalized FEM from a gate output dict (downstream wiring smoke)."""
    return read_final_emission_meta_dict(dict(gm_output)) or {}


def read_turn_debug_notes(payload: Mapping[str, Any]) -> str:
    """Read turn-packet debug notes (downstream HTTP/pipeline wiring smoke)."""
    return read_debug_notes_from_turn_payload(payload)


STRICT_SOCIAL_EMISSION_WILL_APPLY_PATCH = "game.social_exchange_emission.strict_social_emission_will_apply"


# Final emission gate consumer bridge

def apply_final_emission_gate_consumer(
    gm_output: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    scene_id: str = "",
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run full gate orchestration for downstream consumer integration tests; return (output, fem)."""
    from game.final_emission_runtime import finalize_player_facing_emission

    out = finalize_player_facing_emission(
        dict(gm_output),
        resolution=dict(resolution) if isinstance(resolution, Mapping) else resolution,
        session=dict(session) if isinstance(session, Mapping) else session,
        scene_id=scene_id,
        scene=dict(scene) if isinstance(scene, Mapping) else scene,
        world=dict(world) if isinstance(world, Mapping) else world,
    )
    return out, final_emission_meta_from_output(out)


# AC/RD owner-adjacent repair bridges

def validate_answer_completeness(text: str, contract: Mapping[str, Any], *, resolution: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Consumer-owned answer-completeness validator seam (delegates to validator owner)."""
    from game.final_emission_validators import validate_answer_completeness as _fn

    return _fn(text, dict(contract), resolution=dict(resolution) if isinstance(resolution, Mapping) else resolution)


def apply_answer_completeness_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    """Consumer-owned answer-completeness layer seam (delegates to repair owner)."""
    from game.final_emission_repairs import _apply_answer_completeness_layer as _fn

    return _fn(*args, **kwargs)


def apply_response_delta_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any], list[str]]:
    """Consumer-owned response-delta layer seam (delegates to repair owner)."""
    from game.final_emission_repairs import _apply_response_delta_layer as _fn

    return _fn(*args, **kwargs)


def enforce_response_type_contract_layer(*args: Any, **kwargs: Any) -> tuple[str, dict[str, Any]]:
    """Consumer-owned response-type enforcement seam (delegates to response_type owner)."""
    from game.final_emission_response_type import enforce_response_type_contract as _fn

    return _fn(*args, **kwargs)


def skip_answer_completeness_layer(*args: Any, **kwargs: Any) -> bool:
    from game.final_emission_repairs import _skip_answer_completeness_layer as _fn

    return _fn(*args, **kwargs)


def skip_response_delta_layer(*args: Any, **kwargs: Any) -> bool:
    from game.final_emission_repairs import _skip_response_delta_layer as _fn

    return _fn(*args, **kwargs)


def strict_social_answer_pressure_rd_contract_active(gm_output: Mapping[str, Any]) -> bool:
    from game.final_emission_repairs import _strict_social_answer_pressure_rd_contract_active as _fn

    return _fn(dict(gm_output))


def validate_response_delta(emitted: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    from game.final_emission_validators import validate_response_delta as _fn

    return _fn(emitted, dict(contract))


def inspect_response_delta_failure(result: Mapping[str, Any]) -> dict[str, Any]:
    from game.final_emission_validators import inspect_response_delta_failure as _fn

    return _fn(dict(result))


# Core smoke helpers

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


# HTTP fixture compatibility helpers

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


# Core smoke helpers

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


_DIALOGUE_LOCK_SOCIAL_KINDS: tuple[str, ...] = ("question", "social_probe")


# Core smoke helpers

def assert_http_chat_response_smoke(data: Mapping[str, Any]) -> str:
    """HTTP smoke: ``/api/chat`` returned ok with non-empty player-facing text."""
    assert data.get("ok") is True, "expected chat response ok=True"
    return assert_player_text_present(data)


# Route smoke helpers

def assert_dialogue_lock_social_route_smoke(
    resolution: Mapping[str, Any],
    *,
    npc_id: str = "runner",
    allowed_kinds: Sequence[str] = _DIALOGUE_LOCK_SOCIAL_KINDS,
) -> None:
    """HTTP smoke: dialogue-lock turn reached active-target social exchange wiring."""
    kind = resolution.get("kind")
    allowed = set(allowed_kinds)
    assert kind in allowed, (
        f"expected resolution.kind in {sorted(allowed)!r}, got {kind!r}"
    )
    social = resolution.get("social") or {}
    assert social.get("social_intent_class") == "social_exchange", (
        "expected social_intent_class='social_exchange' "
        f"got {social.get('social_intent_class')!r}"
    )
    assert social.get("npc_id") == npc_id, (
        f"expected social.npc_id={npc_id!r}, got {social.get('npc_id')!r}"
    )


def assert_dialogue_lock_non_dialogue_route_smoke(resolution: Mapping[str, Any]) -> None:
    """HTTP smoke: world-action turn did not remain on dialogue or adjudication lanes."""
    kind = resolution.get("kind")
    forbidden = {"question", "social_probe", "adjudication_query"}
    assert kind not in forbidden, (
        f"expected world-action resolution.kind outside {sorted(forbidden)!r}, got {kind!r}"
    )


def assert_response_type_contract_surfaces(
    *,
    required: str,
    debug: Mapping[str, Any] | None = None,
    trace: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
) -> None:
    """HTTP smoke: ``response_type_contract`` threaded through named debug surfaces."""
    for surface_name, contract in (
        ("debug", debug),
        ("trace", trace),
        ("resolution", resolution),
    ):
        if contract is None:
            continue
        actual = contract.get("required_response_type")
        assert actual == required, (
            f"{surface_name} response_type_contract.required_response_type: "
            f"expected {required!r}, got {actual!r}"
        )


# Social/open-call smoke helpers

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


# Social/open-call smoke helpers

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


# Route smoke helpers

def assert_final_route_present_smoke(meta: Mapping[str, Any]) -> None:
    """Smoke: ``final_route`` is present on FEM (wiring only)."""
    route = meta.get("final_route")
    assert route not in (None, ""), "expected final_route on final emission meta"


def assert_final_route_accept_candidate_smoke(meta: Mapping[str, Any]) -> None:
    """Smoke: gate took the accept-candidate path (not a full route-table owner check)."""
    route = meta.get("final_route")
    assert route == "accept_candidate", f"expected accept-candidate final_route smoke, got {route!r}"


def assert_final_route_not_replaced_smoke(meta: Mapping[str, Any]) -> None:
    """Smoke: gate did not route through replacement (e.g. continuity validate-only)."""
    route = meta.get("final_route")
    assert route != "replaced", f"expected non-replacement final_route smoke, got {route!r}"


def has_non_accept_final_route_smoke(meta: Mapping[str, Any]) -> bool:
    """Predicate companion for composite downstream smoke conditions."""
    return meta.get("final_route") not in (None, "", "accept_candidate")


def assert_final_route_replaced_or_not_accept(meta: Mapping[str, Any]) -> None:
    """Smoke: final route is not an accept path (replacement or other non-accept wiring)."""
    route = meta.get("final_route")
    assert has_non_accept_final_route_smoke(meta), f"expected non-accept final_route smoke, got {route!r}"


def assert_no_boundary_reorder_repair(meta: Mapping[str, Any], reason: str) -> None:
    """Smoke: boundary validate-only reason appears in rejection sample."""
    sample = meta.get("rejection_reasons_sample") or []
    assert reason in sample


# AC/RD owner-adjacent repair bridges

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
