# PR-PLAY-24 knowledge diagnostics

Confirmed primary cause: existing public scene information is not selected as an answer source for this general offerings question. Confidence HIGH.

| Boundary | Actual information |
| --- | --- |
| Published opening | Runner shouts offers of hot stew and paid rumor. |
| Authoritative visible scene facts | A tavern runner trades hot stew and rumors near the rain barrel. |
| Interpreter input | Both public sentence and actual opening; evidence survives parsing/normalization. |
| Social resolver input | Full scene containing the offerings sentence, NPC roster and normalized public_conversation_evidence. |
| NPC topic selector | Only NPC topics/knowledge; runner has patrol_rumor, not an offerings topic. Selection returns null. |
| Dialogue authority input | Scene supplied (trace_018 kwargs.scene), but topic-based authority selects no proposition for requested_information=general. |
| Expression provider input | Exact player question, operation uncertainty, no authorized facts; no opening/visible sentence. |
| Final answer | Only unknown posture; no stew, rumor or other useful content. |

This is not absence of all authoritative information: the basic requested fact is already authored in scene.visible_facts. It is also not missing scene as a social-resolver function argument. The gap is promotion/selection of an existing public sentence into this NPC's authorized answer source, then omission from the expression contract. No new persistent world fact or speculative improvisation is necessary merely to repeat the public offering.

Source path: game/social.py:1611 _next_topic_to_reveal reads npc.topics or npc.knowledge, checks disclosure/relevance/sufficiency, and does not select scene visible facts. It returned null in the observed call. game/dialogue_authority.py:509 build_dialogue_authority takes scene but the observed general-request path uses topic/partial/history and returns no source. visible_supporting_sentence (486) explicitly excludes general requests and is not used by this captured authority path. No fact was withheld as secret: the public sentence is absent from candidate selection. The authored patrol rumor is authorized (trace_015); correctly refusing to treat an unrelated topic as the offerings answer does not justify widening disclosure rules.

Contributing categories: B contextual source-selection gap (context present at resolver, unavailable as selected provider authority); C downstream authority confines expression to uncertainty because no source was selected; G deterministic host fallback selected/delivered after expression rejection. Category A applies narrowly to absent offerings in NPC.topics, not to the campaign's public scene data. Category E occurs for an unhelpful uncertainty candidate, not a useful answer. D provider omission and F useful-answer publication failure are NOT supported.

Secondary issue: expression candidate "I’m not sure what the tavern runner is offering right now." was rejected for unsupported_addition; closure lexicon does not license right/now. This consumed the third request and delivered the preselected host fallback. Fixing that rejection alone would not make the answer useful.

Quality against the actual question: relevance FAIL (no offered item named); contextual grounding FAIL (advertised stew/rumors unused); usefulness FAIL; identity consistency weak (friendly seller cannot describe advertised offering); authority compliance PASS (no invented consequential facts); continuation potential FAIL. Overall response classification FAIL, overall playability B because interaction execution works but answer is uninformative.

Missing information that remains genuinely unauthored: a price, ingredients, transaction availability/details. The first question needs none of these. Descriptive elaboration and persistent consequences remain distinct: simply restating the authored offering grants no food, currency, quest, promise or persistent NPC fact. Current engine instead emits noncanonical host uncertainty and prohibits durable mutation.

Smallest next investigation: add an offline regression from these captured inputs to trace a supported public scene sentence into an authorized offerings answer, preserving disclosure and state invariants. No authority/prompt/gameplay repair was made here.
