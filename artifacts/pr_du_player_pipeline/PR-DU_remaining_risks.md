PR-DU Remaining Risks

- The stored interpretation hook is injectable but currently no live provider integration is enabled; live interpretation remains disabled by policy.
- Player-visible narration still needs polish for transition and notice-board specificity.
- Persistence failure handling was not simulated.
- TestClient transport was unavailable in this sandbox; HTTP wrapper behavior is inferred from the thin api_chat -> chat call boundary.
- The repo had substantial pre-existing dirty changes, including handoff and data files, before PR-DU work began.
