# 15 — Expression and Final Adoption

`select_host_speech` returns the locked host line before prior-speech reuse. The existing expression pass may reword it. `seal_host_speech` and `verify_delivery_record` are unchanged. There is no second player-facing path.

On the fresh run, every counted turn required `exact_authorized`, a valid digest, and history text equal to the sealed text. Turns that failed those checks are listed in the delivery report. Rejected expression candidates are not written as the delivered line.
