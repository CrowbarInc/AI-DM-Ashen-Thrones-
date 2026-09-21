# RC-11 Trace

The accepted candidate is `Rain on the gate. Guards watch the choke.` and the stale emitted text is `You stand at the gate.`

Both the preserved inline sequence and the current helper restore exactly the accepted candidate. Candidate and emitted previews are also identical. The first and only meaningful divergence is after restoration, when the current helper records one governed `diagnostic_only` row at `_final_emission_meta.semantic_mutation_write_sites`.

The row identifies `game.final_emission_opening_fallback.reassert_scene_opening_accepted_candidate`, reason `accepted_scene_opening_reassertion`, and the test source. The pre-BU2-C comparator has no corresponding key because it predates semantic mutation write-site attribution.

Ten isolated executions produced the same assertion difference. Module and fallback-family order checks produced no additional failures.

Finding: `STALE_EXPECTATION`, confidence `HIGH`. No candidate selection, candidate identity, acceptance decision, preview, or player-facing text differs.
