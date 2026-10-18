# 06 — Root-Cause Analysis

A rejected fallback had immutable=false, so restoration was a no-op. The authoritative-fact helper treated factual grounding as permission to rewrite speech, never consulting final acceptance, speaker or addressee. It ran after restoration and again in endpoint completion. Fresh testing exposed a second gap: a legacy retry constructed a new dictionary without an adoption record. Guarding only immutable=true would miss that path. Both defects are addressed: terminal fallback adoption and complete missing-adoption authorization before delivery.
