"""Development controls; deliberately separate from the frozen holdout."""
from tests.test_pr_play_57_integrated_narration import ROUTE, hook

PRINTS = ('Faint overlapping prints mark the mud around the old milestone, '
          'but their number, origin, and direction stay unclear.')


def cases():
    rows = []
    def add(group, texts, **kwargs):
        for text in texts:
            rows.append({'id':f'D{len(rows)+1:02}', 'group':group,
                         'expected':'PASS' if group=='legitimate' else 'REVIEW_REQUIRED' if group in ('missing','ambiguous') else 'FAIL',
                         'hook':hook(**kwargs), 'text':text})
    add('legitimate', [ROUTE,
        'Past the crates, the missing patrol was last seen heading along the northwest muddy path.',
        'The missing patrol was last spotted following the northwest mud trail past the crates.',
        'The notices place the missing patrol on the northwest mud track, past the crates.',
        'Wind stirs the paper. '+ROUTE])
    add('legitimate', [PRINTS,
        'Faint overlapping footprints mark the mud around the weathered milestone. Their number, source and direction remain uncertain.',
        'Faint overlapping prints mark the mud around the old milestone, but you cannot determine how many people left them, where they came from or which way they went.',
        'Faint overlapping prints mark the mud around the old milestone, but their number, origin and direction remain ambiguous.',
        'Faint overlapping prints mark the mud around the old milestone, but their number, origin and direction remain unresolved.',
        'Faint overlapping prints mark the mud around the old milestone, but there is no evidence of their number, origin or direction.'], clues=[PRINTS])
    add('legitimate', ['You inspect it again, but find nothing further. '+ROUTE,
        'You recall the earlier examination; no fresh clues emerge. '+ROUTE],
        kind='already_searched', success=False, clues=[], known=[ROUTE])
    add('legitimate', ['Your examination yields no additional information.',
        'You learn nothing new from your failed investigation.'], clues=[], success=False)
    add('missing', ['The board creaks.', 'The missing patrol was last seen taking the northwest mud track.',
        'The missing patrol was last seen past the crates.', 'Northwest mud track, crates, missing patrol.'])
    add('missing', ['Faint overlapping prints mark the mud around the old milestone.',
        'Faint overlapping prints mark the mud around the old milestone, but their number is unknown.'], clues=[PRINTS])
    add('contradictory', [ROUTE.replace('northwest','southwest'), ROUTE.replace('patrol','merchant'),
        ROUTE.replace('past the crates','before the crates'), ROUTE.replace('was last seen','will be seen'),
        ROUTE.replace('was last seen','was not last seen'), 'Your investigation fails.'])
    add('contradictory', ['The prints lead north.', 'Three people left the prints heading east.'], clues=[PRINTS])
    add('contradictory', [
        PRINTS+' Their direction is known.',
        'Faint overlapping prints mark the mud around the old milestone, but their number and origin are unknown; their direction is clear.',
        ROUTE+' The missing patrol was last seen taking the southeast mud track past the crates.',
    ], clues=[PRINTS])
    add('expansion', [ROUTE+' The patrol was ambushed by smugglers.',
        ROUTE+' You find a hidden map beneath the board.', ROUTE+' You acquire a silver key.',
        ROUTE+' The captain knows the secret destination.', ROUTE+' You gain 10 gold coins.',
        ROUTE+' A secret tunnel runs beneath the gate.', ROUTE+' Your quest is complete.',
        ROUTE+' You are poisoned.'])
    add('expansion', ['You discover the route for the first time. '+ROUTE],
        kind='already_searched', success=False, clues=[], known=[ROUTE])
    add('ambiguous', ['Perhaps '+ROUTE[0].lower()+ROUTE[1:],
        'The missing patrol might have followed the northwest mud track past the crates.'])
    return rows
