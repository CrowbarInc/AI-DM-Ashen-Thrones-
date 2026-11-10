# AT-OPT-02 Summary

**Verdict: A/PASS.** Both corrections are demonstrated with provider-free tests. Live provider calls this cycle: 0.

## What was corrected

A clear, simple retreat such as “I step back from the notice board.” is now a physical-action request when physical adjudication is off. The chat turn returns the existing unsupported sentence, “That part is not supported here. It was not carried out.” It does not call `gm.call_gpt`, does not increment the turn, does not move position, and is recorded as an operational refusal rather than completed gameplay.

The F3 HTTP verification script now installs its ceiling through `apply_verification_budget()`. A missing total becomes 3,000. The historical 200,000 total is rejected unless an override is passed and recorded. Admission still refuses an estimate that does not fit before the provider function runs.

Failure class: implementation defect. The retreat was already classified as `retreat`, and the verification cap was already stated. The acting owners did not use those facts. The fast path left the operation unresolved, and the HTTP script wrote 100,000 / 200,000 ceilings.

## What was left unchanged

Physical adjudication, when the experiment is on, still plans and commits a retreat, including the position change after a successful approach. NPC host speech, scene questions, examination, and an unrelated unresolved sentence still use their existing owners. Primary narration stays eligible for those sentences. Production opening ceilings were not changed. The classification-test helper still passes its own explicit ceilings. No movement mechanic was added.

The new retreat checks were written with this fix. They are not an independent holdout. The frozen 28-case 79D-F3 holdout still passes and does not contain this retreat sentence. No Ashen Thrones Gameplay Benchmark was run.

## Remaining risks

The recognition covers a first-person step-back, back-away, or move-back-from, including a bare “I step back.” Compounds, “step back to …”, questions, quotations, and third-person wording still reach their previous route. That is the bound of this correction.

The pre-dispatch estimate is UTF-8 bytes divided by 3, plus 64, and narration reserves its output cap (600 unless configured). A 3,000 verification total refuses an estimate that does not fit. It does not prove that every admitted request’s actual provider total stays under 3,000.

The historical 23,377-token F3 call was not repeated. This cycle shows that the primary route is not dispatched for that sentence under the same relevant flags. It does not measure a new token saving.

## Recommended next step

Do not start AT-OPT-03. Do not open PR-PLAY-80. Do not put the 3,000 verification total on production openings. A later cycle can measure a live token delta only with separate authorization.
