# PR-CH Speaker And Authority Analysis

The target failure is not caused by speaker selection or authority classification.

Evidence:
- The target NPC is explicitly addressed.
- The target NPC is present in the active scene.
- The selected topic belongs to `kiln_tender`.
- Grounding reports `authoritative_speaker_eligible`.
- The authored realization helper formats the answer as `Kiln Tender` speech.

PR-CF does identify adjacent speaker/reply drift, including `C_SPEAKER_CONTRACT_MISMATCH` and `reply_kind` unknown/refusal changes. Those are adjacent to the same social/final-emission surface, but PR-CH does not prove they share the exact target mechanism.

Conclusion: target authority handling is CONFIRMED good through deterministic selection; broader speaker-contract failures remain SUPPORTED adjacent defects.

