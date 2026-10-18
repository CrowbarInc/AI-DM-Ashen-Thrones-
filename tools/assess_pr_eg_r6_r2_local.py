"""Explicit local transcript assessments; no network or external model calls.

Indices identify exact preserved rows. Judgments are the implementing agent's
review, not independent human scoring. Raw evidence and old fixture labels remain.
"""
import json
from pathlib import Path
OUT=Path('artifacts/pr_eg_r6_r2')
METRICS=['intent','addressee','entity_roles','relationship','relevance','sufficiency','correction','follow_up','recovery','clarification','false_clarification']

def numbers(s):return set(int(x) for x in s.split())
corrections=numbers('2 12 18 25 28 36 42 53 68 75 85 94')
followups=numbers('3 5 9 13 19 20 24 26 29 35 37 49 51 54 56 57 67 71 72 78 84 88 105')
# Full local reading identified these responses as nonanswers/false clarifications.
bad_answer=numbers('2 3 5 9 10 12 13 18 19 20 21 23 24 25 26 28 29 31 35 36 37 40 42 46 48 49 50 51 53 54 56 58 65 67 68 75 78 80 81 84 85 94 105 107 119')
bad_relationship=numbers('3 5 9 13 14 19 20 21 23 24 26 29 35 37 40 41 42 45 46 49 51 54 56 57 58 61 65 67 68 71 72 78 80 81 84 85 86 88 91 94 105 107')
bad_roles=numbers('0 6 14 15 23 41 45 46 52 55 58 59 60 61 62 63 64 79 86 91 93 106')
genuine_clarification=numbers('6 39 62 79 106')
unclear_answer=numbers('57 71 72 88')
padding=set(range(95,104))|set(range(110,119))


def main():
    rows=[json.loads(l) for l in (OUT/'live_turns.jsonl').read_text().splitlines()]
    scores=[]
    for i,r in enumerate(rows):
        p=r['plan'];act=p.get('conversational_act');is_correction=i in corrections;is_follow=i in followups
        missing=not p
        delivered_clarification=p.get('response_kind')=='clarification' or i in {10,39}
        correct_address=bool(p.get('addressee_id')) or i in genuine_clarification or i==43
        if i in {10,25,54,80}:correct_address=False
        relevant=i not in bad_answer
        sufficient=relevant and i not in {45}
        relationship=i not in bad_relationship and not missing
        role_ok=correct_address and relationship and i not in bad_roles
        intent=(act=='correction' if is_correction else act=='follow_up' if is_follow else act=='information_question')
        if i in {7,33,38,43}:intent=None;relationship=None;role_ok=None
        if i==10:intent=False;relationship=None;role_ok=False
        if i==39:intent=None;relationship=None;role_ok=None
        reason=('Incorrect continuity/target or false clarification; inspect the stored plan and delivered line.' if i in corrections|followups and not relevant else
                'Known eligible answer or narrow clarification missed.' if not relevant else
                'Safe relevant uncertainty/authorized answer; proposition or role interpretation remains imperfect.' if not relationship or not role_ok else
                'Observed answer/uncertainty fits this request and the supplied sources.')
        quality=0 if i in {10,25,80} else 1 if not relevant or i in unclear_answer else 2
        scores.append({'index':i,'dataset':'pr_eg_r6_r2','intent':intent,'addressee':correct_address,'entity_roles':role_ok,'relationship':relationship,
            'relevance':relevant,'sufficiency':sufficient,'correction':bool(intent and relevant and role_ok) if is_correction else None,
            'follow_up':bool(intent and relevant and role_ok) if is_follow else None,'recovery':bool(intent and relevant and role_ok) if is_correction else None,
            'clarification':i in genuine_clarification if delivered_clarification or i in {21,40,107} else None,
            'false_clarification':delivered_clarification and i not in genuine_clarification,'quality':quality,'playability':quality,
            'reason':reason,'repeated_padding_fixture':i in padding})
    # These matched judgments are sequence-level observations, not causal claims.
    for mode in ['legacy','r6','r2']:
        rs=[json.loads(l) for l in (OUT/('matched_'+mode)/'live_turns.jsonl').read_text().splitlines()]
        good={'legacy':{0,1,3,7,9},'r6':{5,6,7,8,9},'r2':{0,1,3,7,8,9}}[mode]
        addr_bad={'legacy':set(),'r6':{0},'r2':{2,4,5,6}}[mode]
        for i,r in enumerate(rs):
            item={m:None for m in METRICS};item.update(index=i,dataset='matched_'+mode,
               addressee=i not in addr_bad,relevance=i in good,sufficiency=i in good,
               correction=(i in good) if i in {4,5} else None,follow_up=(i in good) if i==6 else None,
               recovery=(i in good) if i in {4,5} else None,quality=2 if i in good else 1,playability=2 if i in good else 1,
               reason='Local matched transcript assessment; later histories differ across modes.')
            scores.append(item)
    (OUT/'judge_scores.json').write_text(json.dumps(scores,indent=2))
    (OUT/'judge_usage.json').write_text('[]')
    (OUT/'local_assessment_method.json').write_text(json.dumps({'assessor':'implementing agent, local transcript review','independent':False,'external_scoring_calls':0,
      'denominator':'122 observed final-code turns. 18 repeated padding fixtures are separately flagged. Null means outside scope or insufficient evidence.',
      'limitations':'Subjective local judgments are not an independent qualification; inspect raw rows and exact index annotations. Correct safe uncertainty is not credited when an eligible answer is present.',
      'all_fields':'Intent/role/relationship estimates assess semantic meaning. Source sufficiency stricter than several inherited fixture labels. Scores never used for implementation tuning.'},indent=2))

if __name__=='__main__':main()
