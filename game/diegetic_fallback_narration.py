"""Diegetic fallback lines for retry / momentum / visibility paths.

Templates are written to avoid patterns flagged by ``player_facing_narration_purity``
(scaffold headers, coaching, UI labels, meta transition bridges). This module does not
validate or repair text — the final emission gate remains authoritative.
"""
from __future__ import annotations

import re
from typing import Dict, List, Mapping


def _stable_u32(seed: str) -> int:
    acc = 2166136261
    for ch in str(seed or ""):
        acc = (acc ^ ord(ch)) * 16777619
        acc &= 0xFFFFFFFF
    return int(acc)


def _clean_detail(text: str, *, max_len: int = 140) -> str:
    detail = " ".join(str(text or "").strip().split()).rstrip(".")
    if len(detail) <= max_len:
        return detail
    return detail[: max_len - 3].rstrip(" ,;:") + "..."


def _inner_scene(scene_or_envelope: Mapping[str, Any] | None) -> Dict[str, Any]:
    if not isinstance(scene_or_envelope, Mapping):
        return {}
    raw = scene_or_envelope.get("scene")
    if isinstance(raw, dict):
        return raw
    return dict(scene_or_envelope)  # type: ignore[arg-type]


def _visible_fact_strings(scene: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(scene, Mapping):
        return []
    vf = scene.get("visible_facts")
    if not isinstance(vf, list):
        return []
    out: List[str] = []
    for item in vf:
        if isinstance(item, str) and item.strip():
            out.append(_clean_detail(item.strip()))
    return out


def _first_summary_sentence(scene: Mapping[str, Any] | None) -> str:
    if not isinstance(scene, Mapping):
        return ""
    summary = str(scene.get("summary") or "").strip()
    if not summary:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", summary)
    first = parts[0].strip() if parts else ""
    return _clean_detail(first, max_len=320) if first else ""


def _humanize_scene_slug(sid: str) -> str:
    s = str(sid or "").strip().replace("_", " ").replace("-", " ")
    return " ".join(s.split()).strip().lower()


def _looks_like_complete_sentence(fact: str) -> bool:
    s = str(fact or "").strip()
    return bool(s) and s[-1] in ".!?"


def _exit_thoroughfare_hint(ex: Mapping[str, Any] | None) -> str:
    if not isinstance(ex, Mapping):
        return ""
    tid = str(ex.get("target_scene_id") or ex.get("targetSceneId") or "").strip()
    if tid:
        return _humanize_scene_slug(tid)
    lab = str(ex.get("label") or "").strip()
    return _clean_detail(lab, max_len=80) if lab else ""


def render_observe_perception_fallback_line(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
) -> str | None:
    """Concrete observation from visible facts (no coaching / menus)."""
    scene = _inner_scene(scene_or_envelope)
    facts = _visible_fact_strings(scene)
    if not facts:
        frag = _first_summary_sentence(scene)
        if not frag:
            return None
        idx = _stable_u32(f"obs|sum|{seed_key}") % 2
        if idx == 0:
            return f"You take in the scene: {frag}."
        return f"What surrounds you resolves into focus—{frag.lower()}."

    n = len(facts)
    i = _stable_u32(f"obs|{seed_key}") % n
    lead = facts[i]
    lead_cap = lead[0].upper() + lead[1:] if lead else lead
    mode = _stable_u32(f"obs|m|{seed_key}") % 3
    if n >= 2:
        j = (i + 1 + (_stable_u32(f"obs|j|{seed_key}") % (n - 1))) % n
        if j == i:
            j = (i + 1) % n
        second = facts[j]
        if _looks_like_complete_sentence(lead) and _looks_like_complete_sentence(second):
            if mode == 0:
                return f"You widen the sweep: {lead} {second}".strip()
            if mode == 1:
                return f"Two details keep trading priority: {lead} {second}".strip()
            return f"{lead} {second}".strip()
        if mode == 0:
            return f"{lead_cap} sharpens when you look again, and {second.lower()} still competes for notice."
        if mode == 1:
            return f"On a slower pass, {lead.lower()} reads clearer while {second.lower()} keeps pulling the eye."
        return f"{lead_cap} holds; beside it, {second.lower()} stays impossible to ignore."
    if _looks_like_complete_sentence(lead):
        if mode == 0:
            return f"You take another pass at the scene; {lead[0].lower()}{lead[1:]}"
        if mode == 1:
            return lead_cap if lead_cap.endswith((".", "!", "?")) else f"{lead_cap}."
        return f"The same impression returns, unchanged: {lead[0].lower()}{lead[1:]}"
    if mode == 0:
        return f"{lead_cap} stands out more sharply on a second pass."
    if mode == 1:
        return f"{lead_cap} reads a little finer when you let the noise thin."
    return f"Your attention settles again on {lead.lower()}."


def render_travel_arrival_fallback_line(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
) -> str | None:
    """Short arrival line from destination scene summary / facts (current envelope only)."""
    scene = _inner_scene(scene_or_envelope)
    summary = _first_summary_sentence(scene)
    facts = _visible_fact_strings(scene)
    loc = str(scene.get("location") or "").strip()

    idx = _stable_u32(f"arr|{seed_key}") % 3
    if summary:
        summ_low = summary[0].lower() + summary[1:] if len(summary) > 1 else summary.lower()
        if idx == 0:
            prefix = f"You arrive{f' in {loc}' if loc else ''} as "
            return f"{prefix}{summ_low}".strip()
        if idx == 1:
            return f"You step through{f' into {loc}' if loc else ''}, and {summ_low}".strip()
        return f"The new ground shows itself: {summ_low}".strip()

    if facts:
        f0 = facts[_stable_u32(f"arr|f|{seed_key}") % len(facts)]
        lead = f0[0].upper() + f0[1:] if f0 else f0
        if idx == 0:
            return f"You arrive{f' in {loc}' if loc else ''} where {f0.lower()}.".strip()
        return f"{lead} is the first thing that defines the space{f' here in {loc}' if loc else ''}.".strip()

    if loc:
        return f"You arrive in {loc}, the air and noise different enough to mark the change."

    return None


def render_scene_momentum_diegetic_append(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
) -> str:
    """One diegetic momentum beat: pressure without scaffold headers or option menus."""
    scene = _inner_scene(scene_or_envelope)
    loc = str(scene.get("location") or "").strip()
    facts = _visible_fact_strings(scene)
    exits = scene.get("exits") if isinstance(scene.get("exits"), list) else []
    exit_hints: List[str] = []
    for ex in exits:
        if isinstance(ex, dict):
            hint = _exit_thoroughfare_hint(ex)
            if hint and hint not in exit_hints:
                exit_hints.append(hint)
    loc_bit = f" in {loc}" if loc else ""

    low_blob = " ".join(f.lower() for f in facts)
    notice = "notice board" in low_blob or "noticeboard" in low_blob
    runner = "tavern runner" in low_blob or ("tavern" in low_blob and "runner" in low_blob)
    patrol = "missing patrol" in low_blob or "patrol" in low_blob

    seed = _stable_u32(f"mom|{seed_key}")

    if notice and patrol:
        opts = (
            f"Fresh worry tracks along the posted lines{loc_bit}; the missing patrol notice keeps drawing eyes.",
            f"Someone jabs at the board{loc_bit}, impatient with anyone who reads too long.",
        )
        return opts[seed % len(opts)]

    if notice:
        opts2 = (
            f"The notice board{loc_bit} collects another crowd—posted lines matter more than courtesy today.",
            f"Taxes and curfew lines{loc_bit} get read aloud by someone who wants witnesses.",
        )
        return opts2[seed % len(opts2)]

    if runner:
        opts3 = (
            f"The tavern runner's shout cuts through rain{loc_bit}, stew steam and rumor braided together.",
            f"A runner shouldering a cauldron{loc_bit} trades glances with the gate line—business and tension both.",
        )
        return opts3[seed % len(opts3)]

    if len(facts) >= 2:
        i = seed % len(facts)
        j = (i + 1 + (seed // 7) % (len(facts) - 1 or 1)) % len(facts)
        if j == i:
            j = (i + 1) % len(facts)
        a, b = facts[i], facts[j]
        if _looks_like_complete_sentence(a) and _looks_like_complete_sentence(b):
            return f"Tension keeps threading through the crowd{loc_bit}: {a} {b}".strip()
        a_cap = a[0].upper() + a[1:] if a else a
        return f"{a_cap} tightens{loc_bit}; {b.lower()} doesn't let the moment go slack."

    if facts:
        f0 = facts[seed % len(facts)]
        if _looks_like_complete_sentence(f0):
            return f"The moment won't idle{loc_bit}: {f0}".strip()
        lead = f0[0].upper() + f0[1:] if f0 else f0
        tail = (
            f"Pressure gathers{loc_bit} without anyone naming it.",
            f"The noise doesn't soften{loc_bit}; it searches for a fault line.",
            f"Someone nearer the press mutters{loc_bit}, and the mood answers.",
        )
        return f"{lead} {tail[seed % len(tail)]}"

    if exit_hints:
        dest = exit_hints[seed % len(exit_hints)]
        return f"Foot traffic still shoulders toward {dest}{loc_bit}, and the crowd won't pretend patience."

    if loc:
        return f"The press of bodies{loc_bit} finds another impatient rhythm—something is about to give."

    return "The crowd's tempo tightens; the next sound will carry weight."


def render_nonsocial_terminal_anchor_line(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str,
) -> str | None:
    """Generic nonsocial anchor: scene facts before abstract coaching."""
    obs = render_observe_perception_fallback_line(scene_or_envelope, seed_key=f"anchor|{seed_key}")
    if obs:
        return obs
    scene = _inner_scene(scene_or_envelope)
    loc = str(scene.get("location") or "").strip()
    if loc:
        mode = _stable_u32(f"anc|{seed_key}") % 2
        if mode == 0:
            return f"Rain and voices tangle{_near_loc_phrase(loc)}—the scene keeps moving without waiting."
        return f"The crowd's rhythm shifts{_near_loc_phrase(loc)}; faces turn, then turn away."
    return None


def _near_loc_phrase(loc: str) -> str:
    s = str(loc or "").strip()
    return f" near {s}" if s else ""


def render_global_scene_anchor_fallback(
    scene_or_envelope: Mapping[str, Any] | None,
    *,
    seed_key: str = "",
) -> str | None:
    """Last-resort global stock replacement when visible facts or summary exist."""
    line = render_observe_perception_fallback_line(scene_or_envelope, seed_key=f"global|{seed_key}")
    if line:
        return line
    scene = _inner_scene(scene_or_envelope)
    summary = _first_summary_sentence(scene)
    if summary:
        s0 = summary[0].lower() + summary[1:] if len(summary) > 1 else summary.lower()
        return f"The moment stays crowded with detail—{s0}."
    loc = str(scene.get("location") or "").strip()
    if loc:
        return f"Sound and motion keep trading places{_near_loc_phrase(loc)}."
    return None
