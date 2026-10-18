"""Run a matched R1-R1 regression using the preserved pre-edit planning module."""
import importlib.util, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('game.unified_semantic_planning',ROOT/'artifacts/pr_eg_r6_r2/baseline_sources/game/unified_semantic_planning.py')
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
import game
setattr(game,'unified_semantic_planning',mod)
import pytest
files=['test_pr_eg_r2c_speech_adoption.py','test_pr_eg_r2c_r2_reference_eligibility.py','test_pr_eg_r3_expressive_dialogue.py','test_pr_eg_r3_r1_expression_semantics.py','test_pr_eg_r4_r1_delivery_integrity.py','test_pr_eg_r6_unified_semantic_planning.py','test_pr_eg_r6_r1_disclosure_boundary.py','test_pr_eg_r6_r1_r1_provenance.py','test_social_question_relevance_answer_selection.py']
sys.exit(pytest.main(['tests/'+f for f in files]+['-vv','-o','faulthandler_timeout=45','--basetemp=development/tmp/r6r2_baseline','--junitxml=artifacts/pr_eg_r6_r2/baseline_junit.xml']))
