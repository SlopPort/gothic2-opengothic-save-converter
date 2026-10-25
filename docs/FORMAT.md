# Format notes

These notes describe assumptions used by this prototype, not a complete Gothic/OpenGothic format specification.

- Original saves are decoded with the pinned ZenKit reader. Packed NPC inventory strings need the included separator-advance fix.
- Original DAT symbol indices must remain stable. The generator appends helpers and a migration mask without reordering the original records.
- OpenGothic saves are ZIP archives. **Explicit directory entries are significant:** the pinned engine counts NPC directories. Keeping only files can make the engine load no player even when NPC records are present. The archive helper preserves directory records, and a synthetic regression test covers this behavior.
- An inactive visited world's ZIP is stored as a uint32 byte length followed by its ZIP bytes. Repacking the ZIP without that length prefix breaks loading.
- The active-world binary layout is tied to format 56 and the pinned engine revision. Inventory records include item data, display slots, equipment indices, hotbar state, and trailing state values.
- Equipment pointers are restored without executing equip scripts: saved attributes already include equipment bonuses. Running equip effects again can double-count them.
- World/container items are created from native item templates. Missing templates are initialized with ZenKit's Daedalus VM from the original local DAT. Unknown or unsupported constructors may still fail.
- Container matching uses type and close spatial correspondence; movers additionally use unique base-world names. This is not a general identity or hierarchy reconciliation algorithm. Repeated names and ambiguous triggers remain limitations.
- Original calendar/playtime and native simulation ticks are distinct. The optional engine patch preserves a header/session offset rather than retiming NPC timers.

Do not publish generated DAT files, item templates, decoded snapshots, original archives, or saves with a bug report by default. The repository's tests use synthetic data.
