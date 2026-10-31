# Current-source excerpts

One-based current working-tree lines; static reconstruction, not original historical instruction-pointer trace.

## game/interaction_completion.py (SHA-256 39d63fa6069354c817d45952a80f6e56c258b412f5c4d742d37ab7bd749d57f7)

```text
82: _MEAN_RE = re.compile(
83:     r"\bi mean\s+(?:the\s+|a\s+|an\s+)?(?P<nominal>[a-z][^?.!,]{0,40})",
84:     re.IGNORECASE,
85: )
86: _VOCATIVE_RE = re.compile(
87:     r"^(?P<nominal>[A-Za-z]+(?:\s+[A-Za-z]+){0,2})\s*[,:]"
88: )
89: _NOT_A_VOCATIVE = frozenset({
90:     "instead", "actually", "well", "so", "then", "please", "wait", "now",
91:     "yes", "no", "okay", "ok", "never", "rather", "anyway", "still",
92: })
93: _INTERJECTION_RE = re.compile(
94:     r"^(?:fine|okay|ok|alright|all right|well|yes|no|hey|oh|ah|hmm|right|sure|wait|now|then)$",
95:     re.IGNORECASE,
96: )
97: _REJECT_RE = re.compile(
98:     r"\b(?:not asking|stop talking to|turn away from|step back from|done with|"
99:     r"leave|leaving|ignore|ignoring|forget)\s+"
100:     r"(?P<nominal>(?:the\s+|a\s+|an\s+)?[a-z][^?.!]{0,48})",
101:     re.IGNORECASE,
102: )
103: _REJECT_PRONOUN_RE = re.compile(
104:     r"\b(?:not asking|done with|leave|ignore|forget)\s+(?:him|her|them)\b"
105:     r"|\b(?:i am|i'm) not asking him\b",
106:     re.IGNORECASE,
```

```text
492: def _nominal_chunk(raw: str) -> str:
493:     chunk = re.split(r",|\b(?:not|and|who|which|holding)\b", raw, maxsplit=1, flags=re.IGNORECASE)[0]
494:     return _clean(chunk).strip(" \"'")
495: 
496: 
497: def _complement_cut(raw: str) -> str:
498:     """Keep a relative clause. Drop the question that follows the address."""
499:     return _clean(_COMPLEMENT_RE.split(str(raw or ""), maxsplit=1)[0]).strip(" \"'")
```

```text
627: def addressed_person_nominal(text: str | None) -> str:
628:     """Nominal of a direct address, or empty when the utterance does not address anyone.
629: 
630:     Question complements are cut off. A mention of a person inside a GM question
631:     is not an address. ``tell`` and ``warn`` are included here because the
632:     existing address pattern does not own those verbs.
633:     """
634:     raw = _clean(text)
635:     if not raw:
636:         return ""
637:     for pattern in (_VOCATIVE_RE, _SPEECH_ADDRESS_RE, _TELL_RE):
638:         for match in pattern.finditer(raw):
639:             span = _complement_cut(match.group("nominal") or "")
640:             nominal = _nominal_chunk(span)
641:             if not nominal or _QUESTION_NOMINAL_RE.match(nominal) or _INTERJECTION_RE.match(nominal):
642:                 continue
643:             if pattern is _VOCATIVE_RE and nominal.casefold() in _NOT_A_VOCATIVE:
644:                 continue
645:             return nominal
646:     return ""
647: 
648: 
649: def explicit_discourse_binding(
650:     text: str | None,
```

## game/ordinary_semantic_ownership.py (SHA-256 273fba46a2b39d5ae9f5343280c2ce3ed2b85f82c1273334de3feef890aba75b)

```text
526: _SINGULAR_PRONOUNS = frozenset({"him", "her", "he", "she"})
527: _PLURAL_PRONOUNS = frozenset({"them", "they", "those"})
528: _DETERMINERS = frozenset({"the", "a", "an", "that", "this"})
```

```text
615: def _active_npc_id(session: Mapping[str, Any] | None, npcs: list[Mapping[str, Any]]) -> str:
616:     if not isinstance(session, Mapping):
617:         return ""
618:     ctx = session.get("interaction_context")
619:     if not isinstance(ctx, Mapping):
620:         return ""
621:     if str(ctx.get("active_interaction_kind") or "").lower() != "social":
622:         return ""
623:     target = str(ctx.get("active_interaction_target_id") or "")
624:     ids = {str(npc.get("id") or "") for npc in npcs}
625:     return target if target in ids else ""
626: 
627: 
```

```text
643: def assess_addressee_grounding(
644:     player_text: str,
645:     *,
646:     scene: Mapping[str, Any] | None = None,
647:     world: Mapping[str, Any] | None = None,
648:     session: Mapping[str, Any] | None = None,
649:     proposed_target_id: str | None = None,
650: ) -> dict[str, Any]:
651:     """Decide whether a person reference is grounded enough to attempt.
652: 
653:     A provider id is a candidate. It authorizes nothing by itself. Explicit
654:     names and unique contextual referents resolve. Quantified or unmatched
655:     references stay unresolved even when one visible person would be convenient.
656:     """
657:     from game.interaction_completion import addressed_person_nominal
658: 
659:     text = " ".join(str(player_text or "").split())
660:     npcs = _visible_npcs(scene, world)
661:     proposed = str(proposed_target_id or "").strip() or None
662:     nominal = addressed_person_nominal(text)
663:     direct = bool(nominal) or bool(_ASK_VERB_RE.search(text) and nominal)
664:     words = _content_words(nominal)
665:     base = {
666:         "communication_ownership": "npc_directed" if direct else "gm_directed",
667:         "intent_purpose": "address_npc" if direct else "request_information",
668:         "target_resolution": "none_required",
669:         "target_provenance": "none",
670:         "target_id": None,
671:         "candidate_target_ids": [proposed] if proposed else [],
672:         "operation_eligibility": "not_assessed",
673:         "mutation_eligibility": True,
674:         "conflict_status": "none",
675:         "conflict_details": {},
676:         "pending_intention_relationship": "none",
677:         "allowed_operation": None,
678:         "clarification": "",
679:         "choices": [_choice(npc) for npc in npcs],
680:         "direct_address": bool(nominal),
681:     }
682:     if not npcs or not nominal:
683:         if nominal and not npcs:
684:             return base
685:         third_person_about_npc = bool(_THIRD_PERSON_RE.search(text)) and not _SECOND_PERSON_RE.search(text)
686:         if not nominal and proposed and _active_npc_id(session, npcs) == proposed and not third_person_about_npc:
687:             return {
688:                 **base,
689:                 "communication_ownership": "npc_directed",
690:                 "intent_purpose": "address_npc",
691:                 "target_resolution": "contextual",
692:                 "target_provenance": "established_interlocutor",
693:                 "target_id": proposed,
694:                 "operation_eligibility": "executable",
695:                 "mutation_eligibility": True,
696:                 "allowed_operation": "ask",
697:                 "pending_intention_relationship": "continues",
698:                 "direct_address": False,
699:             }
```

```text
726: 
727:     nonunique = bool(_NONUNIQUE_ADDRESSEE_RE.search(nominal)) or bool(
728:         re.search(r"\b(?:either|any|another)\s+(?!of\b)", nominal, re.IGNORECASE)
729:     )
730:     if any(word in _PLURAL_PRONOUNS for word in words) or nonunique or _NONUNIQUE_ADDRESSEE_RE.search(nominal):
731:         return {
732:             **base,
733:             "direct_address": True,
734:             "communication_ownership": "ambiguous_unresolved",
735:             "target_resolution": "ambiguous",
736:             "target_provenance": "provider_candidate_only" if proposed else "none",
737:             "operation_eligibility": "requires_clarification",
738:             "mutation_eligibility": False,
739:             "allowed_operation": None,
740:             "pending_intention_relationship": "requires_clarification",
741:             "clarification": _clarification_for(npcs, single_offer=len(npcs) == 1),
742:             "conflict_status": "unresolved" if proposed else "none",
743:             "conflict_details": {"provider_target": proposed} if proposed else {},
744:         }
745: 
746:     if len(words) == 1 and words[0] in _SINGULAR_PRONOUNS:
747:         active = _active_npc_id(session, npcs)
748:         chosen = ""
749:         provenance = ""
750:         if active and (not proposed or proposed == active):
751:             chosen, provenance = active, "established_interlocutor"
752:         elif len(npcs) == 1 and (not proposed or proposed == str(npcs[0].get("id") or "")):
753:             chosen, provenance = str(npcs[0].get("id") or ""), "unique_contextual"
754:         elif active and proposed and proposed != active:
755:             return {
756:                 **base,
757:                 "direct_address": True,
758:                 "communication_ownership": "ambiguous_unresolved",
759:                 "target_resolution": "ambiguous",
760:                 "target_provenance": "provider_candidate_only",
761:                 "operation_eligibility": "requires_clarification",
762:                 "mutation_eligibility": False,
763:                 "clarification": _clarification_for(npcs, single_offer=False),
764:                 "conflict_status": "unresolved",
765:                 "conflict_details": {"established_interlocutor": active, "provider_target": proposed},
766:                 "pending_intention_relationship": "requires_clarification",
767:             }
768:         elif len(npcs) != 1:
769:             return {
770:                 **base,
771:                 "direct_address": True,
772:                 "communication_ownership": "ambiguous_unresolved",
773:                 "target_resolution": "ambiguous",
774:                 "target_provenance": "none",
775:                 "operation_eligibility": "requires_clarification",
776:                 "mutation_eligibility": False,
777:                 "clarification": _clarification_for(npcs, single_offer=False),
778:                 "pending_intention_relationship": "requires_clarification",
779:                 "conflict_status": "unresolved" if proposed else "none",
780:             }
781:         if chosen:
782:             return {
783:                 **base,
784:                 "direct_address": True,
785:                 "communication_ownership": "npc_directed",
786:                 "target_resolution": "contextual",
787:                 "target_provenance": provenance,
788:                 "target_id": chosen,
789:                 "operation_eligibility": "executable",
790:                 "mutation_eligibility": True,
791:                 "allowed_operation": "ask",
792:                 "pending_intention_relationship": "continues" if provenance == "established_interlocutor" else "starts_new",
793:             }
794: 
795:     hits = [npc for npc in npcs if set(words) & _npc_words(npc)]
796:     extras = [word for word in words if not any(word in _npc_words(npc) for npc in hits)]
797:     ambiguous_extras = False
798:     else_provenance = ""
799:     if len(hits) > 1 and extras:
800:         narrowed = [npc for npc in hits if all(extra in _npc_public_blob(npc, scene) for extra in extras)]
801:         if len(narrowed) == 1:
802:             hits = narrowed
```

```text
839:             "choices": [_choice(npc) for npc in (hits or npcs)],
840:             "pending_intention_relationship": "requires_clarification",
841:             "conflict_status": "unresolved" if proposed else "none",
842:         }
843:     return {
844:         **base,
845:         "direct_address": True,
846:         "communication_ownership": "ambiguous_unresolved",
847:         "target_resolution": "unresolved",
848:         "target_provenance": "provider_candidate_only" if proposed else "none",
849:         "operation_eligibility": "requires_clarification",
850:         "mutation_eligibility": False,
851:         "clarification": _clarification_for(npcs, single_offer=len(npcs) == 1),
852:         "pending_intention_relationship": "requires_clarification",
853:         "conflict_status": "unresolved" if proposed else "none",
854:     }
```

## game/conversational_orchestration.py (SHA-256 d3b4f1a077bfb0dbd6454ad61a899fdfc3cbc32e987a051832498b6c92517e9c)

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
342: 
343: 
344: def _reclassify_direct_npc_address(
345:     record: Mapping[str, Any],
```

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
```

```text
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
587:         # Receipt only for a resolved conversational correction with a grounded
588:         # answer. Mechanical revisions returned above; no semantic reclassification.
589:         if (answer and owner == "GM" and purpose == "CORRECTION"
590:                 and status == "INTERPRETED" and not components
591:                 and not (record.get("references") or {}).get("unresolved_references")
592:                 and (record.get("correction") or {}).get("subject") == "REFERENT"
593:                 and evidence_refs and all(ref in evidence for ref in evidence_refs)):
594:             answer = "Understood. " + answer
595:         if purpose == "EXPLANATION" and answer and _CAUSE_QUESTION_RE.search(text) and not any(str(ref).startswith("cause:") for ref in evidence):
596:             answer += " That establishes the observation or result; its cause has not been established."
597:         if not answer:
598:             from game.conversational_continuity import active_followup_target
599: 
600:             follow = active_followup_target(text, session=session, scene=scene, world=world)
601:             if follow:
602:                 record = _operation_record(
603:                     operation="ASK",
604:                     target_id=follow,
605:                     player_text=text,
606:                     summary=text,
607:                     references={"resolved_references": [{"text": "active interlocutor", "entity_id": follow}], "unresolved_references": []},
608:                 )
609:                 return ConversationalDecision(
610:                     category=ConversationalDecisionCategory.EXECUTE,
611:                     primary_intention=text,
612:                     intent_family="world_operation",
613:                     proposed_operation="ASK",
614:                     proposed_target=follow,
615:                     proposed_record=record,
616:                     requires_authoritative_execution=True,
617:                     reason="active_conversation_followup",
618:                     player_facing_text="",
619:                     execution_policy="",
620:                 )
621:             answer = "That has not been established in the information available to you."
622:             if purpose == "RULES" or owner == "SESSION":
623:                 answer = "I don't have an established ruling for that question. No action or roll has been made."
624:     return ConversationalDecision(
625:         category=category, primary_intention=text, intent_family="gm_communication" if owner == "GM" else "communication",
626:         communication_owner=owner, communication_purpose=purpose,
627:         reason="communication_before_execution", player_facing_text=answer,
628:         context_references=list((record.get("public_evidence") or {}).keys()),
629:         context_update=update, execution_policy="answer_only", intent_modality="informational",
630:         secondary_intentions=[dict(c) for c in components if isinstance(c, Mapping)] if owner == "MIXED" or category == ConversationalDecisionCategory.CLARIFY else [],
```

## game/live_chat_interpretation.py (SHA-256 ea88d3317df13001ca328487eaf94a26a8e29246e09c893f55f6d460832f2eba)

```text
323:     # Specialize the legacy mode guidance on the production request only.
324:     messages[1]["content"] = "\n".join(
325:         "Communication modes: IN_WORLD_ACTION=character action or NPC speech; "
326:         "OUT_OF_CHARACTER_CORRECTION=explicit out-of-character correction; "
327:         "RULES_QUESTION=play procedure; CLARIFICATION=the AI-DM needs additional information; "
328:         "OTHER for resolved GM conversation, including ordinary conversational correction."
329:         if line.startswith("Communication modes:") else line
330:         for line in messages[1]["content"].splitlines()
331:     )
332:     from game.conversational_orchestration import public_conversation_evidence
333:     evidence = public_conversation_evidence(scene, log)
334:     messages[0]["content"] += (
335:         " Establish communication.recipient and purpose BEFORE describing operations. "
336:         "GM is the facilitator, never an NPC. Questions about perception, possibility, prior narration, "
337:         "third-person NPC appearance, or what an NPC meant address GM; speaking TO an NPC uses NPC. "
338:         "A short question continuing an active NPC exchange may address NPC; explicit GM address overrides it. "
339:         "SESSION owns rules and interface questions. CHARACTER owns committed attempts only. "
340:         "MIXED owns question plus conditional or independent action; preserve all components, never authorize them. "
341:         "CORRECTION and WITHDRAWAL never undo committed facts. TENTATIVE and capability questions never commit actions. "
342:         "For GM/session communication leave action_components empty unless a NEW observation is requested; "
343:         "use existing PERCEIVE/INSPECT for that. Meaningful communication can be INTERPRETED with zero operations. "
344:         "Ordinary conversational correction supplies corrected meaning, subject, referent or description. "
345:         "Distinguish the player clarifying their own meaning from the AI-DM requesting clarification. "
346:         "When that meaning is established, use INTERPRETED, GM/CORRECTION and legacy OTHER; "
347:         "continue the corrected conversation without asking confirmation merely because it is corrective. "
348:         "Use correction.subject REFERENT for a conversational subject, referent or description correction. "
349:         "This does not itself revise a gameplay action; leave action_components empty. "
350:         "Mechanical revision modifies an actual eligible pending intention and remains subject to host checks; "
351:         "never invent pending work, revise executed actions or execute from a correction alone. "
352:         "Recover the underlying question or request from available conversation context using the corrected meaning. "
353:         "Select relevant authorized PUBLIC evidence_refs that support answering that corrected question; "
354:         "prefer a supported answer over redundant clarification. Subject describes the question, never a new fact. "
355:         "Restricted or unestablished information in internal world state is not disclosure authority; "
356:         "do not select it or infer unsupported facts. Select only supplied PUBLIC passages that support the answer. "
357:         "With insufficient evidence, state the limitation or continue with established information only. "
358:         "Ask a targeted question when meaningful ambiguity remains (such as competing people, a missing "
359:         "interlocutor or action parameter, or conflicting intentions); never guess to avoid clarification. "
360:         "Acknowledgments asserting no world facts may use empty evidence_refs. "
361:         "Do not convert GM communication into SOCIAL_SIGNAL, ASK or an unsupported operation."
362:         " A declaration of what I/we do is CHARACTER/ACTION, including inspection; "
```

```text
490:                 {**payload, "communication": communication}, player_text,
491:                 scene=scene, world=world, session=session)
492:             communication = prepared.get("communication", communication)
493:             payload = {key: prepared[key] for key in payload}
494:         adapted = adapt_interpretation(payload, permitted_ids=[entity_id for entity_id, _label, _kind in catalog])
495:     record = adapted.get("record") if isinstance(adapted.get("record"), dict) else None
496:     if record is not None and communication is not None:
497:         record["communication"] = communication
498:         record["incidental_context"] = incidental
499:         record["reference_reconciliation"] = reconciliation
500:         # Only passages selected from the engine's public projection can reach emission.
501:         record["public_evidence"] = {ref: evidence[ref] for ref in communication["evidence_refs"]}
502:     eligibility = adapted.get("eligibility") if isinstance(adapted.get("eligibility"), dict) else {}
503:     disposition = str(eligibility.get("disposition") or "")
504:     common = {
505:         "raw_interpretation": raw,
```
