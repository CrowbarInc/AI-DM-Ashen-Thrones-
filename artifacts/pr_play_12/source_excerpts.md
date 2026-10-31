## game/api.py:1864 _post_gm_adoption_gateway
```python
def _post_gm_adoption_gateway(
    *,
    operation: str,
    source: str,
    session: dict,
    scene_id: str | None,
    affected_domains: list[str],
    proposed_payload_summary: dict[str, Any] | None = None,
    branch_label: str | None = None,
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Trace the transitional post-GM adoption gateway.

    Branch validators currently enforce payload-shape safety. The gateway records
    routing/adoption decisions and future policy intent, but it does not yet make
    broad semantic gameplay-policy decisions.
    """
    resolved_classification = (
        dict(classification)
        if isinstance(classification, dict)
        else _post_gm_adoption_classification(operation)
    )
    return {
        "allow": True,
        "trace_metadata": {
            "gateway_present": True,
            "gateway_decision": "allow_legacy_behavior",
            "gateway_shape_validation_enforced": True,
            "gateway_policy_enforcement": "observe_only",
            "gateway_mode": "observe_only",
            "future_blocking_candidate": bool(
                resolved_classification.get("needs_gateway")
                and resolved_classification.get("risk_class") in {"medium", "high"}
            ),
        },
    }
```

## game/api.py:3163 _build_gpt_narration_from_authoritative_state
```python
def _build_gpt_narration_from_authoritative_state(
    *,
    campaign: dict,
    world: dict,
    session: dict,
    character: dict,
    scene: dict,
    combat: dict,
    recent_log: list,
    user_text: str,
    resolution: dict | None,
    scene_runtime: dict,
    segmented_turn: dict | None = None,
    route_choice: str | None = None,
    directed_social_entry: dict | None = None,
    response_type_contract: dict | None = None,
    latency_sink: dict | None = None,
    normalized_action: dict | None = None,
) -> dict:
    """Stages 6-7: build prompt context from authoritative state, then narrate with GPT.

    **CTIR seam:** Mutation and stale detach already ran in :func:`_run_resolved_turn_pipeline`. Here,
    resolution-facing hygiene (e.g. topic probe registration, social escalation on ``resolution``) runs
    before ``ensure_ctir_for_turn`` snapshots CTIR for this stamp. The narration plan bundle is then
    ensured for the same stamp via :mod:`game.narration_plan_bundle` (CTIR → plan → session attachment).
    :mod:`game.prompt_context` / :func:`game.gm.build_messages` **render** that bundle for the model;
    they do not rebuild alternate plan semantics for the same stamp. Targeted retries keep the same
    stamp so CTIR and the bundle are reused. If ``resolution`` is not a dict, CTIR is detached and not
    rebuilt for this path (no mandatory plan bundle).
    """
    register_topic_probe(
        session=session,
        scene_envelope=scene,
        player_text=user_text,
        resolution=resolution if isinstance(resolution, dict) else None,
        recent_log=recent_log,
    )
    if isinstance(resolution, dict):
        apply_social_topic_escalation_to_resolution(
            world=world,
            session=session,
            scene=scene,
            user_text=user_text,
            resolution=resolution,
            recent_log=recent_log,
        )
    else:
        # No authoritative resolution dict: drop any stale CTIR; prompt_context will use caller fallbacks.
        detach_ctir(session)
    _nc_kw: dict | None = None
    _seam_stamp_for_retry = ""
    bundle_seam_requirement: dict[str, Any] = {"ok": True, "skipped": "not_applicable"}
    contract_payload: dict | None = None
    planner_convergence_emergency_exit = False
    planner_path_label = "continuation"
    planner_convergence_report_final: dict[str, Any] | None = None
    gm: dict | None = None
    if isinstance(resolution, dict):
        _ctir_stamp = narration_ctir_turn_stamp(session=session, resolution=resolution, user_text=user_text)
        _scene_id_for_ctir = str((scene.get("scene") or {}).get("id") or "").strip() or None
        # Single build per stamp; retries inside this function reuse the attached object (see ctir_runtime).
        ensure_ctir_for_turn(
            session,
            turn_stamp=_ctir_stamp,
            builder=lambda: build_runtime_ctir_for_narration(
                turn_id=session.get("turn_counter"),
                scene_id=_scene_id_for_ctir,
                player_input=user_text,
                builder_source="game.api._build_gpt_narration_from_authoritative_state",
                resolution=resolution,
                normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
                combat=combat if isinstance(combat, dict) else None,
                session=session if isinstance(session, dict) else None,
                world=world if isinstance(world, dict) else None,
            ),
        )
        _nc_kw = collect_narration_context_call_kwargs(
            campaign,
            world,
            session,
            character,
            scene,
            combat,
            recent_log,
            user_text,
            resolution=resolution,
            scene_runtime=scene_runtime,
            prompt_profile="manual_play_auto",
        )
        _nc_kw.pop("known_answer_hint", None)
        ensure_narration_plan_bundle_for_turn(
            session,
            turn_stamp=_ctir_stamp,
            builder=lambda: build_narration_plan_bundle(
                session=session,
                narration_context_kwargs=_nc_kw,
            ),
        )
        _b = session.get("_runtime_narration_plan_bundle_v1")
        if isinstance(_b, dict):
            pm = _b.get("plan_metadata") if isinstance(_b.get("plan_metadata"), dict) else {}
            if pm.get("semantic_bypass_blocked") or (
                get_attached_ctir(session) and not isinstance(_b.get("narrative_plan"), dict)
            ):
                append_debug_trace(
                    session,
                    build_state_mutation_trace(
                        domain=PLAYER_VISIBLE_STATE,
                        owner_module=__name__,
                        operation="narration_plan_bundle_error",
                        extra={
                            "narration_plan_bundle_error": pm.get("narration_plan_bundle_error"),
                            "semantic_bypass_blocked": bool(pm.get("semantic_bypass_blocked")),
                            "ctir_stamp": pm.get("ctir_stamp"),
                        },
                    ),
                )
        bundle_seam_requirement = require_narration_plan_bundle_for_ctir_turn(
            session,
            turn_stamp=_ctir_stamp,
            owner_module=__name__,
        )
        _seam_stamp_for_retry = _ctir_stamp
        contract_payload = (
            dict(response_type_contract)
            if isinstance(response_type_contract, dict)
            else _derive_response_type_contract_for_turn(
                session=session,
                segmented_turn=segmented_turn,
                normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
                resolution=resolution,
                raw_player_text=user_text,
                route_choice=route_choice,
                directed_social_entry=directed_social_entry,
            )
        )
        planner_path_label = _classify_planner_convergence_path_label_for_manual_play(
            resolution=resolution,
            response_type_contract=contract_payload,
            route_choice=route_choice,
        )
        pre_planner_report = build_planner_convergence_report(
            path_label=planner_path_label,
            owner_module=__name__,
            session=session,
            prompt_payload=None,
        )
        _append_planner_convergence_debug_trace(session, report=pre_planner_report, stage="pre_prompt")
        planner_convergence_report_final = dict(pre_planner_report)
        bundle_seam_ok = bundle_seam_requirement.get("ok") is True
        if not planner_convergence_ok(pre_planner_report) or not bundle_seam_ok:
            planner_convergence_emergency_exit = True
    if contract_payload is None:
        contract_payload = (
            dict(response_type_contract)
            if isinstance(response_type_contract, dict)
            else _derive_response_type_contract_for_turn(
                session=session,
                segmented_turn=segmented_turn,
                normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
                resolution=resolution if isinstance(resolution, dict) else None,
                raw_player_text=user_text,
                route_choice=route_choice,
                directed_social_entry=directed_social_entry,
            )
        )
    if planner_convergence_emergency_exit and isinstance(resolution, dict):
        assert planner_convergence_report_final is not None
        gm = _gm_planner_convergence_seam_terminal(
            session=session,
            report=planner_convergence_report_final,
            path_label=planner_path_label,
            player_text=user_text,
            scene=scene,
            world=world,
            resolution=resolution,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        )
        _attach_planner_convergence_gm_metadata(gm, planner_convergence_report_final)
        _annotate_planner_convergence_seam_gm(
            gm,
            report=planner_convergence_report_final,
            bundle_seam_requirement=bundle_seam_requirement,
            session=session,
            turn_stamp=_ctir_stamp,
        )
        prompt_started = _now_perf()
        messages = [{"role": "system", "content": "."}, {"role": "user", "content": "{}"}]
        prompt_payload: dict = {}
        response_policy = dict(build_response_policy())
        cc0 = compact_response_type_contract(contract_payload)
        if cc0:
            response_policy["response_type_contract"] = cc0
        _accumulate_latency(latency_sink, "prompt_construction", _elapsed_ms(prompt_started))
    else:
        prompt_started = _now_perf()
        messages = build_messages(
            campaign,
            world,
            session,
            character,
            scene,
            combat,
            recent_log,
            user_text,
            resolution,
            scene_runtime=scene_runtime,
            prompt_profile="manual_play_auto",
            narration_context_call_kwargs=_nc_kw,
        )
        prompt_payload = {}
        if isinstance(messages, list) and len(messages) > 1:
            try:
                m1 = messages[1]
                if isinstance(m1, dict) and isinstance(m1.get("content"), str):
                    prompt_payload = json.loads(m1["content"])
            except Exception:
                prompt_payload = {}
        if not isinstance(prompt_payload, dict):
            prompt_payload = {}
        response_policy = (
            prompt_payload.get("response_policy")
            if isinstance(prompt_payload.get("response_policy"), dict)
            else build_response_policy()
        )
        if isinstance(prompt_payload, dict) and contract_payload:
            prompt_payload["response_type_contract"] = dict(contract_payload)
            response_policy = dict(response_policy) if isinstance(response_policy, dict) else build_response_policy()
            compact_contract = compact_response_type_contract(contract_payload)
            if compact_contract:
                response_policy["response_type_contract"] = compact_contract
            prompt_payload["response_policy"] = response_policy
            if (
                isinstance(messages, list)
                and len(messages) > 1
                and isinstance(messages[1], dict)
            ):
                messages = list(messages)
                messages[1] = dict(messages[1])
                messages[1]["content"] = json.dumps(prompt_payload, ensure_ascii=True)
        if isinstance(resolution, dict):
            post_planner_report = build_planner_convergence_report(
                path_label=planner_path_label,
                owner_module=__name__,
                session=session,
                prompt_payload=prompt_payload if isinstance(prompt_payload, dict) else None,
            )
            _append_planner_convergence_debug_trace(session, report=post_planner_report, stage="post_prompt")
            planner_convergence_report_final = dict(post_planner_report)
            if not planner_convergence_ok(post_planner_report):
                gm = _gm_planner_convergence_seam_terminal(
                    session=session,
                    report=post_planner_report,
                    path_label=planner_path_label,
                    player_text=user_text,
                    scene=scene,
                    world=world,
                    resolution=resolution,
                    segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                )
                _attach_planner_convergence_gm_metadata(gm, post_planner_report)
                _annotate_planner_convergence_seam_gm(
                    gm,
                    report=post_planner_report,
                    bundle_seam_requirement=bundle_seam_requirement,
                    session=session,
                    turn_stamp=_ctir_stamp,
                )
                planner_convergence_emergency_exit = True
        _accumulate_latency(latency_sink, "prompt_construction", _elapsed_ms(prompt_started))

    def _failures_after_social_answer_priority(raw: list) -> list:
        prioritized, _dbg = prioritize_retry_failures_for_social_answer_candidate(
            raw,
            player_text=user_text,
            resolution=resolution,
            session=session,
            scene_envelope=scene,
            world=world,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        )
        return prioritized

    def _retain_retry_contract_resolution(previous_gm, next_gm, resolution_obj):
        from game.resolution_contract import retain_resolved_contract_text

        if not isinstance(next_gm, dict):
            return next_gm
        previous = str(previous_gm.get("player_facing_text") or "") if isinstance(previous_gm, dict) else ""
        candidate = str(next_gm.get("player_facing_text") or "")
        kept, preserved = retain_resolved_contract_text(
            previous,
            candidate,
            resolution_obj if isinstance(resolution_obj, dict) else None,
        )
        if not preserved:
            return next_gm
        out = dict(next_gm)
        out["player_facing_text"] = kept
        metadata = out.setdefault("metadata", {})
        if isinstance(metadata, dict):
            debug = metadata.setdefault("emission_debug", {})
            if isinstance(debug, dict):
                debug["semantic_preservation"] = {
                    "semantic_payload_preserved": True,
                    "replacement_selected": False,
                    "rejection_reason": "retry_would_drop_resolved_contract",
                }
        return out

    def _repair_candidate_speaker_before_retry(gm_dict: dict | None) -> dict | None:
        if not isinstance(gm_dict, dict) or not isinstance(resolution, dict):
            return gm_dict
        res_md = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        obligation = res_md.get("interaction_obligation") if isinstance(res_md.get("interaction_obligation"), dict) else {}
        if (
            not obligation
            or str(obligation.get("resolution_mode") or "") == "unsupported_consequential_request"
        ):
            return gm_dict
        candidate = str(gm_dict.get("player_facing_text") or "").strip()
        if not candidate:
            return gm_dict
        repaired, payload = enforce_emitted_speaker_with_contract(
            candidate,
            gm_output=gm_dict,
            resolution=resolution,
            eff_resolution=resolution,
            world=world if isinstance(world, dict) else None,
            scene_id=str(((scene or {}).get("scene") or {}).get("id") or "").strip(),
        )
        if repaired != candidate:
            gm_dict["player_facing_text"] = repaired
            md = gm_dict.setdefault("metadata", {})
            if isinstance(md, dict):
                dbg = md.setdefault("emission_debug", {})
                if isinstance(dbg, dict):
                    dbg["pre_retry_speaker_repair"] = payload
        return gm_dict

    def _attach_bounded_improvisation_authority(gm_dict: dict | None) -> dict | None:
        if not isinstance(gm_dict, dict):
            return gm_dict
        decision = select_resolution_mode(
            player_text=user_text,
            scene=scene if isinstance(scene, dict) else None,
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            resolution=resolution if isinstance(resolution, dict) else None,
            normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
            route_choice=route_choice,
        )
        gm_dict = synthesize_live_improvisation_proposal(gm_dict, decision=decision)
        return attach_bounded_improvisation_evaluation(
            gm_dict,
            session=session,
            scene=scene,
            world=world,
            resolution=resolution if isinstance(resolution, dict) else None,
        )

    def _repair_terminal_player_facing_if_needed(
        gm_dict: dict,
        *,
        reason: str,
        preserve_upstream_model_route: bool = False,
    ) -> dict:
        repair_started = _now_perf()
        social_lane = _strict_social_route_signal()
        if _gm_has_usable_player_facing_text(gm_dict):
            _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(repair_started))
            return gm_dict
        if social_lane:
            repaired = ensure_minimal_social_resolution(
                gm=gm_dict,
                session=session,
                reason=reason,
                world=world,
                resolution=resolution if isinstance(resolution, dict) else None,
                scene_envelope=scene,
                player_text=user_text,
                segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            )
            print("[SOCIAL RESOLUTION REPAIR] terminal empty social output repaired")
            _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(repair_started))
            preserve_fallback_provenance_metadata(repaired, gm_dict)
            _preserve_model_route_metadata(
                repaired,
                gm_dict,
                mark_upstream_preserved=preserve_upstream_model_route,
            )
            return repaired
        repaired_ns = ensure_minimal_nonsocial_resolution(gm=gm_dict, session=session)
        dbg = repaired_ns.get("debug_notes") if isinstance(repaired_ns.get("debug_notes"), str) else ""
        repaired_ns["debug_notes"] = (dbg + " | " if dbg else "") + f"nonsocial_repair_context:{reason}"
        print("[NON-SOCIAL RESOLUTION REPAIR] empty output repaired")
        _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(repair_started))
        preserve_fallback_provenance_metadata(repaired_ns, gm_dict)
        _preserve_model_route_metadata(
            repaired_ns,
            gm_dict,
            mark_upstream_preserved=preserve_upstream_model_route,
        )
        return repaired_ns

    def _extract_upstream_api_error(gm_dict: dict | None) -> dict | None:
        md = gm_dict.get("metadata") if isinstance(gm_dict, dict) and isinstance(gm_dict.get("metadata"), dict) else {}
        err = md.get("upstream_api_error") if isinstance(md.get("upstream_api_error"), dict) else None
        return dict(err) if isinstance(err, dict) else None

    def _strict_social_route_signal() -> bool:
        sid = str((scene.get("scene") or {}).get("id") or "").strip()
        return bool(
            _session_social_authority(session)
            or strict_social_emission_will_apply(resolution, session, world, sid)
        )

    def _social_dialogue_turn() -> bool:
        if route_choice == "dialogue":
            return True
        # Engine-resolved turns (``/api/action`` and structured ``/api/chat``) carry a concrete
        # ``kind``; keep the full targeted-retry budget for validator_voice / question-shape races.
        if isinstance(resolution, dict) and str(resolution.get("kind") or "").strip():
            return False
        return _strict_social_route_signal()

    def _fast_fallback_for_upstream_error(
        gm_dict: dict,
        api_error: dict,
        *,
        reason: str,
    ) -> dict:
        failure_class = str(api_error.get("failure_class") or "upstream_api_error").strip() or "upstream_api_error"
        failure = {
            "failure_class": failure_class,
            "priority": -1,
            "reasons": [reason, str(api_error.get("error_code") or "").strip() or failure_class],
        }
        fallback_started = _now_perf()
        out = force_terminal_retry_fallback(
            session=session,
            original_text=str(gm_dict.get("player_facing_text") or ""),
            failure=failure,
            retry_failures=[failure],
            player_text=user_text,
            scene_envelope=scene,
            world=world,
            resolution=resolution,
            base_gm=gm_dict,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        )
        _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(fallback_started))
        out = _repair_terminal_player_facing_if_needed(
            out,
            reason=f"api_upstream_fast_fallback:{failure_class}",
            preserve_upstream_model_route=True,
        )
        out = dict(out)
        tags = out.get("tags") if isinstance(out.get("tags"), list) else []
        tag_list = [str(t) for t in tags if isinstance(t, str)]
        for extra in ("fast_fallback", "upstream_api_fast_fallback", f"upstream_api_failure:{failure_class}"):
            if extra not in tag_list:
                tag_list.append(extra)
        out["tags"] = tag_list
        md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
        out["metadata"] = {
            **md,
            "upstream_api_error": dict(api_error),
            "latency_mode": "fast_fallback",
        }
        attach_realization_fallback_family(out["metadata"], GPT_BUDGET_OR_PROVIDER_FAILURE)
        dbg = out.get("debug_notes") if isinstance(out.get("debug_notes"), str) else ""
        out["debug_notes"] = (
            (dbg + " | " if dbg else "")
            + f"upstream_api_fast_fallback:{failure_class}:{reason}"
        )
        _preserve_model_route_metadata(out, gm_dict, mark_upstream_preserved=True)
        # Canonical provenance packaging (game.fallback_provenance_debug); selection already applied above.
        attach_upstream_fast_fallback_provenance(out)
        _attach_resolution_contract_metadata_to_gm_output(out, resolution if isinstance(resolution, dict) else None)
        record_emergency_nonplan_output(
            session,
            reason=f"upstream_api_fast_fallback:{failure_class}",
            owner_module=__name__,
            extra={"failure_class": failure_class, "reason": reason},
        )
        print(f"[FAST FALLBACK INVOKED] failure_class={failure_class} reason={reason}")
        om = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
        fam = str(om.get("human_adjacent_intent_family") or "").strip().lower()
        if fam not in ("", "none"):
            print("[FAST FALLBACK PRESERVED HUMAN-ADJACENT METADATA]")
        if om.get("nearby_group_continuity_carryover") is True:
            print("[FAST FALLBACK PRESERVED NEARBY-GROUP CONTINUITY CONTEXT]")
        return out

    known_clues = list(get_all_known_clue_texts(session))
    fast_fallback_mode = False
    used_force_terminal_fallback = False
    retry_loop_started: float | None = None
    gpt_calls_used = 0

    def _call_gpt_route_kwargs(
        *,
        retry_attempt: int = 0,
        retry_reason: str | None = None,
    ) -> dict[str, Any]:
        normalized_retry_reason = str(retry_reason or "").strip()
        purpose = "primary_turn"
        strict_social = False
        if retry_attempt >= 1 or normalized_retry_reason in _RETRY_ESCALATION_ROUTE_REASONS:
            purpose = "retry_escalation"
        elif _strict_social_route_signal():
            purpose = "strict_social"
            strict_social = True
        return {
            "purpose": purpose,
            "response_policy": response_policy if isinstance(response_policy, dict) else None,
            "segmented_turn": segmented_turn if isinstance(segmented_turn, dict) else None,
            "retry_attempt": int(retry_attempt or 0),
            "retry_reason": normalized_retry_reason or None,
            "strict_social": strict_social,
        }

    def _bounded_call_gpt(
        msgs: list,
        *,
        retry_attempt: int = 0,
        retry_reason: str | None = None,
    ):
        nonlocal gpt_calls_used
        if gpt_calls_used >= MANUAL_PLAY_MAX_CALL_GPT:
            print("[RETRY SKIPPED: MANUAL_PLAY_GPT_BUDGET_EXCEEDED]")
            return _synthetic_manual_play_gpt_budget_gm()
        if int(retry_attempt or 0) > 0 and _seam_stamp_for_retry:
            verify_same_turn_narration_stamp_for_retry(
                session,
                expected_ctir_stamp=_seam_stamp_for_retry,
                expected_narration_plan_bundle_stamp=_seam_stamp_for_retry,
                owner_module=__name__,
            )
        gpt_calls_used += 1
        call_kwargs = _call_gpt_route_kwargs(
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
        )
        try:
            sig = inspect.signature(call_gpt)
            accepts_route_context = any(
                param.kind == inspect.Parameter.VAR_KEYWORD
                for param in sig.parameters.values()
            ) or all(name in sig.parameters for name in call_kwargs)
        except (TypeError, ValueError):
            accepts_route_context = True
        if accepts_route_context:
            return call_gpt(msgs, **call_kwargs)
        return call_gpt(msgs)

    retry_attempt = 0
    _previous_narration_text = ""
    from game.immutable_valid_response import adopt_host_speech

    adopted_speech = adopt_host_speech(
        gm if isinstance(gm, dict) else _gm_for_skipped_provider_narration("", reason="authorized_host_speech"),
        resolution=resolution, player_text=str(user_text or ""), session=session,
        world=world,
    )
    if adopted_speech is not None:
        gm = adopted_speech
    if gm is None:
        skipped = deterministic_provider_skip_line(
            resolution=resolution if isinstance(resolution, dict) else None,
            scene=scene if isinstance(scene, dict) else None,
            world=world if isinstance(world, dict) else None,
            session=session if isinstance(session, dict) else None,
            player_text=str(user_text or ""),
        )
        if skipped is not None:
            skip_text, skip_reason = skipped
            gm = _gm_for_skipped_provider_narration(skip_text, reason=skip_reason)
    if gm is None:
        initial_gpt_started = _now_perf()
        gm = guard_gm_output(
            _bounded_call_gpt(messages),
            scene,
            user_text,
            known_clues,
            session=session,
            world=world,
            resolution=resolution,
        )
        gm = _attach_bounded_improvisation_authority(gm)
        _accumulate_latency(latency_sink, "gpt_call", _elapsed_ms(initial_gpt_started))
        retry_attempt = 0
        social_dialogue_turn = _social_dialogue_turn()
        # Cap social-dialogue retries at one when the global budget allows it, but honor a test or
        # manual monkeypatch that sets MAX_TARGETED_RETRY_ATTEMPTS to 0 (escape hatch on first failure).
        max_targeted_retry_attempts = (
            min(1, int(MAX_TARGETED_RETRY_ATTEMPTS)) if social_dialogue_turn else int(MAX_TARGETED_RETRY_ATTEMPTS)
        )
        upstream_api_error = _extract_upstream_api_error(gm)
        if upstream_api_error:
            retry_loop_started = _now_perf()
            allow_direct_api_retry = bool(upstream_api_error.get("retryable")) and not social_dialogue_turn
            if allow_direct_api_retry:
                retry_gpt_started = _now_perf()
                gm_retry = guard_gm_output(
                    _bounded_call_gpt(
                        messages,
                        retry_attempt=1,
                        retry_reason=str(upstream_api_error.get("failure_class") or "").strip()
                        or "retryable_upstream_error",
                    ),
                    scene,
                    user_text,
                    known_clues,
                    session=session,
                    world=world,
                    resolution=resolution,
                )
                gm_retry = _attach_bounded_improvisation_authority(gm_retry)
                _ = _elapsed_ms(retry_gpt_started)
                retried_api_error = _extract_upstream_api_error(gm_retry)
                if retried_api_error:
                    gm = _fast_fallback_for_upstream_error(
                        gm_retry,
                        retried_api_error,
                        reason="retryable_upstream_error_exhausted",
                    )
                    fast_fallback_mode = True
                else:
                    gm = gm_retry
            else:
                if not upstream_api_error.get("retryable"):
                    print("[RETRY SKIPPED: NONRETRYABLE UPSTREAM ERROR]")
                else:
                    print("[RETRY SKIPPED: UPSTREAM RETRY SUPPRESSED] social_dialogue_turn=True")
                gm = _fast_fallback_for_upstream_error(
                    gm,
                    upstream_api_error,
                    reason="nonretryable_upstream_error" if not upstream_api_error.get("retryable") else "social_retry_suppressed",
                )
                fast_fallback_mode = True
        if (
            not fast_fallback_mode
            and isinstance(gm, dict)
            and isinstance(resolution, dict)
        ):
            res_md = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
            if (
                str(resolution.get("kind") or "").strip().lower() == "observe"
                and str(res_md.get("parser_lane") or "").strip().lower() == "local_observation_question"
            ):
                from game.perception_grounding import realize_local_observation_line

                grounded = realize_local_observation_line(
                    scene if isinstance(scene, dict) else None,
                    session=session if isinstance(session, dict) else None,
                    world=world if isinstance(world, dict) else None,
                    resolution=resolution,
                    player_text=str(user_text or ""),
                )
                if grounded:
                    gm = dict(gm)
                    gm["player_facing_text"] = grounded
                    md_grounded = dict(gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {})
                    if md_grounded.get("structured_contract_failure"):
                        md_grounded.pop("structured_contract_failure", None)
                        md_grounded.pop("structured_output_rejected", None)
                        md_grounded.pop("structured_contract_reason", None)
                        envelope = md_grounded.get("realization_envelope")
                        if isinstance(envelope, dict):
                            md_grounded["realization_envelope"] = {
                                **envelope,
                                "declared_claims": None,
                                "narration": grounded,
                                "structured_contract_present": False,
                                "deterministic_realization": True,
                                "legacy_fallback": False,
                            }
                    gm["metadata"] = md_grounded
                    tags = list(gm.get("tags") or [])
                    if "local_observation_realization" not in tags:
                        tags.append("local_observation_realization")
                    gm["tags"] = tags
                    md = dict(gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {})
                    md["emission_provenance"] = {
                        "class": "downstream_consequence",
                        "kind": "local_observation",
                        "contract_id": str((res_md.get("resolution_contract") or {}).get("contract_id") or "")
                        if isinstance(res_md.get("resolution_contract"), dict)
                        else "",
                        "operation": "perceive",
                        "semantic_owner": "resolution_contract",
                    }
                    gm["metadata"] = md
            from game.immutable_valid_response import lifecycle_applies, run_preserve_if_valid

            if lifecycle_applies(resolution):
                from game.ordinary_semantic_ownership import social_narration_unnecessary

                allow_regeneration = int(MAX_TARGETED_RETRY_ATTEMPTS) > 0 and not social_narration_unnecessary(
                    resolution if isinstance(resolution, dict) else None
                )

                def _regenerate_once(feedback: str, _messages=messages):
                    retry_messages = (list(_messages) if isinstance(_messages, list) else []) + [
                        {"role": "user", "content": feedback}
                    ]
                    regenerated = guard_gm_output(
                        _bounded_call_gpt(
                            retry_messages,
                            retry_attempt=1,
                            retry_reason="hard_invalid",
                        ),
                        scene,
                        user_text,
                        known_clues,
                        session=session,
                        world=world,
                        resolution=resolution,
                    )
                    return _attach_bounded_improvisation_authority(regenerated)

                gm = run_preserve_if_valid(
                    gm,
                    regenerate=_regenerate_once if allow_regeneration else None,
                    resolution=resolution,
                    player_text=user_text,
                    scene=scene,
                    world=world,
                    session=session,
                )
        from game.immutable_valid_response import response_is_immutable

        if not response_is_immutable(gm):
            gm = _repair_candidate_speaker_before_retry(gm)
        while not fast_fallback_mode and not response_is_immutable(gm):
            from game.ordinary_semantic_ownership import social_narration_unnecessary

            if social_narration_unnecessary(resolution if isinstance(resolution, dict) else None):
                print("[RETRY SKIPPED: DETERMINED NONRESOLUTION]")
                break
            failures = _failures_after_social_answer_priority(
                detect_retry_failures(
                    player_text=user_text,
                    gm_reply=gm,
                    scene_envelope=scene,
                    session=session,
                    world=world,
                    resolution=resolution,
                    segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                )
            )
            selected_failure = choose_retry_strategy(failures)
            if not selected_failure:
                break
            current_text = str(gm.get("player_facing_text") or "").strip() if isinstance(gm, dict) else ""
            md_now = gm.get("metadata") if isinstance(gm, dict) and isinstance(gm.get("metadata"), dict) else {}
            provider_not_sent = bool(
                md_now.get("provider_calls_disabled")
                or md_now.get("provider_budget_refusal")
                or md_now.get("provider_retry_disabled")
            )
            if narration_retry_should_stop(
                provider_not_sent=provider_not_sent,
                retry_attempt=retry_attempt,
                previous_text=_previous_narration_text,
                current_text=current_text,
            ):
                print("[RETRY SKIPPED: UNCHANGED OR UNSENT OUTPUT]")
                fc = str(selected_failure.get("failure_class") or "").strip()
                force_started = _now_perf()
                gm = force_terminal_retry_fallback(
                    session=session,
                    original_text=current_text,
                    failure=selected_failure,
                    retry_failures=failures,
                    player_text=user_text,
                    scene_envelope=scene,
                    world=world,
                    resolution=resolution,
                    base_gm=gm,
                    segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                )
                _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(force_started))
                gm = _repair_terminal_player_facing_if_needed(
                    gm, reason="api_unchanged_narration_retry_stopped"
                )
                used_force_terminal_fallback = True
                record_emergency_nonplan_output(
                    session,
                    reason="unchanged_narration_retry_stopped",
                    owner_module=__name__,
                    extra={"failure_class": fc, "retry_attempt": retry_attempt},
                )
                break
            _previous_narration_text = current_text
            if retry_loop_started is None:
                retry_loop_started = _now_perf()
            if retry_attempt >= max_targeted_retry_attempts:
                fc = str(selected_failure.get("failure_class") or "").strip()
                print(f"[RETRY ESCAPE HATCH] class={fc} attempts={retry_attempt}")
                force_started = _now_perf()
                gm = force_terminal_retry_fallback(
                    session=session,
                    original_text=str(gm.get("player_facing_text") or ""),
                    failure=selected_failure,
                    retry_failures=failures,
                    player_text=user_text,
                    scene_envelope=scene,
                    world=world,
                    resolution=resolution,
                    base_gm=gm,
                    segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                )
                _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(force_started))
                gm = _repair_terminal_player_facing_if_needed(
                    gm, reason="api_post_force_terminal_retry_fallback"
                )
                used_force_terminal_fallback = True
                record_emergency_nonplan_output(
                    session,
                    reason="force_terminal_retry_fallback",
                    owner_module=__name__,
                    extra={"failure_class": fc, "retry_attempt": retry_attempt},
                )
                break
            retry_attempt += 1
            retry_cs_dbg: dict = {}
            selected_class = str(selected_failure.get("failure_class") or "").strip()
            retry_instruction = build_retry_prompt_for_failure(
                selected_failure,
                response_policy=response_policy,
                gm_output=gm,
                retry_debug_sink=retry_cs_dbg,
                player_text=user_text,
            )
            from game.resolution_contract import contract_mapping_from_resolution

            retry_contract = contract_mapping_from_resolution(resolution if isinstance(resolution, dict) else None)
            if retry_contract:
                retry_dimension = retry_contract.get("dimension") or ", ".join(
                    str(item) for item in (retry_contract.get("dimensions") or []) if str(item).strip()
                )
                retry_instruction += (
                    " Keep the same resolution contract"
                    f" (operation={retry_contract.get('operation') or 'unspecified'}"
                    f", dimension={retry_dimension or 'unspecified'})."
                    " Do not replace that answer with an unrelated fact, rumor, or generic inability."
                )
            print(
                "[RETRY] selected_strategy=",
                selected_failure.get("failure_class"),
                "attempt=",
                retry_attempt,
                "reasons=",
                selected_failure.get("reasons"),
            )
            retry_messages = (
                list(messages) if isinstance(messages, list) else []
            ) + [{'role': 'user', 'content': retry_instruction}]
            retry_gpt_started = _now_perf()
            gm_retry = guard_gm_output(
                _bounded_call_gpt(
                    retry_messages,
                    retry_attempt=retry_attempt,
                    retry_reason=selected_class or None,
                ),
                scene,
                user_text,
                known_clues,
                session=session,
                world=world,
                resolution=resolution,
            )
            gm_retry = _attach_bounded_improvisation_authority(gm_retry)
            gm_retry = _repair_candidate_speaker_before_retry(gm_retry)
            _ = _elapsed_ms(retry_gpt_started)
            loop_api_err = _extract_upstream_api_error(gm_retry)
            if loop_api_err:
                fc = str(loop_api_err.get("failure_class") or "")
                if not loop_api_err.get("retryable"):
                    print(f"[RETRY SKIPPED: NONRETRYABLE UPSTREAM ERROR] class={fc}")
                else:
                    print(f"[RETRY SKIPPED: UPSTREAM ERROR IN RETRY LOOP] class={fc}")
                gm = _fast_fallback_for_upstream_error(
                    gm_retry,
                    loop_api_err,
                    reason="retry_loop_upstream_api_error",
                )
                fast_fallback_mode = True
                break
            retry_dbg = gm_retry.get('debug_notes') if isinstance(gm_retry.get('debug_notes'), str) else ''
            reason_suffix = ','.join(str(r) for r in (selected_failure.get("reasons") or []) if isinstance(r, str)) or 'unknown'
            cs_trace = ""
            if retry_cs_dbg:
                cs_trace = (
                    f"retry_context_separation_trace:"
                    f"contract_resolved={retry_cs_dbg.get('retry_context_separation_contract_resolved')}:"
                    f"source={retry_cs_dbg.get('retry_context_separation_contract_source')}:"
                    f"prior_trouble={retry_cs_dbg.get('retry_context_separation_prior_trouble')}:"
                    f"local_first={retry_cs_dbg.get('retry_context_separation_local_first_recovery')}:"
                    f"pf_allowed={retry_cs_dbg.get('retry_context_separation_pressure_focus_allowed')}"
                )
            gm_retry['debug_notes'] = (
                (retry_dbg + ' | ' if retry_dbg else '')
                + f"retry_strategy:selected={selected_failure.get('failure_class')}:attempt={retry_attempt}:reasons={reason_suffix}"
                + (f" | {cs_trace}" if cs_trace else "")
            )
            retry_failures = _failures_after_social_answer_priority(
                detect_retry_failures(
                    player_text=user_text,
                    gm_reply=gm_retry,
                    scene_envelope=scene,
                    session=session,
                    world=world,
                    resolution=resolution,
                    segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                )
            )
            still_failing = next(
                (
                    failure for failure in retry_failures
                    if isinstance(failure, dict) and str(failure.get("failure_class") or "").strip() == selected_class
                ),
                None,
            )
            still_unresolved_after_answer_retry = next(
                (
                    failure
                    for failure in retry_failures
                    if isinstance(failure, dict)
                    and str(failure.get("failure_class") or "").strip() == "unresolved_question"
                ),
                None,
            )
            use_open_crowd_scene_stall_fallback = (
                selected_class == "scene_stall"
                and isinstance(still_failing, dict)
                and resolution_is_open_crowd_social(resolution)
            )
            use_question_retry_fallback = (selected_class == "unresolved_question" and still_failing) or (
                selected_class == "answer" and still_unresolved_after_answer_retry
            ) or use_open_crowd_scene_stall_fallback or (
                selected_class == "followup_soft_repetition" and isinstance(still_failing, dict)
            )
            if use_question_retry_fallback:
                _vf = still_failing if isinstance(still_failing, dict) else still_unresolved_after_answer_retry
                print(
                    "[RETRY] validation_failed selected_strategy=",
                    selected_class,
                    "attempt=",
                    retry_attempt,
                    "reasons=",
                    (_vf.get("reasons") if isinstance(_vf, dict) else None),
                    "action=deterministic_fallback",
                )
                if use_open_crowd_scene_stall_fallback:
                    fallback_failure = {
                        "failure_class": "unresolved_question",
                        "priority": int(RETRY_FAILURE_PRIORITY.get("unresolved_question", 10)),
                        "reasons": ["retry_bridge:open_crowd_scene_stall"],
                    }
                else:
                    if selected_class == "followup_soft_repetition" and isinstance(still_failing, dict):
                        fallback_failure = {
                            "failure_class": "unresolved_question",
                            "priority": int(RETRY_FAILURE_PRIORITY.get("unresolved_question", 10)),
                            "reasons": list(still_failing.get("reasons") or []),
                            "followup_context": (
                                still_failing.get("followup_context")
                                if isinstance(still_failing.get("followup_context"), dict)
                                else {}
                            ),
                        }
                    else:
                        fallback_failure = (
                            still_failing if selected_class == "unresolved_question" else selected_failure
                        )
                deterministic_started = _now_perf()
                gm_retry = apply_deterministic_retry_fallback(
                    gm_retry,
                    failure=fallback_failure,
                    player_text=user_text,
                    scene_envelope=scene,
                    session=session,
                    world=world,
                    resolution=resolution,
                    segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                )
                gm_retry = _attach_bounded_improvisation_authority(gm_retry)
                _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(deterministic_started))
                fallback_failures = _failures_after_social_answer_priority(
                    detect_retry_failures(
                        player_text=user_text,
                        gm_reply=gm_retry,
                        scene_envelope=scene,
                        session=session,
                        world=world,
                        resolution=resolution,
                        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                    )
                )
                compare_class = (
                    "unresolved_question"
                    if use_open_crowd_scene_stall_fallback or selected_class == "followup_soft_repetition"
                    else selected_class
                )
                fallback_still_failing = any(
                    isinstance(failure, dict) and str(failure.get("failure_class") or "").strip() == compare_class
                    for failure in fallback_failures
                )
                print(
                    "[RETRY] fallback_result selected_strategy=",
                    selected_class,
                    "attempt=",
                    retry_attempt,
                    "status=",
                    "failed" if fallback_still_failing else "passed",
                )
                if fallback_still_failing:
                    print(f"[RETRY ESCAPE HATCH] class={selected_class} attempts={retry_attempt}")
                    fail_meta = next(
                        (
                            f
                            for f in fallback_failures
                            if isinstance(f, dict) and str(f.get("failure_class") or "").strip() == selected_class
                        ),
                        selected_failure,
                    )
                    force_started = _now_perf()
                    gm = force_terminal_retry_fallback(
                        session=session,
                        original_text=str(gm_retry.get("player_facing_text") or ""),
                        failure=fail_meta if isinstance(fail_meta, dict) else selected_failure,
                        retry_failures=fallback_failures,
                        player_text=user_text,
                        scene_envelope=scene,
                        world=world,
                        resolution=resolution,
                        base_gm=gm_retry,
                        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
                    )
                    _accumulate_latency(latency_sink, "fallback_repair", _elapsed_ms(force_started))
                    gm = _repair_terminal_player_facing_if_needed(
                        gm, reason="api_post_force_terminal_retry_fallback"
                    )
                    used_force_terminal_fallback = True
                    record_emergency_nonplan_output(
                        session,
                        reason="force_terminal_retry_fallback_after_deterministic",
                        owner_module=__name__,
                        extra={"failure_class": str(selected_class or ""), "retry_attempt": retry_attempt},
                    )
                else:
                    gm = _retain_retry_contract_resolution(gm, gm_retry, resolution)
                break
            gm = _retain_retry_contract_resolution(gm, gm_retry, resolution)
        if retry_loop_started is not None:
            _accumulate_latency(latency_sink, "retry_loop_total", _elapsed_ms(retry_loop_started))
    if isinstance(gm, dict):
        accounting = dict(gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {})
        accounting["narration_provider_calls"] = int(gpt_calls_used)
        accounting["narration_retry_count"] = int(retry_attempt)
        gm["metadata"] = accounting
    gm = _repair_terminal_player_facing_if_needed(
        gm, reason="api_targeted_retry_post_terminal"
    )
    if isinstance(prompt_payload, dict) and isinstance(gm, dict):
        gm = dict(gm)
        sac = prompt_payload.get("scene_state_anchor_contract")
        if isinstance(sac, dict):
            gm["scene_state_anchor_contract"] = dict(sac)
        cmw = prompt_payload.get("conversational_memory_window")
        if not isinstance(cmw, dict):
            # The provider payload omits this top-level copy when it is JSON-equal
            # to the surviving response_policy child. Engine inspection still
            # receives that same object.
            policy_for_memory = prompt_payload.get("response_policy")
            if isinstance(policy_for_memory, dict):
                cmw = policy_for_memory.get("conversational_memory_window")
        if isinstance(cmw, dict):
            gm["conversational_memory_window"] = dict(cmw)
        scm = prompt_payload.get("selected_conversational_memory")
        if isinstance(scm, list):
            gm["selected_conversational_memory"] = list(scm)
        pd0 = prompt_payload.get("prompt_debug")
        if isinstance(pd0, dict):
            cm = pd0.get("conversational_memory")
            if isinstance(cm, dict):
                merged_pd = dict(gm["prompt_debug"]) if isinstance(gm.get("prompt_debug"), dict) else {}
                merged_pd["conversational_memory"] = dict(cm)
                gm["prompt_debug"] = merged_pd
        _attach_scene_opening_curated_facts_to_gm(
            gm,
            prompt_payload=prompt_payload,
            resolution=resolution if isinstance(resolution, dict) else None,
        )
    if retry_attempt == 0 and isinstance(gm, dict) and isinstance(resolution, dict):
        from game.immutable_valid_response import response_is_immutable, run_preserve_if_valid
        from game.resolution_contract import contract_mapping_from_resolution

        _narration_contract = contract_mapping_from_resolution(resolution)
        _opening_meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
        _opening_tags = {str(tag) for tag in (gm.get("tags") or []) if isinstance(tag, str)}
        # A rejected scene_opening must not be sealed as a generic information answer.
        _structured_opening_rejected = _opening_operation_required(
            resolution, response_type_contract
        ) and (
            bool(_opening_meta.get("structured_contract_failure"))
            or bool(_opening_meta.get("structured_output_rejected"))
            or "structured_contract_failure" in _opening_tags
            or "structured_output_rejected" in _opening_tags
        )
        if (
            not _structured_opening_rejected
            and str(_narration_contract.get("operation") or "") == "unresolved"
            and not str(_narration_contract.get("interlocutor_id") or "").strip()
            and not response_is_immutable(gm)
        ):
            # No question or stall retry was owed. Keep a hard-valid narration
            # from being rewritten into a pressure or social beat.
            gm = run_preserve_if_valid(
                gm,
                regenerate=None,
                resolution=resolution,
                player_text=user_text,
                scene=scene,
                world=world,
                session=session,
            )
    gm = _apply_narration_hub_policy_handoff(
        gm,
        fast_fallback_mode=fast_fallback_mode,
        response_policy=response_policy,
        player_text=user_text,
        scene_envelope=scene,
        session=session,
        world=world,
        resolution=resolution,
        discovered_clues=known_clues,
        repair_terminal_player_facing_if_needed=_repair_terminal_player_facing_if_needed,
    )
    gm = apply_authored_knowledge_realization_to_gm(
        gm,
        player_text=user_text,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=str(((scene or {}).get("scene") or {}).get("id") or "").strip(),
    )
    gm = apply_stay_leave_narration_agreement_to_gm(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        origin_scene_id=str((resolution or {}).get("originating_scene_id") or ""),
    )
    gm = apply_destination_arrival_realization_to_gm(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        player_text=user_text,
    )
    gm = apply_perception_non_invention_to_gm(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        player_text=user_text,
    )
    gm = _attach_bounded_improvisation_authority(gm)
    if isinstance(gm, dict):
        decision = select_resolution_mode(
            player_text=user_text,
            scene=scene if isinstance(scene, dict) else None,
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            resolution=resolution if isinstance(resolution, dict) else None,
            normalized_action=normalized_action if isinstance(normalized_action, dict) else None,
            route_choice=route_choice,
        )
        md = gm.setdefault("metadata", {})
        if isinstance(md, dict):
            md.setdefault("live_resolution_mode", live_resolution_trace(decision))
    _attach_scene_opening_curated_facts_to_gm(
        gm,
        prompt_payload=prompt_payload if isinstance(prompt_payload, dict) else None,
        resolution=resolution if isinstance(resolution, dict) else None,
    )
    if isinstance(resolution, dict) and str(resolution.get("kind") or "").strip() == "scene_opening":
        assert "opening_curated_facts" in gm
    if isinstance(session, dict) and isinstance(response_policy, dict):
        session["last_turn_response_policy"] = dict(response_policy)
    store_progression_fingerprint_on_session(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
    )
    _tag_list = [str(t) for t in (gm.get("tags") or []) if isinstance(t, str)]
    _gpt_budget_exceeded = any("manual_play_gpt_budget_exceeded" in t for t in _tag_list)
    (
        _,
        _finalize_path_kind,
        _finalize_annotate_kwargs,
        _,
    ) = _narration_hub_finalize_annotation_parts(
        resolution=resolution if isinstance(resolution, dict) else None,
        planner_convergence_emergency_exit=planner_convergence_emergency_exit,
        gpt_budget_exceeded=_gpt_budget_exceeded,
        fast_fallback_mode=fast_fallback_mode,
        used_force_terminal_fallback=used_force_terminal_fallback,
        bundle_seam_requirement=bundle_seam_requirement,
        gpt_calls_used=gpt_calls_used,
    )
    if _gpt_budget_exceeded:
        annotate_narration_path_kind(gm, path_kind=_finalize_path_kind, **_finalize_annotate_kwargs)
        annotate_narration_continuation_classification(gm, session=session if isinstance(session, dict) else None)
        enforce_plan_driven_continuation_invariant(
            gm,
            session=session if isinstance(session, dict) else None,
            bundle_seam_requirement=bundle_seam_requirement,
            turn_stamp=_seam_stamp_for_retry or None,
        )
        record_emergency_nonplan_output(
            session,
            reason="manual_play_gpt_budget_exceeded",
            owner_module=__name__,
        )
    elif isinstance(resolution, dict):
        if planner_convergence_emergency_exit:
            if isinstance(planner_convergence_report_final, dict):
                _attach_planner_convergence_gm_metadata(gm, planner_convergence_report_final)
        else:
            annotate_narration_path_kind(gm, path_kind=_finalize_path_kind, **_finalize_annotate_kwargs)
            annotate_narration_continuation_classification(gm, session=session if isinstance(session, dict) else None)
            enforce_plan_driven_continuation_invariant(
                gm,
                session=session if isinstance(session, dict) else None,
                bundle_seam_requirement=bundle_seam_requirement,
                turn_stamp=_seam_stamp_for_retry or None,
            )
            if isinstance(planner_convergence_report_final, dict):
                _attach_planner_convergence_gm_metadata(gm, planner_convergence_report_final)
    else:
        annotate_narration_path_kind(gm, path_kind=_finalize_path_kind, **_finalize_annotate_kwargs)
        annotate_narration_continuation_classification(gm, session=session if isinstance(session, dict) else None)
        enforce_plan_driven_continuation_invariant(
            gm,
            session=session if isinstance(session, dict) else None,
            bundle_seam_requirement=None,
            turn_stamp=None,
        )
    return gm
```

## game/api.py:4418 _run_resolved_turn_pipeline
```python
def _run_resolved_turn_pipeline(
    *,
    campaign: dict,
    character: dict,
    session: dict,
    world: dict,
    combat: dict,
    scene: dict,
    recent_log: list,
    resolution: dict,
    normalized_action: dict | None,
    fallback_user_text: str,
    segmented_turn: dict | None = None,
    route_choice: str | None = None,
    directed_social_entry: dict | None = None,
    latency_sink: dict | None = None,
) -> tuple[dict, dict, dict, dict, list[str], dict]:
    """Shared resolved-turn flow for both `/api/action` and `/api/chat`.

    Stage 5: authoritative engine mutation is applied first.
    Stage 6-7: prompt context and GPT narration are built only from that post-resolution state.

    **CTIR:** ``detach_ctir`` is the first step so any prior turn's session-backed CTIR cannot leak into
    this mutation. Fresh CTIR for this turn is attached later inside
    :func:`_build_gpt_narration_from_authoritative_state` (after hygiene on ``resolution``). Do not attach
    CTIR here—keep build/attach next to prompt construction for retry-stable stamps.
    """
    detach_ctir(session)
    from game.semantic_interpreter import player_visible_turns

    attach_interaction_obligation(
        resolution,
        player_text=resolution.get("prompt") or fallback_user_text,
        session=session,
        normalized_action=normalized_action,
        scene_id=str(((scene or {}).get("scene") or {}).get("id") or session.get("active_scene_id") or ""),
        scene=scene,
        world=world,
        visible_turns=player_visible_turns(recent_log),
        enable_model_interpretation=not live_interpretation_consumed(),
    )
    engine_started = _now_perf()
    departure_scene = scene
    scene, session, combat, authoritative_clue_updates, scene_rt = _apply_authoritative_resolution_state_mutation(
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        resolution=resolution,
        normalized_action=normalized_action,
    )
    from game.gm_resolution_decision import reconcile_movement_decision

    reconcile_movement_decision(
        resolution,
        departure_scene=departure_scene,
        destination_scene=scene,
        world=world,
    )
    if isinstance(session, dict):
        append_debug_trace(
            session,
            build_state_mutation_trace(
                domain=SCENE_STATE,
                owner_module=__name__,
                operation="authoritative_resolution_mutation",
                extra={
                    "changed_area": "session+world+scene_runtime",
                    "resolution_kind": str((resolution or {}).get("kind") or ""),
                },
            ),
        )
    _accumulate_latency(latency_sink, "engine_resolution", _elapsed_ms(engine_started))

    user_text = resolution.get('prompt') or fallback_user_text
    response_type_contract = _derive_response_type_contract_for_turn(
        session=session,
        segmented_turn=segmented_turn,
        normalized_action=normalized_action,
        resolution=resolution,
        raw_player_text=user_text,
        route_choice=route_choice,
        directed_social_entry=directed_social_entry,
    )
    gm = _build_gpt_narration_from_authoritative_state(
        campaign=campaign,
        world=world,
        session=session,
        character=character,
        scene=scene,
        combat=combat,
        recent_log=recent_log,
        user_text=user_text,
        resolution=resolution,
        scene_runtime=scene_rt,
        segmented_turn=segmented_turn,
        route_choice=route_choice,
        directed_social_entry=directed_social_entry,
        response_type_contract=response_type_contract,
        latency_sink=latency_sink,
        normalized_action=normalized_action,
    )
    return (scene, session, combat, gm, authoritative_clue_updates, response_type_contract)
```

## game/api.py:4789 _opening_response_rejection
```python
def _opening_response_rejection(
    gm: dict | None,
    resolution: dict | None,
    response_type_contract: dict | None,
) -> str | None:
    """Reject an opening that the existing contract does not accept.

    Safe fallback text is not a completed scene_opening. Structured validation
    is unchanged: a rejected envelope stays rejected.
    """
    if not _opening_operation_required(resolution, response_type_contract):
        return None
    if not isinstance(gm, dict):
        return "missing_opening_response"
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    tags = {str(tag) for tag in (gm.get("tags") or []) if isinstance(tag, str)}
    text = str(gm.get("player_facing_text") or "").strip()
    lowered = text.lower()
    debug_notes = str(gm.get("debug_notes") or "")
    if "provider_budget_refused" in tags or meta.get("provider_budget_refusal") or "provider_budget_refused" in debug_notes:
        return "provider_budget_refused"
    if meta.get("structured_contract_failure") or meta.get("structured_output_rejected"):
        return _stable_opening_reason(meta.get("structured_contract_reason"), "structured_contract_rejected")
    if tags & {"structured_contract_failure", "structured_output_rejected"}:
        return "structured_contract_rejected"
    if tags & {"fast_fallback", "upstream_api_fast_fallback", "provider_calls_disabled"}:
        return "provider_opening_not_delivered"
    if debug_notes.startswith("call_gpt error") or "provider_calls_disabled" in debug_notes:
        return "provider_opening_not_delivered"
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    provenance = str(accepted.get("provenance") or "")
    authorization = str(accepted.get("authorization_source") or "")
    if provenance == "safe_nonresolution" or authorization == "safe_nonresolution":
        return "safe_nonresolution"
    seal = gm.get("_final_delivery_seal")
    if isinstance(seal, str) and "safe_nonresolution" in seal:
        return "safe_nonresolution"
    if isinstance(seal, dict) and (
        seal.get("provenance") == "safe_nonresolution" or seal.get("authorization_source") == "safe_nonresolution"
    ):
        return "safe_nonresolution"
    if any(marker in lowered for marker in _GENERIC_INFORMATION_FALLBACK_MARKERS):
        return "generic_information_request_fallback"
    emission = meta.get("emission_debug") if isinstance(meta.get("emission_debug"), dict) else {}
    if emission.get("opening_fallback_failed_closed"):
        return "opening_fallback_failed_closed"
    if emission.get("response_type_candidate_ok") is False:
        return "scene_opening_contract_rejected"
    from game.final_emission_validators import candidate_satisfies_scene_opening_contract

    accepted_opening, reasons = candidate_satisfies_scene_opening_contract(text)
    if not accepted_opening:
        return _stable_opening_reason((reasons or ["scene_opening_contract_rejected"])[0], "scene_opening_contract_rejected")
    return None
```

## game/api.py:4878 _restore_opening_baseline
```python
def _restore_opening_baseline(baseline: dict) -> None:
    """Write the pre-attempt session, world, combat, and transcript back to disk."""
    save_world(baseline["world"])
    save_combat(baseline["combat"])
    save_session(baseline["session"])
    current = load_log()
    expected = int(baseline.get("log_len") or 0)
    if len(current) > expected:
        prior = current[:expected]
        clear_log()
        for row in prior:
            append_log(row)
```

## game/api.py:5893 _complete_opening_turn_persistence_like_chat
```python
def _complete_opening_turn_persistence_like_chat(
    *,
    turn_started: float,
    campaign: dict,
    character: dict,
    session: dict,
    world: dict,
    combat: dict,
    scene: dict,
    scene_before_id: str,
    trace: dict,
    latency_ms: dict[str, int],
    clue_presentation_before: dict,
    clocks_before: dict,
    time_pressure_after: int,
    tick: dict,
    recent_log: list,
    routed_via_exploration: bool,
    routed_via_adjudication: bool,
    normalized_chat: dict | None,
    resolution: dict | None,
    gm: dict,
    response_type_contract: dict | None,
    route_choice: str | None,
    parsed: dict | None,
    segmented_turn: dict | None,
    compact_segmented: dict | None,
    canonical_entry: dict,
    implied_context: dict,
    authoritative_clue_updates: list[str],
    player_text_for_eval: str,
    debug_action_kind: str,
    trace_source: str,
    trace_action_type: str,
    request_log_payload: dict,
    mark_campaign_started: bool,
) -> dict:
    """Shared tail of ``/api/chat`` after GM output exists (opening / exploration / adjudication paths).

    ``POST /api/start_campaign`` reuses this tail with ``mark_campaign_started`` so bootstrap
    persistence matches chat openings; final-emission layers remain downstream consumers only.
    """
    from game.gm import classify_player_intent

    def _text_preview(value: object, *, limit: int = 180) -> str:
        text = str(value or "")
        return text[:limit] + ("..." if len(text) > limit else "")

    def _attach_final_text_invariant_debug(
        gm_obj: dict,
        *,
        response_payload: dict | None = None,
        log_payload_text: str | None = None,
    ) -> None:
        if not isinstance(gm_obj, dict):
            return
        final_text = str(gm_obj.get("player_facing_text") or "")
        response_text = final_text
        if isinstance(response_payload, dict):
            payload_gm = response_payload.get("gm_output")
            if isinstance(payload_gm, dict):
                response_text = str(payload_gm.get("player_facing_text") or "")
        log_text = str(log_payload_text if log_payload_text is not None else final_text)
        metadata = gm_obj.setdefault("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
            gm_obj["metadata"] = metadata
        emission_debug = metadata.setdefault("emission_debug", {})
        if not isinstance(emission_debug, dict):
            emission_debug = {}
            metadata["emission_debug"] = emission_debug
        emission_debug.update(
            {
                "gm_output_player_facing_len": len(final_text),
                "final_emission_text_preview": _text_preview(final_text),
                "response_payload_text_preview": _text_preview(response_text),
                "log_payload_text_preview": _text_preview(log_text),
                "canonical_gm_object_id": id(gm_obj),
            }
        )

    _include_res_chat = bool(
        isinstance(resolution, dict)
        and (
            routed_via_exploration
            or routed_via_adjudication
            or isinstance((resolution.get("metadata") or {}).get("resolution_contract"), dict)
        )
    )
    if response_type_contract is None:
        response_type_contract = _derive_response_type_contract_for_turn(
            session=session,
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            normalized_action=normalized_chat,
            resolution=resolution if isinstance(resolution, dict) else None,
            raw_player_text=player_text_for_eval,
            route_choice=route_choice,
            directed_social_entry=canonical_entry,
            attach_to_resolution=bool(isinstance(resolution, dict)),
        )
    remember_recent_contextual_leads(
        session,
        scene["scene"]["id"],
        _player_facing_text_for_lead_extraction(gm),
    )
    gm, _narr_consistency_chat = _finalize_player_facing_for_turn(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session,
        world=world,
        scene=scene,
        include_resolution_in_sanitizer=_include_res_chat,
        latency_sink=latency_ms,
    )
    gm = apply_authored_knowledge_realization_to_gm(
        gm,
        player_text=player_text_for_eval,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        scene_id=str((scene.get("scene") or {}).get("id") or "").strip(),
        extra_facts=authoritative_clue_updates,
    )
    gm = apply_stay_leave_narration_agreement_to_gm(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        origin_scene_id=str((resolution or {}).get("originating_scene_id") or ""),
    )
    gm = apply_destination_arrival_realization_to_gm(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        player_text=player_text_for_eval,
    )
    gm = apply_perception_non_invention_to_gm(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        session=session if isinstance(session, dict) else None,
        world=world if isinstance(world, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        player_text=player_text_for_eval,
    )
    if isinstance(resolution, dict):
        from game.resolution_contract import enforce_emitted_contract_monotonicity

        gm = enforce_emitted_contract_monotonicity(gm, resolution)
    if str((resolution or {}).get("kind") or "").strip().lower() not in {
        "scene_opening",
        "scene_transition",
        "travel",
    }:
        from game.perception_grounding import remember_completed_perception_turn

        remember_completed_perception_turn(
            session,
            str((scene.get("scene") or {}).get("id") or "").strip(),
            scene,
            str((gm or {}).get("player_facing_text") or ""),
            resolution=resolution if isinstance(resolution, dict) else None,
            player_text=player_text_for_eval,
        )
    canonical_gm = gm
    if isinstance(resolution, dict) and str(resolution.get("kind") or "").strip().lower() == "scene_opening":
        metadata = canonical_gm.get("metadata") if isinstance(canonical_gm.get("metadata"), dict) else {}
        emission_debug = metadata.get("emission_debug") if isinstance(metadata.get("emission_debug"), dict) else {}
        if isinstance(emission_debug, dict):
            final_meta = canonical_gm.setdefault("_final_emission_meta", {})
            if isinstance(final_meta, dict):
                for key in (
                    "opening_selector_source_used",
                    "opening_selector_selected_facts",
                    "opening_curated_facts",
                    "opening_final_fallback_basis",
                    "opening_final_basis_matches_selector",
                ):
                    if key in emission_debug and key not in final_meta:
                        final_meta[key] = emission_debug.get(key)
    for _rt in _narr_consistency_chat.get("repaired_discovered_clue_texts") or []:
        if isinstance(_rt, str) and _rt.strip() and _rt.strip() not in authoritative_clue_updates:
            authoritative_clue_updates.append(_rt.strip())

    scene, session, combat, surfaced_clue_telemetry, narration_social_leads = _apply_post_gm_updates(
        gm, scene, session, world, combat, resolution=resolution if isinstance(resolution, dict) else None
    )
    for _txt in narration_social_leads:
        if isinstance(_txt, str) and _txt.strip() and _txt.strip() not in authoritative_clue_updates:
            authoritative_clue_updates.append(_txt.strip())
    context_resolution = (
        resolution
        if isinstance(resolution, dict) and resolution.get("kind") and resolution.get("kind") != "adjudication_query"
        else None
    )
    _update_interaction_context_after_action(
        session,
        context_resolution,
        scene_changed=scene_before_id != scene["scene"]["id"],
        preserve_continuity=bool(
            (implied_context.get("applied") or implied_context.get("interaction_established"))
            and not implied_context.get("commitment_broken")
        ),
    )
    _adopt_dbg_chat = None
    _stale_inv_dbg_chat = None
    if scene_before_id == scene["scene"]["id"]:
        _adopt_dbg_chat = apply_post_emission_speaker_adoption(
            session,
            world,
            scene,
            gm,
            resolution=context_resolution if isinstance(context_resolution, dict) else None,
            scene_changed=False,
        )
        _stale_inv_dbg_chat = apply_stale_interlocutor_invalidation_after_emission(
            session,
            world,
            scene,
            gm,
            resolution=context_resolution if isinstance(context_resolution, dict) else None,
            scene_changed=False,
            adoption_debug=_adopt_dbg_chat,
        )
    _preserve_authoritative_resolution_facts_after_gate(
        gm,
        resolution=resolution if isinstance(resolution, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
    )
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    if mark_campaign_started:
        opening_rejection = _opening_response_rejection(gm, resolution, response_type_contract)
        from game.provider_budget import observe_opening_validation
        observe_opening_validation(
            rejection=opening_rejection,
            recovery=_stable_opening_reason(
                ((gm.get("metadata") or {}).get("accepted_response") or {}).get("provenance"),
                "rejected_without_recovery" if opening_rejection else "unavailable",
            ),
        )
        if opening_rejection:
            return _opening_failure_response(opening_rejection)
    save_world(world)

    leads_inspection = _lead_debug_trace_around_authoritative_reconcile(session)

    session["last_action_debug"] = _build_action_debug(
        debug_action_kind, player_text_for_eval, normalized_chat, resolution, response_type_contract
    )
    _merge_emergent_actor_debug_into_action_debug(session)
    maybe_attach_intent_fulfillment_eval(
        session,
        player_input=player_text_for_eval,
        final_output=str(gm.get("player_facing_text") or ""),
        response_type=compact_response_type_contract(response_type_contract),
    )
    maybe_attach_player_agency_eval(
        session,
        final_output=str(gm.get("player_facing_text") or ""),
    )

    clocks_changed = {"time_pressure": time_pressure_after} if clocks_before.get("time_pressure") != time_pressure_after else {}

    trace["parsed_intent"] = parsed if parsed is not None else None
    trace["normalized_action"] = (
        {
            k: normalized_chat[k]
            for k in ("id", "label", "type", "prompt", "targetSceneId", "target_scene_id")
            if k in (normalized_chat or {})
        }
        if normalized_chat and isinstance(normalized_chat, dict)
        else None
    )
    trace["resolution"] = _sanitize_resolution(resolution)
    trace["response_type_contract"] = compact_response_type_contract(response_type_contract)
    trace["scene_after"] = scene["scene"]["id"]
    deduped_clue_updates: list[str] = []
    for txt in authoritative_clue_updates:
        if isinstance(txt, str) and txt.strip() and txt.strip() not in deduped_clue_updates:
            deduped_clue_updates.append(txt.strip())
    trace["clue_updates"] = deduped_clue_updates
    trace["world_flag_updates"] = _trace_world_updates(gm.get("world_updates"), clocks_changed)
    latency_ms["total_turn"] = _elapsed_ms(turn_started)
    trace["turn_trace"] = _build_compact_turn_trace(
        source=trace_source,
        action_type=trace_action_type,
        raw_input=trace["raw_input"],
        parsed_intent=parsed if isinstance(parsed, dict) else None,
        segmented_turn=compact_segmented,
        normalized_action=normalized_chat,
        implied_context=implied_context,
        resolution=resolution,
        scene_before=trace["scene_before"],
        scene_after=trace["scene_after"],
        authoritative_clue_updates=deduped_clue_updates,
        clue_presentation_before=clue_presentation_before,
        session=session,
        world=world,
        scene=scene,
        leads_inspection=leads_inspection,
        response_type_contract=response_type_contract,
        route_selected=route_choice,
        directed_social_entry=canonical_entry,
        adoption_debug=_adopt_dbg_chat,
        stale_invalidation_debug=_stale_inv_dbg_chat,
        latency_ms=_finalize_latency_breakdown(latency_ms),
    )
    trace["latency_ms"] = _finalize_latency_breakdown(latency_ms)
    trace["performance"] = _performance_record(
        latency=trace["latency_ms"],
        gm=gm if isinstance(gm, dict) else None,
        provider_requests=len((trace.get("live_chat_interpretation") or {}).get("provider_requests") or [])
        if isinstance(trace.get("live_chat_interpretation"), dict)
        else 0,
        successful=True,
        disposition=str(trace.get("action_type") or "chat"),
        interpretation_usage=(trace.get("live_chat_interpretation") or {}).get("provider_requests") or [],
    )
    if isinstance(resolution, dict):
        resolution_meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        resolution["metadata"] = {**resolution_meta, "performance": trace["performance"]}
    _finalize_and_append_trace(session, trace, True, None)

    clear_turn_start_interlocutor_snapshot(session)
    # First successful opening only (structured start or chat scene_opening); never set on failed turns.
    if mark_campaign_started:
        session["campaign_started"] = True
    from game.immutable_valid_response import restore_accepted_text

    restore_accepted_text(gm)
    if (isinstance(resolution, dict) and isinstance(resolution.get("social"), dict) and isinstance(gm, dict)
            and ((gm.get("metadata") or {}).get("accepted_response") or {}).get("authorization_source") != "host_terminal_safety"):
        from game.dialogue_authority import remember_dialogue_commitment
        from game.immutable_valid_response import restore_accepted_text

        restore_accepted_text(gm)
        remember_dialogue_commitment(
            session,
            social=resolution.get("social"),
            player_text=str(player_text_for_eval or ""),
            line=str(gm.get("player_facing_text") or ""),
            turn=int(session.get("turn_counter") or 0),
        )
    from game.conversational_continuity import record_delivered_exchange

    speech_adoption = (gm.get("metadata") or {}).get("accepted_response") or {}
    speech_adoption = speech_adoption or None
    record_delivered_exchange(
        session,
        player_text=str(player_text_for_eval or ""),
        delivered_text=str(gm.get("player_facing_text") or ""),
        social=resolution.get("social") if isinstance(resolution, dict) else None,
        scene_id=str(scene["scene"].get("id") or ""),
        turn=int(session.get("turn_counter") or 0),
        adoption=speech_adoption,
    )
    session.setdefault("conversational_context", {})["last_gm_exchange"] = {
        "category": "RESOLVED", "owner": "GM", "purpose": "ACTION_RESULT",
        "subject": str(player_text_for_eval or "")[:240],
        "response": str(gm.get("player_facing_text") or "")[:1200],
        "refusal_reason": None, "scene_id": scene["scene"].get("id"),
        "operation": (resolution or {}).get("kind"),
    }
    save_session(session)
    save_combat(combat)

    intent = classify_player_intent(player_text_for_eval)
    if (routed_via_exploration or routed_via_adjudication) and isinstance(resolution, dict):
        resolution.setdefault("world_tick_events", tick.get("events", []))

    gm_prompt_summary: dict = {
        "scene_id": scene["scene"].get("id"),
        "scene_mode": scene["scene"].get("mode"),
        "response_mode": session.get("response_mode", "standard"),
        "response_type_contract": compact_response_type_contract(response_type_contract),
    }
    if routed_via_exploration and isinstance(resolution, dict):
        gm_prompt_summary["exploration"] = {
            "action_id": resolution.get("action_id"),
            "kind": resolution.get("kind"),
            "scene_transition_occurred": bool(resolution.get("resolved_transition")),
        }
    if routed_via_adjudication and isinstance(resolution, dict):
        gm_prompt_summary["adjudication"] = dict(resolution.get("adjudication") or {})

    log_meta = dict(request_log_payload.get("log_meta") or {})
    log_meta.setdefault("intent_classification", intent)
    log_meta.setdefault("gm_prompt_context_summary", gm_prompt_summary)
    log_meta.setdefault("gm_raw_output_meta", {"has_output": True})
    log_meta.setdefault("approved_state_updates", {
        "scene_update": gm.get("scene_update"),
        "world_updates": gm.get("world_updates"),
        "new_scene_draft": gm.get("new_scene_draft"),
    })
    log_meta.setdefault("rejected_state_updates", [])
    log_meta.setdefault("discovered_clues_added", deduped_clue_updates)
    log_meta.setdefault("surfaced_clues_in_narration_non_authoritative", list(surfaced_clue_telemetry))
    log_meta.setdefault("clocks_changed", clocks_changed)
    log_meta.setdefault("response_type_contract", compact_response_type_contract(response_type_contract))

    response_payload = _build_turn_response_payload(
        gm=gm,
        resolution=resolution if _include_res_chat else None,
        include_resolution=_include_res_chat,
    )
    final_text = str(canonical_gm.get("player_facing_text") or "")
    payload_gm = response_payload.get("gm_output") if isinstance(response_payload, dict) else None
    if mark_campaign_started and isinstance(response_payload, dict):
        response_payload["gm_output"] = canonical_gm
        payload_gm = canonical_gm
    _attach_final_text_invariant_debug(
        canonical_gm,
        response_payload=response_payload if isinstance(response_payload, dict) else None,
        log_payload_text=final_text,
    )
    if isinstance(payload_gm, dict) and payload_gm is not canonical_gm:
        payload_metadata = payload_gm.setdefault("metadata", {})
        if isinstance(payload_metadata, dict):
            payload_debug = payload_metadata.setdefault("emission_debug", {})
            source_debug = (
                (canonical_gm.get("metadata") or {}).get("emission_debug")
                if isinstance(canonical_gm.get("metadata"), dict)
                else {}
            )
            if isinstance(payload_debug, dict) and isinstance(source_debug, dict):
                payload_debug.update(source_debug)
    assert (
        response_payload["gm_output"] is canonical_gm
        or response_payload["gm_output"]["player_facing_text"] == canonical_gm["player_facing_text"]
    )

    append_log(
        {
            "timestamp": utc_iso_now(),
            "player_input": log_meta.get("player_input") or player_text_for_eval or "",
            "request": dict(request_log_payload.get("request") or {}),
            "resolution": resolution,
            "gm_output": canonical_gm,
            "log_meta": log_meta,
        }
    )
    assert (
        response_payload["gm_output"] is canonical_gm
        or response_payload["gm_output"]["player_facing_text"] == canonical_gm["player_facing_text"]
    )
    return response_payload
```

## game/api.py:6342 start_campaign
```python
def start_campaign(request: Request):
    """First opening via internal bootstrap intent; same narration stack as chat opening (OF1 path)."""
    from game.provider_budget import playtest_stop_reason, PLAYTEST_STOP_MESSAGE
    if playtest_stop_reason():
        from game.provider_budget import record_generation_diagnostic
        record_generation_diagnostic({"stage": "opening_admission", "logical_operation": "scene_opening",
            "requested_response_type": "scene_opening", "classification": "provider_budget_refused",
            "rejection_reason": "provider_budget_refused", "opening_accepted": False, "gameplay_committed": False})
        return JSONResponse(status_code=409, content={"ok": False, "status": "blocked", "error": PLAYTEST_STOP_MESSAGE})
    try:
        ui_mode = resolve_requested_ui_mode(request)
        assert_mode_allows_runtime_action(ui_mode)
    except UiModePolicyError as e:
        return _ui_mode_error_response(e)
    gate, gate_operator = _compute_upstream_gate_for_live_gameplay()
    if gate.get("manual_testing_blocked"):
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "status": "blocked",
                "error": (
                    "Upstream API preflight indicates live narration is unhealthy; "
                    "starting the campaign is disabled until upstream recovers."
                ),
                "upstream_dependent_run_gate": gate,
                "upstream_dependent_run_gate_operator": gate_operator,
            },
        )

    opening_scope = _OpeningScope()
    try:
        opening_scope.acquire()
        if playtest_stop_reason():
            return JSONResponse(status_code=409, content={"ok": False, "status": "blocked", "error": PLAYTEST_STOP_MESSAGE})
        return _start_campaign_after_admission(ui_mode, gate, gate_operator, opening_scope)
    finally:
        opening_scope.close()
```

## game/api.py:6382 _start_campaign_after_admission
```python
def _start_campaign_after_admission(ui_mode, gate, gate_operator, opening_scope: _OpeningScope):
    campaign = load_campaign()
    character = load_character()
    session = load_session()
    recent_log = load_log()
    if not _session_allows_structured_start_campaign(session, recent_log):
        from game.provider_budget import observe_opening_validation
        observe_opening_validation(rejection="already_started", recovery="not_attempted")
        st = compose_state()
        return JSONResponse(
            status_code=409,
            content={
                "ok": False,
                "status": "already_started",
                "error": "Campaign has already started, or the transcript is not empty.",
                "upstream_dependent_run_gate": gate,
                "upstream_dependent_run_gate_operator": gate_operator,
                **_project_state_for_ui_mode(st, ui_mode),
            },
        )

    turn_started = _now_perf()
    snapshot_turn_start_interlocutor(session)
    world = load_world()
    combat = load_combat()
    conditions = load_conditions()
    scene = load_active_scene()
    synchronize_scene_addressability(session, scene, world)
    scene["scene_state"] = session.get("scene_state")
    scene_before_id = scene["scene"]["id"]

    trace: dict = {
        "timestamp": utc_iso_now(),
        "source": "start_campaign",
        "action_type": "start_campaign",
        "raw_input": "",
        "turn_stage_order": list(AUTHORITATIVE_TURN_STAGE_ORDER),
        "incoming_payload": {"start_campaign": True},
        "parsed_intent": None,
        "segmented_turn": None,
        "normalized_action": None,
        "resolution": None,
        "scene_before": scene["scene"]["id"],
        "scene_after": None,
        "clue_updates": [],
        "world_flag_updates": [],
        "turn_trace": None,
        "gpt_called": True,
        "response_ok": True,
        "error": None,
    }
    latency_ms: dict[str, int] = {}
    clue_presentation_before = _snapshot_known_clue_presentations(session)

    opening_scope.track(session, world, combat)
    if session.get("turn_counter") is None:
        session["turn_counter"] = 0
    session["turn_counter"] += 1

    tick = advance_world_tick(world, campaign)

    clocks_before = dict(get_or_init_clocks(session))
    time_pressure_after = advance_clock(session, "time_pressure", 1)

    recent_log = load_log()
    scene_rt = get_scene_runtime(session, scene["scene"]["id"])

    routed_via_exploration = True
    routed_via_adjudication = False
    route_choice = "action"
    authoritative_clue_updates: list[str] = []

    classify_started = _now_perf()
    segmented_turn = segment_mixed_player_turn("")
    trace["segmented_turn"] = _compact_segmented_turn(segmented_turn)
    canonical_entry = resolve_directed_social_entry(
        session=session,
        scene=scene,
        world=world,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text="",
    )
    declared_switch_meta = resolve_declared_actor_switch(
        session=session,
        scene=scene,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        raw_text="",
    )
    trace["canonical_entry"] = {
        "should_route_social": bool(canonical_entry.get("should_route_social")),
        "target_actor_id": canonical_entry.get("target_actor_id"),
        "target_source": canonical_entry.get("target_source"),
        "reason": canonical_entry.get("reason"),
        "spoken_text": canonical_entry.get("spoken_text"),
        "declared_switch_detected": bool(declared_switch_meta.get("has_declared_switch")),
        "declared_switch_target_actor_id": (
            declared_switch_meta.get("target_actor_id")
            if declared_switch_meta.get("has_declared_switch")
            else None
        ),
        "continuity_overridden_by_declared_switch": bool(
            canonical_entry.get("continuity_overridden_by_declared_switch")
        ),
        "spoken_vocative_detected": bool(canonical_entry.get("spoken_vocative_detected")),
        "spoken_vocative_target_actor_id": canonical_entry.get("spoken_vocative_target_actor_id"),
        "continuity_overridden_by_spoken_vocative": bool(
            canonical_entry.get("continuity_overridden_by_spoken_vocative")
        ),
    }
    for _k in (
        "open_social_solicitation",
        "broad_address_bid",
        "broadcast_social_open_call",
        "candidate_addressable_ids",
        "candidate_addressable_count",
        "broad_address_reason",
        "broad_address_phrase_matched",
    ):
        if _k in canonical_entry:
            trace["canonical_entry"][_k] = canonical_entry.get(_k)
    trace["canonical_entry_path"] = (
        "social" if canonical_entry.get("should_route_social") else "undecided"
    )
    trace["canonical_entry_reason"] = canonical_entry.get("reason")
    trace["canonical_entry_target_actor_id"] = canonical_entry.get("target_actor_id")
    implied_context = _prepare_interaction_from_turn_input(session, world, scene_before_id, "", scene=scene)
    compact_segmented = _compact_segmented_turn(segmented_turn)

    normalized_chat, resolution = _opening_scene_normalized_action_and_resolution(
        scene=scene,
        player_text=None,
        internal_bootstrap=True,
    )
    parsed = normalized_chat
    _accumulate_latency(latency_ms, "intent_classification", _elapsed_ms(classify_started))

    try:
        scene, session, combat, gm, turn_clue_updates, response_type_contract = _run_resolved_turn_pipeline(
            campaign=campaign,
            character=character,
            session=session,
            world=world,
            combat=combat,
            scene=scene,
            recent_log=recent_log,
            resolution=resolution,
            normalized_action=normalized_chat,
            fallback_user_text="",
            segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
            route_choice="action",
            directed_social_entry=canonical_entry,
            latency_sink=latency_ms,
        )
    except Exception:
        raise

    authoritative_clue_updates.extend(turn_clue_updates)
    if isinstance(resolution, dict):
        resolution["world_tick_events"] = tick.get("events", [])

    _record_scene_pressure_input(
        session,
        scene_before_id,
        "",
        normalized_action=parsed if isinstance(parsed, dict) else None,
        resolution=None,
    )

    request_log = {
        "request": {"start_campaign": True, "action_type": "start_campaign"},
        "log_meta": {
            "bootstrap_intent": "start_campaign",
            "player_input": "",
        },
    }

    result = _complete_opening_turn_persistence_like_chat(
        turn_started=turn_started,
        campaign=campaign,
        character=character,
        session=session,
        world=world,
        combat=combat,
        scene=scene,
        scene_before_id=scene_before_id,
        trace=trace,
        latency_ms=latency_ms,
        clue_presentation_before=clue_presentation_before,
        clocks_before=clocks_before,
        time_pressure_after=time_pressure_after,
        tick=tick,
        recent_log=recent_log,
        routed_via_exploration=routed_via_exploration,
        routed_via_adjudication=routed_via_adjudication,
        normalized_chat=normalized_chat,
        resolution=resolution,
        gm=gm,
        response_type_contract=response_type_contract,
        route_choice=route_choice,
        parsed=parsed,
        segmented_turn=segmented_turn if isinstance(segmented_turn, dict) else None,
        compact_segmented=compact_segmented,
        canonical_entry=canonical_entry,
        implied_context=implied_context,
        authoritative_clue_updates=authoritative_clue_updates,
        player_text_for_eval="",
        debug_action_kind="start_campaign",
        trace_source="start_campaign",
        trace_action_type="start_campaign",
        request_log_payload=request_log,
        mark_campaign_started=True,
    )
    if not isinstance(result, JSONResponse):
        opening_scope.mark_committed()
    return result
```

## game/gm.py:3824 _safe_json
```python
def _safe_json(
    text: str,
    *,
    require_structured_claims: bool = False,
    provider_response_contract: str = "structured_realization",
) -> Dict[str, Any]:
    """Parse model text into a safe, normalized GM response dict.

    A structured response contributes only its player-facing text. The raw
    envelope is never narration. An unparseable or incomplete envelope is
    rejected so a later seal cannot publish it.

    ``require_structured_claims`` is the live generation path. Plain prose and
    legacy player-facing JSON are structured-contract failures there. Direct
    unit tests may still parse the older shapes.
    """
    if provider_response_contract == "narration_only":
        raw = str(text or "").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return _structured_contract_failure(
                "malformed",
                "malformed_narration_only_envelope",
                provider_response_contract=provider_response_contract,
            )
        if not isinstance(parsed, dict):
            return _structured_contract_failure(
                "malformed",
                "malformed_narration_only_envelope",
                provider_response_contract=provider_response_contract,
            )
        keys = {str(key) for key in parsed}
        if keys != {"narration"}:
            if "declared_claims" in keys:
                reason = "unexpected_declared_claims"
            elif "narration" not in keys:
                reason = "missing_narration"
            else:
                reason = "unexpected_narration_only_field"
            return _structured_contract_failure(
                "structured",
                reason,
                provider_response_contract=provider_response_contract,
            )
        prose = parsed.get("narration")
        if not isinstance(prose, str) or not prose.strip():
            return _structured_contract_failure(
                "structured",
                "missing_narration" if prose is None else "invalid_narration",
                provider_response_contract=provider_response_contract,
            )
        from game.structured_player_output import text_contains_response_envelope

        if text_contains_response_envelope(prose):
            return _structured_contract_failure(
                "structured",
                "nested_response_envelope",
                provider_response_contract=provider_response_contract,
            )
        narration = prose.strip()
        return {
            'player_facing_text': narration,
            'tags': [],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Parsed narration-only model output.',
            'metadata': {
                'output_form': 'structured',
                'provider_response_contract': provider_response_contract,
                'realization_envelope': {
                    'schema_version': 1,
                    'provider_response_contract': provider_response_contract,
                    'declared_claims': [],
                    'narration': narration,
                    'structured_contract_present': True,
                    'legacy_fallback': False,
                    'normalized_empty_declarations': True,
                    'declaration_authorship': False,
                },
            },
        }

    from game.structured_player_output import classify_model_output

    classified = classify_model_output(text)
    form = str(classified.get("form") or "")
    if form == "malformed":
        if require_structured_claims:
            return _structured_contract_failure(
                "malformed",
                "malformed_envelope",
                provider_response_contract=provider_response_contract,
            )
        return {
            'player_facing_text': '',
            'tags': ['structured_output_rejected'],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Rejected structured model envelope.',
            'metadata': {'output_form': 'malformed', 'structured_output_rejected': True},
        }
    if form == "plain":
        if require_structured_claims:
            return _structured_contract_failure(
                "plain",
                "missing_structured_envelope",
                provider_response_contract=provider_response_contract,
            )
        prose = str(classified.get("player_facing_text") or "")
        return {
            'player_facing_text': prose or 'No narration provided.',
            'tags': ['fallback'],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': 'Non-JSON response fallback.',
            'metadata': {'output_form': 'plain', 'legacy_fallback': True},
        }

    parsed = classified.get("fields") if isinstance(classified.get("fields"), dict) else {}
    prose = str(classified.get("player_facing_text") or "")
    declared_claims = parsed.get("declared_claims") if isinstance(parsed.get("declared_claims"), list) else None
    if require_structured_claims and declared_claims is None:
        return _structured_contract_failure(
            "structured",
            "missing_declared_claims",
            provider_response_contract=provider_response_contract,
        )
    proposals = parsed.get("improvisation_proposals") if isinstance(parsed.get("improvisation_proposals"), list) else None
    out: Dict[str, Any] = {
        'player_facing_text': prose,
        'tags': parsed.get('tags') if isinstance(parsed.get('tags'), list) else [],
        'scene_update': parsed.get('scene_update') if isinstance(parsed.get('scene_update'), dict) else None,
        'activate_scene_id': parsed.get('activate_scene_id') if isinstance(parsed.get('activate_scene_id'), str) else None,
        'new_scene_draft': parsed.get('new_scene_draft') if isinstance(parsed.get('new_scene_draft'), dict) else None,
        'world_updates': parsed.get('world_updates') if isinstance(parsed.get('world_updates'), dict) else None,
        'suggested_action': parsed.get('suggested_action') if isinstance(parsed.get('suggested_action'), dict) else None,
        'debug_notes': parsed.get('debug_notes') if isinstance(parsed.get('debug_notes'), str) else 'Parsed model output.',
        'metadata': {
            'output_form': 'structured',
            'provider_response_contract': provider_response_contract,
            'realization_envelope': {
                'schema_version': 1,
                'provider_response_contract': provider_response_contract,
                'declared_claims': declared_claims,
                'narration': prose,
                'structured_contract_present': declared_claims is not None,
                'legacy_fallback': False if require_structured_claims else declared_claims is None,
            },
        },
    }
    if proposals is not None:
        out["improvisation_proposals"] = proposals
    return out
```

## game/gm.py:4192 _opening_max_output_tokens
```python
def _opening_max_output_tokens() -> int:
    """Bound the structured opening allowance independently of ordinary narration."""
    value = int(os.environ.get("ASHEN_OPENING_MAX_OUTPUT_TOKENS", "3000") or "3000")
    if not 1 <= value <= 4096:
        raise ValueError("ASHEN_OPENING_MAX_OUTPUT_TOKENS must be between 1 and 4096")
    return value
```

## game/gm.py:5170 call_gpt
```python
def call_gpt(
    messages: List[Dict[str, str]],
    *,
    purpose: str = "primary_turn",
    response_policy: Optional[Dict[str, Any]] = None,
    segmented_turn: Optional[Dict[str, Any]] = None,
    retry_attempt: int = 0,
    retry_reason: Optional[str] = None,
    strict_social: bool = False,
    force_high_precision: bool = False,
) -> Dict[str, Any]:
    # Wrap the OpenAI call so network/API/model errors do not crash gameplay.
    route = resolve_model_route(
        purpose=purpose,
        response_policy=response_policy,
        segmented_turn=segmented_turn,
        retry_attempt=retry_attempt,
        strict_social=strict_social,
        force_high_precision=force_high_precision,
    )
    from game.provider_budget import (
        accounting_active,
        admit_request,
        provider_retries_disabled,
    )

    if provider_retries_disabled() and int(retry_attempt or 0) > 0:
        return _attach_model_route_metadata(
            {
                "player_facing_text": (
                    "The action stands, and no further narration request was sent."
                ),
                "tags": ["provider_retry_disabled", "deterministic_fallback"],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "provider_retry_disabled",
                "metadata": {"provider_retry_disabled": True},
            },
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
    if os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS", "").strip().lower() in {"1", "true", "yes", "on"}:
        metadata = {
            "provider_calls_disabled": True,
            "provider_accounting": {
                "model": route.selected_model,
                "request_count": 0,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "latency_ms": None,
                "usage_unavailable": True,
            },
        }
        return _attach_model_route_metadata({
            "player_facing_text": (
                "Provider calls are disabled for this run, so no live narration was generated."
            ),
            "tags": ["provider_calls_disabled", "deterministic_fallback"],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": f"provider_calls_disabled:purpose={purpose}",
            "metadata": metadata,
        },
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
    _PROVIDER_CALL_STAMP.set(
        {
            "purpose": str(purpose or "primary_turn"),
            "sent": False,
            "latency_ms": None,
            "input_tokens": None,
            "output_tokens": None,
            "started": time.perf_counter(),
        }
    )
    pinned_model = os.environ.get("ASHEN_PIN_PROVIDER_MODEL", "").strip()
    selected_model = pinned_model or route.selected_model
    requested_response_type = _requested_response_type_from_messages(messages)
    is_opening = requested_response_type == "scene_opening"
    if is_opening:
        # Free-text authored claims are checked by lexical coverage, not a
        # synonym/entailment model. Supply that existing constraint at generation.
        messages = [*messages[:1], {"role": "system", "content": (
            "Opening authored-fact realization: when a supplied authorized claim has an empty "
            "semantic_identity, use its exact text as a separate narration sentence. Keep sensory "
            "texture in separate sentences; do not paraphrase or embellish posted information, "
            "history, causes, or gameplay consequences inside that fact sentence. When declaring "
            "a supplied claim, reference its claim_id in source_claim_id and preserve its provenance, "
            "epistemic status, modality, and premise references. A source reference does not authorize "
            "additional prose. Do not invent claim identifiers or semantic identities. Harmless "
            "sensory expression may remain plain narration within the existing authority rules."
        )}, *messages[1:]]
    narration_cap = (_opening_max_output_tokens() if is_opening else
                     int(os.environ.get("ASHEN_NARRATION_MAX_OUTPUT_TOKENS", "600") or "600"))
    estimated_input = 1
    if accounting_active():
        blob = json.dumps(messages, ensure_ascii=False).encode("utf-8")
        estimated_input = max(1, (len(blob) // 3) + 64)
    attempt = admit_request(owner="gm.call_gpt", model=selected_model, purpose=purpose or "narration", estimated_input=estimated_input, max_output=narration_cap)
    refusal = attempt.refusal
    if refusal:
        from game.provider_budget import sdk_retry_options, PLAYTEST_STOP_MESSAGE
        attempt.finish(
            {
                "purpose": purpose or "narration",
                "sent": False,
                "model": selected_model,
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "refusal": refusal,
            }
        )
        return _attach_model_route_metadata(
            {
                "player_facing_text": (
                    PLAYTEST_STOP_MESSAGE if sdk_retry_options() else "The action was resolved, but live narration was not requested because it would exceed the provider budget."
                ),
                "tags": ["provider_budget_refused", "deterministic_fallback"],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": f"provider_budget_refused:{refusal}",
                "metadata": {"provider_budget_refusal": refusal},
            },
            selected_model=selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
    request_sent = False
    from game.provider_budget import generation_diagnostics_enabled, record_generation_diagnostic
    diagnostic_context = {"stage": "provider_response", "logical_operation": purpose,
                          "requested_response_type": None, "provider_model": selected_model}
    if generation_diagnostics_enabled():
        for message in reversed(messages):
            try:
                payload = json.loads(message.get("content") or "")
            except (ValueError, TypeError):
                continue
            if isinstance(payload, dict):
                requested = (payload.get("response_type_contract") or {}).get("required_response_type")
                if requested in {"scene_opening", "answer", "clarification", "action_result", "npc_dialogue"}:
                    diagnostic_context["requested_response_type"] = requested
                    diagnostic_context["logical_operation"] = requested
                break
    try:
        from openai import OpenAI
        from game.provider_budget import sdk_retry_options
        client = OpenAI(api_key=get_openai_api_key(), timeout=provider_timeout_seconds(), **sdk_retry_options())
        _log_model_route(
            selected_model=selected_model,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
        create_kwargs = {"model": selected_model, "input": messages}
        if accounting_active() or is_opening:
            create_kwargs["max_output_tokens"] = narration_cap
        request_sent = True
        stamp = _PROVIDER_CALL_STAMP.get()
        if isinstance(stamp, dict):
            stamp["sent"] = True
            stamp["started"] = time.perf_counter()
        resp = attempt.dispatch(client.responses.create, **create_kwargs)
        if isinstance(stamp, dict):
            stamp["latency_ms"] = max(0, int(round((time.perf_counter() - float(stamp.get("started") or time.perf_counter())) * 1000)))
        text, extraction = _extract_provider_response_text(resp)
        usage = getattr(resp, "usage", None)
        incoming = getattr(usage, "input_tokens", None) if usage is not None else None
        outgoing = getattr(usage, "output_tokens", None) if usage is not None else None
        total = getattr(usage, "total_tokens", None) if usage is not None else None
        if isinstance(stamp, dict):
            stamp["input_tokens"] = None if incoming is None else int(incoming)
            stamp["output_tokens"] = None if outgoing is None else int(outgoing)
        if accounting_active():
            returned_model = str(getattr(resp, "model", "") or "")
            attempt.finish(
                {
                    "purpose": purpose or "narration",
                    "sent": True,
                    "configured_model": selected_model,
                    "model": returned_model,
                    "request_id": getattr(resp, "id", None),
                    "input_tokens": None if incoming is None else int(incoming),
                    "output_tokens": None if outgoing is None else int(outgoing),
                    "total_tokens": None if total is None else int(total),
                    "max_output_tokens": narration_cap,
                    "model_mismatch": bool(pinned_model and returned_model and not returned_model.startswith(pinned_model)),
                }
            )
        provider_response_contract = _provider_response_contract_from_messages(messages)
        parsed_response = _safe_json(
            text.strip(), require_structured_claims=True,
            provider_response_contract=provider_response_contract,
        )
        # A complete JSON fragment cannot override an explicit incomplete opening.
        # Preserve the normal parser diagnostics, then fail through the existing
        # structured-contract rejection/rollback path without retrying.
        if generation_diagnostics_enabled():
            record_generation_diagnostic({**diagnostic_context, **_generation_response_diagnostic(
                resp, text, extraction, parsed_response,
                maximum=create_kwargs.get("max_output_tokens"), contract=provider_response_contract,
            )}, attempt)
            if is_opening:
                from game.provider_budget import capture_opening_response
                capture_opening_response(text, attempt)
        if is_opening and getattr(resp, "status", None) in {
            "incomplete", "failed", "cancelled", "queued", "in_progress"
        }:
            parsed_response = _structured_contract_failure(
                "structured", "provider_opening_not_completed",
                provider_response_contract=provider_response_contract,
            )
        return _attach_model_route_metadata(
            parsed_response,
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
    except Exception as e:
        record_generation_diagnostic({**diagnostic_context, "classification": "provider_error",
                                     "provider_status": None, "provider_finish_reason": None,
                                     "input_tokens": None, "output_tokens": None, "total_tokens": None,
                                     "requested_max_output_tokens": narration_cap if accounting_active() or is_opening else None,
                                     "rejection_reason": "provider_error"}, attempt)
        stamp = _PROVIDER_CALL_STAMP.get()
        if isinstance(stamp, dict):
            stamp["sent"] = bool(request_sent)
            started = stamp.get("started")
            if isinstance(started, float):
                stamp["latency_ms"] = max(0, int(round((time.perf_counter() - started) * 1000)))
        if accounting_active() and request_sent:
            attempt.finish(
                {
                    "purpose": purpose or "narration",
                    "sent": True,
                    "model": selected_model,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "error": type(e).__name__,
                }
            )
        err = _classify_upstream_gpt_error(e)
        # Return a safe fallback response that preserves the expected schema so
        # callers can continue without special-casing exceptions.
        fallback_metadata = {
            'upstream_api_error': err,
        }
        attach_realization_fallback_family(fallback_metadata, GPT_BUDGET_OR_PROVIDER_FAILURE)
        return _attach_model_route_metadata({
            'player_facing_text': 'The game master is temporarily unavailable. Please try again.',
            'tags': [
                'error',
                f"gpt_api_error:{err['failure_class']}",
                'gpt_api_error_retryable' if err['retryable'] else 'gpt_api_error_nonretryable',
            ],
            'scene_update': None,
            'activate_scene_id': None,
            'new_scene_draft': None,
            'world_updates': None,
            'suggested_action': None,
            'debug_notes': re.sub(
                r"sk-[A-Za-z0-9_\-]{8,}|Bearer\s+\S+",
                "[REDACTED]",
                (
                    f"call_gpt error: {repr(e)} | "
                    f"api_error_class={err['failure_class']}:retryable={err['retryable']}"
                ),
                flags=re.IGNORECASE,
            ),
            'metadata': fallback_metadata,
        },
            selected_model=route.selected_model,
            route_reason=route.route_reason,
            route_family=route.route_family,
            purpose=purpose,
            retry_attempt=retry_attempt,
            retry_reason=retry_reason,
            strict_social=strict_social,
            force_high_precision=force_high_precision,
        )
```

## game/gm_resolution_decision.py:1012 _empty_identity_covers
```python
def _empty_identity_covers(sentence: str, fact: str) -> bool:
    """Lexical compatibility for an authored fact that has no semantic identity.

    The sentence may drop content words from the fact. It may add at most one
    content word. A second proposition does not inherit the fact's authority.
    This is token overlap, not synonym or entailment inference.
    """
    sentence_tokens = _token_set(sentence)
    fact_tokens = _token_set(fact)
    if len(fact_tokens) < 3 and len(sentence_tokens) < 3:
        return False
    extra = sentence_tokens - fact_tokens
    if len(sentence_tokens) >= 3 and not extra and sentence_tokens <= fact_tokens:
        return True
    if len(extra) > 1:
        return False
    normalized_fact = fact.lower().strip(" .!?")
    if len(fact_tokens) >= 3 and normalized_fact and normalized_fact in sentence.lower():
        return True
    if len(fact_tokens) >= 3 and fact_tokens <= sentence_tokens:
        return True
    return bool(
        len(fact_tokens) >= 4
        and len(fact_tokens & sentence_tokens) >= max(3, len(fact_tokens) - 1)
    )
```

## game/gm_resolution_decision.py:1645 _proposition_restates_statement
```python
def _proposition_restates_statement(sentence: str, statement: str) -> bool:
    """True when the sentence repeats an authorized statement without adding content words.

    Words may be dropped. A second proposition does not inherit the statement.
    Quoted speech is compared without the speaker frame or the realization wrapper.
    """
    proposition = _quoted_proposition(sentence) if _QUOTE_SPAN_RE.search(sentence or "") else str(sentence or "")
    proposition = _REALIZATION_WRAPPER_RE.sub("", proposition).strip()
    fact_tokens = _token_set(statement)
    prop_tokens = _token_set(proposition)
    if len(fact_tokens) < 3 or not prop_tokens:
        return False
    if prop_tokens <= fact_tokens and len(prop_tokens & fact_tokens) >= max(3, len(fact_tokens) - 1):
        return True
    return _norm_phrase(statement) == _norm_phrase(proposition)
```

## game/gm_resolution_decision.py:2595 build_gm_resolution_decision
```python
def build_gm_resolution_decision(
    *,
    resolution: Mapping[str, Any] | None,
    session: Mapping[str, Any] | None = None,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    normalized_action: Mapping[str, Any] | None = None,
) -> GMResolutionDecision | None:
    """Build the decision from the existing Resolution Contract and state.

    ``session`` and ``normalized_action`` are accepted for call-site symmetry;
    raw player text is intentionally not an input.
    """
    contract = contract_mapping_from_resolution(resolution if isinstance(resolution, Mapping) else None)
    if not contract.get("contract_id"):
        return None
    if session is not None and isinstance(contract, dict):
        contract = {**contract, "session": session}
    return _decision_from_contract(contract, resolution=resolution, scene=scene, world=world)
```

## game/gm_resolution_decision.py:3337 audit_narration_against_decision
```python
def audit_narration_against_decision(
    text: str | None,
    *,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
) -> dict[str, Any]:
    rows: list[GMProposedFact] = []
    claim_rows: list[NarratedClaim] = []
    violations: list[dict[str, Any]] = []
    full = text or ""
    for sentence in _sentences(full):
        claims = audit_narrated_claims(
            sentence,
            decision=decision,
            authored_corpus=authored_corpus,
            response_text=full,
        )
        claim_rows.extend(claims)
        fact = classify_narrated_fact(
            sentence,
            decision=decision,
            authored_corpus=authored_corpus,
            response_text=full,
        )
        if fact is None:
            continue
        rows.append(fact)
        if not fact.authorized:
            violations.append(fact.as_dict())
    obligations = _executable_obligations(decision)
    if (
        isinstance(obligations.get("supporting"), list)
        and len((full or "").split()) >= 8
        and not narration_acknowledges_supporting(full, obligations)
    ):
        violations.append(
            _unauthorized_fact(full, ["supporting_obligation_unacknowledged"]).as_dict()
        )
    return {
        "decision_id": str((decision or {}).get("contract_id") or ""),
        "hard_valid": not violations,
        "violations": violations,
        "proposed_facts": [row.as_dict() for row in rows],
        "claim_results": [row.as_dict() for row in claim_rows],
    }
```

## game/gm_resolution_decision.py:3667 _declared_identity_matches_realization
```python
def _declared_identity_matches_realization(
    declared: DeclaredRealizationClaim,
    claim: Mapping[str, Any],
) -> bool:
    if declared.source_claim_id and declared.source_claim_id == str(claim.get("claim_id") or ""):
        return True
    identity = claim.get("semantic_identity") if isinstance(claim.get("semantic_identity"), Mapping) else {}
    if identity and declared.semantic_identity:
        text = " ".join(
            part
            for part in (declared.text, " ".join(str(v) for v in declared.semantic_identity.values() if isinstance(v, str)))
            if part
        )
        if text and _semantic_identity_matches(text, identity):
            return True
        if _identity_compatible(declared.semantic_identity, identity):
            return True
    claim_text = _clean(claim.get("text"), limit=600)
    if declared.text and claim_text and _norm_phrase(declared.text) == _norm_phrase(claim_text):
        return True
    return bool(declared.text and claim_text and (_empty_identity_covers(declared.text, claim_text) or _empty_identity_covers(claim_text, declared.text)))
```

## game/gm_resolution_decision.py:3797 validate_declared_claims_against_decision
```python
def validate_declared_claims_against_decision(
    declared_claims: Sequence[Mapping[str, Any] | DeclaredRealizationClaim] | None,
    *,
    decision: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate model-declared consequential semantics before prose authority.

    Declarations expose intent; they do not grant authority. Accepted output rows
    are the only declaration-derived claims eligible for temporal persistence.
    """
    if declared_claims is None:
        return {
            "schema_version": STRUCTURED_ENVELOPE_VERSION,
            "structured_contract_present": False,
            "hard_valid": True,
            "accepted_claims": [],
            "rejected_claims": [],
            "violations": [],
        }
    if not isinstance(declared_claims, Sequence) or isinstance(declared_claims, (str, bytes)):
        return {
            "schema_version": STRUCTURED_ENVELOPE_VERSION,
            "structured_contract_present": True,
            "hard_valid": False,
            "accepted_claims": [],
            "rejected_claims": [],
            "violations": [{"reason_codes": ["malformed_declared_claims"], "text": ""}],
        }
    realization_claims = [
        row for row in ((decision or {}).get("realization_claims") or []) if isinstance(row, Mapping)
    ]
    parsed_declared = [
        item if isinstance(item, DeclaredRealizationClaim) else declared_claim_from_mapping(item, index)
        for index, item in enumerate(declared_claims)
        if isinstance(item, (DeclaredRealizationClaim, Mapping))
    ]
    catalog = _premise_catalog(decision, [row for row in parsed_declared if isinstance(row, DeclaredRealizationClaim)])
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for index, item in enumerate(declared_claims):
        declared = item if isinstance(item, DeclaredRealizationClaim) else declared_claim_from_mapping(item, index) if isinstance(item, Mapping) else None
        if declared is None or not declared.declaration_mode:
            row = {"text": "", "reason_codes": ["malformed_declared_claim"], "authorized": False}
            rejected.append(row)
            violations.append(row)
            continue
        if declared.declaration_mode == DECLARATION_MODE_PROPOSE:
            allowed, reasons = _proposal_is_bounded_inference(declared, decision)
            premise_reasons = _embedded_premise_reasons(
                declared,
                {
                    "text": declared.text,
                    "relation_kind": declared.relation_kind,
                    "epistemic_status": declared.epistemic_status,
                    "premise_claim_ids": list(declared.premise_claim_ids),
                    "realization_role": declared.realization_role,
                },
                catalog,
            ) if allowed else []
            if allowed and not premise_reasons:
                accepted.append(_accepted_proposal_claim(declared))
            else:
                row = {
                    **declared.as_dict(),
                    "authorized": False,
                    "authority": AUTH_UNAUTHORIZED,
                    "reason_codes": premise_reasons or reasons or ["unauthorized_declared_proposal"],
                }
                rejected.append(row)
                violations.append(row)
            continue
        matches = [claim for claim in realization_claims if _declared_identity_matches_realization(declared, claim)]
        if not matches:
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["unauthorized_declared_claim"],
            }
            rejected.append(row)
            violations.append(row)
            continue
        match = matches[0]
        if _declaration_modality_rank(declared) > _claim_modality_rank(match):
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["modality_strengthening"],
                "matched_claim_id": match.get("claim_id"),
            }
            rejected.append(row)
            violations.append(row)
            continue
        if (
            str(match.get("provenance") or "") == PROVENANCE_PLAYER_HYPOTHESIS
            and _declaration_modality_rank(declared) >= 3
        ):
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["player_hypothesis_self_promotion"],
                "matched_claim_id": match.get("claim_id"),
            }
            rejected.append(row)
            violations.append(row)
            continue
        premise_reasons = _embedded_premise_reasons(declared, match, catalog)
        if premise_reasons:
            row = {
                **declared.as_dict(),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": premise_reasons,
                "matched_claim_id": match.get("claim_id"),
            }
            rejected.append(row)
            violations.append(row)
            continue
        accepted.append(_realization_claim_to_narrated_claim(match, declared))
    return {
        "schema_version": STRUCTURED_ENVELOPE_VERSION,
        "structured_contract_present": True,
        "hard_valid": not violations,
        "accepted_claims": accepted,
        "rejected_claims": rejected,
        "violations": violations,
    }
```

## game/gm_resolution_decision.py:3971 _undeclared_consequential_violations
```python
def _undeclared_consequential_violations(
    narration_audit: Mapping[str, Any],
    accepted_claims: Sequence[Mapping[str, Any]] | None,
    narration: str | None = None,
    decision: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    accepted_texts = {
        _norm_phrase(row.get("text"))
        for row in (accepted_claims or [])
        if isinstance(row, Mapping) and _norm_phrase(row.get("text"))
    }
    violations: list[dict[str, Any]] = []
    for row in narration_audit.get("claim_results") or []:
        if not isinstance(row, Mapping) or row.get("authorized") is not True:
            continue
        text = _clean(row.get("text"), limit=600)
        if not text or _norm_phrase(text) in accepted_texts:
            continue
        authority = str(row.get("authority") or "")
        relation_kind = str(row.get("relation_kind") or "")
        consequential = []
        consequential.extend(_unlicensed_consequential_reasons(text, decision))
        consequential.extend(_structured_consequential_reasons(text))
        if _NEGATIVE_EVIDENCE_RE.search(text):
            consequential.append("negative_evidence")
        if _SPECIFIC_LEAD_RE.search(text):
            consequential.append("specific_gameplay_lead")
        if _UNDECLARED_CAUSAL_AGENT_RE.search(text):
            consequential.append("undeclared_causal_agent")
        existence_only = _existence_mention(row)
        restates_authorized = any(
            _proposition_restates_statement(text, statement) for statement in _authorized_statement_texts(decision)
        )
        if existence_only:
            if _EXISTENCE_ACTION_RE.search(_outside_quotes(text)):
                consequential.append("unauthorized_npc_action")
        elif restates_authorized and authority == AUTH_WORLD:
            pass
        elif authority == AUTH_WORLD or relation_kind in {REL_CAUSAL, REL_EVIDENTIAL, REL_GAMEPLAY_LEAD}:
            consequential.append("authorized_consequential_claim")
        if authority == AUTH_CLAIM and _STATEFUL_ASSERTION_RE.search(text) and not restates_authorized:
            consequential.append("consequential_npc_claim")
        if _IGNORANCE_SEAL_RE.search(text) and not restates_authorized:
            consequential.append("ignorance_not_authorized_answer")
        if not consequential:
            continue
        violations.append(
            {
                **dict(row),
                "authorized": False,
                "authority": AUTH_UNAUTHORIZED,
                "reason_codes": ["undeclared_consequential_claim"],
            }
        )
    for sentence in _sentences(narration):
        norm = _norm_phrase(sentence)
        if not norm or any(text and text in norm for text in accepted_texts):
            continue
        reasons: list[str] = []
        if _UNDECLARED_CAUSAL_AGENT_RE.search(sentence):
            reasons.append("undeclared_causal_agent")
        if _NEGATIVE_EVIDENCE_RE.search(sentence):
            reasons.append("undeclared_negative_evidence")
        if _SPECIFIC_LEAD_RE.search(sentence):
            reasons.append("undeclared_specific_gameplay_lead")
        if _IGNORANCE_SEAL_RE.search(sentence) and not any(
            _proposition_restates_statement(sentence, statement)
            for statement in _authorized_statement_texts(decision)
        ):
            reasons.append("ignorance_not_authorized_answer")
        if not reasons:
            continue
        violations.append(
            _claim(
                sentence,
                reasons=["undeclared_consequential_claim", *reasons],
                relation_kind=REL_PREDICATE,
            ).as_dict()
        )
    return violations
```

## game/gm_resolution_decision.py:4053 audit_realization_envelope_against_decision
```python
def audit_realization_envelope_against_decision(
    *,
    narration: str | None,
    declared_claims: Sequence[Mapping[str, Any] | DeclaredRealizationClaim] | None,
    decision: Mapping[str, Any] | None,
    authored_corpus: str = "",
) -> dict[str, Any]:
    declaration = validate_declared_claims_against_decision(declared_claims, decision=decision)
    if not declaration.get("hard_valid"):
        return {
            "decision_id": str((decision or {}).get("contract_id") or ""),
            "hard_valid": False,
            "declaration_validation": declaration,
            "narration_validation": None,
            "violations": list(declaration.get("violations") or []),
            "claim_results": list(declaration.get("accepted_claims") or []) + list(declaration.get("rejected_claims") or []),
            "accepted_realized_claims": [],
        }
    effective_decision = _decision_with_accepted_declarations(decision, declaration.get("accepted_claims"))
    narration_audit = audit_narration_against_decision(
        narration,
        decision=effective_decision,
        authored_corpus=authored_corpus,
    )
    undeclared = _undeclared_consequential_violations(
        narration_audit,
        declaration.get("accepted_claims") if isinstance(declaration, Mapping) else [],
        narration=narration,
        decision=effective_decision,
    )
    premise_violations = _narration_premise_ceiling_violations(
        narration,
        decision,
        declaration.get("accepted_claims") if isinstance(declaration, Mapping) else [],
        declared_claims,
    )
    narration_valid = bool(narration_audit.get("hard_valid")) and not undeclared and not premise_violations
    return {
        "decision_id": str((decision or {}).get("contract_id") or ""),
        "hard_valid": narration_valid,
        "declaration_validation": declaration,
        "narration_validation": narration_audit,
        "violations": list(narration_audit.get("violations") or []) + undeclared + premise_violations,
        "proposed_facts": list(narration_audit.get("proposed_facts") or []),
        "claim_results": list(declaration.get("accepted_claims") or []) + list(narration_audit.get("claim_results") or []) + undeclared + premise_violations,
        "accepted_realized_claims": [
            row for row in (declaration.get("accepted_claims") or []) if isinstance(row, Mapping)
        ],
    }
```

## game/gm_resolution_decision.py:4154 remember_temporal_claims
```python
def remember_temporal_claims(
    session: dict[str, Any] | None,
    *,
    claims: Sequence[Mapping[str, Any]] | None,
    scene_id: str | None = None,
    source_turn: int | None = None,
    cap: int = 24,
) -> dict[str, Any]:
    """Persist claim status without promoting it to world truth."""
    if not isinstance(session, dict):
        return {}
    record = ensure_temporal_provenance(session)
    sid = _clean(scene_id or session.get("active_scene_id"), limit=80)
    turn = source_turn if isinstance(source_turn, int) else session.get("turn_counter")
    for claim in claims or []:
        if not isinstance(claim, Mapping):
            continue
        authority = str(claim.get("authority") or "")
        provenance = str(claim.get("provenance") or "")
        authorized = bool(claim.get("authorized"))
        item = {
            "semantic_identity": dict(claim.get("semantic_identity") or {}) if isinstance(claim.get("semantic_identity"), Mapping) else {},
            "text": _clean(claim.get("text"), limit=300),
            "authority": authority,
            "provenance": provenance,
            "epistemic_status": str(claim.get("epistemic_status") or ""),
            "relation_kind": str(claim.get("relation_kind") or ""),
            "scene_id": sid or None,
            "source_turn": turn if isinstance(turn, int) else None,
        }
        if authorized and authority == AUTH_INCIDENTAL:
            bucket = "accepted_incidentals"
        elif authorized and provenance == PROVENANCE_GM_INFERENCE:
            bucket = "gm_inferences"
        elif authorized and provenance == PROVENANCE_PLAYER_HYPOTHESIS:
            bucket = "player_hypotheses"
        elif not authorized:
            item["reason_codes"] = list(claim.get("reason_codes") or [])
            bucket = "rejected_consequential"
        else:
            continue
        fingerprint = (
            _norm_phrase(item.get("text")),
            str(item.get("provenance") or ""),
            str(item.get("authority") or ""),
            item.get("source_turn"),
        )
        if any(
            (
                _norm_phrase(existing.get("text")),
                str(existing.get("provenance") or ""),
                str(existing.get("authority") or ""),
                existing.get("source_turn"),
            )
            == fingerprint
            for existing in record[bucket]
            if isinstance(existing, Mapping)
        ):
            continue
        record[bucket].append(item)
        if len(record[bucket]) > max(1, cap):
            del record[bucket][:-max(1, cap)]
    return record
```

## game/immutable_valid_response.py:623 validate_generated_response
```python
def validate_generated_response(
    text: str | None,
    *,
    contract: Mapping[str, Any] | None = None,
    decision: Mapping[str, Any] | None = None,
    declared_claims: list[Mapping[str, Any]] | None = None,
    player_text: str | None = None,
    resolution: Mapping[str, Any] | None = None,
    referents: list[Mapping[str, Any]] | None = None,
    authored_corpus: str = "",
    present_addressee: str = "",
    dead_actor_labels: list[str] | None = None,
) -> dict[str, Any]:
    """High-confidence hard invalidity only.

    Low-confidence lexical suspicions are soft flags. They do not reject.
    """
    from game.interaction_completion import (
        attribution_shell,
        attributed_speaker_label,
        passive_observation,
        player_utterance_embedded,
        recommends_locating_interlocutor,
        response_attributes_npc_speech,
    )

    raw = str(text or "")
    reasons: list[str] = []
    soft: list[str] = []
    operation = _operation(contract)
    player = str(player_text or (contract or {}).get("raw_input") or "")

    from game.structured_player_output import text_contains_response_envelope

    if text_contains_response_envelope(raw):
        reasons.append("structured_envelope")
    if _malformed(raw):
        reasons.append("malformed_or_truncated")
    if _LEAK_RE.search(raw):
        reasons.append("hidden_information")
    if player_utterance_embedded(raw, player) and _SPLICE_TEMPLATE_RE.search(raw):
        reasons.append("player_text_splice")
    elif player_utterance_embedded(raw, player):
        soft.append("player_echo")
    if operation == "ask" and (_speech_shell(raw) or attribution_shell(raw) and _SPEECH_ATTRIB_RE.search(raw)):
        reasons.append("interaction_incomplete")
    if operation == "ask" and passive_observation(raw):
        reasons.append("interaction_incomplete")
    if _perception_dimension_miss(raw, contract, player_text=player):
        reasons.append("interaction_incomplete")
    if operation in {"inspect", "perceive", "act", "follow"} and response_attributes_npc_speech(raw):
        reasons.append("unsolicited_npc_speech")
    # Reject explicit internal stage headings before sealing. A later sanitizer
    # cannot strip them without violating accepted-response integrity.
    if _HARD_META_VOICE_RE.search(raw) or _INTERNAL_STAGE_LABEL_RE.search(_outside_quotes(raw)):
        reasons.append("malformed_or_truncated")

    explicit = _explicit_addressee(player, referents)
    contract_label = _speaker_constraint_label(contract)
    addressee = explicit or present_addressee or contract_label
    speaker = attributed_speaker_label(raw)
    unresolved_addressee = _unresolved_explicit_addressee(contract)
    social = resolution.get("social") if isinstance(resolution, Mapping) else None
    known_social = (isinstance(social, Mapping) and social.get("target_resolved") is True
                    and social.get("npc_id") == (contract or {}).get("interlocutor_id"))
    if known_social:
        addressee = str(social.get("npc_name") or social.get("npc_id"))
        authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else None
        speaker_name = str(social.get("npc_name") or "").strip().lower()
        incidental_reaction = bool(
            isinstance(authority, Mapping)
            and authority.get("improvisation_permitted")
            and speaker_name
            and speaker_name in raw.lower()
        )
        if operation == "ask" and not response_attributes_npc_speech(raw) and not incidental_reaction:
            reasons.append("interaction_incomplete")
        if re.search(r"\b(?:no one here|nobody here|person you addressed cannot be identified)\b", raw, re.I):
            reasons.append("authoritative_target_contradiction")
        if isinstance(authority, Mapping):
            from game.dialogue_authority import dialogue_rejection_reasons

            for reason in dialogue_rejection_reasons(raw, authority=authority):
                reasons.append(reason)
    if ((contract or {}).get("construction") or {}).get("authority_conflict"):
        reasons.append("conflicting_target_authorities")
    if speaker and unresolved_addressee and _unresolved_addressee_conflict(speaker, unresolved_addressee):
        reasons.append("wrong_interlocutor")
    elif speaker and addressee and _speaker_conflicts(speaker, addressee, referents):
        reasons.append("wrong_interlocutor")

    locate_labels = [label for label in (explicit, present_addressee, contract_label) if label]
    if same_clause_locates(raw, locate_labels):
        reasons.append("locate_present_interlocutor")
    elif (
        _YOU_RE.search(player)
        and _NO_ONE_RE.search(raw)
        and same_clause_locates(raw, ["guard captain", "the captain"])
    ):
        reasons.append("locate_present_interlocutor")
    elif isinstance(contract, Mapping) and recommends_locating_interlocutor(raw, contract):
        soft.append("low_confidence_locate")

    narrator = _outside_quotes(raw)
    clock = _CLOCK_RE.search(narrator)
    if clock and clock.group(0).lower() not in str(authored_corpus or "").lower():
        reasons.append("consequential_invention")

    from game.interpretation_proposal import referential_action_shape
    from game.resolution_contract import _LITERAL_STEP_RE

    if referential_action_shape(player) and _LITERAL_STEP_RE.search(raw):
        reasons.append("consequential_invention")

    from game.proposition_authority import classify_propositions, unauthorized_authoritative_rules

    authority = classify_propositions(raw, authored_corpus=authored_corpus)
    if unauthorized_authoritative_rules(raw, authored_corpus):
        reasons.append("ungrounded_authoritative_rule")
    if decision is not None:
        from game.gm_resolution_decision import decision_with_selected_social_topic

        decision = decision_with_selected_social_topic(decision, resolution)
        if declared_claims is not None:
            from game.gm_resolution_decision import audit_realization_envelope_against_decision

            decision_audit = audit_realization_envelope_against_decision(
                narration=raw,
                declared_claims=declared_claims,
                decision=decision,
                authored_corpus=authored_corpus,
            )
        else:
            from game.gm_resolution_decision import audit_narration_against_decision

            decision_audit = audit_narration_against_decision(
                raw,
                decision=decision,
                authored_corpus=authored_corpus,
            )
        if not decision_audit.get("hard_valid"):
            reasons.append("unauthorized_resolution_decision_fact")
        from game.gm_resolution_decision import _IGNORANCE_SEAL_RE, authorized_observation_line

        # Ignorance must not seal over an authorized observation the player asked for.
        if _IGNORANCE_SEAL_RE.search(raw or ""):
            observed = authorized_observation_line(decision, player)
            observed_norm = " ".join(str(observed or "").lower().split())
            raw_norm = " ".join(str(raw or "").lower().split())
            if observed_norm and observed_norm not in raw_norm:
                if "unauthorized_resolution_decision_fact" not in reasons:
                    reasons.append("unauthorized_resolution_decision_fact")
    else:
        decision_audit = None

    if _unresolved_travel_arrival(raw, resolution):
        reasons.append("consequential_invention")

    success = _mechanical_success(resolution)
    if success is False and _SUCCESS_NARRATION_RE.search(raw) and not _NEGATION_RE.search(raw):
        reasons.append("mechanical_contradiction")
    if success is True and _FAILURE_NARRATION_RE.search(raw):
        reasons.append("mechanical_contradiction")

    for label in dead_actor_labels or []:
        if not str(label).strip():
            continue
        if re.search(
            rf"\b{re.escape(str(label))}\b.{{0,48}}\b(?:says|said|replies|replied|answers)\b",
            raw,
            re.IGNORECASE,
        ):
            reasons.append("impossible_entity_state")
            break

    # De-duplicate while keeping order.
    ordered: list[str] = []
    for reason in reasons:
        if reason not in ordered:
            ordered.append(reason)
    hard_valid = not ordered
    return {
        "hard_valid": hard_valid,
        "reasons": ordered,
        "soft_flags": soft,
        "speaker": speaker,
        "addressee": addressee,
        "operation": operation,
        "interaction_complete": "interaction_incomplete" not in ordered and "malformed_or_truncated" not in ordered,
        "contract_satisfying": hard_valid,
        "authority": authority,
        "gm_resolution_decision_audit": decision_audit,
    }
```

## game/immutable_valid_response.py:1609 run_preserve_if_valid
```python
def run_preserve_if_valid(
    gm: dict[str, Any],
    *,
    regenerate: Callable[[str], dict[str, Any] | None] | None,
    resolution: Mapping[str, Any] | None,
    player_text: str,
    scene: Mapping[str, Any] | None = None,
    world: Mapping[str, Any] | None = None,
    session: Mapping[str, Any] | None = None,
    referents: list[Mapping[str, Any]] | None = None,
    authored_corpus: str = "",
    present_addressee: str = "",
    dead_actor_labels: list[str] | None = None,
    visible_facts: list[str] | None = None,
) -> dict[str, Any]:
    """Generate is already done. Validate, preserve, or retry once."""
    if not isinstance(gm, dict):
        return gm
    adopted = adopt_host_speech(gm, resolution=resolution, player_text=player_text, session=session, world=world)
    if adopted is not None:
        return adopted
    contract = _contract_from_resolution(resolution)
    try:
        from game.gm_resolution_decision import decision_from_resolution

        gm_decision = decision_from_resolution(resolution)
    except Exception:
        gm_decision = {}
    catalog = referents if referents is not None else _referents_for(resolution, scene, world, session)
    corpus = authored_corpus or _authored_corpus(scene)
    facts = visible_facts if visible_facts is not None else _visible_facts(scene)
    player = str(player_text or contract.get("raw_input") or "")
    gm = _project_authorized_social_answer_before_seal(
        gm,
        resolution=resolution,
        player_text=player,
        scene=scene,
        world=world,
        session=session,
    )
    if isinstance(resolution, Mapping) and not isinstance(resolution.get("social"), Mapping):
        # Preserve resolver observations before validation, never by overwriting
        # an already adopted generic sentence downstream.
        from game.api_turn_support import _authoritative_resolution_fact_text, _looks_like_generic_resolution_fallback

        fact, _source = _authoritative_resolution_fact_text(resolution=resolution, scene=scene, world=world)
        if fact:
            # This is the selected public resolver result, not a provider fact
            # or the complete (possibly hidden) clue catalog.
            corpus = corpus + "\n" + fact
            if _source.get("source") == "clue_text" and gm_decision:
                selected = str(resolution.get("clue_text") or "").strip()
                if not selected:
                    selected = " ".join(str(item) for item in resolution.get("discovered_clues") or [])
                if selected:
                    gm_decision = copy.deepcopy(gm_decision)
                    gm_decision.setdefault("proposed_facts", []).append({
                        "text": selected, "provenance": "authored_world_fact", "consequence": "consequential",
                        "authorized": True, "authority": "world_truth", "persistence": "do_not_persist",
                        "source_ref": "resolution.clue_text", "outcome_classification": "established_or_retrieved",
                        "reason_codes": ["resolver_selected_public_clue"], "semantic_identity": {}})
        if _looks_like_generic_resolution_fallback(str(gm.get("player_facing_text") or "")):
            if fact:
                gm = {**gm, "player_facing_text": fact}

    def _check(candidate: dict[str, Any]) -> dict[str, Any]:
        candidate_meta = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
        realization_envelope = (
            candidate_meta.get("realization_envelope")
            if isinstance(candidate_meta.get("realization_envelope"), Mapping)
            else {}
        )
        declared = (
            realization_envelope.get("declared_claims")
            if isinstance(realization_envelope.get("declared_claims"), list)
            else None
        )
        verdict = validate_generated_response(
            str(candidate.get("player_facing_text") or ""),
            contract=contract,
            decision=gm_decision or None,
            declared_claims=declared,
            player_text=player,
            resolution=resolution,
            referents=catalog,
            authored_corpus=corpus,
            present_addressee=present_addressee,
            dead_actor_labels=dead_actor_labels,
        )
        leak_reasons = []
        if isinstance(candidate_meta, Mapping):
            leak_reasons = list(candidate_meta.get("content_leak_reasons") or [])
        if _unsupported_perception(
            str(candidate.get("player_facing_text") or ""),
            resolution=resolution,
            scene=scene,
            world=world,
            session=session,
        ):
            reasons = list(verdict.get("reasons") or [])
            if "consequential_invention" not in reasons:
                reasons.append("consequential_invention")
            verdict = {
                **verdict,
                "hard_valid": False,
                "reasons": reasons,
                "contract_satisfying": False,
            }
        if leak_reasons:
            reasons = list(verdict.get("reasons") or [])
            if "hidden_information" not in reasons:
                reasons.append("hidden_information")
            verdict = {
                **verdict,
                "hard_valid": False,
                "reasons": reasons,
                "contract_satisfying": False,
            }
        if isinstance(candidate_meta, Mapping) and candidate_meta.get("structured_contract_failure"):
            reasons = list(verdict.get("reasons") or [])
            if "structured_contract_failure" not in reasons:
                reasons.append("structured_contract_failure")
            verdict = {
                **verdict,
                "hard_valid": False,
                "reasons": reasons,
                "contract_satisfying": False,
            }
        return verdict

    first = _check(gm)
    if isinstance(resolution, Mapping) and resolution.get("kind") == "scene_opening":
        from game.provider_budget import observe_opening_semantics

        envelope = (gm.get("metadata") or {}).get("realization_envelope") or {}
        declarations = envelope.get("declared_claims")
        observe_opening_semantics({
            "semantic_classification": "candidate_valid" if first["hard_valid"] else "candidate_rejected",
            "classification_source": "game.immutable_valid_response.run_preserve_if_valid._check",
            "classification_reason": "hard_validation_passed" if first["hard_valid"] else "hard_validation_failed",
            "semantic_reasons": list(first.get("reasons") or []),
            "narration_present": bool(gm.get("player_facing_text")),
            "narration_length": len(str(gm.get("player_facing_text") or "")),
            "declarations_present": isinstance(declarations, list),
            "declaration_count": len(declarations) if isinstance(declarations, list) else None,
        })
    metadata = gm.setdefault("metadata", {})
    if isinstance(metadata, dict):
        metadata["hard_validation_attempt_1"] = {
            "hard_valid": first["hard_valid"],
            "reasons": list(first["reasons"]),
            "soft_flags": list(first["soft_flags"]),
            "text": str(gm.get("player_facing_text") or "")[:2000],
        }
    review: dict[str, Any] = {
        "governing_decision_contract_id": str((gm_decision or {}).get("contract_id") or ""),
        "outcome_classification": str((gm_decision or {}).get("outcome_classification") or ""),
        "attempt_1": {
            "text": str(gm.get("player_facing_text") or "")[:2000],
            "reasons": list(first.get("reasons") or []),
            "gm_resolution_decision_audit": first.get("gm_resolution_decision_audit"),
        },
        "retry_context": "",
        "attempt_2": None,
        "acceptance": {"why": "initial_hard_valid"},
    }

    def _finish(sealed: dict[str, Any], *, why: str) -> dict[str, Any]:
        terminal = (sealed.get("metadata") or {}).get(ACCEPTED_KEY) or {}
        if terminal.get("provenance") == PROVENANCE_REJECTED:
            # Conflicting NPC authority can invalidate even a generic line in
            # the NPC validator. The host may only select this fixed GM safety
            # response, with no NPC attribution or state effects.
            rejected = copy.deepcopy(terminal)
            seal_accepted_response(sealed, text=TERMINAL_FALLBACK, provenance=PROVENANCE_SAFE,
                attempt=int((sealed.get("metadata") or {}).get("generation_attempt_count") or 1),
                validation={"hard_valid": True, "speaker": "GM", "addressee": "player",
                            "authority": ["host_terminal_safety"], "reasons": [],
                            "interaction_complete": False, "contract_satisfying": False},
                contract=contract, player_text=player, resolution=resolution)
            record = sealed["metadata"][ACCEPTED_KEY]
            record.update(speaker_id="", subject="", authority_result="safe_nonresolution", authorization_source="host_terminal_safety",
                          candidate_disposition="rejected", rejected_candidate=rejected)
            for key in ("scene_update", "world_updates", "activate_scene_id", "new_scene_draft", "suggested_action"):
                sealed[key] = None
        review["acceptance"] = {"why": why, "text": str(sealed.get("player_facing_text") or "")[:2000]}
        sealed_meta = sealed.setdefault("metadata", {})
        if isinstance(sealed_meta, dict):
            sealed_meta["decision_review"] = review
            record = sealed_meta.get(ACCEPTED_KEY)
            if isinstance(record, dict):
                hard = record.setdefault("hard_validation", {})
                if isinstance(hard, dict):
                    if hard.get("gm_resolution_decision_audit") is None:
                        hard["gm_resolution_decision_audit"] = {
                            "decision_id": review["governing_decision_contract_id"],
                            "source": "decision_review",
                            "attempt_1": review["attempt_1"],
                            "attempt_2": review["attempt_2"],
                            "retry_context_present": bool(review.get("retry_context")),
                            "acceptance_why": why,
                        }
                    hard["decision_acceptance_why"] = why
        seal_delivery_contract(sealed)
        if isinstance(resolution, Mapping) and resolution.get("kind") == "scene_opening":
            from game.provider_budget import observe_opening_semantics

            record = (sealed.get("metadata") or {}).get(ACCEPTED_KEY) or {}
            observe_opening_semantics({
                "semantic_classification": record.get("provenance"),
                "classification_source": "game.immutable_valid_response.run_preserve_if_valid._finish",
                "classification_reason": why,
                "nonresolution_origin": "application" if record.get("provenance") == PROVENANCE_SAFE else None,
            })
        return sealed

    if first["hard_valid"]:
        social = resolution.get("social") if isinstance(resolution, Mapping) else None
        authority = social.get("dialogue_authority") if isinstance(social, Mapping) else None
        from game.conversational_continuity import bounded_personal_line, is_unhelpful_personal_ignorance

        if is_unhelpful_personal_ignorance(str(gm.get("player_facing_text") or ""), authority if isinstance(authority, Mapping) else None):
            kind = str((authority or {}).get("requested_information") or "opinion")
            name = str(social.get("npc_name") or "They") if isinstance(social, Mapping) else "They"
            npc_id = str(social.get("npc_id") or "") if isinstance(social, Mapping) else ""
            recovered_line = bounded_personal_line(name, npc_id, kind)
            checked = _check({"player_facing_text": recovered_line, "metadata": {}})
            if checked.get("hard_valid"):
                sealed = seal_accepted_response(
                    gm,
                    text=recovered_line,
                    provenance=PROVENANCE_INITIAL,
                    attempt=1,
                    validation=checked,
                    contract=contract,
                    player_text=player,
                    resolution=resolution,
                )
                return _finish(sealed, why="incidental_personal_recovery")
        sealed = seal_accepted_response(
            gm,
            text=str(gm.get("player_facing_text") or ""),
            provenance=PROVENANCE_INITIAL,
            attempt=1,
            validation=first,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="initial_hard_valid")

    mark_candidate_rejected(gm, str(gm.get("player_facing_text") or ""), first["reasons"])
    feedback = regeneration_feedback(
        first["reasons"],
        resolution=resolution,
        audit=first.get("gm_resolution_decision_audit") if isinstance(first.get("gm_resolution_decision_audit"), Mapping) else None,
        provider_response_contract=str(metadata.get("provider_response_contract") or ""),
    )
    review["retry_context"] = feedback
    if isinstance(metadata, dict):
        metadata["regeneration_feedback"] = feedback
        metadata["regeneration_invoked"] = regenerate is not None
        metadata["hard_validation_attempt_1"]["gm_resolution_decision_audit"] = first.get("gm_resolution_decision_audit")

    def _early_authored_projection() -> tuple[dict[str, Any], dict[str, Any], str] | None:
        if not isinstance(resolution, Mapping) or _operation(contract) != "ask":
            return None
        social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else None
        if not isinstance(social, Mapping):
            return None
        topic = social.get("topic_revealed") if isinstance(social.get("topic_revealed"), Mapping) else None
        topic_text = str((topic or {}).get("text") or (topic or {}).get("clue_text") or "").strip()
        if not topic_text:
            return None
        if _unresolved_explicit_addressee(contract):
            return None
        if isinstance(gm_decision, Mapping):
            if gm_decision.get("unresolved_qualifiers"):
                return None
            obligations = gm_decision.get("executable_obligations")
            if isinstance(obligations, Mapping) and obligations.get("primary"):
                return None
            mutations = gm_decision.get("permitted_state_mutations")
            allowed_mutations = {
                ("state_change", "topic_revealed"),
                ("state_change", "npc_id"),
            }
            if isinstance(mutations, list) and any(
                (
                    str(item.get("type") or ""),
                    str(item.get("key") or ""),
                )
                not in allowed_mutations
                for item in mutations
                if isinstance(item, Mapping)
            ):
                return None
        try:
            from game.social import format_authored_knowledge_realization_line

            line = format_authored_knowledge_realization_line(dict(resolution), topic_text)
        except Exception:
            return None
        if not str(line or "").strip():
            return None
        projected = copy.deepcopy(gm)
        projected["player_facing_text"] = str(line).strip()
        tags = [str(t) for t in (projected.get("tags") or []) if isinstance(t, str)]
        if "early_authored_answer_projection" not in tags:
            tags.append("early_authored_answer_projection")
        projected["tags"] = tags
        projected_meta = projected.setdefault("metadata", {})
        if isinstance(projected_meta, dict):
            projected_meta.pop("content_leak_reasons", None)
            projected_meta.pop("structured_output_rejected", None)
            projected_meta.pop("structured_contract_failure", None)
            projected_meta["regeneration_invoked"] = False
            projected_meta["generation_attempt_count"] = 1
            projected_meta["deterministic_recovery_method"] = "authored_answer_projection"
            projected_meta["rejected_attempt_1_reasons"] = list(first.get("reasons") or [])
            projected_meta["rejected_attempt_1_text"] = str(gm.get("player_facing_text") or "")[:2000]
            debug = projected_meta.setdefault("emission_debug", {})
            if isinstance(debug, dict):
                debug["early_authored_answer_projection"] = {
                    "applied": True,
                    "topic_id": str((topic or {}).get("id") or ""),
                    "rejected_reasons": list(first.get("reasons") or []),
                    "rejected_preview": str(gm.get("player_facing_text") or "")[:180],
                }
        checked = _check({"player_facing_text": str(line).strip(), "metadata": {}})
        if not checked.get("hard_valid"):
            if isinstance(projected_meta, dict):
                projected_meta["early_authored_projection_rejected"] = {
                    "reasons": list(checked.get("reasons") or []),
                    "text": str(line)[:2000],
                }
            return None
        return projected, checked, str(line).strip()

    def _incidental_quote_recovery(candidate_text: str) -> tuple[str, dict[str, Any]] | None:
        """Keep a harmless quoted remark and drop a consequential sentence beside it."""
        if not isinstance(resolution, Mapping) or _operation(contract) != "ask":
            return None
        social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else None
        if not isinstance(social, Mapping):
            return None
        authority = social.get("dialogue_authority") if isinstance(social.get("dialogue_authority"), Mapping) else None
        if not isinstance(authority, Mapping) or authority.get("improvisation_permitted") is not True:
            return None
        name = str(social.get("npc_name") or "").strip() or "They"
        from game.dialogue_authority import dialogue_rejection_reasons
        from game.proposition_authority import CONSEQUENTIAL_KIND, classify_propositions

        spans = re.findall(r'["“]([^"”]{1,220})["”]', str(candidate_text or ""))
        for span in spans:
            for piece in re.split(r"(?<=[.!?])\s+", span.strip()):
                remark = piece.strip(" \"")
                if len(remark) < 3:
                    continue
                rows = classify_propositions(remark, authored_corpus=corpus)
                if any(row.get("kind") == CONSEQUENTIAL_KIND for row in rows):
                    continue
                if dialogue_rejection_reasons(remark, authority=authority):
                    continue
                spoken = remark[0].upper() + remark[1:] if remark[:1].islower() else remark
                spoken = spoken.rstrip(" ,;:")
                if not spoken:
                    continue
                if spoken[-1] not in ".?!":
                    spoken = spoken + "."
                line = f'{name} says, "{spoken}"'
                checked = _check({"player_facing_text": line, "metadata": {}})
                if checked.get("hard_valid"):
                    return line, checked
        return None

    early_projection = _early_authored_projection()
    if early_projection is not None:
        projected, checked, line = early_projection
        sealed = seal_accepted_response(
            projected,
            text=line,
            provenance=PROVENANCE_AUTHORED_PROJECTION,
            attempt=1,
            validation=checked,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="authored_answer_projection")

    def _bounded_keep(candidate_text: str) -> tuple[str, dict[str, Any]] | None:
        from game.gm_resolution_decision import preservation_structure_valid, structural_narration_units

        source_verdict = _check({"player_facing_text": candidate_text})
        source_audit = source_verdict.get("gm_resolution_decision_audit")
        if not isinstance(source_audit, Mapping) or not source_audit.get("violations"):
            return None
        safe_units: list[str] = []
        for unit in structural_narration_units(candidate_text):
            unit_verdict = _check({"player_facing_text": unit})
            if unit_verdict.get("hard_valid"):
                safe_units.append(unit)
        kept = " ".join(safe_units).strip()
        if not kept or kept == str(candidate_text or "").strip() or not preservation_structure_valid(kept):
            return None
        # C18: this exact post-deletion string, not the source audit, governs sealing.
        checked = _check({"player_facing_text": kept})
        if not checked.get("hard_valid"):
            return None
        return kept, checked

    def _terminal_after_fidelity(reasons: list[str]) -> tuple[str, str]:
        from game.gm_resolution_decision import authorized_observation_line
        from game.social import format_authored_knowledge_realization_line

        social = resolution.get("social") if isinstance(resolution, Mapping) else None
        topic = social.get("topic_revealed") if isinstance(social, Mapping) else None
        topic_text = str((topic or {}).get("text") or (topic or {}).get("clue_text") or "").strip()
        if topic_text:
            projected = format_authored_knowledge_realization_line(
                dict(resolution) if isinstance(resolution, Mapping) else {},
                topic_text,
            )
            if projected.strip():
                checked = _check({"player_facing_text": projected})
                if checked.get("hard_valid"):
                    return projected, "authored_answer_projection"

        if "unauthorized_resolution_decision_fact" in reasons:
            realized = authorized_observation_line(gm_decision, player)
            generic = "No one here can answer that from what is settled here."
            if realized and realized.strip() != generic:
                checked = _check({"player_facing_text": realized})
                if checked.get("hard_valid"):
                    return realized, "authorized_observation"
        return (
            safe_nonresolution(contract, resolution=resolution, visible_facts=facts, player_text=player),
            "safe_nonresolution",
        )

    recovered = _incidental_quote_recovery(str(gm.get("player_facing_text") or ""))
    if recovered is not None:
        line, checked = recovered
        sealed = seal_accepted_response(
            gm,
            text=line,
            provenance=PROVENANCE_INITIAL,
            attempt=1,
            validation=checked,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="incidental_quote_recovery")

    if regenerate is None:
        bounded = (
            None
            if candidate_entered_structured_envelope_path(gm)
            else _bounded_keep(str(gm.get("player_facing_text") or ""))
        )
        if bounded is not None:
            kept, checked = bounded
            sealed = seal_accepted_response(
                gm,
                text=kept,
                provenance=PROVENANCE_INITIAL,
                attempt=1,
                validation=checked,
                contract=contract,
                player_text=player,
                resolution=resolution,
            )
            return _finish(sealed, why="bounded_sentence_preservation")
        line, why = _terminal_after_fidelity(list(first.get("reasons") or []))
        safe_validation = _check({"player_facing_text": line})
        if not safe_validation.get("hard_valid"):
            gm["player_facing_text"] = "I cannot provide a validated response to that request."
            return _finish(mark_candidate_rejected(gm, gm["player_facing_text"],
                                                   list(safe_validation.get("reasons") or [])),
                           why="controlled_validation_failure")
        sealed = seal_accepted_response(
            gm,
            text=line,
            provenance=PROVENANCE_SAFE,
            attempt=1,
            validation=safe_validation,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why=why)

    regenerated = regenerate(feedback)
    if not isinstance(regenerated, dict):
        regenerated = {"player_facing_text": "", "metadata": {}}
    second = _check(regenerated)
    review["attempt_2"] = {
        "text": str(regenerated.get("player_facing_text") or "")[:2000],
        "reasons": list(second.get("reasons") or []),
        "gm_resolution_decision_audit": second.get("gm_resolution_decision_audit"),
    }
    second_meta = regenerated.setdefault("metadata", {})
    if isinstance(second_meta, dict):
        second_meta["hard_validation_attempt_1"] = metadata.get("hard_validation_attempt_1") if isinstance(metadata, dict) else {}
        second_meta["hard_validation_attempt_2"] = {
            "hard_valid": second["hard_valid"],
            "reasons": list(second["reasons"]),
            "soft_flags": list(second["soft_flags"]),
            "text": str(regenerated.get("player_facing_text") or "")[:2000],
            "gm_resolution_decision_audit": second.get("gm_resolution_decision_audit"),
        }
        second_meta["regeneration_feedback"] = feedback
        second_meta["regeneration_invoked"] = True
        second_meta["generation_attempt_count"] = 2
    if second["hard_valid"]:
        sealed = seal_accepted_response(
            regenerated,
            text=str(regenerated.get("player_facing_text") or ""),
            provenance=PROVENANCE_REGENERATION,
            attempt=2,
            validation=second,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="regeneration_hard_valid")
    mark_candidate_rejected(regenerated, str(regenerated.get("player_facing_text") or ""), second["reasons"])
    structured_turn = candidate_entered_structured_envelope_path(gm) or candidate_entered_structured_envelope_path(
        regenerated
    )
    bounded = None
    bounded_from_retry = False
    if not structured_turn:
        bounded = _bounded_keep(str(gm.get("player_facing_text") or ""))
        if bounded is None:
            bounded = _bounded_keep(str(regenerated.get("player_facing_text") or ""))
            bounded_from_retry = bounded is not None
    if bounded is not None:
        kept, checked = bounded
        host = regenerated if bounded_from_retry else gm
        sealed = seal_accepted_response(
            host,
            text=kept,
            provenance=PROVENANCE_REGENERATION if bounded_from_retry else PROVENANCE_INITIAL,
            attempt=2 if bounded_from_retry else 1,
            validation=checked,
            contract=contract,
            player_text=player,
            resolution=resolution,
        )
        return _finish(sealed, why="bounded_sentence_preservation")
    line, why = _terminal_after_fidelity(list(first.get("reasons") or []) + list(second.get("reasons") or []))
    checked_line = _check({"player_facing_text": line})
    if not checked_line.get("hard_valid"):
        regenerated["player_facing_text"] = "I cannot provide a validated response to that request."
        return _finish(mark_candidate_rejected(regenerated, regenerated["player_facing_text"],
                                               list(checked_line.get("reasons") or [])),
                       why="controlled_validation_failure")
    safe_validation = checked_line
    # Keep the rejected attempt record beside the safe seal.
    sealed = seal_accepted_response(
        regenerated,
        text=line,
        provenance=PROVENANCE_SAFE,
        attempt=2,
        validation=safe_validation,
        contract=contract,
        player_text=player,
        resolution=resolution,
    )
    sealed_meta = sealed.setdefault("metadata", {})
    if isinstance(sealed_meta, dict):
        sealed_meta["rejected_attempt_2_reasons"] = list(second["reasons"])
        sealed_meta["generation_attempt_count"] = 2
    if provenance_is_safe(sealed):
        sealed["retry_exhausted"] = True
        sealed["targeted_retry_terminal"] = True
    return _finish(sealed, why=why)
```

## game/narration_visibility.py:373 _normalized_fact_match_kind
```python
def _normalized_fact_match_kind(normalized_text: str, fact: str) -> Optional[str]:
    if not normalized_text or not fact:
        return None
    if normalized_text == fact:
        return "exact"
    if fact in normalized_text:
        return "substring"
    return None
```

## game/narration_visibility.py:1227 validate_player_facing_visibility
```python
def validate_player_facing_visibility(
    text: str,
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    contract = build_narration_visibility_contract(session=session, scene=scene, world=world)
    normalized_text = _normalize_visibility_text(text)
    visible_ids = {
        str(raw).strip()
        for raw in (contract.get("visible_entity_ids") or [])
        if isinstance(raw, str) and str(raw).strip()
    }
    alias_map = contract.get("visible_entity_aliases") if isinstance(contract.get("visible_entity_aliases"), dict) else {}
    visible_facts = [
        str(raw).strip()
        for raw in (contract.get("visible_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    visible_fact_set = set(visible_facts)
    hidden_facts = [
        str(raw).strip()
        for raw in (contract.get("hidden_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]
    discoverable_facts = [
        str(raw).strip()
        for raw in (contract.get("discoverable_fact_strings") or [])
        if isinstance(raw, str) and str(raw).strip()
    ]

    violations: List[Dict[str, Any]] = []
    checked_entities: List[Dict[str, Any]] = []
    checked_facts: List[Dict[str, Any]] = []

    for entity_id, raw_aliases in alias_map.items():
        if not isinstance(entity_id, str) or not entity_id.strip() or not isinstance(raw_aliases, list):
            continue
        matched_aliases: List[str] = []
        for raw_alias in raw_aliases:
            if not isinstance(raw_alias, str):
                continue
            alias = _normalize_visibility_text(raw_alias)
            if alias and _normalized_phrase_in_text(normalized_text, alias) and alias not in matched_aliases:
                matched_aliases.append(alias)
        if not matched_aliases:
            continue
        checked_entities.append(
            {
                "entity_id": entity_id,
                "matched_aliases": matched_aliases,
            }
        )
        if entity_id not in visible_ids:
            violations.append(
                {
                    "kind": "unseen_entity_reference",
                    "token": matched_aliases[0],
                    "matched_entity_id": entity_id,
                    "matched_fact": None,
                }
            )

    seen_fact_checks: Set[tuple[str, str]] = set()
    for fact_kind, facts, illegal in (
        ("hidden_fact_strings", hidden_facts, True),
        ("discoverable_fact_strings", discoverable_facts, True),
        ("visible_fact_strings", visible_facts, False),
    ):
        for fact in facts:
            match_kind = _normalized_fact_match_kind(normalized_text, fact)
            if not match_kind:
                continue
            key = (fact_kind, fact)
            if key not in seen_fact_checks:
                checked_facts.append(_fact_check_entry(fact_kind, fact, match_kind))
                seen_fact_checks.add(key)
            if illegal and fact not in visible_fact_set:
                violations.append(
                    {
                        "kind": "undiscovered_fact_assertion",
                        "token": fact,
                        "matched_entity_id": None,
                        "matched_fact": fact,
                    }
                )

    return {
        "ok": not violations,
        "violations": violations,
        "visibility_checked_entities": checked_entities,
        "visibility_checked_facts": checked_facts,
    }
```

## game/narration_visibility.py:1338 build_narration_visibility_contract
```python
def build_narration_visibility_contract(
    *,
    session: Dict[str, Any] | None,
    scene: Dict[str, Any] | None,
    world: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """Return a read-only, conservative narration visibility snapshot (no mutations)."""
    env = _coerce_scene_envelope(scene)
    sid = _resolve_scene_id(env, session)
    w = world if isinstance(world, dict) else None

    visible_ids_set = addressable_scene_npc_id_universe(session, env, w)
    visible_entity_ids = sorted(visible_ids_set)

    inner_for_roster = env.get("scene")
    roster = canonical_scene_addressable_roster(
        w or {},
        sid,
        scene_envelope=env if isinstance(inner_for_roster, dict) else None,
        session=session if isinstance(session, dict) else None,
    )

    alias_map = _collect_contract_entity_alias_map(roster, w)
    kind_map = _collect_contract_entity_kind_map(roster, w)
    role_map = _collect_contract_entity_role_map(roster, w)
    visible_entity_names: List[str] = []
    for eid in visible_entity_ids:
        names = alias_map.get(eid)
        if names:
            visible_entity_names.append(names[0])
        else:
            fallback = _normalize_visibility_text(eid.replace("_", " "))
            visible_entity_names.append(fallback or eid.lower())

    return {
        "scene_id": sid or None,
        "visible_entity_ids": list(visible_entity_ids),
        "visible_entity_names": visible_entity_names,
        "visible_entity_aliases": dict(alias_map),
        "visible_entity_kinds": {eid: str(kind_map.get(eid) or "") for eid in visible_entity_ids},
        "visible_entity_roles": {
            eid: list(role_map.get(eid) or [])
            for eid in visible_entity_ids
            if list(role_map.get(eid) or [])
        },
        "active_interlocutor_id": _resolve_active_interlocutor_id(session),
        "visible_fact_strings": _collect_scene_visible_fact_strings(env),
        "discoverable_fact_strings": _collect_scene_discoverable_fact_strings(env),
        "hidden_fact_strings": _collect_scene_hidden_fact_strings(env),
        "allowed_narration_sources": dict(_ALLOWED_NARRATION_SOURCES),
    }
```

## game/narrative_authority.py:197 build_narrative_authority_contract
```python
def build_narrative_authority_contract(
    *,
    resolution: Mapping[str, Any] | None,
    narration_visibility: Mapping[str, Any] | None,
    scene_state_anchor_contract: Mapping[str, Any] | None,
    speaker_selection_contract: Mapping[str, Any] | None,
    session_view: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Assemble an inspectable contract for narrative authority (no world mutation).

    Separates **visible observation** (what could be seen) from **bounded inference**
    (hedged impressions), **hidden-fact assertions** (backstage causality stated as fact),
    and **adjudicated outcomes** (engine-resolved mechanical results). The contract never
    reads hidden layers beyond the slices already published in ``narration_visibility``.
    """
    res = _mapping_or_empty(resolution)
    vis = _mapping_or_empty(narration_visibility)
    sp = _mapping_or_empty(speaker_selection_contract)
    sess = _mapping_or_empty(session_view)

    vis_facts_raw = vis.get("visible_fact_strings")
    visible_fact_strings: List[str] = []
    if isinstance(vis_facts_raw, list):
        for item in vis_facts_raw:
            if not isinstance(item, str):
                continue
            n = _normalize_authority_text(item)
            if n:
                visible_fact_strings.append(n)

    hidden_raw = vis.get("hidden_fact_strings")
    hidden_fact_strings_present = bool(
        isinstance(hidden_raw, list)
        and any(isinstance(x, str) and _normalize_authority_text(x) for x in hidden_raw)
    )

    disc_raw = vis.get("discoverable_fact_strings")
    discoverable_hinting_allowed = bool(
        isinstance(disc_raw, list)
        and any(isinstance(x, str) and _normalize_authority_text(x) for x in disc_raw)
    )

    resolution_kind = _normalize_resolution_kind(res if isinstance(resolution, Mapping) else None)
    authoritative_outcome_available = (
        _resolution_has_authoritative_outcome(res) if isinstance(resolution, Mapping) else False
    )
    mechanical_result_available = (
        _mechanical_result_available(res) if isinstance(resolution, Mapping) else False
    )
    success_state_available = (
        _success_state_available(res) if isinstance(resolution, Mapping) else False
    )

    active_speaker_id = _clean_str(sp.get("primary_speaker_id")) or None
    active_target_id = _clean_str(sess.get("active_interaction_target_id")) or _clean_str(
        vis.get("active_interlocutor_id")
    )
    active_target_id = active_target_id or None

    forbid_unresolved_outcome_assertions = not authoritative_outcome_available
    forbid_hidden_fact_assertions = True
    forbid_npc_intent_assertions_without_basis = True

    # Contract flag: builder has no player text; validator refines with ``player_text``.
    allow_bounded_intent_reading_only_when_player_asked = False

    mechanical_risky = False
    if isinstance(resolution, Mapping):
        if resolution_kind in _COMBAT_KINDS or resolution_kind in _MECHANICAL_EXPLORATION_KINDS:
            mechanical_risky = True
        if resolution_kind in _MECHANICAL_SOCIAL_KINDS:
            mechanical_risky = True
        if res.get("requires_check"):
            mechanical_risky = True
        p = _normalize_authority_text(_clean_str(res.get("prompt")))
        for token in (
            "sneak",
            "stealth",
            "hide",
            "lockpick",
            "pick the lock",
            "disable device",
            "bluff",
            "lie",
            "deceive",
            "sense motive",
            "perception",
            "climb",
            "search",
        ):
            if token in p:
                mechanical_risky = True
                break

    if not authoritative_outcome_available and mechanical_risky:
        preferred_deferral_order: List[str] = [
            "ask_for_roll",
            "branch_outcome",
            "bounded_uncertainty",
        ]
    else:
        preferred_deferral_order = ["bounded_uncertainty", "branch_outcome", "ask_for_roll"]

    anchor_on = bool(
        isinstance(scene_state_anchor_contract, Mapping) and scene_state_anchor_contract.get("enabled")
    )
    enabled = True

    debug_flags = {
        "mechanical_risky": mechanical_risky,
        "pending_player_roll": isinstance(resolution, Mapping) and _resolution_pending_player_roll(res),
        "anchor_contract_enabled": anchor_on,
    }
    debug_inputs = {
        "has_resolution": isinstance(resolution, Mapping),
        "has_narration_visibility": bool(vis),
        "has_scene_state_anchor_contract": isinstance(scene_state_anchor_contract, Mapping),
        "has_speaker_selection_contract": bool(sp),
        "has_session_view": bool(sess),
    }
    debug_reason = (
        f"narrative_authority: authoritative_outcome={authoritative_outcome_available} "
        f"kind={resolution_kind!r} mechanical_risky={mechanical_risky}"
    )

    return {
        "enabled": enabled,
        "authoritative_outcome_available": authoritative_outcome_available,
        "resolution_kind": resolution_kind,
        "success_state_available": success_state_available,
        "mechanical_result_available": mechanical_result_available,
        "active_speaker_id": active_speaker_id,
        "active_target_id": active_target_id,
        "visible_fact_strings": list(visible_fact_strings),
        "hidden_fact_strings_present": hidden_fact_strings_present,
        "discoverable_hinting_allowed": discoverable_hinting_allowed,
        "forbid_unresolved_outcome_assertions": forbid_unresolved_outcome_assertions,
        "forbid_hidden_fact_assertions": forbid_hidden_fact_assertions,
        "forbid_npc_intent_assertions_without_basis": forbid_npc_intent_assertions_without_basis,
        "allow_bounded_intent_reading_only_when_player_asked": allow_bounded_intent_reading_only_when_player_asked,
        "allowed_deferrals": list(NARRATIVE_AUTHORITY_ALLOWED_DEFERRALS),
        "preferred_deferral_order": preferred_deferral_order,
        "debug_reason": debug_reason,
        "debug_inputs": debug_inputs,
        "debug_flags": debug_flags,
    }
```

## game/narrative_authority.py:548 validate_narrative_authority
```python
def validate_narrative_authority(
    text: str,
    contract: Mapping[str, Any],
    *,
    resolution: Mapping[str, Any] | None = None,
    player_text: str | None = None,
) -> Dict[str, Any]:
    """Validate *text* against a ``build_narrative_authority_contract`` result.

    Flags **invented outcomes** when success/failure/effect language appears without
    ``authoritative_outcome_available``, **invented hidden facts** when causal certainty
    appears without hedges, and **invented intent** when motive/plan is stated as fact.
    Observable cues and properly hedged reads are allowed; roll prompts and branch framing
    count as approved deferrals.
    """
    if not isinstance(contract, Mapping):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": ["invalid_contract"],
            "matched_deferral_mode": None,
            "assertion_flags": {
                "invented_outcome": False,
                "invented_hidden_fact": False,
                "invented_intent": False,
                "overcertain_unresolved_action": False,
            },
            "debug": {"reason": "invalid_contract"},
        }

    if not contract.get("enabled"):
        return {
            "checked": False,
            "passed": True,
            "failure_reasons": [],
            "matched_deferral_mode": None,
            "assertion_flags": {
                "invented_outcome": False,
                "invented_hidden_fact": False,
                "invented_intent": False,
                "overcertain_unresolved_action": False,
            },
            "debug": {"reason": "contract_disabled"},
        }

    raw = str(text or "")
    masked_full = _mask_dialogue_spans(raw)
    norm_full = _normalize_authority_text(raw)
    matched_deferral = _detect_deferral_mode(masked_full)

    forbid_outcome = bool(contract.get("forbid_unresolved_outcome_assertions"))
    forbid_hidden = bool(contract.get("forbid_hidden_fact_assertions"))
    forbid_intent = bool(contract.get("forbid_npc_intent_assertions_without_basis"))
    player_seeks_read = _player_asks_intent_or_read(player_text) or _player_asks_intent_or_read(
        _clean_str((resolution or {}).get("prompt")) if isinstance(resolution, Mapping) else None
    )

    invented_outcome = False
    invented_hidden_fact = False
    invented_intent = False
    overcertain_unresolved_action = False

    if norm_full and forbid_outcome:
        for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = masked_full[start:end]
            if not msent.strip():
                continue
            if _sentence_has_hedge(sent):
                continue
            if _outcome_assertion_hits(sent, msent):
                invented_outcome = True
                overcertain_unresolved_action = True
                break

    if norm_full and forbid_hidden and not invented_outcome:
        for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = masked_full[start:end]
            if _sentence_has_hedge(sent):
                continue
            if _HIDDEN_FACT_CERTAINTY_RE.search(msent.lower()):
                invented_hidden_fact = True
                break

    if norm_full and forbid_intent:
        for start, end, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = masked_full[start:end]
            if player_seeks_read and _sentence_has_hedge(sent):
                continue
            if player_seeks_read and _ROLL_PROMPT_RE.search(msent):
                continue
            if _INTENT_CERTAINTY_RE.search(msent.lower()):
                if player_seeks_read and (
                    _sentence_has_hedge(sent) or _ROLL_PROMPT_RE.search(msent.lower())
                ):
                    continue
                invented_intent = True
                break

    failure_reasons: List[str] = []
    if invented_outcome:
        failure_reasons.append("unresolved_action")
    if invented_hidden_fact:
        failure_reasons.append("unknown_hidden_fact")
    if invented_intent:
        failure_reasons.append("unknown_intent")
    if overcertain_unresolved_action and "unresolved_action" not in failure_reasons:
        failure_reasons.append("insufficient_basis")

    passed = not (invented_outcome or invented_hidden_fact or invented_intent)

    # If narration already defers with an explicit roll prompt and every sentence either hedges
    # or prompts / branches, soften outcome findings (acceptance: "try the lock—give me a check").
    if not passed and invented_outcome and matched_deferral == "ask_for_roll":
        risky_sentence = False
        for _s, _e, sent in _split_sentences(_mask_dialogue_spans(raw), raw):
            msent = _mask_dialogue_spans(sent)
            if _outcome_assertion_hits(sent, msent) and not _ROLL_PROMPT_RE.search(msent.lower()):
                risky_sentence = True
                break
        if not risky_sentence:
            invented_outcome = False
            overcertain_unresolved_action = False
            failure_reasons = [r for r in failure_reasons if r != "unresolved_action"]
            passed = not (invented_outcome or invented_hidden_fact or invented_intent)

    return {
        "checked": True,
        "passed": passed,
        "failure_reasons": failure_reasons,
        "matched_deferral_mode": matched_deferral,
        "assertion_flags": {
            "invented_outcome": bool(invented_outcome),
            "invented_hidden_fact": bool(invented_hidden_fact),
            "invented_intent": bool(invented_intent),
            "overcertain_unresolved_action": bool(overcertain_unresolved_action),
        },
        "debug": {
            "forbid_unresolved_outcome_assertions": forbid_outcome,
            "player_seeks_intent_read": player_seeks_read,
            "normalized_nonempty": bool(norm_full),
        },
    }
```

## game/bounded_improvisation.py:230 validate_bounded_improvisation_proposal
```python
def validate_bounded_improvisation_proposal(
    proposal: Mapping[str, Any],
    *,
    session: Mapping[str, Any] | None,
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
) -> BoundedImprovisationDecision:
    norm = normalize_improvisation_proposal(proposal)
    if norm is None:
        return BoundedImprovisationDecision({}, False, ["proposal:not_object_or_empty"])
    reasons: list[str] = []
    kind = str(norm.get("kind") or "")
    content = str(norm.get("content") or "")
    category = str(norm.get("category") or "")
    scope = str(norm.get("scope") or "")
    consequence = str(norm.get("consequence_level") or "")
    epistemic = str(norm.get("epistemic_status") or "")
    if scope not in PERMITTED_SCOPES:
        reasons.append("scope:not_permitted")
    if consequence not in LOW_CONSEQUENCE_LEVELS:
        reasons.append("consequence:not_low")
    if kind == CONSEQUENTIAL_KIND:
        reasons.append("kind:consequential")
    if MECHANICAL_TERMS.search(content):
        reasons.append("content:mechanical_authority")
    from game.proposition_authority import PRICE_OFFICIAL, price_class

    if price_class(content) == PRICE_OFFICIAL and kind == INCIDENTAL_KIND:
        reasons.append("content:official_levy")
    if price_class(content) == PRICE_OFFICIAL and kind == NPC_CLAIM_KIND and epistemic in {"known", "grounded"}:
        reasons.append("npc_claim:grounded_consequential_claim")
    if HIDDEN_INFO_TERMS.search(content):
        reasons.append("content:hidden_information")
    if kind == INCIDENTAL_KIND:
        if category not in ALLOWED_INCIDENTAL_CATEGORIES:
            reasons.append("category:not_incidental")
        if CONSEQUENTIAL_TERMS.search(content):
            reasons.append("content:consequential_terms")
    elif kind == NPC_CLAIM_KIND:
        if category not in ALLOWED_NPC_CLAIM_CATEGORIES:
            reasons.append("category:not_npc_claim")
        if epistemic not in ALLOWED_EPISTEMIC_STATUSES:
            reasons.append("epistemic:not_supported")
        if epistemic in {"known", "grounded"} and CONSEQUENTIAL_TERMS.search(content):
            reasons.append("npc_claim:grounded_consequential_claim")
    else:
        reasons.append("kind:not_supported")
    if _contradicts_existing(content, session, scene, world):
        reasons.append("content:contradicts_existing")
    if isinstance(resolution, Mapping):
        kind_res = str(resolution.get("kind") or "").strip().lower()
        if kind_res in {"attack", "spell", "skill_check", "enemy_attack"} and kind != NPC_CLAIM_KIND:
            reasons.append("resolution:mechanical_lane")
        metadata = resolution.get("metadata")
        contract = metadata.get("resolution_contract") if isinstance(metadata, Mapping) else None
        if (
            isinstance(contract, Mapping)
            and contract.get("epistemic_mode") == "consequential_protected"
            and kind == INCIDENTAL_KIND
        ):
            reasons.append("contract:consequential_protected")
    accepted = not reasons
    scene_id = _scene_id_from_scene(scene, session)
    entry = None
    if accepted:
        status = "accepted"
        entry = {
            "id": _entry_id(kind, scene_id, content, str(norm.get("speaker_id") or "")),
            "kind": kind,
            "category": category,
            "content": content,
            "scope": scope,
            "scene_id": scene_id if scope in {"scene", "turn"} else None,
            "consequence_level": consequence,
            "source": str(norm.get("source") or "dm_improvisation"),
            "speaker_id": str(norm.get("speaker_id") or "") or None,
            "epistemic_status": epistemic if kind == NPC_CLAIM_KIND else None,
            "status": status,
            "authority": "bounded_improvisation",
            "truth_status": "not_world_truth" if kind == NPC_CLAIM_KIND else "runtime_incidental",
        }
        if norm.get("satisfies_contract_id"):
            entry["satisfies_contract_id"] = norm.get("satisfies_contract_id")
        if norm.get("requested_dimension"):
            entry["requested_dimension"] = norm.get("requested_dimension")
    return BoundedImprovisationDecision(dict(norm), accepted, reasons, entry)
```

## game/bounded_improvisation.py:402 promote_accepted_bounded_improvisation
```python
def promote_accepted_bounded_improvisation(
    gm: Mapping[str, Any] | None,
    *,
    session: dict[str, Any],
    scene: Mapping[str, Any] | None,
    world: Mapping[str, Any] | None,
    resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from game.immutable_valid_response import accepted_record, effects_allowed

    if accepted_record(gm) is not None and not effects_allowed(gm):
        return {
            "promoted_count": 0,
            "rejected_count": 0,
            "accepted_count": 0,
            "promoted_ids": [],
            "blocked_reason": "rejected_or_unaccepted_candidate",
        }
    evaluation = (
        gm.get(IMPROVISATION_AUTHORITY_KEY)
        if isinstance(gm, Mapping) and isinstance(gm.get(IMPROVISATION_AUTHORITY_KEY), Mapping)
        else evaluate_improvisation_proposals(gm, session=session, scene=scene, world=world, resolution=resolution)
    )
    ledger = ensure_bounded_improvisation_ledger(session)
    entries = ledger.setdefault("entries", [])
    rejected_bucket = ledger.setdefault("rejected", [])
    existing_ids = {str(e.get("id") or "") for e in entries if isinstance(e, Mapping)}
    promoted: list[dict[str, Any]] = []
    for entry in evaluation.get("accepted") or []:
        if not isinstance(entry, dict):
            continue
        eid = str(entry.get("id") or "")
        if eid and eid not in existing_ids:
            stored = dict(entry)
            stored["status"] = "promoted"
            entries.append(stored)
            existing_ids.add(eid)
            promoted.append(stored)
    for rejected in evaluation.get("rejected") or []:
        if isinstance(rejected, dict):
            rejected_bucket.append(dict(rejected))
    if len(rejected_bucket) > 50:
        del rejected_bucket[:-50]
    return {
        "promoted_count": len(promoted),
        "rejected_count": int(evaluation.get("rejected_count") or 0),
        "accepted_count": int(evaluation.get("accepted_count") or 0),
        "promoted_ids": [str(e.get("id") or "") for e in promoted],
    }
```

## game/ctir_runtime.py:303 build_runtime_ctir_for_narration
```python
def build_runtime_ctir_for_narration(
    *,
    turn_id: Any,
    scene_id: str | None,
    player_input: str,
    builder_source: str,
    resolution: dict | None,
    normalized_action: dict | None,
    combat: dict | None,
    session: dict | None,
    world: dict | None = None,
) -> dict[str, Any]:
    """Assemble explicit bounded kwargs for :func:`game.ctir.build_ctir`."""
    return ctir.build_ctir(
        turn_id=turn_id,
        scene_id=scene_id,
        player_input=player_input,
        builder_source=builder_source,
        intent=_slice_intent(player_input=player_input, normalized_action=normalized_action),
        resolution=_slice_resolution(resolution),
        state_mutations=_slice_state_mutations(
            scene_id=scene_id,
            resolution=resolution,
            combat=combat,
            session=session,
        ),
        interaction=_slice_interaction(session),
        world=_slice_world(resolution, world=world, session=session),
        narrative_anchors=None,
        source_modules=("game.ctir_runtime", "game.api"),
        signals_used=None,
        retry_safe_flags=None,
        provenance_extras=None,
    )
```

## game/prompt_context.py:1527 build_narration_context
```python
def build_narration_context(
    campaign: Dict[str, Any],
    world: Dict[str, Any],
    session: Dict[str, Any],
    character: Dict[str, Any],
    scene: Dict[str, Any],
    combat: Dict[str, Any],
    recent_log: List[Dict[str, Any]],
    user_text: str,
    resolution: Dict[str, Any] | None,
    scene_runtime: Dict[str, Any] | None,
    *,
    public_scene: Dict[str, Any],
    discoverable_clues: List[str],
    gm_only_hidden_facts: List[str],
    gm_only_discoverable_locked: List[str],
    discovered_clue_records: List[Dict[str, Any]],
    undiscovered_clue_records: List[Dict[str, Any]],
    pending_leads: List[Any],
    intent: Dict[str, Any],
    world_state_view: Dict[str, Any],
    mode_instruction: str,
    recent_log_for_prompt: List[Dict[str, Any]],
    uncertainty_hint: Dict[str, Any] | None = None,
    prompt_profile: str = "full",
    include_non_public_prompt_keys: bool = False,
) -> Dict[str, Any]:
    """Build a compressed narration context payload for GPT.

    Caller must precompute scene layers (public_scene, clues, hidden, etc.)
    and pass them in. This avoids duplicating _scene_layers logic and ensures
    hidden facts stay in gm_only only.

    Returns a dict suitable for JSON serialization as the user message content.

    Narration contracts are layered: visibility (reference scope), narrative_authority (certainty
    and assertion boundaries), scene_state_anchor (grounding), answer_completeness
    (answer-shape obligations), fallback_behavior (narrow uncertainty fallback shape),
    tone_escalation (interpersonal intensity caps), anti_railroading (player agency vs surfaced leads),
    context_separation (ambient pressure vs local exchange), and player_facing_narration_purity
    (no scaffold/menu/engine coaching in prose),
    and social_response_structure (dialogue-turn spoken shape when response type requires dialogue),
    narrative_authenticity (anti-echo / signal-density / diegetic-shape pressure shipped on response_policy),
    and interaction_continuity (thread / interlocutor anchoring snapshot for enforcement layers);
    see module docstring.

    By default the returned mapping is the **model-facing** bundle: top-level keys are
    shallow-projected through :func:`game.state_channels.project_public_payload` and
    checked with :func:`game.state_channels.assert_no_debug_keys_in_prompt_payload`.
    Set ``include_non_public_prompt_keys=True`` only for tests or tooling that must
    inspect builder-local mirrors such as ``prompt_debug`` (never for live model input).
    """
    assert not (isinstance(scene, dict) and scene.get("_is_canon")), (
        "Prompt built from canonical scene instead of effective scene"
    )
    # Head state through scene anchor: shared with :mod:`game.narration_plan_bundle` (renderer-only downstream).
    _head = _build_narration_context_head_state(
        campaign,
        world,
        session,
        character,
        scene,
        combat,
        recent_log,
        user_text,
        resolution,
        scene_runtime,
        public_scene=public_scene,
        discoverable_clues=discoverable_clues,
        gm_only_hidden_facts=gm_only_hidden_facts,
        gm_only_discoverable_locked=gm_only_discoverable_locked,
        discovered_clue_records=discovered_clue_records,
        undiscovered_clue_records=undiscovered_clue_records,
        pending_leads=pending_leads,
        intent=intent,
        world_state_view=world_state_view,
        mode_instruction=mode_instruction,
        recent_log_for_prompt=recent_log_for_prompt,
        uncertainty_hint=uncertainty_hint,
        prompt_profile=prompt_profile,
        include_non_public_prompt_keys=include_non_public_prompt_keys,
    )
    ctir_obj = _head["ctir_obj"]
    prompt_sem = _head["prompt_sem"]
    resolution_sem = _head["resolution_sem"]
    intent_sem = _head["intent_sem"]
    interaction_sem = _head["interaction_sem"]
    intent_for_scene_payload = _head["intent_for_scene_payload"]
    wp_projection = _head["wp_projection"]
    wp_hint_lines = _head["wp_hint_lines"]
    active_pending_leads = _head["active_pending_leads"]
    runtime = _head["runtime"]
    session_view = _head["session_view"]
    narration_obligations = _head["narration_obligations"]
    social_authority = _head["social_authority"]
    eff_uncertainty_hint = _head["eff_uncertainty_hint"]
    recent_log_compact = _head["recent_log_compact"]
    response_policy = _head["response_policy"]
    res = _head["res"]
    state_changes = _head["state_changes"]
    scene_advancement = _head["scene_advancement"]
    has_scene_change_context = _head["has_scene_change_context"]
    interaction_continuity = _head["interaction_continuity"]
    has_active_interlocutor = _head["has_active_interlocutor"]
    scene_pub_id = _head["scene_pub_id"]
    interlocutor_export = _head["interlocutor_export"]
    answer_style_hints_list = _head["answer_style_hints_list"]
    clue_records_all = _head["clue_records_all"]
    clue_visibility = _head["clue_visibility"]
    visibility_contract = _head["visibility_contract"]
    visible_facts_for_prompt = _head["visible_facts_for_prompt"]
    opening_inputs_are_curated = _head["opening_inputs_are_curated"]
    opening_fact_telemetry = _head["opening_fact_telemetry"]
    opening_selector_selected_facts = _head["opening_selector_selected_facts"]
    res_for_vis = _head["res_for_vis"]
    res_md_vis = _head["res_md_vis"]
    opening_scene_export = _head["opening_scene_export"]
    visible_facts_export = _head["visible_facts_export"]
    narration_visibility = _head["narration_visibility"]
    scene_state_anchor_contract = _head["scene_state_anchor_contract"]
    public_scene = _head["public_scene"]

    # Narrative plan (C1): CTIR-backed narration requires a stamp-matched session bundle; no local replan.
    narrative_plan: Dict[str, Any] | None = None
    narrative_plan_build_error: str | None = None
    _bundle = get_attached_narration_plan_bundle(session if isinstance(session, dict) else None)
    _ctir_stamp = str((session or {}).get(SESSION_CTIR_STAMP_KEY) or "").strip() if isinstance(session, dict) else ""
    _bundle_stamp = get_narration_plan_bundle_stamp(session if isinstance(session, dict) else None)
    _bundle_renderer_inputs: Dict[str, Any] = {}
    bundle_stamp_ok = False
    if ctir_obj is not None:
        bundle_stamp_ok = (
            isinstance(_bundle, dict)
            and bool(_bundle_stamp)
            and bool(_ctir_stamp)
            and _bundle_stamp == _ctir_stamp
        )
        if bundle_stamp_ok:
            np = _bundle.get("narrative_plan")
            narrative_plan = np if isinstance(np, dict) else None
            pm = _bundle.get("plan_metadata") if isinstance(_bundle.get("plan_metadata"), dict) else {}
            err_raw = pm.get("narration_plan_bundle_error")
            narrative_plan_build_error = str(err_raw).strip() if err_raw else None
            if narrative_plan is None and not narrative_plan_build_error:
                narrative_plan_build_error = "narration_plan_bundle_missing_plan"
            _ri = _bundle.get("renderer_inputs")
            _bundle_renderer_inputs = dict(_ri) if isinstance(_ri, dict) else {}
        else:
            narrative_plan = None
            if not _ctir_stamp:
                narrative_plan_build_error = "narration_plan_bundle_required:missing_ctir_stamp"
            elif not isinstance(_bundle, dict):
                narrative_plan_build_error = "narration_plan_bundle_required:bundle_absent"
            elif not _bundle_stamp or _bundle_stamp != _ctir_stamp:
                narrative_plan_build_error = "narration_plan_bundle_required:stamp_mismatch_or_stale"
            else:
                narrative_plan_build_error = "narration_plan_bundle_required"

    if (
        ctir_obj is not None
        and bundle_stamp_ok
        and isinstance(response_policy, dict)
        and isinstance(_bundle_renderer_inputs.get("response_policy"), dict)
    ):
        brp = _bundle_renderer_inputs["response_policy"]
        rtc_override = brp.get("response_type_contract")
        if isinstance(rtc_override, dict):
            response_policy["response_type_contract"] = copy.deepcopy(rtc_override)

    if isinstance(narrative_plan, dict) and isinstance(opening_scene_export, dict):
        patch_opening_export_with_plan_scene_opening(
            opening_scene_export,
            scene_opening=narrative_plan.get("scene_opening"),
        )

    # C1-B: prompt_context must not reconstruct continuation progression from raw state/logs.
    # A "verified CTIR-backed continuation" here means: CTIR attached, stamp-matched bundle,
    # and the attached plan projects a continuation-mode turn. (Block B enforcement happens upstream;
    # prompt_context is a renderer/packager only.)
    is_verified_ctir_continuation = bool(
        ctir_obj is not None
        and bundle_stamp_ok
        and isinstance(narrative_plan, dict)
        and str(narrative_plan.get("narrative_mode") or "").strip().lower() == "continuation"
    )

    prompt_debug_anchor = {
        "scene_state_anchor": {
            "enabled": bool(scene_state_anchor_contract.get("enabled")),
            "scene_id": scene_state_anchor_contract.get("scene_id"),
            "counts": {
                "location": len(scene_state_anchor_contract.get("location_tokens") or []),
                "actor": len(scene_state_anchor_contract.get("actor_tokens") or []),
                "player_action": len(scene_state_anchor_contract.get("player_action_tokens") or []),
            },
        },
        "opening_scene_realization": {
            "opening_mode": bool(opening_scene_export.get("opening_mode"))
            if isinstance(opening_scene_export, dict)
            else False,
            "validator": (opening_scene_export.get("contract") or {}).get("validator")
            if isinstance(opening_scene_export, dict) and isinstance(opening_scene_export.get("contract"), dict)
            else None,
        },
        "narrative_plan": _narrative_plan_prompt_debug_anchor(
            narrative_plan,
            build_error=narrative_plan_build_error,
        ),
        "world_progression": {
            "read_source": "ctir"
            if (
                ctir_obj is not None
                and isinstance((ctir_obj.get("world") or {}).get("progression"), dict)
            )
            else "backbone_fallback",
            "changed_node_count": len((wp_projection or {}).get("changed_node_ids") or []),
            "changed_node_ids_head": list((wp_projection or {}).get("changed_node_ids") or [])[:8],
            "active_projects_n": len((wp_projection or {}).get("active_projects") or []),
            "faction_pressure_n": len((wp_projection or {}).get("faction_pressure") or []),
            "faction_agenda_n": len((wp_projection or {}).get("faction_agenda") or []),
            "world_clocks_n": len((wp_projection or {}).get("world_clocks") or []),
            "set_flags_n": len((wp_projection or {}).get("set_flags") or []),
        },
        "planner_convergence_consumer": _planner_convergence_consumer_debug_slice(
            ctir_present=ctir_obj is not None,
            bundle_present=isinstance(_bundle, dict),
            stamp_matches=bundle_stamp_ok,
            narrative_plan_full=narrative_plan if isinstance(narrative_plan, dict) else None,
        ),
    }
    _cont_mode = (
        str((narrative_plan or {}).get("narrative_mode") or "").strip().lower()
        if isinstance(narrative_plan, dict)
        else ""
    )
    if is_verified_ctir_continuation:
        _progression_src = "narrative_plan_bundle"
    elif _cont_mode != "continuation":
        _progression_src = "not_continuation"
    elif ctir_obj is None:
        _progression_src = "legacy_non_ctir"
    else:
        _progression_src = "unavailable"
    prompt_debug_anchor["continuation_packaging"] = {
        "continuation_progression_source": _progression_src,
        "prompt_context_reconstructed_continuation": False,
        "continuation_plan_projection_used": bool(is_verified_ctir_continuation),
    }
    first_mention_contract: Dict[str, Any] = {
        "enabled": True,
        "requires_explicit_intro": True,
        "requires_grounding": True,
        "disallow_pronoun_first_reference": True,
        "disallow_unearned_familiarity": True,
    }

    narration_seam_audit: Dict[str, Any] | None = None
    if ctir_obj is not None and narrative_plan is None:
        narration_seam_audit = {
            "narrative_plan_mandatory_seam": True,
            "narrative_plan_present": False,
            "narration_plan_bundle_error": narrative_plan_build_error or "unknown_narrative_plan_failure",
            "semantic_bypass_blocked": True,
        }

    # Block B: prompt_context consumes transition_node as structured data only (no inference, no repair).
    transition_payload: dict[str, Any] | None = None
    transition_failure_codes: list[str] = []
    if isinstance(narrative_plan, Mapping):
        transition_payload, transition_failure_codes = _project_transition_node_for_prompt(narrative_plan)
    else:
        transition_payload, transition_failure_codes = (None, ["missing_narrative_plan"])

    transition_required = bool(transition_payload.get("transition_required")) if isinstance(transition_payload, dict) else False
    if isinstance(narration_obligations, dict):
        narration_obligations = {**narration_obligations, "must_advance_scene": bool(transition_required)}

    # Seam-failure metadata for missing/malformed transition_node and for blocked legacy inference paths.
    _transition_signal = _resolution_has_transition_signal(resolution_sem if isinstance(resolution_sem, Mapping) else None)
    _transition_missing = bool(_transition_signal and not isinstance(transition_payload, dict))
    _anchor_incomplete = False
    if isinstance(transition_payload, dict) and transition_required:
        ba = transition_payload.get("before_anchor") if isinstance(transition_payload.get("before_anchor"), Mapping) else {}
        aa = transition_payload.get("after_anchor") if isinstance(transition_payload.get("after_anchor"), Mapping) else {}
        _anchor_incomplete = not bool(ba) or not bool(aa)
    if _transition_missing or _anchor_incomplete or transition_failure_codes:
        tn_audit = {
            "transition_signal_present": bool(_transition_signal),
            "transition_node_present": isinstance(transition_payload, dict),
            "transition_node_failure_codes": list(transition_failure_codes[:16]) if transition_failure_codes else [],
            "transition_required": bool(transition_required),
            "blocked_inference_path": bool(_transition_missing),
            "incomplete_required_anchors": bool(_anchor_incomplete),
        }
        if isinstance(narration_seam_audit, dict):
            narration_seam_audit = {**narration_seam_audit, "transition_node_consumer": tn_audit}
        else:
            narration_seam_audit = {"transition_node_consumer": tn_audit}

    # prompt_debug lane: compact transition consumer mirror (inspect-only).
    prompt_debug_anchor["transition_node_consumer"] = {
        "present": isinstance(transition_payload, dict),
        "transition_signal_present": bool(_transition_signal),
        "failure_codes": list(transition_failure_codes[:16]) if transition_failure_codes else [],
        "blocked_inference_path": bool(_transition_missing),
        "required": bool(transition_required) if isinstance(transition_payload, dict) else None,
    }

    # C1-D: dialogue/social planning is shipped as a deterministic structural plan from the bundle.
    # For CTIR-backed social turns, do not locally infer speaker/intent/pressure/tone from logs or raw text.
    _dsp_required = bool(
        ctir_obj is not None
        and social_authority
        and bool(narration_obligations.get("active_npc_reply_expected"))
    )
    _dsp_raw = _bundle_renderer_inputs.get("dialogue_social_plan") if isinstance(_bundle_renderer_inputs, dict) else None
    _dsp_present = bool(ctir_obj is not None and bundle_stamp_ok and isinstance(_dsp_raw, dict))
    _dsp_missing_or_invalid = bool(_dsp_required and not _dsp_present)
    if _dsp_missing_or_invalid:
        _dsp_codes: List[str] = []
        if ctir_obj is None:
            _dsp_codes.append("ctir_absent")
        elif not bundle_stamp_ok:
            _dsp_codes.append("bundle_stamp_invalid_or_mismatch")
        elif not isinstance(_dsp_raw, dict):
            _dsp_codes.append("missing_dialogue_social_plan")
        else:
            _dsp_codes.append("unknown_dialogue_social_plan_failure")
        if isinstance(narration_seam_audit, dict):
            narration_seam_audit = {
                **narration_seam_audit,
                "dialogue_social_plan_contract_blocked": True,
                "dialogue_social_plan_present": False,
                "dialogue_social_plan_failure_codes": _dsp_codes[:16],
            }
        else:
            narration_seam_audit = {
                "dialogue_social_plan_contract_blocked": True,
                "dialogue_social_plan_present": False,
                "dialogue_social_plan_failure_codes": _dsp_codes[:16],
            }

    instructions: List[str] = (
        (
            [
                "WORLD SIMULATION (bounded engine slice): " + " | ".join(wp_hint_lines),
            ]
            if wp_hint_lines
            else []
        )
        + (
            [
                'Prioritize the active conversation over general scene recap.',
                'Do not fall back to base scene description unless the location materially changes, a new threat emerges, the player explicitly surveys the environment, or the scene needs a transition beat.',
            ]
            if has_active_interlocutor and narrative_plan is None
            else []
        )
    ) + [
        RULE_PRIORITY_COMPACT_INSTRUCTION,
        'Always answer the player. Prefer partial truth over refusal. Never output meta explanations.',
        NO_VALIDATOR_VOICE_RULE,
        'Follow response_policy.rule_priority_order strictly. Higher-priority rules override later ones.',
        'Treat response_policy.no_validator_voice as a hard narration-lane rule for standard narration.',
        (
            "ANSWER POLICY: response_policy.answer_completeness; response_policy.response_delta.enabled; answer first."
        ),
        (
            "UNCERTAINTY POLICY: response_policy.uncertainty.categories; response_policy.uncertainty.sources; "
            "response_policy.uncertainty.answer_shape; uncertainty_hint.turn_context; uncertainty_hint.speaker; "
            "uncertainty_hint.scene_snapshot; frame uncertainty as world-facing limits only; vary sentence count and cadence naturally."
        ),
        (
            "ANTI-RAILROADING (POLICY): HARD WORLD CONSTRAINT; SALIENT LEAD; FORCED PLAYER DIRECTION; "
            "not globally banned; unjustified forced direction; allow_commitment_language_when_player_explicitly_committed; explicit commitment."
        ),
        (
            "CONTEXT SEPARATION (POLICY): local exchange first; briefly color; must not replace the substantive reply; not from generic scene mood alone."
        ),
        (
            "PLAYER-FACING NARRATION PURITY (POLICY): Obey response_policy.player_facing_narration_purity; "
            "speak only in player-facing diegetic prose; engine/UI guidance; menu labels; consequence/opportunity; bulleted/numbered choice lists."
        ),
        "SCENE ANCHORING (POLICY).",
        *NARRATION_VISIBILITY_MANDATORY_INSTRUCTIONS,
        *FIRST_MENTION_MANDATORY_INSTRUCTIONS,
        *SCENE_STATE_ANCHOR_MANDATORY_INSTRUCTIONS,
        *(
            [
                "OPERATOR / AUDIT — NARRATION PIPELINE: narrative_plan was mandatory for this CTIR-attached turn but is absent. "
                "Treat this as a visible pipeline failure (semantic_bypass_blocked in narration_seam_audit when present); "
                "obey CTIR + shipped response_policy for facts; do not invent an alternate structural plan from raw scene text.",
            ]
            if ctir_obj is not None and narrative_plan is None
            else []
        ),
        *(
            [
                "OPERATOR / AUDIT — DIALOGUE SOCIAL PLAN CONTRACT: dialogue_social_plan was required for this CTIR-backed social turn but is missing/invalid. "
                "Use narration_seam_audit.dialogue_social_plan_failure_codes for machine-readable trace; do not invent speaker/intent/tone/pressure or generic conversational glue to compensate.",
            ]
            if _dsp_missing_or_invalid
            else []
        ),
        *(
            [
                "DIALOGUE SOCIAL PLAN (HARD RULE): When top-level dialogue_social_plan is present, it is the ONLY dialogue/social planning source for this turn. "
                "You MUST NOT choose the speaker, decide NPC intent, infer pressure/tone, or add generic conversational glue. "
                "Express only the planned reply_kind and dialogue_intent for the shipped speaker, staying within pressure_state and tone_bounds; obey prohibited_content_codes and derivation_codes.",
                "INCIDENTAL SOCIAL REPLY AUTHORITY: If dialogue_social_plan.reply_plan_kind is harmless_subjective_response_permitted, lack of an authored preference is not a refusal requirement. "
                "The NPC may give a bounded personal opinion, preference, recommendation, reaction, or say they have not tried/seen it; treat it as NPC speech only. "
                "It does not establish objective world truth, inventory, a durable trait, relationship state, quest evidence, or declared_claims. "
                "If reply_plan_kind is consequential_information_request, genuine_refusal, or genuine_uncertainty, preserve that limit and do not convert it into helpful invention. "
                "When dialogue_authority is present, answer its requested_information. Do not substitute a different established fact. "
                "If requested_information is opinion or personal_state and improvisation_permitted is true, state the preference or feeling itself. "
                "Do not claim the speaker lacks knowledge of that preference, and do not add a patrol, a schedule, a payment, or a hidden fact. "
                "Incidental speech is allowed only when improvisation_permitted is true, and that speech is not canonical world truth. "
                "Do not invent patrols, allegiances, rewards, quests, keys, or hidden facts. "
                "If knowledge_posture is unknown, unestablished, or withheld, say so in the speaker's voice without mentioning settled facts, speech authority, or engine limits. "
                "Prior evasive dialogue in recent_log does not by itself force a new refusal when the current plan permits a subjective reply.",
            ]
            if (_dsp_required and _dsp_present)
            else []
        ),
        *(_NARRATIVE_PLAN_STRUCT_GUIDANCE if narrative_plan is not None else ()),
        *(_narrative_plan_roles_trusted_lane() if _narrative_plan_roles_trustworthy(narrative_plan) else ()),
        *(
            _narrative_plan_upstream_role_repair_instruction(narrative_plan)
            if _narrative_plan_roles_trustworthy(narrative_plan)
            else ()
        ),
        (
            "SCENE MOMENTUM RULE (HARD RULE): Every 2–3 exchanges, you MUST introduce exactly one of: "
            "new_information, new_actor_entering, environmental_change, time_pressure, consequence_or_opportunity. "
            "When you do, include exactly one tag in tags: "
            "scene_momentum:<kind> where kind is one of those five identifiers. "
            "If narration_obligations.scene_momentum_due is true, this turn MUST include a momentum beat and MUST include that tag."
        ),
        'Use campaign and world state to keep political and strategic continuity.',
        'Avoid generic dramatic filler and repeated warning phrases. Make NPC replies specific to the speaker and current situation.',
        'Forbidden generic phrases are disallowed: "In this city...", "Times are tough...", "Trust is hard to come by...", "You\'ll need to prove yourself..." — rewrite into specific names/locations/events.',
        'QUESTION / UNCERTAINTY: Answer direct questions before elaboration. Keep uncertainty grounded in response_policy.uncertainty, uncertainty_hint, visible scene limits, or the active NPC knowledge scope.',
        'PERCEPTION / INTENT: For behavioral insight, give one dominant state with concrete observable tells; do not present unsupported motives as fact.',
        'If the player meaningfully moves to a new location, you may provide a new_scene_draft and/or activate_scene_id.',
        'If the player meaningfully changes the world, you may provide world_updates.',
        'If the player text implies a clear mechanical action, suggested_action may be filled for UI assistance, but narration remains primary.',
        'When interaction_continuity has an active target, treat that NPC as the default conversational counterpart.',
        'Non-addressed NPCs should not casually interject; if they interrupt, present it as a notable event with scene justification.',
        'If conversation_privacy or player_position_context implies private exchange (for example lowered_voice), reduce casual eavesdropping/interjection unless scene facts justify otherwise.',
        'Follow authoritative engine state for who is present, player positioning, scene transitions, and check outcomes; narrate outcomes without inventing structured results.',
        'Treat player input as an action declaration: default to third-person phrasing and preserve the user\'s expression format instead of rewriting it.',
        'Quoted in-character dialogue is valid inside an action declaration (for example: Galinor says, "Keep your voice down."); do not treat the quote alone as the entire action when surrounding action context exists.',
        'Follow narration_obligations as output requirements only: they shape wording and focus, but never grant authority to mutate state or decide mechanics.',
        'NARRATION OBLIGATIONS: Use opening and active_npc_reply fields as output requirements only; they shape focus, reply kind, and refusal shape without granting authority.',
        'If narration_obligations.should_answer_active_npc, answer/refuse in active NPC voice rather than empty stalling.',
        'NPC ANSWERS: Provide a concrete answer, partial specific, source, or usable next step when available; otherwise keep the limit in-character.',
        'Use turn_summary and mechanical_resolution as primary narration anchors; treat player_input as supporting evidence for disambiguation, not as the sentence structure to mirror.',
        "Do not restate or paraphrase the player's input. Always continue forward with new information.",
        "Do not repeat the player's spoken line. React to it instead.",
        'If narration_obligations.avoid_input_echo, avoid_player_action_restatement, or prefer_structured_turn_summary is true, continue from resolved state rather than restating player_input.',
        'Keep the narration to 1-4 concise paragraphs.',
        mode_instruction,
    ]

    _opening_contract = opening_scene_export.get("contract") if isinstance(opening_scene_export, dict) else None
    if (
        narration_obligations.get("is_opening_scene")
        and isinstance(_opening_contract, dict)
        and _opening_contract.get("narration_basis_visible_facts") is not None
    ):
        merge_opening_instructions(instructions, contract=_opening_contract)

    if social_authority:
        _skip_instr = (
            "SCENE MOMENTUM RULE",
            "uncertainty_hint",
            "response_policy.uncertainty",
            "classify the uncertainty",
            "Ground uncertainty with",
            "Frame uncertainty as",
            "If uncertainty_hint",
        )
        instructions = [line for line in instructions if not any(m in line for m in _skip_instr)]
        instructions.append(
            "SOCIAL INTERACTION LOCK: Do not use ambient scene narration, scene-wide uncertainty pools, or momentum/pressure "
            "beats as the main voice. The active interlocutor must carry this turn (substantive reply, reaction, or refusal)."
        )

    # Legacy follow-up pressure is derived from recent_log (a continuity proxy). For CTIR-attached turns,
    # prompt_context must not invent continuity/progression signals from logs when the plan is missing or when
    # the plan is verified continuation (C1-B ownership).
    _ctir_plan_missing = bool(ctir_obj is not None and narrative_plan is None)
    if is_verified_ctir_continuation or _ctir_plan_missing:
        follow_up_log_pressure = None
        ap_for_prompt: dict[str, Any] = {}
    else:
        follow_up_log_pressure = _compute_follow_up_pressure(recent_log_compact, user_text)
        ap_for_prompt = _answer_pressure_followup_details(
            player_input=str(user_text or ""),
            recent_log_compact=list(recent_log_compact or []),
            narration_obligations=narration_obligations,
            session_view=session_view,
            answer_completeness=None,
        )
        if follow_up_log_pressure is None and ap_for_prompt.get("answer_pressure_followup_detected"):
            follow_up_log_pressure = _synthetic_follow_up_pressure_from_log(
                recent_log_compact, str(user_text or "")
            )
        if social_authority and not ap_for_prompt.get("answer_pressure_followup_detected"):
            follow_up_log_pressure = None

    active_topic_anchor = explicit_player_topic_anchor_state(str(user_text or ""))

    active_npc_id: str | None = None
    if isinstance(public_scene, Mapping):
        if isinstance(interlocutor_export, dict):
            _nid = str(interlocutor_export.get("npc_id") or "").strip()
            if _nid:
                active_npc_id = _nid
        if active_npc_id is None:
            _tid = session_view.get("active_interaction_target_id")
            if _tid and str(_tid).strip():
                active_npc_id = str(_tid).strip()

    lead_context = build_authoritative_lead_prompt_context(
        session=session,
        world=world,
        public_scene=public_scene,
        runtime=runtime,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_context = build_interlocutor_lead_discussion_context(
        session=session,
        world=world,
        public_scene=public_scene,
        recent_log=recent_log_compact,
        active_npc_id=active_npc_id,
    )
    interlocutor_lead_behavior_hints = deterministic_interlocutor_lead_behavior_hints(
        interlocutor_lead_context
    )
    from_leads_pressure = lead_context.get("follow_up_pressure_from_leads")
    if not isinstance(from_leads_pressure, dict):
        from_leads_pressure = {
            "has_pursued": False,
            "has_stale": False,
            "npc_has_relevant": False,
            "has_escalated_threat": False,
            "has_newly_unlocked": False,
            "has_supersession_cleanup": False,
        }

    if follow_up_log_pressure:
        instructions = list(instructions) + [
            (
                "FOLLOW-UP ESCALATION RULE (HARD RULE): The player is pressing the same topic again (see follow_up_pressure). "
                "Do NOT recycle the same core lead from the previous answer. Escalate by doing AT LEAST TWO of the following: "
                "(1) add one new concrete detail (time, place, condition, count, or observable), "
                "(2) introduce a named person/place/faction/witness tied to the topic (with an in-world source), "
                "(3) narrow the boundary of the unknown (what is ruled out; what is now most likely; what would confirm it), "
                "(4) produce a more actionable immediate next step that uses the new detail. "
                "Preserve uncertainty, but uncertainty must evolve. Preserve speaker grounding."
            ),
            "Allowed repetition: one short anchor clause for continuity. Not allowed: re-stating the same underlying lead as the whole answer.",
        ]

    lead_instr: List[str] = [
        "LEAD REGISTRY (authoritative slice): Use top-level lead_context only as supplied—do not invent leads, facts, or journal summaries. "
        "Turn compact rows into light, actionable nudges (what could matter next), not recap.",
    ]
    # Quarantine progression guidance: for verified CTIR continuation, plan-owned anchors/pressures are the
    # only continuation progression source. Lead registry remains transportable support context, but must not
    # become a substitute continuation planner.
    if is_verified_ctir_continuation or (ctir_obj is not None and narrative_plan is None):
        instructions = list(instructions) + [
            "CTIR CONTINUATION PROGRESSION (HARD RULE): When CTIR is attached, treat `narrative_plan` "
            "(scene_anchors, active_pressures, required_new_information, narrative_mode_contract) as the sole "
            "continuation-progression guide when it is present. If the plan is missing, do not substitute "
            "recent_log, public_scene recap, or lead_context as a replacement continuity plan.",
            *lead_instr,
        ]
    else:
        lead_instr = lead_instr + [
            "When the player is clearly continuing an existing investigation thread, prefer lead_context.currently_pursued_lead as the primary thread anchor when it is non-null.",
            "When interaction_continuity names an active NPC, use lead_context.npc_relevant_leads to tie the exchange to registry-linked threads that list that NPC—without fabricating details beyond those rows.",
            "Use lead_context.urgent_or_stale_leads to surface unattended time pressure or stale threads as diegetic tension or reminders—only as implied by those rows; do not invent urgency.",
            "Use lead_context.recent_lead_changes for continuity with the latest registry state shifts (status, next_step, touches)—do not restate full buckets or dump all leads.",
            "follow_up_pressure.from_leads is boolean-only: has_pursued, has_stale, npc_has_relevant, has_escalated_threat, has_newly_unlocked, has_supersession_cleanup. Do not treat it as prose; use the matching lead_context lists/objects for specifics.",
            "If follow_up_pressure.from_leads.has_pursued is true, bias narration toward continuing that pursued thread when it fits the player's action.",
            "If follow_up_pressure.from_leads.has_stale is true, you may surface reminder, pressure, or unattended-thread beats that fit the scene—without inventing facts beyond lead_context.",
            "If follow_up_pressure.from_leads.npc_has_relevant is true, you may let the active NPC exchange reflect relevance to those threads—within knowledge_scope and without inventing registry facts.",
            "If follow_up_pressure.from_leads.has_escalated_threat is true, bias tension beats toward unattended threat rows in lead_context (escalation fields)—without inventing facts beyond those rows.",
            "If follow_up_pressure.from_leads.has_newly_unlocked is true, you may acknowledge a thread becoming available or unblocked when it fits the scene—grounded in unlocked_by_lead_id / recent_lead_changes only.",
            "If follow_up_pressure.from_leads.has_supersession_cleanup is true, avoid treating superseded obsoleted threads as primary pressure unless the player returns to them; prefer current non-terminal rows.",
        ]
        instructions = list(instructions) + lead_instr

    if social_authority and active_topic_anchor.get("active"):
        instructions = list(instructions) + [
            "ACTIVE TOPIC ANCHOR (HARD RULE): The player explicitly corrected or narrowed the conversational subject "
            "this turn. Answer that subject first in the active interlocutor's voice. Do not pivot back to "
            "lead_context.currently_pursued_lead, urgent_or_stale_leads, or unrelated registry mystery threads "
            "for convenience. Registry salience alone is not sufficient to override the clarified subject. "
            "A redirect is allowed only after a substantive answer—or honest refusal, evasion, or ignorance—on the "
            "asked subject.",
        ]

    if social_authority:
        if follow_up_log_pressure is not None:
            follow_up_pressure = {**follow_up_log_pressure, "from_leads": dict(from_leads_pressure)}
        else:
            follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    elif follow_up_log_pressure is not None:
        follow_up_pressure = {**follow_up_log_pressure, "from_leads": dict(from_leads_pressure)}
    elif any(from_leads_pressure.values()):
        follow_up_pressure = {"from_leads": dict(from_leads_pressure)}
    else:
        follow_up_pressure = None

    naming_line: str | None = None
    if interlocutor_export and str(interlocutor_export.get("npc_id") or "").strip():
        nid = str(interlocutor_export.get("npc_id") or "").strip()
        dn = str(interlocutor_export.get("display_name") or "").strip()
        naming_line = (
            f"NAMING CONTINUITY (engine): Active interlocutor canonical id is {nid!r}"
            + (f", display name {dn!r}" if dn else "")
            + ". Keep this name/title stable across turns unless engine state changes it; "
            "do not regress to generic unnamed incidental-crowd wording for this id."
        )
        instructions = list(instructions) + list(answer_style_hints_list) + [naming_line]

    soc_profile = build_social_interlocutor_profile(interlocutor_export)

    # Presentation-only scene id for speaker contract packaging (not narrative_mode / plan / CTIR).
    scene_id_for_speaker = scene_pub_id or (
        str((session.get("scene_state") or {}).get("active_scene_id") or "").strip()
        if isinstance(session, dict)
        else ""
    )
    speaker_selection = build_speaker_selection_contract(
        session if isinstance(session, dict) else None,
        world if isinstance(world, dict) else None,
        scene_id_for_speaker,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
    )
    tone_escalation_build_error: str | None = None
    try:
        tone_escalation_contract = build_tone_escalation_contract(
            session=session if isinstance(session, dict) else None,
            world=world if isinstance(world, dict) else None,
            scene_id=str(scene_id_for_speaker or "").strip(),
            resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
            speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
            scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
            narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
            recent_log=list(recent_log_for_prompt or []),
        )
    except Exception as exc:
        tone_escalation_build_error = f"{type(exc).__name__}: {exc}"
        tone_escalation_contract = build_tone_escalation_contract(
            session=None,
            world=None,
            scene_id="",
            resolution=None,
            speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
            scene_state_anchor_contract=None,
            narration_visibility=None,
            recent_log=None,
        )
        tone_escalation_contract["scene_id"] = str(scene_id_for_speaker or "").strip()
        tone_escalation_contract["debug_reason"] = (
            f"prompt_context_tone_escalation_build_failed:{type(exc).__name__}"
        )
        _te_df = tone_escalation_contract.get("debug_flags")
        tone_escalation_contract["debug_flags"] = {
            **(_te_df if isinstance(_te_df, dict) else {}),
            "exception": str(exc),
        }
    response_policy["tone_escalation"] = tone_escalation_contract
    _te_dbg = _tone_escalation_prompt_debug_anchor(tone_escalation_contract)
    if tone_escalation_build_error is not None:
        _te_dbg = {**_te_dbg, "build_error": tone_escalation_build_error[:500]}
    prompt_debug_anchor["tone_escalation"] = _te_dbg

    _psid = str((speaker_selection or {}).get("primary_speaker_id") or "").strip()
    _allowed_ids = [
        str(x).strip()
        for x in ((speaker_selection or {}).get("allowed_speaker_ids") or [])
        if isinstance(x, str) and str(x).strip()
    ]
    _switch_ok = bool((speaker_selection or {}).get("speaker_switch_allowed"))
    _gff = bool((speaker_selection or {}).get("generic_fallback_forbidden"))
    _labels_preview = ", ".join(
        repr(x) for x in ((speaker_selection or {}).get("forbidden_fallback_labels") or [])[:8]
    )
    _speaker_contract_instr: List[str] = [
        "SPEAKER SELECTION CONTRACT (HARD RULE): Obey the top-level `speaker_selection` object. "
        "When `primary_speaker_id` is non-null, treat that NPC as the default voice for substantive quoted dialogue "
        "and in-character answers for this turn.",
    ]
    if not _allowed_ids:
        _speaker_contract_instr.append(
            "SPEAKER SELECTION CONTRACT (HARD RULE): `allowed_speaker_ids` is empty — do not attribute quoted speech to any NPC; "
            "remain narrator-neutral. Do not invent incidental speakers or crowd voices to answer for a missing interlocutor."
        )
    else:
        _speaker_contract_instr.append(
            f"SPEAKER SELECTION CONTRACT (HARD RULE): Only these NPC ids may carry quoted NPC dialogue this turn: {_allowed_ids!r}. "
            "Do not give spoken lines to anyone else (including newly invented characters)."
        )
        if not _switch_ok:
            _speaker_contract_instr.append(
                "SPEAKER SELECTION CONTRACT (HARD RULE): `speaker_switch_allowed` is false — do not move the substantive reply "
                "to a different NPC mid-turn. If `interruption_allowed` is true, a single explicit scene-event interruption may cut "
                "off the current speaker per `interruption_requires_scene_event`."
            )
    if _gff:
        _speaker_contract_instr.append(
            "SPEAKER SELECTION CONTRACT (HARD RULE): `generic_fallback_forbidden` is true — do not use generic unnamed stand-ins "
            f"(for example {_labels_preview}) as the answer source."
        )
    instructions = list(instructions) + _speaker_contract_instr

    # Machine-readable boundary only; exhaustive checks live outside this module (e.g. emission gate).
    # narration_visibility= full ``build_narration_visibility_contract`` snapshot (not the slim prompt export).
    narrative_authority_contract = build_narrative_authority_contract(
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        session_view=session_view if isinstance(session_view, dict) else None,
    )
    response_policy["narrative_authority"] = narrative_authority_contract
    response_policy["forbid_unjustified_narrative_authority"] = True

    prompt_debug_anchor["narrative_authority"] = {
        "enabled": narrative_authority_contract.get("enabled"),
        "authoritative_outcome_available": narrative_authority_contract.get("authoritative_outcome_available"),
        "success_state_available": narrative_authority_contract.get("success_state_available"),
        "mechanical_result_available": narrative_authority_contract.get("mechanical_result_available"),
        "forbid_unresolved_outcome_assertions": narrative_authority_contract.get(
            "forbid_unresolved_outcome_assertions"
        ),
        "forbid_hidden_fact_assertions": narrative_authority_contract.get("forbid_hidden_fact_assertions"),
        "forbid_npc_intent_assertions_without_basis": narrative_authority_contract.get(
            "forbid_npc_intent_assertions_without_basis"
        ),
        "preferred_deferral_order": list(narrative_authority_contract.get("preferred_deferral_order") or []),
    }

    follow_surface = session.get("follow_surface") if isinstance(session, dict) else None
    anti_railroading_contract = build_anti_railroading_contract(
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        narration_obligations=narration_obligations,
        session_view=session_view if isinstance(session_view, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        narrative_authority_contract=narrative_authority_contract if isinstance(narrative_authority_contract, dict) else None,
        prompt_leads=lead_context,
        active_pending_leads=active_pending_leads,
        follow_surface=follow_surface,
        player_text=str(user_text or ""),
    )
    response_policy["anti_railroading"] = anti_railroading_contract

    prompt_debug_anchor["anti_railroading"] = {
        "enabled": bool(anti_railroading_contract.get("enabled")),
        "surfaced_lead_count": len(anti_railroading_contract.get("surfaced_lead_ids") or []),
        "allow_directional_language_from_resolved_transition": anti_railroading_contract.get(
            "allow_directional_language_from_resolved_transition"
        ),
        "allow_exclusivity_from_authoritative_resolution": anti_railroading_contract.get(
            "allow_exclusivity_from_authoritative_resolution"
        ),
        "allow_commitment_language_when_player_explicitly_committed": anti_railroading_contract.get(
            "allow_commitment_language_when_player_explicitly_committed"
        ),
    }

    interaction_for_rtc = (
        interaction_context_snapshot_from_ctir_semantics(interaction_sem)
        if ctir_obj is not None
        else response_type_context_snapshot(session if isinstance(session, dict) else None)
    )
    _rtc_policy_early = response_policy.get("response_type_contract")
    _rtc_authoritative, _rtc_authoritative_source = _resolve_authoritative_response_type_contract_impl(
        {"response_policy": {"response_type_contract": _rtc_policy_early}} if isinstance(_rtc_policy_early, dict) else None,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        session=session if isinstance(session, dict) else None,
    )
    if isinstance(_rtc_authoritative, dict):
        rtc_for_social_structure = _rtc_authoritative
        rtc_source = _rtc_authoritative_source or "response_policy"
        response_policy["response_type_contract"] = copy.deepcopy(_rtc_authoritative)
    elif isinstance(_rtc_policy_early, dict):
        rtc_for_social_structure = _rtc_policy_early
        rtc_source = "response_policy"
    else:
        rtc_peeked = peek_response_type_contract_from_resolution(resolution_sem)
        rtc_source = "resolution.metadata" if rtc_peeked is not None else "derived"
        rtc_for_social_structure = rtc_peeked or derive_response_type_contract(
            segmented_turn=None,
            normalized_action=None,
            resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
            interaction_context=interaction_for_rtc,
            directed_social_entry=None,
            route_choice=None,
            raw_player_text=str(user_text or ""),
        ).to_dict()
    _rtc_required = str((rtc_for_social_structure or {}).get("required_response_type") or "").strip().lower()

    _plan_nm = (
        str((narrative_plan or {}).get("narrative_mode") or "").strip()
        if isinstance(narrative_plan, dict)
        else None
    )
    _ao_ok, _ao_reasons = validate_action_outcome_plan_contract(
        narrative_plan if isinstance(narrative_plan, dict) else None,
        response_type_required=_rtc_required or None,
    )
    # Structural action_outcome narration lane follows ``narrative_mode`` only (plan slice may
    # exist with ``present: false`` under continuation; response_type may still tag emission).
    _needs_ao_contract = _plan_nm == "action_outcome"
    # Fail-closed only on the CTIR-backed narration seam; legacy no-CTIR prompts keep prior resolution fallbacks.
    action_outcome_narration_blocked = bool(ctir_obj is not None and _needs_ao_contract and not _ao_ok)
    _ao_src_kind = None
    _ao_deriv_codes: List[str] = []
    if isinstance(narrative_plan, dict):
        _ao_blk = narrative_plan.get("action_outcome")
        if isinstance(_ao_blk, Mapping):
            _ao_src_kind = _ao_blk.get("source_kind")
            _dc = _ao_blk.get("derivation_codes")
            if isinstance(_dc, list):
                _ao_deriv_codes = [str(x) for x in _dc[:48] if isinstance(x, str) and str(x).strip()]
    prompt_debug_anchor["action_outcome_contract"] = {
        "action_outcome_plan_present": bool(
            isinstance(narrative_plan, dict) and isinstance(narrative_plan.get("action_outcome"), Mapping)
        ),
        "action_outcome_plan_valid": bool(_ao_ok),
        "action_outcome_plan_failure_reasons": list(_ao_reasons),
        "action_outcome_source_kind": _ao_src_kind,
        "action_outcome_derivation_codes": _ao_deriv_codes,
        "required_response_type": _rtc_required or None,
    }
    if action_outcome_narration_blocked:
        _ao_audit = {
            "action_outcome_contract_blocked": True,
            "semantic_bypass_blocked": True,
            "action_outcome_plan_failure_reasons": list(_ao_reasons),
        }
        if isinstance(narration_seam_audit, dict):
            narration_seam_audit = {**narration_seam_audit, **_ao_audit}
        else:
            narration_seam_audit = _ao_audit

    turn_summary_struct = _build_turn_summary(
        user_text,
        resolution_sem,
        intent_sem,
        narrative_plan_mode=_plan_nm,
        action_outcome_contract_blocked=action_outcome_narration_blocked,
    )
    _ts_parts = [
        str(turn_summary_struct.get("action_descriptor") or "").strip(),
        str(turn_summary_struct.get("resolution_kind") or "").strip(),
    ]
    _labels_ts = turn_summary_struct.get("intent_labels")
    if isinstance(_labels_ts, list) and _labels_ts:
        _ts_parts.append(", ".join(str(x).strip() for x in _labels_ts if isinstance(x, str) and str(x).strip()))
    turn_summary_for_contract = " ".join(p for p in _ts_parts if p).strip() or None

    scene_summary_for_contract: str | None = None
    if isinstance(public_scene, dict):
        scene_summary_for_contract = str(public_scene.get("summary") or "").strip() or None
    if not scene_summary_for_contract and isinstance(scene, dict):
        _inner = scene.get("scene")
        if isinstance(_inner, dict):
            scene_summary_for_contract = str(_inner.get("summary") or "").strip() or None

    session_view_for_separation: Dict[str, Any] = dict(session_view)
    if isinstance(world_state_view, dict):
        for _k in (
            "compressed_world_pressures",
            "world_pressures",
            "ambient_pressures",
            "surfaced_pressures",
            "surfaced_leads",
            "prompt_leads",
            "active_pending_leads",
            "leads_for_prompt",
        ):
            if _k in world_state_view and _k not in session_view_for_separation:
                session_view_for_separation[_k] = world_state_view[_k]

    compressed_world_pressures_arg: List[str] | None = None
    if isinstance(campaign, dict):
        _cwp_c = campaign.get("world_pressures")
        if isinstance(_cwp_c, list) and _cwp_c:
            compressed_world_pressures_arg = [
                str(x).strip() for x in _cwp_c if isinstance(x, str) and str(x).strip()
            ][:MAX_WORLD_PRESSURES]
    if compressed_world_pressures_arg is None and isinstance(world_state_view, dict):
        for _k in ("compressed_world_pressures", "world_pressures"):
            _raw_wp = world_state_view.get(_k)
            if isinstance(_raw_wp, list) and _raw_wp:
                compressed_world_pressures_arg = [
                    str(x).strip() for x in _raw_wp if isinstance(x, str) and str(x).strip()
                ][:MAX_WORLD_PRESSURES]
                break

    context_separation_contract = build_context_separation_contract(
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        player_text=str(user_text or ""),
        session_view=session_view_for_separation,
        scene_envelope=scene if isinstance(scene, dict) else None,
        scene_summary=scene_summary_for_contract,
        turn_summary=turn_summary_for_contract,
        speaker_selection_contract=speaker_selection if isinstance(speaker_selection, dict) else None,
        scene_state_anchor_contract=scene_state_anchor_contract if isinstance(scene_state_anchor_contract, dict) else None,
        narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
        tone_escalation_contract=tone_escalation_contract if isinstance(tone_escalation_contract, dict) else None,
        compressed_world_pressures=compressed_world_pressures_arg,
        prompt_leads=lead_context,
        active_pending_leads=active_pending_leads,
        follow_surface=follow_surface,
    )
    response_policy["context_separation"] = context_separation_contract
    prompt_debug_anchor["context_separation"] = _context_separation_prompt_debug_anchor(context_separation_contract)

    _pfnp_ik = session_view.get("active_interaction_kind")
    player_facing_narration_purity_contract = build_player_facing_narration_purity_contract(
        interaction_kind=str(_pfnp_ik).strip() if isinstance(_pfnp_ik, str) and str(_pfnp_ik).strip() else None,
        debug_inputs={"scene_id": scene_pub_id or None},
    )
    response_policy["player_facing_narration_purity"] = player_facing_narration_purity_contract
    prompt_debug_anchor["player_facing_narration_purity"] = _player_facing_narration_purity_prompt_debug_anchor(
        player_facing_narration_purity_contract
    )

    # Canonical prompt-contract owner path: ``game.prompt_context`` ships this
    # policy in the prompt bundle. The implementation remains delegated to the
    # downstream policy consumer module as compatibility residue only.
    # ``rtc_for_social_structure`` / ``rtc_source`` are resolved earlier (before
    # ``turn_summary``) for action_outcome contract enforcement.
    social_response_structure_contract = build_social_response_structure_contract(
        rtc_for_social_structure,
        debug_inputs={"scene_id": scene_pub_id or None, "response_type_contract_source": rtc_source},
    )
    response_policy["social_response_structure"] = social_response_structure_contract
    prompt_debug_anchor["social_response_structure"] = _social_response_structure_prompt_debug_anchor(
        social_response_structure_contract
    )

    interaction_continuity_contract = build_interaction_continuity_contract(
        session if isinstance(session, dict) else None,
        scene_id=scene_pub_id or None,
        scene_envelope=scene if isinstance(scene, dict) else None,
        world=world if isinstance(world, dict) else None,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
    )
    response_policy["interaction_continuity"] = interaction_continuity_contract
    prompt_debug_anchor["interaction_continuity"] = _interaction_continuity_prompt_debug_anchor(
        interaction_continuity_contract
    )

    _mechanical_for_policy: Dict[str, Any] | None
    if action_outcome_narration_blocked:
        _mechanical_for_policy = {}
    elif _needs_ao_contract and isinstance(narrative_plan, dict) and _ao_ok:
        _mechanical_for_policy = {"action_outcome": narrative_plan.get("action_outcome")}
    else:
        _mechanical_for_policy = resolution if isinstance(resolution, dict) else None

    fallback_behavior_contract = build_fallback_behavior_contract(
        session=session if isinstance(session, dict) else None,
        scene=scene if isinstance(scene, dict) else None,
        recent_log=recent_log_compact,
        turn_summary=turn_summary_struct,
        # Action-outcome readiness: plan-owned structure only; never raw resolution rescue when blocked.
        mechanical_resolution=_mechanical_for_policy,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        answer_completeness_contract=response_policy.get("answer_completeness"),
        narrative_authority_contract=narrative_authority_contract,
        interaction_continuity_contract=interaction_continuity_contract,
    )
    response_policy["fallback_behavior"] = fallback_behavior_contract
    prompt_debug_anchor["fallback_behavior"] = {
        "enabled": bool(fallback_behavior_contract.get("enabled")),
        "uncertainty_active": bool(fallback_behavior_contract.get("uncertainty_active")),
        "uncertainty_mode": fallback_behavior_contract.get("uncertainty_mode"),
        "uncertainty_sources": list(fallback_behavior_contract.get("uncertainty_sources") or []),
    }

    from game.narrative_authenticity import build_narrative_authenticity_contract

    narrative_authenticity_contract = build_narrative_authenticity_contract(
        response_delta=response_policy.get("response_delta"),
        answer_completeness=response_policy.get("answer_completeness"),
        fallback_behavior=fallback_behavior_contract,
        social_response_structure=social_response_structure_contract,
        response_type_contract=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
        follow_up_pressure=follow_up_pressure if isinstance(follow_up_pressure, Mapping) else None,
        recent_log_compact=recent_log_compact,
        player_text=str(user_text or ""),
    )
    response_policy["narrative_authenticity"] = narrative_authenticity_contract
    prompt_debug_anchor["narrative_authenticity"] = _narrative_authenticity_prompt_debug_anchor(
        narrative_authenticity_contract
    )

    _ic_dbg = interaction_continuity_contract.get("debug")
    _ic_dbg_map = _ic_dbg if isinstance(_ic_dbg, dict) else {}
    _source_of_activity_anchor = str(_ic_dbg_map.get("source_of_anchor") or "").strip()
    _vis_ids_raw = visibility_contract.get("visible_entity_ids") if isinstance(visibility_contract, dict) else []
    _active_scene_entity_ids = [
        str(x).strip() for x in (_vis_ids_raw if isinstance(_vis_ids_raw, list) else []) if isinstance(x, str) and str(x).strip()
    ]
    _alias_map = visibility_contract.get("visible_entity_aliases") if isinstance(visibility_contract, dict) else None
    if not isinstance(_alias_map, dict):
        _alias_map = {}
    _re_ent, _re_top, _re_dbg = _extract_explicit_reintroductions(
        str(user_text or ""),
        entity_alias_map=_alias_map,
        topic_anchor_tokens=_memory_window_focus_topic_tokens(active_topic_anchor),
        anchored_interlocutor_id=str(interaction_continuity_contract.get("anchored_interlocutor_id") or ""),
        active_interaction_target_id=str(interaction_continuity_contract.get("active_interaction_target_id") or ""),
    )
    conversational_memory_window = build_conversational_memory_window_contract(
        enabled=True,
        recent_turn_window=6,
        soft_memory_limit=CONVERSATIONAL_MEMORY_SOFT_LIMIT,
        stale_after_turns=18,
        active_scene_entity_ids=_active_scene_entity_ids,
        anchored_interlocutor_id=str(interaction_continuity_contract.get("anchored_interlocutor_id") or ""),
        active_interaction_target_id=str(interaction_continuity_contract.get("active_interaction_target_id") or ""),
        explicit_reintroduced_entity_ids=_re_ent,
        explicit_reintroduced_topics=_re_top,
        selection_debug=dict(_re_dbg) if isinstance(_re_dbg, dict) else {},
        source_of_activity_anchor=_source_of_activity_anchor or "interaction_continuity",
        source_of_recentness="session.turn_counter",
        source_of_reintroductions="player_text+visibility_aliases",
    )
    _mem_cands, _mem_extras = _assemble_conversational_memory_candidates(
        recent_log_for_prompt=list(recent_log_for_prompt or []),
        current_turn=int(session_view.get("turn_counter") or 0),
        runtime_compressed=runtime,
        interlocutor_lead_context=interlocutor_lead_context,
        active_npc_id=active_npc_id,
    )
    selected_conversational_memory = select_conversational_memory_window(
        _mem_cands,
        conversational_memory_window,
        current_turn=int(session_view.get("turn_counter") or 0),
    )
    recent_log_for_payload = _recent_log_payload_from_selected_memory(
        selected_conversational_memory,
        _mem_cands,
        _mem_extras,
    )
    prompt_debug_anchor["conversational_memory"] = {
        "candidate_count": len(_mem_cands),
        "selected_count": len(selected_conversational_memory),
    }
    # Shipped policy mirror for downstream inspection (same object as payload; no second selector).
    response_policy["conversational_memory_window"] = conversational_memory_window
    instructions = list(instructions) + [
        "CONVERSATIONAL MEMORY WINDOW: Treat `selected_conversational_memory` as the bounded active conversational thread for this turn—prioritize it over older or omitted chat material. "
        "Do not revive stale side threads unless the player explicitly re-grounds them (see `conversational_memory_window.explicit_reintroduced_*`). "
        "Omitted older material is background only—not an active unresolved obligation.",
    ]

    _policy_tail: List[str] = [
        (
            "POLICY BRIDGE: Obey the shipped response_policy objects as the canonical provider-facing policy surface "
            "(narrative_authority, fallback_behavior, tone_escalation, anti_railroading, context_separation, "
            "player_facing_narration_purity, narrative_authenticity, and scene anchoring). Keep local intent primary, "
            "keep uncertainty qualified, preserve player agency and hypotheses, avoid internal/planner language in narration, "
            "and do not treat policy prose or the answer recipe as authority to create facts."
        ),
    ]
    if social_response_structure_contract.get("enabled"):
        _policy_tail = list(_policy_tail) + [
            (
                "SOCIAL RESPONSE STRUCTURE: Obey response_policy.social_response_structure; keep quoted NPC speech primary, "
                "answer/refuse/qualify conversationally, and avoid bullet-like dialogue."
            ),
        ]

    _np_for_mode = narrative_plan if isinstance(narrative_plan, dict) else None
    _pnm = str(_np_for_mode.get("narrative_mode") or "").strip() if isinstance(_np_for_mode, dict) else ""
    narrative_mode_instruction_lines = _build_narrative_mode_instructions(
        narrative_mode_contract=(
            narrative_plan.get("narrative_mode_contract") if isinstance(narrative_plan, dict) else None
        ),
        response_policy=response_policy,
        narration_obligations=narration_obligations,
        resolution_sem=resolution_sem if isinstance(resolution_sem, dict) else None,
        narrative_plan_present=_np_for_mode is not None,
        plan_narrative_mode=_pnm or None,
    )
    prompt_debug_anchor["narrative_mode_instructions"] = _narrative_mode_instruction_prompt_debug(
        narrative_plan.get("narrative_mode_contract") if isinstance(narrative_plan, dict) else None,
        instruction_lines=narrative_mode_instruction_lines,
        narrative_plan_present=_np_for_mode is not None,
        plan_narrative_mode=_pnm or None,
    )
    instructions = list(instructions) + list(narrative_mode_instruction_lines) + _policy_tail
    if action_outcome_narration_blocked:
        _ao_codes = "|".join(str(x) for x in (_ao_reasons or [])[:16])
        instructions = list(instructions) + [
            "OPERATOR / AUDIT — ACTION_OUTCOME CONTRACT: narrative_plan.action_outcome is missing or failed validation. "
            f"Machine-readable codes: {_ao_codes or 'unknown'}. "
            "narration_seam_audit.semantic_bypass_blocked is true for this turn. "
            "Do not narrate resolved mechanics, DCs, rolls, damage, or success from player_input, hints, prompts, or raw resolution text.",
        ]

    use_manual_play_compact = _should_use_manual_play_compact_prompt(
        prompt_profile=prompt_profile,
        narration_obligations=narration_obligations,
        resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
        uncertainty_hint=eff_uncertainty_hint if isinstance(eff_uncertainty_hint, Mapping) else None,
        follow_up_pressure=follow_up_pressure if isinstance(follow_up_pressure, Mapping) else None,
        active_topic_anchor=active_topic_anchor if isinstance(active_topic_anchor, Mapping) else None,
    )
    public_scene_for_prompt = dict(public_scene) if isinstance(public_scene, dict) else {}
    if narration_obligations.get("is_opening_scene") and isinstance(public_scene_for_prompt, dict):
        public_scene_for_prompt["visible_facts"] = list(visible_facts_export)
    if use_manual_play_compact:
        selected_conversational_memory = list(selected_conversational_memory[:MANUAL_PLAY_COMPACT_MEMORY_LIMIT])
        recent_log_for_payload = _recent_log_payload_from_selected_memory(
            selected_conversational_memory,
            _mem_cands,
            _mem_extras,
        )
        recent_log_for_payload = list(recent_log_for_payload[:MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT])
        visible_facts_export = list(visible_facts_export[:MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT])
        if isinstance(public_scene_for_prompt.get("visible_facts"), list):
            public_scene_for_prompt["visible_facts"] = list(
                public_scene_for_prompt.get("visible_facts")[:MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT]
            )
        instructions = _compact_manual_play_instructions(
            mode_instruction=mode_instruction,
            narration_obligations=narration_obligations,
            response_policy=response_policy,
            has_active_interlocutor=has_active_interlocutor,
            social_authority=social_authority,
            has_scene_change_context=has_scene_change_context,
            naming_line=naming_line if isinstance(naming_line, str) else None,
            answer_style_hints=list(answer_style_hints_list),
            narrative_plan_present=narrative_plan is not None,
            narrative_mode_instruction_lines=narrative_mode_instruction_lines,
        )
        prompt_debug_anchor["compact_prompt"] = {
            "enabled": True,
            "profile": "manual_play_compact",
            "visible_fact_limit": MANUAL_PLAY_COMPACT_VISIBLE_FACT_LIMIT,
            "selected_memory_limit": MANUAL_PLAY_COMPACT_MEMORY_LIMIT,
            "recent_log_limit": MANUAL_PLAY_COMPACT_RECENT_LOG_LIMIT,
            "selected_memory_count": len(selected_conversational_memory),
            "recent_log_count": len(recent_log_for_payload),
        }
    else:
        prompt_debug_anchor["compact_prompt"] = {
            "enabled": False,
            "profile": "full",
        }

    # Canonical snapshot for retry / gate contract lookup (not authoritative engine state).
    _btp = _bundle_renderer_inputs.get("turn_packet") if isinstance(_bundle_renderer_inputs, dict) else None
    _brt = _bundle_renderer_inputs.get("referent_tracking") if isinstance(_bundle_renderer_inputs, dict) else None
    _bdsp = _bundle_renderer_inputs.get("dialogue_social_plan") if isinstance(_bundle_renderer_inputs, dict) else None
    if ctir_obj is not None and bundle_stamp_ok and isinstance(_btp, dict) and isinstance(_brt, dict):
        _turn_packet = copy.deepcopy(_btp)
        referent_tracking = copy.deepcopy(_brt)
    else:
        _turn_packet = build_turn_packet(
            response_policy=response_policy,
            scene_id=scene_pub_id or None,
            player_text=str(user_text or ""),
            resolution=resolution_sem if isinstance(resolution_sem, dict) else None,
            interaction_continuity=interaction_continuity,
            narration_obligations=narration_obligations,
            last_human_adjacent_continuity=(
                runtime.get("last_human_adjacent_continuity") if isinstance(runtime, dict) else None
            ),
            response_type=rtc_for_social_structure if isinstance(rtc_for_social_structure, dict) else None,
            sources_used=["prompt_context.build_compressed_narration_context"],
        )
        # Objective #7: single call into referent_tracking owner; visibility remains the narration_visibility *contract* slice.
        _plids_for_referent = pending_lead_ids_from_active_pending(active_pending_leads)
        _session_interaction_for_referent = session_interaction_slice_for_narrative_plan(
            session_view if isinstance(session_view, dict) else None,
            _plids_for_referent,
        )
        referent_tracking = build_referent_tracking_artifact(
            narration_visibility=visibility_contract if isinstance(visibility_contract, dict) else None,
            speaker_selection=speaker_selection if isinstance(speaker_selection, dict) else None,
            interaction_continuity=interaction_continuity_contract if isinstance(interaction_continuity_contract, dict) else None,
            session_interaction=_session_interaction_for_referent if _session_interaction_for_referent else None,
            narrative_plan=narrative_plan if isinstance(narrative_plan, dict) else None,
            turn_packet=_turn_packet if isinstance(_turn_packet, dict) else None,
        )
    if isinstance(_turn_packet, dict):
        _turn_packet["referent_tracking_compact"] = {
            "referent_artifact_version": referent_tracking.get("version"),
            "active_interaction_target": referent_tracking.get("active_interaction_target"),
            "referential_ambiguity_class": referent_tracking.get("referential_ambiguity_class"),
            "ambiguity_risk": referent_tracking.get("ambiguity_risk"),
        }
        _tp_dbg = _turn_packet.get("debug")
        if isinstance(_tp_dbg, dict):
            _turn_packet["debug"] = {
                **_tp_dbg,
                "world_progression": {
                    "changed_nodes_head": list((wp_projection or {}).get("changed_node_ids") or [])[:8],
                    "active_projects_n": len((wp_projection or {}).get("active_projects") or []),
                    "world_clocks_n": len((wp_projection or {}).get("world_clocks") or []),
                },
            }

    projected_narrative_plan = (
        None
        if action_outcome_narration_blocked
        else (
            public_narrative_plan_projection_for_prompt(narrative_plan)
            if isinstance(narrative_plan, dict) and narrative_plan
            else None
        )
    )

    def _validate_projected_answer_exposition_plan(obj: Any) -> str | None:
        if obj is None:
            return "missing"
        if not isinstance(obj, Mapping):
            return "not_mapping"
        for k in ("enabled", "answer_required"):
            if not isinstance(obj.get(k), bool):
                return f"missing_or_bad_bool:{k}"
        if not isinstance(obj.get("facts"), list):
            return "facts_not_list"
        for i, f in enumerate((obj.get("facts") or [])[:48]):
            if not isinstance(f, Mapping):
                return f"fact_not_mapping:{i}"
            if not str(f.get("id") or "").strip():
                return f"fact_missing_id:{i}"
            if not str(f.get("fact") or "").strip():
                return f"fact_missing_fact:{f.get('id')}"
            # Preserve plan-owned metadata; prompt_context must not "fix" these fields.
            for mk in ("source", "visibility", "certainty"):
                if not str(f.get(mk) or "").strip():
                    return f"fact_missing_meta:{mk}:{f.get('id')}"
        for req in ("constraints", "voice", "delivery"):
            if not isinstance(obj.get(req), Mapping):
                return f"missing_{req}"
        return None

    aep = (
        projected_narrative_plan.get("answer_exposition_plan")
        if isinstance(projected_narrative_plan, Mapping)
        else None
    )
    aep_err = _validate_projected_answer_exposition_plan(aep)
    aep_valid = aep_err is None
    ac_policy = (
        response_policy.get("answer_completeness")
        if isinstance(response_policy, dict) and isinstance(response_policy.get("answer_completeness"), Mapping)
        else {}
    )
    answer_required = bool((ac_policy or {}).get("answer_required"))
    prompt_debug_anchor["answer_exposition_plan_projection"] = {
        "present": aep is not None,
        "valid": bool(aep_valid),
        "validation_error": aep_err,
        "answer_required": bool(answer_required),
        "sourced_from": "public_narrative_plan_projection_for_prompt",
    }

    if isinstance(response_policy, dict) and isinstance(ac_policy, dict):
        # Mirror plan-owned answer facts into the shipped response-policy surface for downstream inspection.
        ac_policy["answer_exposition_plan"] = copy.deepcopy(aep) if aep_valid else None
        if not aep_valid:
            ac_policy["answer_exposition_plan_validation_error"] = aep_err
        response_policy["answer_completeness"] = ac_policy

    if answer_required and not aep_valid:
        # Visible seam: answer was required but the plan-owned answer facts did not reach the prompt.
        prompt_debug_anchor["answer_exposition_plan_seam"] = {
            "seam_open": True,
            "reason": "answer_required_but_missing_or_invalid_projected_answer_exposition_plan",
            "validation_error": aep_err,
        }

    payload: Dict[str, Any] = {
        'instructions': instructions,
        'bounded_improvisation': prompt_projection_for_bounded_improvisation(
            session if isinstance(session, Mapping) else None,
            scene_id=scene_pub_id or None,
        ),
        'dialogue_social_plan': (
            copy.deepcopy(_bdsp)
            if (ctir_obj is not None and bundle_stamp_ok and isinstance(_bdsp, dict))
            else None
        ),
        # Block B: structured transition payload sourced ONLY from narrative_plan.transition_node.
        'transition': copy.deepcopy(transition_payload) if isinstance(transition_payload, dict) else None,
        'narrative_plan': (
            None
            if action_outcome_narration_blocked
            else (
                public_narrative_plan_projection_for_prompt(narrative_plan)
                if isinstance(narrative_plan, dict) and narrative_plan
                else None
            )
        ),
        'speaker_selection': speaker_selection,
        'active_topic_anchor': active_topic_anchor,
        'interaction_continuity': interaction_continuity,
        'active_interlocutor': interlocutor_export,
        'social_context': {
            'interlocutor_profile': soc_profile,
            'answer_style_hints': list(answer_style_hints_list),
        },
        'turn_summary': turn_summary_struct,
        'recent_log': recent_log_for_payload,
        'conversational_memory_window': conversational_memory_window,
        'selected_conversational_memory': selected_conversational_memory,
        'player_input': str(user_text or ''),
        'follow_up_pressure': follow_up_pressure,
        'lead_context': lead_context,
        'interlocutor_lead_context': interlocutor_lead_context,
        'interlocutor_lead_behavior_hints': interlocutor_lead_behavior_hints,
        'response_policy': response_policy,
        'referent_tracking': referent_tracking,
        **(
            {'referent_clause_prompt_hints': h}
            if (h := _project_clause_referent_prompt_hints(referent_tracking if isinstance(referent_tracking, dict) else None))
            else {}
        ),
        'turn_packet': _turn_packet,
        'fallback_behavior': fallback_behavior_contract,
        'uncertainty_hint': eff_uncertainty_hint,
        'narration_obligations': narration_obligations,
        'opening_narration_obligations': (
            opening_scene_export.get("opening_narration_obligations")
            if isinstance(opening_scene_export, dict)
            else None
        ),
        'opening_scene_realization': opening_scene_export if isinstance(opening_scene_export, dict) else opening_realization_none(),
        'opening_inputs_are_curated': bool(opening_inputs_are_curated),
        'opening_selector_source_used': (
            opening_fact_telemetry.get("opening_fact_source_used")
            if isinstance(opening_fact_telemetry, dict)
            else "none"
        ),
        'opening_selector_selected_facts': list(opening_selector_selected_facts),
        'opening_curated_facts': list(opening_selector_selected_facts) if opening_inputs_are_curated else [],
        'opening_fact_telemetry': opening_fact_telemetry,
        'narration_visibility': narration_visibility,
        'scene_state_anchor_contract': scene_state_anchor_contract,
        'anti_railroading_contract': anti_railroading_contract,
        'context_separation_contract': context_separation_contract,
        'player_facing_narration_purity_contract': player_facing_narration_purity_contract,
        'social_response_structure_contract': social_response_structure_contract,
        'interaction_continuity_contract': interaction_continuity_contract,
        'prompt_debug': prompt_debug_anchor,
        'first_mention_contract': first_mention_contract,
        'discoverable_hinting': True,
        # Action-outcome readiness: ship plan ``action_outcome`` only when contract-valid; else seam-closed (no raw rescue).
        'mechanical_resolution': (
            None
            if action_outcome_narration_blocked
            else (
                {"action_outcome": narrative_plan.get("action_outcome")}
                if _needs_ao_contract and isinstance(narrative_plan, dict) and _ao_ok
                else resolution
            )
        ),
        'scene_advancement': scene_advancement,
        'session': session_view,
        'character': {
            'name': str(character.get('name', '') or ''),
            'role': str(campaign.get('character_role', '') or ''),
            'hp': character.get('hp'),
            'ac': character.get('ac'),
            'conditions': character.get('conditions', []),
            'attacks': character.get('attacks', []),
            'spells': character.get('spells', {}),
            'skills': character.get('skills', {}),
        }
        if character and isinstance(character, dict)
        else {'name': '', 'role': '', 'hp': {}, 'ac': {}, 'conditions': [], 'attacks': [], 'spells': {}, 'skills': {}},
        'combat': _compress_combat(combat),
        'world_state': world_state_view,
        'world': _compress_world(world),
        'world_progression_summary': list(wp_hint_lines),
        'campaign': _compress_campaign(campaign),
        'scene': {
            'public': public_scene_for_prompt if public_scene_for_prompt else public_scene,
            'discoverable_clues': discoverable_clues,
            'gm_only': {
                'hidden_facts': gm_only_hidden_facts,
                'discoverable_clues_locked': gm_only_discoverable_locked,
            },
            'clue_records': {'discovered': discovered_clue_records, 'undiscovered': undiscovered_clue_records},
            'visible_clues': discovered_clue_records,
            'discovered_clues': discovered_clue_records,
            'clue_visibility': clue_visibility,
            'pending_leads': active_pending_leads,
            'runtime': runtime,
            'intent': intent_for_scene_payload,
            'layering_rules': {
                'visible_facts': 'Only visible facts may be directly asserted; align with narration_visibility.visible_facts.',
                'discoverable_clues': 'Reveal only when player investigates/searches/questions/observes closely; with discoverable_hinting, hint without asserting as confirmed truth.',
                'hidden_facts': 'Never reveal directly; use only for implications, NPC behavior, atmosphere, indirect clues.',
            },
        },
        'player_expression_contract': {
            'default_action_style': 'third_person',
            'quoted_speech_allowed': True,
            'preserve_user_expression_format': True,
            'example': 'Galinor asks, "What changed at the north gate?" while examining the notice board.',
        },
    }
    if narration_obligations.get("is_opening_scene"):
        assert payload["opening_inputs_are_curated"] is True
    if narration_seam_audit is not None:
        payload["narration_seam_audit"] = narration_seam_audit
    if use_manual_play_compact:
        for key in (
            'fallback_behavior',
            'anti_railroading_contract',
            'context_separation_contract',
            'player_facing_narration_purity_contract',
            'social_response_structure_contract',
            'interaction_continuity_contract',
            'first_mention_contract',
        ):
            payload.pop(key, None)
    from game.gm_resolution_decision import narration_authority_fields, prompt_projection_for_temporal_provenance

    authority_fields = narration_authority_fields(resolution)
    if authority_fields.get("resolution_contract"):
        payload["resolution_contract"] = authority_fields["resolution_contract"]
    if authority_fields.get("gm_resolution_decision"):
        payload["gm_resolution_decision"] = authority_fields["gm_resolution_decision"]
    if authority_fields.get("decision_facing_answer_recipe"):
        payload["decision_facing_answer_recipe"] = authority_fields["decision_facing_answer_recipe"]
        payload["instructions"] = list(payload.get("instructions") or []) + [
            "ANSWER RECIPE: Follow decision_facing_answer_recipe for this turn. "
            "It projects gm_resolution_decision and does not add authority. "
            "The decision wins if they disagree."
        ]
    elif authority_fields.get("resolution_contract"):
        payload["instructions"] = list(payload.get("instructions") or []) + [
            "RESOLUTION CONTRACT: Obey resolution_contract.constraint. It names the requested target and semantic point."
        ]
    if (
        authority_fields.get("gm_resolution_decision")
        and isinstance(resolution, dict)
        and payload.get("mechanical_resolution") is resolution
    ):
        payload["mechanical_resolution"] = _provider_mechanical_resolution(resolution)
    temporal_provenance = prompt_projection_for_temporal_provenance(
        session,
        scene_id=str((session or {}).get("active_scene_id") or "") if isinstance(session, Mapping) else None,
    )
    if any(temporal_provenance.get("buckets", {}).values()):
        payload["narration_temporal_provenance"] = temporal_provenance
    if include_non_public_prompt_keys:
        return payload
    shipped = project_public_payload(payload)
    assert_no_debug_keys_in_prompt_payload(shipped)
    return shipped
```
