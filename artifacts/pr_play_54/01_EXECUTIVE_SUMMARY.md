# PR-PLAY-54 — Consequential fabrication validation

Verdict: **B — PARTIAL / FURTHER INVESTIGATION REQUIRED**.

The quarantined prelude gate can now reject the fabrication classes PR-PLAY-53 missed: a found key, a named culprit, an NPC confession, and a failed investigation told as a success. On the scored corpus the new check rejects 49 of 49 consequential fabrications. The previous check rejected 15 of 49 of those same lines. Harmless controls and authorized paraphrases are accepted by the new check: 0 of 31 false positives, 7 of 7 paraphrases. Two ambiguous lines return `REVIEW_REQUIRED` and are not treated as a pass. No provider was called. Player-facing text, inventory, and mechanical results stay on the deterministic path.

The gap that keeps this partial is structural. Weak verbs `find`, `notice`, and `spot` still depend on a head list. A measured line outside the scored corpus, "You find a ribbon beneath the board.", is accepted. "You discover a ribbon beneath the board." is rejected. The combined prelude gate also still rejects two lines the new check accepts, both because of older rules: a synonym paraphrase of a guard route, and dust lying in a pack.

This does not authorize player-facing narration.

Measurement source: `artifacts/pr_play_54/run_regression.py`. Corpus rows: `corpus_results.json`. Counts: `metrics.json`. Tests: `focused.xml`.
