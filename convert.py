"""Prepare a migration session or finalize a native save. Work-in-progress, format 56 only."""
from pathlib import Path
import argparse,json,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parent

def run(*args):
    subprocess.run([str(x) for x in args],check=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for command in ['prepare','finalize']:
        q=sub.add_parser(command)
        q.add_argument('--game-dir',type=Path,required=True)
        q.add_argument('--workspace',type=Path,required=True)
        q.add_argument('--tools-dir',type=Path,required=True,help='Directory containing the compiled C++ exporters')
        if command=='prepare':
            q.add_argument('--save-dir',type=Path,required=True);q.add_argument('--encoding',default='cp1250')
        else:
            q.add_argument('--native-save',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    a=p.parse_args();w=a.workspace.resolve();w.mkdir(parents=True,exist_ok=True)
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
        if source['world']!='NEWWORLD' or set(source['worlds'])-{'NEWWORLD','OLDWORLD'}:
            raise ValueError('Supported scope: current NEWWORLD with NEWWORLD/OLDWORLD saves only')
        run(tool('export_world'),a.save_dir.resolve(),w/'world-state.json')
        run(tool('export_base_world'),a.game_dir.resolve()/'Data',w/'base-world-state.json')
        run(tool('export_guild'),a.save_dir.resolve(),w/'guild-attitudes.bin')
        py('build_import.py',*common,'--encoding',a.encoding)
        run(tool('verify_helpers'),w/'generated/GOTHIC.DAT',a.save_dir.resolve())
        print('Prepared. Continue with the manual engine migration in docs/WORKFLOW.md.')
    else:
        if a.output.exists():raise FileExistsError('Output exists; choose a new filename')
        if a.native_save.resolve()==a.output.resolve():raise ValueError('Input and output must differ')
        py('finalize_save.py','--workspace',w,'--input',a.native_save.resolve(),'--output',w/'normalized.sav')
        # First pass discovers item definitions absent from the native session.
        command=[sys.executable,ROOT/'tools/complete_world_save.py',*common,'--input',w/'normalized.sav','--output',w/'world-restored.sav']
        result=subprocess.run([str(x) for x in command])
        if result.returncode:
            coverage=w/'world-item-coverage.json'
            missing=json.loads(coverage.read_text())['missing'] if coverage.exists() else []
            if not missing:raise RuntimeError('World conversion failed; see the error above')
            run(tool('export_items'),a.game_dir.resolve()/'_work/Data/Scripts/_compiled/GOTHIC.DAT',w/'item-templates',*missing)
            run(*command)
        py('restore_equipment.py',*common,'--input',w/'world-restored.sav','--output',a.output.resolve())
        with zipfile.ZipFile(a.output) as z:
            if z.testzip() is not None:raise RuntimeError('Output CRC check failed')
        print('Experimental converted save:',a.output.resolve())
        print('Test loading, saving, and reloading in the matching engine before continuing a playthrough.')
if __name__=='__main__':main()
