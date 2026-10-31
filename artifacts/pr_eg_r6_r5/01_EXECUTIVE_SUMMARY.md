# 01 — Executive Summary

**Verdict: B — diagnosis supported with limitations.**

The production information path delivers a correct, authorized, sufficient reply on **59/164 (36.0%)** of 164 frozen turns. Validation is **18/54 (33.3%)**. Corrections are **0/25**. Restricted fixture text was not disclosed (0 hits on baseline, interventions, and expression control). Seals and topic snapshots matched on every scored turn.

The loss is upstream of expression. Substituting a host-authorized plan, and leaving disclosure in place, raises validation from 18/54 to **44/54 (I8, net +26)**. Rendering that same plan with expression disabled reaches **45/54 (I10B, net +27)**. A provider asked only to speak that sentence reaches 53/54, and that arm is not the production path. One validation turn (c06t07) shows expression turning a safe ignorance line into a specific false claim. Expression is not where most answers are lost.

Correcting every upstream semantic input and still running authorization (I9) reaches **32/54 (net +14)**. The remaining misses die in host gates: referent bind, witness checks, and `no_relevant_source`. Replacing only the question proposition (I3, net −2) or only the source proposition (I5, net −3) makes results worse. Supplying both (question + source) is the first combination that repairs failures neither side repairs alone (net +8, 7 of them only in the combination).

Filtering eligible source ids (I4) changes **zero** validation outcomes. Intent alone is net +1. Sufficiency relabel is net +2 and cannot create a fact the host did not select.

## Validation paired effects

Baseline validation success is 18/54. `Fixed` means the arm succeeded and the baseline failed. `Lost` means the reverse.

| Arm | Fixed | Lost | Net | Arm success |
|---|---:|---:|---:|---:|
| I10C | 35 | 0 | +35 | 53/54 (98.1%) |
| I10B | 28 | 1 | +27 | 45/54 (83.3%) |
| I8 | 27 | 1 | +26 | 44/54 (81.5%) |
| I9 | 14 | 0 | +14 | 32/54 (59.3%) |
| question_source | 8 | 0 | +8 | 26/54 (48.1%) |
| correspondence_sufficiency | 6 | 0 | +6 | 24/54 (44.4%) |
| intent_referent | 5 | 0 | +5 | 23/54 (42.6%) |
| I2 | 4 | 0 | +4 | 22/54 (40.7%) |
| I6 | 4 | 0 | +4 | 22/54 (40.7%) |
| retrieval_correspondence | 4 | 0 | +4 | 22/54 (40.7%) |
| I7 | 2 | 0 | +2 | 20/54 (37.0%) |
| I1 | 1 | 0 | +1 | 19/54 (35.2%) |
| I4 | 0 | 0 | +0 | 18/54 (33.3%) |
| I3 | 1 | 3 | -2 | 16/54 (29.6%) |
| I5 | 0 | 3 | -3 | 15/54 (27.8%) |

## What to repair first

1. The referent and witness gates that reject corrections and follow-ups before retrieval. Corrections are 0/25, and I9 still dies on bind and witness errors for turns I8 can already say.
2. Correspondence that runs only when both the question proposition and the source proposition are present. Either side alone loses baseline successes.
3. Leave candidate-id retrieval and the expression rewriter alone until those two repairs are measured. I4 did nothing. I8 and I10B are almost the same.

No production code was changed. No PR-EH work was started. Human review of the packet is pending.
