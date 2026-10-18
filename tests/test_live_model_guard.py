"""The deterministic suite must fail before a live model client can wait on the network."""
from __future__ import annotations

import pytest

from tests.helpers.live_model_guard import LiveModelCallForbidden


def test_openai_constructor_fails_closed():
    import openai

    with pytest.raises(LiveModelCallForbidden) as caught:
        openai.OpenAI(api_key="not-a-live-call")
    message = str(caught.value)
    assert "openai.OpenAI" in message
    assert "site:" in message


def test_default_call_gpt_wrapper_fails_closed():
    from game import gm

    with pytest.raises(LiveModelCallForbidden) as caught:
        gm.call_gpt([{"role": "user", "content": "ping"}])
    assert "game.gm.call_gpt" in str(caught.value)
