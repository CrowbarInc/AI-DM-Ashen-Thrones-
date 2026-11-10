# PUBLICATION TEST MATRIX
45 parameterized tests exercise the actual FastAPI HTTP endpoint and inspect the serialized response body. They cover all requested 40 cases plus helper exception, serialization exception, interrupted-request construction control, final invariant recovery and stale evidence. Isolated projection/multiple-fact controls are injected into an HTTP execution, not counted as native multi-discovery mechanics. Validation-status injections at the hook output exercise publisher decisions; PR65 validator-level injections remain in regression. Unsupported actions retain existing grammar behavior, not a new unsupported-action protocol.

publication_matrix.json contains requests, resolver outcomes in bodies, mandatory projections, exact candidate and original validation in hook trace, final publication decisions/bodies, before/after session and narration state guards; error cases record 500 without publication success. Initial development assertions incorrectly demanded fallback even when valid optional text was accepted. Test expectations/setup were corrected, production source unchanged; initial logs/XML are preserved. Final development.xml: 45/45.

| Case | HTTP | Decision / expected behavior | State |
|---|---:|---|---|
| accepted | 200 | published | unchanged by narration |
| rejected | 200 | fallback | unchanged by narration |
| empty | 200 | fallback | unchanged by narration |
| malformed | 200 | fallback | unchanged by narration |
| unavailable | 200 | fallback | unchanged by narration |
| timeout | 200 | fallback | unchanged by narration |
| FAIL | 200 | fallback | unchanged by narration |
| REVIEW_REQUIRED | 200 | fallback | unchanged by narration |
| VALIDATION_ERROR | 200 | fallback | unchanged by narration |
| legacy_stub | 200 | fallback | unchanged by narration |
| legacy_refusal | 200 | fallback | unchanged by narration |
| legacy_unknown | 200 | fallback | unchanged by narration |
| legacy_empty | 200 | fallback | unchanged by narration |
| missing | 200 | fallback | unchanged by narration |
| multiple | 200 | published | unchanged by narration |
| context | 200 | published | unchanged by narration |
| no_new | 200 | published | unchanged by narration |
| hidden | 200 | fallback | unchanged by narration |
| persistent | 200 | fallback | unchanged by narration |
| inventory | 200 | fallback | unchanged by narration |
| death | 200 | fallback | unchanged by narration |
| route | 200 | fallback | unchanged by narration |
| contradiction | 200 | fallback | unchanged by narration |
| duplicate | 200 | fallback | unchanged by narration |
| unsupported | 200 | ordinary/error | unchanged by narration |
| resolution_failure | 500 | ordinary/error | error/isolated control |
| init_failure | 500 | ordinary/error | error/isolated control |
| flag_disabled | 200 | ordinary/error | unchanged by narration |
| flag_enabled | 200 | published | unchanged by narration |
| continuity | 200 | published | unchanged by narration |
| state | 200 | published | unchanged by narration |
| cross_campaign | 200 | ordinary/error | unchanged by narration |
| cross_session | 200 | ordinary/error | unchanged by narration |
| schema | 200 | published | unchanged by narration |
| serialization | 200 | published | unchanged by narration |
| historical | 200 | fallback | unchanged by narration |
| accepted_publish | 200 | published | unchanged by narration |
| fast_path | 200 | fallback | unchanged by narration |
| one_call | 200 | published | unchanged by narration |
| no_loop | 200 | published | unchanged by narration |
| helper_exception | 200 | fallback | unchanged by narration |
| serialization_exception | 500 | ordinary/error | error/isolated control |
| interruption | 200 | published | unchanged by narration |
| invariant_recovery | 200 | fallback | unchanged by narration |
| stale_evidence | 200 | published | unchanged by narration |
