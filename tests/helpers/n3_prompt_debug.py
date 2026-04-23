"""Shared N3 ``prompt_debug.narrative_roles_skim`` shape checks (operator skim contract)."""

from __future__ import annotations

from typing import Any, Mapping

from game.narrative_planning import NARRATIVE_ROLE_FAMILY_KEYS


def assert_narrative_roles_skim_when_trusted(skim: Mapping[str, Any]) -> None:
    """Assert a present skim matches the compact operator layout from ``_narrative_roles_prompt_debug_skim``."""
    assert skim.get("present") is True
    assert skim.get("roles_struct_ok") is True
    families = skim.get("families_shipped") or []
    assert set(families) == set(NARRATIVE_ROLE_FAMILY_KEYS)
    roles = skim.get("roles") or {}
    for rk in NARRATIVE_ROLE_FAMILY_KEYS:
        row = roles.get(rk) or {}
        assert "emphasis_band" in row
        assert "signal_n" in row
        assert "signals_head" in row
    co = skim.get("collapse_observability") or {}
    assert co.get("sig_families_n") is not None
    assert co.get("anchor_hint") in ("none", "high_band_vs_sparse_peers", "low_signal_coverage")
