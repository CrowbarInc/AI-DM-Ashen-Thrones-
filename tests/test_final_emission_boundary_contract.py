"""Tests for ``game.final_emission_boundary_contract`` (Block B + D integration)."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from game.final_emission_boundary_contract import (
    LEGALITY_ALLOWED,
    LEGALITY_ALLOWED_KIND,
    PACKAGING_ALLOWED,
    PACKAGING_ALLOWED_KIND,
    SEMANTIC_DISALLOWED,
    SEMANTIC_DISALLOWED_KIND,
    assert_final_emission_mutation_allowed,
    classify_final_emission_mutation,
    is_legality_allowed,
    is_packaging_allowed,
    is_semantic_disallowed,
)


@pytest.mark.parametrize("kind", sorted(PACKAGING_ALLOWED))
def test_packaging_kinds_classify_as_packaging_allowed(kind: str) -> None:
    assert classify_final_emission_mutation(kind) == PACKAGING_ALLOWED_KIND


@pytest.mark.parametrize("kind", sorted(LEGALITY_ALLOWED))
def test_legality_kinds_classify_as_legality_allowed(kind: str) -> None:
    assert classify_final_emission_mutation(kind) == LEGALITY_ALLOWED_KIND


@pytest.mark.parametrize("kind", sorted(SEMANTIC_DISALLOWED))
def test_semantic_kinds_classify_as_semantic_disallowed(kind: str) -> None:
    assert classify_final_emission_mutation(kind) == SEMANTIC_DISALLOWED_KIND


@pytest.mark.parametrize("kind", sorted(PACKAGING_ALLOWED | LEGALITY_ALLOWED))
def test_assert_allows_packaging_and_legality(kind: str) -> None:
    assert_final_emission_mutation_allowed(kind, source="test")


@pytest.mark.parametrize("kind", sorted(SEMANTIC_DISALLOWED))
def test_assert_rejects_semantic_disallowed(kind: str) -> None:
    with pytest.raises(AssertionError) as excinfo:
        assert_final_emission_mutation_allowed(kind, source="test_layer")
    msg = str(excinfo.value)
    assert kind in msg
    assert "test_layer" in msg
    assert "semantic repair must occur upstream" in msg


@pytest.mark.parametrize("kind", ("not_a_real_mutation", "", "repair_narrative"))
def test_unknown_kind_classify_raises(kind: str) -> None:
    with pytest.raises(ValueError, match="unknown final-emission mutation kind"):
        classify_final_emission_mutation(kind)


@pytest.mark.parametrize("kind", ("not_a_real_mutation", "", "repair_narrative"))
def test_unknown_kind_assert_raises(kind: str) -> None:
    with pytest.raises(ValueError, match="unknown final-emission mutation kind"):
        assert_final_emission_mutation_allowed(kind, source="unknown_source")


def test_unknown_kind_assert_message_includes_source() -> None:
    with pytest.raises(ValueError) as excinfo:
        assert_final_emission_mutation_allowed("bogus", source="gate.foo")
    assert "bogus" in str(excinfo.value)
    assert "gate.foo" in str(excinfo.value)


def test_is_helpers_match_membership() -> None:
    for k in PACKAGING_ALLOWED:
        assert is_packaging_allowed(k) is True
        assert is_legality_allowed(k) is False
        assert is_semantic_disallowed(k) is False
    for k in LEGALITY_ALLOWED:
        assert is_packaging_allowed(k) is False
        assert is_legality_allowed(k) is True
        assert is_semantic_disallowed(k) is False
    for k in SEMANTIC_DISALLOWED:
        assert is_packaging_allowed(k) is False
        assert is_legality_allowed(k) is False
        assert is_semantic_disallowed(k) is True
    assert is_packaging_allowed("unknown") is False
    assert is_legality_allowed("unknown") is False
    assert is_semantic_disallowed("unknown") is False


REPO_ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = REPO_ROOT / "game" / "final_emission_gate.py"
REPAIRS_PATH = REPO_ROOT / "game" / "final_emission_repairs.py"

_ASSERT_MUTATION_KIND_RE = re.compile(
    r"assert_final_emission_mutation_allowed\(\s*(?:\n\s*)?[\"']([a-zA-Z0-9_]+)[\"']",
)


def _mutation_kinds_used_in_sources() -> list[str]:
    kinds: list[str] = []
    for path in (GATE_PATH, REPAIRS_PATH):
        src = path.read_text(encoding="utf-8")
        kinds.extend(_ASSERT_MUTATION_KIND_RE.findall(src))
    # stable dedupe
    return list(dict.fromkeys(kinds))


def test_final_emission_gate_imports_assert_final_emission_mutation_allowed() -> None:
    gate_src = GATE_PATH.read_text(encoding="utf-8")
    assert "from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed" in gate_src
    assert "assert_final_emission_mutation_allowed(" in gate_src


def test_final_emission_repairs_imports_assert_for_subtractive_strips() -> None:
    repairs_src = REPAIRS_PATH.read_text(encoding="utf-8")
    assert "from game.final_emission_boundary_contract import assert_final_emission_mutation_allowed" in repairs_src


def test_assert_sites_never_use_semantic_disallowed_kinds() -> None:
    kinds = _mutation_kinds_used_in_sources()
    assert kinds, "expected assert_final_emission_mutation_allowed(...) call sites in gate/repairs"
    for kind in kinds:
        assert kind not in SEMANTIC_DISALLOWED, (
            f"mutation kind {kind!r} is SEMANTIC_DISALLOWED and must not be passed to "
            "assert_final_emission_mutation_allowed at the boundary"
        )


def test_all_assert_mutation_kinds_are_contract_classified() -> None:
    kinds = _mutation_kinds_used_in_sources()
    for kind in kinds:
        bucket = classify_final_emission_mutation(kind)
        assert bucket in (PACKAGING_ALLOWED_KIND, LEGALITY_ALLOWED_KIND), (
            f"kind {kind!r} classified as {bucket!r}; boundary asserts must use only "
            "PACKAGING_ALLOWED or LEGALITY_ALLOWED kinds"
        )


def test_unknown_mutation_kind_classify_still_fail_closed() -> None:
    with pytest.raises(ValueError, match="unknown final-emission mutation kind"):
        classify_final_emission_mutation("__nonexistent_mutation_kind_for_block_d__")


def test_subtractive_fallback_strip_kinds_are_packaging_allowed() -> None:
    for kind in (
        "strip_meta_fallback_voice_surfaces",
        "strip_fabricated_authority_surfaces",
        "trim_overcertain_claim_spans",
    ):
        assert kind in PACKAGING_ALLOWED
        assert classify_final_emission_mutation(kind) == PACKAGING_ALLOWED_KIND


def test_repair_fallback_behavior_strip_pass_is_subtractive_no_composed_leads() -> None:
    """``repair_fallback_behavior`` only strips patterns; it does not append synthesized leads."""
    from game.final_emission_repairs import repair_fallback_behavior

    contract: dict = {
        "uncertainty_sources": ["unknown_identity"],
        "forbidden_hedge_forms": [],
    }
    text = (
        "I don't have enough information. Gate sergeant watches the lane. "
        "I know the east gate is sealed. He definitely ran toward the wharf docks."
    )
    validation = {
        "meta_fallback_voice_detected": True,
        "fabricated_authority_detected": True,
        "invented_certainty_detected": True,
    }
    out, meta, _ = repair_fallback_behavior(
        text,
        contract,
        validation,
        resolution=None,
        strict_social_path=False,
        session=None,
        scene_id="",
    )
    assert meta.get("fallback_behavior_repaired") is True
    assert meta.get("fallback_behavior_next_lead_added") is not True
    assert meta.get("fallback_behavior_unknown_edge_added") is not True
    assert meta.get("fallback_behavior_known_edge_synthesized") is not True
    assert len(out) < len(text)
    assert "I don't have enough information" not in out
    lowered = out.lower()
    assert "harbor clerk" not in lowered
    assert "duty sergeant" not in lowered
    assert "quartermaster" not in lowered
