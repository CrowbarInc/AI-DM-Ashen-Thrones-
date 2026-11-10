# Provider-assisted matching

The provider is used only when the deterministic score is in the gray band (1 to 3) and an anchor is present. `ASHEN_AUTHORED_MATCH_PROVIDER=1`. Budget: 8 requests and 16,000 tokens. The model may return an id, confidence, and ambiguity. Host validation rejects unknown ids, hidden ids, low confidence, and ambiguous replies. The provider does not commit state.

Live utterance: "The watch ought to hear about those uncertain marks."

Deterministic proposal with the provider gate off: None

Result: ACCEPTED

Player-facing text: You commit to bringing the uncertain trail to the watch instead of conducting a private survey. Return to Cinderwatch Gate to give your report.

Flags after the turn included `patrol_report` and not `patrol_survey`. Save/resume preserved `patrol_report`: True.

Usage: 1 request, 158 tokens, elapsed 3828.4 ms. A second trace in the same turn is the interpretation bridge re-reading the cached proposal. It did not send a second provider request.
