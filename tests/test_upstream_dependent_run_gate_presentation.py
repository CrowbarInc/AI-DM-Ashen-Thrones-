"""BHC3: operator surface derived from canonical gate dicts only (no policy changes)."""

from __future__ import annotations

import pytest

from game.upstream_dependent_run_gate_presentation import (
    DISPOSITION_BLOCKED_UNHEALTHY,
    DISPOSITION_HEALTHY,
    DISPOSITION_PREFLIGHT_NOT_CHECKED,
    DISPOSITION_PREFLIGHT_SKIPPED,
    action_hint_for_gate,
    build_upstream_dependent_run_gate_operator,
    compact_operator_banner,
    print_upstream_gate_startup_operator_summary,
    upstream_gate_disposition,
)

pytestmark = pytest.mark.unit


def _healthy_gate() -> dict:
    return {
        "upstream_runtime_healthy": True,
        "preflight_available": True,
        "startup_run_valid": True,
        "manual_testing_blocked": False,
        "block_reason": None,
        "preflight_health_class": "healthy",
        "preflight_checked_at": "2026-01-01T00:00:00Z",
    }


def _blocked_quota_gate() -> dict:
    return {
        "upstream_runtime_healthy": False,
        "preflight_available": True,
        "startup_run_valid": False,
        "manual_testing_blocked": True,
        "block_reason": "upstream_unhealthy_preflight",
        "preflight_health_class": "insufficient_quota",
        "preflight_checked_at": "2026-01-01T00:00:00Z",
    }


def _skipped_gate() -> dict:
    return {
        "upstream_runtime_healthy": None,
        "preflight_available": False,
        "startup_run_valid": False,
        "manual_testing_blocked": False,
        "block_reason": "preflight_skipped_by_env",
        "preflight_health_class": None,
        "preflight_checked_at": None,
    }


def _not_checked_gate() -> dict:
    return {
        "upstream_runtime_healthy": None,
        "preflight_available": False,
        "startup_run_valid": False,
        "manual_testing_blocked": False,
        "block_reason": "preflight_not_checked",
        "preflight_health_class": None,
        "preflight_checked_at": None,
    }


@pytest.mark.parametrize(
    "gate,expected",
    [
        (_healthy_gate(), DISPOSITION_HEALTHY),
        (_blocked_quota_gate(), DISPOSITION_BLOCKED_UNHEALTHY),
        (_skipped_gate(), DISPOSITION_PREFLIGHT_SKIPPED),
        (_not_checked_gate(), DISPOSITION_PREFLIGHT_NOT_CHECKED),
    ],
)
def test_upstream_gate_disposition(gate: dict, expected: str) -> None:
    assert upstream_gate_disposition(gate) == expected


def test_compact_banner_blocked_unhealthy_includes_health_class() -> None:
    b = compact_operator_banner(_blocked_quota_gate())
    assert b is not None
    assert "BLOCKED" in b
    assert "insufficient_quota" in b
    assert "gameplay testing invalid" in b


def test_compact_banner_skipped_vs_not_checked_distinct() -> None:
    sk = compact_operator_banner(_skipped_gate())
    nc = compact_operator_banner(_not_checked_gate())
    assert sk is not None and nc is not None
    assert "skipped by env" in sk
    assert "not checked" in nc
    assert sk != nc


def test_compact_banner_healthy_is_none() -> None:
    assert compact_operator_banner(_healthy_gate()) is None


def test_action_hint_blocked_quota() -> None:
    h = action_hint_for_gate(_blocked_quota_gate())
    assert "credit" in h.lower() or "recharge" in h.lower()


def test_action_hint_auth_failure() -> None:
    g = {
        **_blocked_quota_gate(),
        "preflight_health_class": "auth_failure",
    }
    h = action_hint_for_gate(g)
    assert "api key" in h.lower()


def test_action_hint_permission_and_model_access() -> None:
    g1 = {**_blocked_quota_gate(), "preflight_health_class": "permission_failure"}
    assert "permission" in action_hint_for_gate(g1).lower()
    g2 = {**_blocked_quota_gate(), "preflight_health_class": "model_access_failure"}
    assert "model" in action_hint_for_gate(g2).lower()


def test_action_hint_skipped_vs_not_checked_wording() -> None:
    hs = action_hint_for_gate(_skipped_gate())
    hn = action_hint_for_gate(_not_checked_gate())
    assert "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT" in hs
    assert "startup" in hn.lower() or "preflight" in hn.lower()
    assert hs != hn


def test_build_operator_mirrors_gate_flags() -> None:
    op = build_upstream_dependent_run_gate_operator(_blocked_quota_gate())
    assert op["upstream_gate_disposition"] == DISPOSITION_BLOCKED_UNHEALTHY
    assert op["manual_testing_blocked"] is True
    assert op["startup_run_valid"] is False
    assert op["gameplay_conclusions_valid"] is False
    assert op["block_reason"] == "upstream_unhealthy_preflight"
    assert op["preflight_health_class"] == "insufficient_quota"


def test_startup_summary_healthy(capsys: pytest.CaptureFixture[str]) -> None:
    print_upstream_gate_startup_operator_summary(_healthy_gate())
    out = capsys.readouterr().out
    assert "[upstream_dependent_run_gate]" in out
    assert "healthy" in out
    assert "startup_run_valid=true" in out


def test_startup_summary_blocked(capsys: pytest.CaptureFixture[str]) -> None:
    print_upstream_gate_startup_operator_summary(_blocked_quota_gate())
    out = capsys.readouterr().out
    assert "BLOCKED" in out
    assert "action_hint:" in out


def test_startup_summary_skipped_by_env(capsys: pytest.CaptureFixture[str]) -> None:
    print_upstream_gate_startup_operator_summary(_skipped_gate())
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "skipped by env" in out


def test_startup_summary_preflight_not_checked(capsys: pytest.CaptureFixture[str]) -> None:
    print_upstream_gate_startup_operator_summary(_not_checked_gate())
    out = capsys.readouterr().out
    assert "WARNING" in out
    assert "not checked" in out


def test_playability_summary_from_eval_attaches_operator() -> None:
    from tools.run_playability_validation import summary_from_eval

    gate = _skipped_gate()
    out = summary_from_eval(
        "p1_direct_answer",
        {"overall": None, "axes": {}, "summary": {}},
        upstream_dependent_run_gate=gate,
    )
    assert out.get("upstream_dependent_run_gate") == gate
    op = out.get("upstream_dependent_run_gate_operator") or {}
    assert op.get("upstream_gate_disposition") == DISPOSITION_PREFLIGHT_SKIPPED
    assert "skipped by env" in str(op.get("compact_banner") or "")
