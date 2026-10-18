# 32 — Failure Attribution

Representative fresh failures, earliest cause:

- "No, what did Brin tell Cala?" often died at host validation, reason `reverse_must_be_empty`. The model selected the reversal candidate and also filled values.
- "Vesper, who keeps the amber lens?" often compiled as a new question and then died at source resolution, reason `no_relevant_source`. The model did not supply a source proposition whose evidence survived the host check. The public sentence was available.
- "What about tomorrow?" was sometimes a real ambiguity among several live questions (`candidate_ambiguity`) and sometimes a temporal follow-up that correctly refused to repeat an untimed fact.
- "Which person exactly?" sometimes failed `unwitnessed_role` before a follow-up could bind.
- Restricted countersign turns failed closed at source resolution or as unknown. That is disclosure success, not interpretation success.

These are not one undifferentiated model failure. The host both prevented bad swaps and rejected repairs that would have answered public questions.
