"""BT1 — Speaker Contract Risk observation helper (tests only).

Captures ordered speaker/text checkpoints around speaker finalize, locates first
divergence, and scores contract risk without changing runtime behavior.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, replace
from typing import Any, Literal, Mapping, Sequence

from game.emitted_speaker_signature import detect_emitted_speaker_signature
from game.final_emission_text_formatting import _normalize_text

from tests.helpers.golden_replay_fixtures import observed_turn_from_gate_output
from tests.helpers.golden_replay_projection import golden_text_hash, normalize_golden_text
from tests.helpers.post_speaker_finalize_probe import (
    POST_SPEAKER_PROBE_ORDER,
    LayerTextDelta,
    first_post_speaker_normalized_divergence,
)

SpeakerStatus = Literal["resolved", "neutral", "unattributed", "ambiguous", "unresolved"]

CHECKPOINT_PRE_SPEAKER = "P0_pre_speaker_finalize"
CHECKPOINT_POST_SPEAKER = "P1_post_speaker_finalize"
CHECKPOINT_FINAL = "P3_final_emission"
CHECKPOINT_REPLAY = "P4_replay_projection"

_LAYER_CHECKPOINT_PREFIX = "P2_"

_MAX_PRESERVED_TEXT = 240


@dataclass(frozen=True)
class SpeakerCheckpoint:
    checkpoint_id: str
    normalized_text: str
    normalized_text_hash: str
    emitted_speaker_signature: dict[str, Any]
    resolved_speaker_id: str | None
    speaker_status: SpeakerStatus
    source: str | None = None
    owner: str | None = None


@dataclass(frozen=True)
class SpeakerContractRiskScore:
    D: int
    S: int
    T: int
    A: int

    @property
    def total(self) -> int:
        return min(100, self.D + self.S + self.T + self.A)

    @property
    def band(self) -> str:
        score = self.total
        if score <= 19:
            return "low"
        if score <= 39:
            return "guarded"
        if score <= 69:
            return "elevated"
        return "high"


@dataclass(frozen=True)
class SpeakerContractObservation:
    checkpoints: tuple[SpeakerCheckpoint, ...]
    layer_events: tuple[LayerTextDelta, ...]
    expected_speaker_id: str | None
    expected_speaker_source: str | None
    enforcement_owner: str | None
    replay_selected_speaker_id: str | None
    replay_selected_speaker_source: str | None
    first_text_divergence_checkpoint_id: str | None
    first_speaker_divergence_checkpoint_id: str | None
    first_divergence_checkpoint_id: str | None
    first_divergence_layer_id: str | None
    risk: SpeakerContractRiskScore
    mismatch_present: bool = False

    def as_record(self) -> dict[str, Any]:
        """Stable JSON-like dict for reports and focused tests."""
        return {
            "checkpoints": [asdict(cp) for cp in self.checkpoints],
            "layer_events": [asdict(ev) for ev in self.layer_events],
            "expected_speaker_id": self.expected_speaker_id,
            "expected_speaker_source": self.expected_speaker_source,
            "enforcement_owner": self.enforcement_owner,
            "replay_selected_speaker_id": self.replay_selected_speaker_id,
            "replay_selected_speaker_source": self.replay_selected_speaker_source,
            "first_text_divergence_checkpoint_id": self.first_text_divergence_checkpoint_id,
            "first_speaker_divergence_checkpoint_id": self.first_speaker_divergence_checkpoint_id,
            "first_divergence_checkpoint_id": self.first_divergence_checkpoint_id,
            "first_divergence_layer_id": self.first_divergence_layer_id,
            "mismatch_present": self.mismatch_present,
            "risk": {
                "D": self.risk.D,
                "S": self.risk.S,
                "T": self.risk.T,
                "A": self.risk.A,
                "total": self.risk.total,
                "band": self.risk.band,
            },
        }


def normalize_checkpoint_text(text: Any, *, use_golden: bool = False) -> str:
    """Normalize player-facing text for checkpoint comparison."""
    if use_golden:
        return normalize_golden_text(text)
    return _normalize_text(str(text or ""))


def checkpoint_text_hash(text: Any, *, use_golden: bool = False) -> str:
    """Short deterministic hash aligned with probe normalization by default."""
    normalized = normalize_checkpoint_text(text, use_golden=use_golden)
    if use_golden:
        return golden_text_hash(normalized)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def parse_emitted_speaker_signature(
    text: str,
    resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse emitted speaker signature via the runtime read helper."""
    res = dict(resolution) if isinstance(resolution, Mapping) else None
    return dict(detect_emitted_speaker_signature(str(text or ""), res))


def _normalize_speaker_label(value: str | None) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _labels_match_expected(
    signature: Mapping[str, Any],
    expected_speaker_name: str | None,
) -> bool:
    if not expected_speaker_name:
        return False
    expected = _normalize_speaker_label(expected_speaker_name)
    for key in ("speaker_name", "speaker_label"):
        candidate = _normalize_speaker_label(str(signature.get(key) or ""))
        if not candidate:
            continue
        if candidate == expected or expected in candidate or candidate in expected:
            return True
    return False


def classify_speaker_status(
    *,
    signature: Mapping[str, Any],
    expected_speaker_id: str | None = None,
    expected_speaker_name: str | None = None,
    enforcement_reason: str | None = None,
    narrator_neutral: bool = False,
) -> tuple[str | None, SpeakerStatus]:
    """Return resolved speaker id (when known) and explicit speaker status."""
    if narrator_neutral or enforcement_reason == "narrator_neutral_no_allowed_speaker":
        return None, "neutral"

    if signature.get("is_generic_fallback_label"):
        return None, "ambiguous"

    label = str(signature.get("speaker_label") or "").strip()
    name = str(signature.get("speaker_name") or "").strip()
    if not label and not name:
        return None, "unattributed"

    if expected_speaker_id and _labels_match_expected(signature, expected_speaker_name):
        return expected_speaker_id, "resolved"

    if name and signature.get("is_explicitly_attributed"):
        return None, "unresolved"

    if label or name:
        confidence = str(signature.get("confidence") or "").strip().lower()
        if confidence == "medium":
            return None, "ambiguous"
        return None, "unresolved"

    return None, "unattributed"


def build_speaker_checkpoint(
    checkpoint_id: str,
    text: str,
    *,
    expected_speaker_id: str | None = None,
    expected_speaker_name: str | None = None,
    enforcement_reason: str | None = None,
    narrator_neutral: bool = False,
    resolution: Mapping[str, Any] | None = None,
    source: str | None = None,
    owner: str | None = None,
    use_golden: bool = False,
) -> SpeakerCheckpoint:
    normalized = normalize_checkpoint_text(text, use_golden=use_golden)
    signature = parse_emitted_speaker_signature(normalized, resolution)
    resolved_id, status = classify_speaker_status(
        signature=signature,
        expected_speaker_id=expected_speaker_id,
        expected_speaker_name=expected_speaker_name,
        enforcement_reason=enforcement_reason,
        narrator_neutral=narrator_neutral,
    )
    return SpeakerCheckpoint(
        checkpoint_id=checkpoint_id,
        normalized_text=normalized,
        normalized_text_hash=checkpoint_text_hash(normalized, use_golden=use_golden),
        emitted_speaker_signature=signature,
        resolved_speaker_id=resolved_id,
        speaker_status=status,
        source=source,
        owner=owner,
    )


def build_replay_projection_checkpoint(
    replay_observation: Mapping[str, Any],
    *,
    expected_speaker_id: str | None = None,
    expected_speaker_name: str | None = None,
    resolution: Mapping[str, Any] | None = None,
) -> SpeakerCheckpoint:
    """Build P4 from :func:`project_turn_observation` output with explicit unavailable handling."""
    speaker_unavailable = replay_speaker_evidence_unavailable(replay_observation)
    selected_id = replay_observation.get("selected_speaker_id")
    selected_source = replay_observation.get("selected_speaker_source")

    if speaker_unavailable:
        final_text = str(replay_observation.get("final_text") or "")
        normalized = normalize_checkpoint_text(final_text, use_golden=True)
        signature = parse_emitted_speaker_signature(normalized, resolution)
        return SpeakerCheckpoint(
            checkpoint_id=CHECKPOINT_REPLAY,
            normalized_text=normalized,
            normalized_text_hash=str(replay_observation.get("final_text_hash") or golden_text_hash(normalized)),
            emitted_speaker_signature=signature,
            resolved_speaker_id=None,
            speaker_status="unresolved",
            source=None,
            owner="golden_replay_projection",
        )

    cp = build_replay_checkpoint(
        replay_observation,
        expected_speaker_id=expected_speaker_id,
        expected_speaker_name=expected_speaker_name,
        resolution=resolution,
    )
    if selected_id is not None and not selected_source:
        return replace(cp, source=None)
    if selected_source:
        return replace(cp, source=str(selected_source))
    return cp


def replay_speaker_evidence_unavailable(replay_observation: Mapping[str, Any]) -> bool:
    """Return True when replay marks ``selected_speaker_id`` unavailable (not silently equal)."""
    unavailable = replay_observation.get("unavailable")
    if not isinstance(unavailable, (list, tuple, set, frozenset)):
        return False
    return "selected_speaker_id" in {str(item) for item in unavailable}


def project_final_emission_for_replay(
    *,
    gm_output: Mapping[str, Any],
    resolution: Mapping[str, Any] | None = None,
    scenario_id: str = "speaker_contract_replay_parity",
    turn_index: int = 0,
    player_text: str = "",
    unavailable: Sequence[str] | None = None,
    extra_fields: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project finalized gate output through canonical golden replay observation."""
    return observed_turn_from_gate_output(
        scenario_id=scenario_id,
        gm_output=gm_output,
        resolution=resolution,
        turn_index=turn_index,
        player_text=player_text,
        unavailable=unavailable,
        extra_fields=extra_fields,
    )


def final_replay_parity_record(
    observation: SpeakerContractObservation,
    *,
    replay_observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Explicit P3/P4 comparison record for BT2 reporting."""
    final_cp = _checkpoint_by_id(observation.checkpoints, CHECKPOINT_FINAL)
    replay_cp = _checkpoint_by_id(observation.checkpoints, CHECKPOINT_REPLAY)
    if final_cp is None or replay_cp is None:
        return {
            "p3_present": final_cp is not None,
            "p4_present": replay_cp is not None,
        }
    speaker_unavailable = (
        replay_speaker_evidence_unavailable(replay_observation)
        if isinstance(replay_observation, Mapping)
        else False
    )
    return {
        "p3_final_text": final_cp.normalized_text,
        "p3_final_text_hash": final_cp.normalized_text_hash,
        "p3_emitted_speaker_signature": dict(final_cp.emitted_speaker_signature),
        "p3_resolved_speaker_id": final_cp.resolved_speaker_id,
        "p4_final_text": replay_cp.normalized_text,
        "p4_final_text_hash": replay_cp.normalized_text_hash,
        "p4_selected_speaker_id": observation.replay_selected_speaker_id,
        "p4_selected_speaker_source": observation.replay_selected_speaker_source,
        "p4_speaker_unavailable": speaker_unavailable,
        "text_hash_match": final_cp.normalized_text_hash == replay_cp.normalized_text_hash,
        "speaker_id_match": (
            not speaker_unavailable
            and final_cp.resolved_speaker_id is not None
            and observation.replay_selected_speaker_id is not None
            and final_cp.resolved_speaker_id == observation.replay_selected_speaker_id
        ),
    }


def observe_final_to_replay_speaker_contract(
    *,
    gm_output: Mapping[str, Any],
    resolution: Mapping[str, Any] | None = None,
    scenario_id: str = "speaker_contract_replay_parity",
    turn_index: int = 0,
    player_text: str = "",
    expected_speaker_id: str | None = None,
    expected_speaker_name: str | None = None,
    expected_speaker_source: str | None = None,
    enforcement_owner: str | None = None,
    unavailable: Sequence[str] | None = None,
    extra_fields: Mapping[str, Any] | None = None,
) -> SpeakerContractObservation:
    """Join P3 final emission to P4 golden replay projection and score contract risk."""
    final_text = str(gm_output.get("player_facing_text") or "")
    replay_observation = project_final_emission_for_replay(
        gm_output=gm_output,
        resolution=resolution,
        scenario_id=scenario_id,
        turn_index=turn_index,
        player_text=player_text,
        unavailable=unavailable,
        extra_fields=extra_fields,
    )
    return observe_speaker_contract(
        pre_speaker_text=final_text,
        gate_post_speaker_text=final_text,
        final_player_text=final_text,
        expected_speaker_id=expected_speaker_id,
        expected_speaker_name=expected_speaker_name,
        expected_speaker_source=expected_speaker_source,
        enforcement_owner=enforcement_owner or "game.final_emission_finalize",
        replay_observation=replay_observation,
        resolution=resolution,
        align_final_replay_normalization=True,
    )


def build_replay_checkpoint(
    replay_observation: Mapping[str, Any],
    *,
    expected_speaker_id: str | None = None,
    expected_speaker_name: str | None = None,
    resolution: Mapping[str, Any] | None = None,
) -> SpeakerCheckpoint:
    final_text = str(replay_observation.get("final_text") or "")
    return build_speaker_checkpoint(
        CHECKPOINT_REPLAY,
        final_text,
        expected_speaker_id=expected_speaker_id,
        expected_speaker_name=expected_speaker_name,
        resolution=resolution,
        source=str(replay_observation.get("selected_speaker_source") or "") or None,
        owner="golden_replay_projection",
        use_golden=True,
    )


def _layer_output_checkpoints(
    layer_events: Sequence[LayerTextDelta],
    *,
    expected_speaker_id: str | None,
    expected_speaker_name: str | None,
    resolution: Mapping[str, Any] | None,
) -> tuple[SpeakerCheckpoint, ...]:
    out: list[SpeakerCheckpoint] = []
    for event in layer_events:
        text = event.normalized_output_text
        if text is None and event.normalized_output_hash:
            text = ""
        if text is None:
            continue
        out.append(
            build_speaker_checkpoint(
                f"{_LAYER_CHECKPOINT_PREFIX}{event.layer_id}",
                text,
                expected_speaker_id=expected_speaker_id,
                expected_speaker_name=expected_speaker_name,
                resolution=resolution,
                owner=event.layer_id,
                source="post_speaker_finalize_probe",
            )
        )
    return tuple(out)


def _layer_probe_rank(layer_id: str) -> int:
    try:
        return POST_SPEAKER_PROBE_ORDER.index(layer_id)
    except ValueError:
        return len(POST_SPEAKER_PROBE_ORDER)


def _checkpoint_order_index(checkpoint_id: str) -> tuple[int, int, str]:
    if checkpoint_id == CHECKPOINT_PRE_SPEAKER:
        return (0, 0, checkpoint_id)
    if checkpoint_id == CHECKPOINT_POST_SPEAKER:
        return (1, 0, checkpoint_id)
    if checkpoint_id.startswith(_LAYER_CHECKPOINT_PREFIX):
        layer_id = checkpoint_id.removeprefix(_LAYER_CHECKPOINT_PREFIX)
        return (2, _layer_probe_rank(layer_id), checkpoint_id)
    if checkpoint_id == CHECKPOINT_FINAL:
        return (3, 0, checkpoint_id)
    if checkpoint_id == CHECKPOINT_REPLAY:
        return (4, 0, checkpoint_id)
    return (5, 0, checkpoint_id)


def _find_first_text_divergence(
    checkpoints: Sequence[SpeakerCheckpoint],
) -> str | None:
    if not checkpoints:
        return None
    prev = checkpoints[0]
    for cp in checkpoints[1:]:
        if cp.normalized_text_hash != prev.normalized_text_hash:
            return cp.checkpoint_id
        prev = cp
    return None


def _find_first_speaker_divergence(
    checkpoints: Sequence[SpeakerCheckpoint],
    *,
    expected_speaker_id: str | None,
) -> str | None:
    if not checkpoints:
        return None
    prev = checkpoints[0]
    for cp in checkpoints[1:]:
        if cp.resolved_speaker_id != prev.resolved_speaker_id and not (
            prev.checkpoint_id == CHECKPOINT_PRE_SPEAKER and cp.checkpoint_id == CHECKPOINT_POST_SPEAKER
        ):
            return cp.checkpoint_id
        if cp.speaker_status != prev.speaker_status and not (
            prev.checkpoint_id == CHECKPOINT_PRE_SPEAKER and cp.checkpoint_id == CHECKPOINT_POST_SPEAKER
        ):
            return cp.checkpoint_id
        if (
            expected_speaker_id
            and cp.checkpoint_id in {CHECKPOINT_POST_SPEAKER, CHECKPOINT_FINAL, CHECKPOINT_REPLAY}
            and cp.resolved_speaker_id
            and cp.resolved_speaker_id != expected_speaker_id
        ):
            return cp.checkpoint_id
        prev = cp
    return None


def _unified_first_divergence(
    checkpoints: Sequence[SpeakerCheckpoint],
    *,
    expected_speaker_id: str | None,
) -> tuple[str | None, str | None, str | None]:
    text_id = _find_first_text_divergence(checkpoints)
    speaker_id = _find_first_speaker_divergence(checkpoints, expected_speaker_id=expected_speaker_id)
    if text_id is None and speaker_id is None:
        return None, None, None

    candidates = [cid for cid in (text_id, speaker_id) if cid]
    unified = min(candidates, key=_checkpoint_order_index)
    layer_id = None
    if unified.startswith(_LAYER_CHECKPOINT_PREFIX):
        layer_id = unified.removeprefix(_LAYER_CHECKPOINT_PREFIX)
    return unified, text_id, speaker_id if not layer_id else None


def _checkpoint_by_id(
    checkpoints: Sequence[SpeakerCheckpoint],
    checkpoint_id: str,
) -> SpeakerCheckpoint | None:
    for cp in checkpoints:
        if cp.checkpoint_id == checkpoint_id:
            return cp
    return None


def _mismatch_present(
    *,
    checkpoints: Sequence[SpeakerCheckpoint],
    expected_speaker_id: str | None,
    replay_selected_speaker_id: str | None,
) -> bool:
    final_cp = _checkpoint_by_id(checkpoints, CHECKPOINT_FINAL)
    replay_cp = _checkpoint_by_id(checkpoints, CHECKPOINT_REPLAY)
    post_cp = _checkpoint_by_id(checkpoints, CHECKPOINT_POST_SPEAKER)

    if post_cp and final_cp and post_cp.normalized_text_hash != final_cp.normalized_text_hash:
        return True
    if final_cp and replay_cp and final_cp.normalized_text_hash != replay_cp.normalized_text_hash:
        return True
    if expected_speaker_id:
        for cp in checkpoints:
            if cp.checkpoint_id in {CHECKPOINT_POST_SPEAKER, CHECKPOINT_FINAL, CHECKPOINT_REPLAY}:
                if cp.resolved_speaker_id and cp.resolved_speaker_id != expected_speaker_id:
                    return True
    if final_cp and replay_selected_speaker_id:
        if final_cp.resolved_speaker_id and final_cp.resolved_speaker_id != replay_selected_speaker_id:
            return True
    return False


def score_speaker_contract_risk(
    observation: SpeakerContractObservation,
) -> SpeakerContractRiskScore:
    """Compute D/S/T/A component scores for one observation."""
    checkpoints = observation.checkpoints
    post_cp = _checkpoint_by_id(checkpoints, CHECKPOINT_POST_SPEAKER)
    final_cp = _checkpoint_by_id(checkpoints, CHECKPOINT_FINAL)
    replay_cp = _checkpoint_by_id(checkpoints, CHECKPOINT_REPLAY)

    mismatch = observation.mismatch_present

    d_score = 0
    if mismatch and not observation.first_divergence_checkpoint_id:
        d_score = 15

    s_score = 0
    status_counts = {
        cp.speaker_status
        for cp in checkpoints
        if cp.checkpoint_id in {CHECKPOINT_POST_SPEAKER, CHECKPOINT_FINAL, CHECKPOINT_REPLAY}
    }
    if observation.expected_speaker_id:
        for cp in (post_cp, final_cp, replay_cp):
            if cp and cp.resolved_speaker_id and cp.resolved_speaker_id != observation.expected_speaker_id:
                s_score = 40
                break
        if (
            s_score == 0
            and final_cp
            and observation.replay_selected_speaker_id
            and final_cp.resolved_speaker_id
            and final_cp.resolved_speaker_id != observation.replay_selected_speaker_id
        ):
            s_score = 40
        if s_score == 0 and status_counts <= {"resolved", "neutral"}:
            s_score = 0
        elif s_score == 0 and ("unresolved" in status_counts or "ambiguous" in status_counts):
            s_score = 20
    elif status_counts <= {"neutral"}:
        s_score = 0
    elif "unresolved" in status_counts or "ambiguous" in status_counts:
        s_score = 20

    t_score = 0
    if post_cp and final_cp and post_cp.normalized_text_hash != final_cp.normalized_text_hash:
        if observation.first_divergence_layer_id:
            t_score = 10
        else:
            t_score = 25
    if final_cp and replay_cp and final_cp.normalized_text_hash != replay_cp.normalized_text_hash:
        t_score = max(t_score, 25)

    a_score = 0
    if observation.expected_speaker_id and not observation.expected_speaker_source:
        a_score += 5
    for cp in (post_cp, final_cp):
        if cp and cp.resolved_speaker_id is None and cp.speaker_status == "resolved":
            a_score += 5
    if mismatch and not observation.enforcement_owner:
        a_score += 5
    if replay_cp is not None and observation.replay_selected_speaker_id and not observation.replay_selected_speaker_source:
        a_score += 5

    return SpeakerContractRiskScore(D=d_score, S=s_score, T=t_score, A=min(20, a_score))


def speaker_contract_family_risk_rows(
    observations: Sequence[tuple[str, SpeakerContractObservation]],
) -> list[dict[str, Any]]:
    """BT3 summary rows: family, total risk, band, divergence, speaker status, text parity, attribution."""
    rows: list[dict[str, Any]] = []
    for family, obs in observations:
        post_cp = _checkpoint_by_id(obs.checkpoints, CHECKPOINT_POST_SPEAKER)
        final_cp = _checkpoint_by_id(obs.checkpoints, CHECKPOINT_FINAL)
        status_cp = final_cp or post_cp
        text_parity = True
        if post_cp and final_cp:
            text_parity = post_cp.normalized_text_hash == final_cp.normalized_text_hash
        elif obs.mismatch_present:
            text_parity = False
        rows.append(
            {
                "family": family,
                "total": obs.risk.total,
                "band": obs.risk.band,
                "first_divergence": obs.first_divergence_checkpoint_id,
                "speaker_status": status_cp.speaker_status if status_cp else None,
                "text_parity": text_parity,
                "attribution_score": obs.risk.A,
            }
        )
    return rows


def speaker_contract_closeout_rows(
    observations: Sequence[tuple[str, str, SpeakerContractObservation, str]],
) -> list[dict[str, Any]]:
    """BT closeout rows: family risk summary plus path, D/S/T/A, owner evidence, and notes."""
    out: list[dict[str, Any]] = []
    for family, observation_path, obs, notes in observations:
        base = speaker_contract_family_risk_rows([(family, obs)])[0]
        post_cp = _checkpoint_by_id(obs.checkpoints, CHECKPOINT_POST_SPEAKER)
        final_cp = _checkpoint_by_id(obs.checkpoints, CHECKPOINT_FINAL)
        owner_present = bool(
            obs.enforcement_owner
            or obs.expected_speaker_source
            or obs.replay_selected_speaker_source
            or (post_cp and post_cp.owner)
            or (final_cp and final_cp.owner)
        )
        out.append(
            {
                **base,
                "observation_path": observation_path,
                "D": obs.risk.D,
                "S": obs.risk.S,
                "T": obs.risk.T,
                "A": obs.risk.A,
                "owner_source_evidence_present": owner_present,
                "notes": notes,
            }
        )
    return out


def observe_speaker_contract(
    *,
    pre_speaker_text: str,
    gate_post_speaker_text: str,
    final_player_text: str,
    expected_speaker_id: str | None = None,
    expected_speaker_name: str | None = None,
    expected_speaker_source: str | None = None,
    enforcement_owner: str | None = None,
    enforcement_reason: str | None = None,
    narrator_neutral: bool = False,
    layer_events: Sequence[LayerTextDelta] | None = None,
    replay_observation: Mapping[str, Any] | None = None,
    resolution: Mapping[str, Any] | None = None,
    align_final_replay_normalization: bool = False,
) -> SpeakerContractObservation:
    """Build a full speaker-contract observation and risk score."""
    events = tuple(layer_events or ())
    checkpoints: list[SpeakerCheckpoint] = [
        build_speaker_checkpoint(
            CHECKPOINT_PRE_SPEAKER,
            pre_speaker_text,
            expected_speaker_id=expected_speaker_id,
            expected_speaker_name=expected_speaker_name,
            enforcement_reason=enforcement_reason,
            narrator_neutral=narrator_neutral,
            resolution=resolution,
            source=expected_speaker_source,
            owner=enforcement_owner,
        ),
        build_speaker_checkpoint(
            CHECKPOINT_POST_SPEAKER,
            gate_post_speaker_text,
            expected_speaker_id=expected_speaker_id,
            expected_speaker_name=expected_speaker_name,
            enforcement_reason=enforcement_reason,
            narrator_neutral=narrator_neutral,
            resolution=resolution,
            source=expected_speaker_source,
            owner=enforcement_owner or "game.speaker_contract_enforcement",
        ),
    ]
    checkpoints.extend(
        _layer_output_checkpoints(
            events,
            expected_speaker_id=expected_speaker_id,
            expected_speaker_name=expected_speaker_name,
            resolution=resolution,
        )
    )
    checkpoints.append(
        build_speaker_checkpoint(
            CHECKPOINT_FINAL,
            final_player_text,
            expected_speaker_id=expected_speaker_id,
            expected_speaker_name=expected_speaker_name,
            enforcement_reason=enforcement_reason,
            narrator_neutral=narrator_neutral,
            resolution=resolution,
            source="final_emission_output",
            owner="game.final_emission_finalize",
            use_golden=align_final_replay_normalization,
        )
    )
    replay_selected_speaker_id = None
    replay_selected_speaker_source = None
    if isinstance(replay_observation, Mapping):
        replay_selected_speaker_id = replay_observation.get("selected_speaker_id")
        replay_selected_speaker_source = replay_observation.get("selected_speaker_source")
        if "final_text" in replay_observation:
            checkpoints.append(
                build_replay_projection_checkpoint(
                    replay_observation,
                    expected_speaker_id=expected_speaker_id,
                    expected_speaker_name=expected_speaker_name,
                    resolution=resolution,
                )
            )

    ordered = sorted(checkpoints, key=lambda cp: _checkpoint_order_index(cp.checkpoint_id))
    unified, text_div, speaker_div = _unified_first_divergence(
        ordered,
        expected_speaker_id=expected_speaker_id,
    )
    layer_id = first_post_speaker_normalized_divergence(list(events))
    if unified and unified.startswith(_LAYER_CHECKPOINT_PREFIX):
        layer_id = unified.removeprefix(_LAYER_CHECKPOINT_PREFIX)

    mismatch = _mismatch_present(
        checkpoints=ordered,
        expected_speaker_id=expected_speaker_id,
        replay_selected_speaker_id=str(replay_selected_speaker_id) if replay_selected_speaker_id else None,
    )

    partial = SpeakerContractObservation(
        checkpoints=tuple(ordered),
        layer_events=events,
        expected_speaker_id=expected_speaker_id,
        expected_speaker_source=expected_speaker_source,
        enforcement_owner=enforcement_owner,
        replay_selected_speaker_id=str(replay_selected_speaker_id) if replay_selected_speaker_id else None,
        replay_selected_speaker_source=str(replay_selected_speaker_source) if replay_selected_speaker_source else None,
        first_text_divergence_checkpoint_id=text_div,
        first_speaker_divergence_checkpoint_id=speaker_div,
        first_divergence_checkpoint_id=unified,
        first_divergence_layer_id=layer_id,
        mismatch_present=mismatch,
        risk=SpeakerContractRiskScore(D=0, S=0, T=0, A=0),
    )
    return SpeakerContractObservation(
        checkpoints=partial.checkpoints,
        layer_events=partial.layer_events,
        expected_speaker_id=partial.expected_speaker_id,
        expected_speaker_source=partial.expected_speaker_source,
        enforcement_owner=partial.enforcement_owner,
        replay_selected_speaker_id=partial.replay_selected_speaker_id,
        replay_selected_speaker_source=partial.replay_selected_speaker_source,
        first_text_divergence_checkpoint_id=partial.first_text_divergence_checkpoint_id,
        first_speaker_divergence_checkpoint_id=partial.first_speaker_divergence_checkpoint_id,
        first_divergence_checkpoint_id=partial.first_divergence_checkpoint_id,
        first_divergence_layer_id=partial.first_divergence_layer_id,
        mismatch_present=partial.mismatch_present,
        risk=score_speaker_contract_risk(partial),
    )
