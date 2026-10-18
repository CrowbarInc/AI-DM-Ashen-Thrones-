# 20 — State Integrity Audit

live_qualification.json stores complete persisted worlds/sessions before and after every final turn. state_audit.json preserves full diffs and commitment changes; live_semantic_audit.json checks stable inventory/party/PC/location/visited locations, existing passive faction/event-log/agenda world ticks only, no new clue knowledge on repeats, accepted=delivered=history and preserved pending clarification.



Expected session changes include runtime/debug/provenance caches, normal turn clocks, initial seed normalization such as character_name, authorized topic/lead discovery and conversation records. They are recorded rather than all labeled immutable. Only the authored road/watch information is disclosed; no reward, password, invented guard gap, obligation or new NPC is authorized by reconciliation.



Adoption/history exclusion tests protect against unsafe candidates even where world state is unchanged. Actual save/load roundtrips verify continuation, not a separate process restart. Captured campaign states are disposable fictional fixtures.
