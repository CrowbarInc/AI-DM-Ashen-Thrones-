# Narrative validation

`validate_narration` is the shared check used by `maybe_narrate`. Integrated and physical publications set `skip_primary_narration` when they already have `engine_publication`. The API skips the large primary narration call only when that flag is true.

The investigation line "The examination adds nothing new to what you already know." does not set that flag. The live run still spent a `primary_turn` of 24,269 tokens on "I look around the milestone." and showed the deterministic line. That path was not changed in this cycle.
