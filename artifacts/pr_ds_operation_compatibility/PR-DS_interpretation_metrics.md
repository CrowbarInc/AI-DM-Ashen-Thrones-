# PR-DS Interpretation Metrics

The PR-DR scores below are the scores already recorded for the stored outputs. This replay does not replace them.

## Original model accuracy

Preserved from PR-DR. The scorer in `experiments/pr_dr/reports.py` counts a class match when the stored operation tuple is in the scenario's acceptable classes, and an entity match when a gameplay row's target is the required target or a non-gameplay row does not execute.

- Schema validity: 10 of 10
- Operation-class accuracy: 7 of 10
- Entity-binding accuracy: 10 of 10

The three class misses in the stored outputs are:

- DR01 stored INSPECT. The predeclared acceptable class is PERCEIVE. The target `courtyard_lantern` matches.
- DR02 stored ASK on `courtyard_lantern`. The acceptable non-gameplay classes are an empty list, UNSUPPORTED_MECHANIC, or RETCON.
- DR06 stored ASK with no target. The acceptable classes are an empty list, PERCEIVE, or INSPECT.

DR02 and DR06 were out of character in the envelope and did not execute. Executing DR01 does not make INSPECT count as the expected class. `sequence_complete` remains false for that reason.

## Adapter compatibility

The stored DR01 INSPECT of `courtyard_lantern` is eligible as a visible-surface inspection and was accepted by the investigate resolver. DR05, DR08, and DR10 were already eligible on their stored classes and targets. Four stored gameplay interpretations were compatible with an existing resolver.

## Successful engine execution

DR01, DR05, DR08, and DR10 executed, in that order, with the OOC and clarification rows still in the history between them. Six non-gameplay rows executed zero times.

## Persistence success

10 of 10 disposable reloads matched.

## Authority safety

0 rows with `execution_authorized` true. 0 unsafe interpretation reasons. 0 hit-point changes. 0 inventory changes. 0 dice on accepted actions. 0 non-gameplay executions. The notice clue was not returned before the gate or by the visible-surface gate.
