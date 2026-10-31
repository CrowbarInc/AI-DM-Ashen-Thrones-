# 21 — Combined Upstream Intervention

I9 supplies the gold act, referent target, question proposition, eligible ids, source propositions, correspondence label, and sufficiency class. It does not install the I8 line. Authorization, witness checks, and bind still run.

Validation: fixed 14, lost 0, net +14, success 32/54 (59.3%).

That is well above I3 or I5 and well below I8. The gap is the host rejecting gold inputs. On validation failures that I8 can already answer, I9 still returns:

- `no_relevant_source` after a gold proposition pair
- `unlisted_role_change`, `unlisted_correction_change`, `invalid_correction_operation`, `invalid_follow_up_operation`
- `unwitnessed_referent_request`, `unwitnessed_operation`
- `invalid_proposition`
- `referent_speaker_mismatch`

Those are the repairs with the largest remaining headroom. I9 is the upper bound of the current gates with better inputs, not the upper bound of a correct plan.
