"""Golden replay speaker projection parity (CE5)."""
from __future__ import annotations

from typing import Any, Literal, Mapping

from game.final_emission_speaker_observation import read_final_speaker_observation

from tests.helpers.golden_replay_projection_fields import _first_present
from tests.helpers.transcript_runner import latest_target_id, latest_target_source

SpeakerProjectionParityStatus = Literal[
    "aligned",
    "final_unresolved",
    "final_ambiguous",
    "mismatch",
    "missing_final_observation",
]
def read_final_speaker_observation_for_replay(
    emission_debug_lane: Mapping[str, Any] | None,
    *,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Read BX2 ``final_speaker_observation`` for replay parity projection.

    Prefers the emission-debug lane when stamped there, then falls back to
    ``gm_output.metadata.emission_debug`` (BX2 finalize attachment path).
    """
    if isinstance(emission_debug_lane, Mapping):
        obs = emission_debug_lane.get("final_speaker_observation")
        if isinstance(obs, Mapping):
            return dict(obs)
    if isinstance(payload, Mapping):
        gm = payload.get("gm_output")
        if isinstance(gm, Mapping):
            stamped = read_final_speaker_observation(gm)
            if stamped is not None:
                return stamped
        stamped = read_final_speaker_observation(payload)
        if stamped is not None:
            return stamped
    return None


def _clean_replay_speaker_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def project_speaker_projection_parity(
    *,
    selected_speaker_id: Any,
    selected_speaker_source: str | None,
    emission_debug_lane: Mapping[str, Any] | None,
    payload: Mapping[str, Any] | None = None,
    final_speaker_observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare replay-selected speaker against BX2 final-emission speaker stamp.

    Read-side only; does not mutate routing or reconcile state. Legacy
    ``selected_speaker_id`` / ``selected_speaker_source`` remain unchanged on the
    observed turn — this payload records agreement or disagreement explicitly.
    """
    notes: list[str] = []
    selected_id = _clean_replay_speaker_id(selected_speaker_id)
    fso: dict[str, Any] | None
    if isinstance(final_speaker_observation, Mapping):
        fso = dict(final_speaker_observation)
    else:
        fso = read_final_speaker_observation_for_replay(
            emission_debug_lane,
            payload=payload,
        )

    if fso is None:
        return {
            "status": "missing_final_observation",
            "selected_speaker_id": selected_id,
            "final_observed_speaker_id": None,
            "final_observed_status": None,
            "final_observed_candidates": [],
            "selected_speaker_source": selected_speaker_source,
            "notes": ["final_speaker_observation_absent"],
        }

    final_status = str(fso.get("status") or "").strip().lower()
    final_observed_id = _clean_replay_speaker_id(fso.get("canonical_speaker_id"))
    raw_candidates = fso.get("candidates")
    candidates = (
        [str(item) for item in raw_candidates if str(item).strip()]
        if isinstance(raw_candidates, list)
        else []
    )

    parity_status: SpeakerProjectionParityStatus

    if final_status == "resolved":
        if selected_id == final_observed_id:
            parity_status = "aligned"
            notes.append("selected_matches_canonical_speaker_id")
        else:
            parity_status = "mismatch"
            notes.append("selected_differs_from_canonical_speaker_id")
    elif final_status == "ambiguous":
        parity_status = "final_ambiguous"
        notes.append("final_emission_speaker_ambiguous")
        if selected_id is not None:
            notes.append("replay_selected_speaker_legacy_preserved")
    elif final_status == "unresolved":
        parity_status = "final_unresolved"
        notes.append("final_emission_speaker_unresolved")
        if selected_id is not None:
            notes.append("replay_selected_speaker_legacy_preserved")
    elif final_status in {"neutral", "unattributed"}:
        if selected_id is not None:
            parity_status = "mismatch"
            notes.append(f"final_status_{final_status}_but_replay_selected_present")
        else:
            parity_status = "aligned"
            notes.append(f"final_status_{final_status}_no_replay_selection_required")
    else:
        parity_status = "missing_final_observation"
        notes.append(f"unrecognized_final_status_{final_status or 'empty'}")

    return {
        "status": parity_status,
        "selected_speaker_id": selected_id,
        "final_observed_speaker_id": final_observed_id,
        "final_observed_status": final_status or None,
        "final_observed_candidates": candidates,
        "selected_speaker_source": selected_speaker_source,
        "notes": notes,
    }


def _resolve_selected_speaker_id(
    *,
    social_contract_trace: Mapping[str, Any],
    snap: Mapping[str, Any],
    social: Mapping[str, Any],
) -> tuple[Any, str | None]:
    selected_speaker_id = _first_present(
        social_contract_trace,
        ("final_reply_owner", "reply_owner_actor_id", "visible_grounded_speaker"),
    )
    selected_speaker_source = "turn_trace.social_contract_trace" if selected_speaker_id else None
    if selected_speaker_id is None:
        selected_speaker_id = latest_target_id(snap)
        selected_speaker_source = latest_target_source(snap)
    if selected_speaker_id is None:
        selected_speaker_id = social.get("npc_id")
        selected_speaker_source = "resolution.social.npc_id" if selected_speaker_id else None
    return selected_speaker_id, selected_speaker_source
