"""AER5: rumor repair gating (low-signal tuple unpack), echo precedence, evaluator verdicts."""

from __future__ import annotations

from unittest import mock

import pytest

from game.narrative_authenticity import (
    build_narrative_authenticity_contract,
    repair_narrative_authenticity_minimal,
    validate_narrative_authenticity,
    _repair_rumor_realism_bounded,
)
from game.narrative_authenticity_eval import evaluate_narrative_authenticity


def _gm_with_na(contract: dict) -> dict:
    return {"response_policy": {"narrative_authenticity": contract}}


def test_repair_rumor_bounded_low_signal_compress_generic_after_tuple_fix(monkeypatch: pytest.MonkeyPatch) -> None:
    """``allow_low_signal_repair`` must use the boolean from ``_rumor_relaxed_signal_requirement``, not the tuple."""
    import game.narrative_authenticity as na

    def _fake_validate(txt: str, contract, gm_output=None):
        t = str(txt or "")
        if "They say" in t:
            return {
                "checked": True,
                "passed": False,
                "failure_reasons": ["secondhand_info_lacks_uncertainty_or_bias"],
                "metrics": {},
                "evidence": {},
            }
        return {
            "checked": True,
            "passed": True,
            "failure_reasons": [],
            "metrics": {},
            "evidence": {},
        }

    monkeypatch.setattr(na, "validate_narrative_authenticity", _fake_validate)

    c = build_narrative_authenticity_contract(
        overrides={"rumor_realism": {"fallback_compatibility": {"do_not_fail_for_brevity_alone": False}}}
    )
    text = (
        'The harbor runner squints toward the torchline. "They say ward chalk changed; rivermarks convoy moved," '
        "he mutters, low enough the watch will not turn."
    )
    fixed, mode = na._repair_rumor_realism_bounded(
        text,
        c,
        None,
        reasons={"secondhand_info_lacks_uncertainty_or_bias"},
        evidence={},
    )
    assert mode == "compress_generic_rumor_shell"
    assert fixed is not None
    assert "They say" not in fixed


def test_repair_rumor_bounded_skips_low_signal_transforms_under_brevity_relaxation(monkeypatch: pytest.MonkeyPatch) -> None:
    import game.narrative_authenticity as na

    captured: list[bool] = []
    orig = na._rumor_try_transforms_on_quote

    def _spy(*args, allow_low_signal_repair=False, **kwargs):
        captured.append(bool(allow_low_signal_repair))
        return orig(*args, allow_low_signal_repair=allow_low_signal_repair, **kwargs)

    monkeypatch.setattr(na, "_rumor_try_transforms_on_quote", _spy)
    c = build_narrative_authenticity_contract()
    text = 'He nods. "They say ward chalk; rivermarks," he mutters.'
    _repair_rumor_realism_bounded(
        text,
        c,
        None,
        reasons={"secondhand_info_lacks_uncertainty_or_bias"},
        evidence={},
    )
    assert captured == [False]


def test_repair_rumor_bounded_echo_drop_wins_over_extra_low_signal_reason() -> None:
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {
                "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight.",
            }
        ],
    )
    bad = (
        'He keeps his voice low. "The east gate is sealed until dawn; only what the dockhands say—that could be drink talk."'
    )
    v = validate_narrative_authenticity(bad, c, gm_output=None)
    reasons = set(v.get("failure_reasons") or [])
    reasons.add("secondhand_info_lacks_uncertainty_or_bias")
    fixed, mode = _repair_rumor_realism_bounded(
        bad,
        c,
        None,
        reasons=reasons,
        evidence=dict(v.get("evidence") or {}),
    )
    assert mode == "drop_echoed_rumor_clause"
    assert fixed is not None


def test_repair_minimal_echo_still_first_without_monkeypatch() -> None:
    c = build_narrative_authenticity_contract(
        player_text="What rumors about the east gate?",
        recent_log_compact=[
            {
                "gm_snippet": "The east gate is sealed until dawn; patrols hold the market lane overnight.",
            }
        ],
    )
    bad = (
        'He keeps his voice low. "The east gate is sealed until dawn; only what the dockhands say—that could be drink talk."'
    )
    v = validate_narrative_authenticity(bad, c, gm_output=None)
    fixed, mode = repair_narrative_authenticity_minimal(bad, v, c, gm_output=None)
    assert mode == "drop_echoed_rumor_clause"
