"""Production ownership write-path governance (tests only).

This module owns **BU8/BU9/BU10 write-path parity and producer-stamp pairing locks** that keep
the BU4 CSV registry aligned with live ``game/`` ownership write-path discovery and ensure
attach/stamp helpers pair correctly at call sites.

This is **not** the global test-responsibility ownership registry. Registry identity and
inventory parity remain in ``tests/test_ownership_registry.py``.

Implementation helpers live in ``tests/helpers/ownership_write_path_governance.py``.

- **BU8 BU4 CSV parity** (Cycle BU8): BU4 CSV registry stays parity-locked with live
  production write-path discovery. Enforced by
  ``test_bu8_bu4_production_ownership_write_paths_parity_locked``.
- **BU8 attach_realization producer stamp pairing** (Cycle BU8): attach_realization_fallback_family
  call sites pair with bucket stamper helpers. Enforced by
  ``test_bu8_attach_realization_fallback_family_producer_stamp_pairing_locked``.
- **BU9 visibility fallback producer stamp pairing** (Cycle BU9/BU10): visibility-family
  producer repair kinds pair with bucket stamper helpers. Enforced by
  ``test_bu9_visibility_fallback_producer_stamp_pairing_locked``.
"""


def test_bu8_bu4_production_ownership_write_paths_parity_locked() -> None:
    """BU8: BU4 CSV registry stays parity-locked with live game/ ownership write-path discovery."""
    from tests.helpers.ownership_write_path_governance import (
        REQUIRED_PRODUCTION_WRITE_PATH_KEYS,
        bu4_csv_path,
        production_write_path_keys_from_csv,
        production_write_path_parity_errors,
    )

    assert bu4_csv_path().is_file()
    csv_keys = production_write_path_keys_from_csv()
    assert REQUIRED_PRODUCTION_WRITE_PATH_KEYS <= csv_keys
    assert production_write_path_parity_errors() == []


def test_bu8_attach_realization_fallback_family_producer_stamp_pairing_locked() -> None:
    """BU8: attach_realization_fallback_family call sites pair with bucket stamper helpers."""
    from tests.helpers.ownership_write_path_governance import (
        attach_realization_exempt_documentation,
        producer_stamp_pairing_errors,
    )

    assert producer_stamp_pairing_errors() == []
    assert attach_realization_exempt_documentation()


def test_bu9_visibility_fallback_producer_stamp_pairing_locked() -> None:
    """BU9/BU10: visibility-family producer repair kinds pair with bucket stamper helpers."""
    from tests.helpers.ownership_write_path_governance import (
        visibility_fallback_write_path_inventory,
        visibility_producer_stamp_exempt_documentation,
        visibility_producer_stamp_pairing_errors,
    )

    assert visibility_producer_stamp_pairing_errors() == []
    assert visibility_producer_stamp_exempt_documentation()
    inventory = visibility_fallback_write_path_inventory()
    assert inventory['visibility_producer_repair_kind_sites']
    assert inventory['visibility_fallback_owner_bucket_writes']
    first_mention_site = ('game/final_emission_visibility_fallback.py', 'apply_first_mention_enforcement')
    referential_site = ('game/final_emission_visibility_fallback.py', 'apply_referential_clarity_enforcement')
    producer_sites = inventory['visibility_producer_repair_kind_sites']
    assert any(
        site[0] == first_mention_site[0] and site[1] == first_mention_site[1]
        for site in producer_sites
    )
    assert sum(
        1
        for site in producer_sites
        if site[0] == referential_site[0] and site[1] == referential_site[1]
    ) >= 2
