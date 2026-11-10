# 09 — Narrative validation

`game/narrative_consistency.py` `publication_conflict` checks location presence, object state, hidden facts, and long opening fingerprints. `scene_publication_replacement` calls it and still keeps the fingerprint loop. The old rain/Cinderwatch/eastern-gate triple is not the only check. Authorized clue text that is already in the resolution is not replaced.

Short text, the current location, and a committed transition are allowed. A foreign opening at Old Milestone is still replaced.

The expression rewrite validator also rejects the word "northwest", which is part of the established clue. That is why a faithful restyle of the milestone observation cannot be published. The check is general, and it is stricter than the deterministic publisher, which still says "northwest mud track."
