# Semantic probe results

Suite: `tests/test_unauthored_reply_structured_fact_integrity.py`

Command:

```
python -m pytest tests/test_unauthored_reply_structured_fact_integrity.py -q --tb=line
```

Collected 9, passed 9, failed 0, skipped 0.

| Probe | Result |
| --- | --- |
| A Unsupported model prose is not selected | Pass. Continuity text remains on `last_answer`. Source is not `topic_pressure:last_answer`. |
| B Authored prior answer remains reusable | Pass. Revealed topic text is selected as `topic_pressure:last_answer`. |
| C Cutoff stays ineligible | Pass. Interruption prose is not selected. |
| D Refusal does not become fact | Pass. Refusal is stored with `generative_reply` and is not selected. |
| E Paraphrase of an authoritative payload | Pass. Spoken paraphrase is remembered. Selected text is the authored payload. |
| F Same-turn self-promotion | Pass. Commit then select in the same session does not emit the new prose. |
| G Cross-turn promotion | Pass. Persisted generative `last_answer` is not selected. |
| H Different NPC / topic | Pass. Wharf tally clerk / cooperage lots, separate from the kiln porter. |
| Human-shaped access claim | Pass. Unsupported access sentence is remembered, `topic_revealed` stays null, follow-up answer kind is `refusal`. |

Adjacent regressions run with this slice:

- `tests/test_followup_topic_continuity_public_clue_paraphrase.py` passed (PR-BG).
- `tests/test_interruption_progression_catalog_residue.py` passed (PR-BI).
- `tests/test_social_answer_candidate.py`, `tests/test_social_topic_anchor.py`, `tests/test_social_escalation.py` passed after authoritative fixtures recorded `last_answer_provenance`.

Known reds not introduced as new owners here:

- `test_emission_quality_anyone_else_talk_to_manifests_preserves_redirect_not_fragment` still expects `topic_pressure:last_answer:redirect` and receives `topic_pressure:last_answer` (documented since PR-AO).
- `test_transcript_runner_asks_about_aldric_followup_stays_runner` and `test_transcript_where_is_aldric_repeated_followups_stay_runner` still see `success` as `None` (documented in PR-BJ).
- `test_response_policy_enforcement_question_resolution_mutation_records_reason` and the commit-contract assertion that the rain sentence must change: adjudication exemption in `question_resolution_rule_check` makes the rule not apply. `game/gm.py` was not modified in PR-BK.
