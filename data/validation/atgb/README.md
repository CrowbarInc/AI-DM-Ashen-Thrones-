# ATGB fixtures

These files are the ATGB-02 corpus. Scenario wording comes from
`development/reports/atgb_01_scenario_catalog.md`. The runner reads them. It does
not score them.

- `corpus.json` names the benchmark, the rubric, the expected partition counts, and the Frontier Gate facts.
- `visible/` holds development-visible scenarios and S08, which is tagged `related_variation`.
- `held_out/` holds S07, S09, and S10.

S07 was development-visible in the ATGB-01 catalog. ATGB-02 moves it to held-out
without changing its lines. Every held-out file is marked
`held_out_previously_exposed` because the ATGB-01 review already contained it.

A future environment is a new object in `corpus.json` plus scenario files that
name it. The runner does not hard-code `frontier_gate`.

Ordinary gameplay tests should not import `held_out/` in order to tune a repair.
The benchmark loader reads that directory when a run asks for the held-out
partition, including the infrastructure check that the adopted counts are intact.
