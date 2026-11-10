# Context Composition and Growth

The captured F3 prompt was not stored. `provider_budget.py` records no request content. What follows is a reconstruction: `build_messages` on the pre-continuation snapshot `2026-11-08T16-50-45_8caf7aff`, with provider calls disabled. Fingerprinted F3 files match the working tree. `game/gm.py` and `game/prompt_context.py` were not in that fingerprint. Treat every byte count below as reconstructed, not as the provider’s token bill.

Recorded input remains 22,777 tokens. The reconstruction with no resolution object estimates 28,031 admission tokens (`(json_bytes // 3) + 64`) from 83,902 blob bytes. The variant that includes the logged resolution without emission debug estimates 33,526. Both are the same family of prompt. Neither is the captured payload. Token estimates are the admission formula, not a tokenizer.

## Reconstructed layout

Two messages. System prompt 9,558 bytes (9,554 characters). User JSON 69,463 bytes without the logged resolution, 84,516 bytes with it.

Largest user sections, resolution omitted, bytes:

| Section | Bytes |
| --- | ---: |
| response_policy | 21,657 |
| instructions | 12,614 |
| turn_packet | 10,659 |
| narrative_plan | 5,051 |
| referent_tracking | 2,673 |
| dialogue_social_plan | 2,271 |
| lead_context | 2,163 |
| scene | 1,619 |
| character | 1,074 |
| recent_log | 402 |
| campaign | 395 |
| player_input | 54 |

`turn_packet.response_policy` is another 6,037 bytes inside the 10,659-byte packet. `response_policy` itself is a stack of contracts: context separation 3,699, answer completeness 2,079, interaction continuity 1,833, and several siblings between 1,300 and 1,800. `instructions` is a long standing list. `dialogue_social_plan.validator` is 1,211 bytes on a turn that was not a resolved social exchange.

Opening-named keys are present (`opening_scene_realization` 208 bytes, `opening_narration_obligations` 136, and smaller siblings). They are not the bulk. The standing policy, the instruction list, and the turn packet are the bulk.

Full system prompt in source is 9,568 bytes. Narration-only system prompt is 4,170 bytes. The reconstruction used a prompt within a few characters of the full system prompt (`system_equals_full_system_prompt: false` because `build_messages` replaces one hidden-fact sentence).

## What grows, and what did not

`collect_narration_context_call_kwargs` keeps `recent_log[-8:]` unless `chat_history` is an empty list (`gm.py` 4039–4044). This snapshot had two log entries. The reconstructed `recent_log` is 402 bytes. History growth does not explain 22,777 tokens.

Primary-turn input counts stay between 22,777 and 25,294 across 79, 79A, 79B, 79C, and F3, including turns that are not the first turn of a long transcript. The large prompt is the ordinary primary-narration payload. Openings recorded at 25,294 input tokens are the same order of magnitude as later primary turns at 22,961–23,178. Opening-scale context is what primary narration sends.

Public scene text in the reconstruction is 688 bytes inside a 1,619-byte scene object. The player utterance is 54 bytes. The expensive material is policy and instruction scaffolding around a small public state.

## Repetition

Reconstructed duplication that is visible as nested size:

- Top-level `response_policy` (21,657 bytes) and `turn_packet.response_policy` (6,037 bytes).
- `referent_tracking` (2,673) and `turn_packet.referent_tracking_compact` (171).
- `interaction_continuity` appears as its own section (258) and inside `response_policy` (1,833).
- Opening obligation keys sit beside narration obligation keys on a mid-scene turn.

These overlaps are reconstructed sizes. They are not a measured token saving. Cutting them can remove a grounding or authority rule that the narration validator still enforces. This audit does not identify a safe deletion.

## Requests over 20,000 input tokens

Eleven sent requests, all `gm.call_gpt`, listed in `04_cost_and_latency.md`. Expression and interpretation requests in the same ledgers stay under 5,000 input tokens. The >20,000 class is the primary narration prompt, including its retry, and it appears in every cycle that still called `gm.call_gpt`.

## Deterministic and bounded alternatives

The retreat already has a deterministic operation and a host sentence behind the physical experiment. With expression enabled, F published that sentence from a 72-token call. With expression disabled, `maybe_narrate` returns the host sentence and does not call the provider, once the turn is an adjudication result.

The F3 miss is earlier: the turn never became that result. A bounded expression path does not help a turn that has already been handed to `gm.call_gpt`.

Conversation history, campaign JSON, and the public scene are small beside the policy stack. Reducing the AI DM to a command menu is not where the bytes are. The bytes are the narration contract that travels with every primary call.
