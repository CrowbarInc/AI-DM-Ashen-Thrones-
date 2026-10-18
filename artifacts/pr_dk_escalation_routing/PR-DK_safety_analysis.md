# PR-DK Safety Analysis

All compared approaches must preserve:

- authoritative engine execution;
- existing dice and mechanics;
- world-state validation;
- hidden-information boundaries;
- no direct model mutation;
- no model-authored outcomes;
- no interpretation execution without authoritative validation.

Selective routing and universal interpretation differ only in when non-authoritative interpretation metadata is requested. Neither may write saves, mutate state, choose dice, reveal hidden information, or replace resolver validation.
