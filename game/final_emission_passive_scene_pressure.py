"""Passive scene pressure visibility fallback helpers.

Due-check and candidate-building for passive-action streak pressure beats.
Does not own fallback ordering inside gate visibility routing.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Tuple

from game.final_emission_text_formatting import _normalize_text
from game.final_emission_visibility_fallback import (
    VisibilitySelectedFallback,
    first_mention_composition_meta as _first_mention_composition_meta,
)
from game.storage import get_scene_runtime

_CONCRETE_INTERACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile("[\"“”'‘’]"),
    re.compile(
        r"\b(?:approach(?:es|ed)?|step(?:s|ped)?\s+(?:toward|forward|out)|comes?\s+(?:straight\s+)?to|cuts?\s+across|"
        r"blocks?|halts?|stops?\s+at|squares?\s+up|hails?|calls?\s+out|speaks?\s+first|says?|asks?|mutters?|warns?|"
        r"orders?|interrupts?|thrusts?|hands?|points?)\b",
        re.IGNORECASE,
    ),
)

_BEAT_TYPE_BY_FALLBACK_KIND: dict[str, str] = {
    "passive_scene_pressure_lead_figure": "observer_interruption",
    "passive_scene_pressure_guard_rumor": "guard_reaction",
    "passive_scene_pressure_visible_figure": "guard_reaction",
    "passive_scene_pressure_generic": "generic_interruption",
}


def reply_has_concrete_interaction(text: str) -> bool:
    """True when *text* satisfies the passive-scene concrete interaction beat contract."""
    return _reply_already_has_concrete_interaction(text)


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scene_inner(scene: Dict[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene, dict):
        return {}
    inner = scene.get("scene")
    if isinstance(inner, dict):
        return inner
    return scene


def _output_sentence(text: str) -> str:
    clean = _normalize_text(text)
    if not clean:
        return ""
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def _scene_visible_facts(scene: Dict[str, Any] | None) -> List[str]:
    inner = _scene_inner(scene)
    raw = inner.get("visible_facts")
    if not isinstance(raw, list):
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        clean = _output_sentence(item)
        if clean:
            out.append(clean)
    return _dedupe_preserve_order(out)


def _passive_scene_pressure_due_for_fallback(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> bool:
    if not isinstance(session, dict):
        return False
    sid = str(scene_id or "").strip()
    if not sid:
        return False
    runtime = get_scene_runtime(session, sid)
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    last_player_action_passive = bool(runtime.get("last_player_action_passive")) if isinstance(runtime, dict) else False
    if not last_player_action_passive and passive_streak <= 0:
        return False
    visible_low = " ".join(fact.lower() for fact in _scene_visible_facts(scene))
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    return bool(
        passive_streak >= 2
        or isinstance(recent, list)
        and any(isinstance(item, dict) for item in recent)
        or "guard" in visible_low
        or "watch" in visible_low
        or "missing patrol" in visible_low
        or "rumor" in visible_low
        or "rumour" in visible_low
    )


def _reply_already_has_concrete_interaction(text: str) -> bool:
    clean = str(text or "").strip()
    if not clean:
        return False
    return any(pattern.search(clean) for pattern in _CONCRETE_INTERACTION_PATTERNS)


def _passive_scene_pressure_visibility_candidate(
    text: str,
    *,
    fallback_kind: str,
    fallback_candidate_source: str,
) -> VisibilitySelectedFallback:
    """Build one passive-scene-pressure visibility fallback candidate (canonical dataclass wire)."""
    return VisibilitySelectedFallback(
        text=_output_sentence(text),
        fallback_pool="passive_scene_pressure",
        fallback_kind=fallback_kind,
        final_emitted_source="passive_scene_pressure_fallback",
        fallback_strategy="passive_scene_pressure_fallback",
        fallback_candidate_source=fallback_candidate_source,
        composition_meta=_first_mention_composition_meta(),
    )


def _passive_scene_pressure_fallback_candidates(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> List[VisibilitySelectedFallback]:
    if not _passive_scene_pressure_due_for_fallback(session=session, scene=scene, scene_id=scene_id):
        return []

    sid = str(scene_id or "").strip()
    runtime = get_scene_runtime(session, sid) if isinstance(session, dict) and sid else {}
    passive_streak = int(runtime.get("passive_action_streak", 0) or 0) if isinstance(runtime, dict) else 0
    recent = runtime.get("recent_contextual_leads") if isinstance(runtime, dict) else []
    if isinstance(recent, list):
        for lead in reversed(recent[-4:]):
            if not isinstance(lead, dict):
                continue
            kind = str(lead.get("kind") or "").strip()
            if kind not in {"visible_suspicious_figure", "recent_named_figure", "visible_named_figure"}:
                continue
            subject = _normalize_text(lead.get("subject"))
            position = _normalize_text(lead.get("position"))
            if not subject:
                continue
            move_from = f" leaves {position} and" if position else ""
            if passive_streak >= 2:
                return [
                    _passive_scene_pressure_visibility_candidate(
                        f'{subject}{move_from} comes straight to you before the pause can settle. "Enough watching," they say. "Ask me now, or lose the trail."',
                        fallback_kind="passive_scene_pressure_lead_figure",
                        fallback_candidate_source="passive_scene_pressure:lead_figure",
                    )
                ]
            return [
                _passive_scene_pressure_visibility_candidate(
                    f'{subject}{move_from} cuts through the crowd and stops at your shoulder. "You\'re asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."',
                    fallback_kind="passive_scene_pressure_lead_figure",
                    fallback_candidate_source="passive_scene_pressure:lead_figure",
                )
            ]

    visible_facts = _scene_visible_facts(scene)
    visible_low = " ".join(fact.lower() for fact in visible_facts)
    if "guard" in visible_low and "missing patrol" in visible_low:
        if passive_streak >= 2:
            text = (
                'The same guard does not let the silence stand a second time. "No more watching," he says, '
                "closing the distance and jabbing a finger at the east-road line on the notice. "
                '"Either tell me who sent you, or get moving before that trail cools for good."'
            )
        else:
            text = (
                'A guard peels away from the notice board and squares up to you. "Standing still won\'t help that patrol," '
                'he says, stabbing two fingers at the posting. "Tell me what you know, or get on the east-road trail before it dies."'
            )
        return [
            _passive_scene_pressure_visibility_candidate(
                text,
                fallback_kind="passive_scene_pressure_guard_rumor",
                fallback_candidate_source="passive_scene_pressure:guard_rumor",
            )
        ]
    if "guard" in visible_low:
        text = (
            'A guard notices you lingering and comes over at once. "If you\'re waiting on trouble, it already passed the checkpoint," '
            'he says. "Take the east-road report or get clear."'
        )
        return [
            _passive_scene_pressure_visibility_candidate(
                text,
                fallback_kind="passive_scene_pressure_visible_figure",
                fallback_candidate_source="passive_scene_pressure:visible_figure",
            )
        ]
    return [
        _passive_scene_pressure_visibility_candidate(
            'The pause snaps when a nearby guard points with his spear-butt instead of waiting for you to choose. '
            '"Board, runner, or road," he says. "Pick one before the gate swallows the trail."',
            fallback_kind="passive_scene_pressure_generic",
            fallback_candidate_source="passive_scene_pressure:fallback",
        )
    ]


def _merge_upstream_concrete_beat(existing_text: str, beat_text: str) -> str:
    existing = _normalize_text(existing_text)
    beat = _output_sentence(beat_text)
    if not existing:
        return beat
    if not beat:
        return existing
    if existing[-1] not in ".!?":
        existing += "."
    return f"{existing} {beat}"


def _select_deterministic_upstream_concrete_beat(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    scene_id: str,
) -> Tuple[str, str] | None:
    """Pick a minimal deterministic beat for upstream satisfier (same pool as sealed candidates)."""
    candidates = _passive_scene_pressure_fallback_candidates(
        session=session,
        scene=scene,
        scene_id=scene_id,
    )
    if not candidates:
        visible_facts = _scene_visible_facts(scene)
        visible_low = " ".join(fact.lower() for fact in visible_facts)
        if "merchant" in visible_low:
            return (
                'A nearby merchant catches your lingering look and nods. '
                '"If you mean to buy or ask, speak up before the board changes," she says.',
                "merchant_acknowledgement",
            )
        return None
    candidate = candidates[0]
    beat_type = _BEAT_TYPE_BY_FALLBACK_KIND.get(str(candidate.fallback_kind or ""), "environmental_reaction")
    return candidate.text, beat_type


def _reset_passive_scene_concrete_beat_satisfier_meta(meta: Dict[str, Any]) -> None:
    meta["passive_scene_concrete_beat_satisfier_attempted"] = False
    meta["passive_scene_concrete_beat_satisfier_applied"] = False
    meta["passive_scene_concrete_beat_satisfier_eligible"] = False
    meta["passive_scene_concrete_beat_type"] = None
    meta["passive_scene_pressure_fallback_avoided"] = False


def passive_scene_concrete_beat_satisfier_meta_snapshot(meta: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "passive_scene_concrete_beat_satisfier_attempted",
        "passive_scene_concrete_beat_satisfier_applied",
        "passive_scene_concrete_beat_satisfier_eligible",
        "passive_scene_concrete_beat_type",
        "passive_scene_pressure_fallback_avoided",
    )
    return {key: meta[key] for key in keys if key in meta}


def restore_passive_scene_concrete_beat_satisfier_meta(
    meta: Dict[str, Any], preserved: Mapping[str, Any]
) -> None:
    for key, value in preserved.items():
        meta[key] = value


def passive_scene_concrete_beat_satisfier_preserves_upstream(
    meta: Mapping[str, Any], candidate_text: str
) -> bool:
    """True when upstream satisfier already injected a contract-satisfying concrete beat."""
    return (
        meta.get("passive_scene_concrete_beat_satisfier_applied") is True
        and reply_has_concrete_interaction(candidate_text)
    )


def apply_observe_passive_scene_concrete_beat_upstream_satisfier(
    out: Dict[str, Any],
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
    scene_id: str,
    res_kind: str,
    strict_social_active: bool,
) -> Dict[str, Any]:
    """Observe-route upstream concrete-beat satisfier before non-strict stack / sealed replace."""
    from game.final_emission_meta import (
        PRODUCER_REPAIR_KIND_PASSIVE_SCENE_CONCRETE_BEAT,
        ensure_final_emission_meta_dict,
        stamp_producer_repair_kind,
    )

    _ = world  # reserved for future scene-aware beat selection
    meta = ensure_final_emission_meta_dict(out)
    candidate_text = _normalize_text(out.get("player_facing_text"))
    if (
        meta.get("passive_scene_concrete_beat_satisfier_applied") is True
        and _reply_already_has_concrete_interaction(candidate_text)
    ):
        return out

    _reset_passive_scene_concrete_beat_satisfier_meta(meta)

    if strict_social_active or str(res_kind or "").strip().lower() != "observe":
        return out

    if not candidate_text:
        return out

    meta["passive_scene_concrete_beat_satisfier_attempted"] = True
    sid = str(scene_id or "").strip()

    if not _passive_scene_pressure_due_for_fallback(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
    ):
        return out

    if _reply_already_has_concrete_interaction(candidate_text):
        return out

    meta["passive_scene_concrete_beat_satisfier_eligible"] = True
    selected = _select_deterministic_upstream_concrete_beat(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=sid,
    )
    if selected is None:
        return out

    beat_text, beat_type = selected
    merged = _merge_upstream_concrete_beat(candidate_text, beat_text)
    if not _reply_already_has_concrete_interaction(merged):
        return out

    out["player_facing_text"] = merged
    meta["passive_scene_concrete_beat_satisfier_applied"] = True
    meta["passive_scene_concrete_beat_type"] = beat_type
    meta["passive_scene_pressure_fallback_avoided"] = True
    stamp_producer_repair_kind(meta, PRODUCER_REPAIR_KIND_PASSIVE_SCENE_CONCRETE_BEAT)
    return out
