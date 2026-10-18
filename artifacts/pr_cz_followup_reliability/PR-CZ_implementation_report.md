# PR-CZ Implementation Report

Mode: conversational follow-up reliability.

Live provider calls: 0.

Inherited PR-CY decision: E - validation false positives.

Decision: A - follow-up reliability repaired.

Summary:
- Target continuity repair: a validated discourse-focus interlocutor now becomes the ask contract interlocutor. This restores Guard Captain continuity for ordinary follow-up questions without inventing a new target.
- Validation repair: qualified, low-stakes NPC demeanor observations in incidental dialogue are accepted only when the governing decision is epistemic, has no state mutations, contains uncertainty language, and does not match structural consequential assertions.
- Reduced-context outcome: after target repair the Turn 2 follow-up has `active_interlocutor=guard_captain`; reduced-context projection remains not selected for the measured follow-up predicate, so no forced eligibility was introduced.

Regression headline:
- PR-CZ focused tests: 10 passed.
- PR-CX/PR-CW/PR-CK inherited guards: 78 passed.
- PR-CT/PR-CP/PR-CE/PR-CN/PR-BY/immutable/C19 authority subset: 97 passed.
- Shared turn pipeline: inherited baseline remains 45 passed / 24 failed.
- Authored-knowledge realization: 14 passed / 2 failed, inherited unrelated HTTP authored-knowledge failures.

