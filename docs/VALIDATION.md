# Validation status

The original working prototype completed a migration, native engine save, and reload on the tested Android build. Character-stat checks matched the source, and structural checks covered the world item records, explicit NPC directories, nested visited-world payload, equipment pointers, and ZIP CRCs. No full-storyline validation was performed.

The extracted public toolkit's C++ readers compiled locally. Its `prepare` path generated DAT helpers and checked their NPC/global assignments in ZenKit. Its `finalize` path processed an existing prototype native intermediate through normalization, world restoration, missing item-template initialization, and accessory restoration. The resulting archive passed CRC checks.

This does not constitute a fresh end-to-end engine session using the newly named public helpers/mod. That clean-checkout-to-engine run remains pending. The source save and native intermediate used for local testing are not distributed.

Synthetic regression tests cover explicit directory preservation, visited-world length prefixes, empty inventory layout, truncated input, and duplicate ZIP entry rejection. Publication tests additionally cover invalid archives, failed flushes, existing or concurrently created destinations, and filesystems without hard-link support. They do not certify gameplay behavior.

An optional source-check workflow template is included as `docs/ci-workflow.yml`. To enable it, copy it to `.github/workflows/check.yml` using credentials with workflow-write permission. It is not an active Actions workflow in this repository.

Finalization now writes unique intermediate archives within the workspace. The CLI validates the completed candidate's top-level ZIP entries and CRCs, plus visited-world payload lengths and nested ZIP integrity, flushes a temporary file in the destination directory, then atomically creates the destination using a hard link. Existing destinations are never replaced, including when another process creates one during conversion. A filesystem without hard-link support fails safely. Among standalone helpers, accessory restoration also provides this publication guarantee; the other helpers do not yet.

The `prepare` and `finalize` commands refuse Python optimization mode because several migration helpers still use assertions. The `validate` command uses explicit checks and can run under optimization mode. Inventory truncation, trailing-data, and item-count guards use explicit exceptions and also operate under optimization mode. This is archive-integrity protection, not full engine-format or gameplay validation.

The `validate` command and finalization preflight/postflight now check header/session world and calendar agreement, the visited-world list against nested payloads, pinned world versions, contiguous explicit NPC directories, required NPC data/visual entries, complete loose-item records, and inventory model/attachment/equipment pointer bounds in both active and visited worlds. Empty NPC inventories are permitted because the pinned engine omits them. The report does not include save titles or per-character/per-item data.

Synthetic fixtures cover a populated inventory, attachment and equipment indices, active slots, missing NPC directories/visuals, non-contiguous identifiers, header/session mismatches, nested inventory corruption, and unsupported versions. Local native prototype and converted archives passed the checks; this adds no new gameplay-validation claim.

Accessory restoration now rebuilds all four player accessory pointers from the source active-item records, clearing stale native assignments. A locally tested intermediate contained a stale second ring pointer; restoration removed it while retaining the intended accessory assignments. Synthetic tests cover two explicit equipped source ring records sharing a native stack, equipped-count updates, repeated restoration, insufficient stacks, conflicting slots, unknown symbols, and unchanged non-accessory records. This does not infer a second equipped ring from a single source record with amount greater than one, and ambiguous native stacks are rejected. No fresh engine reload of this revision has yet been performed.

The standalone accessory-restoration helper now uses the same atomic no-overwrite archive writer as the CLI publication step. Other standalone helpers still need that guarantee.
