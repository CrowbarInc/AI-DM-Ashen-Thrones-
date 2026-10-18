# 12 — Frozen Independent Holdouts

Fixture: `tests/fixtures/pr_eg_r1_continuity_holdouts.json`.

Expectations were written before the implementation and were not edited after results. Scorer: `tests/test_pr_eg_r1_continuity.py`. All 20 cases pass, plus personal-ignorance recovery and the zero-call chat quote of the north road.

Provider calls are not part of the holdout scorer. Live efficiency is in reports 11, 13, and 14.

| Holdout | Interpretation | Grounding | Ownership | Relevance | Authorization | State |
| --- | --- | --- | --- | --- | --- | --- |
| immediate_clarification | ask | preceding statement | NPC | north road | execute, R4 preserved | no undo |
| pronoun_followup | ask | active NPC | NPC | not the internal GM line | ask stays with Mara | no clock in the directive |
| paraphrase_followup | answer | road sentence, not the later preference | NPC | north road | quote, no new fact | none |
| earlier_topic | answer | road, not the preference | NPC | north road | quote | none |
| explicit_addressee_change | none | Bren, not Mara | existing path | not captured | explicit ask unchanged | none |
| gm_about_npc_statement | answer | her statement | GM quote | north road | no "says," | no social |
| ordinary_preference | ask | Mara | NPC | personal flag | improvisation still permitted | no fact |
| repeated_preference | reuse | morning commitment | NPC | morning | narration determined, not canonical | no mechanic |
| conversational_correction | answer | road | NPC | north road, not morning | not an undo | executed intention kept |
| pending_action_correction | none | left to revision path | existing | side gate not executed | authorization unchanged | pending move remains |
| executed_undo | none | not a topic fix | existing | undo not captured | world state kept | none |
| negotiation_request | answer | Mara | NPC | decline | no silver, no quest | withheld commitment |
| unauthorized_promise | answer | same decline | NPC | no ten silver | no obligation | canonical false |
| npc_uncertainty | ask | surveillance exchange | NPC | not the internal line | unknown stays unknown | none |
| hidden_information | none | not captured | existing | password not answered | hidden stays hidden | none |
| absent_npc_reference | clarify | Mara's earlier line | GM | not here, no "says," | no remote speech | none |
| ambiguous_history | clarify | Mara or Bren | GM | names both | does not execute | none |
| save_load_exchange | reload | one row | NPC | same text | no duplicate | password absent |
| rejected_narration_not_history | not stored | rejected line excluded | n/a | n/a | n/a | not in history |
| bounded_commitments | cap | 24 rows | n/a | n/a | canonical false | list bounded |

Naturalness of the live lines is scored in the fresh transcripts, not by these directives. The quote frame "I meant this:" is accurate and stiff. That limitation is in report 17.
