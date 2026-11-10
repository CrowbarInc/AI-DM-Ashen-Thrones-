# PR-PLAY-35 final verdict

**C — FAIL.**

The live provider returned a completed frontier-gate opening. The engine rejected it for `unauthorized_resolution_decision_fact` and did not start the campaign. All five player turns are BLOCKED. Score 0/50. Provider requests 1. Tokens 26714 input / 1667 output / 28381 total. Provider latency 12.105 seconds. Experiment wall time 14.969 seconds.

Critical defect: campaign initialization cannot survive this semantic rejection, so ordinary play never begins. Mechanical state stayed consistent with the rejection. Conversational continuity was not tested. Gameplay implementation files were not changed.

Next investigation: identify the unrealized proposition inside the captured opening and determine why that single validation failure aborts start instead of preserving an authorized opening. Do not treat another five-turn run as useful until a campaign can start. Do not repair it inside this experiment. PR-PLAY-36 was not started.
