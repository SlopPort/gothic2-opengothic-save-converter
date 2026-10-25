"""Restore accessory equipment pointers without applying stat bonuses twice."""
from pathlib import Path
import json,struct,zipfile,sys
from native_format import Reader,item
from dat_symbols import parse_dat
import argparse
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('--game-dir',type=Path,required=True);P.add_argument('--workspace',type=Path,required=True)
P.add_argument('--input',type=Path,required=True);P.add_argument('--output',type=Path,required=True)
args=P.parse_args();ROOT=args.workspace.resolve()
if args.input.resolve()==args.output.resolve():raise ValueError('Input and output must differ')
byname=parse_dat(args.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT')['byname']
source=json.loads((ROOT/'source-save.json').read_text());hero=next(x for x in source['worlds']['NEWWORLD'] if x['player'])
with zipfile.ZipFile(args.input) as z:entries={n:z.read(n) for n in z.namelist()}
hero_symbol=byname['PC_HERO']['index'];paths=[n for n,b in entries.items() if '/npc/' in n and n.endswith('/data') and struct.unpack_from('<I',b)[0]==hero_symbol];assert len(paths)==1,paths
inv_path=paths[0][:-4]+'inventory';b=bytearray(entries[inv_path]);r=Reader(b);records=[item(r) for _ in range(r.u())]
for _ in range(r.u()):r.s();r.skip(4)
for _ in range(2):r.s();r.skip(4)
ptrs=r.p;restored=[];ring=3
for original in hero['items']:
 flags=original['flags']&0xffffffff
 if not flags&0x80000000:continue
 name=original['instance'];slot=1 if flags&(1<<24) else 2 if flags&(1<<22) else ring if flags&(1<<11) else None
 if slot is None:continue
 if flags&(1<<11):ring+=1
 assert slot<=4
 matches=[(i,x) for i,x in enumerate(records) if x['symbol']==byname[name]['index']];assert len(matches)==1,name
 i,rec=matches[0];struct.pack_into('<I',b,ptrs+slot*4,i)
 # Item.equipped follows amount and position. Accessory slots are not hotbar slots.
 start=sum(len(x['raw']) for x in records[:i])+4;b[start+rec['pos']+12]=1;b[start+rec['pos']+13]=255
 restored.append(name)
entries[inv_path]=bytes(b)
with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for n,data in entries.items():z.writestr(n,data)
with zipfile.ZipFile(args.output) as z:assert z.testzip() is None
print('Accessory slots restored:',restored)
