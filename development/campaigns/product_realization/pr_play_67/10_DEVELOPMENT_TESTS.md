# DEVELOPMENT TESTS

42 new focused development tests pass (development.xml). They exercise twenty internal/unknown source paths, six object-valued public scalar probes, both experimental flag modes over complete gameplay/state HTTP, six failure forms, and eight player-field/authority/discovery/repeat/isolation cases. The previous 45 PR66 publication tests and PR55–65 consequence/disclosure/isolation tests run in the aggregate lane.

All assertions for hidden data inspect serialized complete responses. Existing tests that asserted server-only resolver or GM publication metadata through HTTP were migrated to persisted server log assertions, adding explicit assertions that HTTP metadata/resolution are absent/empty. No authoritative assertion was removed. Unknown-mode error wording now expects safe generic copy without request echo. Initial failures and final reruns are preserved separately.
