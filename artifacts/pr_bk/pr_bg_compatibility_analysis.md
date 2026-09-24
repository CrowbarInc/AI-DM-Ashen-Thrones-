# PR-BG compatibility

PR-BG lets a recognized empty-subject follow-up (`Why is that?`, `How come?`, `Who is he?`) reuse the current topic-pressure answer when speaker and dimension allow.

Those fixtures are authoritative because the stored sentence is the revealed NPC topic text:

- Kiln porter `kiln_spur_closed` text is the stored `last_answer`, and `revealed_topics` contains that topic id.
- Gate captain `watch_command` is the same pattern for the watch sentence.
- A follow-up that does not overlap that payload still refuses. `they` / `it` do not inherit.

PR-BK does not special-case those strings. `structured_fact_text_from_topic_pressure` returns a stored line with no explicit provenance only when the line matches an authoritative payload already on the resolution, in revealed topics, or in scene clue knowledge. The selector then emits that payload.

The invariant that separates the two cases:

```
legitimate authored follow-up reuse
    stored text matches a revealed topic, topic_revealed, or clue payload
    OR last_answer_provenance is topic_revealed / authored_topic /
       clue_knowledge / canonical_fact

arbitrary model prose reuse
    last_answer_provenance is generative_reply
    and no authoritative payload was recorded
```

Empty-subject continuation, speaker alignment, and dimension support are unchanged. They apply only after a fact text exists.

PR-BI remains a separate exclusion: interruption/cutoff prose is cleared before provenance is considered, and a cutoff commit does not replace `last_answer`.
