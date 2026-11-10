"""Bounded player knowledge selected by a completed resolver, never a clue catalog.

Narration is allowed to paraphrase. When delivery cannot be established locally,
retain its prose and supplement it with the selected source text before validation.
This is deliberately conservative rather than a semantic-equivalence oracle.
"""
from __future__ import annotations

import re
from typing import Any, Mapping


def revealed_information(resolution: Mapping[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(resolution, Mapping) or resolution.get('success') is not True:
        return []
    changes = resolution.get('state_changes') or {}
    if isinstance(changes, Mapping) and changes.get('already_searched'):
        return []
    if resolution.get('kind') not in {'discover_clue', 'investigate', 'observe'}:
        return []
    texts = resolution.get('discovered_clues')
    selected = [text.strip() for text in texts if isinstance(text, str) and text.strip()] if isinstance(texts, list) else []
    text = resolution.get('clue_text')
    if isinstance(text, str) and text.strip():
        selected.insert(0, text.strip())
    return [dict(text=text, source='resolved_action', status='newly_revealed') for text in dict.fromkeys(selected)]


def supplement_revealed_information(text: str, resolution: Mapping[str, Any] | None) -> tuple[str, list[dict[str, str]]]:
    """Do not reject paraphrases; add a source confirmation if coverage is uncertain."""
    def normalized(value: str) -> str:
        return ' '.join(re.findall(r'\w+', value.casefold()))

    current = str(text or '').strip()
    added = []
    for item in revealed_information(resolution):
        if normalized(item['text']) not in normalized(current):
            current = f"{current} {item['text']}".strip()
            added.append(item)
    return current, added
