"""Classify observed stages, never infer a semantic cause from token counts."""
import copy


def classify(events, *, infrastructure=None, integrity=None, ui=None):
    def result(category, stage, field, value, index=None, source=None):
        return {"category": category, "stage": stage, "evidence_record":
                "diagnostics/provider_usage.jsonl" if index is not None else "reports/result.json",
                "record_index": index, "field": field, "observed_value": value,
                "source": source, "root_cause": "Not established", "inferred": False}
    if infrastructure:
        return result(infrastructure, "infrastructure", "failure", infrastructure)
    if integrity is False:
        return result("state_integrity_violation", "state", "state_comparison.integrity", False,
                      source="docs/state_authority_model.md")
    # Precedence follows earliest evidenced failure; explicit exhaustion beats parsing.
    checks = [
        ("provider_admission_rejection", lambda e: e.get("event") == "rejected", "refusal", "admission"),
        ("provider_exception", lambda e: e.get("classification") == "provider_error", "classification", "provider"),
        ("provider_output_limit_exhaustion", lambda e: e.get("provider_output_limit_exhausted") is True or
         (e.get("provider_status") == "incomplete" and e.get("provider_finish_reason") == "max_output_tokens"), "provider_finish_reason", "provider"),
        ("provider_incomplete_response", lambda e: e.get("provider_status") in {"incomplete", "failed", "cancelled"}, "provider_status", "provider"),
        ("empty_provider_response", lambda e: e.get("classification") == "empty_provider_content", "classification", "extraction"),
        ("json_parsing_failure", lambda e: e.get("classification") == "json_parse_failure", "json_parsing_succeeded", "parsing"),
        ("structured_envelope_failure", lambda e: e.get("classification") in {"missing_structured_envelope", "structured_validation_failure"}, "classification", "structure"),
        ("semantic_validation_failure", lambda e: e.get("stage") == "opening_outcome" and
         (e.get("semantic_classification") == "rejected" or bool(e.get("semantic_reasons"))), "semantic_reasons", "semantic"),
        ("opening_acceptance_failure", lambda e: e.get("stage") == "opening_outcome" and e.get("opening_accepted") is False, "rejection_reason", "acceptance"),
    ]
    for category, predicate, field, stage in checks:
        for i, event in enumerate(events):
            if predicate(event):
                return result(category, stage, field, event.get(field), i,
                              event.get("classification_source") or "game/provider_budget.py")
    if ui and ui.get("status") == "FAIL":
        return result("ui_failure", "ui", "ui.status", "FAIL")
    return result("unknown_failure", "unknown", "failure", "Evidence does not establish a recognized failure stage")


def normalized_document(name, value):
    value = copy.deepcopy(value)
    bookkeeping = {}
    if isinstance(value, dict):
        # Only documented persistence-envelope metadata is excluded.
        if "payload" in value and "persistence_version" in value:
            bookkeeping = {k: value[k] for k in ("saved_at", "integrity") if k in value}
            value = value["payload"]
        if name == "session.json":
            for key in ("last_saved_at", "debug_traces", "__turn_start_active_interaction_target_id"):
                if key in value:
                    bookkeeping[key] = value.pop(key)
    return value, bookkeeping


def compare(before, after, *, accepted):
    gameplay, bookkeeping = [], []
    for name in sorted(set(before) | set(after)):
        a, ab = normalized_document(name, before.get(name))
        b, bb = normalized_document(name, after.get(name))
        # Existing rollback may materialize an empty log.
        if name == "session_log.jsonl":
            a, b = a or [], b or []
        if a != b:
            gameplay.append(name)
        if ab != bb:
            bookkeeping.append(name)
    a, _ = normalized_document("session.json", before.get("session.json", {}))
    b, _ = normalized_document("session.json", after.get("session.json", {}))
    turn_delta = int(b.get("turn_counter") or 0) - int(a.get("turn_counter") or 0)
    log_delta = len(after.get("session_log.jsonl") or []) - len(before.get("session_log.jsonl") or [])
    # Success permits only the runtime roots owned by opening orchestration.
    unexpected = [p for p in gameplay if not accepted or p not in {"session.json", "world.json", "session_log.jsonl"}]
    field_changes = {}
    if accepted:
        allowed_session = {
            'interpretation_telemetry', 'last_bounded_improvisation_promotion', 'last_turn_response_policy',
            'emergent_actor_debug', 'last_action_debug', '_runtime_canonical_ctir_v1',
            '_runtime_narration_plan_bundle_stamp_v1', 'discourse_focus', 'turn_counter', 'chat_history',
            '_runtime_canonical_ctir_stamp_v1', 'conversational_context', 'campaign_started',
            'bounded_improvisation', 'clocks', '_runtime_narration_plan_bundle_v1',
            '_runtime_progression_nodes_fingerprint_v1', 'scene_runtime', 'narration_temporal_provenance',
        }
        for name, allowed in [('session.json', allowed_session), ('world.json', {'event_log', 'factions'})]:
            old, _ = normalized_document(name, before.get(name, {}))
            new, _ = normalized_document(name, after.get(name, {}))
            changed = [k for k in sorted(old.keys() | new.keys()) if old.get(k) != new.get(k)]
            field_changes[name] = changed
            unexpected.extend(name+':'+k for k in changed if k not in allowed)
    integrity = not unexpected and (not accepted or (turn_delta == 1 and log_delta == 1 and b.get("campaign_started") is True))
    return {"gameplay_mutations": gameplay, "bookkeeping_mutations": bookkeeping,
            "unexpected_mutations": unexpected, "integrity": integrity,
            "changed_fields": field_changes,
            "turn_delta": turn_delta, "log_delta": log_delta,
            "campaign_started": bool(b.get("campaign_started")), "scene_identity": b.get("active_scene_id"),
            "contract": "docs/state_authority_model.md; game.api.start_campaign; PR-PLAY-04 rollback"}
