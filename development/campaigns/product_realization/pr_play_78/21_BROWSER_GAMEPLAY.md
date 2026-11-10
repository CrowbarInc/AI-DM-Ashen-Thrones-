# Browser gameplay

Host: `artifacts/pr_play_78/browser_host.py` on `http://127.0.0.1:8092/`. Provider calls disabled. Expression generation disabled. Bounded speech, dynamic NPCs, physical adjudication, world improvisation, initiative, and branching were on. The UI was the existing player page. Dialogue in this section is deterministic. It is not live AI.

Trace: `artifacts/pr_play_78/browser_campaigns.json`. Screenshots: `artifacts/pr_play_78/browser_shots/`.

Campaign A — completed.

New Campaign, Start, look around, examine the notice board (clue published), an unsupported step-closer, approach and greet, ask who passed, ask if he seems nervous, snapshot `2026-11-07T22-45-18_8757597a`, reload, load that snapshot, thank him and step back, look for a struggle. After resume the scene was Cinderwatch Gate, 1 clue, 9 then more log entries. Send was disabled while a request was in flight.

Campaign B — completed.

New Campaign, Start (760 ms to the opening), examine the notice, follow the rumor (arrive Old Milestone), look around, climb the milestone (no check, position unchanged), examine the milestone (uncertain prints). The sentence "I return to report the uncertain trail to the watch." did not take the branch. The player stayed at `old_milestone`. The conditional sentence published the Cinderwatch opening while the heading and save scene stayed Old Milestone. Approaching the guard there failed and the question was not asked. "Am I standing?" answered without a move. The suggested-action button "Return to report the uncertain trail to the watch" did take the branch. Chat then returned to the gate. "Approach the guard and ask whether he needs help." moved beside him and he said he did not know. Snapshot `2026-11-07T22-47-48_1ecf02ec`. Reload restored frontier_gate, 2 clues, and the transcript. Loading that snapshot and pressing "Give the watch your patrol report" published the warning consequence. The survey button was gone.

Both snapshots stayed listed in one store. Loading campaign-b restored campaign B. That is a shared snapshot list, not a mid-turn state leak.

Timed player-visible completions (20, including start and two buttons; the first two Campaign A chats were not timed): mean 598.2 ms, median 542.0 ms, p95 989 ms, maximum 1077 ms. Paint time was not instrumented. These numbers are browser-visible completion of `sendChat` or the button handler, not server-only time.
