PR-DV Response Integrity Tests

Added:

- `test_pr_dv_structured_resolution_facts_survive_generic_final_text`
  - Lantern description preserved.
  - NPC reply/topic preserved.
  - Scene destination preserved.
  - Notice text preserved.

- `test_pr_dv_rejected_and_ambiguous_stored_interpretations_do_not_fallback_execute`
  - Rejected interpretation cannot execute through parser fallback.
  - No resolver invocation.
  - No counter/clock advancement.

Existing PR-DU tests continue to cover:
- Production chat entry point.
- OOC non-mutation.
- Four-action production sequence.
- Disposable state persistence.
