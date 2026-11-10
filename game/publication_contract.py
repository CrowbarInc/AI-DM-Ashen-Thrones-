"""Whether a resolved turn still needs primary narration.

Nonempty text is not completeness. The contract names the owner of the
player-facing sentence. Primary narration is the large turn prompt. A
committed physical change can still take one bounded expression pass.
"""
from __future__ import annotations

import re
from typing import Any

FINAL_ENGINE_RESPONSE = "FINAL_ENGINE_RESPONSE"
ADJUDICATION_RESULT = "ADJUDICATION_RESULT"
LIVE_EXPRESSION_REQUESTED = "LIVE_EXPRESSION_REQUESTED"
CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
UNSUPPORTED_ACTION = "UNSUPPORTED_ACTION"
FAILURE = "FAILURE"

CONTRACTS = frozenset({
    FINAL_ENGINE_RESPONSE,
    ADJUDICATION_RESULT,
    LIVE_EXPRESSION_REQUESTED,
    CLARIFICATION_REQUIRED,
    UNSUPPORTED_ACTION,
    FAILURE,
})

# A completed gameplay publication is a sentence the engine actually delivered:
# accepted speech, a grounded fallback, a deterministic result, or a supported
# read-only gameplay response. An operational refusal means admission or the
# interpretation service stopped the interaction before that delivery.
OPERATIONAL_REFUSAL = "operational_refusal"
OPERATIONAL_REFUSAL_REASONS = frozenset({
    "provider calls disabled",
    "provider budget stopped",
    "playtest_stopped",
    "duplicate request identity",
    "request ceiling",
    "input-token ceiling",
    "output-token ceiling",
    "total-token ceiling",
    "provider admission accounting unavailable",
    "provider usage accounting unavailable",
    "provider budget exceeded after a completed request",
    "provider ledger initialization failed",
    "provider ledger changed within process",
    "provider dispatch ledger write failed",
    "provider completion ledger write failed",
    "provider rejection ledger write failed",
    "generation diagnostic ledger write failed",
    "token_estimate_unavailable",
    "provider_failure",
    "model_mismatch",
    "unresolved_retreat_without_adjudication",
})
_SERVICE_FAILURES = frozenset({"provider_failure", "model_mismatch"})
_ROUTING_REFUSALS = frozenset({"unresolved_retreat_without_adjudication"})
UNADJUDICATED_RETREAT_REASON = "unresolved_retreat_without_adjudication"


_SPOKEN = re.compile(
    r"(?i)\b(?:says|mutters|replies|answers|asks|adds|grunts)\s*,?\s*[\"“]"
)


def gm_is_budget_refusal(gm) -> bool:
    """True when this GM object is an admission refusal, not a narration."""
    if not isinstance(gm, dict):
        return False
    tags = {str(tag) for tag in (gm.get("tags") or []) if isinstance(tag, str)}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    reason = str(meta.get("provider_budget_refusal") or "").strip()
    if reason in OPERATIONAL_REFUSAL_REASONS:
        return True
    return "provider_budget_refused" in tags


def stamp_budget_refusal(resolution, gm) -> str:
    """Mark a budget refusal on the resolution. Does not publish it."""
    if not isinstance(resolution, dict) or not gm_is_budget_refusal(gm):
        return ""
    meta = resolution.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
        resolution["metadata"] = meta
    if meta.get("response_class") == OPERATIONAL_REFUSAL:
        return str(meta.get("refusal_category") or "")
    gm_meta = gm.get("metadata") if isinstance(gm, dict) and isinstance(gm.get("metadata"), dict) else {}
    reason = str(gm_meta.get("provider_budget_refusal") or "").strip()
    if reason not in OPERATIONAL_REFUSAL_REASONS:
        reason = "provider budget stopped"
    classified = classify_operational_refusal(reason, provider_request_sent=False)
    if classified:
        meta.update(classified)
    return reason


def blocks_completed_publication(resolution, gm=None) -> bool:
    """A refusal the player can read that must not become completed gameplay."""
    if gm_is_budget_refusal(gm):
        return True
    if not isinstance(resolution, dict):
        return False
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    return meta.get("response_class") == OPERATIONAL_REFUSAL


def note_completed_publication(session, *, text: str, resolution=None, gm=None):
    """Point session.last_publication at the sentence just delivered.

    The field is the latest completed player-facing publication, not the last
    accepted live expression. A composer that already stored this sentence
    keeps its provenance. A record for any other sentence belongs to an
    earlier turn and is replaced. A rejected expression is not copied forward
    as an acceptance.
    """
    if not isinstance(session, dict):
        return None
    if blocks_completed_publication(resolution, gm):
        return None
    visible = str(text or "").strip()
    if not visible:
        return None
    prior = session.get("last_publication") if isinstance(session.get("last_publication"), dict) else {}
    audit = {}
    if isinstance(gm, dict):
        metadata = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
        candidate = metadata.get("expression_generation")
        if isinstance(candidate, dict):
            audit = candidate
    rejected = audit.get("decision") == "rejected" or audit.get("fallback_used") is True
    campaign_id = session.get("campaign_run_id")
    turn = int(session.get("turn_counter") or 0)
    if (
        prior.get("visible") == visible
        and prior.get("final") is True
        and not rejected
        and prior.get("campaign_run_id", campaign_id) == campaign_id
    ):
        if prior.get("turn") != turn or "campaign_run_id" not in prior:
            prior = dict(prior)
            prior["turn"] = turn
            prior["campaign_run_id"] = campaign_id
            session["last_publication"] = prior
        _sync_exchange(session, visible)
        _sync_expression_audit(session, audit)
        return prior
    speech = bool(_SPOKEN.search(visible))
    candidate = str(audit.get("candidate") or "")
    adopted = (
        audit.get("decision") == "adopted"
        and audit.get("fallback_used") is not True
        and (not candidate or candidate in visible)
    )
    narration = session.get("last_narration") if isinstance(session.get("last_narration"), dict) else {}
    narration_candidate = str(narration.get("candidate") or "")
    narration_accepted = bool(
        not speech
        and narration.get("adopted")
        and narration_candidate
        and narration_candidate in visible
    )
    meta = resolution.get("metadata") if isinstance(resolution, dict) and isinstance(resolution.get("metadata"), dict) else {}
    engine_text = str(meta.get("engine_publication") or "").strip()
    contract = str(meta.get("publication_contract") or "") if engine_text == visible else ""
    if contract not in CONTRACTS:
        contract = FINAL_ENGINE_RESPONSE
    accepted = bool(adopted or narration_accepted)
    record = {
        "owner": "completed_runtime_response",
        "contract": contract,
        "final": True,
        "dialogue_generated": bool(speech or audit),
        "dialogue_accepted": bool(speech and adopted),
        "dialogue_composed": bool(speech),
        "dialogue_published": bool(speech),
        "narration_requested": bool(narration) and not speech,
        "narration_accepted": narration_accepted,
        "narration_published": narration_accepted,
        "visible": visible,
        "validation_outcome": "accepted_expression" if accepted else "engine_or_grounded_fallback",
        "fallback": not accepted,
        "expression_decision": str(audit.get("decision") or "none"),
        "turn": turn,
        "campaign_run_id": campaign_id,
    }
    session["last_publication"] = record
    _sync_exchange(session, visible)
    _sync_expression_audit(session, audit)
    return record


def _sync_exchange(session, visible: str) -> None:
    context = session.get("conversational_context")
    if not isinstance(context, dict):
        return
    exchange = context.get("last_gm_exchange")
    if isinstance(exchange, dict) and exchange.get("response") != visible[:1200]:
        exchange["response"] = visible[:1200]


def _sync_expression_audit(session, audit: dict) -> None:
    """Remember this turn's expression attempt. A missing audit leaves the prior attempt alone."""
    if not audit:
        return
    stored = dict(audit)
    stored["adopted"] = audit.get("decision") == "adopted" and audit.get("fallback_used") is not True
    session["last_background_expression"] = stored


def operational_refusal_reason(reason: str) -> bool:
    """True when admission, interpretation, or a recorded routing refusal stopped the turn."""
    return str(reason or "").strip() in OPERATIONAL_REFUSAL_REASONS


def _refusal_stage(reason: str) -> str:
    if reason in _ROUTING_REFUSALS:
        return "routing"
    if reason in _SERVICE_FAILURES:
        return "interpretation_service"
    return "provider_admission"


def classify_operational_refusal(reason: str, *, provider_request_sent: bool = False) -> dict | None:
    """Diagnostic fields for a player-visible operational refusal.

    These fields stay on the server resolution record. They are not a
    gameplay publication and they do not authorize a state change.
    """
    text = str(reason or "").strip()
    if text not in OPERATIONAL_REFUSAL_REASONS:
        return None
    return {
        "response_class": OPERATIONAL_REFUSAL,
        "failure_stage": _refusal_stage(text),
        "refusal_category": text,
        "provider_request_sent": bool(provider_request_sent),
        "gameplay_executed": False,
        "authoritative_state_changed": False,
        "gameplay_publication_completed": False,
        "player_visible_response_category": OPERATIONAL_REFUSAL,
        "recovery_eligible": True,
    }


def response_is_operational_refusal(result) -> bool:
    """Whether this chat/action payload must not be recorded as gameplay."""
    if not isinstance(result, dict):
        return False
    if gm_is_budget_refusal(result.get("gm_output")):
        return True
    resolution = result.get("resolution")
    if not isinstance(resolution, dict):
        return False
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    if meta.get("response_class") == OPERATIONAL_REFUSAL:
        return True
    if resolution.get("kind") != "interpretation_rejected":
        return False
    if meta.get("authoritative_mutation") is not False or meta.get("resolver_invoked") is not False:
        return False
    return operational_refusal_reason(str(meta.get("processing_outcome") or ""))


def record_completed_publication(response, *, source_handler: str, presentation_rows=(), provider_rows=(), publication_context=None, publication_contract=None, response_class=None):
    """Record the committed, player-projected response once at the HTTP boundary.

    An operational refusal is visible to the player and is not a completed
    gameplay publication. No publication event is written for it.

    Retries returning the ordered-turn cache never reach this boundary. Only
    visible text and hashes of actually published accepted expressions leave
    it; rejected provider prose and hidden resolver fields are excluded.
    HTTP 200 and visible text do not by themselves mean gameplay completed.
    """
    if response_class == OPERATIONAL_REFUSAL:
        return None
    import hashlib
    import json
    import os
    import uuid
    from pathlib import Path
    from game import storage

    status = getattr(response, 'status_code', 200)
    body = json.loads(response.body) if hasattr(response, 'body') else response
    if not isinstance(body, dict):
        return None
    gm = body.get('gm_output') or {}
    text = str(gm.get('player_facing_text') or body.get('error') or body.get('message') or '')
    if not text:
        return None
    def ref(value):
        return hashlib.sha256(value.encode('utf-8')).hexdigest()
    accepted = [r for r in presentation_rows if r.get('decision') == 'accepted'
                and r.get('text') and r['text'] in text]
    context = publication_context if isinstance(publication_context, dict) else {}
    if context.get('visible') == text and any(r.get('sent') is True for r in provider_rows):
        if context.get('dialogue_accepted') and context.get('dialogue_published'):
            if not any(r.get('kind') == 'dialogue' for r in accepted):
                accepted.append(dict(kind='dialogue', text=text))
        if context.get('narration_accepted') and context.get('narration_published'):
            if not any(r.get('kind') == 'narration' for r in accepted):
                accepted.append(dict(kind='narration', text=text))
    kinds = {r.get('kind') for r in accepted}
    category = ('error' if status >= 400 else 'mixed' if len(kinds) > 1 else
                'dialogue' if 'dialogue' in kinds else 'live_narration' if 'narration' in kinds else
                'clarification' if publication_contract == CLARIFICATION_REQUIRED else
                'unsupported_action' if publication_contract == UNSUPPORTED_ACTION else
                'failure' if publication_contract == FAILURE else
                'engine_response')
    row = dict(turn_id=uuid.uuid4().hex, publication_owner=context.get('owner') if context.get('visible') == text else 'completed_runtime_response',
               response_category=category, source_handler=source_handler,
               provider_involvement=bool(presentation_rows) or any(r.get('sent') is True for r in provider_rows),
               provider_attempt_references=[r['attempt_id'] for r in provider_rows if r.get('sent') is True and r.get('attempt_id')],
               accepted_expression_references=[ref(r['text']) for r in accepted],
               published_expression_reference=ref(text), final_player_facing_response=text,
               validation_outcome='accepted_expression' if accepted else 'engine_or_grounded_fallback',
               status_code=status)
    path = Path(os.environ.get('ASHEN_PUBLICATION_TRACE_PATH') or storage.DATA_DIR / 'publication_events.jsonl')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(row, ensure_ascii=False)+'\n')
    return row
# These already have the sentence the player should read.
SKIP_PRIMARY = frozenset({
    FINAL_ENGINE_RESPONSE,
    CLARIFICATION_REQUIRED,
    UNSUPPORTED_ACTION,
    FAILURE,
})
KNOWN_REPEAT_LINE = "The examination adds nothing new to what you already know."


def stamp(metadata: dict, contract: str, *, publication: str | None = None) -> dict:
    """Record the contract on an existing metadata dict. Does not publish."""
    if contract not in CONTRACTS:
        raise ValueError("unknown_publication_contract")
    metadata["publication_contract"] = contract
    if publication:
        metadata["engine_publication"] = publication
    metadata["skip_primary_narration"] = contract in SKIP_PRIMARY
    return metadata


def narration_skip(
    resolution: dict | None,
    *,
    scene=None,
    session=None,
) -> tuple[str, str] | None:
    """Return the sentence that replaces primary narration, or None to continue.

    Adjudication may take one bounded expression attempt. That attempt is not
    the primary narration prompt. A second call does not run.
    """
    if not isinstance(resolution, dict):
        return None
    meta = resolution.get("metadata")
    if not isinstance(meta, dict):
        meta = {}
    contract = str(meta.get("publication_contract") or "")
    published = str(meta.get("engine_publication") or "").strip()
    kind = str(resolution.get("kind") or "").strip().lower()
    if contract in SKIP_PRIMARY and published:
        return published, "publication_contract"
    if published and meta.get("skip_primary_narration") is True:
        return published, "committed_engine_publication"
    if contract == ADJUDICATION_RESULT and published:
        return _express_adjudication(meta, published, session=session, scene=scene)
    if contract == LIVE_EXPRESSION_REQUESTED and published and meta.get("bounded_expression_attempted"):
        return published, "live_expression_settled"
    if kind == "already_searched" or (
        kind in {"investigate", "observe"} and meta.get("action_outcome") == "valid_no_new_information"
    ):
        line = published or KNOWN_REPEAT_LINE
        return line, "final_engine_response"
    return None


def _express_adjudication(meta: dict, published: str, *, session, scene) -> tuple[str, str]:
    if meta.get("bounded_expression_attempted"):
        stamp(meta, FINAL_ENGINE_RESPONSE, publication=published)
        return published, "adjudication_result"
    meta["bounded_expression_attempted"] = True
    expressed = ""
    try:
        from game.integrated_play import maybe_narrate
        narrated = maybe_narrate(published, session=session, scene=scene)
        if isinstance(narrated, dict):
            expressed = str(narrated.get("text") or "").strip()
    except Exception:
        expressed = ""
    if expressed:
        stamp(meta, FINAL_ENGINE_RESPONSE, publication=expressed)
        meta["bounded_expression_attempted"] = True
        meta["live_expression_published"] = True
        return expressed, "bounded_live_expression"
    stamp(meta, FINAL_ENGINE_RESPONSE, publication=published)
    meta["bounded_expression_attempted"] = True
    meta["live_expression_published"] = False
    return published, "adjudication_result"


def summarize_provider_rows(rows: list[dict] | None) -> dict[str, int]:
    """Count completed provider calls once per attempt.

    Admitted and dispatch traces for the same attempt are not extra calls.
    A row that was not sent is not a completed request.
    """
    seen: set[str] = set()
    requests = 0
    incoming = 0
    outgoing = 0
    total = 0
    retries = 0
    rejected = 0
    fallbacks = 0
    for row in rows or []:
        if not isinstance(row, dict) or row.get("event") != "completed":
            continue
        attempt = str(row.get("attempt_id") or "")
        if attempt and attempt in seen:
            continue
        if attempt:
            seen.add(attempt)
        if row.get("sent") is not True:
            fallbacks += 1
            continue
        requests += 1
        incoming += int(row.get("input_tokens") or 0)
        outgoing += int(row.get("output_tokens") or 0)
        total += int(row.get("total_tokens") or 0)
        if int(row.get("retry_attempt") or 0) > 0:
            retries += 1
        if row.get("accepted") is False:
            rejected += int(row.get("total_tokens") or 0)
    return {
        "requests": requests,
        "input_tokens": incoming,
        "output_tokens": outgoing,
        "total_tokens": total,
        "retries": retries,
        "rejected_tokens": rejected,
        "fallbacks": fallbacks,
    }


def contract_name(value: Any) -> str:
    text = str(value or "")
    return text if text in CONTRACTS else ""
