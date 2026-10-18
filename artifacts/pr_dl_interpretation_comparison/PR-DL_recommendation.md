# PR-DL Recommendation

Decision: C — HYBRID REFINEMENT REQUIRED

Selective routing fully handles 16 of 21 scenarios with 10 calls and 9049 tokens. Universal routing fully handles 17 with 21 calls and 18754 tokens. Deterministic handling fully covers 11.

The two full improvements selective routing misses are the paraphrased compound (`var_compound_subtle`) and the quoted joke (`var_quote_control`). Universal routing gains both. It also replaces a correct attack interpretation with a rejected invented weapon id (`control_combat`). Net fully handled scenarios favor universal by one, while the call count more than doubles.

Both consuming policies still fail the canon declaration, which the model turns into a proposed world update, and the hit-point dump, which the model proposes and the adapter rejects. The unsupported mechanic line is only partial. Invoking the lightweight model does not by itself make those authority-heavy turns reliable.

The avoided calls therefore do not justify the missed paraphrase and quote, and the extra universal calls do not justify their cost. The comparison is complete enough to reject both policies as they stand.

Recommended next step: keep this out of production gameplay. Add a consumption guard that discards invented entity ids and proposed hit-point or canon updates, and extend the deterministic completeness checks to paraphrased approach-plus-manipulation and quoted speech. Re-run only the residual rows on stored outputs before any new provider call.
