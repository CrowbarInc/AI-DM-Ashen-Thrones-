# PR-CP state and emission consistency

## Turn 3 discrepancy

PR-CO stored the patrol topic as revealed and then told the player that nothing could be established. `resolve_social_action` commits `topic_revealed` and clue knowledge before narration. That order was not changed.

The contradiction was the emission, not a second commit of the fact. Rejected provider extras never became scene facts. The revealed topic was the authored sentence. The spoken line was a refusal.

## Current contract

Social knowledge commits on resolver success, before the narration seal. This repair does not add a transaction around that commit.

The player-facing line must not deny a topic the resolver has already selected when the existing projection can state it. `_terminal_after_fidelity` now emits the canonical authored line whenever the mixed provider text fails and that line is hard-valid. The spoken sentence and the stored topic are the same fact.

Rejected clauses are not copied into scene, journal, or clue text. The projection uses the topic string already on the resolution.

If that projection is itself hard-invalid, `safe_nonresolution` still replaces the reply and the pre-narration reveal remains. That remaining gap would need a broader commit boundary. It was not redesigned. The reproduced patrol and notice cases project successfully, so the player-facing line matches the committed result.

Subsequent turns see the revealed topic in resolver state and the projected sentence in the sealed response text. History is not rewritten.
