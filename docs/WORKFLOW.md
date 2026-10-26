# Migration workflow

This is a prototype workflow for developers. The earlier public revision completed one player-focused engine migration and native load/save/reload. The current identity-based workflow has also completed one fresh Android migration and native load/save/reload with the importer disabled. The phone results cover one source fixture. A fresh source snapshot reproduced the readers and offline output using an existing engine intermediate, but did not reproduce a clean Android build/full engine migration or establish broader gameplay correctness. It deliberately separates extraction, an engine-assisted migration session, and offline finalization. Use a separate copy of the game installation for the session. Do not experiment on your only installation or save copy.

## 1. Prepare local inputs

Rebuild the C++ readers as described in the README, including the ZenKit NPC hotkey patch. Create a fresh workspace for the identity workflow; do not reuse an older decoded snapshot or generated mod. Use original Gothic II: Night of the Raven data and the original save directory from the same script/data version. The current world must be NEWWORLD; only NEWWORLD and OLDWORLD are handled.

```sh
python convert.py prepare --game-dir /path/to/original-game --save-dir /path/to/original-save --workspace work/session --tools-dir build
```

Preparation reads the original files. It writes a decoded snapshot, world metadata, guild data, a generated append-only `GOTHIC.DAT`, and the `og-save-import` mod into the workspace. These files contain game data or playthrough state and must stay local. The generated DAT preserves original symbol indices and bytecode, appending import helpers. Preparation resolves named internal zero-argument `RTN_*` routines and handles the original archive sentinel without treating it as executable code. The importer replaces default daily schedules and clears stale AI queues, movement targets, and current state before executing a named routine. This initializes a schedule; it does not reconstruct saved current/queued AI execution. `verify_helpers` checks generated NPC/global assignments against the source save.

The default report-text encoding is CP1250; `prepare --encoding cp1252` is available for investigation but has not been validated as a complete compatibility path.

## 2. Build a matching migration engine

Use the pinned OpenGothic-Android revision linked in the README, including its dependency patches. For the tested device, use the separate graphics project. **Apply `patches/migration-identity.patch`, then `patches/migration-routines.patch`, before building the engine. Both patches are required for the current full migration workflow.** It adds temporary per-NPC identities to migration saves and the scripting method used to assign them. Start a fresh migration game with the newly generated helpers/mod; an older intermediate without these identities will fail default finalization. Apply this repository's `patches/preserve-playtime.patch` while building that engine if you want subsequent saves to retain normalized total playtime. Without the patch, later native saves may replace the header playtime with the fresh simulation tick count.

The JavaScript importer needs the pinned fork's scripting/debug API. It is not supported on an arbitrary upstream OpenGothic build. It is intended for a disposable, fresh migration game.

## 3. Run the manual migration session

1. Back up the migration copy's original `_work/Data/Scripts/_compiled/GOTHIC.DAT`. Replace it **only in the migration copy** with `work/session/generated/GOTHIC.DAT`.
2. Copy `work/session/generated/og-save-import` into the engine's mod folder and enable it. On Android, the mod folder is the `mods` directory next to the game folders in the app's external files directory; it is not inside `Gothic2`.
3. Start a NEW game. Open the importer tab and choose **Import into a NEW game**. Do not continue an existing playthrough with this import mod enabled.
4. Wait until the importer reports completion. If OLDWORLD was present in the source, use the importer's **Visit Old World** button, wait for completion, and then **Return to New World**. The current pipeline expects both native worlds when OLDWORLD was extracted.
5. Use **Restore player position and equipment** after returning. A fresh-game introduction/dialogue may need to finish before normal save controls become available. This lifecycle step still needs automation and broader testing.
6. Save into a NEW native slot. Disable the importer before normal play. Keep the generated DAT in the migration game copy while using the resulting save: its appended globals are part of that session's scripts.
7. Export that native save to a local file, called `intermediate.sav` below. For a developer/debug APK, `adb exec-out run-as <package> cat files/save_slot_N.sav` can read it. Redirect the binary stream with a binary-safe tool; avoid text-mode shell redirection. A release APK may not allow `run-as`.

The source includes optional authenticated diagnostic commands for development. They are disabled unless you deliberately edit the generated local config to enable remote control. Do not expose the listener to an untrusted network; the API's binding behavior is inherited from the engine. Disable the importer when finished.

## 4. Finalize offline

```sh
python convert.py finalize --game-dir /path/to/original-game --workspace work/session --tools-dir build --native-save /path/to/intermediate.sav --output /path/to/converted-test.sav
```

`--game-dir` still points to the unmodified original DAT/data, not the generated migration DAT. The finalizer requires a new output filename and refuses to overwrite the native input. It checks the original DAT against the fingerprint recorded during preparation, reconciles player inventory quantities, rebuilds accessory pointers, and verifies selected player fields and inventory against the source before publication. Default finalization additionally requires source-bound NPC identities generated from the original DAT and the exact raw `source-save.json` bytes. Do not edit or reformat that JSON after preparation. The identities check source consistency, not authenticity against malicious changes. Supported NPC state is reconciled and checked in both worlds, including optional exported script waypoints and start-state function fields, then migration-key entries are stripped before final output. Calendar normalization shifts finite absolute AI end deadlines by the same delta while preserving infinite deadlines and simulation-tick timers. Exported AI/news metadata and coverage counts are diagnostic except for specifically restored fields; they do not imply complete behavior restoration. Each finalization attempt uses a new intermediate directory in the workspace. Native-save writing helpers validate and publish archives atomically without replacing existing output files. If conversion fails, inspect the error and retry with a new output filename when necessary.

Copy the new save into an unused native slot of the matching engine, with the importer disabled. Load it, check the player and journal, make a NEW save, and reload it again. CRC and structural checks do not prove gameplay correctness. Keep the original save and the intermediate engine save independently.

For an older intermediate only, `finalize --legacy-player-only` explicitly skips all-NPC reconciliation and identity verification. Player reconciliation/checks still run, but known NPC inventory overcounts remain. This is an incomplete fallback, not equivalent to the default workflow.

For experimental saved-AI entrypoint restart, add `--restart-saved-ai` to default finalization. It cannot be combined with `--legacy-player-only`. It is off by default. One opt-in phone round trip has passed limited checks; missing-waypoint diagnostics remain. Dead source NPCs are skipped, and exports missing AI metadata for any source NPC are rejected. The selected current-or-next named state restarts with empty action queues and reset state age, rather than resuming the saved execution history. See the README for deadline handling and limitations.

## Known manual steps

World visitation, dialogue/cutscene completion, exporting/importing private app saves, and end-to-end quest validation are still manual. Automatic recovery, a desktop-only converter, and a friendlier UI are roadmap work, not implemented features.
