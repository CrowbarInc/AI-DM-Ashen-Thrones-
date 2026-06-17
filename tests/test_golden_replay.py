"""Historical redirect: golden replay tests decomposed into focused owner files.

Practical direct-owner coverage now lives in:

- ``tests/test_golden_replay_protected_bridge.py`` — protected assertion bridge diagnostics
- ``tests/test_golden_replay_structural_invariants.py`` — short structural invariant integration
- ``tests/test_golden_replay_long_session.py`` — 25-turn stability/profile coverage
- ``tests/test_golden_replay_direct_seam.py`` — direct-seam gate output observation
- ``tests/test_golden_replay_scenario_spine.py`` — scenario-spine smoke coverage

Run the focused files above (or the combined golden replay suite) instead of this stub.
"""

# Ownership note (BI-8 governance anchor; practical tests live in focused files above):
# Golden replay owns replay orchestration, replay observation consumption,
# protected assertion bridge diagnostics, and long-session replay execution /
# profile consumption. It must not own speaker legality, route enum legality,
# final emission gate orchestration, opening/fallback owner-bucket semantics,
# sanitizer phrase legality, dashboard/classifier row semantics, or
# stability/taxonomy threshold meaning.


def test_golden_replay_decomposed_redirect_stub():
    import tests.test_golden_replay as stub

    assert stub.__doc__
