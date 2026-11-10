# 10 — Transcript restoration

Browser campaign A (`b71d9ab269b14913826d9790`) and campaign B (`9d6a1a036881996f1883786c`) were created from New Campaign on the same page. No session was seeded.

After B's report follow-up and the live continuation "I ask the watch what they will do.", the visible log contained "The watch has now been warned" and did not contain "Your survey is now recorded" or A's continuation "I continue along the track past the milestone."

Loading slot `Browser survey continued` (`2026-11-06T04-32-48_e69acb53`) then showed:

- Scene: Old Milestone.
- "Your survey is now recorded": present.
- "I continue along the track past the milestone.": present.
- "The watch has now been warned": absent.
- "I ask the watch what they will do.": absent.
- Status line: "Snapshot restored."

The live session file after that load is campaign A at `old_milestone`. `world.json` has `patrol_survey` and `patrol_survey_recorded` and does not contain `patrol_report` or `patrol_guards_warned`. The report snapshot still contains campaign B at `frontier_gate` with `patrol_report` and `patrol_guards_warned`.

The B continuation was attached to the live session after the report slot had already been written. It was not copied into that earlier slot. Loading A therefore dropped the unsaved line from the live session, which is what the slot model does. The line did not appear inside A's restored transcript.

A page reload while B was the live session kept B's scene and the warned sentence before the explicit slot load.
