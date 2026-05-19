# Cycle F Maintenance Drag Closure

Date: 2026-05-19

Scope: closure report only. No runtime code or tests were modified for this closure step.

## Starting Problem

Cycle F started from a practical maintenance-drag concern: fixes were still broad, `game/final_emission_gate.py` kept getting touched, and file-touch metrics were noisy enough that it was hard to tell whether work was actually becoming smaller.

The first pass showed two distortions:

- Tracked runtime/session snapshots made narrow source changes look like broad commits.
- Opening fallback and replay/classifier/dashboard projection contracts created gate gravity, so failures that were really composition, payload, metadata, or projection symptoms still tended to route back to `game/final_emission_gate.py`.

The result was a familiar pattern: when something around opening/fallback/final emission failed, the safest-feeling edit target was often the largest and riskiest file.

## What Cycle F Accomplished

Cycle F did not attempt runtime decomposition. It made the ownership and measurement problem cleaner first.

- Separated true source fanout from snapshot churn.
- Clarified why `game/final_emission_gate.py` remains the top hotspot.
- Added gate-test ownership comments for current routing/projection boundaries.
- Mapped opening fallback ownership across composition, upstream prepared payloads, gate orchestration, metadata owner buckets, replay projection, classifier routing, and dashboard visibility.
- Chose a gradual symptom-specific routing policy instead of broad gate-biased routing.
- Implemented classifier/dashboard `investigate_first` improvements for opening-fallback symptoms while preserving existing categories and owner labels.
- Verified dashboard rows expose the new first-fault targets.
- Deferred broad projection helperization intentionally because the repeated literals currently preserve distinct test intent.

## Before / After Evidence

| Metric | Before / initial view | Refined / after Cycle F |
|---|---:|---:|
| Median non-artifact fanout | 6 files | N/A; replaced by refined metric |
| Median true source fanout | N/A | 4 files |
| Commits touching 8+ files | 11/30 non-artifact | 9/30 true source after snapshot separation |
| `game/final_emission_gate.py` touches | 10/30 | Still 10/30; remains top runtime hotspot |
| Snapshot churn | Mixed into non-artifact fanout | Split out; `data/combat.json`, `data/session.json`, and `data/session_log.jsonl` each appeared in 15/30 |
| Opening fallback routing | Broadly gate-biased through `fallback` | Some opening symptoms now route to first-fault targets outside the gate |

New opening routing now directs selected symptoms away from `game/final_emission_gate.py`:

- `opening_fallback_owner_bucket` -> `game/final_emission_meta.py`
- `opening_fallback_authorship_source` -> `game/upstream_response_repairs.py`
- opening basis/composition fields -> `game/opening_deterministic_fallback.py`
- raw-present replay projection omissions -> `tests/helpers/golden_replay.py`

Gate routing was intentionally preserved for final source/selection, fail-closed/gate-owned FEM symptoms, response-type orchestration, and final output selection cases.

## Remaining Risks

- `game/final_emission_gate.py` is still hot at 10/30 recent commits.
- `tests/test_final_emission_gate.py` remains large and still mixes orchestration, helper-owner checks, projection locks, and historical regressions.
- Helperization was deferred; repeated opening projection literals remain in place by design.
- No runtime decomposition was attempted, so source fanout has not yet been structurally reduced.
- New first-fault routing should improve triage, but it has not yet been proven over future commits.

## Success Assessment

Did Cycle F make fixes smaller or cheaper?

Answer: partially, and mostly by making the problem cleaner.

Measurement is now cleaner: snapshot churn is separated from true source fanout, dropping the median from the original non-artifact fanout of 6 to a refined true source fanout of 4.

Some future triage should be cheaper: opening fallback failures no longer all point at the final gate by default, and dashboard rows now show more precise first-fault targets for metadata, upstream payload, composition, and replay projection symptoms.

Runtime/source fanout has not yet been proven lower over future commits. Cycle F prepared the ground; it did not demonstrate a sustained post-cycle reduction.

## Recommended Next Cycle

Recommended next work: move on to the next planned cycle, with a lightweight measurement follow-up after several real commits.

Do not start runtime final-gate decomposition immediately. The next useful measurement is whether the new routing and ownership comments reduce actual gate touches in practice. After a handful of future commits, rerun the refined fanout/hotspot measurement and compare:

- true source median
- 8+ true-source commit count
- `game/final_emission_gate.py` touch count
- `tests/test_final_emission_gate.py` touch count
- classifier/dashboard routing accuracy for opening fallback failures

If gate touches remain high after that, the best next dedicated cycle is final gate decomposition recon, not direct refactor. Opening fallback helper extraction should stay deferred unless repeated projection literals become a demonstrated maintenance cost after routing stabilizes.

## Recommended Commit Title

Cycle F: Maintenance Drag Measurement and Opening Routing Closure

## Closure Verdict

Cycle F succeeded as a measurement and diagnostic-locality cycle. It did not yet prove smaller runtime fixes, but it removed noisy metrics, identified the true hotspot, narrowed opening fallback triage, and made future drag easier to measure.
