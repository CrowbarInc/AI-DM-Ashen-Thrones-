from pathlib import Path
import json
# Development-stage script; final reviewable changes are in source_diffs.
if 'def broad_topic_discovery_category(' in Path('game/social.py').read_text(encoding='utf-8'):
    raise SystemExit('Repair already applied; use final source diffs for review.')
p=Path('game/social.py');s=p.read_text(encoding='utf-8')
anchor='def authored_topic_relevant_to_question('
addition='''def broad_topic_discovery_category(player_text: str) -> str | None:
    """Recognize bounded category asks, preserving specific subjects and ellipsis."""
    text = " ".join(str(player_text or "").lower().replace("’", "'").split()).rstrip("?!. ")
    if re.fullmatch(
        r"(?:what (?:sort of |kind of )?rumou?rs (?:have you heard|do you know)|"
        r"have you heard (?:any )?rumou?rs|(?:heard )?any rumou?rs|"
        r"what(?:'s| is) the latest gossip|(?:any |what )gossip)", text
    ):
        return "rumor"
    return None


def topic_discoverable_in_category(npc: Dict[str, Any], rec: Any, category: str) -> bool:
    """Discovery is explicit opt-in and never overrides source disclosure policy."""
    from game.dialogue_authority import npc_source_permitted
    if not isinstance(rec, dict):
        return False
    categories = rec.get("discovery_categories")
    return (isinstance(categories, list) and category in categories
            and npc_source_permitted(npc, rec))


'''
s=s.replace(anchor,addition+anchor)
s=s.replace('    speaker_tokens = _speaker_tokens_for_question_relevance(npc, speaker_id, speaker_name)\n    subject =', '    category = broad_topic_discovery_category(player_text)\n    if category:\n        return topic_discoverable_in_category(npc or {}, rec, category)\n    speaker_tokens = _speaker_tokens_for_question_relevance(npc, speaker_id, speaker_name)\n    subject =',1)
s=s.replace('    candidates = []\n    for t in topics:', '    category = broad_topic_discovery_category(text_in)\n    candidates = []\n    for t in topics:',1)
s=s.replace('        score = len(words & reference_subject_tokens(_authored_topic_hay(rec)))','        score = 0 if category else len(words & reference_subject_tokens(_authored_topic_hay(rec)))',1)
s=s.replace('    best = max(score for score, _ in candidates)','    if category:\n        candidates.sort(key=lambda item: item[1]["id"])\n    best = max(score for score, _ in candidates)',1)
p.write_text(s,encoding='utf-8')
p=Path('tools/playtest/overlays.py');s=p.read_text(encoding='utf-8').replace('def compare_overlays(before, after, *, accepted=False, opening_response=None):','def compare_overlays(before, after, *, accepted=False, opening_response=None, ordinary_action=None, turn_response=None):')
s=s.replace("    elif not accepted:\n        reason = 'opening_not_accepted_or_ordinary_turn_authority_unavailable'", "    elif not accepted:\n        reason = 'opening_not_accepted_or_ordinary_turn_authority_unavailable'\n        if ordinary_action is not None and turn_response is not None:\n            from tools.playtest.social_overlay_authority import social_overlay_projection\n            projection = social_overlay_projection(before, after, ordinary_action, turn_response)\n            if projection is not None:\n                expected, receipt = projection\n                proven, reason = True, 'authored_social_clue_projection'")
s=s.replace("'authored_scene': 'scenes/'+str(sid)+'.json'} if allowed else None", "'authored_scene': 'scenes/'+str(sid)+'.json',\n                                               'ordinary_turn': receipt if receipt and receipt.get('action_id') else None} if allowed else None")
s=s.replace('Only an exact accepted-opening projection of already authored public facts is\nrecognized here. Other mutations remain explicit stop conditions.','Exact accepted-opening and persisted authored-social projections are recognized.\nOther mutations remain explicit stop conditions.')
p.write_text(s,encoding='utf-8')
p=Path('tools/playtest/gameplay.py');s=p.read_text(encoding='utf-8').replace('overlays = compare_overlays(before, after)','overlays = compare_overlays(before, after, ordinary_action=action, turn_response=body)');p.write_text(s,encoding='utf-8')
p=Path('data/world.json');raw=p.read_text(encoding='utf-8');needle='"id": "patrol_rumor",';assert raw.count(needle)==1;raw=raw.replace(needle,needle+'\n          "discovery_categories": ["rumor"],');p.write_text(raw,encoding='utf-8')

p=Path('data/validation/atgb/baselines/frontier-gate-v1/world.json');raw=p.read_text(encoding='utf-8');needle='"id": "patrol_rumor",';assert raw.count(needle)==1;raw=raw.replace(needle,needle+'\n          "discovery_categories": ["rumor"],');p.write_text(raw,encoding='utf-8')
