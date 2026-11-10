# Browser Gameplay

Host: `artifacts/pr_play_77/runtime.py` on `http://127.0.0.1:8091/`. Provider calls disabled on this host. Network log: `artifacts/pr_play_77/browser_network.jsonl`.

Campaign A, typed in the chat composer:

- New Campaign, Start Campaign, examine the notice board, follow the rumor, examine the milestone.
- Survey the uncertain trail yourself. Record the limits of your survey.
- "Is there a small loose stone I could shift aside?"
- "I push the loose stone aside and look where it was."
- "I push the loose stone farther, climb the milestone, and look down the road."
- Create Snapshot labeled partial. Reload. Load. "Where is the loose stone?" The stone was farther aside. "continue" did not resume the plan.

Screenshot: `artifacts/pr_play_77/screenshots/browser_a_partial.png` shows the partial-success narration at Old Milestone.

Campaign B:

- New Campaign, Start, the same investigation, Return to report the uncertain trail, return to the gate, Give the watch your patrol report.
- Conditional step-back skipped.
- "I stand up and approach the notice board." Beside the board.
- "Is the notice board here, and what is on the hidden side?" Nothing on the other side was established, and nothing was opened or moved.
- Those two requests overlapped in the page script. The read-only response completed before the stand response. The read-only text still reported no mutation. The stand then committed beside.
- Snapshot `beside-after` was taken after that stand. Reload and Load restored beside. "Am I beside the notice board?" yes. The conditional then stepped back.

Screenshot: `artifacts/pr_play_77/screenshots/browser_b_resume.png`.

Browser chat requests: 19. Server-side mean 551.42 ms, median 424.55 ms, maximum 1683.87 ms. Authored action clicks: 4, mean 252.63 ms, maximum 305.26 ms. Paint time was not instrumented. Browser success is not inferred from the HTTP suite.
