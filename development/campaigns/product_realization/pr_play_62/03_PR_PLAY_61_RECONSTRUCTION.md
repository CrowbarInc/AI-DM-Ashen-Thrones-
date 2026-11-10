# PR61 reconstruction

Sources: original experiment_results.json, replay_results.json, provider ledger,
and quarantine records 001–004. Full original candidates, per-layer traces,
outcomes, publication, provider/HTTP timings and authoritative projections are
preserved in restricted pr_play_61_reconstruction.json. No missing evidence is
reconstructed by inference.

| Action | Deterministic result | Semantic | Legacy hard-valid | Coverage | Combined |
|---|---|---|---|---|---|
| Notice board | discover_clue, true; route disclosed | PASS | true | PASS | PASS |
| Rain barrel | investigate, true; no discovery | FAIL | false after semantic gate | REVIEW_REQUIRED | FAIL |
| Board again | already_searched, false; prior route | PASS | true | PASS | PASS |
| Gate | observe, null; no discovery | PASS | true | REVIEW_REQUIRED | REVIEW_REQUIRED |

Both passing narrations published in the original live capture. Both rejected
ones originally left a provider-disabled stub. PR61's later repaired saved-text
replay published broad deterministic fallback instead. This distinction is
preserved: repaired replay publication is not original live publication evidence.
Four requests consumed 1,926 tokens, HTTP mean 2.601s/max 3.331s.
