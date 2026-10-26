# Roadmap

## Next

- Compare the tested opt-in saved-AI restart mode with the default path under controlled simulation, investigate missing-waypoint diagnostics, and exercise additional state types. Both modes have completed limited native load/save/reload checks; exact saved AI execution remains incomplete.

- Extend the single successful identity-based engine round trip with controlled simulation tests. Distinguish expected active-world NPC item consumption/creation from migration defects; offline source equality does not imply unchanged inventories after live AI runs.
- Exercise missing/duplicate identities, same-instance NPC groups, cross-world player aliases, hotkeys, and pose changes on additional real source saves.

- Reproduce a clean Android build and complete fresh engine migration from a source snapshot, then test additional source saves and script editions. Fresh Windows reader builds and offline output reproduction with a reused engine intermediate have passed; the phone checks still cover one source fixture.
- Validate more cross-file NPC/script references and additional script editions. Python guards use explicit errors; the native-save writing helpers publish atomically without overwriting existing files. Synthetic DAT, inventory, equipment, nested-world, global, and journal fixtures are present.
- Automate world visitation and the fresh-game dialogue/cutscene lifecycle without leaving a diagnostic listener enabled.
- Track object identity and parent transforms consistently; investigate skipped duplicate-name movers/triggers.

## Compatibility research

- Reconstruct exact current/queued AI execution, news, respawn/spawn scheduling, timed effects, and dynamic relationships beyond the implemented named daily schedules. Use coverage reports to track captured metadata separately from restored behavior.
- Preserve the complete interaction/mover/trigger state and validate representative quest chains.
- Support additional current/visited worlds and script editions only after explicit fixtures and testing.
- Add format/revision negotiation instead of relying on a format number alone.

## Longer term

- A desktop-only migration path that does not require the engine-assisted session.
- A guided interface with per-field coverage and a clear report of skipped or approximated state.
- Upstream collaboration where the work is useful; this repository does not imply upstream endorsement or a promised delivery date.
