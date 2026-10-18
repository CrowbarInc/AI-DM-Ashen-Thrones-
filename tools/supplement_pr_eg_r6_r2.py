"""Three additional final-code turns to exceed the 120-turn minimum.

The frozen primary plan totals 119 turns because its first new-holdout group
contains 14 rather than 15. This explicit supplement is not a replacement for
any failed primary turn and does not alter the frozen corpora.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import qualify_pr_eg_r6_r2 as runner
runner.OUT=ROOT/'artifacts/pr_eg_r6_r2/supplement'

def specs():
    from tools.qualify_pr_eg_r6 import HARBOR_DIRECT
    return [{'id':'supplement_harbor','npcs':HARBOR_DIRECT,'source':'supplemental_final_code','turns':[
       ('Keeper Nara, what is the harbor bell called?',{'addressee':'keeper_nara','sufficiency':'direct'}),
       ('Clerk Oren, who manages the ferry schedules?',{'addressee':'clerk_oren','sufficiency':'unknown'}),
       ('Keeper Nara, who forged the bell?',{'addressee':'keeper_nara','sufficiency':'unknown'})]}]
runner.specifications=specs
runner.main()
