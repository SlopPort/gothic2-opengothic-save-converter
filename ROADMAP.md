# Roadmap

## Next

- Reconcile NPC inventory quantities: the native clear operation retains equipped/mission items. The player is corrected offline; uniquely matched NPCs still show overcounts, and ambiguous NPC groups need stable identity mapping.

- Independently reproduce the public-toolkit fresh-session result from a clean checkout, then test additional source saves and script editions; the current engine load/save/reload check covers one fixture.
- Validate more cross-file NPC/script references and additional script editions. Python guards use explicit errors; all four native-save writers publish atomically without overwriting existing files. Synthetic DAT, inventory, equipment, nested-world, global, and journal fixtures are present.
- Automate world visitation and the fresh-game dialogue/cutscene lifecycle without leaving a diagnostic listener enabled.
- Track object identity and parent transforms consistently; investigate skipped duplicate-name movers/triggers.

## Compatibility research

- Reconstruct NPC routines, AI queues, news, spawn scheduling, timed effects, and dynamic relationships.
- Preserve the complete interaction/mover/trigger state and validate representative quest chains.
- Support additional current/visited worlds and script editions only after explicit fixtures and testing.
- Add format/revision negotiation instead of relying on a format number alone.

## Longer term

- A desktop-only migration path that does not require the engine-assisted session.
- A guided interface with per-field coverage and a clear report of skipped or approximated state.
- Upstream collaboration where the work is useful; this repository does not imply upstream endorsement or a promised delivery date.
