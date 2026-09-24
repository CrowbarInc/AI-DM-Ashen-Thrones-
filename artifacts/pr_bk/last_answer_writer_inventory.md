# Writers of `topic_pressure.last_answer`

Production assignment sites:

| Writer | Class | What it stored |
| --- | --- | --- |
| `register_topic_probe` in `game/gm.py` | F | Initializes `last_answer` to `""` when the topic entry is created. Not a fact. |
| `_commit_topic_progress` in `game/response_policy_enforcement.py` | D, unless the reply communicates an existing payload | Any non-cutoff reply, truncated to 480 characters. This is the writer that stored ordinary model prose. |

There is no second production setter.

## Classification of the commit writer

The same function writes every non-cutoff reply. The reply’s class depends on provenance available at commit:

- A — the reply communicates `topic_revealed` or a revealed NPC topic. Provenance `topic_revealed` or `authored_topic`. The stored fact text is the payload, not the paraphrase.
- B — the reply communicates scene `clue_knowledge` or another resolution-authored sentence. Provenance `clue_knowledge` or `topic_revealed` (resolution clue text is collected with the reveal helper).
- C — a paraphrase of A or B. `last_answer` keeps the spoken line for continuity. `last_answer_authoritative_text` keeps the payload.
- D — arbitrary reply text, including unsupported model prose. Provenance `generative_reply`. The line is remembered. It is not a structured fact.
- E — interruption/cutoff prose. Still not stored (PR-BI). Refusal and authored-concealment lines are class D: remembered, provenance `generative_reply`.

`recent_contextual_leads` writer is `remember_recent_contextual_leads` in `game/gm.py`, called from perception grounding and the API after player-facing text exists. It extracts fragments. It does not set `last_answer` and is not a structured-fact source. Not changed.
