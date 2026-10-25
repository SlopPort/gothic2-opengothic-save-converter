"""Restore accessory equipment pointers without applying stat bonuses twice."""
from pathlib import Path
import argparse,json,struct
from accessories import restore_accessories
from native_format import archive,write_archive
from dat_symbols import parse_dat

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir',type=Path,required=True)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.input.resolve()==args.output.resolve():raise ValueError('Input and output must differ')
    byname=parse_dat(args.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT')['byname']
    source=json.loads((args.workspace/'source-save.json').read_text())
    heroes=[npc for npc in source['worlds']['NEWWORLD'] if npc['player']]
    if len(heroes)!=1:raise ValueError('Expected exactly one source player')
    entries=archive(args.input.read_bytes())
    hero_symbol=byname['PC_HERO']['index']
    paths=[name for name,data in entries.items() if name.startswith('worlds/newworld.zen/npc/')
           and name.endswith('/data') and len(data)>=4 and struct.unpack_from('<I',data)[0]==hero_symbol]
    if len(paths)!=1:raise ValueError('Expected exactly one native player record')
    inventory_path=paths[0][:-4]+'inventory'
    if inventory_path not in entries:raise ValueError('Native player inventory is missing')
    entries[inventory_path],restored=restore_accessories(entries[inventory_path],heroes[0]['items'],byname)
    write_archive(entries,args.output)
    print('Accessory slots restored:',restored)

if __name__=='__main__':main()
