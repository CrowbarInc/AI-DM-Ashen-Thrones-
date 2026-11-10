# Scene publication

`scene_publication_replacement` rejects the Cinderwatch opening ("Rain spatters soot-dark stone" plus Cinderwatch plus the eastern gate) when the active scene is not `frontier_gate` and no transition committed. The replacement says the character is still at the current place. A committed transition is left alone. The same opening is legal at the gate.

The guard runs at the end of `_finalize_investigation_publication`. Early returns that already published engine or trusted text do not pass through it. The conditional that previously published the opening is now declined before that path, and the holdout conditional at Old Milestone did not contain the opening. Adaptive play recorded 0 scene contradictions.
