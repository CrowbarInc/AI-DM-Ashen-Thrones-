# Intermediate validation findings

These records explain fixture development and expected protocol changes. Final
results are in focused.xml and harness_final.xml.

* focused_initial.txt: six new-fixture failures. A parsed engine-enriched record
  was incorrectly replayed as raw provider JSON, default fixture guard IDs differed
  from the captured world, and positive target labels were not established.
* focused_second/third.txt: three remaining fixture assertions. The guard needed
  explicit authored eligibility and an unambiguous roster. A question can publish
  existing authorized deterministic host/NPC speech without invoking narration.
  Successful ordinary actions legitimately tick the world. The final assertions
  require actual social resolution/publication and compare world state to exactly
  one authorized deterministic tick; they do not demand immutable world time.
* harness_initial.txt/xml: 12 failures / 34 passes. Two were new controller
  integration failures and eight old real-worker tests could not pass their
  initial Debug HTTP snapshot after PR-PLAY-21. The harness now reads Player HTTP
  and retains authoritative state through its existing isolated-file capture.
  Two evaluator expectations were obsolete: text alone is not execution evidence,
  and an absent public reply is a decisive semantic failure.
* First combined harness run: 86 passed / 5 failed. All 24 existing automated
  playtest controls passed. Four five-turn expectations stopped at T1 because
  the initial classifier mistook an intermediate blocked adapter result for a
  terminal refusal even after a valid authorized host description. This was a
  real classifier bug and was fixed, with a focused regression. One rules test
  exposed a positive fixture that supplied a resolver merely to establish reply
  completion; the fixture now supplies accepted-speaker completion evidence and
  preserves unknown rules status.
* Second combined gameplay run: 64 passed / 3 failed. The remaining T3 injection,
  request-count and token-count expectations assumed continuation past a real T2
  ungrounded_provider_target refusal. Actual T2 host text was “I cannot tell who
  that is addressed to. Nothing has been attempted.” The new semantic stop is
  required to terminate there. The assertions now require two attempted turns,
  three total synthetic requests, 60 input / 30 output / 90 total tokens, and
  skipping T3 onward. The unrelated T2 grounding ambiguity was not repaired.
* Final combined run: 70 passed. Final focused run: 37 passed. No assertions about
  the 17 historical functional failures or eight expanded-scope failures changed.

The initial two combined-run text/XML files were replaced by their final reruns;
their precise failure identities/counts and causes are retained here. Other
intermediate logs are preserved verbatim. No live calls occurred in any run.
