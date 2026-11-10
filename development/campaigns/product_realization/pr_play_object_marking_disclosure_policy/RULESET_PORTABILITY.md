# Ruleset Portability

Milestone: `pr_play_object_marking_disclosure_policy`. Date: 2026-11-09.

The same mechanism and authorized inscription are tested with pf1e@1 (AC/perception DC), rules_light@1 (tags/private data) and scifi@1 (sensor/battery/encryption). Exact whole-character equality across observation and actual save/reload proves extensions are opaque and preserved. The projected value is identical across all three; no extension is inspected for permission. Evidence: observation_portability_*.json and focused JUnit. No DC/skill/spell/proficiency/rarity/crafting/sensor interpretation occurs; those remain upstream authority or future adapters. This demonstrates boundary portability, not a complete alternate-ruleset game runtime.
