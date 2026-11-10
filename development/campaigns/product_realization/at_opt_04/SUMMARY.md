# AT-OPT-04 Summary

**Verdict: A/PASS.** `omit_duplicate_turn_packet_policy` now drops each nested policy key whose complete JSON value equals the same root key, and keeps keys that differ or that the root does not have. Live provider calls: 0. No commit or push.

The root `response_policy` is unchanged. On the F3 reconstruction the twelve JSON-equal nested keys are gone from the serialized request. `response_delta`, `answer_completeness`, and `planner_seam_trace` remain, including the extra or missing child that makes each one unequal. No other request section hash changed. `must_advance_scene` is still true and the instruction list is still 78 lines.

Serialized primary narration request, same snapshot and the admission serializer:

| | Bytes | Admission estimate |
| --- | ---: | ---: |
| Baseline | 83,040 | 27,744 |
| Optimized | 80,403 | 26,865 |
| Reduction | 2,637 (3.18%) | 879 |

The 879 figure is `(blob bytes // 3) + 64` before minus after. It is not a provider tokenizer count and it is not a measured bill. It matches the AT-OPT-03 hypothesis on this reconstruction. The recorded F3 input remains 22,777. The reconstruction is still an estimate, not that bill.

## What remains unproven

Provider-free tests show that duplicated serialized values were removed and that the remaining policy objects were preserved. They do not show that a language model reads the shorter request as the same narration, and they do not show a change in live-provider latency or cost.

The compact-instruction gate was not bypassed. Production openings were not capped at 3,000. No gameplay state changed on the reconstruction.

## Next step

Stop. Do not start AT-OPT-05. Do not open PR-PLAY-80.
