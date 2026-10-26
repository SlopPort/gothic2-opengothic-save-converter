"""Prepare a migration session or finalize a native save. Work-in-progress, format 56 only."""
from pathlib import Path
import argparse,json,subprocess,sys,tempfile
from tools.native_format import publish_archive
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
from native_validation import validate_save
from workspace_checks import verify_original_scripts
from player_checks import verify_player
from native_format import archive,write_archive
from restore_npcs import verify_npcs
from migration_identity import source_fingerprint,strip_migration_keys
from dat_symbols import parse_dat
ROOT=Path(__file__).resolve().parent

def run(*args):
    subprocess.run([str(x) for x in args],check=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    check=sub.add_parser('validate',help='Check the pinned native layout without game assets')
    check.add_argument('--native-save',type=Path,required=True)
    for command in ['prepare','finalize']:
        q=sub.add_parser(command)
        q.add_argument('--game-dir',type=Path,required=True)
        q.add_argument('--workspace',type=Path,required=True)
        q.add_argument('--tools-dir',type=Path,required=True,help='Directory containing the compiled C++ exporters')
        if command=='prepare':
            q.add_argument('--save-dir',type=Path,required=True);q.add_argument('--encoding',default='cp1250')
        else:
            q.add_argument('--native-save',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
            q.add_argument('--legacy-player-only',action='store_true',help='Explicitly skip NPC reconciliation for older intermediates without stable identities')
            q.add_argument('--restart-saved-ai',action='store_true',help='Experimental: restart saved AI script entrypoints instead of retaining migration-session state')
    a=p.parse_args()
    if a.command=='validate':
        print(json.dumps(validate_save(a.native_save.read_bytes()),indent=2))
        return
    w=a.workspace.resolve();w.mkdir(parents=True,exist_ok=True)
    def tool(name):
        path=a.tools_dir.resolve()/(name+('.exe' if sys.platform=='win32' else ''))
        if not path.is_file():raise FileNotFoundError(path)
        return path
    def py(name,*args):run(sys.executable,ROOT/'tools'/name,*args)
    common=['--game-dir',a.game_dir.resolve(),'--workspace',w]
    if a.command=='prepare':
        if (w/'source-save.json').exists():raise FileExistsError('Use a fresh workspace for each source save')
        run(tool('export_save'),a.save_dir.resolve(),w/'source-save.json')
        source=json.loads((w/'source-save.json').read_text())
        from source_validation import validate_source
        validate_source(source)
        run(tool('export_world'),a.save_dir.resolve(),w/'world-state.json')
        run(tool('export_base_world'),a.game_dir.resolve()/'Data',w/'base-world-state.json')
        run(tool('export_guild'),a.save_dir.resolve(),w/'guild-attitudes.bin')
        py('build_import.py',*common,'--encoding',a.encoding)
        run(tool('verify_helpers'),w/'generated/GOTHIC.DAT',a.save_dir.resolve())
        print('Prepared. Continue with the manual engine migration in docs/WORKFLOW.md.')
    else:
        if a.legacy_player_only and a.restart_saved_ai:raise ValueError('Saved AI restart requires NPC reconciliation')
        if a.output.exists():raise FileExistsError('Output exists; choose a new filename')
        if a.native_save.resolve()==a.output.resolve():raise ValueError('Input and output must differ')
        verify_original_scripts(a.game_dir,w)
        validate_save(a.native_save.read_bytes())
        # Unique intermediates prevent concurrent runs from sharing partial archives.
        staging=Path(tempfile.mkdtemp(prefix='finalize-',dir=w))
        py('finalize_save.py','--workspace',w,'--input',a.native_save.resolve(),'--output',staging/'normalized.sav')
        # First pass discovers item definitions absent from the native session.
        command=[sys.executable,ROOT/'tools/complete_world_save.py',*common,'--input',staging/'normalized.sav','--output',staging/'world-restored.sav']
        coverage=w/'world-item-coverage.json'
        coverage.unlink(missing_ok=True)
        result=subprocess.run([str(x) for x in command])
        if result.returncode:
            coverage=w/'world-item-coverage.json'
            missing=json.loads(coverage.read_text())['missing'] if coverage.exists() else []
            if not missing:raise RuntimeError('World conversion failed; see the error above')
            run(tool('export_items'),a.game_dir.resolve()/'_work/Data/Scripts/_compiled/GOTHIC.DAT',w/'item-templates',*missing)
            run(*command)
        inventory_input=staging/'world-restored.sav'
        if not a.legacy_player_only:
            coverage=w/'npc-item-coverage.json';coverage.unlink(missing_ok=True)
            command=[sys.executable,ROOT/'tools/restore_npcs.py',*common,'--input',inventory_input,'--output',staging/'npcs-restored.sav']
            if a.restart_saved_ai:command.append('--restart-saved-ai')
            result=subprocess.run([str(x) for x in command])
            if result.returncode:
                missing=json.loads(coverage.read_text()).get('missing',[]) if coverage.exists() else []
                if not missing:raise RuntimeError('NPC reconciliation failed; see the error above')
                run(tool('export_items'),a.game_dir.resolve()/'_work/Data/Scripts/_compiled/GOTHIC.DAT',w/'item-templates',*missing)
                run(*command)
            inventory_input=staging/'npcs-restored.sav'
        else:print('Legacy mode: NPC quantities are NOT reconciled')
        py('restore_inventory.py',*common,'--input',inventory_input,'--output',staging/'inventory-restored.sav')
        py('restore_equipment.py',*common,'--input',staging/'inventory-restored.sav','--output',staging/'equipped.sav')
        equipped=archive((staging/'equipped.sav').read_bytes())
        if not a.legacy_player_only:
            dat=(a.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT').read_bytes()
            source_bytes=(w/'source-save.json').read_bytes()
            verify_npcs(equipped,json.loads(source_bytes),source_fingerprint(dat,source_bytes),
                        parse_dat(a.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT')['byname'],a.restart_saved_ai)
        write_archive(strip_migration_keys(equipped),staging/'candidate.sav')
        candidate=(staging/'candidate.sav').read_bytes()
        validate_save(candidate)
        verify_player(archive(candidate),json.loads((w/'source-save.json').read_text()),
                      parse_dat(a.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT')['byname'])
        publish_archive(staging/'candidate.sav',a.output.resolve())
        print('Experimental converted save:',a.output.resolve())
        print('Test loading, saving, and reloading in the matching engine before continuing a playthrough.')
if __name__=='__main__':main()
