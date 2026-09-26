# Regression Results

## Focused

`python -m pytest tests/test_unparsed_movement_state_narration_integrity.py tests/test_unresolved_travel_narration_authority.py tests/test_unauthored_reply_structured_fact_integrity.py -q --tb=line`

| Suite | Collected | Passed | Failed |
| --- | --- | --- | --- |
| PR-BL `tests/test_unparsed_movement_state_narration_integrity.py` | 12 | 12 | 0 |
| PR-BF `tests/test_unresolved_travel_narration_authority.py` | 14 | 14 | 0 |
| PR-BK `tests/test_unauthored_reply_structured_fact_integrity.py` | 9 | 9 | 0 |

Also passed in the same family: scene destination binding, scene transition authority, post-GM adoption gateway, stay/leave social lock, physical-action typing, follow-up continuity, interruption residue.

One notice-read regression appeared on the first full suite: discover-clue narration that opens with engine stock `The new ground shows itself` was treated as a transition. That phrase is current-scene stock. The general guard no longer uses it. Unresolved travel still rejects it through the existing PR-BF kind check. The notice-read test passes after that correction.

## Full suite

`python -m pytest -q --tb=line`

Progress marks:

```text
7065 collected
6937 passed
29 failed
99 skipped
```

PR-BK baseline was 7,053 collected, 6,927 passed, 27 failed, 99 skipped. This run adds the 12 PR-BL tests. 6,927 + 12 = 6,939. The two extra failures are Windows `PermissionError` on pytest temp `session.json` renames (`test_http_undirected_who_last_read_stays_inspect`, `test_http_tavern_nearby_is_not_npc_catalog`). Both pass when run alone. The handoff already records that permission error as environmental. They are not PR-BL behavior changes.

The other 27 names match `artifacts/pr_bk/validation_failure_inventory.md`. They were not repaired.

## PR-BF

Remains settled. Unresolved `I'll head northwest` still fails closed. Successful follow still transitions. The new guard does not add a second travel resolver.

## PR-BK

Remains settled. No edit under the structured-fact owner. The 9 provenance tests pass.
