"""Historical redirect: fallback projection tests decomposed into focused owner files.

Practical direct-owner coverage now lives in:

- ``tests/test_golden_replay_fallback_opening_projection.py`` — opening/sealed-gate opening projection
- ``tests/test_golden_replay_fallback_sealed_projection.py`` — sealed and strict-social sealed projection
- ``tests/test_golden_replay_fallback_visibility_projection.py`` — visibility/referential hard-replacement projection
- ``tests/test_golden_replay_fallback_upstream_projection.py`` — upstream prepared emission telemetry
- ``tests/test_golden_replay_fallback_sanitizer_projection.py`` — sanitizer empty/strict-social projection
- ``tests/test_golden_replay_fallback_upstream_fast_projection.py`` — upstream-fast split-owner projection
- ``tests/test_golden_replay_fallback_long_session_summary.py`` — long-session lineage/escalation summaries
- ``tests/test_golden_replay_fallback_acceptance_matrix.py`` — split-owner acceptance matrix alignment

Run the focused files above (or ``pytest tests/test_golden_replay_fallback_*.py``) instead of this stub.
"""


def test_golden_replay_fallback_projection_decomposed_redirect_stub() -> None:
    import tests.test_golden_replay_fallback_projection as stub

    assert stub.__doc__
