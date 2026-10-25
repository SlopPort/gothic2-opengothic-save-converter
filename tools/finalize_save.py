"""Normalize a format-56 export using original save data, without touching inputs."""
import argparse,hashlib,json,struct
from pathlib import Path
from native_format import Reader,archive,write_archive
from native_validation import MAGIC,validate_save
from script_state import restore_globals,restore_journal,string

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.workspace.resolve()
    if args.input.resolve()==args.output.resolve():raise ValueError('Input and output must differ')
    data=args.input.read_bytes();validate_save(data);entries=archive(data)
    source=json.loads((root/'source-save.json').read_text())
    header=Reader(entries['header']);header.skip(len(MAGIC));version=header.number('<H')
    header.s();world=header.s().decode('latin1');calendar_bytes=header.read(36)
    header.skip(16);game=header.number('<B');tail=header.b[header.p:]
    day,hour,minute=source['time']
    if day<0 or not 0<=hour<24 or not 0<=minute<60 or source['playSeconds']<0:
        raise ValueError('Invalid source calendar or playtime')
    worldtime=((day*24+hour)*60+minute)*60000
    entries['header']=MAGIC+struct.pack('<H',version)+string('ORIGINAL SAVE IMPORT (EXPERIMENTAL)')+string(world)+calendar_bytes+struct.pack('<qQ',worldtime,source['playSeconds']*1000)+bytes([game])+tail
    # Preserve simulation ticks and NPC timers; restore only the world calendar.
    session=bytearray(entries['game/session']);struct.pack_into('<q',session,8,worldtime);entries['game/session']=session
    entries['game/quests']=restore_journal(entries['game/quests'],source['quests'])
    entries['game/daedalus'],globals_report=restore_globals(entries['game/daedalus'],source['symbols'])
    write_archive(entries,args.output)
    report=dict(output=str(args.output),version=version,world=world,**globals_report,
                journalTopics=len(source['quests']),calendar=source['time'],nativePlayTicksPreserved=True,
                entries=len(entries),sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                limitations='Intermediate normalization only. Run world restoration and equipment restoration next; exact AI compatibility remains unsupported.')
    (root/'normalization-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
