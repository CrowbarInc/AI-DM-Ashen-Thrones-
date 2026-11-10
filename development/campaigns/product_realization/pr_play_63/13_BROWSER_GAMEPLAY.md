# Browser gameplay

**Zero browser-originated actions; NOT TESTED.** Input usability, frontend submission/rendering, conversation order and duplicates remain unverified. browser_actions.json is the inherited capture filename; all PR63 rows are urllib real HTTP, never browser actions.

Minimal manual procedure: prepare a fresh disposable campaign with existing fixture setup and session-bound experimental flags (do not rerun capture scripts over frozen evidence). Start its application on localhost; open existing frontend in a standalone browser. Submit the five http_client_actions.json inputs. Check one player/GM pair each, mandatory route on turn 1, no route repetition on turn 2, repeat continuity, follow-up limitation, fallback on rejection, conversation order and usable input. Capture screenshots and API traces; compare authority to provider-disabled control. Keep bounded provider budget; stop disposable server afterward.
