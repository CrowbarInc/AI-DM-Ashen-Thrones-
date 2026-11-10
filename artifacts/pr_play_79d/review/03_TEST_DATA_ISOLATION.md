# Test-data isolation

tests/conftest.py installs storage isolation before game imports. It configures campaign/session/save/provider locations, disables live test transports and installs a fail-closed audit guard on production data and historical artifacts. Every executed lane has its own basetemp/evidence root. Individual HTTP fixtures seed their own mutable data. Snapshots were explicitly isolated in the new persistence check.

Browser data is a copy of the existing 79C browser campaign. Existing provider ledger is excluded; each host process owns a new exclusive execution ledger outside copied gameplay state. Separate localhost origins isolate browser storage. No provider responses, routing, adjudication, validation or publication were stubbed for the browser.

Initial reproduction attempts using pytest's fixed default basetemp collided; their setup errors are retained and excluded from product verdicts. Unique-root reproductions then established all five failures. A legacy 79C holdout driver attempted to overwrite its historical RESULTS file; the audit guard blocked it. The original archive was not overwritten, and that failed attempted export is retained in gate_final.xml. The new frozen holdout was not rerun.

Protected data: 150/150 entry hashes unchanged. See protected_after.json.
