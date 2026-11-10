# 04 Experimental flag

Flag: `ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION`.

It publishes only when all of these are true:

- The flag value is exactly `1`.
- `ASHEN_QUARANTINE_INVESTIGATION_NARRATION` is exactly `1`.
- `ASHEN_QUARANTINE_NARRATION_MODE` is `integrated`.
- `ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION_SESSION` equals the session `campaign_run_id` or `session_id`.
- The resolved kind is investigate, observe, discover_clue, or already_searched.
- The latest quarantine record is for the same player text.
- Combined validation is PASS, fallback was not used, and the assembled sentence is the provider sentence.

Otherwise the ordinary sentence remains. If that ordinary sentence is the provider-disabled stub and the engine already stored a different fallback, the stub is replaced by that engine sentence. Rejected provider text is never copied into the response.

Unsetting the flag requires no migration. A different campaign run id in the same process did not receive the route sentence even when a passing candidate existed.
