# PR-DF Decision Framework

Use this after the experiment in `PR-DF_experiment_design.md` has evidence. Do not fill in scores for B or C now. Do not fill in a winner for A from the PR-DE byte table alone.

## Hard disqualifiers

A candidate is out of the replacement decision if any of these occur on the scored set:

1. A prohibited state diff on scenarios 4, 8, 13, or 14 (hidden dump, fiat HP, declared canon, combat write outside the resolver).
2. A second world document or a writer other than the shared mutators.
3. Dice, DC, or HP taken from model text.
4. Missing token accounting for any provider request on a turn that is claimed successful.
5. A write to the production save files.
6. Narration payload for B or C silently smaller than A's during a run that claims a cost win. Cost runs must use the shared payload until a separate, pre-registered payload experiment.

A disqualified candidate can still be described. It cannot replace A.

## Weights

Weights sum to 100. They express the product priorities in the PR-DF brief. They are not measurements.

| Criterion | Weight | Why this weight |
|---|---:|---|
| Authority integrity | 20 | Authoritative state, persistent consequences, and hidden information are the constraints every other goal sits on. A fluent turn that corrupts the world fails the product. |
| Gameplay usefulness | 12 | The player needs a result they can act on. Refusals count as useful when the scenario requires a refusal. |
| Open-ended action support | 12 | Agency and unusual actions are a priority. They are weighted under authority so a more open model does not win by breaking the table. |
| Total cost per successful turn | 12 | Affordability is why this chapter exists. The metric is the completed turn, including retries and tool rounds. |
| Reliability | 10 | Wrong resolver, retry exhaustion, and partial failure decide whether a session is playable. |
| Latency | 8 | Wait time matters at the table. It is below cost and authority because a fast wrong turn is still wrong. |
| Maintainability | 8 | The current tree is already large. A design that adds a second rules engine would score poorly here even if a demo looked good. |
| World independence | 6 | Scheduled ticks and NPC continuity matter. Downtime is unwired for everyone, so this weight is real but not large enough to swing a decision on rest scenes nobody can run. |
| Narrative quality | 6 | Useful voice matters. The weight is low because length and drama are not success, and the live rubric is the only evidence. |
| Implementation effort | 6 | Effort changes which experiment to run next. It must not crown A merely for existing, so the weight is the smallest of the decision criteria. |

## How to apply

1. Drop disqualified candidates.
2. Score each remaining candidate 0–4 on each criterion from the experiment tables only.
3. Multiply by the weight. Publish the arithmetic.
4. A gap under 8 weighted points is a tie. Ties keep A in place and may add a supplement. They do not start a rewrite.
5. Authority score 0 on any disqualifier scenario is already a disqualification. Do not let high narrative or cost scores buy it back.

Criterion notes:

- **Authority:** fraction of scenarios with a clean tuple, with 13 and 14 mandatory.
- **Usefulness:** fraction of successful sheets. Adversarial refusals that meet the sheet count.
- **Open-ended:** scenarios 10 and 11, and the live unusual set. Passing by refusing an impossible pry counts. Passing by inventing a compartment does not.
- **Cost:** median completed-turn input estimate on the successful S1, S2, and C1 runs. Unknown `R` stays unknown. Do not impute zero retries.
- **Reliability:** authority passes minus turns that hit a budget before success.
- **Latency:** median sum of recorded timers on those same successful runs.
- **Maintainability:** judge from the reuse list. A harness that only calls current owners scores higher than a fork of combat or social resolution. This is a code-structure judgment, stated in prose, not a feeling about the narration.
- **World independence:** scenario 12 tick identity and "no second tick."
- **Narrative:** live checklist pass rate. No score until the live arm exists.
- **Effort:** record actual time after the prototype. The ranges in the reuse note are not scores.

## What this framework will not do

It will not select B or C from this document. It will not treat the 11% PR-DE reduction as a comparison against B or C. It will not treat inherited test failures as points against the idea of a deterministic pipeline.
