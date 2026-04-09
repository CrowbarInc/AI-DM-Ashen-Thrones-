"""gm_retry context-separation contract consumption and retry steering (no gate duplication)."""
from __future__ import annotations

import pytest

from game.context_separation import build_context_separation_contract
from game.gm import build_retry_prompt_for_failure
import game.gm_retry as gm_retry

pytestmark = pytest.mark.unit


def _minimal_cs_contract(**overrides: object) -> dict:
    c = build_context_separation_contract(
        resolution={"kind": "barter"},
        player_text="What does it cost?",
    )
    assert isinstance(c, dict)
    return {**c, **overrides}  # type: ignore[misc]


def test_retry_resolves_contract_from_response_policy() -> None:
    c = _minimal_cs_contract()
    pol = {"context_separation_contract": c}
    got, src = gm_retry._resolve_context_separation_contract_for_retry(None, pol)
    assert got is c
    assert src == "response_policy.context_separation_contract"


def test_retry_resolves_contract_from_prompt_payload_mirror() -> None:
    c = _minimal_cs_contract()
    gm = {"prompt_payload": {"response_policy": {"context_separation": c}}}
    got, src = gm_retry._resolve_context_separation_contract_for_retry(gm, None)
    assert got is c
    assert src == "prompt_payload.response_policy"


def test_retry_resolves_contract_from_metadata_emission_debug() -> None:
    c = _minimal_cs_contract()
    gm = {"metadata": {"emission_debug": {"context_separation_contract": c}}}
    got, src = gm_retry._resolve_context_separation_contract_for_retry(gm, None)
    assert got is c
    assert src == "metadata.emission_debug"


def test_retry_resolves_contract_from_trace_emission_debug() -> None:
    c = _minimal_cs_contract()
    gm = {"trace": {"emission_debug": {"context_separation": c}}}
    got, src = gm_retry._resolve_context_separation_contract_for_retry(gm, None)
    assert src == "trace.emission_debug"


def test_prior_trouble_from_repaired_marker_and_nested_validation() -> None:
    gm = {
        "_final_emission_meta": {"context_separation_repaired": True},
        "metadata": {
            "emission_debug": {
                "context_separation": {
                    "validation": {"passed": False},
                    "failure_reasons": ["topic_hijack_background_pressure"],
                }
            }
        },
    }
    trouble, sigs = gm_retry.prior_context_separation_trouble_signals(gm)
    assert trouble is True
    assert any("repaired" in s for s in sigs)
    assert any("validation_failed" in s for s in sigs)


def test_default_recovery_suppresses_broad_pressure_after_cs_trouble() -> None:
    gm = {"metadata": {"context_separation_repaired": True}}
    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=gm,
    ).lower()
    assert "local-first recovery" in p
    assert "broad unrest" in p
    assert "open with" in p


def test_gm_retry_does_not_import_context_separation_validator() -> None:
    assert not hasattr(gm_retry, "validate_context_separation")
    src = open(gm_retry.__file__, encoding="utf-8").read()
    assert "validate_context_separation" not in src
    assert "_repair_context_separation" not in src


def test_pressure_color_subordinate_without_trouble() -> None:
    c = _minimal_cs_contract()
    gm = {"context_separation_contract": c}
    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=gm,
    ).lower()
    assert "ambient pressure may briefly color" in p
    assert "subordinate" in p or "contract marks" in p


def test_pressure_focus_allowed_skips_one_clause_compression() -> None:
    c = _minimal_cs_contract()
    c.setdefault("debug_flags", {})["pressure_focus_allowed"] = True
    gm = {
        "context_separation_contract": c,
        "metadata": {"context_separation_failed": True},
    }
    p = build_retry_prompt_for_failure(
        {"failure_class": "scene_stall"},
        response_policy=None,
        gm_output=gm,
    ).lower()
    assert "pressure focus" in p
    assert "one short ambient-pressure clause" not in p
    assert "interaction-linked" in p


def test_tone_protection_line_present() -> None:
    p = build_retry_prompt_for_failure(
        {"failure_class": "echo_or_repetition"},
        response_policy=None,
        gm_output=None,
    ).lower()
    assert "do not escalate harshness" in p
    assert "tone caps" in p


def test_retry_debug_sink_populated() -> None:
    c = _minimal_cs_contract()
    sink: dict = {}
    build_retry_prompt_for_failure(
        {"failure_class": "npc_contract_failure", "missing": []},
        response_policy={"context_separation_contract": c},
        gm_output=None,
        retry_debug_sink=sink,
    )
    assert sink.get("retry_context_separation_contract_resolved") is True
    assert sink.get("retry_context_separation_contract_source") == "response_policy.context_separation_contract"
    assert isinstance(sink.get("retry_context_separation_guidance"), str)
