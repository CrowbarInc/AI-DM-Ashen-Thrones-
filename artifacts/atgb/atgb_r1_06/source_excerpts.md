# Selected source excerpts

Current working-tree, one-based lines. Static inspection only; no provider dispatch or gameplay execution. Full selected source hashes appear in the handoff manifest.

## game/live_chat_interpretation.py:29–75

```text
29: 
30: RECIPIENTS = ("GM", "NPC", "CHARACTER", "SESSION", "MIXED", "AMBIGUOUS")
31: PURPOSES = ("QUESTION", "DESCRIPTION", "EXPLANATION", "RECALL", "RULES", "ACTION", "OBSERVATION", "CORRECTION", "WITHDRAWAL", "CONFIRMATION", "TENTATIVE", "CLARIFICATION")
32: 
33: 
34: def production_interpretation_schema() -> dict[str, Any]:
35:     """Extend the existing interpretation envelope, without granting outcomes."""
36:     import copy
37:     schema = copy.deepcopy(_contract()[5]())
38:     schema["properties"]["communication"] = {
39:         "type": "object", "additionalProperties": False,
40:         "properties": {
41:             "recipient": {"type": "string", "enum": list(RECIPIENTS)},
42:             "purpose": {"type": "string", "enum": list(PURPOSES)},
43:             "subject": {"type": "string"},
44:             "evidence_refs": {"type": "array", "items": {"type": "string"}},
45:         },
46:         "required": ["recipient", "purpose", "subject", "evidence_refs"],
47:     }
48:     schema["required"].append("communication")
49:     # Structured generation follows property order. Choose the speech act
50:     # before the operation-shaped legacy fields can bias the recipient.
51:     schema["properties"] = {"communication": schema["properties"].pop("communication"), **schema["properties"]}
52:     schema["properties"]["communication"]["properties"]["recipient"]["description"] = (
53:         "Communicative function of the whole turn, not the person mentioned. GM: asks the facilitator about the world, "
54:         "including interpreting another person's behavior. NPC: the character actually speaks to that person. "
55:         "SESSION: mechanics or play procedure. CHARACTER: committed physical attempt. "
56:         "MIXED: distinct speech/action intentions, including conditional action. AMBIGUOUS: unresolved referent."
57:     )
58:     schema["properties"]["communication"]["properties"]["purpose"]["description"] = (
59:         "Speech act, independent of executable operations: CONFIRMATION accepts pending work; CORRECTION revises "
60:         "unexecuted intent; WITHDRAWAL cancels it; RULES asks play procedure; EXPLANATION asks cause or meaning. "
61:         "These control acts are never ACTION, even when mentioning a physical operation."
62:     )
63:     return schema
64: 
65: 
66: def valid_communication(value: Any, evidence: dict[str, str]) -> bool:
67:     return (
68:         isinstance(value, dict)
69:         and set(value) == {"recipient", "purpose", "subject", "evidence_refs"}
70:         and value.get("recipient") in RECIPIENTS
71:         and value.get("purpose") in PURPOSES
72:         and isinstance(value.get("subject"), str)
73:         and isinstance(value.get("evidence_refs"), list)
74:         and all(isinstance(ref, str) and ref in evidence for ref in value["evidence_refs"])
75:     )
```

## game/live_chat_interpretation.py:130–159

```text
130: 
131: def live_interpretation_consumed() -> bool:
132:     return bool(_CONSUMED.get())
133: 
134: 
135: def production_live_interpretation_enabled() -> bool:
136:     return live_interpretation_enabled() and not provider_calls_disabled()
137: 
138: 
139: def _contract():
140:     """Import the existing contract after its packages force interpretation off."""
141:     global _CONTRACT
142:     if _CONTRACT is not None:
143:         return _CONTRACT
144:     previous = os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION")
145:     try:
146:         from experiments.pr_do.adapter import adapt_interpretation
147:         from experiments.pr_dp import CONFIGURED_MODEL
148:         from experiments.pr_dp.prompt import provider_schema
149:         from experiments.pr_dr.prompt import build_messages_for_catalog, context_leaks, preflight_tokens
150:     finally:
151:         if previous is None:
152:             os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)
153:         else:
154:             os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = previous
155:     _CONTRACT = (
156:         adapt_interpretation,
157:         build_messages_for_catalog,
158:         context_leaks,
159:         preflight_tokens,
```

## game/live_chat_interpretation.py:214–253

```text
214: def request_interpretation(messages: list[dict[str, str]], *, estimated_input: int) -> dict[str, Any]:
215:     """One structured completion. No retry and no model switch."""
216:     _adapt, _build, _leaks, _preflight, model_id, schema_fn = _contract()
217:     attempt = admit_request(owner="live_chat_interpretation.request_interpretation", model=model_id, purpose="interpretation", estimated_input=estimated_input, max_output=_OUTPUT_CAP)
218:     refusal = attempt.refusal
219:     if refusal:
220:         usage = attempt.finish(
221:             {
222:                 "purpose": "interpretation",
223:                 "sent": False,
224:                 "model": model_id,
225:                 "input_tokens": None,
226:                 "output_tokens": None,
227:                 "total_tokens": None,
228:                 "refusal": refusal,
229:             }
230:         )
231:         return {"ok": False, "sent": False, "reason": refusal, "error": refusal, "usage": usage}
232:     from openai import OpenAI
233: 
234:     from game.config import get_openai_api_key
235: 
236:     started = time.perf_counter()
237:     try:
238:         from game.gm import provider_timeout_seconds
239: 
240:         client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds())
241:         response = attempt.dispatch(client.responses.create,
242:             model=model_id,
243:             input=messages,
244:             temperature=0,
245:             max_output_tokens=_OUTPUT_CAP,
246:             text={
247:                 "format": {
248:                     "type": "json_schema",
249:                     "name": "pr_dr_interpretation",
250:                     "strict": True,
251:                     "schema": production_interpretation_schema(),
252:                 }
253:             },
```

## game/live_chat_interpretation.py:297–376

```text
297: def interpret_production_turn(
298:     *,
299:     player_text: str,
300:     mode: str,
301:     scene: dict | None,
302:     world: dict | None,
303:     log: list | None,
304:     session: dict | None = None,
305: ) -> dict[str, Any]:
306:     """Return skipped, blocked, or accepted. Accepted carries a bridge record."""
307:     if not production_live_interpretation_enabled():
308:         reason = "provider_calls_disabled" if provider_calls_disabled() else "live_interpretation_disabled"
309:         return {"status": "skipped", "reason": reason, "record": None, "provider_requests": []}
310: 
311:     adapt_interpretation, build_messages_for_catalog, context_leaks, preflight_tokens, _model, _schema = _contract()
312:     catalog = _catalog_rows(scene, world)
313:     recent = player_visible_turns(log or [], limit=2)
314:     messages = build_messages_for_catalog(
315:         player_text,
316:         scene_summary=_scene_summary(scene),
317:         catalog=catalog,
318:         recent_visible=recent or None,
319:     )
320:     from game.conversational_orchestration import public_conversation_evidence
321:     evidence = public_conversation_evidence(scene, log)
322:     messages[0]["content"] += (
323:         " Establish communication.recipient and purpose BEFORE describing operations. "
324:         "GM is the facilitator, never an NPC. Questions about perception, possibility, prior narration, "
325:         "third-person NPC appearance, or what an NPC meant address GM; speaking TO an NPC uses NPC. "
326:         "A short question continuing an active NPC exchange may address NPC; explicit GM address overrides it. "
327:         "SESSION owns rules and interface questions. CHARACTER owns committed attempts only. "
328:         "MIXED owns question plus conditional or independent action; preserve all components, never authorize them. "
329:         "CORRECTION and WITHDRAWAL never undo committed facts. TENTATIVE and capability questions never commit actions. "
330:         "For GM/session communication leave action_components empty unless a NEW observation is requested; "
331:         "use existing PERCEIVE/INSPECT for that. Meaningful communication can be INTERPRETED with zero operations. "
332:         "Select evidence_refs only when the supplied PUBLIC passage actually answers the question. "
333:         "No evidence means unknown. Subject describes the question, never a new fact. "
334:         "Do not convert GM communication into SOCIAL_SIGNAL, ASK or an unsupported operation."
335:         " A declaration of what I/we do is CHARACTER/ACTION, including inspection; "
336:         "a request to describe already visible information is GM/DESCRIPTION. "
337:         "NPC clarification or recall of what that NPC just said is NPC/CLARIFICATION with an ASK component; "
338:         "select its npc:<speaker>:<topic> evidence reference when supplied. "
339:         "For GM recall of NPC speech, prefer that same established NPC answer passage."
340:         " For clarification of the most recent NPC statement, npc_latest_reply is the actual latest "
341:         "utterance, including inability or refusal. Do not substitute an earlier topic for it. "
342:         " Communication is the primary contract; legacy communication_mode describes the same speech act. "
343:         "Third-person description of a person does not speak to them. A question about what their expression "
344:         "implies is GM/EXPLANATION; do not ask the person on the player's behalf. "
345:         "A request about checks, rolls or adjudication is SESSION/RULES even when phrased hypothetically. "
346:         "Cancellation, revision and assent describe control of pending intent, never a new world attempt. "
347:         "Use AMBIGUOUS when a demonstrative has no unique context referent. "
348:         "For a cause question prefer cause: evidence; if only an outcome is known, do not pretend it explains why. "
349:         "For mixed observation and speech preserve both components under MIXED; the engine controls their order. "
350:         "Keep descriptions concise so the complete schema fits the output budget."
351:         " SESSION does NOT mean every instruction submitted to the engine: describing a character's physical "
352:         "movement is CHARACTER/ACTION. Assent to proceeding is GM/CONFIRMATION even without a pending proposal "
353:         "(then the engine will clarify); revising a proposed attempt is GM/CORRECTION. "
354:         "Conditional commitments are MIXED, even without a question mark. "
355:         "Ancillary facing, turning toward a speaker, or addressing them is context for ASK, not a separate "
356:         "SOCIAL_SIGNAL attempt. Dialogue topics need not be entity ids: unresolved_references holds missing "
357:         "action targets or referents, never merely an unknown subject of a question."
358:     )
359:     messages[1]["content"] += "\nPUBLIC answer evidence: " + json.dumps(evidence, ensure_ascii=False)
360:     interaction = (session or {}).get("interaction_context") or {}
361:     context = (session or {}).get("conversational_context") or {}
362:     exchange = context.get("last_gm_exchange") or {}
363:     messages[1]["content"] += "\nConversation ownership context: " + json.dumps({
364:         "active_npc_id": interaction.get("active_interaction_target_id"),
365:         "last_response_category": exchange.get("category"),
366:         "last_response_owner": exchange.get("owner"),
367:         "last_subject": exchange.get("subject"),
368:         "pending_kind": (context.get("pending_clarification") or {}).get("kind"),
369:         "pending_scene_id": (context.get("pending_clarification") or {}).get("scene_id"),
370:         "pending_steps": [
371:             {key: step.get(key) for key in ("operation", "target_id", "text", "supported")}
372:             for step in (context.get("pending_clarification") or {}).get("steps", [])[:4]
373:             if isinstance(step, dict)
374:         ],
375:         "pending_choices": (context.get("pending_clarification") or {}).get("choices", [])[:4],
376:     }, ensure_ascii=False)
```

## game/live_chat_interpretation.py:427–506

```text
427:     payload = dict(parsed)
428:     communication = payload.pop("communication", None)
429:     # Old recorded records remain replayable; the live provider schema requires ownership.
430:     if communication is not None and not valid_communication(communication, evidence):
431:         return _blocked("malformed_communication", "I need you to clarify who you are addressing.",
432:                         tags=["interpretation_rejected", "non_mutating"],
433:                         extra={"provider_requests": provider_requests})
434:     if mode == "IC":
435:         payload["communication_mode"] = "IN_WORLD_ACTION"
436:     if communication and payload.get("action_components") and (
437:         communication["recipient"] in {"CHARACTER", "NPC"}
438:         or (communication["recipient"] == "GM" and communication["purpose"] == "OBSERVATION")
439:     ):
440:         payload["communication_mode"] = "IN_WORLD_ACTION"
441:     if communication and communication["recipient"] in {"GM", "SESSION"} and communication["purpose"] == "ACTION" and payload.get("communication_mode") == "IN_WORLD_ACTION":
442:         # Recipient is where the player speaks; ACTION purpose is a declared
443:         # character attempt. Preserve that commitment rather than swallowing it
444:         # as a description request when the two model labels disagree.
445:         components = payload.get("action_components") or []
446:         if len(components) == 1 and components[0].get("operation_class") in {"MOVE", "INSPECT", "PERCEIVE"}:
447:             communication["recipient"] = "CHARACTER"
448:         elif len(components) > 1:
449:             communication["recipient"] = "MIXED"
450:     payload, incidental = normalize_social_scope(payload, communication)
451:     adapted = adapt_interpretation(payload, permitted_ids=[entity_id for entity_id, _label, _kind in catalog])
452:     reconciliation = None
453:     if adapted.get("structurally_valid"):
454:         from game.player_interpretation_bridge import reconcile_reference_annotations
455:         payload, reconciliation = reconcile_reference_annotations(
456:             payload, player_text=player_text, scene=scene, world=world, session=session)
457:         if communication:
458:             # Reuse the established ownership correction before eligibility can
459:             # reject a grounded direct address on a stale GM/clarification label.
460:             from game.conversational_orchestration import _reclassify_direct_npc_address
461:             prepared = _reclassify_direct_npc_address(
462:                 {**payload, "communication": communication}, player_text,
463:                 scene=scene, world=world, session=session)
464:             communication = prepared.get("communication", communication)
465:             payload = {key: prepared[key] for key in payload}
466:         adapted = adapt_interpretation(payload, permitted_ids=[entity_id for entity_id, _label, _kind in catalog])
467:     record = adapted.get("record") if isinstance(adapted.get("record"), dict) else None
468:     if record is not None and communication is not None:
469:         record["communication"] = communication
470:         record["incidental_context"] = incidental
471:         record["reference_reconciliation"] = reconciliation
472:         # Only passages selected from the engine's public projection can reach emission.
473:         record["public_evidence"] = {ref: evidence[ref] for ref in communication["evidence_refs"]}
474:     eligibility = adapted.get("eligibility") if isinstance(adapted.get("eligibility"), dict) else {}
475:     disposition = str(eligibility.get("disposition") or "")
476:     common = {
477:         "raw_interpretation": raw,
478:         "reference_reconciliation": reconciliation,
479:         "provider_requests": provider_requests,
480:         "eligibility_disposition": disposition,
481:         "model_communication_mode": parsed.get("communication_mode"),
482:         "interpretation_status": None if record is None else record.get("interpretation_status"),
483:     }
484:     if not adapted.get("structurally_valid") or record is None:
485:         return _blocked(
486:             "malformed_interpretation",
487:             "I couldn't read that as a gameplay action. Please say it again in plain words.",
488:             tags=["interpretation_rejected", "non_mutating", "malformed_interpretation"],
489:             extra=common,
490:         )
491:     if disposition == "OUT_OF_CHARACTER" and mode != "IC":
492:         return _blocked(
493:             "automatic_ooc",
494:             "Understood. I'll treat that as out of character. No gameplay action is executed, "
495:             "no game time advances, and committed state is unchanged.",
496:             tags=["ooc_correction", "non_mutating", "automatic_ooc"],
497:             extra={**common, "record": record},
498:         )
499:     if disposition in {"NEEDS_CLARIFICATION", "SAFE_ABSTENTION"}:
500:         question = str(record.get("clarification_question") or "").strip()
501:         text = question or "I need a clearer action or target before I change anything in the scene."
502:         return _blocked(
503:             "clarification_required",
504:             text,
505:             tags=["interpretation_clarification", "non_mutating"],
506:             extra={**common, "record": record},
```

## experiments/pr_dr/prompt.py:15–21

```text
15: _MODE_LINE = (
16:     "IN_WORLD_ACTION=the character acts or speaks in the scene; "
17:     "OUT_OF_CHARACTER_CORRECTION=the player corrects a referent, an intention, or a committed action; "
18:     "RULES_QUESTION=the player asks how play works; "
19:     "CLARIFICATION=the utterance is unclear; "
20:     "OTHER=none of these."
21: )
```

## experiments/pr_dr/prompt.py:60–83

```text
60:     *,
61:     scene_summary: str,
62:     catalog: list[tuple[str, str, str]],
63:     recent_visible: list[dict[str, str]] | None = None,
64: ) -> list[dict[str, str]]:
65:     """PR-DO prompt for one visible catalog. Recent lines are player-visible text only."""
66:     visible = "; ".join(f"{entity_id}={label} ({kind})" for entity_id, label, kind in catalog)
67:     lines = [
68:         f"Utterance: {utterance}",
69:         f"Visible scene: {scene_summary}",
70:         f"Permitted entity references: {visible}.",
71:         f"Communication modes: {_MODE_LINE}",
72:         f"Operation classes: {_CLASS_LINE}",
73:         "Later validation is not authorization. Describe the attempt. Do not authorize execution.",
74:         "If the utterance is ambiguous between in-character play and table talk, use CLARIFICATION, one question, and no guessed id.",
75:         "Premises and wished results are text. No outcomes, HP, dice, inventory, time, canon, NPC commitments, hidden facts, or execution.",
76:         "Use only permitted entity ids. Order attempts. Empty list or string if unused.",
77:     ]
78:     if recent_visible:
79:         lines.append("Recent visible turns: " + json.dumps(recent_visible, ensure_ascii=False))
80:     return [
81:         {"role": "system", "content": "Fill the schema. Describe the attempt. Do not authorize execution."},
82:         {"role": "user", "content": "\n".join(lines)},
83:     ]
```

## experiments/pr_dp/prompt.py:25–37

```text
25: def provider_schema() -> dict[str, Any]:
26:     """JSON Schema for the model-writable PR-DO object.
27: 
28:     ``not_model_writable`` is documentation in schema_document(). It is not a
29:     model field and not a JSON Schema keyword, so it is omitted here. Property
30:     names, enums, and required fields are copied unchanged.
31:     """
32:     document = schema_document()
33:     return {
34:         "type": "object",
35:         "additionalProperties": False,
36:         "properties": document["properties"],
37:         "required": list(document["required"]),
```

## experiments/pr_do/schema.py:9–29

```text
9: COMMUNICATION_MODES = frozenset(
10:     {
11:         "IN_WORLD_ACTION",
12:         "OUT_OF_CHARACTER_CORRECTION",
13:         "RULES_QUESTION",
14:         "CLARIFICATION",
15:         "OTHER",
16:     }
17: )
18: 
19: INTERPRETATION_STATUSES = frozenset(
20:     {
21:         "INTERPRETED",
22:         "CLARIFICATION_REQUIRED",
23:         "UNSUPPORTED_REQUEST",
24:         "ABSTAIN",
25:     }
26: )
27: 
28: # Classes the engine may later validate. Eligibility is not execution.
29: VALIDATION_ALLOWLIST = frozenset(
```

## experiments/pr_do/schema.py:59–62

```text
59: CORRECTION_SUBJECTS = frozenset({"NONE", "REFERENT", "INTENTION", "COMMITTED_ACTION"})
60: 
61: DISPOSITIONS = frozenset(
62:     {
```

## experiments/pr_do/schema.py:145–202

```text
145:             "asserted_premises": {
146:                 "type": "array",
147:                 "items": {
148:                     "type": "object",
149:                     "additionalProperties": False,
150:                     "properties": {"text": {"type": "string"}},
151:                     "required": ["text"],
152:                 },
153:             },
154:             "requested_outcomes": {
155:                 "type": "array",
156:                 "items": {
157:                     "type": "object",
158:                     "additionalProperties": False,
159:                     "properties": {"text": {"type": "string"}},
160:                     "required": ["text"],
161:                 },
162:             },
163:             "action_components": {
164:                 "type": "array",
165:                 "items": {
166:                     "type": "object",
167:                     "additionalProperties": False,
168:                     "properties": {
169:                         "order": {"type": "integer"},
170:                         "description": {"type": "string"},
171:                         "target_ref": {"anyOf": [{"type": "string"}, {"type": "null"}]},
172:                         "operation_class": {"enum": sorted(OPERATION_CLASSES)},
173:                     },
174:                     "required": ["order", "description", "target_ref", "operation_class"],
175:                 },
176:             },
177:             "references": {
178:                 "type": "object",
179:                 "additionalProperties": False,
180:                 "properties": {
181:                     "permitted_entity_ids": {"type": "array", "items": {"type": "string"}},
182:                     "unresolved_references": {"type": "array", "items": {"type": "string"}},
183:                 },
184:                 "required": ["permitted_entity_ids", "unresolved_references"],
185:             },
186:             "clarification_question": {"type": "string"},
187:             "correction": {
188:                 "type": "object",
189:                 "additionalProperties": False,
190:                 "properties": {
191:                     "subject": {"enum": sorted(CORRECTION_SUBJECTS)},
192:                     "note": {"type": "string"},
193:                 },
194:                 "required": ["subject", "note"],
195:             },
196:         },
197:         "required": sorted(MODEL_TOP_LEVEL),
198:         "not_model_writable": [
199:             "execution_eligibility",
200:             "execution_authorized",
201:             "canon_status",
202:             "adjudication_status",
```

## experiments/pr_do/adapter.py:119–131

```text
119:     if not isinstance(payload.get("clarification_question"), str):
120:         errors.append("clarification_question must be a string")
121:     correction = payload.get("correction")
122:     if not isinstance(correction, Mapping) or set(correction) != {"subject", "note"}:
123:         errors.append("correction must contain subject and note")
124:     elif correction.get("subject") not in CORRECTION_SUBJECTS or not isinstance(correction.get("note"), str):
125:         errors.append("correction subject is unknown or note is not a string")
126: 
127:     if status == "CLARIFICATION_REQUIRED":
128:         question = str(payload.get("clarification_question") or "").strip()
129:         unresolved_values = unresolved or []
130:         if not question and not unresolved_values:
131:             errors.append("clarification status requires a question or an unresolved reference")
```

## experiments/pr_do/eligibility.py:109–121

```text
109:     needs_clarification = (
110:         communication_mode == "CLARIFICATION"
111:         or interpretation_status == "CLARIFICATION_REQUIRED"
112:         or bool(unresolved_references)
113:         or bool(rejected)
114:         or any(entity_id not in permitted_ids for entity_id in targets)
115:     )
116:     if needs_clarification:
117:         return _base(
118:             disposition=NEEDS_CLARIFICATION,
119:             rejected_identifiers=rejected,
120:             reasons=["clarification_or_unresolved_reference"],
121:         )
```

## game/semantic_interpreter.py:127–141

```text
127: def player_visible_turns(log: Sequence[Mapping[str, Any]] | None, *, limit: int = 2) -> list[dict[str, str]]:
128:     """Last player-visible lines only. Resolution metadata stays out."""
129:     found: list[dict[str, str]] = []
130:     for entry in reversed(list(log or [])):
131:         if not isinstance(entry, Mapping):
132:             continue
133:         player = " ".join(str(entry.get("player_input") or "").split())[:240]
134:         gm = " ".join(str(entry.get("player_facing_text") or "").split())[:240]
135:         if not player and not gm:
136:             continue
137:         found.append({"player": player, "gm": gm})
138:         if len(found) >= limit:
139:             break
140:     found.reverse()
141:     return found
```

## game/conversational_orchestration.py:308–341

```text
308: def public_conversation_evidence(scene: Mapping[str, Any] | None, log: list | None) -> dict[str, str]:
309:     """Public summaries and previously emitted text only; no clue/NPC/private data."""
310:     evidence: dict[str, str] = {}
311:     summary = _visible_scene_summary(scene)
312:     if summary:
313:         evidence["scene"] = summary
314:     for index, fact in enumerate(_scene_obj(scene).get("visible_facts") or []):
315:         if isinstance(fact, str) and fact.strip():
316:             evidence[f"visible:{index}"] = fact.strip()
317:     for index, row in enumerate((log or [])[-4:]):
318:         if not isinstance(row, Mapping):
319:             continue
320:         gm = row.get("gm_output") or {}
321:         visible = row.get("player_facing_text") or (gm.get("player_facing_text") if isinstance(gm, Mapping) else "")
322:         if isinstance(visible, str) and visible.strip():
323:             evidence[f"reply:{index}"] = visible.strip()[:1200]
324:         resolution = row.get("resolution") or {}
325:         if isinstance(resolution, Mapping) and resolution.get("success") is True and resolution.get("kind") in {"investigate", "discover_clue"}:
326:             action_id = str(resolution.get("action_id") or "")
327:             if action_id and visible:
328:                 evidence[f"cause:reply:{index}"] = (
329:                     f"Your inspection of {action_id.replace('_', ' ')} revealed the detail. "
330:                     "That explains how you found it; its origin or purpose has not been established by that discovery."
331:                 )
332:         social = resolution.get("social") if isinstance(resolution, Mapping) else None
333:         if isinstance(social, Mapping) and social.get("target_resolved") and visible:
334:             # Latest spoken inability/refusal is conversation evidence too;
335:             # older revealed topics must not stand in for a newer reply.
336:             evidence["npc_latest_reply"] = str(visible).strip()[:1200]
337:         if isinstance(social, Mapping) and isinstance(social.get("topic_revealed"), Mapping):
338:             topic = social["topic_revealed"]
339:             if social.get("npc_id") and topic.get("id") and topic.get("text"):
340:                 evidence[f"npc:{social['npc_id']}:{topic['id']}"] = str(topic["text"])
341:     return evidence
```

## game/conversational_orchestration.py:394–459

```text
394:         return None
395:     ctx = _conversation_context(session)
396:     pending = ctx.get("pending_intention") if isinstance(ctx.get("pending_intention"), Mapping) else None
397:     if pending is None and isinstance(ctx.get("pending_clarification"), Mapping):
398:         pending = ctx.get("pending_clarification")
399:     # A correction label or conversational repair phrase is not action control.
400:     # Implicit revisions need both an intention referent and an action proposal;
401:     # explicit revision requests still reach the no-pending / executed guards.
402:     if not _REVISION_RE.search(text) and not (
403:         (purpose == "CORRECTION" or re.search(r"\b(?:i meant|change that)\b", text, re.I))
404:         and (isinstance(pending, Mapping) or isinstance(ctx.get("last_executed_intention"), Mapping))
405:         and any(
406:             isinstance(component, Mapping)
407:             and component.get("operation_class") in _CONNECTED_OPERATIONS | {"ATTACK", "USE_VISIBLE_OBJECT", "FOLLOW"}
408:             for component in components
409:         )
410:     ):
411:         return None
412:     scene_id = _scene_id(scene)
413:     if isinstance(pending, Mapping) and str(pending.get("status") or "pending") != "executed":
414:         if pending.get("scene_id") and scene_id and pending.get("scene_id") != scene_id:
415:             pending = None
416:         else:
417:             revised = dict(pending)
418:             revised["revised_text"] = text
419:             revised["status"] = "pending"
420:             return ConversationalDecision(
421:                 category=ConversationalDecisionCategory.CLARIFY,
422:                 primary_intention=text,
423:                 intent_family="clarification",
424:                 communication_owner="GM",
425:                 communication_purpose="CORRECTION",
426:                 reason="pending_intention_revised",
427:                 player_facing_text=(
428:                     "I've revised that unexecuted intention. It has not been attempted. "
429:                     + str(revised.get("clarification") or "Tell me who it is addressed to before I carry it out.")
430:                 ),
431:                 context_update=_context_update(pending=revised, pending_set=True, intention=revised, intention_set=True),
432:                 execution_policy="answer_only",
433:                 intent_modality="informational",
434:             )
435:     executed = ctx.get("last_executed_intention")
436:     if isinstance(executed, Mapping) and executed.get("status") == "executed":
437:         return ConversationalDecision(
438:             category=ConversationalDecisionCategory.ANSWER,
439:             primary_intention=text,
440:             intent_family="communication",
441:             communication_owner="GM",
442:             communication_purpose="CORRECTION",
443:             reason="executed_intention_not_reversible",
444:             player_facing_text="That action already resolved, so I cannot undo it. You can take a new action if you want.",
445:             execution_policy="answer_only",
446:             intent_modality="informational",
447:         )
448:     return ConversationalDecision(
449:         category=ConversationalDecisionCategory.CLARIFY,
450:         primary_intention=text,
451:         intent_family="clarification",
452:         communication_owner="GM",
453:         communication_purpose="CORRECTION",
454:         reason="no_pending_intention",
455:         player_facing_text="I don't have an unexecuted intention to revise. What do you want to change?",
456:         execution_policy="answer_only",
457:         intent_modality="informational",
458:     )
459: 
```

## game/conversational_orchestration.py:461–623

```text
461: def _communication_decision(record: Mapping[str, Any], text: str, *, session=None, scene=None, world=None) -> ConversationalDecision | None:
462:     communication = record.get("communication")
463:     if not isinstance(communication, Mapping):
464:         return None
465:     owner = str(communication.get("recipient") or "AMBIGUOUS")
466:     purpose = str(communication.get("purpose") or "CLARIFICATION")
467:     if record.get("communication_mode") == "RULES_QUESTION" and owner in {"GM", "SESSION"}:
468:         owner, purpose = "SESSION", "RULES"
469:     components = record.get("action_components") or []
470:     status = str(record.get("interpretation_status") or "")
471:     evidence_refs = list(communication.get("evidence_refs") or [])
472:     if status and status != "INTERPRETED":
473:         evidence = record.get("public_evidence") if isinstance(record.get("public_evidence"), Mapping) else {}
474:         selected = bool(evidence_refs) and all(ref in evidence for ref in evidence_refs)
475:         if not (selected and owner == "GM" and purpose in {"QUESTION", "DESCRIPTION", "EXPLANATION", "RECALL", "RULES"}):
476:             return None
477:     ask_targets = [
478:         str(component.get("target_ref") or "")
479:         for component in components
480:         if isinstance(component, Mapping) and component.get("operation_class") == "ASK" and component.get("target_ref")
481:     ]
482:     from game.ordinary_semantic_ownership import (
483:         assess_addressee_grounding,
484:         conversational_authorization_record,
485:         pending_addressee_clarification,
486:     )
487: 
488:     grounding = assess_addressee_grounding(
489:         text,
490:         scene=scene,
491:         world=world,
492:         session=session,
493:         proposed_target_id=ask_targets[0] if len(ask_targets) == 1 else None,
494:     )
495:     if grounding.get("direct_address") and grounding.get("operation_eligibility") == "requires_clarification":
496:         pending = pending_addressee_clarification(grounding, text, scene)
497:         return ConversationalDecision(
498:             category=ConversationalDecisionCategory.CLARIFY,
499:             primary_intention=text,
500:             intent_family="clarification",
501:             communication_owner="GM",
502:             communication_purpose="CLARIFICATION",
503:             reason="unresolved_addressee",
504:             player_facing_text=str(grounding.get("clarification") or "Which person do you mean? Nothing has been attempted."),
505:             context_update=_context_update(pending=pending, pending_set=True, intention=pending, intention_set=True),
506:             execution_policy="answer_only",
507:             intent_modality="informational",
508:             proposed_operation="ASK",
509:             proposed_target=ask_targets[0] if ask_targets else None,
510:             missing_information=["interlocutor"],
511:             authorization=conversational_authorization_record(
512:                 grounding,
513:                 player_text=text,
514:                 authority_provenance="communication_decision",
515:             ),
516:         )
517:     if purpose == "CONFIRMATION":
518:         # The semantic call identifies assent; the existing continuation owner
519:         # supplies and revalidates the actual pending operation.
520:         resumed = _resume_pending_clarification(player_text="Yes.", scene=scene, session=session)
521:         if resumed is not None:
522:             return resumed
523:     if purpose == "CORRECTION":
524:         pending = _conversation_context(session).get("pending_clarification") or {}
525:         if pending.get("kind") == "compound_sequence" and pending.get("scene_id") == _scene_id(scene) and len(components) == 1:
526:             component = components[0]
527:             operation = component.get("operation_class")
528:             if operation in _CONNECTED_OPERATIONS and component.get("target_ref"):
529:                 steps = [{"operation": operation, "target_id": component["target_ref"],
530:                           "text": component.get("description") or text, "supported": True},
531:                          *[dict(s) for s in pending.get("steps", [])[1:] if isinstance(s, Mapping)]]
532:                 revised = _compound_clarification(text, steps, scene=scene, world=world, clear=False, incidental=[])
533:                 return ConversationalDecision(**{**revised.__dict__, "communication_owner": "GM", "communication_purpose": purpose})
534:     if owner == "GM" and purpose in {"QUESTION", "DESCRIPTION", "EXPLANATION", "RECALL", "RULES"} and any(
535:         isinstance(c, Mapping) and (c.get("operation_class") in {"MOVE", "ATTACK", "USE_VISIBLE_OBJECT", "FOLLOW"}
536:                                     or (len(components) > 1 and c.get("operation_class") == "ASK" and c.get("target_ref")))
537:         for c in components
538:     ):
539:         owner = "MIXED"
540:     if owner in {"CHARACTER", "NPC"} and purpose in {"ACTION", "OBSERVATION", "QUESTION", "CLARIFICATION", "RECALL"} and record.get("action_components"):
541:         # A provider ASK does not turn a third-person question into NPC dialogue.
542:         ungrounded_gm_question = (
543:             any(isinstance(c, Mapping) and c.get("operation_class") == "ASK" for c in components)
544:             and grounding.get("operation_eligibility") != "executable"
545:             and _QUESTION_START_RE.search(text)
546:             and not re.search(r"\b(?:you|your|you're|youre)\b", text, re.IGNORECASE)
547:         )
548:         if ungrounded_gm_question:
549:             owner = "GM"
550:             if purpose not in {"EXPLANATION", "RECALL", "RULES", "DESCRIPTION"}:
551:                 purpose = "QUESTION"
552:         else:
553:             return None
554:     if owner == "GM" and purpose == "OBSERVATION" and components:
555:         if all(isinstance(c, Mapping) and c.get("operation_class") in {"PERCEIVE", "INSPECT"} for c in components):
556:             return None
557:     revision = _pending_revision_decision(text, session=session, scene=scene, purpose=purpose, components=components)
558:     if revision is not None:
559:         return revision
560:     category = ConversationalDecisionCategory.ANSWER
561:     update = None
562:     if purpose == "WITHDRAWAL":
563:         answer = "I've set aside the unexecuted intention. Anything already resolved still stands."
564:         update = _context_update(pending=None, pending_set=True, intention=None, intention_set=True, clear_interlocutor=False)
565:     elif owner == "MIXED":
566:         category = ConversationalDecisionCategory.CLARIFY
567:         answer = "Let's settle the question before attempting the action. "
568:         evidence = record.get("public_evidence") or {}
569:         answer += " ".join(str(v) for v in evidence.values()) if evidence else "That condition is not established yet."
570:         answer += " No part of the action has been attempted."
571:     elif purpose == "TENTATIVE":
572:         answer = "We can consider that before committing. Nothing has been attempted."
573:     elif owner == "AMBIGUOUS" or purpose == "CONFIRMATION" or (
574:         purpose == "CLARIFICATION" and (
575:             not record.get("public_evidence")
576:             or record.get("interpretation_status") != "INTERPRETED"
577:             or (record.get("references") or {}).get("unresolved_references")
578:         )
579:     ) or (owner == "CHARACTER" and not components):
580:         category = ConversationalDecisionCategory.CLARIFY
581:         answer = str(record.get("clarification_question") or "").strip() or "Which person, object, or pending action do you mean?"
582:     else:
583:         evidence = record.get("public_evidence") if isinstance(record.get("public_evidence"), Mapping) else {}
584:         if evidence_refs:
585:             evidence = {key: evidence[key] for key in evidence_refs if key in evidence}
586:         answer = " ".join(dict.fromkeys(str(value) for value in evidence.values()))
587:         if purpose == "EXPLANATION" and answer and _CAUSE_QUESTION_RE.search(text) and not any(str(ref).startswith("cause:") for ref in evidence):
588:             answer += " That establishes the observation or result; its cause has not been established."
589:         if not answer:
590:             from game.conversational_continuity import active_followup_target
591: 
592:             follow = active_followup_target(text, session=session, scene=scene, world=world)
593:             if follow:
594:                 record = _operation_record(
595:                     operation="ASK",
596:                     target_id=follow,
597:                     player_text=text,
598:                     summary=text,
599:                     references={"resolved_references": [{"text": "active interlocutor", "entity_id": follow}], "unresolved_references": []},
600:                 )
601:                 return ConversationalDecision(
602:                     category=ConversationalDecisionCategory.EXECUTE,
603:                     primary_intention=text,
604:                     intent_family="world_operation",
605:                     proposed_operation="ASK",
606:                     proposed_target=follow,
607:                     proposed_record=record,
608:                     requires_authoritative_execution=True,
609:                     reason="active_conversation_followup",
610:                     player_facing_text="",
611:                     execution_policy="",
612:                 )
613:             answer = "That has not been established in the information available to you."
614:             if purpose == "RULES" or owner == "SESSION":
615:                 answer = "I don't have an established ruling for that question. No action or roll has been made."
616:     return ConversationalDecision(
617:         category=category, primary_intention=text, intent_family="gm_communication" if owner == "GM" else "communication",
618:         communication_owner=owner, communication_purpose=purpose,
619:         reason="communication_before_execution", player_facing_text=answer,
620:         context_references=list((record.get("public_evidence") or {}).keys()),
621:         context_update=update, execution_policy="answer_only", intent_modality="informational",
622:         secondary_intentions=[dict(c) for c in components if isinstance(c, Mapping)] if owner == "MIXED" or category == ConversationalDecisionCategory.CLARIFY else [],
623:     )
```

## game/conversational_orchestration.py:2187–2219

```text
2187: def decision_from_interpretation_record(
2188:     record: Mapping[str, Any] | None,
2189:     *,
2190:     bridge_meta: Mapping[str, Any] | None = None,
2191:     player_text: str = "",
2192:     scene: Mapping[str, Any] | None = None,
2193:     world: Mapping[str, Any] | None = None,
2194:     session: Mapping[str, Any] | None = None,
2195: ) -> ConversationalDecision:
2196:     """Build a decision envelope from an existing interpretation/bridge result."""
2197:     text = _clean_text(player_text)
2198:     grounded = decision_from_delivered_exchange(
2199:         text, session=session, scene=scene, world=world,
2200:     )
2201:     if grounded is not None:
2202:         return grounded
2203:     if isinstance(record, Mapping):
2204:         record = _reclassify_direct_npc_address(record, text, scene=scene, world=world, session=session)
2205:     if not isinstance(record, Mapping):
2206:         reason = _clean_text((bridge_meta or {}).get("reason") if isinstance(bridge_meta, Mapping) else "") or "missing_record"
2207:         message, missing = _focused_bridge_clarification(reason)
2208:         return ConversationalDecision(
2209:             category=ConversationalDecisionCategory.CLARIFY,
2210:             primary_intention=text or "Unclear player intention.",
2211:             intent_family="clarification",
2212:             missing_information=missing,
2213:             reason=reason,
2214:             confidence=0.4,
2215:             player_facing_text=message,
2216:         )
2217:     communication_decision = _communication_decision(record, text, session=session, scene=scene, world=world)
2218:     if communication_decision is not None:
2219:         return communication_decision
```

## game/api.py:773–826

```text
773: def _nonmutating_conversational_decision_response(
774:     req: ChatRequest,
775:     mode_decision: _CommunicationModeDecision,
776:     decision: ConversationalDecision,
777:     *,
778:     live_outcome: dict | None = None,
779:     bridge_meta: dict | None = None,
780: ) -> dict:
781:     original_text = mode_decision.original_text or req.text or ""
782:     public_live = _public_live_interpretation(live_outcome) if isinstance(live_outcome, dict) else None
783:     decision_public = decision.to_public_dict()
784:     category = decision.category.value
785:     provider_requests = []
786:     if isinstance(public_live, dict):
787:         provider_requests = list(public_live.get("provider_requests") or [])
788:     gm = {
789:         "player_facing_text": decision.player_facing_text or "No gameplay action was taken.",
790:         "tags": ["conversational_orchestration", category.lower(), "non_mutating"],
791:         "scene_update": None,
792:         "activate_scene_id": None,
793:         "new_scene_draft": None,
794:         "world_updates": None,
795:         "suggested_action": None,
796:         "debug_notes": f"conversational_orchestration:{decision.reason}",
797:     }
798:     resolution = {
799:         "kind": f"conversational_{category.lower()}",
800:         "action_id": f"conversational_{category.lower()}",
801:         "label": original_text,
802:         "prompt": original_text,
803:         "success": None if decision.category != ConversationalDecisionCategory.DECLINE else False,
804:         "resolved_transition": False,
805:         "target_scene_id": None,
806:         "discovered_clues": [],
807:         "world_updates": None,
808:         "state_changes": {},
809:         "metadata": {
810:             "communication_mode": mode_decision.mode,
811:             "mode_source": mode_decision.source,
812:             "authoritative_mutation": False,
813:             "resolver_invoked": False,
814:             "gameplay_parser_invoked": False,
815:             "narration_invoked": False,
816:             "processing_outcome": f"conversational_{category.lower()}",
817:             "conversational_decision": decision_public,
818:             "live_chat_interpretation": public_live,
819:             "stored_interpretation_bridge": dict(bridge_meta or {}) if isinstance(bridge_meta, dict) else None,
820:             "provider_calls": {
821:                 "interpretation_requests": len(provider_requests),
822:                 "narration_requests": 0,
823:                 "ooc_assistance_requests": 0,
824:                 "retries": 0,
825:             },
826:             "performance": _performance_record(
```

## game/api.py:6514–6580

```text
6514:     if stored_interpretation is None and bridged_from_stored_interpretation is None and mode_decision.mode in {"AUTO", "IC"}:
6515:         live_outcome = interpret_production_turn(
6516:             player_text=req.text or "",
6517:             mode=mode_decision.mode,
6518:             scene=scene,
6519:             world=world,
6520:             log=recent_log,
6521:             session=session,
6522:         )
6523:         if live_outcome.get("status") == "blocked":
6524:             live_record = live_outcome.get("record") if isinstance(live_outcome.get("record"), dict) else None
6525:             if live_record is not None:
6526:                 decision = decision_from_interpretation_record(
6527:                     live_record,
6528:                     bridge_meta=live_outcome,
6529:                     player_text=req.text or "",
6530:                     scene=scene, world=world, session=session,
6531:                 )
6532:                 if decision.category == ConversationalDecisionCategory.EXECUTE:
6533:                     live_locked_action, stored_bridge_meta = normalized_action_from_interpretation(
6534:                         decision.proposed_record or live_record,
6535:                         scene=scene,
6536:                         world=world,
6537:                         player_text=req.text or "",
6538:                         known_scene_ids=list_scene_ids,
6539:                         session=session,
6540:                         authorized_target_id=_confirmed_addressee_target(decision),
6541:                     )
6542:                     if not (isinstance(stored_bridge_meta, dict) and stored_bridge_meta.get("accepted") is True):
6543:                         rejection = decision_from_bridge_rejection(
6544:                             bridge_meta=stored_bridge_meta or {},
6545:                             player_text=req.text or "",
6546:                             record=decision.proposed_record or live_record,
6547:                         )
6548:                         return _nonmutating_conversational_decision_response(
6549:                             req,
6550:                             mode_decision,
6551:                             rejection,
6552:                             live_outcome=live_outcome,
6553:                             bridge_meta=stored_bridge_meta,
6554:                         )
6555:                     bridged_from_stored_interpretation = live_locked_action
6556:                     execution_decision = decision
6557:                     live_outcome = {**live_outcome, "status": "accepted", "reason": "orchestration_execute", "bridge": stored_bridge_meta}
6558:                 else:
6559:                     return _nonmutating_conversational_decision_response(
6560:                         req,
6561:                         mode_decision,
6562:                         decision,
6563:                         live_outcome=live_outcome,
6564:                     )
6565:             if live_locked_action is None:
6566:                 return _live_interpretation_block_response(req, mode_decision, live_outcome)
6567:         if live_outcome.get("status") == "accepted":
6568:             decision = decision_from_interpretation_record(
6569:                 live_outcome.get("record") if isinstance(live_outcome.get("record"), dict) else None,
6570:                 bridge_meta=live_outcome,
6571:                 player_text=req.text or "",
6572:                 scene=scene, world=world, session=session,
6573:             )
6574:             if decision.category != ConversationalDecisionCategory.EXECUTE:
6575:                 return _nonmutating_conversational_decision_response(
6576:                     req,
6577:                     mode_decision,
6578:                     decision,
6579:                     live_outcome=live_outcome,
6580:                 )
```

## game/immutable_valid_response.py:1564–1590

```text
1564:         elif is_host_operation(line):
1565:             category = CATEGORY_HOST
1566:             validation = "host_operation"
1567:             if contains_protected_disclosure(line) or consequential_addition(line):
1568:                 _deny()
1569:         elif contains_protected_disclosure(line) or consequential_addition(line):
1570:             _deny()
1571:         else:
1572:             # Expression may reword an already selected host sentence. Protected
1573:             # and consequential additions are rejected above; this is not a
1574:             # source-less grant for a new topic.
1575:             category = CATEGORY_HOST
1576:             validation = "host_operation"
1577:     candidate = str(gm.get("player_facing_text") or "")
1578:     # A discarded draft cannot supply state effects alongside the host answer.
1579:     for key in ("scene_update", "world_updates", "activate_scene_id", "new_scene_draft", "suggested_action"):
1580:         gm[key] = None
1581:     gm.pop("improvisation_proposals", None)
1582:     gm.pop("bounded_improvisation_authority", None)
1583:     sealed = seal_accepted_response(
1584:         gm, text=line, provenance="authorized_host_speech", attempt=0,
1585:         validation={"hard_valid": True, "reasons": [], "soft_flags": [],
1586:                     "speaker": speaker_name, "addressee": "player",
1587:                     "operation": "ask", "interaction_complete": True,
1588:                     "contract_satisfying": True, "authority": [source]},
1589:         contract=_contract_from_resolution(resolution), player_text=player_text,
1590:         resolution=resolution,
```

## tests/test_atgb_r1_02_revision_boundary.py:106–125

```text
106:     session = {"active_scene_id": "frontier_gate", "conversational_context": {
107:         "last_gm_exchange": {"player_text": first["player_input"], "response_text": first["response_text"]}}}
108:     before = copy.deepcopy(session)
109:     decision = orchestration.decision_from_interpretation_record(
110:         raw_record(purpose=purpose), player_text=second["player_input"], session=session,
111:         scene={"scene": {"id": "frontier_gate"}},
112:     )
113:     assert decision.reason == "communication_before_execution"
114:     assert decision.player_facing_text == "That has not been established in the information available to you."
115:     assert decision.context_update is None
116:     assert session == before
117: 
118: 
119: def test_correction_preserves_selected_public_evidence():
120:     record = raw_record(purpose="CORRECTION", refs=["visible:people"])
121:     record["public_evidence"] = {"visible:people": "Two astronomers stand by the telescope."}
122:     decision = orchestration.decision_from_interpretation_record(record, player_text="I meant the people.")
123:     assert decision.player_facing_text == record["public_evidence"]["visible:people"]
124:     assert decision.reason == "communication_before_execution"
125: 
```

## tests/test_pr_ea_conversational_orchestration.py:41–47

```text
41: def test_pr_ea_deterministic_incomplete_movement_clarifies_without_context() -> None:
42:     decision = deterministic_conversational_decision(player_text="I leave.")
43: 
44:     assert decision is not None
45:     assert decision.category == ConversationalDecisionCategory.CLARIFY
46:     assert decision.missing_information == ["destination"]
47:     assert decision.player_facing_text == "Where are you trying to go?"
```

## tests/test_pr_ea_conversational_orchestration.py:115–137

```text
115: def test_pr_ea_live_missing_move_target_uses_focused_clarification(tmp_path, monkeypatch) -> None:
116:     _seed_pr_du_world(tmp_path, monkeypatch)
117:     _enable_live(monkeypatch)
118:     before = copy.deepcopy(storage.load_session())
119:     _install_interpretation(
120:         monkeypatch,
121:         _payload("IN_WORLD_ACTION", "INTERPRETED", [("MOVE", None)]),
122:         [],
123:     )
124:     monkeypatch.setattr(
125:         "game.api.call_gpt",
126:         lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
127:     )
128: 
129:     data = chat(ChatRequest(text="I head out.", ui_mode="player"))
130: 
131:     assert data["resolution"]["kind"] == "conversational_clarify"
132:     assert data["gm_output"]["player_facing_text"] == "Where are you trying to go?"
133:     after = storage.load_session()
134:     assert after["turn_counter"] == before["turn_counter"]
135:     assert after["clocks"] == before["clocks"]
136:     assert after["active_scene_id"] == before["active_scene_id"]
137:     assert after["conversational_context"]["pending_clarification"]["operation"] == "MOVE"
```

## tests/test_pr_eb_conversational_continuity.py:24–87

```text
24:     _seed_pr_du_world(tmp_path, monkeypatch)
25:     _activate_mara()
26:     monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)
27:     monkeypatch.setattr(
28:         "game.live_chat_interpretation.request_interpretation",
29:         lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("interpretation provider called")),
30:     )
31: 
32:     data = chat(ChatRequest(text="Which captain?", ui_mode="player"))
33: 
34:     assert data["ok"] is True
35:     assert data["resolution"]["kind"] == "question"
36:     assert data["resolution"]["social"]["npc_id"] == MARA_ID
37:     assert data["resolution"]["metadata"]["stored_interpretation"]["operation"] == "ASK"
38:     assert storage.load_session()["turn_counter"] == 1
39: 
40: 
41: def test_pr_eb_conversation_exit_clears_active_interlocutor_without_world_mutation(tmp_path, monkeypatch) -> None:
42:     _seed_pr_du_world(tmp_path, monkeypatch)
43:     _activate_mara()
44:     before_world = copy.deepcopy(storage.load_world())
45:     monkeypatch.setattr(
46:         "game.api.call_gpt",
47:         lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("narration provider called")),
48:     )
49: 
50:     data = chat(ChatRequest(text="That's enough for now.", ui_mode="player"))
51: 
52:     assert data["resolution"]["kind"] == "conversational_answer"
53:     session = storage.load_session()
54:     ctx = session["interaction_context"]
55:     assert ctx["active_interaction_target_id"] is None
56:     assert ctx["active_interaction_kind"] is None
57:     assert storage.load_world() == before_world
58: 
59: 
60: def test_pr_eb_ambiguous_pronoun_inspection_resumes_after_clarification(tmp_path, monkeypatch) -> None:
61:     _seed_pr_du_world(tmp_path, monkeypatch)
62:     scene = storage.load_active_scene()
63:     scene["scene"]["interactables"].append(
64:         {
65:             "id": "courtyard-shield",
66:             "label": "weathered shield",
67:             "aliases": ["shield"],
68:             "reveals_clue": "Old paint marks the shield.",
69:         }
70:     )
71:     storage.save_scene(scene)
72:     monkeypatch.setattr("game.api.call_gpt", _fake_gm_for_resolution)
73: 
74:     clarify = chat(ChatRequest(text="I examine it.", ui_mode="player"))
75: 
76:     assert clarify["resolution"]["kind"] == "conversational_clarify"
77:     assert "lantern" in clarify["gm_output"]["player_facing_text"].lower()
78:     assert "weathered shield" in clarify["gm_output"]["player_facing_text"].lower()
79:     pending = storage.load_session()["conversational_context"]["pending_clarification"]
80:     assert pending["operation"] == "INSPECT"
81: 
82:     resolved = chat(ChatRequest(text="the lantern", ui_mode="player"))
83: 
84:     assert resolved["ok"] is True
85:     assert resolved["resolution"]["kind"] in {"investigate", "observe"}
86:     assert resolved["resolution"]["action_id"] == LANTERN_ID
87:     assert storage.load_session()["conversational_context"]["pending_clarification"] is None
```

## experiments/pr_do/fixtures.py:102–123

```text
102:             ),
103:         },
104:         {
105:             "case_id": "DN04",
106:             "permitted_ids": list(GATE),
107:             "utterance": "OOC: I meant the left guard, not the captain.",
108:             "engine_channel": "OUT_OF_CHARACTER_CORRECTION",
109:             "assumptions": [
110:                 "The leading OOC prefix is an engine channel marker.",
111:                 "The correction subject is REFERENT. Left guard is unresolved because it is not a permitted id.",
112:             ],
113:             "payload": _payload(
114:                 mode="OUT_OF_CHARACTER_CORRECTION",
115:                 status="CLARIFICATION_REQUIRED",
116:                 summary="OOC correction of a previous referent from the captain to the left guard.",
117:                 unresolved=["left guard"],
118:                 question="Left guard is not a visible entity. Which prior reference should be corrected?",
119:                 correction_subject="REFERENT",
120:                 correction_note="Referent correction. No in-world action is issued.",
121:             ),
122:         },
123:         {
```
