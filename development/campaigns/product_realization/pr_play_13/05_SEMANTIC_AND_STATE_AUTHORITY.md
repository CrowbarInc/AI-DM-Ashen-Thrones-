# 05 — Semantic and State Authority

The legacy semantic validator is still installed and still runs for ordinary turns and for legacy openings. It is not globally disabled.

## Renderer path

The renderer does not skip `validate_generated_response`. It gives that validator engine sentences as both narration and declarations, with the source claim id copied from the catalog. Lexical comparison therefore checks identity with the authorized sentence. It is not asked to accept a paraphrase. That is a narrower input to the same check, not an exemption.

If a reviewed variant later fails a hard hidden-information, consequential, or opening-contract check, the opening fails and rolls back. There is no blanket exemption for renderer output.

Hidden-information and state checks that already run in `run_preserve_if_valid` still apply. Opening acceptance, the single commit, and rollback stay on the existing API path. A rejected render does not commit. A failed opening can be retried. Concurrent starts still commit one opening.

## What a plan cannot authorize

Player movement, combat, skill checks, resources, inventory, quest completion, NPC death or injury, faction changes, hidden disclosure, and time beyond the opening's existing initialization remain engine-owned. The rendered GM object carries no scene or world update. An existing runtime overlay is left in place. A model `scene_update` is an unsupported plan field and is not adopted.

The opening's existing initialization, including the current time-pressure step on a successful commit, is unchanged. The plan does not add another clock change.
