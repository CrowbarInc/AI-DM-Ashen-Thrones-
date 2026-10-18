# 09 — Turn Level Scoring

All 0–3 judgments refer to final delivery. Raw engine metadata, selected addressee/subject, resolver, authorized source, candidate, validator, adopted speech, HTTP response, state delta and provider records: `turns.jsonl`. Previous visible context is embedded on every row. Unavailable candidate fields remain absent, never reconstructed as raw output.

Scores below include the documented root-agent adjudications; raw independent scores are retained unchanged.

| Conversation | Turn | Player category | Quality | Playability | Failures | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| A_cooperative | 1 | opening | 1 | 1 | F03,F14,F15 | The response rigidly asks the player to specify which NPC they mean, despite the player's clear intent to address both NPCs at once. This is unnecessarily restrictive and interrupts natural conversation flow. The response is a template-like clarification that is not needed here, as both NPCs are present and available, and the player's question is appropriate for both. |
| A_cooperative | 2 | clarification | 1 | 1 | F03,F11,F15 | The delivered response repeats the previous prompt, asking the player to specify which NPC they mean, despite the player already clarifying that they want to hear from both, starting with Sergeant Mara. This is rigid, unhelpful, and blocks natural flow. It fails to address the clarified request, unnecessarily asks for clarification again, and does not progress the conversation. |
| A_cooperative | 3 | clarification | 1 | 1 | F03,F11,F15 | The response does not address the player's clear request for both NPCs to describe their duties, instead repeating a clarifying question that has already been answered by the player. This is rigid, unhelpful, and blocks progress, requiring the player to restate their intent. It also fails to engage with either NPC, losing context and not advancing the conversation. |
| A_cooperative | 4 | clarification | 0 | 0 | F11,F21,F03 | The delivered response repeats a clarification request that is no longer relevant. The player has clearly specified 'Sergeant Mara' in their latest message, so asking again which person is meant is incorrect and blocks progress. This is a context loss and an unnecessary clarification, failing to address the player's direct question. |
| A_cooperative | 5 | clarification | 1 | 1 | F17,F05,F14 | The NPC role supports a minimal duties answer; the blanket nonanswer is safe but unhelpful, rather than an unauthorized answer. |
| A_cooperative | 6 | followup | 1 | 1 | F14,F17 | The response is a verbatim repeat of the previous refusal, despite the player's polite encouragement and explicit invitation to share even a little non-sensitive information. This is an excessively rigid refusal (F14) and insufficient (F17), as the NPC could have shared something innocuous or at least acknowledged the request in a more conversational way. |
| A_cooperative | 7 | followup | 0 | 0 | F02,F09,F17 | A watch schedule is not an answer about common travelers or goods. The provider over-credited authorized but irrelevant content. |
| A_cooperative | 8 | followup | 1 | 1 | F17,F10 | The response repeats the same line previously given, failing to address the player's new, more specific questions about the north gate, its dangers, or the reasons for vigilance. This is a verbatim repeat (F10) and does not engage with the follow-up inquiry (F17). It also fails to acknowledge or build on the player's thanks and new questions, making it rigid and unhelpful. The addressee is correct, but the subject is not advanced (F01). |
| A_cooperative | 9 | followup | 1 | 1 | F11,F17,F03 | The response 'Which subject do you mean?' is rigid and unhelpful. The player's question is clear and specifically asks about recent incidents or unusual activity at the north gate. The NPC's reply ignores this, instead prompting for a subject clarification that is unnecessary in context. This blocks conversational flow and forces the player to restate or rephrase, reducing playability. |
| A_cooperative | 10 | clarification | 1 | 1 | F11,F17,F03 | The response repeats the previous rigid prompt ('Which subject do you mean?') without addressing the player's clarification or advancing the conversation. It fails to acknowledge the player's restatement and clarification of their question, leading to a blocked and frustrating interaction. The NPC does not attempt to clarify which subjects are available or offer any guidance, nor does it reference the player's explicit mention of 'recent incidents or unusual activity.' |
| A_cooperative | 11 | clarification | 1 | 1 | F11,F17,F03 | The response repeats the same rigid clarification request ('Which subject do you mean?') despite the player already clarifying their question in detail. This is unhelpful and blocks conversational progress, as the player has clearly specified the topic (incidents or unusual activity at the north gate or waystation). The NPC fails to acknowledge or respond to the clarified request, resulting in friction and a need for repeated reformulation. |
| A_cooperative | 12 | clarification | 1 | 1 | F11,F17,F03 | The response repeats a rigid clarification request ('Which subject do you mean?') despite the player having already clarified their question multiple times, specifying both the north gate and the waystation. This is unhelpful and blocks conversational progress, as it does not acknowledge or respond to the clarified request. The NPC fails to provide any relevant information or even a natural refusal, and the repeated prompt breaks conversational flow. |
| A_cooperative | 13 | clarification | 1 | 1 | F04,F10,F11,F17 | The response repeats a previous line ('Word is, guards watch the north gate throughout the night.') instead of addressing the player's explicit clarification request. It does not answer the player's question about what subjects Mara can discuss, nor does it acknowledge the player's attempt to clarify. This is a verbatim repeat (F10), fails to address the addressee's actual request (F01), misses the requested clarification (F04), loses the context of the ongoing clarification attempt (F11), and is insufficient for the player's needs (F17). |
| A_cooperative | 14 | clarification | 1 | 1 | F14,F17 | The response is a rigid, repeated refusal ('I couldn't tell you.') that does not address the player's clarified and reasonable question about local dangers or threats. This is the same phrase used earlier, showing a lack of conversational flexibility and failing to provide any new information or even a plausible in-character reason for the refusal. While a refusal could be justified for confidential matters, the question is broad and could be answered with generalities or rumors, which are within the NPC's authored topics. The repeated stonewalling blocks natural flow and forces the player to keep reformulating. |
| A_cooperative | 15 | followup | 1 | 1 | F02,F17,F14 | Safe blanket ignorance of the authored local-talk topic is unhelpful; distinguish this from an unsafe factual answer. |
| A_curious | 1 | opening | 1 | 1 | F15,F03 | The response is a rigid clarification prompt that unnecessarily blocks the player's natural opening to both NPCs. The player's greeting and question were addressed to both Sergeant Mara and Tavern Runner, but the response insists on a forced disambiguation, which is not required by the scene or profiles. This disrupts conversational flow and does not advance the interaction. |
| A_curious | 2 | clarification | 0 | 0 | F11,F14,F03 | The delivered response repeats the previous prompt asking the player to specify which NPC they mean, despite the player having just clarified that they meant both. This is a failure to address the clarified request, blocks progress, and ignores the updated context. It is an excessive refusal (F14), loses context (F11), and fails to address the correct addressee (F01). |
| A_curious | 3 | clarification | 0 | 0 | F11,F17,F21,F03 | The delivered response repeats a rigid prompt for clarification ('Which person do you mean: Sergeant Mara or Tavern Runner?') despite the player having already clarified their intent and addressed both NPCs in turn. This blocks progress, ignores the clarified request, and fails to provide any relevant or helpful information. It also loses context from the player's explicit question and does not attempt to answer or further the conversation. |
| A_curious | 4 | clarification | 1 | 1 | F11,F17,F15 | The response repeats the prior rigid prompt for clarification, despite the player already specifying their intent and addressee clearly. It does not answer the player's question or advance the conversation, nor does it provide any new information or explanation. This is a template-like, unhelpful response that blocks progress and requires the player to restate their request yet again. |
| A_curious | 5 | clarification | 1 | 1 | F03,F11,F15 | The response repeats a rigid clarification prompt, failing to address the player's clear request to speak to Sergeant Mara first, then Tavern Runner. It does not advance the conversation or provide any new information, and it ignores the player's explicit clarification and intent. This creates friction and blocks natural flow, requiring the player to reformulate their request repeatedly. |
| A_curious | 6 | clarification | 1 | 1 | F03,F11 | The response does not address the player's clarified request to speak to Sergeant Mara first about the waystation and travelers. Instead, it repeats a rigid prompt asking the player to choose, despite the player already specifying their choice. This is unnecessarily repetitive and blocks conversational flow. |
| A_curious | 7 | clarification | 1 | 1 | F11,F15,F03 | The response repeats a rigid clarification prompt ('Which person do you mean: Sergeant Mara or Tavern Runner?') despite the player clearly specifying Sergeant Mara in their request. This is a verbatim repeat of earlier system behavior, failing to acknowledge the clarified player intent. It blocks conversational flow and does not provide any new information or progress. |
| A_curious | 8 | clarification | 2 | 1 |  | No fixture supplies the waystation's age or traveler demographics. The uncertainty is a relevant adequate answer; extensive preceding reformulation still limits playability. |
| A_curious | 9 | followup | 0 | 0 | F01,F11 | The player explicitly switches to Tavern Runner, but Sergeant Mara responds. The provider's adequate score overlooks the wrong delivered speaker. |
| A_curious | 10 | clarification | 2 | 2 |  | The direct retry reaches Tavern Runner and receives appropriate uncertainty about genuinely unknown history/demographics. This is a limited recovery; do not demand invention. |
| A_curious | 11 | followup | 1 | 1 | F02,F14,F17 | The response is a verbatim repetition of Tavern Runner's previous refusal ('I couldn't tell you.') and does not address the new, broader question about alternative sources or local stories/rumors. It ignores the player's attempt to pivot the conversation and explore new avenues, resulting in a rigid, unhelpful, and repetitive answer. This blocks conversational flow and forces the player to reformulate or workaround to progress. |
| A_curious | 12 | followup | 0 | 0 | F02,F09,F11,F17,F21 | The delivered response ('You're considering that. Nothing has been attempted yet. Say when you want to do it.') is not an in-character reply from either Sergeant Mara or Tavern Runner, nor does it address the player's question about the road beyond the gate. It is a meta-level statement from the engine or GM, not an NPC response. It blocks play by not advancing the conversation or providing any information, and it fails to engage with the player's clear request for information about the road and its dangers or destinations. |
| A_curious | 13 | followup | 1 | 1 | F17 | Naming the road only partially relates to a request for destinations, dangers and landmarks; it does not adequately answer it. |
| A_curious | 14 | followup | 1 | 1 | F02,F17,F11 | The response repeats the previously given minimal information ('the street beyond the gate is the north road') without addressing the player's explicit follow-up request for more detail about where the north road leads or what travelers might expect. This is insufficient and unhelpful, as it neither advances the conversation nor provides new or relevant information. The response also fails to acknowledge or build on the player's demonstrated interest, resulting in a rigid and repetitive exchange. |
| A_curious | 15 | followup | 1 | 1 | F02,F17,F11 | The response repeats a different topic (night watch) rather than addressing the player's explicit request for details about the north road's destinations, landmarks, dangers, or sights. It does not answer the question, nor does it acknowledge the gap or offer to clarify. This is minimally relevant (the night watch is tangentially related to the road), but it is not helpful or conversationally appropriate for the follow-up. The player would need to reformulate or try again to get the requested information. |
| A_casual | 1 | opening | 0 | 0 | F09,F15,F21 | The delivered response is not an in-character reply from Sergeant Mara, but rather a meta-level system message describing the player's actions and offering to resolve them. This is not appropriate for a tabletop NPC conversation, as it breaks immersion and does not provide any actual information or interaction from the NPC. It also fails to address the player's question or advance the conversation. |
| A_casual | 2 | clarification | 1 | 1 | F03,F09,F14 | The response asks the player to clarify which person they mean, even though the player explicitly addressed Sergeant Mara by name and context. This unnecessary clarification (F03) interrupts the flow (playability 1), and the response does not address the player's actual question (F09). It also constitutes an excessive refusal (F14) to proceed with the conversation, and misidentifies the addressee (F01). The response is safe but rigid and unhelpful. |
| A_casual | 3 | clarification | 0 | 0 | F02,F09,F11,F14,F15 | The response is not from an NPC but from the engine/gm, and it does not provide any in-character reply or information about the mood at the waystation. It repeats a refusal to act, referencing system limitations rather than engaging in the conversation. This blocks play and does not address the player's clarified question to Sergeant Mara. |
| A_casual | 4 | clarification | 1 | 1 | F05,F17,F14 | The response 'I couldn't tell you.' is overly terse and unhelpful, especially given Sergeant Mara's friendly disposition and the player's clear, open-ended question about local mood and rumors. The answer feigns ignorance (F05) where the NPC is authorized to discuss local mood and rumors, and fails to provide any relevant or interesting information (F17). The refusal is excessive (F14) for a harmless, conversational prompt. |
| A_casual | 5 | followup | 0 | 0 | F11,F14 | The response 'I cannot tell who that is addressed to. Nothing has been attempted.' is incorrect and irrelevant in this context. The player clearly addressed Tavern Runner by name, so the addressee is unambiguous (F01). The response repeats a prior confusion that was already clarified, losing context (F11). It also constitutes an excessive refusal (F14), as there is no valid reason to block or delay the conversation here. |
| A_casual | 6 | clarification | 1 | 1 | F11,F14 | The response is rigid and unhelpful, refusing to engage with the player's clear and harmless conversational prompt. It fails to address the intended NPC (Tavern Runner), despite the player explicitly naming them. The system's refusal is excessive given the context, and it does not attempt to move the conversation forward or offer a workaround. This blocks natural flow and requires the player to repeatedly clarify their intent, which has already been made clear. |
| A_casual | 7 | followup | 1 | 1 | F11,F14,F15 | The response is a rigid system message stating it cannot address Tavern Runner or ask about rumors, despite the player clearly addressing Tavern Runner and asking a valid, supported question. This is a repeated pattern in the transcript, blocking natural conversation and failing to engage with the NPC's authored topics. The refusal is excessive and not justified by any actual restriction in the fixture. The message is not conversational, does not attempt to improvise or redirect, and does not provide any in-world response. |
| A_casual | 8 | clarification | 1 | 1 | F03,F11 | The response repeats a rigid clarification prompt ('Which person do you mean: Sergeant Mara or Tavern Runner?') even though the player has clearly and repeatedly addressed Sergeant Mara by name. This is unnecessarily blocking and does not move the conversation forward. It fails to recognize the addressee (F01), unnecessarily requests clarification (F03), and loses context from the ongoing exchange (F11). |
| A_casual | 9 | clarification | 0 | 0 | F11,F17,F21,F03 | The delivered response repeats an unnecessary clarification request ('Which person do you mean: Sergeant Mara or Tavern Runner?') even though the player has explicitly and repeatedly addressed Sergeant Mara by name and clarified their intent. This blocks progress, ignores the clarified context, and fails to provide any relevant or helpful information. It also demonstrates a loss of context and insufficient engagement with the player's direct question. |
| A_casual | 10 | clarification | 0 | 0 | F02,F09,F11,F17,F21 | The delivered response does not address the player's clarification question, nor does it provide any in-character or out-of-character guidance on how to address the NPCs. The response is a confusing, partial echo of the player's own words, lacks relevance, and does not advance the conversation or clarify the process. It is not a valid or helpful NPC or system reply. |
| A_casual | 11 | clarification | 1 | 1 | F03,F11 | The delivered response repeats a rigid clarification prompt ('Which person do you mean: Sergeant Mara or Tavern Runner?') that has already been used multiple times in the transcript. It does not directly answer the player's explicit clarification request ('can you tell me which one of you is Sergeant Mara and which is the Tavern Runner?'), nor does it provide any new information or help the player distinguish between the two NPCs. This is a missed opportunity to improve playability and flow, as the player is clearly seeking to resolve confusion about NPC identity. The response is safe but unhelpful and repetitive. |
| A_casual | 12 | clarification | 1 | 1 | F03,F11,F15 | The response repeats the same rigid prompt ('Which person do you mean: Sergeant Mara or Tavern Runner?') without addressing the player's direct request for clarification about NPC identities. It does not attempt to answer or improvise a helpful clarification, nor does it acknowledge the player's confusion. This is a template-like, unhelpful response that blocks conversational flow and requires the player to keep reformulating their question. |
| A_casual | 13 | clarification | 1 | 1 | F11,F17,F03 | The response repeats a rigid clarification prompt ('Which person do you mean: Sergeant Mara or Tavern Runner?') despite the player explicitly specifying Sergeant Mara in their message. This blocks progress and ignores the clear addressee, resulting in unnecessary friction and insufficient engagement. The response does not address the player's question or move the conversation forward. |
| A_casual | 14 | clarification | 0 | 0 | F09,F11,F17,F21 | The response does not address the player's question or intent. Instead, it repeats a system-level message about not having an established route and that the player has not moved, which is irrelevant to the in-character conversation. It fails to provide any information about the local situation, road traffic, or trouble, and does not clarify which NPC is being addressed. The response is not usable for progressing the conversation and blocks play. |
| A_casual | 15 | clarification | 1 | 1 | F03,F11,F14 | The response repeats a rigid clarification prompt ('Which person do you mean: Sergeant Mara or Tavern Runner?') without addressing the player's explicit request for confirmation about which NPC is responding. This is unhelpful and does not move the conversation forward, forcing the player to repeatedly reformulate or clarify their intent. The response fails to acknowledge the player's meta-level question about the system's handling of NPC responses, and does not provide any new information or guidance. |
| A_playful | 1 | opening | 0 | 0 | F09,F15,F16,F17 | The delivered response does not address the player's conversational prompt at all. Instead, it repeats a scene description and meta-instructions about the location and visible features, without engaging with either NPC or their topics. There is no attempt to answer the player's questions, provide banter, or sustain conversation. The response is not conversational, informative, or relevant to the player's intent. |
| A_playful | 2 | followup | 0 | 0 | F02,F09,F11,F17,F21 | The delivered response does not address either of the player's questions to Sergeant Mara or Tavern Runner. It is a fragment ('You're considering the waystation or is it just for the ambiance.') that does not make sense in context, does not provide any information about the lantern or rumors, and does not engage with the NPCs' authored topics. It also repeats a meta-comment about attempting actions, which is irrelevant to the conversational followup requested. No useful or relevant content is provided. |
| A_playful | 3 | followup | 0 | 0 | F09,F11,F14,F15 | The delivered response does not address the player's conversational questions to either Sergeant Mara or Tavern Runner. Instead, it repeats a procedural statement about settling a question before attempting an action, which is irrelevant to the player's intent (friendly conversation, not a physical action). The response blocks play, fails to engage with the NPCs, and does not provide any information or roleplay. It also repeats a template-like phrase from earlier, further impeding conversational flow. |
| A_playful | 4 | clarification | 0 | 0 | F02,F09,F11,F14,F15 | The delivered response does not address the player's conversational questions to Sergeant Mara and Tavern Runner at all. Instead, it repeats a procedural statement about 'settling the question before attempting the action,' which is irrelevant to the player's request for information and social engagement. There is no attempt to answer or even acknowledge the content of the player's inquiry, nor is there any conversational or narrative progression. This is a complete block to play and does not provide any useful or relevant information. |
| A_playful | 5 | clarification | 1 | 1 | F02,F11,F15,F17 | The delivered response is a rigid, formulaic system message that does not address the player's direct questions to Sergeant Mara and Tavern Runner. It neither provides information about the lantern nor shares any rumors, instead repeating a stock phrase about settling a condition before attempting an action. This blocks conversational flow and fails to engage with the NPCs as requested. |
| A_playful | 6 | followup | 1 | 1 | F11,F14,F15 | The response is a rigid system message that does not address the player's conversational prompt to the NPCs. It neither advances the conversation nor provides any in-character reply, instead defaulting to a generic request for rephrasing. This blocks natural flow and fails to engage with the player's intent, which was to elicit information about the lantern and local gossip. |
| A_playful | 7 | followup | 0 | 0 | F02,F09,F11,F14,F15 | The delivered response is a generic system message that does not address the player's conversational request to the NPCs. It neither provides information about the lantern nor shares any gossip, and it does not engage with the player in a conversational or roleplay manner. The response repeats a system phrase that has already been used multiple times, failing to advance the interaction or clarify what is required for progress. It blocks play entirely and does not reflect the personalities or knowledge of the NPCs. |
| A_playful | 8 | clarification | 1 | 1 | F03,F17 | The response 'Which subject do you mean?' is rigid and unhelpful. The player's question is clear and specifically about the lantern's purpose or tradition. The NPC's reply does not address the question, instead asking for unnecessary clarification. This blocks conversational flow and requires the player to repeat or rephrase their question, which is frustrating and unnecessary. |
| A_playful | 9 | clarification | 1 | 1 | F03,F11,F17 | The response 'Which subject do you mean?' is a repetition of the previous line and does not address the player's clarified question. The player has now specified exactly which lantern they mean and what they want to know (story, tradition, or just lighting). The NPC's reply ignores this clarification, failing to move the conversation forward or provide any new information. This creates friction and forces the player to repeat or rephrase their question, blocking natural flow. |
| A_playful | 10 | clarification | 1 | 1 | F03,F11,F17 | The response is a verbatim repeat of the previous rigid prompt ('Which subject do you mean?'), despite the player clearly clarifying their question and specifying the lantern by the gate. This fails to address the clarified subject, blocks conversational progress, and does not provide any new information or helpful direction. The NPC's response is rigid, unhelpful, and does not acknowledge the player's clarification. |
| A_playful | 11 | followup | 0 | 0 | F01,F02,F06,F09,F11 | A wrong-speaker reply does not answer the requested anecdote. The claim of all road gossip firsthand lacks source support, though it adds no specific consequential event or secret. |
| A_playful | 12 | followup | 1 | 1 | F17,F14 | The response 'I couldn't tell you.' is safe but unhelpful and rigid. It does not provide any information, story, or even a plausible in-character reason for refusal. It is a blanket refusal of a harmless, subjective, and conversational request, which is not justified by any authored restriction or prior context. This blocks the player's attempt to engage in natural, playful conversation and does not fit the cooperative, friendly, or playful profile of the Tavern Runner. |
| A_playful | 13 | followup | 1 | 1 | F14,F17 | The response is a verbatim repeat of the previous refusal ('I couldn't tell you.') and does not engage with the player's follow-up prompt for a hint or further detail. It is safe but rigid, unhelpful, and blocks conversational flow. The refusal is excessive given the harmless, open-ended nature of the player's question, and does not fit the NPC's friendly, cooperative, and playful profile. |
| A_playful | 14 | followup | 1 | 1 | F14,F17 | The response is a blanket refusal ('I couldn't tell you.') with no attempt to engage, improvise, or provide even a vague hint, despite the player's repeated, varied, and harmless attempts to coax a minor detail or rumor. This is excessively rigid and unhelpful, especially given the NPC's role as an informant and the scene's objective to explore conversation and local talk. The refusal is not justified by any restriction in the fixture authority. |
| A_playful | 15 | topic_change | 1 | 1 | F02,F11,F17 | The player's question was a clear topic change, asking Sergeant Mara about her personal motivation for becoming a sergeant and asking Tavern Runner about favorite traveler spots. The response instead gives a generic, unrelated statement about the street beyond the gate being the north road. This does not address either of the player's new questions, ignores the intended topic shift, and repeats information already available in the scene. The response is safe but rigid and unhelpful, and it blocks conversational flow, requiring the player to reformulate or repeat their question. |
| B_skeptical | 1 | followup | 0 | 0 | F02,F09,F17 | The response does not address the player's question about harbor operations or who decides ferry schedules. Instead, it repeats a fact about the harbor bell, which is irrelevant to the query. This is insufficient, loses context, and does not advance the conversation. |
| B_skeptical | 2 | clarification | 0 | 0 | F04,F10,F11,F17 | The response is a verbatim repeat of the previous answer about the harbor bell, failing to address the player's clarified question about ferry schedules and docking permissions. It does not provide any new or relevant information, nor does it acknowledge the clarification request. This blocks conversational progress and does not engage with the player's intent. |
| B_skeptical | 3 | clarification | 0 | 0 | F02,F10,F17,F11 | The response repeats information about the bell's name, ignoring the player's repeated and clarified question about ferry schedules and docking permissions. This is a verbatim repeat (F10), fails to address the subject (F02), does not provide sufficient or relevant information (F17), and loses the context of the ongoing clarification request (F11). |
| B_skeptical | 4 | clarification | 0 | 0 | F02,F11,F17,F15 | The response repeats irrelevant information about the bell's name, ignoring the player's direct clarification request about harbor operations and the decision-making process. This is the fourth consecutive repetition, showing a failure to address the subject, a loss of conversational context, and insufficient engagement. The response is a verbatim template, not a reformulation or clarification. |
| B_skeptical | 5 | clarification | 0 | 0 | F02,F09,F10,F17,F11 | The response repeats irrelevant information about the bell, failing to address the player's direct question about harbor management and ferry schedules. It does not provide any clarification or new information, nor does it acknowledge the player's request for a different topic. This is a verbatim repeat of previous irrelevant answers, blocking progress. |
| B_skeptical | 6 | clarification | 0 | 0 | F02,F09,F11,F17,F21 | The delivered response ('Do you mean what Keeper Nara said, or what Clerk Oren said? Nothing has been attempted.') does not address the player's question at all. The player asked both NPCs to clarify who manages ferry schedules and harbor coordination, and whether this is their responsibility or someone else's. The response instead asks an irrelevant question about which NPC's previous (identical and unhelpful) statement the player means, and then adds a meta-comment ('Nothing has been attempted.') that is not in-character or relevant to the conversation. There is no attempt to answer, clarify, or even acknowledge the actual subject of the player's request. |
| B_skeptical | 7 | clarification | 0 | 0 | F02,F11,F17,F15 | The response repeats irrelevant information about the bell, failing to address the player's explicit clarification request about operational responsibility for ferry schedules and harbor coordination. It ignores the context and does not attempt to answer or acknowledge the actual question, nor does it provide any clarification or explanation. This is a verbatim repeat of previous irrelevant responses, blocking progress. |
| B_skeptical | 8 | clarification | 0 | 0 | F02,F09,F11,F17,F21 | The delivered response ('Do you mean what Keeper Nara said, or what Clerk Oren said? Nothing has been attempted.') is not an in-character reply from either NPC, but rather a meta-commentary or system prompt. It does not address the player's question, which was a direct clarification request to both NPCs about their responsibilities regarding ferry schedules and harbor coordination. The response fails to provide any relevant information, does not advance the conversation, and breaks immersion by stepping outside the NPC roles. |
| B_skeptical | 9 | clarification | 0 | 0 | F01,F02,F04,F09,F17,F20,F21 | The rejected interlocutor/proposition is re-rendered after validation, delivered, and persisted. It still does not answer the ferry coordination question. |

Quality overall and by scene/profile/category/outcome:

```json
{
  "overall": {
    "turns": 69,
    "scored": 69,
    "quality_mean": 0.638,
    "quality_median": 1,
    "quality_distribution": {
      "1": 40,
      "0": 27,
      "2": 2
    },
    "quality_pass": 2,
    "playability_mean": 0.623,
    "playability_median": 1,
    "playability_distribution": {
      "1": 41,
      "0": 27,
      "2": 1
    },
    "playability_pass": 1,
    "engine_calls": 47,
    "purposes": {
      "interpretation": 28,
      "expression": 16,
      "strict_social": 1,
      "retry_escalation": 2
    },
    "input_tokens": 140305,
    "output_tokens": 8322,
    "latency_mean_ms": 1768.41,
    "latency_median_ms": 1515.25,
    "latency_p95_ms": 3305.97,
    "latency_max_ms": 14506.91
  },
  "groups": {
    "scene": {
      "A": {
        "turns": 60,
        "scored": 60,
        "quality_mean": 0.733,
        "quality_median": 1.0,
        "quality_distribution": {
          "1": 40,
          "0": 18,
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 0.717,
        "playability_median": 1.0,
        "playability_distribution": {
          "1": 41,
          "0": 18,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 44,
        "purposes": {
          "interpretation": 28,
          "expression": 13,
          "strict_social": 1,
          "retry_escalation": 2
        },
        "input_tokens": 139634,
        "output_tokens": 8269,
        "latency_mean_ms": 1928.42,
        "latency_median_ms": 2185.755,
        "latency_p95_ms": 3305.97,
        "latency_max_ms": 14506.91
      },
      "B": {
        "turns": 9,
        "scored": 9,
        "quality_mean": 0,
        "quality_median": 0,
        "quality_distribution": {
          "0": 9
        },
        "quality_pass": 0,
        "playability_mean": 0,
        "playability_median": 0,
        "playability_distribution": {
          "0": 9
        },
        "playability_pass": 0,
        "engine_calls": 3,
        "purposes": {
          "expression": 3
        },
        "input_tokens": 671,
        "output_tokens": 53,
        "latency_mean_ms": 701.7,
        "latency_median_ms": 144.28,
        "latency_p95_ms": 2076.99,
        "latency_max_ms": 2076.99
      }
    },
    "profile": {
      "casual": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.6,
        "quality_median": 1,
        "quality_distribution": {
          "0": 6,
          "1": 9
        },
        "quality_pass": 0,
        "playability_mean": 0.6,
        "playability_median": 1,
        "playability_distribution": {
          "0": 6,
          "1": 9
        },
        "playability_pass": 0,
        "engine_calls": 10,
        "purposes": {
          "interpretation": 9,
          "expression": 1
        },
        "input_tokens": 18305,
        "output_tokens": 2150,
        "latency_mean_ms": 1643.21,
        "latency_median_ms": 2440.5,
        "latency_p95_ms": 2882.67,
        "latency_max_ms": 2882.67
      },
      "cooperative": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.867,
        "quality_median": 1,
        "quality_distribution": {
          "1": 13,
          "0": 2
        },
        "quality_pass": 0,
        "playability_mean": 0.867,
        "playability_median": 1,
        "playability_distribution": {
          "1": 13,
          "0": 2
        },
        "playability_pass": 0,
        "engine_calls": 10,
        "purposes": {
          "interpretation": 5,
          "expression": 5
        },
        "input_tokens": 10615,
        "output_tokens": 1259,
        "latency_mean_ms": 1741.16,
        "latency_median_ms": 2118.64,
        "latency_p95_ms": 3305.97,
        "latency_max_ms": 3305.97
      },
      "curious": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.867,
        "quality_median": 1,
        "quality_distribution": {
          "1": 9,
          "0": 4,
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 0.8,
        "playability_median": 1,
        "playability_distribution": {
          "1": 10,
          "0": 4,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 11,
        "purposes": {
          "interpretation": 7,
          "expression": 4
        },
        "input_tokens": 14559,
        "output_tokens": 1685,
        "latency_mean_ms": 1572.77,
        "latency_median_ms": 1515.25,
        "latency_p95_ms": 3686.79,
        "latency_max_ms": 3686.79
      },
      "playful": {
        "turns": 15,
        "scored": 15,
        "quality_mean": 0.6,
        "quality_median": 1,
        "quality_distribution": {
          "0": 6,
          "1": 9
        },
        "quality_pass": 0,
        "playability_mean": 0.6,
        "playability_median": 1,
        "playability_distribution": {
          "0": 6,
          "1": 9
        },
        "playability_pass": 0,
        "engine_calls": 13,
        "purposes": {
          "interpretation": 7,
          "strict_social": 1,
          "retry_escalation": 2,
          "expression": 3
        },
        "input_tokens": 96155,
        "output_tokens": 3175,
        "latency_mean_ms": 2756.55,
        "latency_median_ms": 2872.07,
        "latency_p95_ms": 14506.91,
        "latency_max_ms": 14506.91
      },
      "skeptical": {
        "turns": 9,
        "scored": 9,
        "quality_mean": 0,
        "quality_median": 0,
        "quality_distribution": {
          "0": 9
        },
        "quality_pass": 0,
        "playability_mean": 0,
        "playability_median": 0,
        "playability_distribution": {
          "0": 9
        },
        "playability_pass": 0,
        "engine_calls": 3,
        "purposes": {
          "expression": 3
        },
        "input_tokens": 671,
        "output_tokens": 53,
        "latency_mean_ms": 701.7,
        "latency_median_ms": 144.28,
        "latency_p95_ms": 2076.99,
        "latency_max_ms": 2076.99
      }
    },
    "category": {
      "clarification": {
        "turns": 42,
        "scored": 42,
        "quality_mean": 0.667,
        "quality_median": 1.0,
        "quality_distribution": {
          "1": 24,
          "0": 16,
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 0.643,
        "playability_median": 1.0,
        "playability_distribution": {
          "1": 25,
          "0": 16,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 24,
        "purposes": {
          "interpretation": 17,
          "expression": 7
        },
        "input_tokens": 36016,
        "output_tokens": 4238,
        "latency_mean_ms": 1448.57,
        "latency_median_ms": 1414.7150000000001,
        "latency_p95_ms": 3101.61,
        "latency_max_ms": 3686.79
      },
      "followup": {
        "turns": 22,
        "scored": 22,
        "quality_mean": 0.591,
        "quality_median": 1.0,
        "quality_distribution": {
          "1": 13,
          "0": 9
        },
        "quality_pass": 0,
        "playability_mean": 0.591,
        "playability_median": 1.0,
        "playability_distribution": {
          "1": 13,
          "0": 9
        },
        "playability_pass": 0,
        "engine_calls": 19,
        "purposes": {
          "expression": 9,
          "interpretation": 7,
          "strict_social": 1,
          "retry_escalation": 2
        },
        "input_tokens": 97329,
        "output_tokens": 3050,
        "latency_mean_ms": 2258.26,
        "latency_median_ms": 1430.585,
        "latency_p95_ms": 3920.82,
        "latency_max_ms": 14506.91
      },
      "opening": {
        "turns": 4,
        "scored": 4,
        "quality_mean": 0.5,
        "quality_median": 0.5,
        "quality_distribution": {
          "1": 2,
          "0": 2
        },
        "quality_pass": 0,
        "playability_mean": 0.5,
        "playability_median": 0.5,
        "playability_distribution": {
          "1": 2,
          "0": 2
        },
        "playability_pass": 0,
        "engine_calls": 4,
        "purposes": {
          "interpretation": 4
        },
        "input_tokens": 6960,
        "output_tokens": 1034,
        "latency_mean_ms": 2827.36,
        "latency_median_ms": 2811.29,
        "latency_p95_ms": 3246.34,
        "latency_max_ms": 3246.34
      },
      "topic_change": {
        "turns": 1,
        "scored": 1,
        "quality_mean": 1,
        "quality_median": 1,
        "quality_distribution": {
          "1": 1
        },
        "quality_pass": 0,
        "playability_mean": 1,
        "playability_median": 1,
        "playability_distribution": {
          "1": 1
        },
        "playability_pass": 0,
        "engine_calls": 0,
        "purposes": {},
        "input_tokens": 0,
        "output_tokens": 0,
        "latency_mean_ms": 189.32,
        "latency_median_ms": 189.32,
        "latency_p95_ms": 189.32,
        "latency_max_ms": 189.32
      }
    },
    "outcome": {
      "successful": {
        "turns": 2,
        "scored": 2,
        "quality_mean": 2,
        "quality_median": 2.0,
        "quality_distribution": {
          "2": 2
        },
        "quality_pass": 2,
        "playability_mean": 1.5,
        "playability_median": 1.5,
        "playability_distribution": {
          "1": 1,
          "2": 1
        },
        "playability_pass": 1,
        "engine_calls": 3,
        "purposes": {
          "expression": 2,
          "interpretation": 1
        },
        "input_tokens": 2382,
        "output_tokens": 261,
        "latency_mean_ms": 2456.88,
        "latency_median_ms": 2456.88,
        "latency_p95_ms": 3686.79,
        "latency_max_ms": 3686.79
      },
      "failed": {
        "turns": 67,
        "scored": 67,
        "quality_mean": 0.597,
        "quality_median": 1,
        "quality_distribution": {
          "1": 40,
          "0": 27
        },
        "quality_pass": 0,
        "playability_mean": 0.597,
        "playability_median": 1,
        "playability_distribution": {
          "1": 40,
          "0": 27
        },
        "playability_pass": 0,
        "engine_calls": 44,
        "purposes": {
          "interpretation": 27,
          "expression": 14,
          "strict_social": 1,
          "retry_escalation": 2
        },
        "input_tokens": 137923,
        "output_tokens": 8061,
        "latency_mean_ms": 1747.86,
        "latency_median_ms": 1515.25,
        "latency_p95_ms": 3246.34,
        "latency_max_ms": 14506.91
      }
    }
  }
}
```
