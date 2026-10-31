"""Offline evidence helpers for PR-PLAY-06. No tokenizer downloads or provider calls."""
import json
import math
from pathlib import Path


def size(text):
    return {"characters": len(text), "utf8_bytes": len(text.encode()),
            "estimated_tokens_chars_div_4": math.ceil(len(text) / 4),
            "tokenization": "estimate only; model-compatible tokenizer unavailable"}


def write(name, value):
    path = Path('artifacts/pr_play_06') / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def opening_fixture(name, payload):
    from tests.test_pr_play_04_opening_integrity import VALID_NARRATION, MARKET_NARRATION
    from tests.test_start_campaign_api import CONTRACT_OPENING_GPT_RESPONSE, RICH_OPENING_GPT_RESPONSE
    narration = {'minimal': MARKET_NARRATION, 'typical': CONTRACT_OPENING_GPT_RESPONSE['player_facing_text'],
                 'rich': VALID_NARRATION,
                 'multiple_details': VALID_NARRATION, 'npc': VALID_NARRATION,
                 'declarations': VALID_NARRATION, 'over_600': VALID_NARRATION}[name]
    claims = (payload.get('gm_resolution_decision') or {}).get('realization_claims') or []
    # Reuse the declaration projection from test_start_campaign_api._structured_opening_fixture.
    declarations = [{'declaration_mode': 'realize', 'source_claim_id': c['claim_id'],
                     'text': c['text'], 'relation_kind': c.get('relation_kind', 'observation')}
                    for c in claims if c.get('text') and c['text'] in narration]
    envelope = {'declared_claims': declarations, 'narration': narration}
    if name in {'rich', 'over_600'}:
        from tests.test_pr_br_structured_realization_envelope import _decl
        envelope['declared_claims'] = [_decl(d['text'], source_claim_id=d['source_claim_id'],
                                           relation=d['relation_kind']) for d in declarations]
    return json.dumps(envelope)


def measure(name, text):
    from game.gm import _safe_json
    value = json.loads(text)
    parsed = _safe_json(text, require_structured_claims=True)
    narration = value['narration']
    declarations = json.dumps(value['declared_claims'])
    return {'name': name, 'serialized_output': size(text), 'narration': size(narration),
            'declarations': size(declarations),
            'structural_characters_including_escaping_whitespace': len(text)-len(narration)-len(declarations),
            'parser_valid': not parsed.get('metadata', {}).get('structured_contract_failure', False),
            'declaration_count': len(value['declared_claims'])}
