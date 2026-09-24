# Existing `last_answer` contract (before PR-BK)

Reconstructed from `game/gm.py` (`register_topic_probe`), `game/response_policy_enforcement.py` (`_commit_topic_progress`), and `game/social.py` (`select_best_social_answer_candidate`, `determine_social_escalation_outcome`).

## Field meanings

| Field | Meaning before PR-BK |
| --- | --- |
| `topic_pressure.last_answer` | Latest non-cutoff reply text for the topic, truncated to 480 characters. Used both as conversational memory and as a selectable answer. |
| `topic_pressure.last_answer_dimension` | Not a stored field. Dimension is classified from the player line at read time (`classify_social_question_dimension` / `classify_social_followup_dimension`). `last_probe_dimension` and `previous_probe_dimension` are the stored probe dimensions. |
| `topic_pressure.last_topic_key` | Not on the entry. `scene_runtime.topic_pressure_last_topic_key` is the current topic key. |
| `recent_contextual_leads` | Extracted subject/position fragments from player-facing text (`remember_recent_contextual_leads`). Prompt and scene-pressure context. Not the structured-fact selector. |
| `topic_revealed` | Resolution social payload for an authored topic that this turn actually revealed (`clue_text` / `text`). Precedence A in the selector (`resolution:topic_revealed`). |
| `reply_kind` | Social resolution class (`answer`, `refusal`, `explanation`, …). Escalation may rewrite it. It does not by itself prove the reply text is authored. |
| `prior_same_dimension_answer_exists` | True when stored `last_answer` supported the current dimension and overlapped the question. That flag treated the stored prose as an existing answer. |
| `social_answer_retry_candidate_source` | Source string from `select_best_social_answer_candidate`, including `topic_pressure:last_answer`. |
| `structured_fact_candidate` | Selector result with `answer_kind` `structured_fact` and text taken from `last_answer` or `topic_revealed`. |
| `structured_fact_candidate_emission` | Strict-social emission source when that candidate is spoken (`game/social_exchange_emission.py`). |

## Provenance already nearby

- `social.topic_revealed` (authored reveal on this resolution)
- NPC `topics` plus `npc_runtime.revealed_topics`
- `session.clue_knowledge`
- PR-BI interruption exclusion (`_stored_answer_is_interruption_narration`)
- No field recorded whether `last_answer` itself was authored

## Contract answers

1. `last_answer` was both dialogue history and fact memory. Nothing in the entry distinguished them.
2. The production writer is `_commit_topic_progress` (via `_commit_topic_progress_after_enforcement` at the end of `apply_response_policy_enforcement`). `register_topic_probe` creates the entry with `last_answer: ""`.
3. Readers are listed in `last_answer_reader_inventory.md`.
4. Authority-bearing readers were `select_best_social_answer_candidate` (paths A and C) and `determine_social_escalation_outcome` (`prior_same_dimension_answer_exists`).
5. Continuity readers compare or remember the text: progress scoring, surfaced-topic overlap, and “this speaker has a stored answer” for promotion.
6. The system already distinguishes an authored reveal (`topic_revealed`, revealed NPC topics, clue knowledge) from realized dialogue. It did not store that distinction on `last_answer`.
7. Yes. Those payloads are the provenance PR-BK reuses. No new store was added.
8. `recent_contextual_leads` is not the structured-fact selector. A later scene-fact helper can copy only `visible_suspicious_figure`, `recent_named_figure`, and `visible_named_figure` into visible facts. The human captain claims were emitted from `last_answer`, not from that helper. PR-BK does not change it.
9. Yes. One player-facing reply can be stored as `last_answer` and also scanned into `recent_contextual_leads`.
10. At commit time the resolution, world, and session are available, including `reply_kind`, `topic_revealed`, revealed topics, and clue knowledge. PR-BI’s cutoff check was the only eligibility gate.
