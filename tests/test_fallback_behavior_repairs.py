"""Downstream fallback-consumer coverage.

This suite validates how repaired outputs are consumed by fallback,
gate, and retry systems.

It does NOT own repair semantics. All repair derivation, helper logic,
and materialization behavior are owned by:

```
tests/test_final_emission_repairs.py
```

This file owns downstream consumer behavior for shipped ``fallback_behavior``
metadata. Failures here should point first to
``game.response_policy_enforcement.apply_response_policy_enforcement`` (``game.gm`` re-export),
``game.gm_retry.build_retry_prompt_for_failure``, or the ``game.gm_retry``
fallback/debug metadata consumption path.

It should not duplicate detailed validator/repair predicate ownership except
where needed for end-to-end metadata observation.

"""
from __future__ import annotations

from game.final_emission_meta import read_final_emission_meta_dict

import pytest

from game.final_emission_gate import apply_final_emission_gate
from game.gm import apply_response_policy_enforcement
from tests.helpers.fallback_behavior_fixtures import answer_contract, fallback_contract
from tests.helpers.final_emission_gate_fixtures import response_type_contract
from game.gm_retry import build_retry_prompt_for_failure


pytestmark = pytest.mark.unit


def test_downstream_retry_observes_shipped_fallback_contract_and_final_emission_meta() -> None:
    contract = fallback_contract()
    gm = apply_response_policy_enforcement(
        {"player_facing_text": "The line inches forward."},
        response_policy={"fallback_behavior": contract},
        player_text="Who did it?",
        scene_envelope={"scene": {"id": "frontier_gate"}},
        session={},
        world={},
        resolution={"kind": "adjudication_query", "prompt": "Who did it?"},
    )

    emitted_contract = ((gm.get("metadata") or {}).get("emission_debug") or {}).get("fallback_behavior_contract") or {}
    assert emitted_contract.get("enabled") is True
    assert emitted_contract.get("uncertainty_active") is True
    assert emitted_contract.get("prefer_partial_over_question") is True

    retry_debug: dict = {}
    gm_with_meta = dict(gm)
    gm_with_meta["_final_emission_meta"] = {
        "fallback_behavior_checked": True,
        "fallback_behavior_failed": True,
        "fallback_behavior_repaired": True,
        "fallback_behavior_skip_reason": None,
        "fallback_behavior_failure_reasons": ["missing_allowed_fallback_shape"],
    }
    build_retry_prompt_for_failure(
        {"failure_class": "scene_stall", "reasons": ["test"]},
        response_policy=gm.get("response_policy"),
        gm_output=gm_with_meta,
        retry_debug_sink=retry_debug,
        player_text="Who did it?",
    )

    assert retry_debug.get("retry_fallback_behavior_contract_present") is True
    assert retry_debug.get("retry_fallback_behavior_uncertainty_active") is True
    assert retry_debug.get("retry_fallback_behavior_checked") is True
    assert retry_debug.get("retry_fallback_behavior_repaired") is True
    assert retry_debug.get("retry_fallback_behavior_failure_reasons") == [
        "missing_allowed_fallback_shape"
    ]


def test_retry_consumer_prefers_upstream_fallback_meta_over_nested_debug_noise() -> None:
    retry_debug: dict = {}
    build_retry_prompt_for_failure(
        {"failure_class": "scene_stall", "reasons": ["test"]},
        response_policy={"fallback_behavior": fallback_contract()},
        gm_output={
            "response_policy": {"fallback_behavior": fallback_contract(uncertainty_active=False)},
            "_final_emission_meta": {
                "fallback_behavior_checked": False,
                "fallback_behavior_failed": True,
                "fallback_behavior_repaired": False,
                "fallback_behavior_skip_reason": "upstream_skip",
                "fallback_behavior_failure_reasons": ["residual_shape_gap"],
            },
            "metadata": {
                "emission_debug": {
                    "fallback_behavior": {
                        "validation": {"checked": True, "passed": True},
                        "skip_reason": "conflicting_nested_value",
                    }
                }
            },
        },
        retry_debug_sink=retry_debug,
        player_text="No. Exactly who?",
    )

    assert retry_debug.get("retry_fallback_behavior_contract_present") is True
    assert retry_debug.get("retry_fallback_behavior_uncertainty_active") is True
    assert retry_debug.get("retry_fallback_behavior_checked") is False
    assert retry_debug.get("retry_fallback_behavior_failed") is True
    assert retry_debug.get("retry_fallback_behavior_repaired") is False
    assert retry_debug.get("retry_fallback_behavior_skip_reason") == "upstream_skip"
    assert retry_debug.get("retry_fallback_behavior_failure_reasons") == ["residual_shape_gap"]


def test_downstream_gate_observesanswer_contract_meta_when_output_exhibits_smoothed_fallback_shape() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "No names yet. Check the ward clerk at the east gate office. "
                "I don't have enough information to answer confidently."
            ),
            "tags": [],
            "response_policy": {
                "response_type_contract": response_type_contract("answer"),
                "answer_completeness": answer_contract(),
                "fallback_behavior": fallback_contract(),
            },
        },
        resolution={"kind": "adjudication_query", "prompt": "No. Exactly who?"},
        session={},
        scene_id="frontier_gate",
        scene={},
        world={},
    )

    meta = read_final_emission_meta_dict(out) or {}
    emission_debug = ((out.get("metadata") or {}).get("emission_debug") or {}).get("fallback_behavior") or {}
    text = str(out.get("player_facing_text") or "")

    # Consumer ownership: downstream can observe shipped answer/fallback metadata
    # and a player-facing result. Predicate and repair details live in owner suites.
    assert meta.get("response_type_required") == "answer"
    assert meta.get("fallback_behavior_repaired") is True
    assert emission_debug.get("validation", {}).get("checked") is True
    assert text.strip()
