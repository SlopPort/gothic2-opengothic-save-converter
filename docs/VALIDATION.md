# Validation status

## Earlier public baseline

Public revision `33441b5` completed one fresh-workspace migration using locally compiled readers and a previously built matching Android engine. Both supported worlds were visited. The importer was disabled before final loading, native saving, and reloading. Player fields, corrected exact inventory quantities, accessory identities, journal records, known-dialog pairs, and guild-table data were checked through the relevant round trips. Pre-existing native saves were checked by hash and remained unchanged. This earlier stage had 90 Python tests passing normally and under `-O`.

That result covers the earlier player-focused pipeline. NPC inventory overcounts were observed and remained unresolved at that revision. It is not evidence for the new identity-based all-NPC reconciliation path, independent clean-checkout reproduction, other script editions, or full-storyline correctness.

## Current identity-based development

Default finalization now requires a fresh preparation workspace, fresh migration game, and matching engine built with `patches/migration-identity.patch`. Temporary OGI1 identities bind the original DAT bytes and raw source JSON bytes to source-world/index records. Offline reconciliation restores supported NPC script fields, exact inventory quantities, accessory pointers, spell shortcuts, position/heading, scale/fatness, true guild, attitudes, and talents in the supported worlds. Verification runs before migration-key entries are stripped from active and nested visited worlds and output is published.

One fresh identity-based Android migration has completed. Readers were rebuilt, the matching native engine was rebuilt with the identity patch and installed, a NEW migration game visited both supported worlds, and strict default finalization verified the identified source NPC records before stripping temporary metadata. The output loaded with the importer disabled, spell shortcuts were visible, a new native save was created, and that save reloaded successfully.

The native resave passed the selected player-field checks, including exact player inventory quantities, accessories, and spell shortcuts. Journal, known-dialog, and guild-table payloads were byte-identical through that round trip. Visited-world NPC inventory multisets were unchanged. Active-world NPC inventory multisets changed during live simulation, with changes consistent with item consumption, transformation, and AI item creation. All-NPC source equality is checked before publication; it is not claimed as an invariant after live AI runs.

A comparison of named script integer globals found changes in function-local, random, and per-frame scratch values; no story-global change was identified in that comparison. Full instance-reference bytes can change during native saving. These observations are limited to this test and do not establish semantic equality of every global or quest state. Pre-existing native save slots were unchanged by hash. The explicit `--legacy-player-only` path skips all-NPC reconciliation and identity verification and retains the earlier NPC quantity limitations. Source fingerprints check consistency; they do not authenticate an intermediate against deliberate forgery.

The current Python suite has 120 passing tests both normally and under `-O`. Synthetic coverage includes identity mismatch/missing/duplicate/index checks, NPC state and inventory transforms, pointer remapping, equipment counts, hotkeys, bounded DAT/native readers, nested world archives, globals, journal/guild layouts, and exclusive output publication. A synthetic C++ save-reader round trip covering the ZenKit hotkey patch and JavaScript lifecycle tests exercising importer behavior also passed. These tests and the single engine round trip do not establish full-storyline correctness or universal save compatibility.

## Structural checks and limits

The `validate` command checks header/session agreement, supported versions/worlds, NPC directory continuity and required entries, bounded NPC script-state prefixes, inventory records/pointers, script-variable boundaries, and journal/dialog/guild-table layout in the applicable archives. Remaining movement, animation, AI queues, routines, news, scheduling, and dynamic relationships are not fully reconstructed. Script IDs are not generally resolved against all game data. Structural checks do not prove quest semantics or compatibility with an arbitrary engine revision.

The JSON validation report omits save titles, individual character/item values, and local paths. Generated snapshots, DAT files, item templates, and detailed conversion reports contain game data, local paths, or playthrough state and must remain local. No source saves, screenshots, personal reports, or game assets are distributed.

## Output protection

The CLI uses unique intermediate archives for each finalization attempt. Native-save writers validate ZIP entries/CRCs and nested visited-world lengths/integrity, flush a temporary file in the destination directory, and atomically create output using a hard link. Existing or concurrently created destinations are never replaced; unsupported filesystems fail safely. These guarantees do not certify gameplay or guarantee persistence after a filesystem/power failure. Python structural guards use explicit errors and remain active under `-O`.

An optional source-check workflow template is included as `docs/ci-workflow.yml`. It is not an active Actions workflow; enabling it requires installing it in `.github/workflows` with suitable permissions.
