# Validation status

The public toolkit completed a fresh-workspace migration session on the matching Android build using one local source save. Preparation generated the public `OGI_` helpers and `og-save-import` mod, and the C++ verifier checked their NPC/global assignments against the source. A NEW engine game migrated both supported worlds. The resulting native intermediate went through the public finalizer, including missing item-template generation. With the importer disabled, the final save loaded, was saved by the engine into a new slot, and loaded again.

The visible character screen matched the source before and after the final native reload. Binary round-trip checks preserved the tested player attributes, hit chances, protection values, guild, level, experience, next-level threshold, learning points, and accessory identities. Journal records matched, known-dialog pairs were preserved, and the native guild-attitude table was unchanged through the native save. The corrected empty second ring slot stayed empty. Pre-existing native saves were checked by hash and were unchanged. Test saves, reports, screenshots, and game data remain local and are not distributed.

This is one fresh-session fixture using a previously built matching engine and locally compiled public readers. It is not independent clean-checkout reproduction or validation of other game/script editions. The earlier private development prototype was a separate validation stage. No full-storyline or broad quest/AI behavior test has been performed. Exact AI queues, NPC news, routines, spawn scheduling, all interactions, and dynamic relationships remain unsupported or incomplete.

## Automated checks

Synthetic fixtures exercise explicit directory preservation, visited-world length prefixes and nested archive integrity, populated inventory layouts and pointer bounds, active slots, NPC directory continuity, missing data/visual entries, header/session agreement, pinned versions, and bounded NPC script-state prefixes. The remaining NPC movement/AI/relationship payload is not decoded by the prefix reader.

Accessory fixtures cover stale-slot removal, repeated restoration, two explicit equipped source ring records sharing a native stack, equipped-count updates, insufficient amounts, conflicting slots, missing/ambiguous stacks, and unchanged non-accessory records. A second equipped ring is not inferred from a single source record with amount greater than one.

DAT fixtures cover numeric/string/function/member records, byte-preserving record extraction, every truncated prefix of a small file, and up to four extra newline bytes before a constant string's parent. The newline workaround matches the pinned ZenKit reader's first retry position. Script-state fixtures cover integer-array type/length mismatches, missing/duplicate globals, preserved float/string/instance records, legacy-byte journal text and ordering, preserved known-dialog pairs, and guild updates that retain extra engine rows/columns. The tests and offline finalization pass with Python optimization mode (`-O`); Python structural guards use explicit errors rather than assertions.

The `validate` command checks the active and visited worlds, including their inventories, script-variable record boundaries, and the journal/dialog/guild-table layout. Its JSON report excludes save titles, per-character/per-item values, and local paths. It does not resolve script IDs against the game DAT, decode every native field, certify an arbitrary engine revision, or establish quest semantics.

## Output protection

The CLI uses unique intermediate archives for each finalization attempt. The CLI publication step and all three native-save writing helpers check ZIP entries/CRCs and nested visited-world lengths/integrity, flush a temporary file in the destination directory, and atomically create the output using a hard link. An existing or concurrently created destination is never replaced. Filesystems without hard-link support fail safely. These guarantees do not certify gameplay compatibility or guarantee persistence after a filesystem/power failure.

Generated snapshots, DAT files, item templates, and detailed normalization/world reports contain local paths, game data, or playthrough state and must remain local. They are not covered by the `validate` command's limited-report privacy claim.

An optional source-check workflow template is included as `docs/ci-workflow.yml`. To enable it, copy it to `.github/workflows/check.yml` using credentials with workflow-write permission. It is not an active Actions workflow in this repository.
