# 23 — Source Change Inventory

Cycle-relevant files, against the already dirty worktree:

| Path | Change |
| --- | --- |
| game/expressive_dialogue.py | Structured permitted meaning, characterization premise, degree and non-referential grammar, prohibited categories, proposition id, entity aliases |
| game/dialogue_authority.py | Answer sufficiency and the partial host line; proposition id on the authority record |
| game/conversational_continuity.py | Proposition id on delivered rows; equivalent grouping; multi-sentence exact recall; "another way" bound as a restatement |
| game/conversational_orchestration.py | Copies `proposition_id` onto continuity context references |
| game/api.py | Conversational social payload includes that proposition id |
| tests/test_pr_eg_r3_r1_expression_semantics.py | Matrix T01–T30, holdouts, production stub |
| tools/validate_pr_eg_r3_r1.py | Two frozen live plans and the fresh `/api/chat` runner |

`game/immutable_valid_response.py` was not given a new adoption path. Generated lines still enter through the existing host seal. No active campaign data file was edited. Disposable live sessions under `artifacts/pr_eg_r3_r1/disposable_state/` are excluded from the review bundle.
