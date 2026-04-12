"""Deterministic, shallow behavioral checks for narration-style transcripts (tests/tooling only).

Inspects only caller-supplied turn dicts; no GPT calls and no ``game/`` imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "behavioral_gauntlet_eval.v1"
MAX_EVIDENCE_TURNS = 5

_ALL_AXIS_NAMES = frozenset(
    {
        "neutrality",
        "escalation_correctness",
        "reengagement_quality",
        "dialogue_coherence",
    }
)


@dataclass
class BehavioralTurnSlice:
    """Normalized single exchange for evaluation."""

    turn_index: int
    player_text: str
    gm_text: str
    resolution_kind: str | None = None
    speaker_id: str | None = None
    scene_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BehavioralAxisResult:
    axis: str
    passed: bool
    score: int  # 0..2
    reason_codes: tuple[str, ...]
    summary: str
    evidence_turn_indexes: tuple[int, ...]


@dataclass(frozen=True)
class BehavioralGauntletResult:
    schema_version: str
    axes: dict[str, BehavioralAxisResult]
    overall_passed: bool


def _norm_text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: str) -> str:
    return value.lower()


def _bounded_indexes(indexes: Iterable[int]) -> tuple[int, ...]:
    out: list[int] = []
    for idx in indexes:
        if idx not in out:
            out.append(int(idx))
        if len(out) >= MAX_EVIDENCE_TURNS:
            break
    return tuple(out)


def _messages_pair(raw: Mapping[str, Any]) -> tuple[str, str]:
    """Extract (player, gm) from a ``messages``-style payload if present."""
    msgs = raw.get("messages")
    if not isinstance(msgs, list) or not msgs:
        return "", ""
    user_chunks: list[str] = []
    asst_chunks: list[str] = []
    for item in msgs:
        if not isinstance(item, dict):
            continue
        role = _lower(_norm_text(item.get("role")))
        content = item.get("content")
        if isinstance(content, list):
            text_parts: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    text_parts.append(_norm_text(block.get("text") or block.get("content")))
                else:
                    text_parts.append(_norm_text(block))
            blob = " ".join(part for part in text_parts if part).strip()
        else:
            blob = _norm_text(content if content is not None else item.get("text"))
        if role in {"user", "player"}:
            user_chunks.append(blob)
        elif role in {"assistant", "gm"}:
            asst_chunks.append(blob)
    return " ".join(user_chunks).strip(), " ".join(asst_chunks).strip()


def normalize_turn_dict(raw: Mapping[str, Any], *, turn_index: int) -> BehavioralTurnSlice:
    """Map a raw snapshot or simplified dict into a :class:`BehavioralTurnSlice`."""
    player = _norm_text(
        raw.get("player_text", raw.get("user_text", raw.get("player", raw.get("prompt", ""))))
    )
    gm = _norm_text(raw.get("gm_text", raw.get("assistant_text", raw.get("gm", raw.get("response", "")))))
    if not player or not gm:
        m_player, m_gm = _messages_pair(raw)
        player = player or m_player
        gm = gm or m_gm

    meta = raw.get("metadata")
    metadata: dict[str, Any] = dict(meta) if isinstance(meta, dict) else {}

    rk = raw.get("resolution_kind")
    resolution_kind = str(rk).strip() if rk is not None and str(rk).strip() else None

    sid = raw.get("speaker_id")
    speaker_id = str(sid).strip() if sid is not None and str(sid).strip() else None

    sc = raw.get("scene_id")
    scene_id = str(sc).strip() if sc is not None and str(sc).strip() else None

    return BehavioralTurnSlice(
        turn_index=int(turn_index),
        player_text=player,
        gm_text=gm,
        resolution_kind=resolution_kind,
        speaker_id=speaker_id,
        scene_id=scene_id,
        metadata=metadata,
    )


def normalize_turn_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[BehavioralTurnSlice, ...]:
    return tuple(normalize_turn_dict(row, turn_index=idx) for idx, row in enumerate(rows))


# --- Lexicons (bounded, deterministic) ---

_PLAYER_HOSTILE = (
    "kill you",
    "attack",
    "punch",
    "spit",
    "hate you",
    "traitor",
    "draw my sword",
    "draw steel",
    "threat",
    "curse you",
    "insult",
)

_PLAYER_NEUTRALISH = (
    "what do i see",
    "look around",
    "describe",
    "ask about",
    "where is",
    "who is",
    "read the",
    "examine",
    "listen",
    "approach calmly",
)

_GM_HOSTILITY = (
    "how dare you",
    "accuse you",
    "you're a liar",
    "you are a liar",
    "traitor",
    "filthy",
    "coward",
    "i'll kill you",
    "cut you down",
    "enemy of the",
    "you fool",
    "idiot",
)

_GM_GROUNDING = (
    "because",
    "given the",
    "due to",
    "orders",
    "notice",
    "posted",
    "report",
    "according to",
    "patrol",
    "checkpoint",
    "law",
    "regulation",
)

_GM_ESCALATION = (
    "attacks you",
    "draws a weapon",
    "draws steel",
    "initiative",
    "blood",
    "slashes",
    "combat",
    "arrest you",
    "shackle",
)

_GM_OVERLY_COMPLIANT = (
    "anything you wish",
    "anything you ask",
    "happy to oblige",
    "certainly sir",
    "of course master",
    "as you command",
    "no problem at all",
)

_GM_STONEWALL = (
    "need more specifics",
    "need more specific",
    "need more detail",
    "be more specific",
    "what exactly do you mean",
    "clarify what you",
    "which detail",
    "i need more",
)

_GM_PROGRESS = (
    "instead",
    "narrow",
    "specifically",
    "you notice",
    "the trail",
    "the sign",
    "the guard",
    "here is",
    "one path",
    "try the",
)

_NEGATION_A = ("no gate", "there is no gate", "no such", "nothing here", "no sign of")
_AFFIRM_A = ("the gate", "through the gate", "you pass the gate", "beyond the gate")

_RESET_PHRASES = ("welcome to the tutorial", "session reset", "starting fresh")


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    h = _lower(haystack)
    return any(n in h for n in needles)


def _player_tone(player: str) -> str:
    p = _lower(player)
    if not p:
        return "unknown"
    if any(tok in p for tok in _PLAYER_HOSTILE):
        return "hostile"
    if any(tok in p for tok in _PLAYER_NEUTRALISH):
        return "neutral"
    return "mixed"


def _axis_result(
    *,
    axis: str,
    passed: bool,
    score: int,
    reason_codes: tuple[str, ...],
    summary: str,
    evidence_turn_indexes: Iterable[int],
) -> BehavioralAxisResult:
    score = max(0, min(2, int(score)))
    return BehavioralAxisResult(
        axis=axis,
        passed=passed,
        score=score,
        reason_codes=reason_codes,
        summary=summary,
        evidence_turn_indexes=_bounded_indexes(evidence_turn_indexes),
    )


def evaluate_neutrality(slices: Sequence[BehavioralTurnSlice]) -> BehavioralAxisResult:
    """Fail on ungrounded social aggression after neutral-ish player input."""
    if not slices:
        return _axis_result(
            axis="neutrality",
            passed=True,
            score=2,
            reason_codes=("neutral_ok",),
            summary="No turns supplied; neutrality not violated.",
            evidence_turn_indexes=(),
        )

    for sl in slices:
        tone = _player_tone(sl.player_text)
        if tone != "neutral":
            continue
        gm = sl.gm_text
        if not gm.strip():
            continue
        hostile = _contains_any(gm, _GM_HOSTILITY)
        grounded = _contains_any(gm, _GM_GROUNDING) or _contains_any(sl.player_text, _GM_GROUNDING)
        if hostile and not grounded:
            return _axis_result(
                axis="neutrality",
                passed=False,
                score=0,
                reason_codes=("ungrounded_hostility",),
                summary="Neutral player input met socially aggressive GM prose without clear grounding.",
                evidence_turn_indexes=(sl.turn_index,),
            )
    return _axis_result(
        axis="neutrality",
        passed=True,
        score=2,
        reason_codes=("neutral_ok",),
        summary="No ungrounded hostility detected for neutral player prompts.",
        evidence_turn_indexes=(),
    )


def evaluate_escalation_correctness(slices: Sequence[BehavioralTurnSlice]) -> BehavioralAxisResult:
    """Broad proportionality between player tone and GM escalation/compliance."""
    evidence: list[int] = []
    for sl in slices:
        tone = _player_tone(sl.player_text)
        gm = sl.gm_text
        rk = (sl.resolution_kind or "").lower()

        if tone == "neutral":
            if rk in {"combat", "violence", "attack"} or _contains_any(gm, _GM_ESCALATION):
                return _axis_result(
                    axis="escalation_correctness",
                    passed=False,
                    score=0,
                    reason_codes=("escalation_too_high",),
                    summary="Neutral player input received combat-grade escalation.",
                    evidence_turn_indexes=(sl.turn_index,),
                )

        if tone == "hostile":
            if _contains_any(gm, _GM_OVERLY_COMPLIANT) and not _contains_any(gm, _GM_ESCALATION + _GM_HOSTILITY):
                return _axis_result(
                    axis="escalation_correctness",
                    passed=False,
                    score=0,
                    reason_codes=("escalation_too_flat",),
                    summary="Hostile player input was met with implausibly compliant GM tone.",
                    evidence_turn_indexes=(sl.turn_index,),
                )

        evidence.append(sl.turn_index)

    return _axis_result(
        axis="escalation_correctness",
        passed=True,
        score=2,
        reason_codes=("escalation_proportional",),
        summary="Escalation stayed broadly proportional to player tone and resolution hints.",
        evidence_turn_indexes=evidence[:1],
    )


def evaluate_reengagement_quality(slices: Sequence[BehavioralTurnSlice]) -> BehavioralAxisResult:
    """Detect clarification loops across adjacent turns (shallow)."""
    if len(slices) < 2:
        return _axis_result(
            axis="reengagement_quality",
            passed=True,
            score=2,
            reason_codes=("reengagement_progress",),
            summary="Not enough turns to assess re-engagement; treating as non-violation.",
            evidence_turn_indexes=(),
        )

    for left, right in zip(slices, slices[1:], strict=False):
        if _contains_any(left.gm_text, _GM_STONEWALL) and _contains_any(right.gm_text, _GM_STONEWALL):
            return _axis_result(
                axis="reengagement_quality",
                passed=False,
                score=0,
                reason_codes=("reengagement_loop",),
                summary="Adjacent GM turns repeated generic clarification without forward progress.",
                evidence_turn_indexes=(left.turn_index, right.turn_index),
            )

    return _axis_result(
        axis="reengagement_quality",
        passed=True,
        score=2,
        reason_codes=("reengagement_progress",),
        summary="No adjacent stonewall loop detected; follow-ups look serviceable at a coarse level.",
        evidence_turn_indexes=_bounded_indexes(range(min(len(slices), 2))),
    )


_HANDOFF_HINTS = (
    "turn to",
    "to the clerk",
    "to the guard",
    "other npc",
    "someone else",
    "instead i speak",
)


def evaluate_dialogue_coherence(slices: Sequence[BehavioralTurnSlice]) -> BehavioralAxisResult:
    """Local adjacency checks only (speaker/scene/reset/contradiction heuristics)."""
    if len(slices) < 2:
        return _axis_result(
            axis="dialogue_coherence",
            passed=True,
            score=2,
            reason_codes=("coherence_ok",),
            summary="Not enough turns for adjacency coherence checks.",
            evidence_turn_indexes=(),
        )

    for left, right in zip(slices, slices[1:], strict=False):
        if right.turn_index >= 1 and _contains_any(right.gm_text, _RESET_PHRASES):
            return _axis_result(
                axis="dialogue_coherence",
                passed=False,
                score=0,
                reason_codes=("local_reset",),
                summary="Detected a tutorial/session-reset style break mid-transcript window.",
                evidence_turn_indexes=(left.turn_index, right.turn_index),
            )

        if _contains_any(left.gm_text, _NEGATION_A) and _contains_any(right.gm_text, _AFFIRM_A):
            return _axis_result(
                axis="dialogue_coherence",
                passed=False,
                score=0,
                reason_codes=("contradiction_local",),
                summary="Adjacent GM turns flip between denying and affirming the same focal object.",
                evidence_turn_indexes=(left.turn_index, right.turn_index),
            )

        if (
            left.speaker_id
            and right.speaker_id
            and left.scene_id
            and right.scene_id
            and left.scene_id == right.scene_id
            and left.speaker_id != right.speaker_id
        ):
            bridge = _lower(right.player_text)
            if not any(h in bridge for h in _HANDOFF_HINTS):
                return _axis_result(
                    axis="dialogue_coherence",
                    passed=False,
                    score=0,
                    reason_codes=("speaker_drift",),
                    summary="Speaker id changed within the same scene without a coarse player handoff cue.",
                    evidence_turn_indexes=(left.turn_index, right.turn_index),
                )

    return _axis_result(
        axis="dialogue_coherence",
        passed=True,
        score=2,
        reason_codes=("coherence_ok",),
        summary="Adjacent-turn continuity looks locally consistent under shallow checks.",
        evidence_turn_indexes=(0, 1),
    )


def _axis_to_mapping(result: BehavioralAxisResult) -> dict[str, Any]:
    return {
        "axis": result.axis,
        "passed": result.passed,
        "score": result.score,
        "reason_codes": list(result.reason_codes),
        "summary": result.summary,
        "evidence_turn_indexes": list(result.evidence_turn_indexes),
    }


def _result_to_mapping(result: BehavioralGauntletResult) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "overall_passed": result.overall_passed,
        "axes": {name: _axis_to_mapping(axis) for name, axis in result.axes.items()},
    }


def evaluate_behavioral_gauntlet(
    turns: list[dict[str, Any]],
    *,
    expected_axis: set[str] | None = None,
) -> dict[str, Any]:
    """Evaluate normalized transcript rows; returns a compact, stable dict payload.

    ``expected_axis`` optionally restricts which axes are evaluated (names must be known).
    """
    slices = normalize_turn_rows(turns)
    axes_to_run = frozenset(expected_axis) if expected_axis is not None else set(_ALL_AXIS_NAMES)
    unknown = axes_to_run - set(_ALL_AXIS_NAMES)
    if unknown:
        raise ValueError(f"Unknown axis names: {sorted(unknown)}")

    runners: dict[str, Any] = {
        "neutrality": evaluate_neutrality,
        "escalation_correctness": evaluate_escalation_correctness,
        "reengagement_quality": evaluate_reengagement_quality,
        "dialogue_coherence": evaluate_dialogue_coherence,
    }

    axis_results: dict[str, BehavioralAxisResult] = {}
    for name in sorted(axes_to_run):
        axis_results[name] = runners[name](slices)

    overall = all(r.passed for r in axis_results.values())
    bundle = BehavioralGauntletResult(
        schema_version=SCHEMA_VERSION,
        axes=axis_results,
        overall_passed=overall,
    )
    return _result_to_mapping(bundle)
