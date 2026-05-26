from __future__ import annotations

from typing import Any, Dict

import pytest

import game.final_emission_gate as final_emission_gate
import game.final_emission_opening_fallback as opening_fallback
from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    opening_fallback_owner_bucket_from_fields,
)
from game.opening_deterministic_fallback import OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
from game.upstream_response_repairs import (
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
)


pytestmark = pytest.mark.unit

PREPARED_TEXT = "Rain glints on the checkpoint stones while a queue waits beneath the gate."


def _fail_closed_composition_meta() -> Dict[str, Any]:
    return {
        "first_mention_composition_used": False,
        "first_mention_composition_layers": {"environment": None, "motion": None, "entities": []},
    }


def _prepared_payload() -> Dict[str, Any]:
    return {
        "prepared_opening_fallback_text": PREPARED_TEXT,
        "opening_fallback_meta": {"opening_fallback_failed_closed": False},
        "opening_fallback_composition_meta": {
            "fallback_family_used": "scene_opening",
            "fallback_temporal_frame": "first_impression",
            "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        },
    }


def _select(gm_output: Dict[str, Any]) -> tuple[str, str, str, str, str, str, Dict[str, Any]]:
    return opening_fallback._opening_scene_safe_fallback_tuple(
        gm_output,
        fail_closed_composition_meta_factory=_fail_closed_composition_meta,
    )


def _owner_bucket(meta: Dict[str, Any], *, repair_kind: str) -> str:
    return opening_fallback_owner_bucket_from_fields(
        final_emitted_source="opening_deterministic_fallback",
        opening_recovered_via_fallback=True,
        opening_fallback_authorship_source=meta.get("opening_fallback_authorship_source"),
        response_type_repair_kind=repair_kind,
        fallback_family=meta.get("fallback_family_used"),
        fallback_temporal_frame=meta.get("fallback_temporal_frame"),
    )


def test_adapter_selects_usable_upstream_prepared_payload_unchanged() -> None:
    payload = _prepared_payload()
    gm_output = {UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: payload}

    selected = opening_fallback._opening_scene_safe_fallback_tuple(
        gm_output,
        fail_closed_composition_meta_factory=lambda: pytest.fail("prepared selection must not build fail-closed meta"),
    )

    text, pool, kind, emitted_source, strategy, candidate_source, meta = selected
    assert text == PREPARED_TEXT
    assert (pool, kind, emitted_source, strategy, candidate_source) == (
        "scene_opening_deterministic",
        "opening_deterministic_fallback",
        "opening_deterministic_fallback",
        "opening_scene_safe_fallback",
        "opening_deterministic_fallback",
    )
    assert meta == payload["opening_fallback_composition_meta"]
    assert meta is not payload["opening_fallback_composition_meta"]
    assert meta["opening_fallback_authorship_source"] == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    assert _owner_bucket(meta, repair_kind=kind) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_adapter_missing_upstream_payload_fails_closed_with_existing_metadata_shape() -> None:
    _text, _pool, kind, _emitted_source, _strategy, _candidate_source, meta = _select(
        {"opening_curated_facts": ["Rain needles the stones at the gate."]}
    )

    assert _text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    assert kind == "opening_deterministic_fallback"
    assert meta["opening_fallback_failed_closed"] is True
    assert meta["opening_fallback_missing_upstream_prepared_payload"] is True
    assert meta["opening_fallback_missing_curated_facts"] is False
    assert meta["opening_fallback_basis_count"] == 1
    assert meta["opening_fallback_authorship_source"] is None
    assert meta["fallback_family_used"] == "scene_opening"
    assert meta["fallback_temporal_frame"] == "first_impression"
    assert (
        _owner_bucket(meta, repair_kind="opening_deterministic_fallback_failed_closed")
        == OPENING_FALLBACK_OWNER_SEALED_GATE
    )


def test_adapter_insufficient_curated_facts_fails_closed_with_existing_metadata_shape() -> None:
    text, _pool, _kind, _emitted_source, _strategy, _candidate_source, meta = _select(
        {"opening_curated_facts": []}
    )

    assert text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    assert meta["opening_fallback_failed_closed"] is True
    assert meta["opening_fallback_missing_upstream_prepared_payload"] is True
    assert meta["opening_fallback_compatibility_local_disabled"] is True
    assert meta["opening_fallback_context_missing"] is True
    assert meta["opening_curated_facts_present"] is False
    assert meta["opening_curated_facts_count"] == 0
    assert meta["opening_fallback_authorship_source"] is None
    assert (
        _owner_bucket(meta, repair_kind="opening_deterministic_fallback_failed_closed")
        == OPENING_FALLBACK_OWNER_SEALED_GATE
    )


def test_adapter_unusable_upstream_stub_preserves_fail_closed_metadata() -> None:
    text, _pool, _kind, _emitted_source, _strategy, _candidate_source, meta = _select(
        {
            "opening_curated_facts": ["Rain needles the stones at the gate."],
            UPSTREAM_PREPARED_OPENING_FALLBACK_KEY: {"prepared_opening_fallback_text": PREPARED_TEXT},
        }
    )

    assert text == OPENING_FALLBACK_EMPTY_CURATED_FACTS_MARKER
    assert meta["opening_fallback_failed_closed"] is True
    assert meta["opening_fallback_upstream_payload_unusable"] is True
    assert meta["opening_fallback_upstream_payload_recovered"] is False
    assert meta["opening_fallback_missing_upstream_prepared_payload"] is False
    assert meta["opening_fallback_compatibility_local_disabled"] is True
    assert meta["opening_fallback_authorship_source"] is None
    assert (
        _owner_bucket(meta, repair_kind="opening_deterministic_fallback_failed_closed")
        == OPENING_FALLBACK_OWNER_SEALED_GATE
    )


def test_adapter_does_not_export_prose_authorship_or_payload_packaging() -> None:
    assert not hasattr(opening_fallback, "deterministic_opening_fallback_text_and_meta")
    assert not hasattr(opening_fallback, "build_upstream_prepared_opening_fallback_payload")


def test_gate_opening_tuple_wrapper_delegates_to_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = ("text", "pool", "kind", "emitted", "strategy", "candidate", {"meta": True})
    captured: Dict[str, Any] = {}

    def fake_adapter(
        gm_output: Dict[str, Any],
        *,
        fail_closed_composition_meta_factory: Any,
    ) -> tuple[str, str, str, str, str, str, Dict[str, Any]]:
        captured["gm_output"] = gm_output
        captured["meta_factory"] = fail_closed_composition_meta_factory
        return sentinel

    monkeypatch.setattr(final_emission_gate, "_opening_scene_safe_fallback_tuple_from_adapter", fake_adapter)
    gm_output = {"opening_curated_facts": []}

    assert final_emission_gate._opening_scene_safe_fallback_tuple(gm_output) == sentinel
    assert captured["gm_output"] is gm_output
    assert captured["meta_factory"] is final_emission_gate._first_mention_composition_meta
