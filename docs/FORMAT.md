# Format notes

These notes describe assumptions used by this prototype, not a complete Gothic/OpenGothic format specification.

- Original saves are decoded with the pinned ZenKit reader. Packed NPC inventory strings need the included separator-advance fix.
- The migration engine patch writes temporary `migration-key` entries with schema 1 and an `OGI1:<fingerprint>:<world>:<source-index>` identity. The fingerprint hashes the original DAT bytes and raw decoded-source JSON bytes with an OGI1 domain prefix. Default finalization rejects missing, duplicate, mismatched, or out-of-range identities and checks instance symbols. These hashes provide consistency checks, not cryptographic authentication. Migration-key entries are removed from both active and nested visited worlds before publication.
- Source NPC quantities and supported fields are verified before final publication. Once loaded, active-world AI can consume, transform, or create items; source equality at publication is not an invariant of later native saves.
- NPC reconciliation restores supported script fields and selected pose/attitude/talent fields. Heading is derived from the original rotation; this does not reconstruct every animation, movement queue, routine, or dynamic relationship. NPC spell shortcuts rely on the included ZenKit hotkey patch.
- Original DAT symbol indices must remain stable. The generator appends helpers and a migration mask without reordering the original records.
- OpenGothic saves are ZIP archives. **Explicit directory entries are significant:** the pinned engine counts NPC directories. Keeping only files can make the engine load no player even when NPC records are present. The archive helper preserves directory records, and a synthetic regression test covers this behavior.
- An inactive visited world's ZIP is stored as a uint32 byte length followed by its ZIP bytes. Repacking the ZIP without that length prefix breaks loading.
- The active-world binary layout is tied to format 56 and the pinned engine revision. Inventory records include item data, display slots, equipment indices, hotbar state, and trailing state values.
- Native inventory clearing preserves equipped and mission items. Reapplying a source inventory can therefore duplicate quantities. Offline player reconciliation sets exact source amounts, removes extra stacks, remaps inventory-local pointers, and clears accessory pointers before rebuilding them. Missing or ambiguous requested native stacks are rejected. The default identity-based path applies this reconciliation to all mapped source NPC records; the explicit legacy fallback covers only the player.
- Player accessory pointers are rebuilt from active source item records; absent accessories clear the corresponding native slots. Two explicit source ring records may share one native stack; its equipped field is a count, not a boolean. Duplicate native stacks for a requested accessory are rejected as ambiguous.
- Equipment pointers are restored without executing equip scripts: saved attributes already include equipment bonuses. Running equip effects again can double-count them.
- World/container items are created from native item templates. Missing templates are initialized with ZenKit's Daedalus VM from the original local DAT. Unknown or unsupported constructors may still fail.
- Container matching uses type and close spatial correspondence; movers additionally use unique base-world names. This is not a general identity or hierarchy reconciliation algorithm. Repeated names and ambiguous triggers remain limitations.
- Original calendar/playtime and native simulation ticks are distinct. The optional engine patch preserves a header/session offset rather than retiming NPC timers.

Do not publish generated DAT files, item templates, decoded snapshots, original archives, or saves with a bug report by default. The repository's tests use synthetic data.
