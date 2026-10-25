# Validation status

The original working prototype completed a migration, native engine save, and reload on the tested Android build. Character-stat checks matched the source, and structural checks covered the world item records, explicit NPC directories, nested visited-world payload, equipment pointers, and ZIP CRCs. No full-storyline validation was performed.

The extracted public C++ readers compiled locally. Its `prepare` path generated DAT helpers and checked their NPC/global assignments in ZenKit. Its `finalize` path processed an existing prototype native intermediate through normalization, world restoration, missing item-template initialization, and accessory restoration. The resulting archive passed CRC checks.

This does not constitute a fresh end-to-end engine session using the newly named public helpers/mod. That clean-checkout-to-engine run remains pending. The source save and native intermediate used for local testing are not distributed.

Synthetic regression tests cover explicit directory preservation, visited-world length prefixes, empty inventory layout, truncated input, and duplicate ZIP entry rejection. They do not certify gameplay behavior.

An optional source-check workflow template is included as `docs/ci-workflow.yml`. To enable it, copy it to `.github/workflows/check.yml` using credentials with workflow-write permission. It is not an active Actions workflow in this repository.
