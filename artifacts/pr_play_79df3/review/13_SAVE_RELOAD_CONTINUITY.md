# Save and Reload Continuity

## HTTP script

After the examination, `session.last_publication` is the examine sentence and the turn is 5. After the operational refusal, both are unchanged. After snapshot and reload, the pointer is still the examine sentence and the turn is still 5. The following gameplay response advances the pointer and adds one publication event. The refusal text is not that event.

## Development test

`test_save_reload_keeps_the_preceding_publication` saves after a refusal and reloads. The prior publication and turn 4 remain, and the log keeps `response_class: operational_refusal`.

## Browser

The isolated session was saved by the normal chat path. After reload, the page shows three log entries. The latest visible GM sentence matches `last_publication.visible`. The refusal remains in the session log with an explicit operational class. It was not deleted and it is not a publication event.

No phantom turn was created for the refusal. The browser turn moved 4 to 5 on the first examination, stayed 5 across the refusal, and moved to 6 on the repeat examination. Campaign run id stayed `browser-79df3`.
