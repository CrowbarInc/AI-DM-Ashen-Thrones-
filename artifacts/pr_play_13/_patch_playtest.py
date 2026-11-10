from pathlib import Path

worker = Path("tools/playtest/worker.py")
text = worker.read_text(encoding="utf-8")
old = """    from game import api, gm, provider_budget as budget
    from game.config import get_openai_api_key, DEFAULT_MODEL_NAME"""
new = """    from game import api, gm, provider_budget as budget
    from game.config import get_openai_api_key, DEFAULT_MODEL_NAME
    from game.opening_presentation_renderer import opening_renderer_diagnostics"""
if old not in text:
    raise SystemExit("worker import missing")
text = text.replace(old, new, 1)
old = """          'model': DEFAULT_MODEL_NAME, 'opening_output_allowance': gm._opening_max_output_tokens(),
          'limits': budget.limits(), 'sdk_retries': 0, 'host_retries': 0,"""
new = """          'model': DEFAULT_MODEL_NAME, 'opening_output_allowance': gm._opening_max_output_tokens(),
          'opening_renderer': opening_renderer_diagnostics(),
          'limits': budget.limits(), 'sdk_retries': 0, 'host_retries': 0,"""
if old not in text:
    raise SystemExit("worker pattern missing")
replacement = text.replace(old, new, 1)
temp = worker.with_suffix(".py.tmp")
with temp.open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(replacement)
temp.replace(worker)

runner = Path("tools/playtest/runner.py")
text = runner.read_text(encoding="utf-8")
old = """            'live_authorization': authorize_live and mode == 'Live', 'retry_configuration': 'SDK=0, host=0',
            'response_capture_opt_in': capture_response}"""
new = """            'live_authorization': authorize_live and mode == 'Live', 'retry_configuration': 'SDK=0, host=0',
            'response_capture_opt_in': capture_response,
            'opening_renderer': cfg['opening_renderer']}"""
if old not in text:
    raise SystemExit("runner pattern missing")
replacement = text.replace(old, new, 1)
temp = runner.with_suffix(".py.tmp")
with temp.open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(replacement)
temp.replace(runner)
print("patched")
