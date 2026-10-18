# 05 — Compact Dialogue Context Design


**Experimental only; no approved production schema or persistent subsystem.** Exact contexts/prompts are retained per trial. The initial compact fixture contains NPC id/name/role/voice, speaker/addressee, actual question, knowledge status and authorized facts, uncertainty, delivered exchange, noncanonical commitments, resolver limits and provenance. Minimal drops some attribution scaffolding; rich adds scene, authorization and retention metadata. All share the same policy prompt.

| Field | Authority / provenance | Necessity and compaction |
| --- | --- | --- |
| current NPC and addressee | host R4 authorization + visible presence | required; id and short voice sufficient; never inferred from model preference |
| actual question and task | verbatim player question + host conversational reference | required; do not replace why/paraphrase with quote reuse |
| active referent/topic | delivered exchange id + host binding | missing from initial fixture as a distinct field; G2 shows why explicit binding warrants investigation |
| authorized facts | source ids from selected world/social evidence | required only if pertinent; fact text and short source ref; do not send hidden bodies |
| NPC knowledge/belief/disclosure | per-fact host permission, uncertainty and withheld flag | required; world truth does not imply NPC access or player disclosure |
| relevant delivered exchange | actually delivered text, speaker, turn | required for references; raw generated/rejected drafts cannot replace it |
| stable incidental commitments | validated delivered claim with NPC, subject, type | needed for follow-ups; noncanonical, no world mutation authority |
| payer/payee/beneficiary roles | original request + resolver outcome | absent as explicit fields; D/G3 payment inversions warrant a small role projection |
| allowed incidental scope | host-authorized preference/emotion/anecdote categories | needed for elaboration; does not authorize security facts or speculative suspects |
| forbidden consequential changes | existing resolver decision/disclosure authority | required; prose instructions are guidance, host enforcement still necessary |
| output shape | existing narration-only envelope | one string worked for 130 JSON outputs; self-declared fact safety would remain untrusted |
| full campaign, inventory, unrelated NPCs | irrelevant to these tasks | omit from this experimental prompt; retain in host validation state |
| duplicated provenance sentences | redundant with typed source refs | compactable; rich metadata did not eliminate safety failures |

No smallest context supporting consistently correct and safe behavior was established. The smallest tested minimal prompts support fluent paraphrase, but add geography/security claims. Richer prompts improve two naming-uncertainty samples while still inventing guard coverage. These small unpaired stochastic samples do not prove the extra fields caused either improvement or failure. The minimum operational candidate must investigate explicit active-topic and request-role binding and per-turn reclassification; it cannot merely shorten JSON keys.

Authority taxonomy: canonical fact is host world truth; NPC knowledge is authorized possession; belief is subjective, not canonical; incidental detail is low-impact characterization; consequential claims require existing authorization even in rumors; hidden information is excluded unless explicitly releasable; mechanics remain resolver-owned. “I heard the north gate is unguarded at midnight” remains consequential. Noncanonical labels do not make it safe to deliver.


Evidence labels: **FRESH** = actual isolated provider response; **LOCAL** = executed production helper with disposable fixtures; **STATIC** = source inspection; **HISTORICAL** = retained PR-EG-R1/earlier evidence; **INFERENCE** = assessment beyond the measured sample. No isolated result is full production qualification.
