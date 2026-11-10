# EXECUTIVE SUMMARY

B — PARTIAL / BOTH NORMAL PLAYER LIFECYCLES DEMONSTRATED; FINAL HOLDOUT COVERAGE INCOMPLETE

Normal UI New Campaign and Start Campaign work; two separate campaigns reached Old Milestone, made exclusive survey/report choices, completed distinct follow-ups, saved through Save Slots, reloaded, resumed, and continued. No runtime seeding, injected discoveries, or prestarted sessions were used for these lifecycle demonstrations. Bootstrap campaign/character/world/scenes were copied into ASHEN_DATA_DIR; New Campaign itself created runtime identities. Character Galinor is the existing authored bootstrap; no setup form is provided.

Three lifecycle defects were exposed: new identities did not inherit session-bound experimental access; milestone disclosure could be replaced with refusal when optional narration was off; loading a save refreshed state but retained the other campaign's transcript. Targeted repairs address these. A cached browser retained the old frontend until the application context was reopened; both corrected save-slot transitions were then observed.

Frozen developer holdout: 46/50; four failures retained. Two evaluators wrongly required an error instead of legitimate deterministic opening recovery. Two genuine WinError 5 rename failures affected New Campaign/chat. After the frozen run finished, bounded rename retry, failed-reset rollback, and a dependency-boundary cleanup were applied. These final repairs have focused validation but have no new frozen holdout or live-browser rerun. This prevents an A verdict. No official ATGB, external independence, or full-suite claim. No commit/push.

Provider: 15 requests / 189036 tokens, including four preflights, eight primary turns and three interpretation requests. One additional admission was refused before sending for “provider usage accounting unavailable”; its existing deterministic result remained player-visible. Zero SDK/host retries. Saved A opening used accepted AI; B used authorized deterministic opening recovery after semantic rejection. Fallback counts for earlier discarded openings were not recovered. One baseline disclosure omission; zero observed after repair. Zero observed unsafe publications or hidden HTTP exposures.

Exactly one primary next step: PR-PLAY-71 verification closure: use a fresh, correctly specified holdout against the final persistence repair, including transient and permanent Windows rename failures. Preserve this frozen run without rerunning or tuning it.
