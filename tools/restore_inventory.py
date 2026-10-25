"""Restore exact player inventory counts before restoring accessory pointers."""
import argparse,json,struct
from pathlib import Path
from dat_symbols import parse_dat
from native_format import archive,write_archive
from inventory_restore import reconcile_inventory,source_inventory

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('game-dir','workspace','input','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.input.resolve()==args.output.resolve():raise ValueError('Input and output must differ')
    source=json.loads((args.workspace/'source-save.json').read_text())
    heroes=[npc for npc in source['worlds']['NEWWORLD'] if npc['player']]
    if len(heroes)!=1:raise ValueError('Expected exactly one source player')
    byname=parse_dat(args.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT')['byname']
    expected={byname[name]['index']:amount for name,amount in source_inventory(heroes[0]).items()}
    entries=archive(args.input.read_bytes());hero_symbol=byname['PC_HERO']['index']
    paths=[name for name,data in entries.items() if name.startswith('worlds/newworld.zen/npc/')
           and name.endswith('/data') and len(data)>=4 and struct.unpack_from('<I',data)[0]==hero_symbol]
    if len(paths)!=1:raise ValueError('Expected exactly one native player')
    path=paths[0][:-4]+'inventory'
    entries[path]=reconcile_inventory(entries[path],expected,clear_accessories=True)
    write_archive(entries,args.output)
    print('Restored exact source player inventory amounts; accessory restoration is required next')

if __name__=='__main__':main()
