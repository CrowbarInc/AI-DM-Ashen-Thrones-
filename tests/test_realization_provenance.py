"""Metadata-only provenance tests for realization fallback families."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GPT_BUDGET_OR_PROVIDER_FAILURE,
    LEGACY_UNCLASSIFIED,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    RETRY_TERMINAL_FALLBACK,
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    UPSTREAM_PREPARED_EMISSION,
    attach_realization_fallback_family,
    normalize_realization_fallback_family,
)
from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_EMISSION_KEY,
    build_upstream_prepared_emission_payload,
    build_upstream_prepared_opening_fallback_payload,
    merge_upstream_prepared_emission_into_gm_output,
)
from tests.helpers.opening_fallback_evidence import opening_gm_output

pytestmark = pytest.mark.unit


def _assert_known_family(value: str) -> None:
    assert value in FALLBACK_FAMILIES


def test_normalize_realization_fallback_family_defaults_ambiguous_to_legacy_unclassified() -> None:
    assert normalize_realization_fallback_family("not_a_family") == LEGACY_UNCLASSIFIED
    meta: dict = {}
    attach_realization_fallback_family(meta, "not_a_family")
    assert meta[REALIZATION_FALLBACK_FAMILY_FIELD] == LEGACY_UNCLASSIFIED


def test_upstream_prepared_payload_has_upstream_family_not_gate_terminal() -> None:
    payload = build_upstream_prepared_emission_payload(
        resolution={"kind": "observe", "prompt": "I look around."},
        session={"active_scene_id": "s"},
        world={},
        scene_id="s",
    )
    family = payload[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == UPSTREAM_PREPARED_EMISSION
    assert family != "gate_terminal_repair"


def test_merge_upstream_prepared_overrides_legacy_unclassified_for_known_path() -> None:
    gm = {
        UPSTREAM_PREPARED_EMISSION_KEY: {
            "prepared_answer_fallback_text": "OVERRIDE.",
            REALIZATION_FALLBACK_FAMILY_FIELD: LEGACY_UNCLASSIFIED,
        }
    }
    merge_upstream_prepared_emission_into_gm_output(
        gm,
        resolution={"kind": "observe", "prompt": "x"},
        session={},
        world={},
        scene_id="s",
    )
    family = gm[UPSTREAM_PREPARED_EMISSION_KEY][REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == UPSTREAM_PREPARED_EMISSION
    assert family != LEGACY_UNCLASSIFIED


def test_call_gpt_provider_failure_metadata_has_provider_family(monkeypatch) -> None:
    import game.gm as gm

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(
        gm,
        "resolve_model_route",
        lambda **_: SimpleNamespace(
            selected_model="test-model",
            route_family="test",
            route_reason="test",
        ),
    )

    class RaisingOpenAI:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("provider down")

    import types

    monkeypatch.setitem(__import__("sys").modules, "openai", types.SimpleNamespace(OpenAI=RaisingOpenAI))
    out = gm.call_gpt([{"role": "user", "content": "hello"}])
    family = out["metadata"][REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == GPT_BUDGET_OR_PROVIDER_FAILURE


def test_retry_terminal_fallback_has_retry_family_not_upstream_prepared() -> None:
    from game.gm_retry import force_terminal_retry_fallback

    out = force_terminal_retry_fallback(
        session={"active_scene_id": "s"},
        original_text="",
        failure={"failure_class": "validator_voice", "reasons": ["empty"]},
        retry_failures=[],
        player_text="I wait.",
        scene_envelope={"scene": {"id": "s", "location": "Crossroad", "visible_facts": []}},
        world={},
        resolution={"kind": "observe", "prompt": "I wait."},
        base_gm={"player_facing_text": "", "tags": [], "metadata": {}},
    )
    family = out[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == RETRY_TERMINAL_FALLBACK
    assert family != UPSTREAM_PREPARED_EMISSION
    assert out["metadata"][REALIZATION_FALLBACK_FAMILY_FIELD] == RETRY_TERMINAL_FALLBACK


def test_strict_social_internal_fallback_details_have_strict_social_family() -> None:
    from game.social_exchange_emission import build_final_strict_social_response

    text, details = build_final_strict_social_response(
        "The scene holds in silence.",
        resolution={
            "kind": "question",
            "prompt": "Who did this?",
            "social": {"npc_id": "guard", "npc_name": "Guard"},
        },
        tags=[],
        session={"active_scene_id": "gate"},
        scene_id="gate",
        world={"npcs": [{"id": "guard", "name": "Guard", "location": "gate"}]},
    )
    assert text
    family = details[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_family(family)
    assert family == STRICT_SOCIAL_DETERMINISTIC_FALLBACK


def test_upstream_prepared_opening_payload_stamps_realization_family_distinct_from_diegetic() -> None:
    """Opening upstream payload carries both taxonomies without collapsing them."""
    payload = build_upstream_prepared_opening_fallback_payload(opening_gm_output())
    comp = payload["opening_fallback_composition_meta"]
    assert comp["fallback_family_used"] == "scene_opening"
    assert payload[REALIZATION_FALLBACK_FAMILY_FIELD] == UPSTREAM_PREPARED_EMISSION
    assert comp["fallback_family_used"] != payload[REALIZATION_FALLBACK_FAMILY_FIELD]
    assert payload[REALIZATION_FALLBACK_FAMILY_FIELD] in FALLBACK_FAMILIES
