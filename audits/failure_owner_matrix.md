# Failure Owner Matrix

Rule used here: one primary owner, optional secondary only when diagnosability genuinely crosses a boundary. Primary owner is the earliest legitimate fault location, not the layer where the bad prose finally became visible.

Opening-fallback routing policy note (Cycle F.H): current dashboard/classifier behavior is still coarse and gate-biased. Opening-fallback fields classify under `fallback`, and `fallback` currently routes to `game/final_emission_gate.py`. Desired future routing is symptom-specific first-fault routing after a reviewed classifier policy change: gate selection/final source/fail-closed/FEM merge stay with `game/final_emission_gate.py`; composition/basis goes to `game/opening_deterministic_fallback.py`; upstream payload shape/authorship goes to `game/upstream_response_repairs.py`; owner-bucket mapping goes to `game/final_emission_meta.py`; replay projection goes to `tests/helpers/golden_replay.py`; classifier policy goes to `tests/helpers/failure_classifier.py`; dashboard rendering goes to `tests/helpers/failure_dashboard_report.py`.

| Failure Type | Primary Owner | Secondary Owner | Why |
|---|---|---|---|
| Exact final-text hash mismatch | replay | emission | Exact drift is an opt-in replay assertion; emission is secondary only when no upstream structural predicate changed. |
| Golden structural field mismatch | replay | projection | Replay detects the mismatch; projection is secondary if the observed field was missing from payload/trace. |
| Dotted-path assertion missing | replay | projection | Assertion system owns the fail; projection owns absence if runtime emitted data but helper failed to project it. |
| Missing `route_kind` in replay row | projection | route | Current helper marks unavailable; route is secondary if runtime never produced route metadata. |
| Missing `trace.social_contract_trace` | projection | route | Replay cannot classify route owner confidently without the compact trace. |
| Wrong route selection | route | planner | Route owner is `interaction_context`/API routing; planner is secondary if planner/resolution shaped a misleading route input. |
| No addressable social target | route | speaker | Social target resolution failed before speaker validation can operate. |
| Target not addressable/offscene | route | validator | Route owns target choice; validators/scene roster legality are secondary. |
| Missing route metadata | route | projection | Metadata should be emitted by routing/API trace assembly; projection may fail to expose it. |
| Dialogue lock broken | continuity | route | Continuity owns active interlocutor preservation; route owns final lane choice. |
| Vocative override ignored | route | speaker | Canonical entry owns explicit target override; speaker owns final reply if target was correct but emitted speaker drifted. |
| Declared actor switch ignored | route | continuity | Route target selection owns explicit switch; continuity is secondary because it may have over-preserved prior target. |
| Speaker attribution mismatch | speaker | emission | Speaker contract enforcement owns emitted speaker legality; emission is secondary when late rewriting changes labels. |
| Forbidden generic fallback speaker | speaker | fallback | Speaker contract rejects labels like generic fallback speakers; fallback may have authored the illegal label. |
| Dialogue ownership invented with no allowed speaker | speaker | emission | Speaker contract detects invented dialogue ownership; emission text generation authored it. |
| Pregate alias rejected incorrectly | speaker | planner | Alias legality belongs to dialogue social plan/speaker contract; planner may have omitted declared alias metadata. |
| Multi-speaker interruption under continuity | continuity | speaker | Continuity validator owns uncued switch; speaker contract owns speaker legality details. |
| Planner bypass / nonplan narration | planner | emission | CTIR/narration seam guard records planner bypass before final text is packaged. |
| Planner continuity bundle stamp drift | planner | continuity | Planner/narration bundle mismatch is primary; continuity is secondary when same-turn retry drift manifests as continuity loss. |
| Invalid scene transition target | route | validator | Destination binding route/action target is primary; scene validation provides legality support. |
| Transition destination semantic mismatch | route | semantic_mutation | Route/normalized action chose wrong destination; semantic mutation if text later implies a different one. |
| Missing response type contract | validator | planner | Contract derivation/materialization should exist before emission; planner/resolution may lack required inputs. |
| Response-type violation | validator | emission | Validator owns required answer/action/opening/dialogue shape; emission authored nonconforming text. |
| Response-type repair used unexpectedly | emission | validator | Gate/emission stack performed mutation; validator explains why it considered candidate illegal. |
| Answer completeness failure | validator | emission | Deterministic validator owns fail; emission authored incomplete answer. |
| Response delta echo | validator | semantic_mutation | Validator owns anti-echo; semantic mutation is secondary when repair/rewrite preserves too much prior content. |
| Fallback behavior violation | validator | fallback | Validator owns behavior contract; fallback owns authored fallback shape. |
| Fallback substitution observed | fallback | emission | Fallback family/source is primary; emission gate may be selecting and packaging it. |
| Global scene fallback emitted | fallback | emission | Fallback substitution occurred; emission only owns final selection point if upstream did not request it. |
| Opening deterministic fallback | fallback | emission | Opening fallback composer/upstream-prepared payload owns fallback prose; gate selects it. |
| Opening fallback failed closed | fallback | validator | Fallback/context preparation failed; validator response-type/opening rules explain failure. |
| Emergency nonplan output | fallback | planner | Emergency fallback is primary emitted substitute; planner seam failed earlier. |
| Stock-line leakage or overuse | fallback | evaluator | Fallback authored repeated stock lines; evaluator may observe degradation over time. |
| Sanitizer scaffold leakage | sanitizer | emission | Sanitizer owns strip/rewrite of internal labels; emission is where final leakage becomes visible. |
| Sanitizer over-rewrite | sanitizer | semantic_mutation | Sanitizer owns rewrite; semantic mutation captures meaning loss after rewrite. |
| Serialized payload leakage | sanitizer | emission | Sanitizer has detectors for JSON-ish payloads; emission exposes final text. |
| Final-emission semantic mutation | semantic_mutation | emission | Meaning changed after planning; emission gate/repairs are the physical site. |
| Late whitespace-only normalization | normalization | emission | Normalization owns deterministic formatting; emission owns application point. |
| Metadata normalization drift | normalization | projection | Normalized observability view differs from raw metadata; projection may consume normalized view. |
| FEM missing final source | emission | projection | Gate should stamp `final_emitted_source`; replay projection may miss legacy lanes. |
| FEM fallback family missing | emission | fallback | Gate stamps final metadata; fallback source may have lacked classification. |
| Stage-diff transition missing | emission | projection | Gate/retry should record snapshots; projection/dashboard may not consume them. |
| Schema validation error | validator | normalization | Schema validators own malformed object detection; normalizers may have adapted bad legacy input. |
| Validator repair changed text | validator | semantic_mutation | Some validation packages include minimal repairs; semantic mutation tracks meaning risk. |
| State authority violation | validator | normalization | Authority guard owns illegal write; normalizers/adapters may have routed data to wrong domain. |
| Evaluator hard failure | evaluator | replay | Evaluator owns scores/failures; replay is secondary if failure occurred during replay run. |
| Evaluator warning only | evaluator | none | Warnings are evaluator-owned advisory signals. |
| Evaluator downgrade/score zero due to dead turn | evaluator | emission | Evaluator applies policy; emission/FEM dead-turn metadata drives it. |
| Progressive degradation | evaluator | continuity | Scenario-spine evaluator observes degradation; continuity may be the runtime root if callbacks/anchors decay. |
| Branch coherence failure | evaluator | planner | Evaluator detects non-divergence/coherence failure; planner/route often owns root branch behavior. |
| Replay exact text misleading while structure passes | replay | evaluator | Replay exact drift alone may not indicate owner; evaluator/semantic checks decide severity. |
| Projection strips debug needed for classification | projection | emission | Projection/read-side owns missing dashboard field; emission owns whether raw debug existed. |
