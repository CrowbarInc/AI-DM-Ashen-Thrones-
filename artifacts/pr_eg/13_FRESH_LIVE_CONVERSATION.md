# 13 — Fresh Live Conversation

Final run: `tools/validate_pr_eg.py`, disposable campaign, `POST /api/chat?ui_mode=player`, model `gpt-4.1-mini-2025-04-14`. Full records, including authorization objects, are in `live_qualification.json`. An earlier run of the same script, before quote recovery, is `live_qualification_before_quote_recovery.json`.

16 provider calls. 145,400 input tokens. One retry (turn 3). Wall clock 44.6 seconds.

## Transcript

1. Player: “Could you describe the courtyard?”
   Response: a factual courtyard list, including the lantern, the barred side gate, and that Sergeant Mara watches the road and looks concerned.
   Authority: none. This stayed a GM description. One interpretation call, 1,704 input tokens, 3,981 ms. State unchanged.

2. Player: “I ask Sergeant Mara what the street beyond the gate is called.”
   Response: “Sergeant Mara mutters, ‘Word is, the street beyond the gate is the north road.’”
   Authorization: npc_directed, explicit, executable, ask. Requested information: general. Posture: established. Improvisation: no. Topic `street` revealed in the social record. One interpretation and one strict-social call, no retry, 26,258 input tokens, 5,243 ms. Turn counter and clocks changed. Topics did not.

3. Player: “What did you mean by that?”
   Response: “Sergeant Mara says, ‘I couldn’t tell you.’”
   She had just named the road. This does not continue that answer. Three calls, one retry, 52,957 input tokens. Turn counter and clocks changed. Topics did not.

4. Player: “Has anyone been keeping an eye on it after dark?”
   Response: “That has not been established in the information available to you.”
   Class: internal. Authorization and dialogue authority are null. The question did not become Mara’s. One interpretation call, 1,937 input tokens. State unchanged. This fails relevance and naturalness. The harness marked naturalness true because it only looks for “settled here” and “speech authority.” The human read does not.

5. Player: “I ask Mara who forged the lantern.”
   Response: “Sergeant Mara says, ‘I couldn’t tell you.’”
   Maker, unknown, narration determined, improvisation false. One interpretation call, 1,965 input tokens, no narration, no retry. Topics unchanged. This is the historical expensive gap, now cheap. The line is generic and it does not invent a smith.

6. Player: “What troubles you, standing out here?”
   Response: “Sergeant Mara says, ‘It’s this watch, mostly.’”
   Personal state, belief, improvisation permitted. One interpretation and one narration, no retry, 26,791 input tokens. Topics unchanged. This is a useful incidental answer. It does not mention a patrol, a lurking threat, or a new fact about the road.

7. Player: “Do you prefer the morning or the evening?”
   Response: “Sergeant Mara says, ‘I do not know enough to answer that.’”
   Opinion, improvisation permitted, and the spoken result is still ignorance. Two calls, no retry, 26,291 input tokens. Not a preference. Not an invented schedule.

8. Player: “I meant the road, not how you feel.”
   Response: “That action already resolved, so I cannot undo it. You can take a new action if you want.”
   Read as a correction of an executed action. It does not return to the road. One interpretation call, 1,861 input tokens. State unchanged, and the earlier turns were not rolled back.

9. Player: “What is the password for the side gate?”
   Response: “Sergeant Mara says, ‘I couldn’t answer that.’”
   Hidden, withheld, narration determined. One interpretation call, 1,892 input tokens. No password in the text. Topics unchanged.

10. Player: “Promise me a reward if I carry a message for you.”
    Response: “I cannot carry out Speak to Sergeant Mara and say: ‘Promise me a reward if I carry a message for you.’ with the available actions. No action has been attempted.”
    No reward was created. State unchanged. The wording is an action failure, not Mara refusing a bargain. One interpretation call, 1,891 input tokens.

11. Player: “I walk through the courtyard gate.”
    Response: “You arrive. The waystation street runs north from the courtyard gate. A notice board stands by the road.”
    Character action, scene transition, existing movement path. Zero provider calls, 290 ms. Scene, turn counter, and clocks changed. Topics did not.

12. Player: “Earlier you could not tell me who watches the north road. Is that still where you stand?”
    Response: “Which person, object, or pending action do you mean?”
    She is no longer in the arrived scene as an addressed speaker. The clarification does not invent her presence and does not continue the watch conversation. One interpretation call, 1,853 input tokens. State unchanged.

## Human-playability

A player can get the road’s name, a short honest gap about the lantern, a small personal remark, a password refusal that does not leak, and a real walk through the gate. The conversation does not feel continuous. Turn 3 drops the fact from turn 2. Turn 4 talks like a database. Turn 7 dodges a harmless preference after a large narration. Turn 8 answers a different question. Turn 10 talks like a command parser. Turn 12 asks who is meant instead of picking up the watch. Several gap lines are the same “I couldn’t tell you.”

Completing twelve turns without an exception is not success. The useful turns are 2, 5, 6, 9, and 11. The failing turns are important enough that the cycle is not accepted.
