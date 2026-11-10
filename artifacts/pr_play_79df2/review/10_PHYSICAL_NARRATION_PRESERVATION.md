# Physical narration preservation

Physical narration publication was not rewritten. Shared publication state still accepts a narration only when the visible sentence is not speech, `last_narration.adopted` is true, and the narration candidate is inside the visible sentence.

Development tests check one bounded expression attempt, no second expression on a repeated narration skip, and rejection of irrelevant or hidden narration. Historical focused, boundary, and broader lanes show zero new identities, so the physical-narration suites that sit in those lanes did not gain a new failure.
