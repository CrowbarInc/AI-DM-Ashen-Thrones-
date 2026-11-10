from pathlib import Path
p=Path('game/expressive_dialogue.py')
s=p.read_text()
a=s.index('            # Only this source projection licenses first-person offering verbs.')
b=s.index('        else:\n            reasons.extend(_faithful_reasons',a)
s=s[:a]+'''            reasons.extend(_offering_reasons(spoken, proposition, contract))
'''+s[b:]
pos=s.index('\ndef _characterization_reasons')
s=s[:pos]+'''
def _offering_reasons(spoken: str, proposition: str, contract: Mapping[str, Any]) -> list[str]:
    """Closed offering grammar, licensed only by the host's own_offerings relation.

    Compare whole item phrases (including adjectives), not a bag of words.
    Offering does not license ownership, gifts, prices or a sale commitment.
    """
    source = _plain(proposition).strip().rstrip(".").lower()
    speaker = re.escape(str(contract.get("speaker_name") or "").lower())
    match = re.fullmatch(rf"(?:i|(?:the )?{speaker}) (offer[s]?|sell[s]?|serve[s]?) (.+)", source)
    if not match:
        return ["offering_structure_unsupported"]
    verb, items = match.groups()
    sale = verb in {"sell", "sells"}

    def item_phrases(text: str) -> list[str]:
        parts = re.split(r"\\s+and\\s+|,\\s*", text)
        # Singular room is a grammatical service unit, not a stock quantity.
        return sorted("room" if part.strip() in {"rooms", "a room"} else part.strip()
                      for part in parts if part.strip())

    text = _plain(spoken).strip().rstrip(".!?").lower()
    text = re.sub(r"^well,?\\s+", "", text)
    # These are complete sentence frames. No globally ignored content words.
    prefix = r"(?:i offer(?: you)?|i can offer(?: you)?|i serve|i(?:'ve| have) got) "
    if sale:
        prefix = r"(?:i sell|i(?:'ve| have) got) "
    candidate = re.fullmatch(prefix + r"(.+)", text)
    if candidate:
        candidate_items = candidate.group(1)
        if sale:
            if text.startswith("i sell "):
                pass
            elif candidate_items.endswith(" for sale"):
                candidate_items = candidate_items[:-9]
            else:
                return ["offering_relation_changed"]
        elif candidate_items.endswith(" to share"):
            candidate_items = candidate_items[:-9]
    else:
        reverse = re.fullmatch(r"(.+?)[—–-]\\s*that's what i(?:'ve| have) got", text)
        if not reverse or sale:
            return ["unsupported_offering_expression"]
        candidate_items = reverse.group(1)
    if item_phrases(candidate_items) != item_phrases(items):
        return ["offering_items_changed"]
    if _norm(spoken) == _norm(proposition):
        return ["verbatim_repetition"]
    return []

'''+s[pos:]
s=s.replace('For your own offerings, offer/sell/serve/I\'ve got are also allowed. Keep every item description.', "For your own offerings, use I offer, I can offer you, I serve, or I've got. "
            "You may start with Well or end with to share, and reorder whole items. "
            "Use for sale only if the authority explicitly says sell. Keep every item description.")
p.write_text(s)
p=Path('tools/playtest/gameplay.py'); s=p.read_text(); pos=s.index('\ndef classify_turn')
s=s[:pos]+'''
def can_start_interaction(usage, request_limit):
    """Reserve interpretation plus optional expression before starting a turn."""
    return (not usage.get('stopped')
            and request_limit - usage.get('dispatched_requests', 0) >= 2)


def expression_outcome(gm):
    """Evaluate delivered wording against native authority, never candidate adoption alone."""
    from game.expressive_dialogue import validate_expression, spoken_text, _norm
    metadata = gm.get('metadata') or {}
    audit = metadata.get('expression_generation') or {}
    accepted = metadata.get('accepted_response') or {}
    decision = audit.get('decision') or accepted.get('expression_decision')
    if decision not in {'adopted', 'rejected'}:
        return 'EXPRESSION_NOT_INVOKED', []
    contract = audit.get('contract') or {}
    text = str(gm.get('player_facing_text') or '')
    reasons = []
    if not text.strip():
        reasons.append('unrecoverable_expression_failure')
    elif contract:
        spoken = spoken_text(text, str(contract.get('speaker_name') or ''))
        props = contract.get('authorized_propositions') or []
        # Exact canonical answer is a valid fallback, although expression
        # adoption deliberately rejects verbatim repetition.
        exact = len(props) == 1 and _norm(spoken) == _norm(props[0])
        validation = validate_expression(spoken, contract)
        if not exact and not validation['adopt']:
            reasons.append('published_expression_not_authorized')
    elif decision == 'rejected':
        # Player projection may omit the full audit. Require native authority
        # and validation evidence instead of inferring recovery from text alone.
        proposition = str(accepted.get('authorized_proposition') or '')
        spoken = spoken_text(text, '')
        if (not proposition or _norm(spoken) != _norm(proposition)
                or (accepted.get('hard_validation') or {}).get('hard_valid') is not True):
            reasons.append('expression_recovery_unverified')
    return ('EXPRESSION_ACCEPTED' if decision == 'adopted' else
            'EXPRESSION_REJECTED_UNRECOVERED' if reasons else
            'EXPRESSION_REJECTED_RECOVERED'), reasons

'''+s[pos:]
s=s.replace('    reasons = []\n    if status != 200:', "    expression_status, expression_reasons = expression_outcome(gm)\n    reasons = list(expression_reasons)\n    if status != 200:")
s=s.replace("return {'transport_completed': status == 200,", "return {'expression_status': expression_status, 'transport_completed': status == 200,")
p.write_text(s)
p=Path('tools/playtest/runner.py'); s=p.read_text().replace('from tools.playtest.gameplay import execute_turn, prerequisite_failure','from tools.playtest.gameplay import execute_turn, prerequisite_failure, can_start_interaction').replace("if current_usage.get('dispatched_requests', 0) >= int(env['ASHEN_PROVIDER_REQUEST_LIMIT']):", "if not can_start_interaction(current_usage, int(env['ASHEN_PROVIDER_REQUEST_LIMIT'])):")
p.write_text(s)
