# RC-10 / RC-21 Policy Resolution Dossier

Campaign: RC-10 / RC-21 Policy Resolution  
Identifier: `rc10_rc21_policy_resolution_20260919`  
Date: 2026-09-19  
Type: policy analysis / human decision support  
Implementation: completed in `rc10_rc21_policy_implementation_20260919` — see `docs/rc10_rc21_policy_implementation.md`

# Human Decisions (settled)

```text
RC-10 = A
RC-21 = B + C
```

These were pending when this dossier was written. They are no longer pending. The analysis below is the decision record, not an open question. Do not treat the “USER DECISION REQUIRED” blocks as still open.

Supporting detail:

- `artifacts/policy_resolution/rc10_policy_analysis.md`
- `artifacts/policy_resolution/rc21_policy_analysis.md`
- `artifacts/policy_resolution/policy_decision_summary.md`
- `artifacts/policy_resolution/policy_evidence_manifest.json`
- `artifacts/policy_resolution/rc21_runtime_snapshot.json`

# Executive Summary

Ashen Thrones now has a technically clean red baseline except for two unanswered design questions.

RC-10 asks who may own a **retired opening-fallback label**. It is not a live gameplay bug. Current architecture substantially favors keeping the raw label inside the opening-fallback evidence helper.

RC-21 asks what official follow-up the game should record when an NPC points the player at a named person or landmark. Current runtime records “Check the notice board.” The remaining tests expect “Find Lirael (town crier).” Current architecture substantially favors authored-scene evidence plus a canonical lead registry, not narration inventing an NPC pending lead.

These are independent decisions. Recommendations below are advisory. The user still chooses.

# Current Baseline

Focused policy tests were re-run this campaign and remain the same four failures.

| Node | Cluster | Result |
|---|---|---|
| `tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only` | RC-10 | failed |
| `tests/test_social_destination_redirect_leads.py::test_lirael_near_notice_board_creates_actionable_npc_pending_and_registry` | RC-21 | failed |
| `tests/test_social_destination_redirect_leads.py::test_repeat_redirect_merges_pending_no_duplicate_authoritative_rows` | RC-21 | failed |
| `tests/test_social_destination_redirect_leads.py::test_destination_lead_distinct_from_existing_milestone_pending` | RC-21 | failed |

This campaign’s `PRE_POLICY_BASELINE` and `POST_POLICY_ANALYSIS_BASELINE` are identical: 6,450 collected, 6,347 passed, 4 failed, 99 skipped. The four failures are exactly the RC-10 and RC-21 nodes above. Evidence: `artifacts/policy_resolution/pre_policy_baseline.xml` and `post_policy_analysis_baseline.xml`. Analysis artifacts did not turn any policy test green.

No unexplained technical defect is known in the red baseline.

# Why These Tests Are Still Red

They are the mechanism that preserves unresolved policy.

```text
red test ≠ implementation is necessarily wrong
red test = repository contains competing or incomplete policy authority
```

RC-10’s fence and a later incidence-report fixture disagree about where a retired label may appear.

RC-21’s tests and current destination extraction disagree about whether a spoken Lirael redirect becomes an NPC follow-up.

# RC-10

## Plain-English Explanation

The game used to let the last-mile opening gate compose first-turn safety text itself. That old path was stamped `compatibility_local_opening_deterministic`.

That path is retired. Live openings use prepared upstream fallback or fail closed. The remaining question is: may tests still write that historical stamp as a raw string anywhere, or only in the opening-fallback evidence helper?

Player-visible opening text does not depend on this choice.

## Current Runtime Behavior

**CONFIRMED BY CURRENT CODE.**

Canonical live authorship is `upstream_prepared_opening_fallback`. Fail-closed openings leave authorship empty. If a legacy token is injected, `opening_fallback_owner_bucket_from_fields` maps it to `unknown-ambiguous`.

Production comments say `game/` must not emit the token.

## Current Test Expectation

**CONFIRMED BY CURRENT TEST.**

The RC-10 test scans `tests/**/*.py` except `tests/helpers/opening_fallback_evidence.py`. It fails because `tests/test_fallback_incidence_report.py:150` still contains the raw string.

## Architectural Context

**CONFIRMED BY CURRENT ARCHITECTURE DOC.**

CR-01 lists compatibility-local opening authorship as transitional residue: keep it readable for negative replay/classifier evidence; do not make it runtime provenance.

## Historical Context

**CONFIRMED BY HISTORICAL ARTIFACT.**

CK (2026-06-26) treated the evidence-only fence as complete. CT (2026-06-28) added the incidence-report raw literal. CU then observed RC-10 as a pre-existing failure.

**INFERRED:** CT treated the token as historical event vocabulary and did not migrate through the CK helper.

## Policy Options

**A — Evidence-only fence.**  
Only the opening-fallback evidence helper may contain the raw test literal. Other tests use the helper/accessor.

**B — Diagnostic allowlist.**  
Selected diagnostic tests may name the raw historical token.

**C — Schema-only contraction.**  
Even the helper would read the schema constant only. Stricter than the current red test; not the live decision it preserves.

## Consequences

A is a tiny test-only change and strengthens one-owner residue management.

B is also tiny, but reopens scatter.

Neither changes player-facing opening behavior.

## Evidence

See `artifacts/policy_resolution/rc10_policy_analysis.md` §9.

Current runtime, sibling tests, CR-01, and CK **SUPPORTS_OPTION_A**.  
The incidence-report literal **SUPPORTS_OPTION_B**.  
Gameplay impact is **NEUTRAL**.

Existing Ashen Thrones architecture substantially favors Policy A. That is not the same as “the policy has already been decided.”

## Repository-Supported Recommendation

```text
Repository-supported recommendation: POLICY A
Confidence: HIGH
Reason: The retired label already has a declared evidence home. The remaining offender is one later diagnostic fixture.
```

## User Decision

```text
RC-10

Plain-English question:
Should the retired opening-fallback label be allowed as a raw string only in the opening-fallback evidence helper?

Option A:
Yes. Route other tests through the helper.

Option B:
No. Selected diagnostic tests may name the raw token.

Existing architecture leans:
A

Important consequence:
No player-facing change. A prevents a retired path from looking live.

Cursor recommendation:
A

USER DECISION MADE:
A
```

# RC-21

## Plain-English Explanation

When the tavern runner says the player will find Lirael near the notice board, where does the game officially record that the party now has something to follow?

- **NPC pending-lead:** a scene sticky note saying “talk to the town crier.”
- **Discoverable-clue / landmark evidence:** only authored scene content can become that follow-up. Here that is the notice board.
- **Lead registry:** the session case file already declared as the source of truth; pending is a compatibility mirror.

## Current Runtime Behavior

**CONFIRMED BY CURRENT CODE.**

`load_scene("frontier_gate")` loads current canon. That file does not author Lirael and does not expose `emergent_town_crier`.

Extraction therefore cannot take the named-crier path. It writes `scene_anchor:notice_board`:

- clue `lead_frontier_gate_notice_board`
- registry location/rumor row
- pending rumor row “Check the notice board”
- no `leads_to_npc=emergent_town_crier`

Lirael is heard and then dropped.

## Current Test Expectation

**CONFIRMED BY CURRENT TEST.**

The three red tests require exactly one pending row targeting `emergent_town_crier`, with registry linkage, merge-on-repeat, and distinction from an old-milestone pending row.

They fail `assert len(npc_pending) == 1` because that row is absent.

## Architectural Context

**CONFIRMED BY CURRENT CODE** and **CONFIRMED BY CURRENT ARCHITECTURE DOC.**

`_apply_extracted_social_leads` already says the registry row is the source of truth and `pending_leads` is a compatibility mirror.

Campaign 1–6 doctrine: runtime truth before narration; GPT does not own state; derived stores must not become second owners.

The AI GM contract allows a named entity in **narration** when an NPC says it. That is not the same as creating an official NPC lead.

## Historical Context

**CONFIRMED BY HISTORICAL ARTIFACT.**

The tests were added 2026-04-03, when frontier_gate still authored Lirael. Scene canon was cleaned 2026-04-25 and lost that authorship. Extraction comments and `game/defaults.py` still remember the old world.

**INFERRED:** RC-21 is leftover pre-cleanup expectation plus an unfinished lead-ownership decision, not a random regression.

## Policy Options

**A — Spoken redirect creates an NPC follow-up.**  
“Find Lirael” becomes official, even if current canon does not author her.

**B — Spoken redirect follows authored scene evidence.**  
Without authored Lirael/crier, the official follow-up is the notice board.

**C — Registry is canonical; pending and clues are projections.**  
Already declared. Does not by itself decide the Lirael gameplay question. Should accompany A or B.

The binary is false. C is not a new architecture.

## Simulationist Consequences

| Question | Policy A | Policy B / current | Policy C |
|---|---|---|---|
| Who knows the destination? | Engine treats the claim as an actionable person | Engine treats the authored board as the follow-up | Official record lives in the registry |
| Does Lirael exist independently? | Effectively yes, as a pursueable target | Not in current canon | Only if content or a later realization writes her |
| Has the player learned her? | Yes, as an official lead | Only as spoken text | Player-known vs official lead can be separated |
| If the NPC lies? | The lie still creates a person-target | The board still exists; Lirael is not instantiated | Claims could later be stored as provenance; not modeled today |
| Does mention make her discoverable? | Yes | No | Only after an authorized write |
| If the runner dies? | Person-target can remain | Board remains | Registry can outlive the speaker |
| Competing redirects? | Another pending/person row or merge | Another authored-evidence realization | Monotonic registry merge; competing claims not modeled |
| Why does this matter later? | Because pending says so | Because the scene authored the landmark | Because the case file says so, with evidence ids |
| Replay? | Deterministic if extraction changes | Deterministic now | Deterministic now |
| Future AI distinctions | Weak; sticky note collapses kinds | Stronger for world vs speech | Strongest available current model |

## Consequences

A improves “follow Lirael” and risks narration inventing people unless Lirael is restored as content.

B preserves engine-first simulation and disappoints person-pursuit unless content is restored.

C reduces duplicate ownership and should be kept either way.

Implementation after decision:

- A without content restore: moderate/architectural product change.
- A with restored Lirael authorship: moderate content + extraction bind.
- B: localized test/doc alignment, plus leftover `defaults.py` / comment cleanup later.
- C: mostly already present.

## Evidence

See `artifacts/policy_resolution/rc21_policy_analysis.md` §13.

Current runtime, current canon, extractor gates, and Campaign 1–6 doctrine **SUPPORTS_OPTION_B** and **SUPPORTS_OTHER (C)**.  
The three red tests and qualified pursuit **SUPPORTS_OPTION_A**.  
Leftover defaults Lirael text is **AMBIGUOUS**.

Existing Ashen Thrones architecture substantially favors Policy B inside store model C. The user still must decide the gameplay question.

## Repository-Supported Recommendation

```text
Repository-supported recommendation: POLICY B, keeping POLICY C
Confidence: MEDIUM-HIGH
Reason: Current scene canon, extractor gates, registry comments, and architecture doctrine refuse to let narration invent an NPC lead. If Lirael pursuit is desired, restore her as authored content rather than making pending_leads authoritative again.
```

## User Decision

```text
RC-21

Plain-English question:
When an NPC points the player at a named person or landmark, what official follow-up should the game record?

Option A:
Record an NPC follow-up (Find Lirael / town crier).

Option B:
Record only authored scene evidence (here: Check the notice board).

Option C:
Keep the lead registry official; pending and clues are projections. Accompanies A or B.

Existing architecture leans:
B + C

Important consequence:
A makes person-pursuit work. B prevents spoken text from inventing people.

Cursor recommendation:
B, keep C

USER DECISION MADE:
B + C
```

# Relationship Between RC-10 and RC-21

Both ask whether a compatibility or narration-adjacent surface may become a second owner of meaning.

They are otherwise independent:

- RC-10 is test/diagnostic ownership of a retired opening label.
- RC-21 is live follow-up ownership after social redirects.

Choosing A on one does not force a choice on the other.

# What Remains Technically Unresolved

Nothing in the red baseline is a known unexplained product defect.

Leftover drift that a later implementation campaign should notice, but must not “fix” until policy is chosen:

- stale `game/clues.py` comment claiming frontier_gate still authors Lirael
- `game/defaults.py` still contains old Lirael discoverable rumor
- `compat_pending_lead_needed` ignores NPC-only targets
- intent parsing still reads `pending_leads` as the pursuit surface

Those are not this campaign’s repairs.

# What Requires Human Policy Judgment

1. RC-10: exclusive evidence helper versus diagnostic raw-token allowlist.
2. RC-21: person-follow-up versus authored-evidence follow-up, and whether to ratify the registry as the official store.

# Implementation Implications After Decision

Do not implement in this campaign.

After the user answers:

1. Record the decisions in governance/policy artifacts.
2. Align only the side the user chose: tests, production, or content.
3. Keep the other policy red until that decision exists.
4. Re-run the suite and expect the chosen cluster to go green only after that later campaign.

Likely size:

- RC-10 A or B: tiny / localized, tests only.
- RC-21 B: localized expectation maintenance.
- RC-21 A: moderate product and/or content work.
- RC-21 C ratification: documentation plus later lead-cleanup, already deferred.

# Recommended Next Campaign

The user chose RC-10 = A and RC-21 = B + C. Implementation is recorded in `docs/rc10_rc21_policy_implementation.md`.

Review the clean post-policy baseline before Calibration Round #2, State ↔ Narration Consistency, or new Product Realization work.
