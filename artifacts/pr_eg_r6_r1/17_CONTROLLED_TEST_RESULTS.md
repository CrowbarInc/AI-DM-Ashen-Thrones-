# 17 CONTROLLED TEST RESULTS

Final focused JUnit: 84 passed / 0 failed across the new disclosure suite and unchanged R6 suite. New suite covers 53 cases; unchanged R6 contributes 31. Provider exception testing patches the actual transport boundary; invalid plan testing supplies forbidden authorization metadata. Existing tests were not rewritten to improve counts.

Requested T01–T28 are not all independently qualified through `/api/chat`: public/secret, routing, failure, invalid-plan, expression, clue/idempotence, sealing and history cases are covered; exhaustive strict-social retries, rumor/disputed realization, partial persistence and legacy save reconstruction need further evidence.
