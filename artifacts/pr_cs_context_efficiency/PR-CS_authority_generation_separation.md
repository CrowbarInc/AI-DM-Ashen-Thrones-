# PR-CS Authority / Generation Separation

The deterministic resolver, hard validator, immutable finalizer, state persistence, and subsequent-turn continuity all require rich authority state. The provider does not require all of that state in full.

Material needed by deterministic pipeline but over-sent to provider:

- Full realization claim arrays with source refs, semantic identity, persistence, relation kind, and premise IDs for simple narration-only social turns.
- Multiple copies of authored scene facts through visible facts, opening seed facts, journal seed facts, `gm_resolution_decision.realization_claims`, and recipe `required_content`.
- Full policy object shapes when the provider only needs compact behavioral obligations for the selected response type.
- Broad lead/world pressure booleans when the turn is a local harmless exchange.

Safe separation principle: keep complete CTIR, resolver, validator, and persistence data in app memory and logs; send a compact provider-facing projection that contains only the claims, constraints, and output contract needed to realize this turn. Authority must remain app-owned.
