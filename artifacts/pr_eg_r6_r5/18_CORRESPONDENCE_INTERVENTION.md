# 18 — Gold correspondence

Validation paired result: fixed 4, lost 0, net +4, success 22/54 (40.7%).

Forcing `coverage()` to the gold label, without adding a schema-illegal `proposed_coverage` field, fixes 4 failures and loses none. Retrieval plus correspondence does not beat correspondence alone (both net +4). Correspondence helps only after a source proposition exists for that source. Turns rejected before the source scan cannot be saved here.

The arm replays the cached proposal. It does not resample the semantic model. Disclosure still runs. Restricted hits on this file: 0.
