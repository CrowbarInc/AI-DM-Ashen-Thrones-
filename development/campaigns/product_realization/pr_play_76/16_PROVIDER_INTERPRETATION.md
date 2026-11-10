# Provider Interpretation

`validate_provider_interpretation` accepts only an operation and a target reference that the host can already ground. Extra fields, invented targets, hidden sentinels, and an operation that disagrees with the deterministic parse are rejected. There is no retry. The proposal does not commit.

Live campaigns used deterministic wording. `ASHEN_PHYSICAL_PROVIDER` was off on the browser host, and the HTTP trace disabled provider calls. Live physical provider requests: 0. Live provider tokens: 0. The unit tests cover malformed, timeout, disagreement, and candidate acceptance with a stub. Those stubs are not counted as live traffic.
