# Semantic Mutation Attribution Closeout (BY4)

- schema version: 1
- closeout: by4_semantic_mutation_attribution

## Final measurement

- total turns: 8
- mutated turns: 3
- attributable first mutations: 3
- first-source coverage rate: 100.00%
- unknown first-source count: 0
- attribution gap count: 0
- semantic mutation risk (mean / max): 3.33 / 10

## BY1 synthetic fixture coverage

- fixture source: tests/helpers/semantic_mutation_attribution_closeout.py::build_by1_synthetic_fixture_corpus
- total turns: 7
- mutated turns: 6
- first-source coverage rate: 100.00%
- buckets covered: fallback, final_emission, policy, repair, sanitizer

## BY2 protected corpus measurement

- corpus: protected_replay
- first-source coverage rate: 100.00%
- unknown first-source count: 0
- attribution gap count: 0

## BY3 strict-social gap closure

- target turn: wrong_speaker_strict_social_emission|idx:0
- gap closed: True

## Bucket distribution (final)

- fallback: 1
- policy: 1
- sanitizer: 1

## Top mutation sources (final)

- game.response_policy_enforcement.apply_response_policy_enforcement: 1
- game.output_sanitizer.sanitize_player_facing_output: 1
- game.social_exchange_emission.build_final_strict_social_response: 1

## Protected replay non-interference

- verified: True
- final_text_hash stable (probe-on vs probe-off): True
- protected fields stable: True

## Remaining risks

- Semantic mutation probes are test/replay-only; production runtime does not stamp ordered checkpoints.
- Protected replay corpus covers 8 turns across 6 scenarios; live campaign paths may diverge.
- Risk score measures attribution completeness, not semantic equivalence of before/after text.

## Schema promotion recommendation

- promote to protected replay schema now: False
- measurement ready for future promotion: True
- rationale: Attribution measurement is stable on the protected corpus with zero gaps and full first-source coverage, but BY fields remain test-only diagnostics. Do not promote trace checkpoints or risk scores into protected golden replay schema until a dedicated cycle validates long-term non-interference, corpus breadth, and operational need for replay diffs.

## How to rerun BY measurement

Run the closeout regression guard (refreshes `artifacts/by4/` when using the repo artifact test):

```bash
python -m pytest tests/test_by4_semantic_mutation_attribution_closeout.py -q
```

Refresh individual deliverables:

```bash
python -m pytest tests/test_by_first_semantic_mutation_attribution.py -q
python -m pytest tests/test_by2_protected_semantic_mutation_measurement.py::test_by2_generate_repo_corpus_report_artifacts -q
python -m pytest tests/test_by3_strict_social_semantic_mutation.py::test_by3_generate_repo_artifacts -q
python -m pytest tests/test_by4_semantic_mutation_attribution_closeout.py::test_by4_generate_repo_artifacts -q
```

BY2/BY3 artifact tests write to `artifacts/by2/` and `artifacts/by3/`. The BY4 artifact test writes to `artifacts/by4/`.
