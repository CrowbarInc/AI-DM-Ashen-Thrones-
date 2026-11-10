# Controlled Success

Fixture: `tests/test_grounded_marking_action.py`. A seeded Frontier Gate character is given an identified travel coat with an accessible cloth sleeve, carried mud compatible with cloth, paper, and wood, loose paper, and charcoal. Quantity is 1 and each row already has identity. Clues `north_warning` (`Warning: keep to the north wall.`) and `known_name` (`The name is Mara Voss.`) are disclosed. `physical_status.ordinary_marking` is `able`. The frozen scene file is not edited.

HTTP `POST /api/chat?ui_mode=player` with `I copy the warning onto my sleeve using the available mud.` and `client_request_id` `grounded-copy-1`:

- Status 200.
- Narration contains `The marking is on it now.` and the warning text.
- Narration does not contain `request_id` or `prepare_marking`.
- The coat has one mark, revision 2, classification `visible`.
- The ruleset extension is still present.
- `observe_object` with an authorized grant returns the warning.
- Disk reload matches.
- The same request id, including after the in-memory lane is cleared, does not add a mark.
- The same id with different literal content, after the lane is cleared, returns `Nothing further was written.` and the content stays the warning.
- Request id `grounded-copy-2` adds a second identical mark.
- Snapshot S0, taken before the action, restores zero marks. Snapshot S1, taken after, restores both.

A concealed utterance, `I secretly copy the warning onto my sleeve using the available mud.`, commits classification `concealed`. Ordinary observation returns no marking content. Observation with concealed authority returns the warning and does not include `request_id`.

The performance run repeated the success sentence over HTTP in an isolated store: one mark, published success, zero network blocks.
