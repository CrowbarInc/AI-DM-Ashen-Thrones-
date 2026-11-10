# Structured outcome contract

The ephemeral request reuses AuthorizedInvestigation and DiscoveryAnchor. It includes bounded player_action; resolved_outcome status/success; must_communicate facts with stable per-outcome IDs, source and epistemic status; may_reference visible_scene and previously known continuity; authorized_consequences (empty in this disclosure-only slice); and must_not_establish constraints. No raw state, clue catalog, target IDs, private notes or hidden facts are sent. Required text is never silently truncated; oversized projections refuse.

New discoveries are mandatory. No-clue status is mandatory. Repeat-search no-new status and already-known clue are mandatory. All footprint uncertainty facets remain part of the mandatory fact. Scene observations are optional. Exact requests and mandatory IDs are in authorized_outcome_contracts.json and mandatory_fact_identifiers.json.
