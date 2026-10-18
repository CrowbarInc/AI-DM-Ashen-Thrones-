# PR-DK Existing Signal Audit

Existing signals were populated as boolean fields for every row, but most are derived from the selected contract construction. The fields that fired in PR-DJ were text-backed override/canon signals; the fields intended to catch pronouns, compound action, and referent ambiguity were either false or unavailable in the compact selector.

- `explicit_abstention`: available only if the router reads `construction.fast_path_abstained`; PR-DJ's compact selector placed `fast_path_abstained` at top level, while `_signals` looked under `construction`, so it was effectively ignored.
- `missing_required_entity`: depends on `construction.entity_binding.status`; missed in PR-DJ because the compact selector discarded construction.
- `unresolved_pronoun`: depends on `selector.ambiguous`, so unresolved but non-ambiguous pronoun cases such as S11 are missed.
- `multiple_possible_referents`: depends on `selector.ambiguous` or an explicit ambiguous binding; unresolved addressee/claim states do not count.
- `compound_action`: depends on `secondary_operations` or executable obligations after construction; S10's secondary pry was never represented there.
- `resolver_disagreement`: only catches generation fallback disagreement, not an incomplete specialized resolver choice.
- `unsupported_mechanic`, `attempted_direct_state_override`, `attempted_world_canon_declaration`: populated from raw text and caught the two PR-DJ positives.

Existing data could detect S10's abstention and unresolved entity if construction were passed through, but it could not detect C1's consequential social content or S11's two unresolved personal references without additional checks.
