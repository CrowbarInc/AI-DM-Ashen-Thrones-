# Browser acceptance

One sequence on the frozen host, pid 23332, `http://127.0.0.1:8111/`, player mode. The campaign was the isolated initialized copy. No opening was generated. No suggested-action button was clicked. Chat submissions used `#chatInput` and Send.

1. Opened the campaign. Scene title became Cinderwatch Gate District. Position was beside the notice board. The patrol clue was already discovered.
2. Typed `I step back from the notice board.` One expression request. Accepted live narration published. Position became back.
3. Typed `Gate Guard, what does the notice board say about the patrol?` The guard’s speech was visible. The publication record classifies it as a grounded fallback.
4. Typed `I examine the notice board.` The previously disclosed patrol sentence was shown, with the no-new-information line.
5. Typed `I examine the notice board again.` The same disclosed sentence was shown. No expression request.
6. Created snapshot `79DF final-source`, id `2026-11-08T13-23-16_b6d3684f`. No provider call.
7. Reloaded `http://127.0.0.1:8111/`. The session restored the scene, the journal, and the chat, including both examination replies.
8. Loaded that snapshot from Save Slots. The UI said `Snapshot restored.` Position remained back from the notice board. Turn remained 18. Both clues remained. No provider call.

Screenshots: `physical_step_back.png`, `npc_dialogue.png`, `79df_snapshot_restored.png`.

The sequence used one source fingerprint. Provider use stopped at five completed requests.
