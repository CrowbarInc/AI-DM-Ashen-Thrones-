# PR-DB Original Failure Replay

Source: PR-DA preflight of "Does the rain make it harder to keep watch?" on the reconstructed post-Turn-1 session. No new provider call was made for this replay.

State before the turn:

- Scene: `frontier_gate`
- `interaction_context.active_interaction_target_id`: `guard_captain`
- `interaction_mode`: `social`
- `discourse_focus.active_interlocutor.id`: `guard_captain`
- Guard Captain present and addressable

Recorded turn fields:

| Field | Value |
|---|---|
| Selected resolver | `social` |
| `resolution_contract.operation` | `ask` |
| `resolution_contract.interlocutor` | `guard_captain` |
| `interaction_obligation.interlocutor_id` | null |
| `interaction_obligation.resolution_mode` | `clarification_target_failure` |
| Provider `active_interlocutor` | null |
| `social.npc_id` | null |
| `social.target_resolved` | false |
| `speaker_selection.allowed_speaker_ids` | `[]` |
| `speaker_selection.authoritative_reason` | `no addressable target resolved` |
| Response envelope | `narration_only` |
| `provider_context_projection` | absent |

Prompt-time interaction hints on that captured payload:

- `active_interaction_target_id`: null
- `active_interaction_kind`: `observe`
- `interaction_mode`: `activity`
- `engagement_level`: `focused`

State after the turn:

- `discourse_focus.active_interlocutor`: `guard_captain`
- `interaction_context.active_interaction_target_id`: null
- `interaction_mode`: `social`
- Topic-pressure snapshot taken during the turn still showed `interaction_kind: observe` and `speaker_key: __scene__`

The contract id was not invented. It was the discourse interlocutor committed by Turn 1.
