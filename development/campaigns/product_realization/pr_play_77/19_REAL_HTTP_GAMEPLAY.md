# Real HTTP Gameplay

Harness: `tests/test_pr_play_77_http.py` using `TestClient` against the normal campaign routes. No developer-only seed API.

Campaign A, survey branch:

- Established a small loose stone by asking whether one could be shifted. It had not been moved.
- "I push the loose stone aside and look where it was." Both consequences published. Elapsed 306.8 ms.
- "I push the loose stone farther, climb the milestone, and look down the road." Farther, no climbing check, look not attempted, not elevated. Elapsed 792.0 ms.
- Snapshot, new campaign, load. "Where is the loose stone?" still farther. "continue" did not resume the plan.

Campaign B, report branch:

- Conditional step-back skipped. Position unchanged. Elapsed 42.9 ms.
- "I stand up and approach the notice board." Beside the board. Elapsed 839.7 ms.
- "Is the notice board here, and what is on the hidden side?" did not approach again, did not add clues, and did not change position or flags. Elapsed 43.6 ms.
- Snapshot, load. Beside persisted. The same conditional then stepped back. Elapsed 908.1 ms.

All ten measured chat turns: mean 364.25 ms, median 175.2 ms, maximum 908.1 ms. HTTP 200 was not the acceptance check. State and publication assertions passed.
