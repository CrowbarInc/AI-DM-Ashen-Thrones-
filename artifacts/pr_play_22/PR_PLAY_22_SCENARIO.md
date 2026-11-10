# PR-PLAY-22 scenario

## Actual published opening

Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate. Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in. A notice board lists new taxes, curfews, and a posted warning about a missing patrol. A tavern runner shouts offers of hot stew and paid rumor. A well-appointed townhouse overlooking the square flies noble colors—a quiet contrast to the mud and clamor. One figure in threadbare clothes stands uncannily still, gaze flicking to packs and faces more than the gate queue.

Objective: approach an opening NPC, ask about offerings, follow up, investigate a detail, make a supported choice, and follow through.

Planned deterministic rules: select the first present published name in tavern runner / gate serjeant / guard. T1 asks about offerings for the runner, otherwise the situation. T2 quotes the first preceding sentence longer than 25 characters and asks for elaboration; T3 asks how the NPC knows that sentence. T4 examines the notice board only if published; T5 examines the missing-patrol posting only if T4 mentions a patrol. No planning model or judge calls.

Adaptation: the published opening contains the tavern runner. T1 selected it. After T1 the quote rules incorrectly treated a host refusal as NPC material; T2/T3 consequently asked about system inability, not stew or rumors. T4 selected the notice board from the opening despite the conversation already failing. T5 was not submitted because T4 did not mention a patrol.

PROTOCOL DEVIATION: T1 already made the intended NPC sequence unusable. The controller checked HTTP/provider errors but failed to detect this host-generated semantic dead end. It submitted T2–T4 before stopping, and its raw ordinary_completed=4 counter counts HTTP success, not gameplay success. Those raw records are preserved. Review counts: 4 attempted, 4 HTTP responses, 0 successful NPC/gameplay interactions. T2–T4 are post-failure diagnostic observations, not a valid continuation or recovery. No restart, provider retry, replacement initialization, or extra live run occurred.

## Actually executed actions

1. I approach the tavern runner and ask what they're offering.
2. I ask the tavern runner to explain more about this: "I cannot carry out Approach the tavern runner, then Ask the tavern runner what they are offering with the available actions and targets." What can they tell me?
3. I ask the tavern runner: "I cannot carry out Approach the tavern runner, then Ask the tavern runner what they are offering with the available actions and targets." How do they know that?
4. I decide to read the notice board and walk over to examine the posted notices.
