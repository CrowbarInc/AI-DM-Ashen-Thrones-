# Next-step decision

Verdict for this milestone: **B/PARTIAL**.

The inherited failure `admission/compound-social` is repaired. “I go to the fortress trail and persuade the guard to help me.” no longer travels, spends nothing, and does not resolve persuasion. Purpose infinitives that already traveled still travel. T11, disjunctive destinations, and the route/destination pair on committed trips are intact. Regression suites added no failure identity.

The milestone is not integrity-clean. Three reason or participle sentences still select `leave_for_seek_the_fortress_trail`, fail the transition, and spend one turn, one tick, and one pressure increment without arriving and without a social receipt:

- “I go to the fortress trail looking for the guard.”
- “I go to the fortress trail so I can persuade the guard.”
- “I go to the fortress trail because I want to persuade the guard.”

Recommended next milestone: one narrow continuation that stops that failed-transition commit when the destination is an authorized route with a trailing reason or participle, and that does not execute the social verb. Do not rewrite committed route/arrival pairing to do it. Do not build a compound executor or a persuasion system.

Do not start that milestone automatically. Do not open live-play validation on this result. Live validation still needs its own authorization and spending ceiling, and it should wait until this failed-transition turn is closed. The original 20-turn live evaluation remains the baseline when that separate run is authorized.
