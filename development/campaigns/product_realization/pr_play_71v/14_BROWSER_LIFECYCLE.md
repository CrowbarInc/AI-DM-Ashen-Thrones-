# 14 — Browser lifecycle

The existing isolated host served `http://127.0.0.1:8072/` with `ASHEN_71V_DATA_NAME=browser_data` and network log `browser_lifecycle_network.jsonl`. The browser tab was the Cursor browser. Both campaigns started with New Campaign. Nothing was preseeded.

`browser_network.jsonl` is an earlier aborted run that reached a survey snapshot and then stopped. It is not this lifecycle.

## Campaign A — pass

New Campaign, Start, opening at Cinderwatch Gate District, notice board, travel, milestone, survey choice, "Record the limits of your survey", mud-print continuation, slot `Browser survey` at 11:30:23 PM, reload, explicit load, continuation "I continue along the track past the milestone.", slot `Browser survey continued` at 11:32:48 PM.

The survey sentence occurred once. The engine logged `[CLUE DUPLICATE IGNORED] milestone_mud_prints` on the repeated look. "The watch has now been warned" was absent. Screenshots: `artifacts/pr_play_71v/screenshots/pr71v-a-opening.png` and `pr71v-a-survey.png`.

## Campaign B — pass

New Campaign cleared the visible log and kept A's slots. Start, the same discoveries, report choice, return to the gate, "Give the watch your patrol report". The warned sentence was present and the survey-recorded sentence was absent. Slot `Browser report` at 11:34:47 PM. Reload kept the live B session. Explicit load restored that slot. The continuation "I ask the watch what they will do." attached. The GM reply was "Which person do you mean: Gate Guard or Gate Serjeant? Nothing has been attempted." No second warning was published. Screenshot: `pr71v-b-report.png`.

## Isolation

Loading `Browser survey continued` restored A and removed B-only lines, as recorded in report 10. The report slot on disk still holds B.

The browser network log has 75 responses, all HTTP 200. Mean middleware time 90.9 milliseconds, maximum 397.7 milliseconds. Those are server times. A separate paint timer was not installed, so browser-visible latency is not claimed as a measured number. The player saw each step complete before the next click.

Journal lead text still concatenates the turn marker with the repeated fact. That display issue was already present and was not part of this repair.
