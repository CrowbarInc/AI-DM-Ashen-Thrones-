# Readers of `topic_pressure.last_answer`

| Reader | Class | PR-BK |
| --- | --- | --- |
| `select_best_social_answer_candidate` path A (`topic_pressure:last_answer`) | Authority-bearing. Selected the stored prose as `structured_fact`. | Now calls `structured_fact_text_from_topic_pressure`. Generative prose is not selected. |
| `select_best_social_answer_candidate` path C (`topic_pressure:last_answer:redirect`) | Authority-bearing partial. | Same gate. |
| `select_best_grounded_social_answer_text` | Authority-bearing. Delegates to the selector. | Covered by the selector gate. |
| `determine_social_escalation_outcome` (`prior_same_dimension_answer_exists`, then `force_partial_answer`) | Authority-bearing. Treated stored prose as an existing answer. | Uses the same fact text. Generative prose does not count. |
| `prioritize_retry_failures_for_social_answer_candidate` | Authority-bearing. Copies the selector source onto the resolution. | Covered by the selector gate. |
| `_topic_progress_score` / `_commit_topic_progress` | Continuity. Compares the new reply with the previous line. | Still reads raw `last_answer`. |
| `_topic_pressure_speaker_has_prior_answer` | Continuity for “this speaker has spoken on the topic” (promotion). | Unchanged. Presence of text is not fact eligibility. |
| `interaction_context` surfaced-topic overlap | Continuity. Detects that the player is still on a surfaced thread. | Unchanged. |
| Strict-social emission of `structured_fact_candidate_emission` | Authority-bearing downstream of the selector. | No separate change. It cannot emit a candidate the selector no longer returns. |

`recent_contextual_leads` readers (prompt context, planner projection, passive scene pressure, and `final_emission_scene_facts` for three figure kinds) do not read `last_answer` and do not call the structured-fact selector. They were not modified.
