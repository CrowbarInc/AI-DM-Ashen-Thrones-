"""Historical redirect: final emission gate tests decomposed into focused owner files.

Practical direct-owner coverage now lives in:

- ``tests/test_final_emission_gate_orchestration_order.py`` — behavioral layer order
- ``tests/test_final_emission_gate_n4.py`` — N4 acceptance-quality gate placement
- ``tests/test_final_emission_gate_diagnostics.py`` — FEM/debug diagnostics
- ``tests/test_final_emission_gate_selector_snapshots.py`` — selector/source snapshots
- ``tests/test_final_emission_gate_delegator_regression.py`` — BJ delegator/re-export locks

Run the focused files above (or the combined gate suite) instead of this stub.
"""


def test_final_emission_gate_decomposed_redirect_stub():
    import tests.test_final_emission_gate as stub

    assert stub.__doc__

