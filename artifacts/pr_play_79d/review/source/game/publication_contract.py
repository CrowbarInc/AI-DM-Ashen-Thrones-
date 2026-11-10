"""Whether a resolved turn still needs primary narration.

Nonempty text is not completeness. The contract names the owner of the
player-facing sentence. Primary narration is the large turn prompt. A
committed physical change can still take one bounded expression pass.
"""
from __future__ import annotations

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


def record_completed_publication(response, *, source_handler: str, presentation_rows=(), provider_rows=(), publication_context=None, publication_contract=None):
    """Record the committed, player-projected response once at the HTTP boundary.

    Retries returning the ordered-turn cache never reach this boundary. Only
    visible text and hashes of actually published accepted expressions leave
    it; rejected provider prose and hidden resolver fields are excluded.
    """
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
