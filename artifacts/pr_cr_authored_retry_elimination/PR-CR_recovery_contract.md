# PR-CR Recovery Contract

Existing sequence inspected:

1. Social resolution selects a topic in `resolution["social"]["topic_revealed"]`.
2. `run_preserve_if_valid` validates the initial provider answer with `validate_generated_response`.
3. A hard-invalid first answer is marked rejected with `mark_candidate_rejected`.
4. Regeneration feedback is built.
5. The new early projection eligibility check runs before the regeneration callback.
6. The existing canonical projection renderer `format_authored_knowledge_realization_line` renders the topic text.
7. The projected line is checked by the existing hard validator.
8. `seal_accepted_response` immutably seals the projected response.

Eligibility is intentionally narrow:

- resolution must be social;
- operation must be `ask`;
- a concrete `topic_revealed` dict must exist;
- topic text or clue text must be non-empty;
- no unresolved explicit addressee may exist;
- unresolved qualifiers must be absent;
- executable obligations must be absent;
- permitted mutations are limited to the already-selected social topic bookkeeping (`topic_revealed`, `npc_id`);
- projection must validate hard-valid;
- projection must be eligible for immutable sealing.

If any requirement fails, the existing retry/fallback path remains in force.

