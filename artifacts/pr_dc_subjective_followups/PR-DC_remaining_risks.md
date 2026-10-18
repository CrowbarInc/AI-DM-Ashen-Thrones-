# PR-DC Remaining Risks

LIVE CALLS: 0

## Closed frames miss paraphrases

"Is the watch rough in this rain?" and "Do you get worn down out here?" do not match the experiential pattern. They stay `genuine_uncertainty`. Widening to open adjectives or to model intent classification was stopped.

## "Leave" never reaches the classifier

"Do long shifts leave you tired?" is claim-only if `resolve_social_action` is called directly. The live entry parser classifies "leave" as travel, so the reply plan is absent. The same parse still catches "Can I persuade the captain to leave?". Changing that parse would be a resolver change and was not done.

## Third-person experience stays uncertain

"Does the baker find early mornings tiring?" and "Does the innkeeper enjoy busy evenings?" stay `genuine_uncertainty`. The routed baker sentence still drops `social.npc_id` and clears the active target afterward. That behavior was in the baseline and was not changed.

## Preference matching is still broad

Lines that contain `prefer` still use the older pattern, which does not consult the new experiential blocker. "Why do you prefer somewhere dry?" is the intended case. A sentence that says "prefer" and also asks for harm would still be claim-only if it avoids the restricted and consequential patterns. That path was already present.

## Projection now applies to these follow-ups

Turns 2 and 3 omit opening, transition, and progression sections through the existing PR-CW projector. Compaction drops `requires_check` from the model-facing mechanical resolution after the eligibility check has already required it to be false. Validators still receive the in-process resolution. This is existing projection behavior, newly reached by these two sentences.

A post-compaction predicate scan reports `requires_check` null. That scan is not the eligibility decision. Eligibility already passed inside `build_messages`.

## Inherited failures

Authored patrol realization still fails 3 tests. The shared turn pipeline still fails 24 tests. Neither set was treated as repaired.

## No live realization check

No provider call was made. The classification, projection, and hard-validator results are deterministic. They do not show how a model phrases the claim-only answer.
