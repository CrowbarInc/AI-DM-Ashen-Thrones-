# Current source evidence (numbered, read only)

### game/api.py:2466-2540

```text
2466: def _apply_authoritative_resolution_state_mutation(
2467:     *,
2468:     session: dict,
2469:     world: dict,
2470:     combat: dict,
2471:     scene: dict,
2472:     resolution: dict,
2473:     normalized_action: dict | None,
2474: ) -> tuple[dict, dict, dict, list[str], dict]:
2475:     """Stage 5: apply deterministic state mutation from resolved engine output."""
2476:     assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="authoritative_resolution_mutation")
2477:     assert_owner_can_mutate_domain(__name__, SCENE_STATE, operation="authoritative_resolution_mutation")
2478:     assert_canon_immutable(scene)
2479:     authoritative_clue_updates: list[str] = []
2480: 
2481:     merged_res = normalize_runtime_engine_result(resolution)
2482:     resolution.clear()
2483:     resolution.update(merged_res)
2484: 
2485:     wu = resolution.get('world_updates')
2486:     if isinstance(wu, dict) and wu:
2487:         if resolution_world_updates_use_engine_apply_only(wu):
2488:             apply_resolution_world_updates(world, wu)
2489:         else:
2490:             normalized_wu = normalize_runtime_world_updates(wu)
2491:             scene_id = str(scene.get('scene', {}).get('id') or '').strip() or None
2492:             apply_normalized_world_updates(world, normalized_wu, session=session, scene_id=scene_id)
2493:         save_world(world)
2494: 
2495:     originating_scene_id = str(scene['scene']['id'] or '').strip()
2496:     if resolution.get('resolved_transition') and resolution.get('target_scene_id'):
2497:         target_scene_id = str(resolution['target_scene_id'] or '').strip()
2498:         resolution['originating_scene_id'] = originating_scene_id
2499:         # Authoritative same-scene transition: suppress reload/re-entry; skip follow-lead hook.
2500:         if originating_scene_id and target_scene_id and originating_scene_id == target_scene_id:
2501:             resolution['same_scene_transition_suppressed'] = True
2502:             resolution['transition_applied'] = False
2503:             resolution['resolved_transition'] = False
2504:             resolution['target_scene_id'] = None
2505:             sc = resolution.get('state_changes')
2506:             if isinstance(sc, dict):
2507:                 for k in (
2508:                     'scene_changed',
2509:                     'scene_transition_occurred',
2510:                     'arrived_at_scene',
2511:                     'new_scene_context_available',
2512:                 ):
2513:                     sc.pop(k, None)
2514:                 resolution['state_changes'] = sc
2515:         else:
2516:             print("[ENGINE] Scene transition ->", target_scene_id)
2517:             scene, session, combat = _apply_authoritative_scene_transition(target_scene_id, scene, session, combat, world)
2518:             apply_follow_lead_commitment_after_resolved_scene_transition(
2519:                 session,
2520:                 resolution,
2521:                 normalized_action,
2522:                 target_scene_id=target_scene_id,
2523:             )
2524:             maybe_finalize_pursued_lead_destination_payoff_after_scene_transition(
2525:                 session,
2526:                 resolution,
2527:                 normalized_action,
2528:                 target_scene_id=target_scene_id,
2529:             )
2530: 
2531:     res_kind = str(resolution.get("kind") or "").strip().lower()
2532:     if res_kind in SOCIAL_KINDS:
2533:         # Canonical first landing for socially revealed clues/leads (clue_knowledge, runtime, pending_leads, event_log).
2534:         authoritative_clue_updates.extend(
2535:             apply_socially_revealed_leads(
2536:                 session, scene["scene"]["id"], world, resolution, scene=scene
2537:             )
2538:         )
2539:         apply_social_lead_discussion_tracking(
2540:             session=session,
```

### game/api.py:2800-2868

```text
2800: def _scene_opening_curated_facts_from_prompt_payload(prompt_payload: dict | None) -> tuple[list[str], str, list[str]]:
2801:     if not isinstance(prompt_payload, dict):
2802:         return [], "none", []
2803:     selector_facts = _dedupe_clean_string_list(prompt_payload.get("opening_selector_selected_facts"))
2804:     raw = selector_facts if selector_facts else prompt_payload.get("opening_curated_facts")
2805:     if not isinstance(raw, list):
2806:         opening_realization = prompt_payload.get("opening_scene_realization")
2807:         contract = (
2808:             opening_realization.get("contract")
2809:             if isinstance(opening_realization, dict) and isinstance(opening_realization.get("contract"), dict)
2810:             else {}
2811:         )
2812:         raw = contract.get("narration_basis_visible_facts")
2813:     facts = _dedupe_clean_string_list(raw)
2814:     telemetry = prompt_payload.get("opening_fact_telemetry")
2815:     source = ""
2816:     if isinstance(telemetry, dict):
2817:         source = str(telemetry.get("opening_fact_source_used") or "").strip()
2818:     if not source:
2819:         source = str(prompt_payload.get("opening_selector_source_used") or "").strip()
2820:     if not source:
2821:         source = "selector" if selector_facts else "realization"
2822:     return facts, source, selector_facts or facts
2823: 
2824: 
2825: def _attach_scene_opening_curated_facts_to_gm(
2826:     gm: dict | None,
2827:     *,
2828:     prompt_payload: dict | None,
2829:     resolution: dict | None,
2830: ) -> None:
2831:     if not isinstance(gm, dict) or not isinstance(resolution, dict):
2832:         return
2833:     if str(resolution.get("kind") or "").strip() != "scene_opening":
2834:         return
2835:     opening_basis_facts, source, selector_facts = _scene_opening_curated_facts_from_prompt_payload(prompt_payload)
2836:     gm["opening_curated_facts"] = opening_basis_facts
2837:     gm["opening_selector_selected_facts"] = list(selector_facts)
2838:     md = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
2839:     gm["metadata"] = md
2840:     if isinstance(md, dict):
2841:         em = md.setdefault("emission_debug", {})
2842:         if isinstance(em, dict):
2843:             em["opening_curated_facts_present"] = bool(opening_basis_facts)
2844:             em["opening_curated_facts_count"] = len(opening_basis_facts)
2845:             em["opening_curated_facts_source"] = "selector"
2846:             em["opening_selector_source_used"] = source
2847:             em["opening_selector_selected_facts"] = list(selector_facts)
2848:             em["opening_curated_facts"] = list(opening_basis_facts)
2849:     assert "opening_curated_facts" in gm
2850: 
2851: 
2852: def _classify_planner_convergence_path_label_for_manual_play(
2853:     *,
2854:     resolution: dict,
2855:     response_type_contract: dict,
2856:     route_choice: str | None,
2857: ) -> str:
2858:     rk = str(resolution.get("kind") or "").strip().lower()
2859:     sc = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
2860:     transitionish = bool(
2861:         resolution.get("resolved_transition") is True
2862:         or rk in ("travel", "scene_transition")
2863:         or sc.get("scene_transition_occurred")
2864:         or sc.get("arrived_at_scene")
2865:         or sc.get("new_scene_context_available")
2866:     )
2867:     if rk == "scene_opening":
2868:         return "scene_opening"
```

### game/api.py:3161-3250

```text
3161: def _build_gpt_narration_from_authoritative_state(
3162:     *,
3163:     campaign: dict,
3164:     world: dict,
3165:     session: dict,
3166:     character: dict,
3167:     scene: dict,
3168:     combat: dict,
3169:     recent_log: list,
3170:     user_text: str,
3171:     resolution: dict | None,
3172:     scene_runtime: dict,
3173:     segmented_turn: dict | None = None,
3174:     route_choice: str | None = None,
3175:     directed_social_entry: dict | None = None,
3176:     response_type_contract: dict | None = None,
3177:     latency_sink: dict | None = None,
3178:     normalized_action: dict | None = None,
3179: ) -> dict:
3180:     """Stages 6-7: build prompt context from authoritative state, then narrate with GPT.
3181: 
3182:     **CTIR seam:** Mutation and stale detach already ran in :func:`_run_resolved_turn_pipeline`. Here,
3183:     resolution-facing hygiene (e.g. topic probe registration, social escalation on ``resolution``) runs
3184:     before ``ensure_ctir_for_turn`` snapshots CTIR for this stamp. The narration plan bundle is then
3185:     ensured for the same stamp via :mod:`game.narration_plan_bundle` (CTIR → plan → session attachment).
3186:     :mod:`game.prompt_context` / :func:`game.gm.build_messages` **render** that bundle for the model;
3187:     they do not rebuild alternate plan semantics for the same stamp. Targeted retries keep the same
3188:     stamp so CTIR and the bundle are reused. If ``resolution`` is not a dict, CTIR is detached and not
3189:     rebuilt for this path (no mandatory plan bundle).
3190:     """
3191:     register_topic_probe(
3192:         session=session,
3193:         scene_envelope=scene,
3194:         player_text=user_text,
3195:         resolution=resolution if isinstance(resolution, dict) else None,
3196:         recent_log=recent_log,
3197:     )
3198:     if isinstance(resolution, dict):
3199:         apply_social_topic_escalation_to_resolution(
3200:             world=world,
3201:             session=session,
3202:             scene=scene,
3203:             user_text=user_text,
3204:             resolution=resolution,
3205:             recent_log=recent_log,
3206:         )
3207:     else:
3208:         # No authoritative resolution dict: drop any stale CTIR; prompt_context will use caller fallbacks.
3209:         detach_ctir(session)
3210:     _nc_kw: dict | None = None
3211:     _seam_stamp_for_retry = ""
3212:     bundle_seam_requirement: dict[str, Any] = {"ok": True, "skipped": "not_applicable"}
3213:     contract_payload: dict | None = None
3214:     planner_convergence_emergency_exit = False
3215:     planner_path_label = "continuation"
3216:     planner_convergence_report_final: dict[str, Any] | None = None
3217:     gm: dict | None = None
3218:     if isinstance(resolution, dict):
3219:         _ctir_stamp = narration_ctir_turn_stamp(session=session, resolution=resolution, user_text=user_text)
3220:         _scene_id_for_ctir = str((scene.get("scene") or {}).get("id") or "").strip() or None
3221:         # Single build per stamp; retries inside this function reuse the attached object (see ctir_runtime).
3222:         ensure_ctir_for_turn(
3223:             session,
3224:             turn_stamp=_ctir_stamp,
3225:             builder=lambda: build_runtime_ctir_for_narration(
3226:                 turn_id=session.get("turn_counter"),
3227:                 scene_id=_scene_id_for_ctir,
3228:                 player_input=user_text,
3229:                 builder_source="game.api._build_gpt_narration_from_authoritative_state",
3230:                 resolution=resolution,
3231:                 normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
3232:                 combat=combat if isinstance(combat, dict) else None,
3233:                 session=session if isinstance(session, dict) else None,
3234:                 world=world if isinstance(world, dict) else None,
3235:             ),
3236:         )
3237:         _nc_kw = collect_narration_context_call_kwargs(
3238:             campaign,
3239:             world,
3240:             session,
3241:             character,
3242:             scene,
3243:             combat,
3244:             recent_log,
3245:             user_text,
3246:             resolution=resolution,
3247:             scene_runtime=scene_runtime,
3248:             prompt_profile="manual_play_auto",
3249:         )
3250:         _nc_kw.pop("known_answer_hint", None)
```

### game/api.py:3497-3569

```text
3497:                 if isinstance(dbg, dict):
3498:                     dbg["pre_retry_speaker_repair"] = payload
3499:         return gm_dict
3500: 
3501:     def _attach_bounded_improvisation_authority(gm_dict: dict | None) -> dict | None:
3502:         if not isinstance(gm_dict, dict):
3503:             return gm_dict
3504:         decision = select_resolution_mode(
3505:             player_text=user_text,
3506:             scene=scene if isinstance(scene, dict) else None,
3507:             session=session if isinstance(session, dict) else None,
3508:             world=world if isinstance(world, dict) else None,
3509:             resolution=resolution if isinstance(resolution, dict) else None,
3510:             normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
3511:             route_choice=route_choice,
3512:         )
3513:         gm_dict = synthesize_live_improvisation_proposal(gm_dict, decision=decision)
3514:         return attach_bounded_improvisation_evaluation(
3515:             gm_dict,
3516:             session=session,
3517:             scene=scene,
3518:             world=world,
3519:             resolution=resolution if isinstance(resolution, dict) else None,
3520:         )
3521: 
3522:     def _repair_terminal_player_facing_if_needed(
3523:         gm_dict: dict,
3524:         *,
3525:         reason: str,
3526:         preserve_upstream_model_route: bool = False,
3527:     ) -> dict:
3528:         repair_started = _now_perf()
3529:         social_lane = _strict_social_route_signal()
3530:         if _gm_has_usable_player_facing_text(gm_dict):
3531:             _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(repair_started))
3532:             return gm_dict
3533:         if social_lane:
3534:             repaired = ensure_minimal_social_resolution(
3535:                 gm=gm_dict,
3536:                 session=session,
3537:                 reason=reason,
3538:                 world=world,
3539:                 resolution=resolution if isinstance(resolution, dict) else None,
3540:                 scene_envelope=scene,
3541:                 player_text=user_text,
3542:                 segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
3543:             )
3544:             print("[SOCIAL RESOLUTION REPAIR] terminal empty social output repaired")
3545:             _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(repair_started))
3546:             preserve_fallback_provenance_metadata(repaired, gm_dict)
3547:             _preserve_model_route_metadata(
3548:                 repaired,
3549:                 gm_dict,
3550:                 mark_upstream_preserved=preserve_upstream_model_route,
3551:             )
3552:             return repaired
3553:         repaired_ns = ensure_minimal_nonsocial_resolution(gm=gm_dict, session=session)
3554:         dbg = repaired_ns.get("debug_notes") if isinstance(repaired_ns.get("debug_notes"), str) else ""
3555:         repaired_ns["debug_notes"] = (dbg + " | " if dbg else "") + f"nonsocial_repair_context:{reason}"
3556:         print("[NON-SOCIAL RESOLUTION REPAIR] empty output repaired")
3557:         _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(repair_started))
3558:         preserve_fallback_provenance_metadata(repaired_ns, gm_dict)
3559:         _preserve_model_route_metadata(
3560:             repaired_ns,
3561:             gm_dict,
3562:             mark_upstream_preserved=preserve_upstream_model_route,
3563:         )
3564:         return repaired_ns
3565: 
3566:     def _extract_upstream_api_error(gm_dict: dict | None) -> dict | None:
3567:         md = gm_dict.get("metadata") if isinstance(gm_dict, dict) and isinstance(gm_dict.get("metadata"), dict) else {}
3568:         err = md.get("upstream_api_error") if isinstance(md.get("upstream_api_error"), dict) else None
3569:         return dict(err) if isinstance(err, dict) else None
```

### game/api.py:3650-3754

```text
3650:         if fam not in ("", "none"):
3651:             print("[FAST FALLBACK PRESERVED HUMAN-ADJACENT METADATA]")
3652:         if om.get("nearby_group_continuity_carryover") is True:
3653:             print("[FAST FALLBACK PRESERVED NEARBY-GROUP CONTINUITY CONTEXT]")
3654:         return out
3655: 
3656:     known_clues = list(get_all_known_clue_texts(session))
3657:     fast_fallback_mode = False
3658:     used_force_terminal_fallback = False
3659:     retry_loop_started: float | None = None
3660:     gpt_calls_used = 0
3661: 
3662:     def _call_gpt_route_kwargs(
3663:         *,
3664:         retry_attempt: int = 0,
3665:         retry_reason: str | None = None,
3666:     ) -> dict[str, Any]:
3667:         normalized_retry_reason = str(retry_reason or "").strip()
3668:         purpose = "primary_turn"
3669:         strict_social = False
3670:         if retry_attempt >= 1 or normalized_retry_reason in _RETRY_ESCALATION_ROUTE_REASONS:
3671:             purpose = "retry_escalation"
3672:         elif _strict_social_route_signal():
3673:             purpose = "strict_social"
3674:             strict_social = True
3675:         return {
3676:             "purpose": purpose,
3677:             "response_policy": response_policy if isinstance(response_policy, dict) else None,
3678:             "segmented_turn": segmented_turn if isinstance(segmented_turn, dict) else None,
3679:             "retry_attempt": int(retry_attempt or 0),
3680:             "retry_reason": normalized_retry_reason or None,
3681:             "strict_social": strict_social,
3682:         }
3683: 
3684:     def _bounded_call_gpt(
3685:         msgs: list,
3686:         *,
3687:         retry_attempt: int = 0,
3688:         retry_reason: str | None = None,
3689:     ):
3690:         nonlocal gpt_calls_used
3691:         if gpt_calls_used >= MANUAL_PLAY_MAX_CALL_GPT:
3692:             print("[RETRY SKIPPED: MANUAL_PLAY_GPT_BUDGET_EXCEEDED]")
3693:             return _synthetic_manual_play_gpt_budget_gm()
3694:         if int(retry_attempt or 0) > 0 and _seam_stamp_for_retry:
3695:             verify_same_turn_narration_stamp_for_retry(
3696:                 session,
3697:                 expected_ctir_stamp=_seam_stamp_for_retry,
3698:                 expected_narration_plan_bundle_stamp=_seam_stamp_for_retry,
3699:                 owner_module=__name__,
3700:             )
3701:         gpt_calls_used += 1
3702:         call_kwargs = _call_gpt_route_kwargs(
3703:             retry_attempt=retry_attempt,
3704:             retry_reason=retry_reason,
3705:         )
3706:         try:
3707:             sig = inspect.signature(call_gpt)
3708:             accepts_route_context = any(
3709:                 param.kind == inspect.Parameter.VAR_KEYWORD
3710:                 for param in sig.parameters.values()
3711:             ) or all(name in sig.parameters for name in call_kwargs)
3712:         except (TypeError, ValueError):
3713:             accepts_route_context = True
3714:         if accepts_route_context:
3715:             return call_gpt(msgs, **call_kwargs)
3716:         return call_gpt(msgs)
3717: 
3718:     retry_attempt = 0
3719:     _previous_narration_text = ""
3720:     from game.immutable_valid_response import adopt_host_speech
3721: 
3722:     adopted_speech = adopt_host_speech(
3723:         gm if isinstance(gm, dict) else _gm_for_skipped_provider_narration("", reason="authorized_host_speech"),
3724:         resolution=resolution, player_text=str(user_text or ""), session=session,
3725:         world=world,
3726:     )
3727:     if adopted_speech is not None:
3728:         gm = adopted_speech
3729:     if gm is None:
3730:         skipped = deterministic_provider_skip_line(
3731:             resolution=resolution if isinstance(resolution, dict) else None,
3732:             scene=scene if isinstance(scene, dict) else None,
3733:             world=world if isinstance(world, dict) else None,
3734:             session=session if isinstance(session, dict) else None,
3735:             player_text=str(user_text or ""),
3736:         )
3737:         if skipped is not None:
3738:             skip_text, skip_reason = skipped
3739:             gm = _gm_for_skipped_provider_narration(skip_text, reason=skip_reason)
3740:     if gm is None:
3741:         initial_gpt_started = _now_perf()
3742:         gm = guard_gm_output(
3743:             _bounded_call_gpt(messages),
3744:             scene,
3745:             user_text,
3746:             known_clues,
3747:             session=session,
3748:             world=world,
3749:             resolution=resolution,
3750:         )
3751:         gm = _attach_bounded_improvisation_authority(gm)
3752:         _accumulate_latency(latency_sink, "gpt_call", _elapsed_ms(initial_gpt_started))
3753:         retry_attempt = 0
3754:         social_dialogue_turn = _social_dialogue_turn()
```

### game/api.py:3800-3968

```text
3800:                     reason="nonretryable_upstream_error" if not upstream_api_error.get("retryable") else "social_retry_suppressed",
3801:                 )
3802:                 fast_fallback_mode = True
3803:         if (
3804:             not fast_fallback_mode
3805:             and isinstance(gm, dict)
3806:             and isinstance(resolution, dict)
3807:         ):
3808:             res_md = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
3809:             if (
3810:                 str(resolution.get("kind") or "").strip().lower() == "observe"
3811:                 and str(res_md.get("parser_lane") or "").strip().lower() == "local_observation_question"
3812:             ):
3813:                 from game.perception_grounding import realize_local_observation_line
3814: 
3815:                 grounded = realize_local_observation_line(
3816:                     scene if isinstance(scene, dict) else None,
3817:                     session=session if isinstance(session, dict) else None,
3818:                     world=world if isinstance(world, dict) else None,
3819:                     resolution=resolution,
3820:                     player_text=str(user_text or ""),
3821:                 )
3822:                 if grounded:
3823:                     gm = dict(gm)
3824:                     gm["player_facing_text"] = grounded
3825:                     md_grounded = dict(gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {})
3826:                     if md_grounded.get("structured_contract_failure"):
3827:                         md_grounded.pop("structured_contract_failure", None)
3828:                         md_grounded.pop("structured_output_rejected", None)
3829:                         md_grounded.pop("structured_contract_reason", None)
3830:                         envelope = md_grounded.get("realization_envelope")
3831:                         if isinstance(envelope, dict):
3832:                             md_grounded["realization_envelope"] = {
3833:                                 **envelope,
3834:                                 "declared_claims": None,
3835:                                 "narration": grounded,
3836:                                 "structured_contract_present": False,
3837:                                 "deterministic_realization": True,
3838:                                 "legacy_fallback": False,
3839:                             }
3840:                     gm["metadata"] = md_grounded
3841:                     tags = list(gm.get("tags") or [])
3842:                     if "local_observation_realization" not in tags:
3843:                         tags.append("local_observation_realization")
3844:                     gm["tags"] = tags
3845:                     md = dict(gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {})
3846:                     md["emission_provenance"] = {
3847:                         "class": "downstream_consequence",
3848:                         "kind": "local_observation",
3849:                         "contract_id": str((res_md.get("resolution_contract") or {}).get("contract_id") or "")
3850:                         if isinstance(res_md.get("resolution_contract"), dict)
3851:                         else "",
3852:                         "operation": "perceive",
3853:                         "semantic_owner": "resolution_contract",
3854:                     }
3855:                     gm["metadata"] = md
3856:             from game.immutable_valid_response import lifecycle_applies, run_preserve_if_valid
3857: 
3858:             if lifecycle_applies(resolution):
3859:                 from game.ordinary_semantic_ownership import social_narration_unnecessary
3860: 
3861:                 allow_regeneration = int(MAX_TARGETED_RETRY_ATTEMPTS) > 0 and not social_narration_unnecessary(
3862:                     resolution if isinstance(resolution, dict) else None
3863:                 )
3864: 
3865:                 def _regenerate_once(feedback: str, _messages=messages):
3866:                     retry_messages = (list(_messages) if isinstance(_messages, list) else []) + [
3867:                         {"role": "user", "content": feedback}
3868:                     ]
3869:                     regenerated = guard_gm_output(
3870:                         _bounded_call_gpt(
3871:                             retry_messages,
3872:                             retry_attempt=1,
3873:                             retry_reason="hard_invalid",
3874:                         ),
3875:                         scene,
3876:                         user_text,
3877:                         known_clues,
3878:                         session=session,
3879:                         world=world,
3880:                         resolution=resolution,
3881:                     )
3882:                     return _attach_bounded_improvisation_authority(regenerated)
3883: 
3884:                 gm = run_preserve_if_valid(
3885:                     gm,
3886:                     regenerate=_regenerate_once if allow_regeneration else None,
3887:                     resolution=resolution,
3888:                     player_text=user_text,
3889:                     scene=scene,
3890:                     world=world,
3891:                     session=session,
3892:                 )
3893:         from game.immutable_valid_response import response_is_immutable
3894: 
3895:         if not response_is_immutable(gm):
3896:             gm = _repair_candidate_speaker_before_retry(gm)
3897:         while not fast_fallback_mode and not response_is_immutable(gm):
3898:             from game.ordinary_semantic_ownership import social_narration_unnecessary
3899: 
3900:             if social_narration_unnecessary(resolution if isinstance(resolution, dict) else None):
3901:                 print("[RETRY SKIPPED: DETERMINED NONRESOLUTION]")
3902:                 break
3903:             failures = _failures_after_social_answer_priority(
3904:                 detect_retry_failures(
3905:                     player_text=user_text,
3906:                     gm_reply=gm,
3907:                     scene_envelope=scene,
3908:                     session=session,
3909:                     world=world,
3910:                     resolution=resolution,
3911:                     segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
3912:                 )
3913:             )
3914:             selected_failure = choose_retry_strategy(failures)
3915:             if not selected_failure:
3916:                 break
3917:             current_text = str(gm.get("player_facing_text") or "").strip() if isinstance(gm, dict) else ""
3918:             md_now = gm.get("metadata") if isinstance(gm, dict) and isinstance(gm.get("metadata"), dict) else {}
3919:             provider_not_sent = bool(
3920:                 md_now.get("provider_calls_disabled")
3921:                 or md_now.get("provider_budget_refusal")
3922:                 or md_now.get("provider_retry_disabled")
3923:             )
3924:             if narration_retry_should_stop(
3925:                 provider_not_sent=provider_not_sent,
3926:                 retry_attempt=retry_attempt,
3927:                 previous_text=_previous_narration_text,
3928:                 current_text=current_text,
3929:             ):
3930:                 print("[RETRY SKIPPED: UNCHANGED OR UNSENT OUTPUT]")
3931:                 fc = str(selected_failure.get("failure_class") or "").strip()
3932:                 force_started = _now_perf()
3933:                 gm = force_terminal_retry_fallback(
3934:                     session=session,
3935:                     original_text=current_text,
3936:                     failure=selected_failure,
3937:                     retry_failures=failures,
3938:                     player_text=user_text,
3939:                     scene_envelope=scene,
3940:                     world=world,
3941:                     resolution=resolution,
3942:                     base_gm=gm,
3943:                     segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
3944:                 )
3945:                 _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(force_started))
3946:                 gm = _repair_terminal_player_facing_if_needed(
3947:                     gm, reason="api_unchanged_narration_retry_stopped"
3948:                 )
3949:                 used_force_terminal_fallback = True
3950:                 record_emergency_nonplan_output(
3951:                     session,
3952:                     reason="unchanged_narration_retry_stopped",
3953:                     owner_module=__name__,
3954:                     extra={"failure_class": fc, "retry_attempt": retry_attempt},
3955:                 )
3956:                 break
3957:             _previous_narration_text = current_text
3958:             if retry_loop_started is None:
3959:                 retry_loop_started = _now_perf()
3960:             if retry_attempt >= max_targeted_retry_attempts:
3961:                 fc = str(selected_failure.get("failure_class") or "").strip()
3962:                 print(f"[RETRY ESCAPE HATCH] class={fc} attempts={retry_attempt}")
3963:                 force_started = _now_perf()
3964:                 gm = force_terminal_retry_fallback(
3965:                     session=session,
3966:                     original_text=str(gm.get("player_facing_text") or ""),
3967:                     failure=selected_failure,
3968:                     retry_failures=failures,
```

### game/api.py:4215-4290

```text
4215:                 else:
4216:                     gm = _retain_retry_contract_resolution(gm, gm_retry, resolution)
4217:                 break
4218:             gm = _retain_retry_contract_resolution(gm, gm_retry, resolution)
4219:         if retry_loop_started is not None:
4220:             _accumulate_latency(latency_sink, "retry_loop_total", _elapsed_ms(retry_loop_started))
4221:     if isinstance(gm, dict):
4222:         accounting = dict(gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {})
4223:         accounting["narration_provider_calls"] = int(gpt_calls_used)
4224:         accounting["narration_retry_count"] = int(retry_attempt)
4225:         gm["metadata"] = accounting
4226:     gm = _repair_terminal_player_facing_if_needed(
4227:         gm, reason="api_targeted_retry_post_terminal"
4228:     )
4229:     if isinstance(prompt_payload, dict) and isinstance(gm, dict):
4230:         gm = dict(gm)
4231:         sac = prompt_payload.get("scene_state_anchor_contract")
4232:         if isinstance(sac, dict):
4233:             gm["scene_state_anchor_contract"] = dict(sac)
4234:         cmw = prompt_payload.get("conversational_memory_window")
4235:         if not isinstance(cmw, dict):
4236:             # The provider payload omits this top-level copy when it is JSON-equal
4237:             # to the surviving response_policy child. Engine inspection still
4238:             # receives that same object.
4239:             policy_for_memory = prompt_payload.get("response_policy")
4240:             if isinstance(policy_for_memory, dict):
4241:                 cmw = policy_for_memory.get("conversational_memory_window")
4242:         if isinstance(cmw, dict):
4243:             gm["conversational_memory_window"] = dict(cmw)
4244:         scm = prompt_payload.get("selected_conversational_memory")
4245:         if isinstance(scm, list):
4246:             gm["selected_conversational_memory"] = list(scm)
4247:         pd0 = prompt_payload.get("prompt_debug")
4248:         if isinstance(pd0, dict):
4249:             cm = pd0.get("conversational_memory")
4250:             if isinstance(cm, dict):
4251:                 merged_pd = dict(gm["prompt_debug"]) if isinstance(gm.get("prompt_debug"), dict) else {}
4252:                 merged_pd["conversational_memory"] = dict(cm)
4253:                 gm["prompt_debug"] = merged_pd
4254:         _attach_scene_opening_curated_facts_to_gm(
4255:             gm,
4256:             prompt_payload=prompt_payload,
4257:             resolution=resolution if isinstance(resolution, dict) else None,
4258:         )
4259:     if retry_attempt == 0 and isinstance(gm, dict) and isinstance(resolution, dict):
4260:         from game.immutable_valid_response import response_is_immutable, run_preserve_if_valid
4261:         from game.resolution_contract import contract_mapping_from_resolution
4262: 
4263:         _narration_contract = contract_mapping_from_resolution(resolution)
4264:         if (
4265:             str(_narration_contract.get("operation") or "") == "unresolved"
4266:             and not str(_narration_contract.get("interlocutor_id") or "").strip()
4267:             and not response_is_immutable(gm)
4268:         ):
4269:             # No question or stall retry was owed. Keep a hard-valid narration
4270:             # from being rewritten into a pressure or social beat.
4271:             gm = run_preserve_if_valid(
4272:                 gm,
4273:                 regenerate=None,
4274:                 resolution=resolution,
4275:                 player_text=user_text,
4276:                 scene=scene,
4277:                 world=world,
4278:                 session=session,
4279:             )
4280:     gm = _apply_narration_hub_policy_handoff(
4281:         gm,
4282:         fast_fallback_mode=fast_fallback_mode,
4283:         response_policy=response_policy,
4284:         player_text=user_text,
4285:         scene_envelope=scene,
4286:         session=session,
4287:         world=world,
4288:         resolution=resolution,
4289:         discovered_clues=known_clues,
4290:         repair_terminal_player_facing_if_needed=_repair_terminal_player_facing_if_needed,
```

### game/api.py:4404-4510

```text
4404: def _run_resolved_turn_pipeline(
4405:     *,
4406:     campaign: dict,
4407:     character: dict,
4408:     session: dict,
4409:     world: dict,
4410:     combat: dict,
4411:     scene: dict,
4412:     recent_log: list,
4413:     resolution: dict,
4414:     normalized_action: dict | None,
4415:     fallback_user_text: str,
4416:     segmented_turn: dict | None = None,
4417:     route_choice: str | None = None,
4418:     directed_social_entry: dict | None = None,
4419:     latency_sink: dict | None = None,
4420: ) -> tuple[dict, dict, dict, dict, list[str], dict]:
4421:     """Shared resolved-turn flow for both `/api/action` and `/api/chat`.
4422: 
4423:     Stage 5: authoritative engine mutation is applied first.
4424:     Stage 6-7: prompt context and GPT narration are built only from that post-resolution state.
4425: 
4426:     **CTIR:** ``detach_ctir`` is the first step so any prior turn's session-backed CTIR cannot leak into
4427:     this mutation. Fresh CTIR for this turn is attached later inside
4428:     :func:`_build_gpt_narration_from_authoritative_state` (after hygiene on ``resolution``). Do not attach
4429:     CTIR here—keep build/attach next to prompt construction for retry-stable stamps.
4430:     """
4431:     detach_ctir(session)
4432:     from game.semantic_interpreter import player_visible_turns
4433: 
4434:     attach_interaction_obligation(
4435:         resolution,
4436:         player_text=resolution.get("prompt") or fallback_user_text,
4437:         session=session,
4438:         normalized_action=normalized_action,
4439:         scene_id=str(((scene or {}).get("scene") or {}).get("id") or session.get("active_scene_id") or ""),
4440:         scene=scene,
4441:         world=world,
4442:         visible_turns=player_visible_turns(recent_log),
4443:         enable_model_interpretation=not live_interpretation_consumed(),
4444:     )
4445:     engine_started = _now_perf()
4446:     departure_scene = scene
4447:     scene, session, combat, authoritative_clue_updates, scene_rt = _apply_authoritative_resolution_state_mutation(
4448:         session=session,
4449:         world=world,
4450:         combat=combat,
4451:         scene=scene,
4452:         resolution=resolution,
4453:         normalized_action=normalized_action,
4454:     )
4455:     from game.gm_resolution_decision import reconcile_movement_decision
4456: 
4457:     reconcile_movement_decision(
4458:         resolution,
4459:         departure_scene=departure_scene,
4460:         destination_scene=scene,
4461:         world=world,
4462:     )
4463:     if isinstance(session, dict):
4464:         append_debug_trace(
4465:             session,
4466:             build_state_mutation_trace(
4467:                 domain=SCENE_STATE,
4468:                 owner_module=__name__,
4469:                 operation="authoritative_resolution_mutation",
4470:                 extra={
4471:                     "changed_area": "session+world+scene_runtime",
4472:                     "resolution_kind": str((resolution or {}).get("kind") or ""),
4473:                 },
4474:             ),
4475:         )
4476:     _accumulate_latency(latency_sink, "engine_resolution", _elapsed_ms(engine_started))
4477: 
4478:     user_text = resolution.get('prompt') or fallback_user_text
4479:     response_type_contract = _derive_response_type_contract_for_turn(
4480:         session=session,
4481:         segmented_turn=segmented_turn,
4482:         normalized_action=normalized_action,
4483:         resolution=resolution,
4484:         raw_player_text=user_text,
4485:         route_choice=route_choice,
4486:         directed_social_entry=directed_social_entry,
4487:     )
4488:     gm = _build_gpt_narration_from_authoritative_state(
4489:         campaign=campaign,
4490:         world=world,
4491:         session=session,
4492:         character=character,
4493:         scene=scene,
4494:         combat=combat,
4495:         recent_log=recent_log,
4496:         user_text=user_text,
4497:         resolution=resolution,
4498:         scene_runtime=scene_rt,
4499:         segmented_turn=segmented_turn,
4500:         route_choice=route_choice,
4501:         directed_social_entry=directed_social_entry,
4502:         response_type_contract=response_type_contract,
4503:         latency_sink=latency_sink,
4504:         normalized_action=normalized_action,
4505:     )
4506:     return (scene, session, combat, gm, authoritative_clue_updates, response_type_contract)
4507: 
4508: 
4509: def _resolve_engine_noncombat_seam(
4510:     scene: dict,
```

### game/api.py:4690-4750

```text
4690:         "hint": (
4691:             "Campaign opening turn: narrate the active scene as an immediate playable situation, "
4692:             "with concrete opportunities grounded in the current scene state."
4693:         ),
4694:     }
4695: 
4696: 
4697: def _opening_scene_normalized_action_and_resolution(
4698:     *,
4699:     scene: dict,
4700:     player_text: str | None,
4701:     internal_bootstrap: bool,
4702: ) -> tuple[dict, dict]:
4703:     """Shared opening-scene engine bundle for chat campaign-start cues and ``/api/start_campaign``."""
4704:     scene_obj = scene.get("scene") if isinstance(scene.get("scene"), dict) else {}
4705:     sid = str(scene_obj.get("id") or "").strip()
4706:     if internal_bootstrap:
4707:         resolution = _build_opening_scene_resolution("", sid, internal_bootstrap=True)
4708:         normalized = {
4709:             "id": "campaign_start_opening_scene",
4710:             "label": "start_campaign",
4711:             "type": "scene_opening",
4712:             "prompt": "",
4713:             "targetSceneId": sid or None,
4714:             "target_scene_id": sid or None,
4715:         }
4716:         return normalized, resolution
4717:     pt = (player_text or "").strip()
4718:     resolution = _build_opening_scene_resolution(pt, sid, internal_bootstrap=False)
4719:     normalized = {
4720:         "id": "campaign_start_opening_scene",
4721:         "label": pt,
4722:         "type": "scene_opening",
4723:         "prompt": pt,
4724:         "targetSceneId": sid or None,
4725:         "target_scene_id": sid or None,
4726:     }
4727:     return normalized, resolution
4728: 
4729: 
4730: def _session_allows_structured_start_campaign(session: dict, recent_log: list | None) -> bool:
4731:     """Fresh run: no prior opening emission, empty transcript, first chat-scale turn index.
4732: 
4733:     Drives ``ui.campaign_can_start`` only; ``session.campaign_started`` is the separate latch
4734:     set after a successful first opening (see ``_complete_opening_turn_persistence_like_chat``).
4735:     """
4736:     if bool(session.get("campaign_started")):
4737:         return False
4738:     if recent_log:
4739:         return False
4740:     if int(session.get("turn_counter", 0) or 0) != 0:
4741:         return False
4742:     return True
4743: 
4744: 
4745: def _compose_ui_interaction_snapshot(session: dict, world: dict) -> dict:
4746:     """Compact active interaction context for the player UI."""
4747:     snap = dict(response_type_context_snapshot(session))
4748:     tid = str(snap.get("active_interaction_target_id") or "").strip()
4749:     if tid:
4750:         npc = npc_dict_by_id(world, tid)
```

### game/api.py:5054-5092

```text
5054: 
5055: @app.post('/api/new_campaign')
5056: def new_campaign(request: Request):
5057:     """Hard reset: new session graph, fresh combat, world playthrough cleared, transcript empty."""
5058:     try:
5059:         ui_mode = resolve_requested_ui_mode(request)
5060:         assert_mode_allows_runtime_action(ui_mode)
5061:     except UiModePolicyError as e:
5062:         return _ui_mode_error_response(e)
5063:     gate, gate_operator = _compute_upstream_gate_for_live_gameplay()
5064:     if gate.get("manual_testing_blocked"):
5065:         return JSONResponse(
5066:             status_code=503,
5067:             content={
5068:                 "ok": False,
5069:                 "status": "blocked",
5070:                 "error": (
5071:                     "Upstream API preflight indicates live narration is unhealthy; "
5072:                     "new campaign start is disabled until upstream recovers."
5073:                 ),
5074:                 "upstream_dependent_run_gate": gate,
5075:                 "upstream_dependent_run_gate_operator": gate_operator,
5076:             },
5077:         )
5078:     meta = apply_new_campaign_hard_reset()
5079:     # When ASHEN_THRONES_DEV_VERIFY=1, ``campaign_reset`` prints a compact runtime-clean summary.
5080:     if "dev_verify_ok" not in meta:
5081:         print("[API] New campaign started", meta.get("campaign_run_id"))
5082:     return {
5083:         "status": "ok",
5084:         "ok": True,
5085:         "ui_mode": ui_mode,
5086:         "upstream_dependent_run_gate": gate,
5087:         "upstream_dependent_run_gate_operator": gate_operator,
5088:         **meta,
5089:     }
5090: 
5091: 
5092: @app.post('/api/reset_session')
```

### game/api.py:5710-5752

```text
5710:     combat: dict,
5711:     scene: dict,
5712:     scene_before_id: str,
5713:     trace: dict,
5714:     latency_ms: dict[str, int],
5715:     clue_presentation_before: dict,
5716:     clocks_before: dict,
5717:     time_pressure_after: int,
5718:     tick: dict,
5719:     recent_log: list,
5720:     routed_via_exploration: bool,
5721:     routed_via_adjudication: bool,
5722:     normalized_chat: dict | None,
5723:     resolution: dict | None,
5724:     gm: dict,
5725:     response_type_contract: dict | None,
5726:     route_choice: str | None,
5727:     parsed: dict | None,
5728:     segmented_turn: dict | None,
5729:     compact_segmented: dict | None,
5730:     canonical_entry: dict,
5731:     implied_context: dict,
5732:     authoritative_clue_updates: list[str],
5733:     player_text_for_eval: str,
5734:     debug_action_kind: str,
5735:     trace_source: str,
5736:     trace_action_type: str,
5737:     request_log_payload: dict,
5738:     mark_campaign_started: bool,
5739: ) -> dict:
5740:     """Shared tail of ``/api/chat`` after GM output exists (opening / exploration / adjudication paths).
5741: 
5742:     ``POST /api/start_campaign`` reuses this tail with ``mark_campaign_started`` so bootstrap
5743:     persistence matches chat openings; final-emission layers remain downstream consumers only.
5744:     """
5745:     from game.gm import classify_player_intent
5746: 
5747:     def _text_preview(value: object, *, limit: int = 180) -> str:
5748:         text = str(value or "")
5749:         return text[:limit] + ("..." if len(text) > limit else "")
5750: 
5751:     def _attach_final_text_invariant_debug(
5752:         gm_obj: dict,
```

### game/api.py:5790-5868

```text
5790:         )
5791:     )
5792:     if response_type_contract is None:
5793:         response_type_contract = _derive_response_type_contract_for_turn(
5794:             session=session,
5795:             segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
5796:             normalized_action=normalized_chat,
5797:             resolution=resolution if isinstance(resolution, dict) else None,
5798:             raw_player_text=player_text_for_eval,
5799:             route_choice=route_choice,
5800:             directed_social_entry=canonical_entry,
5801:             attach_to_resolution=bool(isinstance(resolution, dict)),
5802:         )
5803:     remember_recent_contextual_leads(
5804:         session,
5805:         scene["scene"]["id"],
5806:         _player_facing_text_for_lead_extraction(gm),
5807:     )
5808:     gm, _narr_consistency_chat = _finalize_player_facing_for_turn(
5809:         gm,
5810:         resolution=resolution if isinstance(resolution, dict) else None,
5811:         session=session,
5812:         world=world,
5813:         scene=scene,
5814:         include_resolution_in_sanitizer=_include_res_chat,
5815:         latency_sink=latency_ms,
5816:     )
5817:     gm = apply_authored_knowledge_realization_to_gm(
5818:         gm,
5819:         player_text=player_text_for_eval,
5820:         resolution=resolution if isinstance(resolution, dict) else None,
5821:         session=session if isinstance(session, dict) else None,
5822:         world=world if isinstance(world, dict) else None,
5823:         scene=scene if isinstance(scene, dict) else None,
5824:         scene_id=str((scene.get("scene") or {}).get("id") or "").strip(),
5825:         extra_facts=authoritative_clue_updates,
5826:     )
5827:     gm = apply_stay_leave_narration_agreement_to_gm(
5828:         gm,
5829:         resolution=resolution if isinstance(resolution, dict) else None,
5830:         origin_scene_id=str((resolution or {}).get("originating_scene_id") or ""),
5831:     )
5832:     gm = apply_destination_arrival_realization_to_gm(
5833:         gm,
5834:         resolution=resolution if isinstance(resolution, dict) else None,
5835:         scene=scene if isinstance(scene, dict) else None,
5836:         player_text=player_text_for_eval,
5837:     )
5838:     gm = apply_perception_non_invention_to_gm(
5839:         gm,
5840:         resolution=resolution if isinstance(resolution, dict) else None,
5841:         session=session if isinstance(session, dict) else None,
5842:         world=world if isinstance(world, dict) else None,
5843:         scene=scene if isinstance(scene, dict) else None,
5844:         player_text=player_text_for_eval,
5845:     )
5846:     if isinstance(resolution, dict):
5847:         from game.resolution_contract import enforce_emitted_contract_monotonicity
5848: 
5849:         gm = enforce_emitted_contract_monotonicity(gm, resolution)
5850:     if str((resolution or {}).get("kind") or "").strip().lower() not in {
5851:         "scene_opening",
5852:         "scene_transition",
5853:         "travel",
5854:     }:
5855:         from game.perception_grounding import remember_completed_perception_turn
5856: 
5857:         remember_completed_perception_turn(
5858:             session,
5859:             str((scene.get("scene") or {}).get("id") or "").strip(),
5860:             scene,
5861:             str((gm or {}).get("player_facing_text") or ""),
5862:             resolution=resolution if isinstance(resolution, dict) else None,
5863:             player_text=player_text_for_eval,
5864:         )
5865:     canonical_gm = gm
5866:     if isinstance(resolution, dict) and str(resolution.get("kind") or "").strip().lower() == "scene_opening":
5867:         metadata = canonical_gm.get("metadata") if isinstance(canonical_gm.get("metadata"), dict) else {}
5868:         emission_debug = metadata.get("emission_debug") if isinstance(metadata.get("emission_debug"), dict) else {}
```

### game/api.py:5927-6120

```text
5927:         resolution=resolution if isinstance(resolution, dict) else None,
5928:         scene=scene if isinstance(scene, dict) else None,
5929:         world=world if isinstance(world, dict) else None,
5930:     )
5931:     synchronize_scene_addressability(session, scene, world)
5932:     scene["scene_state"] = session.get("scene_state")
5933:     save_world(world)
5934: 
5935:     leads_inspection = _lead_debug_trace_around_authoritative_reconcile(session)
5936: 
5937:     session["last_action_debug"] = _build_action_debug(
5938:         debug_action_kind, player_text_for_eval, normalized_chat, resolution, response_type_contract
5939:     )
5940:     _merge_emergent_actor_debug_into_action_debug(session)
5941:     maybe_attach_intent_fulfillment_eval(
5942:         session,
5943:         player_input=player_text_for_eval,
5944:         final_output=str(gm.get("player_facing_text") or ""),
5945:         response_type=compact_response_type_contract(response_type_contract),
5946:     )
5947:     maybe_attach_player_agency_eval(
5948:         session,
5949:         final_output=str(gm.get("player_facing_text") or ""),
5950:     )
5951: 
5952:     clocks_changed = {"time_pressure": time_pressure_after} if clocks_before.get("time_pressure") != time_pressure_after else {}
5953: 
5954:     trace["parsed_intent"] = parsed if parsed is not None else None
5955:     trace["normalized_action"] = (
5956:         {
5957:             k: normalized_chat[k]
5958:             for k in ("id", "label", "type", "prompt", "targetSceneId", "target_scene_id")
5959:             if k in (normalized_chat or {})
5960:         }
5961:         if normalized_chat and isinstance(normalized_chat, dict)
5962:         else None
5963:     )
5964:     trace["resolution"] = _sanitize_resolution(resolution)
5965:     trace["response_type_contract"] = compact_response_type_contract(response_type_contract)
5966:     trace["scene_after"] = scene["scene"]["id"]
5967:     deduped_clue_updates: list[str] = []
5968:     for txt in authoritative_clue_updates:
5969:         if isinstance(txt, str) and txt.strip() and txt.strip() not in deduped_clue_updates:
5970:             deduped_clue_updates.append(txt.strip())
5971:     trace["clue_updates"] = deduped_clue_updates
5972:     trace["world_flag_updates"] = _trace_world_updates(gm.get("world_updates"), clocks_changed)
5973:     latency_ms["total_turn"] = _elapsed_ms(turn_started)
5974:     trace["turn_trace"] = _build_compact_turn_trace(
5975:         source=trace_source,
5976:         action_type=trace_action_type,
5977:         raw_input=trace["raw_input"],
5978:         parsed_intent=parsed if isinstance(parsed, dict) else None,
5979:         segmented_turn=compact_segmented,
5980:         normalized_action=normalized_chat,
5981:         implied_context=implied_context,
5982:         resolution=resolution,
5983:         scene_before=trace["scene_before"],
5984:         scene_after=trace["scene_after"],
5985:         authoritative_clue_updates=deduped_clue_updates,
5986:         clue_presentation_before=clue_presentation_before,
5987:         session=session,
5988:         world=world,
5989:         scene=scene,
5990:         leads_inspection=leads_inspection,
5991:         response_type_contract=response_type_contract,
5992:         route_selected=route_choice,
5993:         directed_social_entry=canonical_entry,
5994:         adoption_debug=_adopt_dbg_chat,
5995:         stale_invalidation_debug=_stale_inv_dbg_chat,
5996:         latency_ms=_finalize_latency_breakdown(latency_ms),
5997:     )
5998:     trace["latency_ms"] = _finalize_latency_breakdown(latency_ms)
5999:     trace["performance"] = _performance_record(
6000:         latency=trace["latency_ms"],
6001:         gm=gm if isinstance(gm, dict) else None,
6002:         provider_requests=len((trace.get("live_chat_interpretation") or {}).get("provider_requests") or [])
6003:         if isinstance(trace.get("live_chat_interpretation"), dict)
6004:         else 0,
6005:         successful=True,
6006:         disposition=str(trace.get("action_type") or "chat"),
6007:         interpretation_usage=(trace.get("live_chat_interpretation") or {}).get("provider_requests") or [],
6008:     )
6009:     if isinstance(resolution, dict):
6010:         resolution_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
6011:         resolution["metadata"] = {**resolution_meta, "performance": trace["performance"]}
6012:     _finalize_and_append_trace(session, trace, True, None)
6013: 
6014:     clear_turn_start_interlocutor_snapshot(session)
6015:     # First successful opening only (structured start or chat scene_opening); never set on failed turns.
6016:     if mark_campaign_started:
6017:         session["campaign_started"] = True
6018:     from game.immutable_valid_response import restore_accepted_text
6019: 
6020:     restore_accepted_text(gm)
6021:     if (isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) and isinstance(gm, dict)
6022:             and ((gm.get("metadata") or {}).get("accepted_response") or {}).get("authorization_source") != "host_terminal_safety"):
6023:         from game.dialogue_authority import remember_dialogue_commitment
6024:         from game.immutable_valid_response import restore_accepted_text
6025: 
6026:         restore_accepted_text(gm)
6027:         remember_dialogue_commitment(
6028:             session,
6029:             social=resolution.get("social"),
6030:             player_text=str(player_text_for_eval or ""),
6031:             line=str(gm.get("player_facing_text") or ""),
6032:             turn=int(session.get("turn_counter") or 0),
6033:         )
6034:     from game.conversational_continuity import record_delivered_exchange
6035: 
6036:     speech_adoption = (gm.get("metadata") or {}).get("accepted_response") or {}
6037:     speech_adoption = speech_adoption or None
6038:     record_delivered_exchange(
6039:         session,
6040:         player_text=str(player_text_for_eval or ""),
6041:         delivered_text=str(gm.get("player_facing_text") or ""),
6042:         social=resolution.get("social") if isinstance(resolution, dict) else None,
6043:         scene_id=str(scene["scene"].get("id") or ""),
6044:         turn=int(session.get("turn_counter") or 0),
6045:         adoption=speech_adoption,
6046:     )
6047:     session.setdefault("conversational_context", {})["last_gm_exchange"] = {
6048:         "category": "RESOLVED", "owner": "GM", "purpose": "ACTION_RESULT",
6049:         "subject": str(player_text_for_eval or "")[:240],
6050:         "response": str(gm.get("player_facing_text") or "")[:1200],
6051:         "refusal_reason": None, "scene_id": scene["scene"].get("id"),
6052:         "operation": (resolution or {}).get("kind"),
6053:     }
6054:     save_session(session)
6055:     save_combat(combat)
6056: 
6057:     intent = classify_player_intent(player_text_for_eval)
6058:     if (routed_via_exploration or routed_via_adjudication) and isinstance(resolution, dict):
6059:         resolution.setdefault("world_tick_events", tick.get("events", []))
6060: 
6061:     gm_prompt_summary: dict = {
6062:         "scene_id": scene["scene"].get("id"),
6063:         "scene_mode": scene["scene"].get("mode"),
6064:         "response_mode": session.get("response_mode", "standard"),
6065:         "response_type_contract": compact_response_type_contract(response_type_contract),
6066:     }
6067:     if routed_via_exploration and isinstance(resolution, dict):
6068:         gm_prompt_summary["exploration"] = {
6069:             "action_id": resolution.get("action_id"),
6070:             "kind": resolution.get("kind"),
6071:             "scene_transition_occurred": bool(resolution.get("resolved_transition")),
6072:         }
6073:     if routed_via_adjudication and isinstance(resolution, dict):
6074:         gm_prompt_summary["adjudication"] = dict(resolution.get("adjudication") or {})
6075: 
6076:     log_meta = dict(request_log_payload.get("log_meta") or {})
6077:     log_meta.setdefault("intent_classification", intent)
6078:     log_meta.setdefault("gm_prompt_context_summary", gm_prompt_summary)
6079:     log_meta.setdefault("gm_raw_output_meta", {"has_output": True})
6080:     log_meta.setdefault("approved_state_updates", {
6081:         "scene_update": gm.get("scene_update"),
6082:         "world_updates": gm.get("world_updates"),
6083:         "new_scene_draft": gm.get("new_scene_draft"),
6084:     })
6085:     log_meta.setdefault("rejected_state_updates", [])
6086:     log_meta.setdefault("discovered_clues_added", deduped_clue_updates)
6087:     log_meta.setdefault("surfaced_clues_in_narration_non_authoritative", list(surfaced_clue_telemetry))
6088:     log_meta.setdefault("clocks_changed", clocks_changed)
6089:     log_meta.setdefault("response_type_contract", compact_response_type_contract(response_type_contract))
6090: 
6091:     response_payload = _build_turn_response_payload(
6092:         gm=gm,
6093:         resolution=resolution if _include_res_chat else None,
6094:         include_resolution=_include_res_chat,
6095:     )
6096:     final_text = str(canonical_gm.get("player_facing_text") or "")
6097:     payload_gm = response_payload.get("gm_output") if isinstance(response_payload, dict) else None
6098:     if mark_campaign_started and isinstance(response_payload, dict):
6099:         response_payload["gm_output"] = canonical_gm
6100:         payload_gm = canonical_gm
6101:     _attach_final_text_invariant_debug(
6102:         canonical_gm,
6103:         response_payload=response_payload if isinstance(response_payload, dict) else None,
6104:         log_payload_text=final_text,
6105:     )
6106:     if isinstance(payload_gm, dict) and payload_gm is not canonical_gm:
6107:         payload_metadata = payload_gm.setdefault("metadata", {})
6108:         if isinstance(payload_metadata, dict):
6109:             payload_debug = payload_metadata.setdefault("emission_debug", {})
6110:             source_debug = (
6111:                 (canonical_gm.get("metadata") or {}).get("emission_debug")
6112:                 if isinstance(canonical_gm.get("metadata"), dict)
6113:                 else {}
6114:             )
6115:             if isinstance(payload_debug, dict) and isinstance(source_debug, dict):
6116:                 payload_debug.update(source_debug)
6117:     assert (
6118:         response_payload["gm_output"] is canonical_gm
6119:         or response_payload["gm_output"]["player_facing_text"] == canonical_gm["player_facing_text"]
6120:     )
```

### game/api.py:6138-6378

```text
6138: 
6139: @app.post('/api/start_campaign')
6140: def start_campaign(request: Request):
6141:     """First opening via internal bootstrap intent; same narration stack as chat opening (OF1 path)."""
6142:     from game.provider_budget import playtest_stop_reason, PLAYTEST_STOP_MESSAGE
6143:     if playtest_stop_reason():
6144:         return JSONResponse(status_code=409, content={"ok": False, "status": "blocked", "error": PLAYTEST_STOP_MESSAGE})
6145:     try:
6146:         ui_mode = resolve_requested_ui_mode(request)
6147:         assert_mode_allows_runtime_action(ui_mode)
6148:     except UiModePolicyError as e:
6149:         return _ui_mode_error_response(e)
6150:     gate, gate_operator = _compute_upstream_gate_for_live_gameplay()
6151:     if gate.get("manual_testing_blocked"):
6152:         return JSONResponse(
6153:             status_code=503,
6154:             content={
6155:                 "ok": False,
6156:                 "status": "blocked",
6157:                 "error": (
6158:                     "Upstream API preflight indicates live narration is unhealthy; "
6159:                     "starting the campaign is disabled until upstream recovers."
6160:                 ),
6161:                 "upstream_dependent_run_gate": gate,
6162:                 "upstream_dependent_run_gate_operator": gate_operator,
6163:             },
6164:         )
6165: 
6166:     campaign = load_campaign()
6167:     character = load_character()
6168:     session = load_session()
6169:     recent_log = load_log()
6170:     if not _session_allows_structured_start_campaign(session, recent_log):
6171:         st = compose_state()
6172:         return JSONResponse(
6173:             status_code=409,
6174:             content={
6175:                 "ok": False,
6176:                 "status": "already_started",
6177:                 "error": "Campaign has already started, or the transcript is not empty.",
6178:                 "upstream_dependent_run_gate": gate,
6179:                 "upstream_dependent_run_gate_operator": gate_operator,
6180:                 **_project_state_for_ui_mode(st, ui_mode),
6181:             },
6182:         )
6183: 
6184:     turn_started = _now_perf()
6185:     snapshot_turn_start_interlocutor(session)
6186:     world = load_world()
6187:     combat = load_combat()
6188:     conditions = load_conditions()
6189:     scene = load_active_scene()
6190:     synchronize_scene_addressability(session, scene, world)
6191:     scene["scene_state"] = session.get("scene_state")
6192:     scene_before_id = scene["scene"]["id"]
6193: 
6194:     trace: dict = {
6195:         "timestamp": utc_iso_now(),
6196:         "source": "start_campaign",
6197:         "action_type": "start_campaign",
6198:         "raw_input": "",
6199:         "turn_stage_order": list(AUTHORITATIVE_TURN_STAGE_ORDER),
6200:         "incoming_payload": {"start_campaign": True},
6201:         "parsed_intent": None,
6202:         "segmented_turn": None,
6203:         "normalized_action": None,
6204:         "resolution": None,
6205:         "scene_before": scene["scene"]["id"],
6206:         "scene_after": None,
6207:         "clue_updates": [],
6208:         "world_flag_updates": [],
6209:         "turn_trace": None,
6210:         "gpt_called": True,
6211:         "response_ok": True,
6212:         "error": None,
6213:     }
6214:     latency_ms: dict[str, int] = {}
6215:     clue_presentation_before = _snapshot_known_clue_presentations(session)
6216: 
6217:     if session.get("turn_counter") is None:
6218:         session["turn_counter"] = 0
6219:     session["turn_counter"] += 1
6220: 
6221:     tick = advance_world_tick(world, campaign)
6222:     save_world(world)
6223: 
6224:     clocks_before = dict(get_or_init_clocks(session))
6225:     time_pressure_after = advance_clock(session, "time_pressure", 1)
6226: 
6227:     recent_log = load_log()
6228:     scene_rt = get_scene_runtime(session, scene["scene"]["id"])
6229: 
6230:     routed_via_exploration = True
6231:     routed_via_adjudication = False
6232:     route_choice = "action"
6233:     authoritative_clue_updates: list[str] = []
6234: 
6235:     classify_started = _now_perf()
6236:     segmented_turn = segment_mixed_player_turn("")
6237:     trace["segmented_turn"] = _compact_segmented_turn(segmented_turn)
6238:     canonical_entry = resolve_directed_social_entry(
6239:         session=session,
6240:         scene=scene,
6241:         world=world,
6242:         segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
6243:         raw_text="",
6244:     )
6245:     declared_switch_meta = resolve_declared_actor_switch(
6246:         session=session,
6247:         scene=scene,
6248:         segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
6249:         raw_text="",
6250:     )
6251:     trace["canonical_entry"] = {
6252:         "should_route_social": bool(canonical_entry.get("should_route_social")),
6253:         "target_actor_id": canonical_entry.get("target_actor_id"),
6254:         "target_source": canonical_entry.get("target_source"),
6255:         "reason": canonical_entry.get("reason"),
6256:         "spoken_text": canonical_entry.get("spoken_text"),
6257:         "declared_switch_detected": bool(declared_switch_meta.get("has_declared_switch")),
6258:         "declared_switch_target_actor_id": (
6259:             declared_switch_meta.get("target_actor_id")
6260:             if declared_switch_meta.get("has_declared_switch")
6261:             else None
6262:         ),
6263:         "continuity_overridden_by_declared_switch": bool(
6264:             canonical_entry.get("continuity_overridden_by_declared_switch")
6265:         ),
6266:         "spoken_vocative_detected": bool(canonical_entry.get("spoken_vocative_detected")),
6267:         "spoken_vocative_target_actor_id": canonical_entry.get("spoken_vocative_target_actor_id"),
6268:         "continuity_overridden_by_spoken_vocative": bool(
6269:             canonical_entry.get("continuity_overridden_by_spoken_vocative")
6270:         ),
6271:     }
6272:     for _k in (
6273:         "open_social_solicitation",
6274:         "broad_address_bid",
6275:         "broadcast_social_open_call",
6276:         "candidate_addressable_ids",
6277:         "candidate_addressable_count",
6278:         "broad_address_reason",
6279:         "broad_address_phrase_matched",
6280:     ):
6281:         if _k in canonical_entry:
6282:             trace["canonical_entry"][_k] = canonical_entry.get(_k)
6283:     trace["canonical_entry_path"] = (
6284:         "social" if canonical_entry.get("should_route_social") else "undecided"
6285:     )
6286:     trace["canonical_entry_reason"] = canonical_entry.get("reason")
6287:     trace["canonical_entry_target_actor_id"] = canonical_entry.get("target_actor_id")
6288:     implied_context = _prepare_interaction_from_turn_input(session, world, scene_before_id, "", scene=scene)
6289:     compact_segmented = _compact_segmented_turn(segmented_turn)
6290: 
6291:     normalized_chat, resolution = _opening_scene_normalized_action_and_resolution(
6292:         scene=scene,
6293:         player_text=None,
6294:         internal_bootstrap=True,
6295:     )
6296:     parsed = normalized_chat
6297:     _accumulate_latency(latency_ms, "intent_classification", _elapsed_ms(classify_started))
6298: 
6299:     try:
6300:         scene, session, combat, gm, turn_clue_updates, response_type_contract = _run_resolved_turn_pipeline(
6301:             campaign=campaign,
6302:             character=character,
6303:             session=session,
6304:             world=world,
6305:             combat=combat,
6306:             scene=scene,
6307:             recent_log=recent_log,
6308:             resolution=resolution,
6309:             normalized_action=normalized_chat,
6310:             fallback_user_text="",
6311:             segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
6312:             route_choice="action",
6313:             directed_social_entry=canonical_entry,
6314:             latency_sink=latency_ms,
6315:         )
6316:     except Exception:
6317:         session["turn_counter"] = max(0, int(session.get("turn_counter", 0) or 0) - 1)
6318:         save_session(session)
6319:         raise
6320: 
6321:     authoritative_clue_updates.extend(turn_clue_updates)
6322:     if isinstance(resolution, dict):
6323:         resolution["world_tick_events"] = tick.get("events", [])
6324: 
6325:     _record_scene_pressure_input(
6326:         session,
6327:         scene_before_id,
6328:         "",
6329:         normalized_action=parsed if isinstance(parsed, dict) else None,
6330:         resolution=None,
6331:     )
6332: 
6333:     request_log = {
6334:         "request": {"start_campaign": True, "action_type": "start_campaign"},
6335:         "log_meta": {
6336:             "bootstrap_intent": "start_campaign",
6337:             "player_input": "",
6338:         },
6339:     }
6340: 
6341:     return _complete_opening_turn_persistence_like_chat(
6342:         turn_started=turn_started,
6343:         campaign=campaign,
6344:         character=character,
6345:         session=session,
6346:         world=world,
6347:         combat=combat,
6348:         scene=scene,
6349:         scene_before_id=scene_before_id,
6350:         trace=trace,
6351:         latency_ms=latency_ms,
6352:         clue_presentation_before=clue_presentation_before,
6353:         clocks_before=clocks_before,
6354:         time_pressure_after=time_pressure_after,
6355:         tick=tick,
6356:         recent_log=recent_log,
6357:         routed_via_exploration=routed_via_exploration,
6358:         routed_via_adjudication=routed_via_adjudication,
6359:         normalized_chat=normalized_chat,
6360:         resolution=resolution,
6361:         gm=gm,
6362:         response_type_contract=response_type_contract,
6363:         route_choice=route_choice,
6364:         parsed=parsed,
6365:         segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
6366:         compact_segmented=compact_segmented,
6367:         canonical_entry=canonical_entry,
6368:         implied_context=implied_context,
6369:         authoritative_clue_updates=authoritative_clue_updates,
6370:         player_text_for_eval="",
6371:         debug_action_kind="start_campaign",
6372:         trace_source="start_campaign",
6373:         trace_action_type="start_campaign",
6374:         request_log_payload=request_log,
6375:         mark_campaign_started=True,
6376:     )
6377: 
6378: 
```

### game/gm.py:202-290

```text
202: SYSTEM_PROMPT = _SYSTEM_PROMPT_HEADER + """The application owns authoritative mechanics, state, and persistence. You realize the supplied turn: narrate within the payload, propose only through the structured lanes, and never invent dice results or override app-supplied resolutions.
203: Use the shipped response_policy, visibility data, resolution_contract, gm_resolution_decision, and decision_facing_answer_recipe as the operational guide for this turn. The recipe is guidance only; it grants no new authority.
204: Answer direct questions first. If certainty is incomplete, give the strongest grounded partial answer and keep the limit diegetic. Player hypotheses remain hypothetical unless the supplied decision/claims authorize more.
205: Treat player input as an action declaration. resolved_exploration_action; scene_transition_already_occurred; do not restate; third person; quoted in-character speech; do not restate or paraphrase the player's input.
206: Never speak as a validator, analyst, system, or referee of canon in standard narration. Spoiler safeguard: no hidden_facts, clues, planner labels, JSON, or engine scaffolding.
207: Specific NPC replies should provide a concrete answer, partial specific, source, or usable next step when the NPC can plausibly know one. Mundane NPC dialogue and low-stakes texture may be bounded incidental realization; unsupported durable facts require the structured lanes.
208: When app-resolved mechanics, scene transitions, speaker selection, visibility, or narration obligations are present, follow them exactly. Do not choose the player's next action or turn a lead into a mandatory path unless authoritative state already imposes that constraint.
209: Question resolution rule: direct answer (first sentence). Scene momentum rule: every 2-3 exchanges tag scene_momentum:<kind>, including consequence_or_opportunity.
210: 
211: Return valid JSON only with this one-call realization envelope. The final player response is `narration`; `declared_claims` is internal:
212: {
213:   "declared_claims": [
214:     {
215:       "declaration_id": "string",
216:       "declaration_mode": "realize|propose",
217:       "source_claim_id": null | "claim_id_from_gm_resolution_decision",
218:       "premise_claim_ids": ["claim_id_of_each_proposition_this_epistemic_claim_depends_on"],
219:       "semantic_identity": {},
220:       "provenance_requested": "authored_world_fact|gm_inference|player_hypothesis|generated_proposal|bounded_incidental|npc_claim",
221:       "epistemic_status": "established|inferred|hypothesis|unresolved|possible",
222:       "modality": "established|possible|hypothetical|unresolved",
223:       "realization_role": "MUST_STATE|MAY_STATE|MAY_INFER|MUST_PRESERVE_UNCERTAINTY|INCIDENTAL_TEXTURE",
224:       "relation_kind": "observation|causal|evidential|epistemic_status|ordinary_predicate|gameplay_lead",
225:       "text": "short internal claim text"
226:     }
227:   ],
228:   "narration": "string",
229:   "player_facing_text": "same string as narration for temporary legacy compatibility",
230:   "tags": ["string"],
231:   "improvisation_proposals": null | [
232:     {
233:       "kind": "incidental_fact|npc_claim|consequential_proposal",
234:       "category": "sensory_detail|food_composition|mundane_service_detail|background_npc_detail|mannerism|local_color|environmental_elaboration|social_connective|ordinary_personal_detail|rumor|hearsay|uncertain_claim|speculation|opinion",
235:       "content": "string",
236:       "scope": "turn|scene|session",
237:       "consequence_level": "none|low|incidental",
238:       "source": "dm_improvisation|npc:<id>|observation",
239:       "speaker_id": null | "npc_id",
240:       "epistemic_status": null | "known|grounded|rumor|hearsay|uncertain|speculative"
241:     }
242:   ],
243:   "scene_update": null | {
244:     "visible_facts_add": ["string"],
245:     "discoverable_clues_add": ["string"],
246:     "hidden_facts_add": ["string"],
247:     "mode": "exploration|combat|social|travel"
248:   },
249:   "activate_scene_id": null | "scene_id",
250:   "new_scene_draft": null | {
251:     "id": "string",
252:     "location": "string",
253:     "summary": "string",
254:     "mode": "exploration",
255:     "visible_facts": ["string"],
256:     "discoverable_clues": ["string"],
257:     "hidden_facts": ["string"],
258:     "exits": [{"label":"string","target_scene_id":"string"}],
259:     "enemies": []
260:   },
261:   "world_updates": null | {
262:     "append_events": ["string"],
263:     "projects": [],
264:     "assets": [],
265:     "factions": [],
266:     "world_state": { "flags": {}, "counters": {}, "clocks": {} }
267:   },
268:   "suggested_action": null | {
269:     "action_type": "attack|cast_spell|skill_check|freeform|none",
270:     "attack_id": null,
271:     "spell_id": null,
272:     "skill_id": null,
273:     "target_id": null,
274:     "modifiers": []
275:   },
276:   "debug_notes": "string"
277: }
278: 
279: STRUCTURED CLAIM DECLARATION RULE:
280: Every consequential proposition intended for player-facing narration must appear in declared_claims before it appears in narration: causes, actors, event times, historical events, consequential relationships, negative evidence, specific gameplay leads, state mutation, NPC knowledge, generated inferences, and generated hypotheses. Mundane sensory texture, gestures, cadence, ordinary NPC dialogue, refusal, hesitation, and mannerism stay plain narration or incidental improvisation; they are not authored world facts. Declarations do not authorize themselves: realize existing gm_resolution_decision.realization_claims when possible; use declaration_mode "propose" only for bounded possible inference/hypothesis when the supplied decision permits inference. Do not request or imply world_truth authority for a proposal. An epistemic-status claim about a cause, actor, time, reason, or certainty must set premise_claim_ids to the propositions it depends on. Uncertainty about a premise does not establish that premise, and a hypothetical premise may be realized only conditionally. Narration must correspond to declared and accepted consequential claims, and structured metadata must never be spoken to the player.
281: 
282: BOUNDED IMPROVISATION AUTHORITY:
283: You may invent ordinary low-consequence details only by expressing them in player_facing_text AND adding a matching improvisation_proposals entry.
284: Use kind "incidental_fact" for mundane sensory/service/background details such as food composition, mannerisms, local color, ordinary refusals, and low-stakes connective social detail.
285: Use kind "npc_claim" for something a speaker reports, believes, or speculates; set epistemic_status to rumor/hearsay/uncertain/speculative unless it is grounded in supplied state.
286: Do not use bounded improvisation for mechanics, inventory changes, clues, hidden facts, secret passages, factions, major geography/history, quest-critical facts, or player decisions. Mark such attempted material as consequential_proposal rather than presenting it as truth.
287: Accepted bounded improvisation is runtime continuity only; it is not authored world truth.
288: """
289: if SYSTEM_PROMPT.count(_PR_BT_ABSTRACT_EPISTEMIC_SENTENCE) != 1:
290:     raise RuntimeError("PR-BT abstract epistemic sentence was not found exactly once")
```

### game/gm.py:3796-3988

```text
3796: def _structured_contract_failure(
3797:     form: str,
3798:     reason: str,
3799:     *,
3800:     provider_response_contract: str = "structured_realization",
3801: ) -> Dict[str, Any]:
3802:     """Model text that is not a claim envelope. It is not narration."""
3803:     normalized = form if form in {"plain", "malformed", "structured"} else "malformed"
3804:     return {
3805:         'player_facing_text': '',
3806:         'tags': ['structured_output_rejected', 'structured_contract_failure'],
3807:         'scene_update': None,
3808:         'activate_scene_id': None,
3809:         'new_scene_draft': None,
3810:         'world_updates': None,
3811:         'suggested_action': None,
3812:         'debug_notes': 'Structured realization envelope required.',
3813:         'metadata': {
3814:             'output_form': normalized,
3815:             'structured_output_rejected': True,
3816:             'structured_contract_failure': True,
3817:             'structured_contract_reason': reason,
3818:             'provider_response_contract': provider_response_contract,
3819:             'legacy_fallback': False,
3820:         },
3821:     }
3822: 
3823: 
3824: def _safe_json(
3825:     text: str,
3826:     *,
3827:     require_structured_claims: bool = False,
3828:     provider_response_contract: str = "structured_realization",
3829: ) -> Dict[str, Any]:
3830:     """Parse model text into a safe, normalized GM response dict.
3831: 
3832:     A structured response contributes only its player-facing text. The raw
3833:     envelope is never narration. An unparseable or incomplete envelope is
3834:     rejected so a later seal cannot publish it.
3835: 
3836:     ``require_structured_claims`` is the live generation path. Plain prose and
3837:     legacy player-facing JSON are structured-contract failures there. Direct
3838:     unit tests may still parse the older shapes.
3839:     """
3840:     if provider_response_contract == "narration_only":
3841:         raw = str(text or "").strip()
3842:         try:
3843:             parsed = json.loads(raw)
3844:         except json.JSONDecodeError:
3845:             return _structured_contract_failure(
3846:                 "malformed",
3847:                 "malformed_narration_only_envelope",
3848:                 provider_response_contract=provider_response_contract,
3849:             )
3850:         if not isinstance(parsed, dict):
3851:             return _structured_contract_failure(
3852:                 "malformed",
3853:                 "malformed_narration_only_envelope",
3854:                 provider_response_contract=provider_response_contract,
3855:             )
3856:         keys = {str(key) for key in parsed}
3857:         if keys != {"narration"}:
3858:             if "declared_claims" in keys:
3859:                 reason = "unexpected_declared_claims"
3860:             elif "narration" not in keys:
3861:                 reason = "missing_narration"
3862:             else:
3863:                 reason = "unexpected_narration_only_field"
3864:             return _structured_contract_failure(
3865:                 "structured",
3866:                 reason,
3867:                 provider_response_contract=provider_response_contract,
3868:             )
3869:         prose = parsed.get("narration")
3870:         if not isinstance(prose, str) or not prose.strip():
3871:             return _structured_contract_failure(
3872:                 "structured",
3873:                 "missing_narration" if prose is None else "invalid_narration",
3874:                 provider_response_contract=provider_response_contract,
3875:             )
3876:         from game.structured_player_output import text_contains_response_envelope
3877: 
3878:         if text_contains_response_envelope(prose):
3879:             return _structured_contract_failure(
3880:                 "structured",
3881:                 "nested_response_envelope",
3882:                 provider_response_contract=provider_response_contract,
3883:             )
3884:         narration = prose.strip()
3885:         return {
3886:             'player_facing_text': narration,
3887:             'tags': [],
3888:             'scene_update': None,
3889:             'activate_scene_id': None,
3890:             'new_scene_draft': None,
3891:             'world_updates': None,
3892:             'suggested_action': None,
3893:             'debug_notes': 'Parsed narration-only model output.',
3894:             'metadata': {
3895:                 'output_form': 'structured',
3896:                 'provider_response_contract': provider_response_contract,
3897:                 'realization_envelope': {
3898:                     'schema_version': 1,
3899:                     'provider_response_contract': provider_response_contract,
3900:                     'declared_claims': [],
3901:                     'narration': narration,
3902:                     'structured_contract_present': True,
3903:                     'legacy_fallback': False,
3904:                     'normalized_empty_declarations': True,
3905:                     'declaration_authorship': False,
3906:                 },
3907:             },
3908:         }
3909: 
3910:     from game.structured_player_output import classify_model_output
3911: 
3912:     classified = classify_model_output(text)
3913:     form = str(classified.get("form") or "")
3914:     if form == "malformed":
3915:         if require_structured_claims:
3916:             return _structured_contract_failure(
3917:                 "malformed",
3918:                 "malformed_envelope",
3919:                 provider_response_contract=provider_response_contract,
3920:             )
3921:         return {
3922:             'player_facing_text': '',
3923:             'tags': ['structured_output_rejected'],
3924:             'scene_update': None,
3925:             'activate_scene_id': None,
3926:             'new_scene_draft': None,
3927:             'world_updates': None,
3928:             'suggested_action': None,
3929:             'debug_notes': 'Rejected structured model envelope.',
3930:             'metadata': {'output_form': 'malformed', 'structured_output_rejected': True},
3931:         }
3932:     if form == "plain":
3933:         if require_structured_claims:
3934:             return _structured_contract_failure(
3935:                 "plain",
3936:                 "missing_structured_envelope",
3937:                 provider_response_contract=provider_response_contract,
3938:             )
3939:         prose = str(classified.get("player_facing_text") or "")
3940:         return {
3941:             'player_facing_text': prose or 'No narration provided.',
3942:             'tags': ['fallback'],
3943:             'scene_update': None,
3944:             'activate_scene_id': None,
3945:             'new_scene_draft': None,
3946:             'world_updates': None,
3947:             'suggested_action': None,
3948:             'debug_notes': 'Non-JSON response fallback.',
3949:             'metadata': {'output_form': 'plain', 'legacy_fallback': True},
3950:         }
3951: 
3952:     parsed = classified.get("fields") if isinstance(classified.get("fields"), dict) else {}
3953:     prose = str(classified.get("player_facing_text") or "")
3954:     declared_claims = parsed.get("declared_claims") if isinstance(parsed.get("declared_claims"), list) else None
3955:     if require_structured_claims and declared_claims is None:
3956:         return _structured_contract_failure(
3957:             "structured",
3958:             "missing_declared_claims",
3959:             provider_response_contract=provider_response_contract,
3960:         )
3961:     proposals = parsed.get("improvisation_proposals") if isinstance(parsed.get("improvisation_proposals"), list) else None
3962:     out: Dict[str, Any] = {
3963:         'player_facing_text': prose,
3964:         'tags': parsed.get('tags') if isinstance(parsed.get('tags'), list) else [],
3965:         'scene_update': parsed.get('scene_update') if isinstance(parsed.get('scene_update'), dict) else None,
3966:         'activate_scene_id': parsed.get('activate_scene_id') if isinstance(parsed.get('activate_scene_id'), str) else None,
3967:         'new_scene_draft': parsed.get('new_scene_draft') if isinstance(parsed.get('new_scene_draft'), dict) else None,
3968:         'world_updates': parsed.get('world_updates') if isinstance(parsed.get('world_updates'), dict) else None,
3969:         'suggested_action': parsed.get('suggested_action') if isinstance(parsed.get('suggested_action'), dict) else None,
3970:         'debug_notes': parsed.get('debug_notes') if isinstance(parsed.get('debug_notes'), str) else 'Parsed model output.',
3971:         'metadata': {
3972:             'output_form': 'structured',
3973:             'provider_response_contract': provider_response_contract,
3974:             'realization_envelope': {
3975:                 'schema_version': 1,
3976:                 'provider_response_contract': provider_response_contract,
3977:                 'declared_claims': declared_claims,
3978:                 'narration': prose,
3979:                 'structured_contract_present': declared_claims is not None,
3980:                 'legacy_fallback': False if require_structured_claims else declared_claims is None,
3981:             },
3982:         },
3983:     }
3984:     if proposals is not None:
3985:         out["improvisation_proposals"] = proposals
3986:     return out
3987: 
3988: 
```

### game/gm.py:4154-4175

```text
4154: def _provider_response_contract_from_payload(payload: Dict[str, Any]) -> str:
4155:     """Select model-facing envelope from existing decision projection only."""
4156:     try:
4157:         from game.gm_resolution_decision import (
4158:             PROVIDER_ENVELOPE_NARRATION_ONLY,
4159:             select_provider_response_envelope,
4160:         )
4161:     except Exception:
4162:         return "structured_realization"
4163:     decision = payload.get("gm_resolution_decision") if isinstance(payload.get("gm_resolution_decision"), dict) else None
4164:     contract = payload.get("resolution_contract") if isinstance(payload.get("resolution_contract"), dict) else None
4165:     selected = select_provider_response_envelope(decision, contract)
4166:     envelope = str(selected.get("selected_envelope") or "")
4167:     return PROVIDER_ENVELOPE_NARRATION_ONLY if envelope == PROVIDER_ENVELOPE_NARRATION_ONLY else "structured_realization"
4168: 
4169: 
4170: def _provider_response_contract_from_messages(messages: List[Dict[str, str]] | None) -> str:
4171:     if not isinstance(messages, list) or not messages:
4172:         return "structured_realization"
4173:     system = str((messages[0] or {}).get("content") or "")
4174:     return "narration_only" if NARRATION_ONLY_RESPONSE_CONTRACT in system else "structured_realization"
4175: 
```

### game/gm.py:4786-4817

```text
4786:             payload['instructions'] = list(payload.get('instructions', [])) + [
4787:                 'The mechanical_resolution contains resolved_combat_action with authoritative dice rolls and outcomes. '
4788:                 'Narrate the combat outcome based on the resolved result; do not invent dice rolls or override app-side resolutions.',
4789:             ]
4790:         else:
4791:             # Social or other: pass skill_check when present; GPT must only narrate, never decide success/failure
4792:             if resolution.get('skill_check'):
4793:                 from game.social import SOCIAL_KINDS
4794:                 if res_kind and res_kind in SOCIAL_KINDS:
4795:                     payload['skill_check'] = resolution['skill_check']
4796:                     payload['instructions'] = list(payload.get('instructions', [])) + [
4797:                         'The skill check was already resolved by the app (skill, roll, modifier, total, difficulty, success). '
4798:                         'NEVER decide success or failure yourself. ONLY narrate the authoritative result given.',
4799:                     ]
4800: 
4801:     if not action_outcome_mode and resolution and isinstance(resolution, dict) and resolution.get('hint'):
4802:         payload['instructions'] = list(payload['instructions']) + [resolution['hint']]
4803:     provider_response_contract = _provider_response_contract_from_payload(payload)
4804:     system_prompt = NARRATION_ONLY_SYSTEM_PROMPT if provider_response_contract == "narration_only" else SYSTEM_PROMPT
4805:     payload = _dedupe_provider_payload_instructions(payload, system_prompt)
4806:     payload = _project_harmless_social_provider_context(
4807:         payload,
4808:         provider_response_contract=provider_response_contract,
4809:     )
4810:     payload = omit_exact_duplicate_provider_contracts(payload)
4811:     payload = omit_duplicate_turn_packet_policy(payload)
4812:     return [
4813:         {'role': 'system', 'content': system_prompt},
4814:         {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}
4815:     ]
4816: 
4817: 
```

### game/gm.py:5055-5321

```text
5055: def call_gpt(
5056:     messages: List[Dict[str, str]],
5057:     *,
5058:     purpose: str = "primary_turn",
5059:     response_policy: Optional[Dict[str, Any]] = None,
5060:     segmented_turn: Optional[Dict[str, Any]] = None,
5061:     retry_attempt: int = 0,
5062:     retry_reason: Optional[str] = None,
5063:     strict_social: bool = False,
5064:     force_high_precision: bool = False,
5065: ) -> Dict[str, Any]:
5066:     # Wrap the OpenAI call so network/API/model errors do not crash gameplay.
5067:     route = resolve_model_route(
5068:         purpose=purpose,
5069:         response_policy=response_policy,
5070:         segmented_turn=segmented_turn,
5071:         retry_attempt=retry_attempt,
5072:         strict_social=strict_social,
5073:         force_high_precision=force_high_precision,
5074:     )
5075:     from game.provider_budget import (
5076:         accounting_active,
5077:         admit_request,
5078:         provider_retries_disabled,
5079:     )
5080: 
5081:     if provider_retries_disabled() and int(retry_attempt or 0) > 0:
5082:         return _attach_model_route_metadata(
5083:             {
5084:                 "player_facing_text": (
5085:                     "The action stands, and no further narration request was sent."
5086:                 ),
5087:                 "tags": ["provider_retry_disabled", "deterministic_fallback"],
5088:                 "scene_update": None,
5089:                 "activate_scene_id": None,
5090:                 "new_scene_draft": None,
5091:                 "world_updates": None,
5092:                 "suggested_action": None,
5093:                 "debug_notes": "provider_retry_disabled",
5094:                 "metadata": {"provider_retry_disabled": True},
5095:             },
5096:             selected_model=route.selected_model,
5097:             route_reason=route.route_reason,
5098:             route_family=route.route_family,
5099:             purpose=purpose,
5100:             retry_attempt=retry_attempt,
5101:             retry_reason=retry_reason,
5102:             strict_social=strict_social,
5103:             force_high_precision=force_high_precision,
5104:         )
5105:     if os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS", "").strip().lower() in {"1", "true", "yes", "on"}:
5106:         metadata = {
5107:             "provider_calls_disabled": True,
5108:             "provider_accounting": {
5109:                 "model": route.selected_model,
5110:                 "request_count": 0,
5111:                 "input_tokens": None,
5112:                 "output_tokens": None,
5113:                 "total_tokens": None,
5114:                 "latency_ms": None,
5115:                 "usage_unavailable": True,
5116:             },
5117:         }
5118:         return _attach_model_route_metadata({
5119:             "player_facing_text": (
5120:                 "Provider calls are disabled for this run, so no live narration was generated."
5121:             ),
5122:             "tags": ["provider_calls_disabled", "deterministic_fallback"],
5123:             "scene_update": None,
5124:             "activate_scene_id": None,
5125:             "new_scene_draft": None,
5126:             "world_updates": None,
5127:             "suggested_action": None,
5128:             "debug_notes": f"provider_calls_disabled:purpose={purpose}",
5129:             "metadata": metadata,
5130:         },
5131:             selected_model=route.selected_model,
5132:             route_reason=route.route_reason,
5133:             route_family=route.route_family,
5134:             purpose=purpose,
5135:             retry_attempt=retry_attempt,
5136:             retry_reason=retry_reason,
5137:             strict_social=strict_social,
5138:             force_high_precision=force_high_precision,
5139:         )
5140:     _PROVIDER_CALL_STAMP.set(
5141:         {
5142:             "purpose": str(purpose or "primary_turn"),
5143:             "sent": False,
5144:             "latency_ms": None,
5145:             "input_tokens": None,
5146:             "output_tokens": None,
5147:             "started": time.perf_counter(),
5148:         }
5149:     )
5150:     pinned_model = os.environ.get("ASHEN_PIN_PROVIDER_MODEL", "").strip()
5151:     selected_model = pinned_model or route.selected_model
5152:     narration_cap = int(os.environ.get("ASHEN_NARRATION_MAX_OUTPUT_TOKENS", "600") or "600")
5153:     estimated_input = 1
5154:     if accounting_active():
5155:         blob = json.dumps(messages, ensure_ascii=False).encode("utf-8")
5156:         estimated_input = max(1, (len(blob) // 3) + 64)
5157:     attempt = admit_request(owner="gm.call_gpt", model=selected_model, purpose=purpose or "narration", estimated_input=estimated_input, max_output=narration_cap)
5158:     refusal = attempt.refusal
5159:     if refusal:
5160:         from game.provider_budget import sdk_retry_options, PLAYTEST_STOP_MESSAGE
5161:         attempt.finish(
5162:             {
5163:                 "purpose": purpose or "narration",
5164:                 "sent": False,
5165:                 "model": selected_model,
5166:                 "input_tokens": None,
5167:                 "output_tokens": None,
5168:                 "total_tokens": None,
5169:                 "refusal": refusal,
5170:             }
5171:         )
5172:         return _attach_model_route_metadata(
5173:             {
5174:                 "player_facing_text": (
5175:                     PLAYTEST_STOP_MESSAGE if sdk_retry_options() else "The action was resolved, but live narration was not requested because it would exceed the provider budget."
5176:                 ),
5177:                 "tags": ["provider_budget_refused", "deterministic_fallback"],
5178:                 "scene_update": None,
5179:                 "activate_scene_id": None,
5180:                 "new_scene_draft": None,
5181:                 "world_updates": None,
5182:                 "suggested_action": None,
5183:                 "debug_notes": f"provider_budget_refused:{refusal}",
5184:                 "metadata": {"provider_budget_refusal": refusal},
5185:             },
5186:             selected_model=selected_model,
5187:             route_reason=route.route_reason,
5188:             route_family=route.route_family,
5189:             purpose=purpose,
5190:             retry_attempt=retry_attempt,
5191:             retry_reason=retry_reason,
5192:             strict_social=strict_social,
5193:             force_high_precision=force_high_precision,
5194:         )
5195:     request_sent = False
5196:     try:
5197:         from openai import OpenAI
5198:         from game.provider_budget import sdk_retry_options
5199:         client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds(), **sdk_retry_options())
5200:         _log_model_route(
5201:             selected_model=selected_model,
5202:             route_family=route.route_family,
5203:             purpose=purpose,
5204:             retry_attempt=retry_attempt,
5205:             retry_reason=retry_reason,
5206:             strict_social=strict_social,
5207:             force_high_precision=force_high_precision,
5208:         )
5209:         create_kwargs = {"model": selected_model, "input": messages}
5210:         if accounting_active():
5211:             create_kwargs["max_output_tokens"] = narration_cap
5212:         request_sent = True
5213:         stamp = _PROVIDER_CALL_STAMP.get()
5214:         if isinstance(stamp, dict):
5215:             stamp["sent"] = True
5216:             stamp["started"] = time.perf_counter()
5217:         resp = attempt.dispatch(client.responses.create, **create_kwargs)
5218:         if isinstance(stamp, dict):
5219:             stamp["latency_ms"] = max(0, int(round((time.perf_counter() - float(stamp.get("started") or time.perf_counter())) * 1000)))
5220:         text = getattr(resp, 'output_text', None)
5221:         if text is None:
5222:             # Fallback to stringifying the response if expected attribute missing.
5223:             text = str(resp)
5224:         usage = getattr(resp, "usage", None)
5225:         incoming = getattr(usage, "input_tokens", None) if usage is not None else None
5226:         outgoing = getattr(usage, "output_tokens", None) if usage is not None else None
5227:         total = getattr(usage, "total_tokens", None) if usage is not None else None
5228:         if isinstance(stamp, dict):
5229:             stamp["input_tokens"] = None if incoming is None else int(incoming)
5230:             stamp["output_tokens"] = None if outgoing is None else int(outgoing)
5231:         if accounting_active():
5232:             returned_model = str(getattr(resp, "model", "") or "")
5233:             attempt.finish(
5234:                 {
5235:                     "purpose": purpose or "narration",
5236:                     "sent": True,
5237:                     "configured_model": selected_model,
5238:                     "model": returned_model,
5239:                     "request_id": getattr(resp, "id", None),
5240:                     "input_tokens": None if incoming is None else int(incoming),
5241:                     "output_tokens": None if outgoing is None else int(outgoing),
5242:                     "total_tokens": None if total is None else int(total),
5243:                     "max_output_tokens": narration_cap,
5244:                     "model_mismatch": bool(pinned_model and returned_model and not returned_model.startswith(pinned_model)),
5245:                 }
5246:             )
5247:         provider_response_contract = _provider_response_contract_from_messages(messages)
5248:         return _attach_model_route_metadata(
5249:             _safe_json(
5250:                 text.strip(),
5251:                 require_structured_claims=True,
5252:                 provider_response_contract=provider_response_contract,
5253:             ),
5254:             selected_model=route.selected_model,
5255:             route_reason=route.route_reason,
5256:             route_family=route.route_family,
5257:             purpose=purpose,
5258:             retry_attempt=retry_attempt,
5259:             retry_reason=retry_reason,
5260:             strict_social=strict_social,
5261:             force_high_precision=force_high_precision,
5262:         )
5263:     except Exception as e:
5264:         stamp = _PROVIDER_CALL_STAMP.get()
5265:         if isinstance(stamp, dict):
5266:             stamp["sent"] = bool(request_sent)
5267:             started = stamp.get("started")
5268:             if isinstance(started, float):
5269:                 stamp["latency_ms"] = max(0, int(round((time.perf_counter() - started) * 1000)))
5270:         if accounting_active() and request_sent:
5271:             attempt.finish(
5272:                 {
5273:                     "purpose": purpose or "narration",
5274:                     "sent": True,
5275:                     "model": selected_model,
5276:                     "input_tokens": None,
5277:                     "output_tokens": None,
5278:                     "total_tokens": None,
5279:                     "error": type(e).__name__,
5280:                 }
5281:             )
5282:         err = _classify_upstream_gpt_error(e)
5283:         # Return a safe fallback response that preserves the expected schema so
5284:         # callers can continue without special-casing exceptions.
5285:         fallback_metadata = {
5286:             'upstream_api_error': err,
5287:         }
5288:         attach_realization_fallback_family(fallback_metadata, GPT_BUDGET_OR_PROVIDER_FAILURE)
5289:         return _attach_model_route_metadata({
5290:             'player_facing_text': 'The game master is temporarily unavailable. Please try again.',
5291:             'tags': [
5292:                 'error',
5293:                 f"gpt_api_error:{err['failure_class']}",
5294:                 'gpt_api_error_retryable' if err['retryable'] else 'gpt_api_error_nonretryable',
5295:             ],
5296:             'scene_update': None,
5297:             'activate_scene_id': None,
5298:             'new_scene_draft': None,
5299:             'world_updates': None,
5300:             'suggested_action': None,
5301:             'debug_notes': re.sub(
5302:                 r"sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+",
5303:                 "[REDACTED]",
5304:                 (
5305:                     f"call_gpt error: {repr(e)} | "
5306:                     f"api_error_class={err['failure_class']}:retryable={err['retryable']}"
5307:                 ),
5308:                 flags=re.IGNORECASE,
5309:             ),
5310:             'metadata': fallback_metadata,
5311:         },
5312:             selected_model=route.selected_model,
5313:             route_reason=route.route_reason,
5314:             route_family=route.route_family,
5315:             purpose=purpose,
5316:             retry_attempt=retry_attempt,
5317:             retry_reason=retry_reason,
5318:             strict_social=strict_social,
5319:             force_high_precision=force_high_precision,
5320:         )
5321: 
```

### game/structured_player_output.py:1-112

```text
1: """Player-facing boundary for model output.
2: 
3: A structured GM response is parsed and reduced to its player-facing text
4: before sealing. A raw envelope, or an unparseable envelope, is rejected.
5: Ordinary narration may contain braces, colons, and quotes.
6: """
7: from __future__ import annotations
8: 
9: import json
10: import re
11: 
12: _ENVELOPE_KEYS = frozenset(
13:     {
14:         "declared_claims",
15:         "narration",
16:         "player_facing_text",
17:         "improvisation_proposals",
18:         "debug_notes",
19:         "scene_update",
20:         "activate_scene_id",
21:         "new_scene_draft",
22:         "world_updates",
23:         "suggested_action",
24:     }
25: )
26: _FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
27: _KEY_RE = re.compile(
28:     r'"(?:player_facing_text|improvisation_proposals|debug_notes|scene_update|activate_scene_id|new_scene_draft|world_updates|suggested_action)"\s*:',
29: )
30: 
31: 
32: def is_response_envelope(value: object) -> bool:
33:     if not isinstance(value, dict):
34:         return False
35:     keys = {str(key) for key in value}
36:     if "declared_claims" in keys and "narration" in keys:
37:         return True
38:     if "player_facing_text" in keys:
39:         return True
40:     return len(keys & _ENVELOPE_KEYS) >= 2
41: 
42: 
43: def _iter_objects(text: str):
44:     decoder = json.JSONDecoder()
45:     index = 0
46:     while True:
47:         start = text.find("{", index)
48:         if start < 0:
49:             return
50:         try:
51:             parsed, consumed = decoder.raw_decode(text[start:])
52:         except json.JSONDecodeError:
53:             index = start + 1
54:             continue
55:         yield parsed
56:         index = start + consumed
57: 
58: 
59: def text_contains_response_envelope(text: str | None) -> bool:
60:     raw = str(text or "")
61:     if not raw.strip():
62:         return False
63:     for parsed in _iter_objects(raw):
64:         if is_response_envelope(parsed):
65:             return True
66:     return bool(_KEY_RE.search(raw) and "{" in raw)
67: 
68: 
69: def classify_model_output(text: str | None) -> dict:
70:     """Return form plain, structured, or malformed, plus extracted prose."""
71:     raw = str(text or "").strip()
72:     fenced = _FENCE_RE.match(raw)
73:     if fenced:
74:         raw = fenced.group(1).strip()
75:     if not raw:
76:         return {"form": "malformed", "player_facing_text": "", "fields": {}}
77:     try:
78:         parsed = json.loads(raw)
79:     except json.JSONDecodeError:
80:         parsed = None
81:     if isinstance(parsed, dict):
82:         if is_response_envelope(parsed):
83:             prose = parsed.get("narration") if "narration" in parsed else parsed.get("player_facing_text")
84:             if isinstance(prose, str) and prose.strip() and not text_contains_response_envelope(prose):
85:                 return {"form": "structured", "player_facing_text": prose.strip(), "fields": parsed}
86:             return {"form": "malformed", "player_facing_text": "", "fields": {}}
87:         return {"form": "malformed", "player_facing_text": "", "fields": {}}
88:     if parsed is not None:
89:         return {"form": "malformed", "player_facing_text": "", "fields": {}}
90:     if text_contains_response_envelope(raw):
91:         return {"form": "malformed", "player_facing_text": "", "fields": {}}
92:     return {"form": "plain", "player_facing_text": raw, "fields": {}}
```

### game/live_resolution.py:384-490

```text
384: def attach_interaction_obligation(
385:     resolution: dict[str, Any],
386:     *,
387:     player_text: str | None,
388:     session: Mapping[str, Any] | None = None,
389:     normalized_action: Mapping[str, Any] | None = None,
390:     scene_id: str | None = None,
391:     scene: Mapping[str, Any] | None = None,
392:     world: Mapping[str, Any] | None = None,
393:     visible_turns: Sequence[Mapping[str, Any]] | None = None,
394:     enable_model_interpretation: bool = False,
395: ) -> dict[str, Any]:
396:     if not isinstance(resolution, dict):
397:         return resolution
398:     md = resolution.setdefault("metadata", {})
399:     if not isinstance(md, dict):
400:         md = {}
401:         resolution["metadata"] = md
402:     existing = md.get("resolution_contract")
403:     if isinstance(existing, dict) and existing.get("contract_id"):
404:         # The contract is already authoritative. Do not rebuild it.
405:         # Social, movement, perception, clarification, and retry paths can
406:         # arrive here. They still need a decision that consumes this contract.
407:         existing["retry_preserved"] = True
408:         if isinstance(session, dict):
409:             from game.storage import append_debug_trace
410: 
411:             append_debug_trace(
412:                 session,
413:                 contract_trace(existing, obligation_kind=str((md.get("interaction_obligation") or {}).get("kind") or ""), retry_preserved=True),
414:             )
415:         contract_id = str(existing.get("contract_id") or "")
416:         current = md.get(DECISION_METADATA_KEY) if isinstance(md.get(DECISION_METADATA_KEY), dict) else {}
417:         if str(current.get("contract_id") or "") != contract_id:
418:             attach_gm_resolution_decision(
419:                 resolution,
420:                 session=session,
421:                 scene=scene,
422:                 world=world,
423:                 normalized_action=normalized_action,
424:             )
425:         return resolution
426:     catalog = None
427:     interpreter = None
428:     if scene is not None or world is not None or enable_model_interpretation:
429:         from game.scene_referent_catalog import build_canonical_referent_catalog
430: 
431:         catalog = build_canonical_referent_catalog(
432:             scene=scene,
433:             world=world,
434:             session=session,
435:             scene_id=scene_id,
436:         )
437:     if enable_model_interpretation:
438:         from game.semantic_interpreter import interpret_for_contract
439: 
440:         interpreter = interpret_for_contract
441:     contract = construct_resolution_contract(
442:         player_text=player_text,
443:         session=session,
444:         resolution=resolution,
445:         normalized_action=normalized_action,
446:         scene_id=scene_id,
447:         canonical_referents=catalog,
448:         model_interpreter=interpreter,
449:         visible_turns=visible_turns,
450:         scene=scene,
451:     )
452:     md["resolution_contract"] = contract.as_dict()
453:     if isinstance(session, dict):
454:         from game.incidental_entity import apply_entity_binding
455: 
456:         apply_entity_binding(resolution, session, scene_id=scene_id)
457:     decision = select_resolution_mode(
458:         player_text=player_text,
459:         scene=None,
460:         session=session,
461:         resolution=resolution,
462:         normalized_action=normalized_action,
463:     )
464:     obligation = derive_interaction_obligation(
465:         player_text=player_text,
466:         session=session,
467:         resolution=resolution,
468:         normalized_action=normalized_action,
469:         decision=decision,
470:     )
471:     md["interaction_obligation"] = {
472:         "kind": obligation.kind,
473:         "target": obligation.target,
474:         "interlocutor_id": obligation.interlocutor_id,
475:         "subject": obligation.subject,
476:         "requested_outcome": obligation.requested_outcome,
477:         "claim_id": obligation.claim_id,
478:         "resolution_mode": decision.mode,
479:         "turn_index": obligation.turn_index,
480:         "resolution_contract_id": contract.contract_id,
481:         "executable_obligations": dict(
482:             (contract.as_dict().get("construction") or {}).get("executable_obligations") or {}
483:         ),
484:     }
485:     attach_gm_resolution_decision(
486:         resolution,
487:         session=session,
488:         scene=scene,
489:         world=world,
490:         normalized_action=normalized_action,
```

### game/live_resolution.py:642-713

```text
642:     world: Mapping[str, Any] | None = None,
643:     resolution: Mapping[str, Any] | None = None,
644:     normalized_action: Mapping[str, Any] | None = None,
645:     route_choice: str | None = None,
646: ) -> ResolutionModeDecision:
647:     text = _clean_text(player_text, limit=240)
648:     low = text.lower()
649:     target_from_res, speaker = _target_from_resolution(resolution)
650:     target = _target_from_action(normalized_action) or target_from_res or _target_from_context(session) or None
651:     topic = _topic_from_text(text) or target
652:     reasons: list[str] = []
653: 
654:     res_kind = str((resolution or {}).get("kind") or "").strip().lower() if isinstance(resolution, Mapping) else ""
655:     action_type = str((normalized_action or {}).get("type") or "").strip().lower() if isinstance(normalized_action, Mapping) else ""
656:     if res_kind in {"attack", "spell", "skill_check", "enemy_attack", "initiative"} or action_type == "attack":
657:         return ResolutionModeDecision(AUTHORITATIVE_MECHANICAL_ACTION, ["mechanical_resolution"], target, speaker, topic)
658: 
659:     if _CONSEQUENTIAL_RE.search(low):
660:         return ResolutionModeDecision(UNSUPPORTED_CONSEQUENTIAL_REQUEST, ["consequential_terms"], target, speaker, topic)
661: 
662:     if _MECHANICAL_RE.search(low) and not (_SERVICE_RE.search(low) and _QUESTION_RE.search(low)):
663:         return ResolutionModeDecision(AUTHORITATIVE_MECHANICAL_ACTION, ["mechanical_or_economy_terms"], target, speaker, topic)
664: 
665:     if _NPC_CLAIM_RE.search(low):
666:         return ResolutionModeDecision(
667:             NPC_CLAIM_RESPONSE,
668:             ["npc_claim_or_epistemic_question"],
669:             target,
670:             speaker,
671:             topic,
672:             NPC_CLAIM_KIND,
673:             "rumor",
674:             "hearsay",
675:         )
676: 
677:     if _QUESTION_RE.search(low) and _has_grounded_answer(text, scene):
678:         return ResolutionModeDecision(GROUNDED_INFORMATION_REQUEST, ["authored_topic_overlap"], target, speaker, topic)
679: 
680:     if _INCIDENTAL_DESCRIPTION_RE.search(low):
681:         return ResolutionModeDecision(
682:             BOUNDED_IMPROVISABLE_REQUEST,
683:             ["incidental_description_gap"],
684:             target,
685:             speaker,
686:             topic,
687:             INCIDENTAL_KIND,
688:             "sensory_detail",
689:         )
690: 
691:     if _QUESTION_RE.search(low) and _SERVICE_RE.search(low):
692:         return ResolutionModeDecision(
693:             BOUNDED_IMPROVISABLE_REQUEST,
694:             ["mundane_service_gap"],
695:             target,
696:             speaker,
697:             topic,
698:             INCIDENTAL_KIND,
699:             "mundane_service_detail",
700:         )
701: 
702:     if _PHYSICAL_ACTION_RE.search(low):
703:         return ResolutionModeDecision(AUTHORITATIVE_MECHANICAL_ACTION, ["physical_affordance_action"], target, speaker, topic)
704: 
705:     if _QUESTION_RE.search(low) and not target:
706:         return ResolutionModeDecision(CLARIFICATION_TARGET_FAILURE, ["question_without_bound_target"], None, speaker, topic)
707: 
708:     return ResolutionModeDecision(GROUNDED_INFORMATION_REQUEST, reasons or ["default_existing_resolution"], target, speaker, topic)
709: 
710: 
711: def select_resolution_mode(
712:     *,
713:     player_text: str | None,
```

### game/resolution_contract.py:1328-1341

```text
1328: 
1329:     if _looks_like_local_observation_question(text):
1330:         return REQUEST_INQUIRY, OP_PERCEIVE
1331:     # Questions, requests, and quoted speech stay inquiries.
1332:     # Waits, descriptions, scene-orientation, and unmatched statements do not
1333:     # become asks, so they are not answered as NPC dialogue or incomplete acts.
1334:     if _social_or_inquiry_operation(text):
1335:         return REQUEST_INQUIRY, OP_ASK
1336:     return REQUEST_ACTION, "unresolved"
1337: 
1338: 
1339: def construct_resolution_contract(
1340:     *,
1341:     player_text: str | None,
```

### game/resolution_contract.py:1380-1415

```text
1380:     provenance, target, discourse, ambiguous, referent_reason = _resolve_referent(
1381:         text,
1382:         dimensions=dimensions,
1383:         focus=focus,
1384:         explicit_target=explicit,
1385:     )
1386:     action_type = ""
1387:     if isinstance(normalized_action, Mapping):
1388:         action_type = str(normalized_action.get("type") or "").strip().lower()
1389:     request_kind, operation = _operation(text, dimensions, action_type=action_type)
1390:     unresolved_anaphor = provenance == PROVENANCE_UNRESOLVED and bool(_ANAPHOR_RE.search(text))
1391:     clear_claim_question = referent_reason == "claim_unresolved" and bool(set(dimensions) & CLAIM_DIMENSIONS)
1392:     if (ambiguous or unresolved_anaphor) and not clear_claim_question:
1393:         request_kind = REQUEST_CLARIFICATION
1394:         expected = EXPECT_CLARIFICATION
1395:     elif _CONSEQUENTIAL_RE.search(text):
1396:         expected = EXPECT_REFUSAL
1397:     elif operation in {OP_ACT, OP_FOLLOW, OP_CONFIRM}:
1398:         expected = EXPECT_ACTION
1399:     else:
1400:         expected = EXPECT_ANSWER
1401:     if ambiguous:
1402:         provenance = PROVENANCE_AMBIGUOUS
1403:     if _CONSEQUENTIAL_RE.search(text):
1404:         epistemic = EPISTEMIC_CONSEQUENTIAL
1405:     elif set(dimensions) & {DIM_SOURCE, DIM_CONFIDENCE}:
1406:         epistemic = EPISTEMIC_NPC_CLAIM
1407:     elif set(dimensions) & PERCEPTION_DIMENSIONS:
1408:         epistemic = EPISTEMIC_INCIDENTAL
1409:     elif set(dimensions) & CLAIM_DIMENSIONS or re.search(r"\b(?:rumou?rs?|heard)\b", text, re.IGNORECASE):
1410:         epistemic = EPISTEMIC_NPC_CLAIM
1411:     elif operation in {OP_ACT, OP_FOLLOW} and not (set(dimensions) & PERCEPTION_DIMENSIONS):
1412:         epistemic = EPISTEMIC_AUTHORITATIVE
1413:     else:
1414:         epistemic = EPISTEMIC_UNKNOWN
1415: 
```

### game/immutable_valid_response.py:800-818

```text
800:     for reason in reasons:
801:         if reason not in ordered:
802:             ordered.append(reason)
803:     hard_valid = not ordered
804:     return {
805:         "hard_valid": hard_valid,
806:         "reasons": ordered,
807:         "soft_flags": soft,
808:         "speaker": speaker,
809:         "addressee": addressee,
810:         "operation": operation,
811:         "interaction_complete": "interaction_incomplete" not in ordered and "malformed_or_truncated" not in ordered,
812:         "contract_satisfying": hard_valid,
813:         "authority": authority,
814:         "gm_resolution_decision_audit": decision_audit,
815:     }
816: 
817: 
818: _NARRATION_ONLY_RETRY_SHAPE = (
```

### game/immutable_valid_response.py:974-1034

```text
974: def safe_nonresolution(
975:     contract: Mapping[str, Any] | None,
976:     *,
977:     resolution: Mapping[str, Any] | None = None,
978:     visible_facts: list[str] | None = None,
979:     player_text: str | None = None,
980: ) -> str:
981:     """Last resort. No new topic, no player-text splice, no switched speaker."""
982:     from game.interaction_completion import generic_ask_completion
983: 
984:     operation = _operation(contract)
985:     construction = (contract or {}).get("construction") if isinstance(contract, Mapping) else {}
986:     authorization = construction.get("conversational_authorization") if isinstance(construction, Mapping) else {}
987:     if isinstance(authorization, Mapping) and authorization.get("mutation_eligibility") is False and (
988:         authorization.get("operation_eligibility") == "requires_clarification"
989:         or authorization.get("target_resolution") in {"ambiguous", "unresolved"}
990:     ):
991:         clarification = str(authorization.get("clarification") or "").strip()
992:         return clarification or "Which person do you mean? Nothing has been attempted."
993:     player = str(player_text or (contract or {}).get("raw_input") or "")
994:     requested = [name for name in _player_sensory_dimensions(player) if name in _DIMENSION_LEXICON]
995:     success = _mechanical_success(resolution)
996:     social = resolution.get("social") if isinstance(resolution, Mapping) else None
997:     if (operation == "ask" and isinstance(social, Mapping) and social.get("target_resolved") is True
998:             and social.get("npc_id") == (contract or {}).get("interlocutor_id")):
999:         authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else {}
1000:         authored_line = str(authority.get("player_line") or "").strip()
1001:         label = str(social.get("npc_name") or "").strip()
1002:         if authored_line:
1003:             return authored_line
1004:         if authority and label:
1005:             from game.dialogue_authority import _player_line
1006: 
1007:             return _player_line(label, str(authority.get("knowledge_posture") or "unknown"), "")
1008:         if label:
1009:             return f'{label} says, "I cannot answer that from what is settled here."'
1010:     if operation in {"inspect", "perceive"} and len(requested) == 1:
1011:         token = str(requested[0] or "").strip().lower()
1012:         if re.fullmatch(r"[a-z][a-z ]{2,40}", token):
1013:             return f"The inspection establishes no further reliable detail about the {token}."
1014:         return INSPECT_SAFE_LINE
1015:     if operation in {"inspect", "perceive"}:
1016:         return INSPECT_SAFE_LINE
1017:     if success is False:
1018:         line = ACTION_FAILED_LINE
1019:     elif operation in {"inspect", "perceive"}:
1020:         fact = next((str(item).strip() for item in (visible_facts or []) if str(item).strip()), "")
1021:         line = fact or INSPECT_SAFE_LINE
1022:     elif operation in {"act", "follow", "confirm"}:
1023:         line = ACTION_INCOMPLETE_LINE
1024:     elif _unresolved_explicit_addressee(contract):
1025:         line = "The person you addressed cannot be identified clearly enough to answer."
1026:     elif isinstance(contract, Mapping) and contract.get("ambiguous") and not _contract_label(contract):
1027:         line = CLARIFICATION_LINE
1028:     else:
1029:         line = generic_ask_completion(contract)
1030:     if player_utterance_in_line(line, player_text) or _label_repeats_player(line, player_text):
1031:         line = "No one here can answer that from what is settled here."
1032:     return line
1033: 
1034: 
```

### game/immutable_valid_response.py:1057-1070

```text
1057: def lifecycle_applies(resolution: Mapping[str, Any] | None) -> bool:
1058:     if not isinstance(resolution, Mapping):
1059:         return False
1060:     if str(resolution.get("kind") or "").strip().lower() == "scene_opening":
1061:         return False
1062:     contract = _contract_from_resolution(resolution)
1063:     operation = str(contract.get("operation") or "").strip()
1064:     # Ordinary unmatched narration is not an owed answer or action. Sealing it
1065:     # before the existing question and scene-stall retry loop would hide those
1066:     # failures. Social, inspection, and world-action contracts still seal.
1067:     if operation == "unresolved" and not str(contract.get("interlocutor_id") or "").strip():
1068:         return False
1069:     return bool(operation)
1070: 
```

### game/immutable_valid_response.py:1620-1754

```text
1620:     present_addressee: str = "",
1621:     dead_actor_labels: list[str] | None = None,
1622:     visible_facts: list[str] | None = None,
1623: ) -> dict[str, Any]:
1624:     """Generate is already done. Validate, preserve, or retry once."""
1625:     if not isinstance(gm, dict):
1626:         return gm
1627:     adopted = adopt_host_speech(gm, resolution=resolution, player_text=player_text, session=session, world=world)
1628:     if adopted is not None:
1629:         return adopted
1630:     contract = _contract_from_resolution(resolution)
1631:     try:
1632:         from game.gm_resolution_decision import decision_from_resolution
1633: 
1634:         gm_decision = decision_from_resolution(resolution)
1635:     except Exception:
1636:         gm_decision = {}
1637:     catalog = referents if referents is not None else _referents_for(resolution, scene, world, session)
1638:     corpus = authored_corpus or _authored_corpus(scene)
1639:     facts = visible_facts if visible_facts is not None else _visible_facts(scene)
1640:     player = str(player_text or contract.get("raw_input") or "")
1641:     gm = _project_authorized_social_answer_before_seal(
1642:         gm,
1643:         resolution=resolution,
1644:         player_text=player,
1645:         scene=scene,
1646:         world=world,
1647:         session=session,
1648:     )
1649:     if isinstance(resolution, Mapping) and not isinstance(resolution.get("social"), Mapping):
1650:         # Preserve resolver observations before validation, never by overwriting
1651:         # an already adopted generic sentence downstream.
1652:         from game.api_turn_support import _authoritative_resolution_fact_text, _looks_like_generic_resolution_fallback
1653: 
1654:         fact, _source = _authoritative_resolution_fact_text(resolution=resolution, scene=scene, world=world)
1655:         if fact:
1656:             # This is the selected public resolver result, not a provider fact
1657:             # or the complete (possibly hidden) clue catalog.
1658:             corpus = corpus + "\n" + fact
1659:             if _source.get("source") == "clue_text" and gm_decision:
1660:                 selected = str(resolution.get("clue_text") or "").strip()
1661:                 if not selected:
1662:                     selected = " ".join(str(item) for item in resolution.get("discovered_clues") or [])
1663:                 if selected:
1664:                     gm_decision = copy.deepcopy(gm_decision)
1665:                     gm_decision.setdefault("proposed_facts", []).append({
1666:                         "text": selected, "provenance": "authored_world_fact", "consequence": "consequential",
1667:                         "authorized": True, "authority": "world_truth", "persistence": "do_not_persist",
1668:                         "source_ref": "resolution.clue_text", "outcome_classification": "established_or_retrieved",
1669:                         "reason_codes": ["resolver_selected_public_clue"], "semantic_identity": {}})
1670:         if _looks_like_generic_resolution_fallback(str(gm.get("player_facing_text") or "")):
1671:             if fact:
1672:                 gm = {**gm, "player_facing_text": fact}
1673: 
1674:     def _check(candidate: dict[str, Any]) -> dict[str, Any]:
1675:         candidate_meta = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
1676:         realization_envelope = (
1677:             candidate_meta.get("realization_envelope")
1678:             if isinstance(candidate_meta.get("realization_envelope"), Mapping)
1679:             else {}
1680:         )
1681:         declared = (
1682:             realization_envelope.get("declared_claims")
1683:             if isinstance(realization_envelope.get("declared_claims"), list)
1684:             else None
1685:         )
1686:         verdict = validate_generated_response(
1687:             str(candidate.get("player_facing_text") or ""),
1688:             contract=contract,
1689:             decision=gm_decision or None,
1690:             declared_claims=declared,
1691:             player_text=player,
1692:             resolution=resolution,
1693:             referents=catalog,
1694:             authored_corpus=corpus,
1695:             present_addressee=present_addressee,
1696:             dead_actor_labels=dead_actor_labels,
1697:         )
1698:         leak_reasons = []
1699:         if isinstance(candidate_meta, Mapping):
1700:             leak_reasons = list(candidate_meta.get("content_leak_reasons") or [])
1701:         if _unsupported_perception(
1702:             str(candidate.get("player_facing_text") or ""),
1703:             resolution=resolution,
1704:             scene=scene,
1705:             world=world,
1706:             session=session,
1707:         ):
1708:             reasons = list(verdict.get("reasons") or [])
1709:             if "consequential_invention" not in reasons:
1710:                 reasons.append("consequential_invention")
1711:             verdict = {
1712:                 **verdict,
1713:                 "hard_valid": False,
1714:                 "reasons": reasons,
1715:                 "contract_satisfying": False,
1716:             }
1717:         if leak_reasons:
1718:             reasons = list(verdict.get("reasons") or [])
1719:             if "hidden_information" not in reasons:
1720:                 reasons.append("hidden_information")
1721:             verdict = {
1722:                 **verdict,
1723:                 "hard_valid": False,
1724:                 "reasons": reasons,
1725:                 "contract_satisfying": False,
1726:             }
1727:         if isinstance(candidate_meta, Mapping) and candidate_meta.get("structured_contract_failure"):
1728:             reasons = list(verdict.get("reasons") or [])
1729:             if "structured_contract_failure" not in reasons:
1730:                 reasons.append("structured_contract_failure")
1731:             verdict = {
1732:                 **verdict,
1733:                 "hard_valid": False,
1734:                 "reasons": reasons,
1735:                 "contract_satisfying": False,
1736:             }
1737:         return verdict
1738: 
1739:     first = _check(gm)
1740:     metadata = gm.setdefault("metadata", {})
1741:     if isinstance(metadata, dict):
1742:         metadata["hard_validation_attempt_1"] = {
1743:             "hard_valid": first["hard_valid"],
1744:             "reasons": list(first["reasons"]),
1745:             "soft_flags": list(first["soft_flags"]),
1746:             "text": str(gm.get("player_facing_text") or "")[:2000],
1747:         }
1748:     review: dict[str, Any] = {
1749:         "governing_decision_contract_id": str((gm_decision or {}).get("contract_id") or ""),
1750:         "outcome_classification": str((gm_decision or {}).get("outcome_classification") or ""),
1751:         "attempt_1": {
1752:             "text": str(gm.get("player_facing_text") or "")[:2000],
1753:             "reasons": list(first.get("reasons") or []),
1754:             "gm_resolution_decision_audit": first.get("gm_resolution_decision_audit"),
```

### game/immutable_valid_response.py:1975-2090

```text
1975:     def _bounded_keep(candidate_text: str) -> tuple[str, dict[str, Any]] | None:
1976:         from game.gm_resolution_decision import preservation_structure_valid, structural_narration_units
1977: 
1978:         source_verdict = _check({"player_facing_text": candidate_text})
1979:         source_audit = source_verdict.get("gm_resolution_decision_audit")
1980:         if not isinstance(source_audit, Mapping) or not source_audit.get("violations"):
1981:             return None
1982:         safe_units: list[str] = []
1983:         for unit in structural_narration_units(candidate_text):
1984:             unit_verdict = _check({"player_facing_text": unit})
1985:             if unit_verdict.get("hard_valid"):
1986:                 safe_units.append(unit)
1987:         kept = " ".join(safe_units).strip()
1988:         if not kept or kept == str(candidate_text or "").strip() or not preservation_structure_valid(kept):
1989:             return None
1990:         # C18: this exact post-deletion string, not the source audit, governs sealing.
1991:         checked = _check({"player_facing_text": kept})
1992:         if not checked.get("hard_valid"):
1993:             return None
1994:         return kept, checked
1995: 
1996:     def _terminal_after_fidelity(reasons: list[str]) -> tuple[str, str]:
1997:         from game.gm_resolution_decision import authorized_observation_line
1998:         from game.social import format_authored_knowledge_realization_line
1999: 
2000:         social = resolution.get("social") if isinstance(resolution, Mapping) else None
2001:         topic = social.get("topic_revealed") if isinstance(social, Mapping) else None
2002:         topic_text = str((topic or {}).get("text") or (topic or {}).get("clue_text") or "").strip()
2003:         if topic_text:
2004:             projected = format_authored_knowledge_realization_line(
2005:                 dict(resolution) if isinstance(resolution, Mapping) else {},
2006:                 topic_text,
2007:             )
2008:             if projected.strip():
2009:                 checked = _check({"player_facing_text": projected})
2010:                 if checked.get("hard_valid"):
2011:                     return projected, "authored_answer_projection"
2012: 
2013:         if "unauthorized_resolution_decision_fact" in reasons:
2014:             realized = authorized_observation_line(gm_decision, player)
2015:             generic = "No one here can answer that from what is settled here."
2016:             if realized and realized.strip() != generic:
2017:                 checked = _check({"player_facing_text": realized})
2018:                 if checked.get("hard_valid"):
2019:                     return realized, "authorized_observation"
2020:         return (
2021:             safe_nonresolution(contract, resolution=resolution, visible_facts=facts, player_text=player),
2022:             "safe_nonresolution",
2023:         )
2024: 
2025:     recovered = _incidental_quote_recovery(str(gm.get("player_facing_text") or ""))
2026:     if recovered is not None:
2027:         line, checked = recovered
2028:         sealed = seal_accepted_response(
2029:             gm,
2030:             text=line,
2031:             provenance=PROVENANCE_INITIAL,
2032:             attempt=1,
2033:             validation=checked,
2034:             contract=contract,
2035:             player_text=player,
2036:             resolution=resolution,
2037:         )
2038:         return _finish(sealed, why="incidental_quote_recovery")
2039: 
2040:     if regenerate is None:
2041:         bounded = (
2042:             None
2043:             if candidate_entered_structured_envelope_path(gm)
2044:             else _bounded_keep(str(gm.get("player_facing_text") or ""))
2045:         )
2046:         if bounded is not None:
2047:             kept, checked = bounded
2048:             sealed = seal_accepted_response(
2049:                 gm,
2050:                 text=kept,
2051:                 provenance=PROVENANCE_INITIAL,
2052:                 attempt=1,
2053:                 validation=checked,
2054:                 contract=contract,
2055:                 player_text=player,
2056:                 resolution=resolution,
2057:             )
2058:             return _finish(sealed, why="bounded_sentence_preservation")
2059:         line, why = _terminal_after_fidelity(list(first.get("reasons") or []))
2060:         safe_validation = _check({"player_facing_text": line})
2061:         if not safe_validation.get("hard_valid"):
2062:             gm["player_facing_text"] = "I cannot provide a validated response to that request."
2063:             return _finish(mark_candidate_rejected(gm, gm["player_facing_text"],
2064:                                                    list(safe_validation.get("reasons") or [])),
2065:                            why="controlled_validation_failure")
2066:         sealed = seal_accepted_response(
2067:             gm,
2068:             text=line,
2069:             provenance=PROVENANCE_SAFE,
2070:             attempt=1,
2071:             validation=safe_validation,
2072:             contract=contract,
2073:             player_text=player,
2074:             resolution=resolution,
2075:         )
2076:         return _finish(sealed, why=why)
2077: 
2078:     regenerated = regenerate(feedback)
2079:     if not isinstance(regenerated, dict):
2080:         regenerated = {"player_facing_text": "", "metadata": {}}
2081:     second = _check(regenerated)
2082:     review["attempt_2"] = {
2083:         "text": str(regenerated.get("player_facing_text") or "")[:2000],
2084:         "reasons": list(second.get("reasons") or []),
2085:         "gm_resolution_decision_audit": second.get("gm_resolution_decision_audit"),
2086:     }
2087:     second_meta = regenerated.setdefault("metadata", {})
2088:     if isinstance(second_meta, dict):
2089:         second_meta["hard_validation_attempt_1"] = metadata.get("hard_validation_attempt_1") if isinstance(metadata, dict) else {}
2090:         second_meta["hard_validation_attempt_2"] = {
```

### game/gm_retry.py:2511-2610

```text
2511:     return out
2512: 
2513: 
2514: def _nonsocial_minimal_resolution_line(*, session: Dict[str, Any] | None) -> str:
2515:     """Conservative forward beat for empty non-social GM text; may anchor to on-disk scene template facts."""
2516:     sess = session if isinstance(session, dict) else None
2517:     if not sess:
2518:         return _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
2519:     sid = str(sess.get("active_scene_id") or "").strip()
2520:     if not sid:
2521:         return _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
2522:     try:
2523:         env = get_effective_scene(sess, sid)
2524:     except (OSError, ValueError, TypeError, json.JSONDecodeError):
2525:         env = {}
2526:     if not isinstance(env, dict):
2527:         env = {}
2528:     if sess.get("campaign_started") is not True:
2529:         try:
2530:             from game.opening_visible_fact_selection import select_opening_narration_visible_facts
2531: 
2532:             inner = env.get("scene") if isinstance(env.get("scene"), dict) else env
2533:             curated = select_opening_narration_visible_facts(inner if isinstance(inner, dict) else {})
2534:             if curated and isinstance(inner, dict):
2535:                 env = {**env, "scene": {**inner, "visible_facts": curated}}
2536:         except Exception:
2537:             pass
2538:     detail = _first_scene_repair_anchor_detail(env)
2539:     if detail:
2540:         lead = detail[0].upper() + (detail[1:] if len(detail) > 1 else "")
2541:         return _ensure_terminal_punctuation(
2542:             f"{lead} still frames what you can see; the moment invites your next move."
2543:         )
2544:     seed = f"{sid}|nonsocial_empty_resolution_repair"
2545:     idx = _stable_u32_from_seed(seed) % 2
2546:     alts = (
2547:         str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip(),
2548:         "The air settles into a clear beat—time to commit to your next step.",
2549:     )
2550:     return _ensure_terminal_punctuation(alts[idx])
2551: 
2552: 
2553: def ensure_minimal_nonsocial_resolution(
2554:     *,
2555:     gm: Dict[str, Any] | None,
2556:     session: Dict[str, Any] | None,
2557: ) -> Dict[str, Any]:
2558:     """
2559:     Return a minimally valid non-social GM payload when narration is empty or structurally unusable.
2560:     Does not invent NPCs or clues; may reference visible_facts from the active scene template only.
2561:     """
2562:     out: Dict[str, Any] = copy.deepcopy(gm) if isinstance(gm, dict) else {}
2563:     hard_line = _ensure_terminal_punctuation(str(_NONSOCIAL_EMPTY_REPAIR_HARD_LINE).strip())
2564:     ctx_mode_ns = ""
2565:     if not _gm_has_usable_player_facing_text(out):
2566:         line = _gm_binding()._nonsocial_minimal_resolution_line(session=session)
2567:         bad = (
2568:             not isinstance(line, str)
2569:             or not line.strip()
2570:             or _gm_binding().is_route_illegal_global_or_sanitizer_fallback_text(line)
2571:             or _is_placeholder_only_player_facing_text(line)
2572:         )
2573:         need_ctx = bad or _player_facing_text_same_line(line, hard_line)
2574:         if need_ctx:
2575:             c_line, ctx_mode_ns = _contextual_nonsocial_repair_line(gm=out, session=session)
2576:             if _gm_has_usable_player_facing_text({"player_facing_text": c_line}):
2577:                 line = c_line
2578:             else:
2579:                 line = hard_line
2580:                 ctx_mode_ns = "hard_fallback"
2581:         out["player_facing_text"] = line
2582:     if not _gm_has_usable_player_facing_text(out):
2583:         out["player_facing_text"] = hard_line
2584:         ctx_mode_ns = "hard_fallback"
2585: 
2586:     existing_route = str(out.get("final_route") or "").strip()
2587:     if existing_route and existing_route not in _SOCIAL_EXCLUSIVE_FINAL_ROUTES_FOR_NONSOCIAL_REPAIR:
2588:         out["final_route"] = existing_route
2589:     else:
2590:         out["final_route"] = "nonsocial_fallback_minimal"
2591:     out["fallback_kind"] = "nonsocial_empty_resolution_repair"
2592:     out["accepted_via"] = "nonsocial_resolution_repair"
2593:     out["targeted_retry_terminal"] = True
2594:     out["retry_exhausted"] = True
2595: 
2596:     tags = out.get("tags") if isinstance(out.get("tags"), list) else []
2597:     tag_list = [str(t) for t in tags if isinstance(t, str)]
2598:     for extra in ("nonsocial_empty_resolution_repair", "retry_exhausted"):
2599:         if extra not in tag_list:
2600:             tag_list.append(extra)
2601:     out["tags"] = tag_list
2602: 
2603:     dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
2604:     repair_note = "nonsocial_empty_resolution_repair:terminal non-social resolution repair"
2605:     dbg_suffix = repair_note
2606:     if ctx_mode_ns:
2607:         dbg_suffix = f"{repair_note}|nonsocial_contextual_repair:{ctx_mode_ns}"
2608:     out["debug_notes"] = (dbg + " | " if dbg else "") + dbg_suffix
2609:     return out
2610: 
```

### game/final_emission_gate.py:79-106

```text
79: 
80: 
81: def apply_final_emission_gate(
82:     gm_output: Dict[str, Any],
83:     *,
84:     resolution: Dict[str, Any] | None,
85:     session: Dict[str, Any] | None,
86:     scene_id: str,
87:     scene: Dict[str, Any] | None = None,
88:     world: Dict[str, Any] | None = None,
89: ) -> Dict[str, Any]:
90:     """Hard legal-state gate for the final emitted text.
91: 
92:     Orchestrates in-module policy layers with :mod:`game.final_emission_validators`,
93:     :mod:`game.final_emission_repairs`, and sanitizer/strict-social integration; see module
94:     docstring for ownership boundaries.
95:     """
96:     if not isinstance(gm_output, dict):
97:         return gm_output
98:     from game.immutable_valid_response import leave_text_unchanged
99: 
100:     if leave_text_unchanged(gm_output, "apply_final_emission_gate"):
101:         return gm_output
102:     _ctx = initialize_gate_execution_context(
103:         gm_output,
104:         resolution=resolution,
105:         session=session,
106:         scene_id=scene_id,
```

### game/final_emission_validators.py:312-331

```text
312: def candidate_satisfies_scene_opening_contract(text: str) -> tuple[bool, List[str]]:
313:     clean = _normalize_text(text)
314:     if not clean:
315:         return False, ["scene_opening_empty"]
316:     low = clean.lower()
317:     if is_route_illegal_global_or_sanitizer_fallback_text(clean):
318:         return False, ["scene_opening_generic_fallback_text"]
319:     if any(p.search(clean) for p in _ANSWER_FILLER_PATTERNS):
320:         return False, ["scene_opening_generic_fallback_text"]
321:     if re.search(r"\b(?:the scene holds|voices shift around you|insufficient context|not established)\b", low):
322:         return False, ["scene_opening_generic_fallback_text"]
323:     if not re.search(
324:         r"\b(?:you|gate|district|market|lane|road|square|yard|bridge|dock|pier|tavern|hall|ward|street|"
325:         r"rain|mist|crowd|guards?|refugees?|wagons?|torchlight|notice board)\b",
326:         low,
327:     ):
328:         return False, ["scene_opening_not_scene_establishing"]
329:     if clean.endswith("?"):
330:         return False, ["scene_opening_is_question"]
331:     return True, []
```

### game/api_turn_support.py:665-686

```text
665:             "mismatch_repairs_applied": [],
666:             "repaired_discovered_clue_texts": [],
667:         }
668:     from game.immutable_valid_response import accepted_record, restore_accepted_text, run_preserve_if_valid
669: 
670:     if (isinstance(resolution, dict) and isinstance(resolution.get("social"), dict)
671:             and accepted_record(gm) is None):
672:         # Legacy retry/fallback constructors can discard an earlier adoption.
673:         # They must re-enter the same complete decision path before delivery.
674:         contract = (resolution.get("metadata") or {}).get("resolution_contract") or {}
675:         gm = run_preserve_if_valid(gm, regenerate=None, resolution=resolution,
676:             player_text=str(contract.get("raw_input") or resolution.get("prompt") or ""),
677:             session=session, scene=scene, world=world)
678:     restore_accepted_text(gm)
679:     gm_out = dict(gm)
680:     gm_out = attach_bounded_improvisation_evaluation(
681:         gm_out,
682:         session=session,
683:         scene=scene,
684:         world=world,
685:         resolution=resolution if isinstance(resolution, dict) else None,
686:     )
```

### game/provider_budget.py:42-82

```text
42: def _truthy(name: str) -> bool:
43:     return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}
44: 
45: 
46: def provider_calls_disabled() -> bool:
47:     return _truthy("ASHEN_DISABLE_PROVIDER_CALLS")
48: 
49: 
50: def provider_retries_disabled() -> bool:
51:     return _truthy("ASHEN_DISABLE_PROVIDER_RETRIES")
52: 
53: 
54: def sdk_retry_options() -> dict[str, int]:
55:     """Opt-in constructor options; leave the SDK's ordinary default untouched."""
56:     return {"max_retries": 0} if _truthy("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES") else {}
57: 
58: 
59: def playtest_stop_reason() -> str:
60:     """Non-reserving submission gate, supplemental to atomic request admission."""
61:     if not sdk_retry_options() or not accounting_active():
62:         return ""
63:     with _LOCK:
64:         ceiling = limits()
65:         if _STOPPED:
66:             return _STOP_REASON
67:         return "request ceiling" if ceiling and _REQUESTS >= ceiling[0] else ""
68: 
69: 
70: PLAYTEST_STOP_MESSAGE = "The controlled playtest request limit has been reached. Stop and export diagnostics; do not restart to continue this session."
71: 
72: 
73: def accounting_active() -> bool:
74:     return bool(os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT", "").strip() or
75:                 os.environ.get("ASHEN_PROVIDER_USAGE_PATH", "").strip())
76: 
77: 
78: def limits() -> tuple[int, int, int, int] | None:
79:     raw = os.environ.get("ASHEN_PROVIDER_REQUEST_LIMIT", "").strip()
80:     if not raw:
81:         return None
82:     return (int(raw), int(os.environ.get("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", "8000")),
```

### game/provider_budget.py:214-255

```text
214:     def finish(self, record: dict[str, Any]) -> dict[str, Any]:
215:         global _INPUT, _OUTPUT, _RESERVED_INPUT, _RESERVED_OUTPUT, _USAGE_KNOWN
216:         with _LOCK:
217:             if self.completed is not None:
218:                 if record.get("model_mismatch") and self.active:
219:                     _stop("provider returned a different model")
220:                 return dict(self.completed)  # Multiple observers, one completion.
221:             incoming, outgoing, total = (record.get(k) for k in ("input_tokens", "output_tokens", "total_tokens"))
222:             consistent = all(type(v) is int and v >= 0 for v in (incoming, outgoing, total)) and total == incoming + outgoing
223:             if not consistent:
224:                 incoming = outgoing = total = None
225:             stored = {**self._event("completed"), "sent": self.dispatched,
226:                       "request_id": record.get("request_id") if isinstance(record.get("request_id"), str) else None,
227:                       "model": record.get("model") if isinstance(record.get("model"), str) else self.model,
228:                       "input_tokens": incoming, "output_tokens": outgoing, "total_tokens": total,
229:                       "usage_consistent": consistent, "refusal": self.refusal or None,
230:                       "completion_status": record.get("completion_status") or ("completed" if self.dispatched else "not_dispatched"),
231:                       "dispatch_attempted": self.dispatched,
232:                       "latency_ms": round((time.perf_counter() - self.dispatch_started) * 1000, 3) if self.dispatched else None}
233:             if record.get("error"):
234:                 # Never persist provider exception messages or request content.
235:                 stored["error"] = "provider_error"
236:             if record.get("model_mismatch"):
237:                 stored["model_mismatch"] = True
238:             # A failed durable completion must not be applied twice if an owner
239:             # observes the accounting exception and calls finish again.
240:             self.completed = stored
241:             if self.active and not self.refusal:
242:                 _RESERVED_INPUT -= self.estimated_input
243:                 _RESERVED_OUTPUT -= self.max_output
244:                 if self.dispatched and not consistent:
245:                     _USAGE_KNOWN = False
246:                     _stop("provider usage accounting unavailable")
247:                 elif consistent:
248:                     _INPUT += incoming
249:                     _OUTPUT += outgoing
250:                     ceiling = limits()
251:                     if ceiling and (_INPUT > ceiling[1] or _OUTPUT > ceiling[2] or _INPUT + _OUTPUT > ceiling[3]):
252:                         _stop("provider budget exceeded after a completed request")
253:                 if record.get("model_mismatch"):
254:                     _stop("provider returned a different model")
255:                 try:
```

### game/world.py:258-367

```text
258: 
259: def _tick_advance_factions_one_step(
260:     world: Dict[str, Any], progression_sink: List[Dict[str, Any]], generated: List[Dict[str, Any]]
261: ) -> None:
262:     """+1 pressure and agenda per faction via backbone; threshold triggers preserve legacy shapes."""
263:     uid_counts = _faction_progression_uid_counts(world)
264:     for faction in world.get("factions") or []:
265:         if not isinstance(faction, dict):
266:             continue
267:         _ensure_faction_agenda(faction)
268:         fid = faction.get("id", "") or str(faction.get("name", "unknown"))
269:         uid = _faction_progression_uid(faction)
270:         old_pressure = int(faction.get("pressure", 0) or 0)
271:         old_agenda = int(faction.get("agenda_progress", 0) or 0)
272: 
273:         if uid_counts.get(uid, 0) > 1:
274:             _tick_direct_faction_row_advance(faction)
275:         else:
276:             wp.advance_progression_node(
277:                 world,
278:                 wp.faction_pressure_node_id(uid),
279:                 1,
280:                 reason="world_tick",
281:                 event_log=progression_sink,
282:             )
283:             wp.advance_progression_node(
284:                 world,
285:                 wp.faction_agenda_node_id(uid),
286:                 1,
287:                 reason="world_tick",
288:                 event_log=progression_sink,
289:             )
290: 
291:         new_pressure = int(faction.get("pressure", 0) or 0)
292:         new_agenda = int(faction.get("agenda_progress", 0) or 0)
293: 
294:         if old_pressure < PRESSURE_THRESHOLD_EVENT and new_pressure >= PRESSURE_THRESHOLD_EVENT:
295:             fname = faction.get("name", fid)
296:             generated.append(
297:                 {
298:                     "type": "faction_pressure",
299:                     "text": f"{fname}'s pressure mounts.",
300:                     "source": fid,
301:                 }
302:             )
303: 
304:         if old_agenda < AGENDA_THRESHOLD_FLAG and new_agenda >= AGENDA_THRESHOLD_FLAG:
305:             flag_key = f"faction_{fid}_agenda_advanced"
306:             wp.set_progression_node_value(
307:                 world,
308:                 f"world_flag:{flag_key}",
309:                 True,
310:                 reason="world_tick_agenda_threshold",
311:                 event_log=progression_sink,
312:             )
313: 
314:         if old_agenda < AGENDA_THRESHOLD_OP_COMPLETE and new_agenda >= AGENDA_THRESHOLD_OP_COMPLETE:
315:             fname = faction.get("name", fid)
316:             generated.append(
317:                 {
318:                     "type": "faction_operation_complete",
319:                     "text": f"{fname} completes an off-screen operation.",
320:                     "source": fid,
321:                 }
322:             )
323: 
324: 
325: def advance_world_tick(world: Dict[str, Any], campaign: Dict[str, Any]) -> Dict[str, Any]:
326:     """Advance persistent world simulation by one deterministic tick.
327: 
328:     Active projects and faction pressure/agenda move through ``game.world_progression``
329:     with a detached progression-event sink so helper rows do not enter ``event_log``.
330:     Legacy threshold events (pressure, agenda milestones, project completion) and
331:     eligible NPC moves are appended to the player-facing ``event_log``. Return shape preserved.
332:     """
333:     assert_owner_can_mutate_domain(__name__, WORLD_STATE, operation="advance_world_tick")
334:     ensure_defaults(world)
335:     generated: List[Dict[str, Any]] = []
336:     ws = world['world_state']
337:     if not isinstance(ws, dict):
338:         ws = world.setdefault('world_state', {'flags': {}, 'counters': {}, 'clocks': {}})
339: 
340:     # Routine backbone writes attach ``world_progression`` rows only to ``progression_sink``;
341:     # player-facing ``event_log`` carries legacy threshold shapes instead.
342:     progression_sink: List[Dict[str, Any]] = []
343: 
344:     _tick_advance_active_projects(world, progression_sink, generated)
345:     _tick_advance_factions_one_step(world, progression_sink, generated)
346: 
347:     # --- NPC movement (deterministic: mobile + agenda_move_to_scene_id) ---
348:     # Not a supported progression node kind; remains local to this tick until unified elsewhere.
349:     for npc in world.get('npcs') or []:
350:         if not isinstance(npc, dict):
351:             continue
352:         _ensure_npc_agenda(npc)
353:         avail = str(npc.get('availability', 'available') or 'available').strip().lower()
354:         if avail != 'mobile':
355:             continue
356:         move_to = npc.get('agenda_move_to_scene_id') or npc.get('move_to_scene_id')
357:         if not move_to or not isinstance(move_to, str):
358:             continue
359:         move_to = move_to.strip()
360:         if not move_to:
361:             continue
362:         loc = str(npc.get('location', '') or npc.get('scene_id', '') or '')
363:         if loc == move_to:
364:             continue
365:         npc['location'] = move_to
366:         if 'scene_id' in npc:
367:             npc['scene_id'] = move_to
```

### game/storage.py:221-305

```text
221: def load_session() -> Dict[str, Any]:
222:     default_payload = default_session()
223:     if not SESSION_PATH.exists():
224:         # Fresh runtime document: write canonical envelope.
225:         now = utc_iso_now()
226:         default_payload = dict(default_payload)
227:         default_payload["last_saved_at"] = now
228:         env = wrap_runtime_payload(kind="session", payload=default_payload, saved_at=now, include_integrity=True)
229:         _atomic_save_json(SESSION_PATH, env)
230:         return copy.deepcopy(default_payload)
231: 
232:     raw = _load_json(SESSION_PATH, default_payload)
233:     try:
234:         payload, decision = unwrap_and_validate(raw, expected_kind="session", allow_legacy_missing_envelope=True)
235:     except PersistenceContractError as e:
236:         # Safe failure: fall back to deterministic default for malformed/unsafe persisted data.
237:         # This preserves fresh-session bootstrap behavior and prevents undefined state.
238:         if e.category in (
239:             PersistenceFailureCategory.MALFORMED_PAYLOAD,
240:             PersistenceFailureCategory.UNSUPPORTED_VERSION,
241:             PersistenceFailureCategory.WRONG_DOCUMENT_KIND,
242:             PersistenceFailureCategory.INTEGRITY_MISMATCH,
243:             PersistenceFailureCategory.MISSING_ENVELOPE,
244:         ):
245:             return copy.deepcopy(default_payload)
246:         raise
247: 
248:     return payload
249: 
250: 
251: def save_session(data: Dict[str, Any]) -> None:
252:     """Persist session to disk. Sets last_saved_at timestamp for save summary."""
253:     with _runtime_persistence_guard("save_session"):
254:         payload = dict(data)
255:         now = utc_iso_now()
256:         payload["last_saved_at"] = now
257:         env = wrap_runtime_payload(kind="session", payload=payload, saved_at=now, include_integrity=True)
258:         _atomic_save_json(SESSION_PATH, env)
259: 
260: 
261: def load_world() -> Dict[str, Any]:
262:     data = _load_json(WORLD_PATH, default_world())
263:     from game.world import ensure_defaults, ensure_npc_social_fields
264: 
265:     ensure_defaults(data)
266:     for npc in data.get("npcs") or []:
267:         if isinstance(npc, dict):
268:             ensure_npc_social_fields(npc)
269:     return data
270: 
271: 
272: def save_world(data: Dict[str, Any]) -> None:
273:     _save_json(WORLD_PATH, data)
274: 
275: 
276: def load_combat() -> Dict[str, Any]:
277:     default_payload = default_combat()
278:     if not COMBAT_PATH.exists():
279:         now = utc_iso_now()
280:         env = wrap_runtime_payload(kind="combat", payload=dict(default_payload), saved_at=now, include_integrity=True)
281:         _atomic_save_json(COMBAT_PATH, env)
282:         return copy.deepcopy(default_payload)
283: 
284:     raw = _load_json(COMBAT_PATH, default_payload)
285:     try:
286:         payload, _ = unwrap_and_validate(raw, expected_kind="combat", allow_legacy_missing_envelope=True)
287:     except PersistenceContractError as e:
288:         if e.category in (
289:             PersistenceFailureCategory.MALFORMED_PAYLOAD,
290:             PersistenceFailureCategory.UNSUPPORTED_VERSION,
291:             PersistenceFailureCategory.WRONG_DOCUMENT_KIND,
292:             PersistenceFailureCategory.INTEGRITY_MISMATCH,
293:             PersistenceFailureCategory.MISSING_ENVELOPE,
294:         ):
295:             return copy.deepcopy(default_payload)
296:         raise
297:     return payload
298: 
299: 
300: def save_combat(data: Dict[str, Any]) -> None:
301:     with _runtime_persistence_guard("save_combat"):
302:         payload = dict(data)
303:         now = utc_iso_now()
304:         env = wrap_runtime_payload(kind="combat", payload=payload, saved_at=now, include_integrity=True)
305:         _atomic_save_json(COMBAT_PATH, env)
```

### game/storage.py:375-399

```text
375: def append_log(entry: Dict[str, Any]) -> None:
376:     # Serialize with other runtime persistence ops (restore/reset/clear/save) to avoid
377:     # mixed visible state windows where the transcript diverges from session/combat.
378:     with _runtime_persistence_guard("append_log"):
379:         with SESSION_LOG_PATH.open('a', encoding='utf-8') as f:
380:             f.write(json.dumps(entry, ensure_ascii=False) + '\n')
381:             f.flush()
382:             try:
383:                 os.fsync(f.fileno())
384:             except OSError:
385:                 # Best-effort durability; some platforms/filesystems may not support fsync.
386:                 pass
387: 
388: 
389: def load_log() -> List[Dict[str, Any]]:
390:     if not SESSION_LOG_PATH.exists():
391:         return []
392:     entries = []
393:     for line in SESSION_LOG_PATH.read_text(encoding='utf-8').splitlines():
394:         if line.strip():
395:             entries.append(json.loads(line))
396:     return entries
397: 
398: 
399: def clear_log() -> None:
```

### game/campaign_reset.py:1-70

```text
1: """Authoritative New Campaign hard reset.
2: 
3: A single entry point replaces runtime session (root dict replacement via ``reset_session_state``),
4: replaces combat with ``create_fresh_combat_state``, clears the transcript, and strips world
5: playthrough residue. Bootstrap JSON files (campaign, character, scene templates) are not deleted;
6: ``compose_state`` then syncs character name and other intentional bootstrap fields from disk.
7: 
8: Set ``ASHEN_THRONES_DEV_VERIFY=1`` to reload persisted state after reset and run
9: :func:`game.fresh_campaign_verify.verify_fresh_campaign_runtime` (warnings to log + concise
10: ``print``). ``ASHEN_THRONES_DEV_VERIFY_STRICT=1`` turns failures into ``RuntimeError`` (e.g. CI).
11: """
12: from __future__ import annotations
13: 
14: from typing import Any, Dict
15: 
16: from game.campaign_state import create_fresh_combat_state
17: from game.session import reset_session_state
18: from game.storage import (
19:     clear_log,
20:     load_combat,
21:     load_log,
22:     load_session,
23:     load_world,
24:     save_combat,
25:     save_session,
26:     save_world,
27: )
28: from game.world import reset_world_playthrough_state
29: 
30: 
31: def apply_new_campaign_hard_reset() -> Dict[str, Any]:
32:     """Perform full New Campaign reset: session root replacement, fresh combat, world runtime clear, empty log.
33: 
34:     Session must be replaced before applying bootstrap-derived sync (e.g. clocks init in
35:     ``compose_state`` / ``get_or_init_clocks``); world playthrough state must be cleared
36:     or ``world.json`` would re-contaminate prompts (event log, faction ticks, flags).
37:     """
38:     # Serialize against snapshot restore/save collisions: this flow rewrites runtime state.
39:     from game.storage import _runtime_persistence_guard
40: 
41:     with _runtime_persistence_guard("new_campaign_hard_reset"):
42:         session = load_session()
43:         # Root replacement: stale keys from older engines cannot survive.
44:         reset_session_state(session)
45:         save_session(session)
46: 
47:         world = load_world()
48:         reset_world_playthrough_state(world)
49:         save_world(world)
50: 
51:         combat = load_combat()
52:         combat.clear()
53:         combat.update(create_fresh_combat_state())
54:         save_combat(combat)
55: 
56:         clear_log()
57:     # Invariant (NC2): New Campaign is a silent reset — no persisted transcript rows until a turn runs.
58:     tail = load_log()
59:     if tail:
60:         clear_log()
61:         tail = load_log()
62:     if tail:
63:         raise RuntimeError(
64:             "New Campaign invariant violated: session transcript is non-empty immediately after clear_log()."
65:         )
66:     meta: Dict[str, Any] = {
67:         "campaign_run_id": session.get("campaign_run_id"),
68:         "session_id": session.get("session_id"),
69:         # Operator/debug only (HTTP JSON for /api/new_campaign); proves reset + empty transcript.
70:         "transcript_entry_count_after_reset": 0,
```

### static/app.js:649-681

```text
649: const startCampaignBtn = $('startCampaignBtn');
650: if(startCampaignBtn){
651:   startCampaignBtn.addEventListener('click', async ()=>{
652:     if(currentUIMode !== "player") return;
653:     if(startCampaignBusy) return;
654:     if(!state?.ui?.campaign_can_start) return;
655:     startCampaignBusy = true;
656:     startCampaignBtn.disabled = true;
657:     const thinking = addMessage('system','System','Preparing opening…');
658:     try {
659:       const res = await fetch(apiUrl('/start_campaign', {ui_mode: currentUIMode}), {method:'POST'});
660:       const data = await res.json();
661:       if(res.status === 503 || data.status === 'blocked'){
662:         replaceMessage(thinking,'error','System', formatBlockedNewCampaignMessage(data), newCampaignBlockedDetails(data));
663:         return;
664:       }
665:       if(res.status === 409 || data.ok === false){
666:         replaceMessage(thinking,'error','System', data.error || 'Could not start campaign.');
667:         await reloadAll();
668:         return;
669:       }
670:       if(!data.ok){
671:         replaceMessage(thinking,'error','System', data.error || 'Unknown error');
672:         return;
673:       }
674:       replaceMessage(thinking,'gm','GM', data.gm_output?.player_facing_text || '(no narration)', data.resolution);
675:       await reloadAll();
676:     } finally {
677:       startCampaignBusy = false;
678:       if(state) updateCampaignBootstrapUI(state);
679:     }
680:   });
681: }
```

### game/gm_resolution_decision.py:4755-4830

```text
4755: def select_provider_response_envelope(
4756:     decision: Mapping[str, Any] | None,
4757:     contract: Mapping[str, Any] | None = None,
4758: ) -> dict[str, Any]:
4759:     """Choose the model-facing response contract as a projection of authority.
4760: 
4761:     This is not a second authority source. It only decides whether the provider
4762:     needs the structured declaration channel for this already-classified turn.
4763:     Canonical internal responses still normalize to the structured representation.
4764:     """
4765:     projected = project_turn_local_operation(decision, contract)
4766:     if not isinstance(projected, Mapping):
4767:         return {
4768:             "selected_envelope": PROVIDER_ENVELOPE_STRUCTURED,
4769:             "projection_only": True,
4770:             "authority_owner": "gm_resolution_decision",
4771:             "selection_authority_source": ["gm_resolution_decision"],
4772:             "declaration_channel_exposed": True,
4773:             "reason": "missing_turn_operation_projection",
4774:         }
4775:     response_operation = str(projected.get("response_operation") or "")
4776:     declaration_expectation = str(projected.get("declaration_expectation") or "")
4777:     consequential = _consequential_realization_authorized(decision if isinstance(decision, Mapping) else {})
4778:     eligible = (
4779:         response_operation == OP_INCIDENTAL_DIALOGUE
4780:         and declaration_expectation == DECL_REPLY_NOT_REQUIRED
4781:         and not consequential
4782:     )
4783:     if not eligible:
4784:         return {
4785:             "selected_envelope": PROVIDER_ENVELOPE_STRUCTURED,
4786:             "projection_only": True,
4787:             "authority_owner": "gm_resolution_decision",
4788:             "selection_authority_source": list(projected.get("source_authority_fields") or []),
4789:             "declaration_channel_exposed": True,
4790:             "reason": "structured_declaration_channel_still_available",
4791:             "response_operation": response_operation,
4792:             "declaration_expectation": declaration_expectation,
4793:             "consequential_realization_required": consequential,
4794:         }
4795:     return {
4796:         "selected_envelope": PROVIDER_ENVELOPE_NARRATION_ONLY,
4797:         "projection_only": True,
4798:         "authority_owner": "gm_resolution_decision",
4799:         "selection_authority_source": list(projected.get("source_authority_fields") or []),
4800:         "declaration_channel_exposed": False,
4801:         "reason": "ordinary_incidental_dialogue_reply_requires_no_declaration",
4802:         "response_operation": response_operation,
4803:         "declaration_expectation": declaration_expectation,
4804:         "consequential_realization_required": False,
4805:     }
4806: 
4807: 
4808: def _model_turn_operation(projected: Mapping[str, Any]) -> dict[str, Any]:
4809:     return {key: projected[key] for key in _TURN_OPERATION_MODEL_KEYS}
4810: 
4811: 
4812: def _align_answer_strategy(strategy: str, response_operation: str) -> str:
4813:     """Keep the existing summary, and attach the projection where it would otherwise compete."""
4814:     if response_operation == OP_BOUNDED_INTERPRETATION:
4815:         clause = " Do not explain an unauthorized cause, actor, time, or history."
4816:         return strategy if clause.strip() in strategy else strategy + clause
4817:     if response_operation == OP_PLAYER_HYPOTHESIS:
4818:         if "existing status" in strategy:
4819:             clause = " Discuss that hypothesis only conditionally. Do not establish it."
4820:             return strategy if "only conditionally" in strategy else strategy + clause
4821:         return "Realize the listed claims. Discuss the player's hypothesis conditionally. Do not establish it."
4822:     if response_operation == OP_CONSEQUENTIAL_REALIZATION:
4823:         return (
4824:             "Realize the authorized consequential claims and declare them with "
4825:             "source_claim_id and their provenance."
4826:         )
4827:     if response_operation == OP_DIRECT_OBSERVATION:
4828:         if "unresolved" in strategy:
4829:             clause = " Do not add an inference or a new world fact."
4830:             return strategy if clause.strip() in strategy else strategy + clause
```

### game/opening_scene_realization.py:540-568

```text
540: def merge_opening_instructions(existing: MutableSequence[str], *, contract: Mapping[str, Any]) -> None:
541:     """Append compact opening-scene instructions (caller owns the list)."""
542:     c = contract if isinstance(contract, Mapping) else {}
543:     prohib = c.get("prohibited_opener_content")
544:     lines = [str(x).strip() for x in prohib if isinstance(x, str) and str(x).strip()] if isinstance(prohib, list) else []
545:     existing.append(
546:         "OPENING SCENE (STRUCTURED COMPOSITION): Start from the player's anchored perspective: where the "
547:         "player is positioned and what immediately surrounds them. Then expand the selected visible facts into "
548:         "sensory detail (sound, motion, texture, smell), introduce light tension (crowd pressure, authority "
549:         "friction, urgency), and only then present affordances the player can act on now."
550:     )
551:     existing.append(
552:         "OPENING SCENE COMPOSITION CONTRACT: Do not list facts. Do not compress facts into clauses. Expand "
553:         "each fact into a natural sentence or phrase, blending every selected fact through one focal player "
554:         "perspective. Include at least one positional anchor, at least two sensory cues (sound, motion, texture, "
555:         "or smell), and at least one pressure/tension element. Preserve source integrity: use only externally "
556:         "observable facts from opening_scene_realization.contract narration_basis_visible_facts and existing "
557:         "visible context; no omniscient briefing, no title-cased role labels as names, no hidden-fact assertions."
558:     )
559:     existing.append(
560:         "OPENING SCENE EXAMPLE: BAD: \"Rain spatters... Refugees... Guards...\" GOOD: \"You stand in the "
561:         "churned mud before Cinderwatch's eastern gate as rain spatters against soot-dark stone. Refugees press "
562:         "shoulder to shoulder around you, wagons grinding forward under shouted orders while guards hold the "
563:         "choke. A tavern runner weaves through the crush, calling out offers of hot stew and paid rumor.\""
564:     )
565:     if lines:
566:         existing.append("OPENING SCENE PROHIBITED CONTENT: " + " | ".join(lines[:5]))
567: 
568: 
```

### game/interaction_completion.py:419-429

```text
419: def generic_ask_completion(contract: Mapping[str, Any] | None) -> str:
420:     """A completed inability that does not invent a fact or quote the player."""
421:     label = ""
422:     for item in _labels(contract):
423:         if " " in item or item[:1].isupper():
424:             label = item
425:             break
426:     statement = "I cannot answer that from what is settled here."
427:     if label and " " in label:
428:         return f'{label} says, "{statement}"'
429:     return "No one here can answer that from what is settled here."
```

### game/response_type_gating.py:223-306

```text
223: def derive_response_type_contract(
224:     *,
225:     segmented_turn: dict | None,
226:     normalized_action: dict | None,
227:     resolution: dict | None,
228:     interaction_context: dict | None,
229:     directed_social_entry: dict | None = None,
230:     route_choice: str | None = None,
231:     raw_player_text: str | None = None,
232:     suppress_phrase_heuristics: bool = False,
233: ) -> ResponseTypeContract:
234:     """Derive the shipped ``response_type_contract`` shape.
235: 
236:     When ``suppress_phrase_heuristics`` is True (CTIR planner seam), regex/question
237:     guards driven by *raw_player_text* are disabled — resolution/interaction fields only.
238:     """
239:     reasons: list[str] = []
240:     phrase_effective_text = (
241:         ""
242:         if suppress_phrase_heuristics
243:         else _clean_str(raw_player_text)
244:     )
245:     if suppress_phrase_heuristics:
246:         reasons.append("phrase_heuristics_suppressed_for_ctir_planner_seam")
247:     resolution_kind = _clean_str((resolution or {}).get("kind")).lower()
248:     normalized_type = _clean_str((normalized_action or {}).get("type")).lower()
249:     source_route = _resolve_source_route(
250:         segmented_turn=segmented_turn,
251:         normalized_action=normalized_action,
252:         resolution=resolution,
253:         interaction_context=interaction_context,
254:         directed_social_entry=directed_social_entry,
255:         route_choice=route_choice,
256:     )
257:     strict_target_id = _strict_target_id(
258:         resolution=resolution,
259:         interaction_context=interaction_context,
260:         directed_social_entry=directed_social_entry,
261:     )
262: 
263:     if resolution_kind == "scene_opening" or normalized_type == "scene_opening":
264:         required_response_type: ResponseType = "scene_opening"
265:         source_route = "exploration"
266:         reasons.append("scene_opening_requires_opening_response")
267:     elif resolution_kind == "adjudication_query":
268:         required_response_type: ResponseType = "answer"
269:         reasons.append("adjudication_query_requires_answer")
270:     elif _resolution_requires_dialogue(
271:         resolution=resolution,
272:         directed_social_entry=directed_social_entry,
273:         route_choice=route_choice,
274:         strict_target_id=strict_target_id,
275:     ):
276:         required_response_type = "dialogue"
277:         reasons.append("authoritative_social_target_requires_dialogue")
278:     else:
279:         route_choice_clean = _clean_str(route_choice).lower()
280:         if resolution_kind in _ACTION_OUTCOME_KINDS or normalized_type in _ACTION_OUTCOME_KINDS:
281:             required_response_type = "action_outcome"
282:             reasons.append("resolved_world_action_requires_action_outcome")
283:         elif route_choice_clean == "action":
284:             required_response_type = "action_outcome"
285:             reasons.append("action_route_requires_action_outcome")
286:         else:
287:             required_response_type = "neutral_narration"
288:             reasons.append("no_stricter_authoritative_contract")
289: 
290:     strict_answer_expected = False if required_response_type == "scene_opening" else _resolution_requires_answer(
291:         segmented_turn=segmented_turn,
292:         resolution=resolution,
293:         raw_player_text=phrase_effective_text,
294:     )
295:     if required_response_type == "dialogue" and strict_answer_expected:
296:         reasons.append("dialogue_turn_contains_question_expectation")
297: 
298:     guard_applies, block_reason = _non_hostile_guard_applies(
299:         segmented_turn=segmented_turn,
300:         normalized_action=normalized_action,
301:         resolution=resolution,
302:         raw_player_text=phrase_effective_text,
303:         required_response_type=required_response_type,
304:     )
305:     allow_escalation = False if required_response_type == "scene_opening" else not guard_applies
306:     if not allow_escalation and block_reason:
```
