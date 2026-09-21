# RC-10 Policy Analysis

Campaign: RC-10 / RC-21 Policy Resolution  
Identifier: `rc10_rc21_policy_resolution_20260919`  
Status: analysis only; no policy chosen; no implementation

## 1. Plain English

Ashen Thrones used to have a fallback path in which the **final-emission gate itself** composed the first-turn opening text when the usual prepared opening text was missing. That old path was labeled with an internal stamp:

```text
compatibility_local_opening_deterministic
```

In ordinary language:

- A **raw token** is this exact historical label, written as a string in source or tests.
- **Local** means the gate composed the opening locally, instead of selecting opening text prepared upstream.
- The **boundary** is the rule for who is allowed to mention that retired label.
- **Opening fallback** is the first-turn safety text used when the normal opening path cannot emit.
- **Compatibility** means the label still exists so old replay/classifier fixtures can be recognized, not so live play can use that path again.

This is **not** a player-visible gameplay rule today. Production opening paths no longer write the token. The remaining question is ownership of a retired label.

## 2. What The Phrase Actually Means

| Phrase | Ordinary meaning | Repository meaning |
|---|---|---|
| raw token | a literal historical string | `compatibility_local_opening_deterministic` |
| local | composed at the last-mile gate | retired gate-local opening composer |
| boundary | who may own/mention the label | AST lock over `tests/**/*.py` |
| opening fallback | first-turn safety narration | `game.final_emission_opening_fallback` plus upstream-prepared authorship |
| compatibility | keep old evidence readable | CR-01 / CK read-side mapping to `unknown-ambiguous` |

Evidence class: **CONFIRMED BY CURRENT CODE** and **CONFIRMED BY CURRENT TEST**.

## 3. Current Runtime Behavior

```text
player/runtime opening request
        ↓
upstream opening packaging
        ↓
canonical authorship: upstream_prepared_opening_fallback
        ↓
final-emission selection / fail-closed
        ↓
read-side owner-bucket mapping
        ↓
if a legacy token is injected: unknown-ambiguous
        ↓
replay / classifier / incidence diagnostics
```

Actual symbols:

| Role | Symbol |
|---|---|
| Owner of retired vocabulary | `game.final_emission_ownership_schema.OPENING_FALLBACK_LEGACY_COMPATIBILITY_LOCAL_AUTHORSHIP_SOURCES` |
| Canonical live authorship | `OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED` / `upstream_prepared_opening_fallback` |
| Compatibility reader | `game.final_emission_owner_bucket_views.opening_fallback_owner_bucket_from_fields` |
| Fallback layer | `game.final_emission_opening_fallback` |
| Evidence-only raw-token home | `tests.helpers.opening_fallback_evidence` |
| Accessor | `legacy_compatibility_local_opening_authorship_source()` |
| Extra current consumer | `tests/test_fallback_incidence_report.py:150` |

Production comments and CK closeout say production `game/` must not emit the token. The failing test does **not** claim production emits it. It claims another **test file** still contains the raw string.

Evidence class: **CONFIRMED BY CURRENT CODE**.

## 4. Current Test Expectation

`tests/test_final_emission_meta.py::test_compat_local_raw_token_boundary_is_opening_fallback_evidence_only` scans every file under `tests/` except `tests/helpers/opening_fallback_evidence.py`.

It fails if any other test file:

1. contains the raw string `compatibility_local_opening_deterministic`, or
2. imports `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL`.

Focused reproduction on this campaign:

```text
AssertionError: ["tests\\test_fallback_incidence_report.py:150:'compatibility_local_opening_deterministic'"]
```

Sibling passing tests already require classifier and dashboard fixtures to use the helper accessors. The incidence-report test, added later, names the raw token as event input.

Evidence class: **CONFIRMED BY CURRENT TEST**.

## 5. Architectural Context

`docs/compatibility_residue_register.md` CR-01 classifies compatibility-local opening authorship as **transitional** residue:

- canonical opening prefers upstream-prepared or fail-closed
- legacy rows remain for negative projection and classifier coverage
- the token must not become runtime provenance
- retirement requires a consumer inventory

CK Fallback Authorship Contraction (2026-06-26) treated the evidence-only fence as completed work. CT Runtime Fallback Incidence Baseline (2026-06-28) added the raw literal that now keeps RC-10 red.

Evidence class: **CONFIRMED BY CURRENT ARCHITECTURE DOC** and **CONFIRMED BY HISTORICAL ARTIFACT**.

## 6. Historical Intent

| Fact | Class |
|---|---|
| The token originally stamped gate-local opening composition | **CONFIRMED BY HISTORICAL ARTIFACT** (`audits/opening_fallback_surface_inventory_2026-05-11.md`) |
| Production assignment was later retired | **CONFIRMED BY HISTORICAL ARTIFACT** (Cycle AB/AP/CK) |
| CK Block 4 quarantined raw literals to the evidence helper | **CONFIRMED BY HISTORICAL ARTIFACT** (`CK_fallback_authorship_contraction_closeout.md`) |
| Two days later, CT introduced one raw literal in incidence reporting | **CONFIRMED BY HISTORICAL ARTIFACT** (`845e6db`, 2026-06-28) |
| RC-10 remains classified `POLICY_DECISION_REQUIRED` | **CONFIRMED BY CURRENT ARCHITECTURE DOC** / triage artifacts |

Inference, not fact: CT treated the historical token as incidence-report vocabulary and did not migrate through the CK helper. That is why the fence is still red.

RC-10 is therefore:

- an intentional architectural boundary that was declared complete
- then reopened by a later diagnostic consumer
- not a live gameplay defect
- not accidental ambiguity in current opening selection

## 7. Competing Policies

### POLICY A — Evidence-only raw-token fence

Meaning: Only `tests/helpers/opening_fallback_evidence.py` may contain the raw historical string in tests. Other tests must call the helper/accessor. Production schema may define the token for read-side recognition. Live opening paths must not emit it.

Current support:

- the failing test itself
- sibling classifier/dashboard locks
- helper docstring: “sole raw-token boundary”
- CK closeout
- CR-01 transitional posture
- production comments forbidding live writes

Contradicting evidence:

- `tests/test_fallback_incidence_report.py` currently names the raw token
- that file is a real diagnostic consumer of historical fallback events

Runtime consequence: none for players. Opening selection stays upstream-prepared / fail-closed.

Architecture consequence: one owner for the retired label; duplicate vocabulary shrinks.

Compatibility consequence: historical events remain injectable through helpers; read-side mapping stays.

Player-facing consequence: none.

Migration cost: **tiny / localized**. Route the incidence-report fixture through `legacy_compatibility_local_opening_authorship_source()` or the legacy evidence builder.

Long-term maintenance: prevents accidental reintroduction of a retired authorship path as if it were live.

### POLICY B — Diagnostic surfaces may name the raw token

Meaning: Opening-fallback evidence remains the preferred inject home, but later diagnostic tests may include the raw historical string when they classify old events.

Current support:

- the incidence-report test as written
- CR-01 still lists dashboards/classifiers as consumers
- the token is historical event vocabulary, not live authorship

Contradicting evidence:

- CK treated scatter as the problem to close
- the AST lock exists specifically to prevent new raw homes
- sibling tests already migrated

Runtime consequence: none for players.

Architecture consequence: the fence becomes an allowlist. Each new diagnostic file can reopen RC-10.

Compatibility consequence: slightly easier historical-event fixtures; weaker ownership.

Player-facing consequence: none.

Migration cost: **tiny / localized**. Widen the RC-10 allowlist to include incidence-report (and any later named consumers).

Long-term maintenance: the retired token can spread again.

### POLICY C — Retire every test literal and read only from the schema constant

Meaning: even the evidence helper would stop owning a string literal and would import the schema value only.

Current support: schema already defines the token as the canonical legacy inject/read value.

Contradicting evidence: the current failing test **forbids** other test files from importing `OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL`. C is stricter than the present lock and is not what the red test encodes.

This is a plausible future contraction, not the live decision the red test is preserving.

## 8. Decision Consequences

### If we choose A

- Conceptually: the retired label has one test-side home.
- Authoritative: production schema for recognition; evidence helper for inject.
- Evidence-only: raw literals and the short constant name in tests.
- Transitional: CR-01 remains transitional until a later retirement campaign.
- Future developers preserve: no new raw literals; use the helper.
- Bugs prevented: accidental revival of gate-local opening authorship as a live path; fixture drift.
- Legitimate behavior constrained: diagnostic tests cannot paste the historical string without going through the helper.
- Duplicate ownership: decreases.
- Reconciled boundaries: strengthened.
- Implementation size: tiny / localized.

### If we choose B

- Conceptually: historical-token mention is allowed in selected diagnostic suites.
- Authoritative: still not live opening authorship.
- Evidence-only: no longer exclusive.
- Transitional: CR-01 remains, but the fence is weaker.
- Future developers preserve: an allowlist, not a single home.
- Bugs prevented: fewer; naming the token in diagnostics stays easy.
- Legitimate behavior constrained: almost none.
- Duplicate ownership: increases.
- Reconciled boundaries: weakened.
- Implementation size: tiny / localized.

### If we choose C

- Strongest contraction. Would require changing the current fence test as well as fixtures.
- Implementation size: localized, slightly broader than A.
- Not required to resolve the current red.

## 9. Evidence Table

| Category | Evidence | Stance |
|---|---|---|
| Current runtime behavior | Production opening writes `upstream_prepared_opening_fallback` or fail-closed `None`; mapper sends legacy token to `unknown-ambiguous` | SUPPORTS_OPTION_A |
| Current tests | RC-10 AST lock; sibling helper-only locks | SUPPORTS_OPTION_A |
| Current tests | `test_fallback_incidence_report.py:150` raw literal | SUPPORTS_OPTION_B |
| Current architecture | CR-01 transitional, not live provenance | SUPPORTS_OPTION_A |
| Current governance | CK closeout called the fence complete | SUPPORTS_OPTION_A |
| Historical design intent | Gate-local composer once emitted the token | NEUTRAL |
| Historical design intent | AB/AP/CK retired production writes | SUPPORTS_OPTION_A |
| Simulationist/gameplay implications | No player-facing opening change either way | NEUTRAL |
| Future extensibility | Single helper scales; allowlists re-open scatter | SUPPORTS_OPTION_A |
| Migration/implementation impact | Either A or B is a small test-only change | NEUTRAL |

## 10. Repository-Supported Recommendation

```text
Repository-supported recommendation: POLICY A
Confidence: HIGH
Reason: CK, CR-01, production comments, and sibling tests already treat the raw token as evidence-only. The remaining offender is one later diagnostic fixture, not a competing live authorship path.
```

This is advisory. The policy has **not** been decided.

## 11. User Decision

```text
RC-10

Plain-English question:
Should the retired opening-fallback label be allowed to appear as a raw string only in the opening-fallback evidence helper, or may other diagnostic tests name it directly?

Option A:
Keep the evidence-only fence. Route the incidence-report fixture through the helper.

Option B:
Allow selected diagnostic tests to name the raw historical token.

Existing architecture leans:
A

Important consequence:
Neither choice changes what players see. A keeps a retired path from looking live again.

Cursor recommendation:
A

USER DECISION REQUIRED:
[A / B / Other]
```
