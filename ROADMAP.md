# Roadmap

## Next

- Run the extracted toolkit from a clean checkout through a fresh migration session; the working private prototype and the refactored public CLI are separate validation stages.
- Replace assert-based guards with explicit errors; make every final output write atomic and validate more cross-file references.
- Add synthetic fixtures for full inventory layouts, nested visited worlds, equipment pointers, and DAT edge cases.
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
