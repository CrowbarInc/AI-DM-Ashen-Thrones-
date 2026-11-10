# Test-Data Isolation

Protected set recorded before edits: `artifacts/pr_play_77/protected_before.json`.

Recount after gameplay, tests, and regression:

- Compared: 150
- Changed: 0
- Missing: 0

Preservation count: **150/150**.

Pytest basetemp for this cycle stayed under `development/tmp/pr77_multistep` and `development/tmp/pr77_regression`. The isolation hook still refuses a pytest basetemp inside `artifacts/`.

The browser host used `artifacts/pr_play_77/browser_data` through the existing isolation install. Campaign storage, session storage, snapshots, and the browser network log were written there. Canonical `data/` was not the browser store.

`ASHEN_TEST_EVIDENCE_DIR` was used only for the earlier HTTP evidence write. The regression runner removed that variable before launching pytest.
