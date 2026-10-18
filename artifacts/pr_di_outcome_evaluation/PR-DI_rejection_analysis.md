# PR-DI Rejection Analysis

## Candidate B Rejections

| scenario | rejection categories | exact evidence | semantic usefulness |
| --- | --- | --- | --- |
| ambiguous | B invalid schema; E correct ambiguity recognition | validation errors: `role:ask_target`, `role:subject_of_trust_question`; clarification: `Who does 'him' refer to, and who is 'the other one' in this context?` | High. The player-facing clarification is the right next move even though role labels failed validation. |
| declared_canon | B invalid schema; C unsupported operation; F partial authority refusal; G unauthorized proposal | validation errors: `role:agent`, `role:group`, `role:location`; actions used resolver `none` and `expects_mutation=world` | Mixed. It understood the attempted world update, but proposed unauthorized world mutation before validation stopped it. |
| mechanical_dump | B invalid schema; C unsupported operation; D invalid/unavailable entity/item references; G unauthorized proposal | validation errors: `role:item`, `role:information`; actions include setting target `goblin_1` via combat and perceiving unavailable map/motives | Useful. It decomposed the three demands and asked a reasonable clarification, but its representation was unsafe/unsupported. |

## Non-Rejection Does Not Equal Success

- Compound was schema-valid, but the plan represented the utterance as one `act`; the engine selector disagreed on resolver (`exploration` proposed, `travel` selected), and no notice-board mutation occurred.
- C1 was schema-valid but rejected before execution due the ambiguity/unsupported-mechanic clarification path. This was semantically useful and should not be scored as gameplay failure.
