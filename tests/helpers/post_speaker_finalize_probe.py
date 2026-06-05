"""Block U — post-speaker finalize stack probes (tests only).

Wraps Gate layer callables to record whether normalized ``player_facing_text`` changes at each
invocation. Order matches the strict-social accept trunk in ``apply_final_emission_gate`` (post
``enforce_emitted_speaker_with_contract`` / sync), then late-stack seams through finalize.

Also probes **inline** ``_strip_dialogue_from_text`` calls **after** speaker enforcement (dialogue-plan
subtractive strip following fast-fallback neutral composition), which are not a named layer function.

Does not change production behavior beyond monkeypatched wrappers delegating to originals.

**Retained private ``feg._*`` seams (AS6):** layer wrappers in
:func:`install_post_speaker_text_probes` and :func:`chain_enforce_phase_marker` must patch gate-module
symbols because divergence inventory is defined over the strict-social accept trunk's private layer
callables. Replacing with ``apply_final_emission_gate_consumer`` would collapse observability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Protocol

import game.final_emission_gate as feg
from game.final_emission_text import _normalize_text


@dataclass(frozen=True)
class LayerTextDelta:
    """Single observed crossing for one wrapped callable."""

    layer_id: str
    normalized_changed: bool


class PostSpeakerPhase(Protocol):
    """Set by tests after :func:`~game.final_emission_gate.enforce_emitted_speaker_with_contract` returns."""

    after_enforce: bool


# Pipeline order for reporting / “first diverger” scan (strict-social accept path).
POST_SPEAKER_PROBE_ORDER: tuple[str, ...] = (
    "anti_railroading",
    "context_separation",
    "narration_purity",
    "answer_shape_primacy",
    "scene_state_anchor",
    "fast_fallback_neutral_composition",
    "dialogue_plan_subtractive_strip",
    "answer_exposition_plan_post_speaker",
    "visibility_enforcement",
    "interaction_continuity_step",
    "fallback_behavior",
    "referent_clarity_pre_finalize",
    "acceptance_quality_n4",
    "attach_interaction_continuity_validation",
    "finalize_emission_output",
)

# First ``answer_exposition_plan`` call in strict-social trunk is **before** speaker enforcement.
PRE_SPEAKER_PROBE_IDS: frozenset[str] = frozenset({"answer_exposition_plan_pre_speaker"})


def _track(events: List[LayerTextDelta], layer_id: str, tin: str, tout: str) -> None:
    events.append(
        LayerTextDelta(
            layer_id=layer_id,
            normalized_changed=tin != tout,
        )
    )


def chain_enforce_phase_marker(monkeypatch: Any, phase: PostSpeakerPhase) -> None:
    """Wrap ``enforce_emitted_speaker_with_contract`` so ``phase.after_enforce`` is True after it returns."""

    cur = feg.enforce_emitted_speaker_with_contract

    def _marked(text: str, **kwargs: Any) -> Any:
        r = cur(text, **kwargs)
        phase.after_enforce = True  # type: ignore[misc]
        return r

    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", _marked)


def install_post_speaker_text_probes(
    monkeypatch: Any,
    events: List[LayerTextDelta],
    *,
    phase: PostSpeakerPhase | None = None,
) -> None:
    """Install wrappers on ``game.final_emission_gate`` symbols; append one record per invocation.

    Pass *phase* (+ :func:`chain_enforce_phase_marker`) so ``answer_exposition_plan`` can be split into
    pre- vs post-speaker ids and ``_strip_dialogue_from_text`` can record dialogue-plan subtractive strip.
    """

    def wrap_tuple(layer_id: str, orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(text: str, *args: Any, **kwargs: Any) -> Any:
            tin = _normalize_text(text)
            out = orig(text, *args, **kwargs)
            if isinstance(out, tuple) and out:
                tout = _normalize_text(str(out[0] or ""))
            else:
                tout = tin
            _track(events, layer_id, tin, tout)
            return out

        return w

    def wrap_answer_exposition(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(text: str, *args: Any, **kwargs: Any) -> Any:
            if phase is None:
                lid = "answer_exposition_plan"
            elif not getattr(phase, "after_enforce", False):
                lid = "answer_exposition_plan_pre_speaker"
            else:
                lid = "answer_exposition_plan_post_speaker"
            tin = _normalize_text(text)
            out = orig(text, *args, **kwargs)
            if isinstance(out, tuple) and out:
                tout = _normalize_text(str(out[0] or ""))
            else:
                tout = tin
            _track(events, lid, tin, tout)
            return out

        return w

    def wrap_visibility(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: Dict[str, Any], **kwargs: Any) -> Any:
            tin = _normalize_text(str(out.get("player_facing_text") or ""))
            res = orig(out, **kwargs)
            base = res if isinstance(res, dict) else out
            tout = _normalize_text(str(base.get("player_facing_text") or ""))
            _track(events, "visibility_enforcement", tin, tout)
            return res

        return w

    def wrap_ic_step(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: Any, *, text: str, **kwargs: Any) -> Any:
            tin = _normalize_text(str(text or ""))
            result = orig(out, text=text, **kwargs)
            if isinstance(result, tuple) and result:
                tout = _normalize_text(str(result[0] or ""))
            else:
                tout = tin
            _track(events, "interaction_continuity_step", tin, tout)
            return result

        return w

    def wrap_out_mutate(layer_id: str, orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(*args: Any, **kwargs: Any) -> Any:
            out = args[0] if args else kwargs.get("out")
            if not isinstance(out, dict):
                return orig(*args, **kwargs)
            tin = _normalize_text(str(out.get("player_facing_text") or ""))
            res = orig(*args, **kwargs)
            tout = _normalize_text(str(out.get("player_facing_text") or ""))
            _track(events, layer_id, tin, tout)
            return res

        return w

    def wrap_finalize(orig: Callable[..., Any]) -> Callable[..., Any]:
        def w(out: Dict[str, Any], **kwargs: Any) -> Any:
            if not isinstance(out, dict):
                return orig(out, **kwargs)
            tin = _normalize_text(str(out.get("player_facing_text") or ""))
            res = orig(out, **kwargs)
            tout = _normalize_text(str(out.get("player_facing_text") or ""))
            _track(events, "finalize_emission_output", tin, tout)
            return res

        return w

    if phase is not None:

        def wrap_strip(orig: Callable[..., Any]) -> Callable[..., Any]:
            def w(t: str) -> str:
                tin = _normalize_text(str(t or ""))
                r = orig(t)
                tout = _normalize_text(str(r or ""))
                if getattr(phase, "after_enforce", False):
                    _track(events, "dialogue_plan_subtractive_strip", tin, tout)
                return r

            return w

        monkeypatch.setattr(feg, "_strip_dialogue_from_text", wrap_strip(feg._strip_dialogue_from_text))

    monkeypatch.setattr(feg, "_apply_anti_railroading_layer", wrap_tuple("anti_railroading", feg._apply_anti_railroading_layer))
    monkeypatch.setattr(
        feg, "_apply_context_separation_layer", wrap_tuple("context_separation", feg._apply_context_separation_layer)
    )
    monkeypatch.setattr(
        feg,
        "_apply_player_facing_narration_purity_layer",
        wrap_tuple("narration_purity", feg._apply_player_facing_narration_purity_layer),
    )
    monkeypatch.setattr(
        feg, "_apply_answer_shape_primacy_layer", wrap_tuple("answer_shape_primacy", feg._apply_answer_shape_primacy_layer)
    )
    monkeypatch.setattr(
        feg, "_apply_scene_state_anchor_layer", wrap_tuple("scene_state_anchor", feg._apply_scene_state_anchor_layer)
    )
    monkeypatch.setattr(
        feg,
        "_apply_fast_fallback_neutral_composition_layer",
        wrap_tuple("fast_fallback_neutral_composition", feg._apply_fast_fallback_neutral_composition_layer),
    )

    monkeypatch.setattr(feg, "_apply_answer_exposition_plan_layer", wrap_answer_exposition(feg._apply_answer_exposition_plan_layer))

    monkeypatch.setattr(feg, "_apply_visibility_enforcement", wrap_visibility(feg._apply_visibility_enforcement))
    monkeypatch.setattr(
        feg, "_apply_interaction_continuity_emission_step", wrap_ic_step(feg._apply_interaction_continuity_emission_step)
    )
    monkeypatch.setattr(
        feg, "_apply_fallback_behavior_layer", wrap_tuple("fallback_behavior", feg._apply_fallback_behavior_layer)
    )
    monkeypatch.setattr(
        feg, "_apply_referent_clarity_pre_finalize", wrap_out_mutate("referent_clarity_pre_finalize", feg._apply_referent_clarity_pre_finalize)
    )
    monkeypatch.setattr(
        feg,
        "_apply_acceptance_quality_n4_floor_seam",
        wrap_out_mutate("acceptance_quality_n4", feg._apply_acceptance_quality_n4_floor_seam),
    )
    monkeypatch.setattr(
        feg,
        "_attach_interaction_continuity_validation",
        wrap_out_mutate("attach_interaction_continuity_validation", feg._attach_interaction_continuity_validation),
    )
    monkeypatch.setattr(feg, "_finalize_emission_output", wrap_finalize(feg._finalize_emission_output))


def first_normalized_divergence(events: List[LayerTextDelta]) -> str | None:
    """Return ``layer_id`` of the first probe where normalized text changed, or ``None``."""
    for e in events:
        if e.normalized_changed:
            return e.layer_id
    return None


def divergence_summary(events: List[LayerTextDelta]) -> dict[str, bool]:
    """Whether each ``layer_id`` ever flipped normalized text in this run (last write wins per id)."""
    out: dict[str, bool] = {}
    for e in events:
        out[e.layer_id] = e.normalized_changed
    return out


def first_post_speaker_normalized_divergence(events: List[LayerTextDelta]) -> str | None:
    """First probe after speaker enforcement whose normalized text changed (skips pre-speaker AEP)."""
    for e in events:
        if e.layer_id in PRE_SPEAKER_PROBE_IDS:
            continue
        if e.normalized_changed:
            return e.layer_id
    return None


def post_speaker_events_only(events: List[LayerTextDelta]) -> List[LayerTextDelta]:
    """Drop strictly pre-speaker instrumentation rows."""
    return [e for e in events if e.layer_id not in PRE_SPEAKER_PROBE_IDS]
