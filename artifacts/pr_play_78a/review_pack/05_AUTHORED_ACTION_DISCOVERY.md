# Authored-action discovery

`discover` returns consequence actions for the current scene when `enabled_for_session` is true. Each row is available, unavailable, or completed. Hidden rows are omitted. Actions from another scene are not candidates. Another campaign enrollment returns no candidates.

At the prepared milestone the visible rows are `patrol_survey` and `patrol_report` (available) and `patrol_record_survey` (unavailable until `patrol_survey`). At the gate, `patrol_warn_watch` is available only after `patrol_report`.
