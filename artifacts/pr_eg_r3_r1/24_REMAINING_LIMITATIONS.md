# 24 — Remaining Limitations

The characterization premise is one host theme, licensed only by an established "I prefer ..." sentence. An NPC without that sentence gets the ordinary fallback. The host does not invent a quiet personality for them. Other subjective themes are out of scope.

"The world seems to slow down", "comes", and "end of the day" remain unsupported. The validator fails closed.

A second request for the same explanation reuses the adopted sentence and rejects a verbatim repeat. It does not produce a fresh wording of the same premise.

The isolated historical harness still reports equivalent paraphrases as ambiguous when the second record omits `proposition_id`. Production copies the id. A delivered row written without it can still collide. Reusing an adopted explanation also hashes that full sentence, so the same reason can appear under the original preference id and under a second statement id.

Ambiguous clarification says "Which earlier remark do you mean?" and does not name the competing sentences.

The first qualification is a real miss: characterization was not adopted, one restatement became ignorance, and one secondary turn made a narration call. It is preserved in `qualification_before_degree_repair.json`.

The first post-repair regression run recorded two Windows `PermissionError` failures while renaming `session.json`. The confirming run passed those tests. They are environmental.

The full repository suite was not run. Twenty-five inherited relevant-suite failures remain.
