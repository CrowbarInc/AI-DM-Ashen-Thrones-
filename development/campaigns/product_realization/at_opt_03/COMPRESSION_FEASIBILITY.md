# Compression Feasibility

All experiments re-serialized the F3 reconstruction. Production `build_messages` was not modified. No provider was called. Baseline blob: 83,040 bytes. Admission estimate: 27,744. A smaller copy is a size result. It does not show that narration quality would stay the same.

| Experiment | Blob delta | Estimate delta | What changed | Authority still present | Limitation |
| --- | ---: | ---: | --- | --- | --- |
| Drop JSON-equal keys inside `turn_packet.response_policy` | −2,637 | −879 | Twelve equal keys removed. `response_delta`, `answer_completeness`, and `planner_seam_trace` kept | Root `response_policy` still has the equal values, including rule priority, the secrecy flags, and `no_validator_voice` | Unequal packet children remain (6,016-byte object becomes the three survivors). Token effect on a live call is unmeasured |
| Drop every key named `debug` | −2,405 | −802 | Speaker-selection traces, referent debug, packet debug, and small derivation traces | Speaker selection, referent tracking, and the policy objects that contained those traces stay | Some traces say why a speaker was chosen. Zero instruction lines mention debug. Quality effect unknown |
| Drop `opening_*` while `opening_mode` is false | −525 | −175 | Opening obligation and selector keys | `is_opening_scene` is already false on `narration_obligations` | Small. A later opening turn must keep these keys |
| Drop `dialogue_social_plan.validator` | −1,345 | −449 | Validator object only | The rest of the dialogue plan stays | This rebuild was a structured, non-dialogue envelope. Whether the validator steers refusals is untested |
| Those four together | −6,912 | −2,304 | The stack above | Root policy, scene, recent log, and the three unequal packet keys stay | Still a copy. Do not ship the stack as one change |
| Replace the 78-line instruction list with the existing compact helper | −10,011 | −3,337 | Instructions become 10 lines, 2,741 bytes. Narrative-mode lines were not copied into that call, so the compact block is slightly smaller than production’s compact path | `response_policy` stays and the compact lines point at it | Production keeps the long list because `must_advance_scene` is true. Forcing the swap bypasses that gate |
| Narration-only system text on the same user JSON | −5,661 | −1,887 | Structured-claim schema leaves the system message | User JSON still describes the structured envelope | The two sides would disagree. Rejected as a change |

Exact duplicate strings of at least 80 characters account for 1,365 extra bytes if later copies were deleted. Most of that is the lead title repeated across lead context and policy, and the validator-voice rule repeated in the nested packet. The lead repetition is a cross-reference of one established fact. The nested rule is part of the equal-key cut above.

## What these runs do not justify

Utterance-based omission. On this snapshot the scaffold stays near 83,000 bytes for a push, a look, a wait, a greeting, a recall, and an open question. The question rows grow. Removing scene or NPC material because the current sentence does not name it would leave the model unable to answer a follow-up, and the measured prize is a few kilobytes against a policy stack of about 59,000 bytes.

History trimming. Recent log is 306 bytes.

Shrinking `response_policy` prose. It is 31.5% of the user JSON and it is the authority surface the instructions tell the model to obey. A prose cut needs a live narration check this cycle did not run.

## Reproduction

`artifacts/at_opt_03/reconstruct_context.py` copies the F3 snapshot into a temporary directory, sets `ASHEN_DISABLE_PROVIDER_CALLS=1`, and writes `measurements.json`. The OpenAI client constructor was replaced with a class that raises. `provider_client_constructed` is false.
