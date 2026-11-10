# PR-PLAY-47 — Controlled narrative renderer prototype

Verdict: **B — PARTIAL**. The offline, explicitly enabled preview preserves the
exercised mechanical and disclosure boundaries. All 30 matrix renderings and
ten fixed-outcome stress renderings preserve their authorized discoveries and
pass the existing mechanical validator. No new regression is observed. The
result does **not** yet demonstrate a sufficiently strong narrative improvement
to recommend a live-provider trial. Long variants remain recognizably assembled
and repetitive. Textual uniqueness is not evidence of creative breadth.

Real provider requests: **0**. Real provider tokens: **0**. Live gameplay
experiments: **0**. No model/configuration/token-budget changes, campaign edits,
pushes, or follow-up experiments. Default gameplay has no import or reference
to the new renderer. This is a review artifact producer, not a GM response path.

## Architectural baseline and source map

PR-PLAY-46's 69-case corpus remains the baseline: 27 true positives, seven
false negatives, one false positive, 30 true negatives; precision 96.43%, recall
79.41%. Unsupported healing, poison removal, arrival, quest completion, NPC
allegiance, possession and wealth paraphrases still pass. “Dust rests in your
pack” is falsely rejected. The archived report, metrics and full before/after
corpora are included under `baseline_46/`; prior CURRENT_REVIEW is preserved
under `predecessor/` locally. No recognizer expansion or expectation edit occurs.

Relevant existing sources and functions:

| Responsibility | Existing implementation |
|---|---|
| Investigation resolution | `game/exploration.py::resolve_exploration_action`, `process_investigation_discovery` |
| Outcome representation | `game/models.py::ExplorationEngineResult` (resolver-returned dictionary); `game/mechanical_claims.py::mechanical_outcome` derived effect view |
| Disclosure selection | `game/authorized_information.py::revealed_information`, `supplement_revealed_information` |
| Clue handling | Resolver selects the clue; exploration discovery processing and session scene-runtime discovery records own persistence |
| Public scene extraction | `game/gm.py::_scene_layers`; player-known discovered-clue projection assembled by existing narration context |
| Narration projection | `game/narration_authorization.py::project_narration_payload` |
| Deterministic investigation speech | `game/api.py::deterministic_provider_skip_line`; `game/api_turn_support.py::_authoritative_resolution_fact_text` |
| Deterministic fallback | `game/immutable_valid_response.py::safe_nonresolution`; `game/mechanical_claims.py::mechanical_fallback` |
| AI narration and context | `game/gm.py::build_messages`, `call_gpt`; `game/prompt_context.py::build_narration_context` |
| Existing narrative-plan bundle | `game/narration_plan_bundle.py::build_narration_plan_bundle`, `public_narrative_plan_projection_for_prompt`; broader orchestration plan, deliberately not extended |
| Semantic checks | `game/immutable_valid_response.py::validate_generated_response`; `game/mechanical_claims.py::audit_mechanical_claims` |
| Final response assembly | `run_preserve_if_valid`, `seal_host_speech`, `seal_accepted_response`, `commit_text` in `immutable_valid_response.py`; API response assembly |
| Scene proposal adoption | `game/api.py::_validate_gm_scene_update_for_legacy_adoption` and post-GM adoption |
| World proposal adoption | API `_validate_gm_world_updates_for_legacy_adoption`, `apply_normalized_world_updates`; `game/world.py::apply_resolution_world_updates` |
| Improvisation promotion | `game/bounded_improvisation.py::promote_accepted_bounded_improvisation`, API post-GM pathway |
| Contextual leads | `game/gm.py::remember_recent_contextual_leads`, called by API and perception-grounding paths |

Reused components are the existing resolver, disclosure selection, public
projection, mechanical effect adapter/fallback and existing semantic validator.
There is no second writable outcome model or clue registry. The new frozen
view is a transient projection of the existing result. No broad orchestrator
change, production migration, or existing-plan integration is implemented.

## Three-layer prototype and explicit activation

**A. Authoritative outcome.** The existing resolver dictionary stays with the
engine. `authorize_investigation(resolution, narration_payload)` accepts only
investigation/observe/discover-clue/already-searched results and reuses the
production narration projection. Its frozen `AuthorizedInvestigation` contains:

* `status`: discovered, failed, known, or observed, derived from existing fields.
* `success`: the existing true/false/unknown value.
* `target_id`: the engine-resolved action/interactable identifier, not a catalog.
* `revealed`: exact strings from `revealed_information`; stale failed/repeated
  clue fields do not become newly revealed information.
* `known`: exact established player-knowledge strings, deduplicated against new
  discoveries; never constructed from the discoverable-clue catalog.
* `observations`: existing public visible-fact strings.
* `consequences`: existing deterministic effect realization, without private
  NPC/faction updates. Unsupported effect categories fail at the adapter.

The frozen view holds strings/tuples, and selection receives a JSON-detached
copy. Layer A cannot be edited through selection. Target identity and outcome
are available to the selector, but identifiers never become interpolated prose.
The generic target wording is a narrative specificity limitation.

**B. Presentation plan.** `OfflinePlanSelector.select(payload)` receives that
view and the available JSON Schema. It returns an object or JSON string. All
eight fields are required strings. Additional properties are forbidden.

| Field | Exact allowed values |
|---|---|
| structure | action_first, evidence_first, setting_first |
| pace | clipped, flowing, measured |
| tone | spare, reflective, intent |
| sensory_focus | none, visual, texture, listening |
| detail | lean, standard, extended |
| perspective | second_person, close_observation |
| transition | direct, pause, question |
| information_order | new_first, known_first |

`evidence_schema.json` contains the complete schema. Validation checks exact
keys/types/enum membership, rejects duplicate JSON properties and limits string
responses to 2,048 UTF-8 bytes. Nested values, arbitrary prose, identifiers,
update proposals and unbounded-detail values cannot enter the plan. It does
not use a forbidden-word classifier. No free-text plan field exists.

**C. Rendering.** `render_investigation` validates even for direct calls and
composes engine-owned opening/attention/transition clauses with unchanged
authorized strings. It can change block order, paragraph pauses, a semicolon
join, optional public observations, perspective, and sensory attention. Detail
controls zero/one/two optional observations; it cannot omit a discovery,
previously known clue, outcome status, or supported consequence. Appropriate
uncertainty is preserved in the exact source sentence rather than guessed or
paraphrased by the model.

Approved descriptive material describes momentary attention: looking, listening,
attending to texture, and pausing. These do not create objects, hazards, NPCs,
routes, rewards or persistent leads. No campaign record is required for such
texture. Specific environmental atmosphere comes only from public observations.
This is deliberately conservative; it does not prove a general distinction
between safe arbitrary English and mechanical facts.

`preview_investigation(view, selector, enabled=True)` is the only wrapper. The
default raises before invoking selection. There is no environment switch or
API wiring that enables it during play. Before application imports, the test
runner sets `ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT=1`, disables live
interpretation/expression, and pytest installs the existing live-model guard.
An offline selector is trusted Python code with untrusted returned data, not
an operating-system sandbox for arbitrary plugins. No real-provider adapter is
provided.

The frozen `InvestigationPreview` serializes only `preview_text`, validated
`plan`, `diagnostic`, and `used_fallback`. It has no `player_facing_text`,
metadata, scene/world updates, new-scene proposal, or mutation permissions.
It is never submitted to API legacy adoption, contextual-lead memory or
improvisation promotion. Sink instrumentation fails if any such call occurs;
accepted JSON and rejected hostile proposals make zero sink calls. No claim
is made that a future adapter could safely copy preview prose into those
legacy pathways without further work.

## Canonical and unfamiliar investigation results

Both canonical cases use the **actual exploration resolver** and unmodified
current campaign scene files in memory, not fabricated expected outcome text.

Notice board: resolver succeeds, clue `notice_patrol_route`:

> The missing patrol was last seen taking the northwest mud track past the crates.

Footprints: resolver succeeds, clue `milestone_mud_prints`:

> Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear.

All three plans retain those exact actionable/uncertain source sentences. No
extra patrol details, culprit, number of tracks, or destination are introduced.
Complete canonical source scenes, resolutions, selection payloads, plans,
narrations and audits are in `evidence_scenario_frontier_gate.json` and
`evidence_scenario_old_milestone.json`. A further ten valid plans use the same
footprints result without changing it.

The eight additional cases use unfamiliar identifiers absent from generic
rendering logic:

| Scenario | Authoritative result | Renderings complete / mechanically valid |
|---|---|---:|
| Successful discovery: ledger | Twelve ingots arrived; nine entered stock | 3/3 |
| Partial discovery: cipher | First symbol is a crescent; remainder illegible | 3/3 |
| Failed investigation: seal | Failed check establishes nothing; secret opening sequence unavailable | 3/3 |
| Previously discovered: rubbing | No new discovery; prior mason mark and unknown date retained | 3/3 |
| Uncertain evidence: fibres | Wool or flax possible; source undetermined | 3/3 |
| Mundane observation: basin | Public basin surface; no new clue | 3/3 |
| NPC evidence: receipt | Names porter Iven, involvement unexplained | 3/3 |
| No significant clue: tile | Public tile surface; no new clue | 3/3 |

Six of these matrix cases directly use resolver outputs on synthetic scenes.
The failed and repeat matrix cases are explicitly labeled outcome fixtures;
separate tests exercise the real failed skill-check resolver and the real
already-resolved-interactable marker, then render those actual outputs.
Partial discovery is partial information within an actual successful resolver
result, not a newly invented mechanical success tier. The two mundane cases
use the actual resolver's nullable success value rather than forcing success.

Each `evidence_scenario_*.json` retains full authoritative outcome, public and
private input, authorized renderer view, selection payload, host baseline,
three plans, full narration, completeness/consistency audits and state snapshot
comparison. `scenario_matrix.json` is an index, not a replacement for raw cases.

## Mechanical authority, hidden information, and fallback evidence

There are **26 direct/nested proposal tests** over 13 categories: item gain,
currency, damage, healing, conditions, travel, new clue, objective completion,
NPC changes, scene changes, world changes, remembered leads and improvised
details. Every proposal is rejected as an unknown field or non-string enum
value; every case preserves the legitimate clue and original outcome, invokes
the stub exactly once, and serializes no proposal. A separate authorized-damage
case renders an existing two-damage consequence once without applying it again.

Hidden canaries cover an undiscovered clue, GM notes, private NPC motivation,
faction activity, destination and world state. They are present in raw test
input and absent from both selection payload and renderer view/output. Actual
canonical hidden-fact strings are also excluded. Unknown identifier selections
are rejected by schema rather than resolved through a secret catalog. A selector
that mutates its detached request cannot change the view or final facts.
Known information and newly authorized discoveries remain available; real
failed investigations expose no secret.

These guarantees assume the engine correctly designates public observations,
known-clue records and resolver-authorized discoveries. Passing a secret string
as an already-discovered clue would violate that trusted caller contract; the
prototype is not a semantic classifier for incorrectly labeled engine content.

Fourteen invalid-plan cases cover empty/malformed JSON, wrong container/types,
missing keys, unsupported values, hidden identifiers, extra prose, oversized
responses and duplicate keys. Their raw inputs and results are retained as
`evidence_invalid_*.json`. Additional exception tests simulate selection
TimeoutError, selector RuntimeError and renderer RuntimeError. Each returns
deterministic fallback text with the actual clue, default-plan metadata and
fixed diagnostic code, without retrying or invalidating the completed action. No
exception prose or rejected proposal text becomes player narration. This is
timeout **simulation**, not a real deadline/cancellation implementation.

`evidence_mutation_sinks.json`, `evidence_isolation.json`, the 26 authority files,
and `evidence_actual_failed_repeat.json` preserve the boundary evidence. The
tests instrument legacy API validators/adopters, lead remembrance, improvisation
promotion and storage save functions. Static checks also verify no production
module imports the prototype. This establishes isolation for the standalone
preview, not an unimplemented gameplay integration.

## Provisional narrative-quality comparison

Every response is assessed with identical 0-2 criteria: information completeness,
mechanical consistency, naturalness, expressive range, atmosphere, investigative
clarity, repetition and cohesion. Maximum total is 16. A/B are reported separately
from the six prose categories (maximum 12). Full rubric, 40 individual score
vectors, complete responses and editorial reasons are in
`quality_comparison.json` and `NARRATIVE_COMPARISON.md`.

The baseline uses actual `deterministic_provider_skip_line` where available,
otherwise the existing authoritative fact emitter, then existing
`safe_nonresolution` if the emitter returns nothing. Each source is recorded;
fallback comparisons are not falsely described as the default production
provider-skip path for every scenario.

| Family | Mechanics /2 | Information /2 | Narrative /12 | Total /16 |
|---|---:|---:|---:|---:|
| Existing host/fallback | 2.0 | 1.5 | 5.1 | 8.6 |
| Controlled concise | 2.0 | 2.0 | 6.8 | 10.8 |
| Controlled atmospheric | 2.0 | 2.0 | 6.1 | 10.1 |
| Controlled investigative | 2.0 | 2.0 | 6.0 | 10.0 |

These are **provisional, unblinded editorial judgments by the implementing
agent**, not an independent evaluation, live-model creativity, statistical
effect estimate, or measured player preference. The one-word basin/tile host
emissions are weak baselines that inflate aggregate improvement. On canonical
cases alone, prose scores are host 6/12, concise 7/12, atmospheric 6.5/12,
investigative 6/12. That small, subjective difference does not justify calling
this a demonstrated worthwhile player-experience improvement.

The concise family is usually clear and economical. Extended variants add
some real public atmosphere, but “examination,” “attention,” and rhetorical
question scaffolding recur. Prior-clue delivery is complete but label-like.
Context-first ordering sometimes delays the actionable result. Sensory focus
changes attention more than physical atmosphere. Perfect mechanics does not
make those prose weaknesses disappear.

## Expressive-range stress test

Ten distinct valid plans yield ten distinct readable outputs for the unchanged
footprints result. They span three block orders, three cadences and four sensory
attention modes, with 22-70 words. Four outputs reuse the same rhetorical
question, five use “examination,” and six use “evidence.” Every output repeats
the exact clue sentence by design. `evidence_stress.json` preserves all text;
`expressive_range.json` assesses each requested dimension and repetition counts.

Result-first versus context-first and paragraph pauses are real presentation
changes. However, there are **three recognizable block-order families**, finite
opening/attention/transition inventories, and inert controls when optional
material or prior knowledge is absent. The 3,888 syntactically valid enum
combinations are not 3,888 meaningfully different narratives. No adjectives or
irrelevant filler were added just to make ten text strings differ. The limited
range remains the central negative finding.

## Regression and state integrity

The predecessor's 28-suite selection was replayed in an independent repository
copy under `development/tmp/pr_play_47_workspace`, with actual code, tests,
campaign copies and saved offline fixtures. This protects prior artifact files
from tests that write evidence to fixed paths. Existing test expectations,
default host speech, semantic validation and production source remain untouched.

| Run | Collected | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|
| Fresh baseline | 640 | 617 | 23 | 0 |
| Final including prototype | 698 | 675 | 23 | 0 |

All **58 new tests pass**; zero new regressions and identical existing test
results. The 23 pre-existing failures cover finalization/API narration,
exploration, travel, social locks and opening behavior. They are not suppressed
or relabeled. PR-PLAY-44, -45 and -46, investigation/skill checks, clue delivery,
public context projection, mechanical claim composition, host speech grounding,
fallback, combat/state integrity and finalization are included. One existing
FastAPI/Starlette deprecation warning remains. The complete repository suite
was not run and is not claimed green.

Initial isolation setup attempts failed because legacy root-level fixtures,
saved evidence directories and a pytest temporary parent were missing. Raw
collection/setup failures are retained as `baseline_setup_failure.*` and
`baseline_fixture_failure.*`. Copying the required fixtures and creating the
temporary parent resolved those harness errors; no application or test
expectation was changed to improve the pass count.

Full commands, stdout, JUnit failures and exact per-test result comparison are
packaged. The initial focused run passed 57 tests before the additional
serialization/mutation-sink test; all 58 pass in both complete final runs.
SHA256 comparison of every campaign-data file before/after must pass
before packaging. Existing production/test source is compared against the
isolated task-start copy. State integrity is also checked at each exercised
projection/render/fallback boundary. These are read-only narration tests; the
existing isolated resolver/regression tests may legitimately mutate their own
temporary copied state.

## Performance and implementation complexity

For the fixed footprints case, `evidence_performance.json` records 500 local
samples per operation, serialized UTF-8 sizes and traced Python allocation data:

| Measurement | Result |
|---|---:|
| Presentation schema | 820 bytes |
| Representative plan | 213 bytes |
| Authorized view | 520 bytes |
| Full selector request including controls | 1,394 bytes |
| Validation median / p95 | 2.9 / 3.7 microseconds |
| Rendering including validation median / p95 | 6.3 / 7.5 microseconds |
| Fallback including selection-payload/stub overhead median / p95 | 104.3 microseconds / 0.1321 ms |
| Accepted preview median / p95 | 114.3 microseconds / 0.1571 ms |
| Traced allocation peak / retained after 100 calls | 29,797 / 21,504 bytes |

The earlier complete run's noisy end-to-end tails (4.08 ms fallback p95 and
6.73 ms accepted-preview p95) are retained in `earlier_final_performance.json`,
not replaced with the faster render-only number. The final measurements above
are from sequential local wall time in the regression
process, not deployment latency guarantees. Tracemalloc figures include fixture
and serialization allocations, not incremental process RSS or a leak estimate.
`source_change_manifest.json` records exact source bytes and line counts.

A rough bytes/4 estimate is **349 input and 54 output tokens** for plan selection
(rounded up, excluding surrounding provider instructions/envelope). It is an
estimate, not measured tokenizer usage, billing or a configured budget increase.
No monetary quote is inferred without a verified model tariff. Actual provider
usage remains zero. Validation is local and requires no second provider call.
A future plan could be an optional sibling field in an existing interpretation
response, provided selection sees an appropriately authorized outcome; that
outcome is generally not yet available before mechanical resolution, so timing
and generic-versus-outcome-aware controls require evaluation. No such integration
or second call is implemented here.

The prototype keeps implementation localized, but authoring cost remains real:
six opening variants, three nonempty sensory-attention clauses, two nonempty
transitions, status clauses, and a small composition grammar. Expanding freedom
by hand-authoring many more such clauses risks becoming exactly the elaborate
template system this investigation was intended to avoid. No evidence here
establishes that this tradeoff scales economically to other actions.

## Architectural questions and next-step decision

1. **Mechanical authority:** demonstrated for exercised standalone previews:
   strict enum plans, immutable derived view, exact facts, no adoption route.
2. **Authorized information:** demonstrated across 30 variants, ten stress
   outputs and rejection fallbacks; actual canonical disclosures preserved.
3. **Hidden information:** demonstrated on canonical hidden facts and six
   synthetic secret classes; assumes correct engine public/known designation.
4. **More natural narration:** small provisional advantage for concise output;
   no defensible general naturalness or player-experience improvement yet.
5. **Expressive variation:** real ordering/cadence variation, insufficient
   structural breadth. Ten different strings do not resolve that limitation.
6. **Readability across outcomes:** readable in the matrix, with repetitive
   attention language and awkward known-information framing.
7. **Authoring burden:** already template-dependent; larger burden is a
   reasonable inference, not a measured authoring-time study.
8. **Implementation complexity:** small isolated module is demonstrated;
   production integration complexity remains unverified.
9. **Expected provider cost:** compact plan suggests modest cost; token and
   monetary costs are unverified estimates. No budget was changed.
10. **Expansion beyond investigation:** not justified by this offline evidence.
    Other effect categories and safe legacy adoption need separate design.

**Recommendation:** retain the offline prototype and its authority boundary,
but perform another bounded offline quality pass before a live-provider trial.
Define blind comparison criteria and a clear threshold for actual prose
improvement; test whether fewer, better compositional controls and relevant
public observations improve specificity without proliferating canned clauses.
Do not expand arbitrary free-text authority or phrase recognizers to manufacture
freedom. A future live-provider proposal should require evidence of quality
improvement, outcome-availability/call-budget design, actual timeout isolation,
and an adapter that cannot reach legacy memory/adoption sinks. No live trial,
production adoption, PR-PLAY-48 or further task is authorized or started here.

## Package contents and exact changes

New application source: `game/controlled_investigation_renderer.py`.
New acceptance tests: `tests/test_pr_play_47_controlled_renderer.py`.
New reproducibility utilities: `artifacts/pr_play_47/run_regression.py`,
`evaluate.py`, `package_review.py`. Report/evidence files are confined to
`artifacts/pr_play_47/`; CURRENT_REVIEW pointers are updated after preserving
their predecessors. Existing application/test/configuration/campaign source
is not edited by this task.

The archive includes this executive/design/contract/baseline report, exact
source snapshots and diff/manifest, full schema, canonical and eight-scenario
records, 30 presentation variants, all proposal/invalid/exception inputs and
outputs, hidden/state-integrity evidence, all 40 individually scored host and
controlled responses, ten stress outputs, raw regression failures/commands/XML,
performance evidence, usage declaration and hashed content manifest. Failed
cases and limitations are retained in full. The verified timestamped archive
and stable `handoff/CURRENT_REVIEW.zip` contain the same package. Work stops
after evidence packaging.
