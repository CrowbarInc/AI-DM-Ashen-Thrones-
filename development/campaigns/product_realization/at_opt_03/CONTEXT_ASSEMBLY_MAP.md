# Primary Narration Context Assembly

Observed from the current working tree. The F3 provider payload itself was not stored, so the byte map in `TOKEN_ATTRIBUTION.md` is a reconstruction through these functions.

## Flow

1. `game.api.chat` loads campaign, world, session, character, scene, combat, and `load_log()`.
2. Host speech, `narration_skip`, and `deterministic_provider_skip_line` can finish the turn with an existing sentence. `disabled_retreat_skip` does that for a clear step-back when physical adjudication is off. Observed this cycle: “I step back from the notice board.” made 0 `build_messages` calls and 0 `call_gpt` entries.
3. When a resolution dict exists, `_build_gpt_narration_from_authoritative_state` registers the topic, applies social escalation, stamps CTIR, calls `collect_narration_context_call_kwargs` with `prompt_profile="manual_play_auto"`, and attaches the narration-plan bundle.
4. `build_messages` calls `build_narration_context`, then serializes two messages.

`call_gpt` is the provider boundary. With `ASHEN_DISABLE_PROVIDER_CALLS=1` it returns before constructing a client. The admission estimate, when accounting is active, is `(len(json.dumps(messages)) // 3) + 64` in `gm.py`.

## What each stage adds

| Stage | Function | Always when a primary prompt is built | Conditional |
| --- | --- | --- | --- |
| Scene and intent | `collect_narration_context_call_kwargs` | Effective scene, public layer, intent, mode line, world-state view of flags, counters, and clock lines | Discoverable clues depend on intent. Uncertainty hint only for a direct question without a known answer. Recent log is `recent_log[-8:]`, or empty when `chat_history` is `[]` |
| Policy and plan | `build_narration_context` | `response_policy`, instructions, turn packet, referent tracking, scene anchor, narration visibility | Compact instruction list only when `_should_use_manual_play_compact_prompt` is true. Narrative plan comes from the stamp-matched bundle when CTIR is present |
| Envelope | `select_provider_response_envelope` | Full `SYSTEM_PROMPT`, including the structured-claim schema, unless the turn is incidental dialogue with no consequential realization | Narration-only system prompt and the narrow social projection apply only on that envelope |
| Exact-copy cleanup | `build_messages` tail | Instruction lines that are exact substrings of the system prompt are removed. Top-level contracts that are JSON-equal to a policy child are removed. Nested packet policy is removed only when every nested key equals the root | Harmless-social projection omits opening and lead blocks and compacts the packet, plan, and mechanical resolution, under a long predicate |

## Compact-instruction gate

`_should_use_manual_play_compact_prompt` returns false when the profile is `manual_play_auto` and any of these hold: opening scene, `must_advance_scene`, a required check, a nonempty uncertainty hint, an active topic anchor, or a nonempty follow-up pressure object.

On the F3 reconstruction, `is_opening_scene` is false and `must_advance_scene` is true. The flag is copied from `transition.transition_required`, which is true. The full instruction list is 78 lines and 12,596 bytes. The existing compact helper, called offline with the same policy, is 10 lines and 2,741 bytes. Production did not select it.

## Duplication points

Observed in the rebuilt user JSON:

- `turn_packet.response_policy` is 6,016 bytes. Twelve of its keys are JSON-equal to `response_policy` and remain because three sibling keys differ. The omit function is all-or-nothing. Tests in `tests/test_pr_ed_provider_efficiency.py` cover the all-equal drop and the all-unequal keep. They do not cover a mixed packet.
- `turn_packet.contracts` still carries unequal `answer_completeness` (1,371 bytes) and `response_delta` (1,764 bytes). Equal contract keys are already removed.
- The same lead title and summary appear under `lead_context` and again inside anti-railroading and context-separation. Eight copies of an 80-byte string. That cross-reference is small.
- `character.role` matches `campaign.character_role` (95 bytes).
- Opening keys are still present while `opening_mode` is false. Together they are 525 bytes on the copy that drops them.
- Keys named `debug` remain inside the model payload. No instruction line mentions debug. Their removal saves 2,405 bytes on a copy. Several of those objects are speaker-selection traces (`why_speaker_chosen`, `why_switch_permitted_or_not`).

## Route versus prompt

Observed with provider calls disabled, on the snapshot state:

| Utterance | `build_messages` | `call_gpt` | Result |
| --- | ---: | ---: | --- |
| I step back from the notice board. | 0 | 0 | Existing unsupported sentence. Operational refusal |
| What do I see? | 1 | 0 | Local-observation sentence. The prompt was built and not sent |
| Hello, Gate Guard. | 1 | 1 | Entered `call_gpt`. Expression was disabled, so the greeting still uses the primary prompt. The disabled-call fallback is not a live narration |

Inferred: a legitimate primary narration, such as that greeting with expression off, still receives the full scaffold. Utterance text changes the blob by at most a few kilobytes on this snapshot.
