# False-positive analysis

New check, scored positive and paraphrase lines: 0 rejected out of 31.

That set includes sensory lines, weather, gestures, atmosphere, background motion, tone, failed-investigation wording, uncertainty, and the authorized paraphrases.

Two combined-gate rejections remain. The new check accepts both. The older checker still rejects them, and the gate does not override that rejection.

| Id | Line | New check | Combined prelude gate | Older reason |
| --- | --- | --- | --- | --- |
| P1 | At sundown, the guard makes his rounds along the west road. | PASS | reject | `ungrounded_authoritative_rule` (geography family, no synonym match) |
| S21 | A little dust lies in your pack. | PASS | reject | `unsupported_mechanical_claim:items_added` |

S21 was already a false reject in the PR-PLAY-49 corpus. P1 is the same older geography rule: the authorized sentence is "The guard patrols the western road at dusk.", and the older token check does not treat sundown/dusk, rounds/patrol, or west/western as the same fact.

Saved provider preludes A1, A2, B1, and B2 still pass `validate_prelude`. The PR-PLAY-49 safe lines other than dust still pass. The PR-PLAY-51 harmless geography lines still pass. Those checks ran inside the focused suite.

The new check does not reject a line only because a noun is unfamiliar. "A chipped ceramic cup sits beside the innkeeper." and "You notice a crack in the board." pass. The crack line is in `residual_probe.json`.
