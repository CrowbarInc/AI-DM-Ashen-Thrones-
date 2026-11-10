# Bounded narration

Prior defect: a physical action was adjudicated, one bounded expression ran, and the opportunity stayed eligible, so a second bounded expression could run for the same action.

Repair on this source, physical branch of `game/bounded_improvisation.py`: after `commit_physical`, `maybe_narrate` runs once when integrated narration is enabled. The result metadata then sets `bounded_expression_attempted` and `publication_contract` to `FINAL_ENGINE_RESPONSE`, whether the expression was accepted or the engine sentence remains. `narration_skip` returns immediately when that contract and a published sentence are present, so it does not call `_express_adjudication` again.

Settlement is the contract stamp plus the attempted flag, not the flag alone. A second `narration_skip` on that resolution adds no provider call.

Deterministic confirmation on this fingerprint: an accepted candidate, an irrelevant candidate, a hidden-fact candidate, and an unestablished-direction candidate each produce one transport call. A second skip adds zero calls. With the narration gate off, the transport is not called and the engine sentence is published.

Live confirmation on the same fingerprint: “I step back from the notice board.” produced one completed expression request and no interpretation request. The publication record is one row, category `live_narration`, validation `accepted_expression`. No second expression row exists for that turn.
