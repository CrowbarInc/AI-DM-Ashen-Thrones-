# Browser Gameplay

Host: `artifacts/pr_play_76/runtime.py` on `http://127.0.0.1:8078/`, isolated storage `artifacts/pr_play_76/browser_data`. Player mode. Chat was entered in `#chatInput` and sent with the Send button. Branch choices used the on-screen affordance buttons. Snapshots used Create Snapshot and Load. Two controls that sat below the viewport were activated through the page's own button click after the browser click tool could not scroll them into view.

## Campaign A

New Campaign, Start, typed notice-board examination, typed patrol follow, typed milestone examination, Survey the uncertain trail yourself, Record the limits of your survey, typed loose-stone question, typed push, typed follow-up. The visible answer was "The ordinary loose stone is aside from the stonework." Snapshot `survey-stone` (`2026-11-07T17-12-22_cf8cc1f4`), reload, Load, typed "Where is the loose stone?" The same aside position was published. Screenshot: `browser_A_survey_push.png`.

Result: PASS.

## Campaign B

New Campaign, Start, typed investigation, Return to report the uncertain trail to the watch, typed return to the gate, Give the watch your patrol report, typed approach, typed climb, typed "Am I beside the notice board?" The climb was refused and the beside position remained. Snapshot `report-approach` (`2026-11-07T17-14-59_3b3dd5fd`), reload, Load of that snapshot, typed step back. The visible answer was "You step back from the Notice board." Screenshot: `browser_B_report_climb.png`.

Result: PASS.

Browser success is not inferred from the HTTP runs. The two hosts were separate.
