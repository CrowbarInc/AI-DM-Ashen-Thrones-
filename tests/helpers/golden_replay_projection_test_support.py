"""Shared fixtures for golden replay projection test suites (CF5 split)."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from game.ownership_projection_views import (
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
)

from tests.helpers.golden_replay_fixtures import fem_payload, minimal_gm_output_payload
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED


def load_manifest_refresh_tool():
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "refresh_protected_replay_manifest",
        root / "tools" / "refresh_protected_replay_manifest.py",
    )
    assert spec is not None and spec.loader is not None
    refresh_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_mod)
    return refresh_mod


def speaker_parity_turn_payload(
    *,
    scenario_id: str,
    selected_speaker_id: str | None,
    final_speaker_observation: dict[str, Any] | None,
    gm_text: str = 'Guard Captain says, "Posted at dawn."',
) -> dict[str, Any]:
    from tests.helpers.golden_replay_fixtures import minimal_turn_payload

    gm_output: dict[str, Any] = {
        "player_facing_text": gm_text,
        "_final_emission_meta": {"final_emitted_source": "generated_candidate"},
    }
    if final_speaker_observation is not None:
        gm_output["metadata"] = {
            "emission_debug": {"final_speaker_observation": final_speaker_observation}
        }
    social_trace: dict[str, Any] = {}
    if selected_speaker_id:
        social_trace["final_reply_owner"] = selected_speaker_id
    return minimal_turn_payload(
        scenario_id=scenario_id,
        gm_text=gm_text,
        resolution={"kind": "question", "social": {"npc_id": selected_speaker_id}},
        payload={
            "gm_output": gm_output,
            "debug_traces": [
                {
                    "turn_trace": {
                        "social_contract_trace": {
                            "route_selected": "dialogue",
                            **social_trace,
                        }
                    }
                }
            ],
        },
    )


def ak5_rich_projection_payload() -> dict[str, Any]:
    rich_payload = minimal_gm_output_payload(
        fem_meta=fem_payload(
            final_emitted_source="upstream_prepared_emission",
            response_type_required="dialogue_response",
            response_type_repair_used=True,
            response_type_repair_kind="dialogue_minimal_repair",
            fallback_temporal_frame="present",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            fallback_family_used="social",
            realization_fallback_family="upstream_prepared_emission",
            opening_recovered_via_fallback=False,
            opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
            sealed_fallback_owner_bucket="unknown-none",
            visibility_fallback_owner_bucket="unknown-none",
        ),
        metadata={
            "sanitizer_trace": {
                "sanitizer_lineage_mode": "strip_only",
                "sanitizer_empty_fallback_used": True,
                "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                "sanitizer_lineage_changed_count": 1,
                "sanitizer_lineage_dropped_count": 0,
                "sanitizer_lineage_empty_fallback_used": True,
                "sanitizer_lineage_legacy_rewrite_active": False,
                "sanitizer_strict_social_fallback_used": False,
            }
        },
    )
    rich_payload["sanitizer_debug"] = [
        {"event": "strip_only_dropped_rewrite_candidate", "sentence": "Planner scaffold."},
    ]
    rich_payload["debug_traces"] = [
        {
            "canonical_entry": {
                "target_actor_id": "runner",
                "target_source": "social",
                "reason": "direct_vocative",
            },
            "turn_trace": {
                "social_contract_trace": {"route_selected": "dialogue"},
            },
        }
    ]
    return rich_payload
