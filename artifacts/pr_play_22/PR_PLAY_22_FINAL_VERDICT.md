# PR-PLAY-22 final verdict

Status: PARTIAL (experiment executed and evidenced; stop-rule deviation). Overall: C — NOT CURRENTLY PLAYABLE for the tested ordinary NPC sequence. A functional short RPG session was not demonstrated. This does not establish that every possible single-action phrasing fails.

| Dimension | Verdict | Evidence |
|---|---|---|
| Responsiveness | FAIL | Correctly understood T1 question yields host refusal rather than answer. |
| Continuity | FAIL | No NPC dialogue established; T2/T3 repeat T1 refusal. Post-failure inputs are themselves flawed. |
| NPC interaction | FAIL | Zero NPC lines or offering answers. |
| Agency | PARTIAL | No action executed; T4 offers a clarification choice for a supported first step. |
| State integrity | PASS in observed scope | Consequential state unchanged; no invented completion. Mutating subsystems untested. |
| Narrative coherence | FAIL | Opening offers an NPC; routine approach/question leads to system-level refusal. |
| Reliability | PARTIAL | All HTTP calls complete, but zero successful NPC turns. |
| Performance | PARTIAL | Short API times, but tokens purchase no useful NPC dialogue; successful-session cost untested. |

1. Initialization succeeded: accepted structured plan, renderer success, published opening and campaign_started=true.
2. Provider requests: 4 total (1 opening, 3 interpretation).
3. Ordinary turns attempted: 4.
4. Ordinary turns completed: 4 HTTP responses; 0 successful intended gameplay interactions.
5. AI-DM addresses actions: interpretation recognizes T1; player-facing response fails to answer it.
6. NPC interaction: failed; no dialogue reached.
7. Conversational continuity: no viable NPC sequence established; repeated refusal and flawed post-failure prompts.
8. Meaningful choices: not realized; T4 limited clarification only.
9. State changes: authorized opening and conversation/log bookkeeping; no unauthorized mutation observed.
10. Unsupported consequences narrated: none observed.
11. Hidden information: protected in observed payloads (True); key/exact-string checks are bounded, not a semantic proof.
12. Provider responses rejected: no malformed/schema/parser response rejection observed. Host blocked T1 action eligibility, distinct from provider contract rejection.
13. Average ordinary API latency: 2.476s.
14. Total consumption: 9495 tokens (8755 input, 740 output).
15. Known failure correlation: concrete conversational_clarify instead of social route resembles existing routing test; identical root cause not proved.
16. Functional short RPG session: not demonstrated; tested opening-to-NPC path blocked at T1.
17. Highest-priority next step: offline investigation of exact approach-NPC MOVE binding and compound rejection, without relaxing authority.

First decisive failure: T1 proposal_not_eligible. Actual controller stop: no_supported_consequence_followup before T5; budget still had two requests. No new live attempt authorized or performed.

PROTOCOL DEVIATION: T1 already made the intended NPC sequence unusable. The controller checked HTTP/provider errors but failed to detect this host-generated semantic dead end. It submitted T2–T4 before stopping, and its raw ordinary_completed=4 counter counts HTTP success, not gameplay success. Those raw records are preserved. Review counts: 4 attempted, 4 HTTP responses, 0 successful NPC/gameplay interactions. T2–T4 are post-failure diagnostic observations, not a valid continuation or recovery. No restart, provider retry, replacement initialization, or extra live run occurred.

No production changes, commits or pushes. Stop and await external review.
