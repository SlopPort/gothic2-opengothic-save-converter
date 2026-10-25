"""Restore supported world state into a separate OpenGothic save. Input files remain unchanged."""
from pathlib import Path
import struct,json,math
from native_format import Reader,item,inventory,archive,pack_visited_world,write_archive
from script_state import restore_guild_table
from dat_symbols import parse_dat
import argparse
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('--game-dir',type=Path,required=True);P.add_argument('--workspace',type=Path,required=True)
P.add_argument('--input',type=Path,required=True);P.add_argument('--output',type=Path,required=True)
args=P.parse_args();ROOT=args.workspace.resolve()
if args.input.resolve()==args.output.resolve():raise ValueError('Input and output must differ')
source=args.input
entries=archive(source.read_bytes());worlds={}
header=entries['header']
if not header.startswith(b'OpenGothic/Save\0') or struct.unpack_from('<H',header,len(b'OpenGothic/Save\0'))[0]!=56:
 raise ValueError('Only the tested OpenGothic format 56 is supported')
original=json.loads((ROOT/'source-save.json').read_text())
if original['world']!='NEWWORLD' or set(original['worlds'])-{'NEWWORLD','OLDWORLD'}:
 raise ValueError('This prototype supports a New World save with New World/Old World data only')
for key in ('NEWWORLD','OLDWORLD'):
 if key not in original['worlds']:continue
 name=key.lower()+'.zen'
 worlds[key]=archive(entries['worlds/'+name+'.zip']) if key=='OLDWORLD' else {n:v for n,v in entries.items() if n.startswith('worlds/'+name+'/')}
parsed=parse_dat(args.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT')
byname=parsed['byname']
templates={}
for key,files in worlds.items():
 for name,b in files.items():
  if name.endswith('/inventory'):
   for rec in inventory(b):templates.setdefault(rec['symbol'],rec)
  elif name.endswith('/items'):
   r=Reader(b)
   for _ in range(r.u()):
    rec=item(r);templates.setdefault(rec['symbol'],rec)
   r.end()
state=json.loads((ROOT/'world-state.json').read_text())
needed={i['instance'].upper() for vobs in state.values() for v in vobs for i in v.get('items',[])}
needed|={v['item'].upper() for vobs in state.values() for v in vobs if 'item' in v}
for p in (ROOT/'item-templates').glob('*.item'):
 r=Reader(p.read_bytes());rec=item(r);r.end();templates[rec['symbol']]=rec
missing=sorted(n for n in needed if n not in byname or byname[n]['index'] not in templates)
(ROOT/'world-item-coverage.json').write_text(json.dumps(dict(templates=len(templates),needed=len(needed),missing=missing),indent=2))
if missing:raise ValueError('Missing item templates: '+', '.join(missing))
def pack_s(v):return struct.pack('<I',len(v))+v
def native_item(name,amount,pos=None,rot=None):
 rec=templates[byname[name.upper()]['index']];b=bytearray(rec['raw']);struct.pack_into('<I',b,rec['amount'],max(1,amount))
 pos=pos or [0.,0.,0.];rot=rot or [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
 struct.pack_into('<3fBB',b,rec['pos'],*pos,0,255)
 matrix=[*rot[0],0.,*rot[1],0.,*rot[2],0.,*pos,1.]
 struct.pack_into('<16f',b,rec['matrix'],*matrix);return bytes(b)
def make_inventory(items):
 records=[native_item(i['instance'],i['amount']) for i in items if i['amount']>0]
 return struct.pack('<I',len(records))+b''.join(records)+struct.pack('<I',0)+(struct.pack('<II',0,0xffffffff)*2)+struct.pack('<16IBii',*([0xffffffff]*16),255,0,0)
report={}
for key,files in worlds.items():
 containers=[v for v in state[key] if v.get('container')];doors=[v for v in state[key] if v.get('door')]
 candidates=[]
 for n,b in files.items():
  if not n.endswith('/data') or '/mobsi/' not in n or len(b)<=129 or b[0] not in {v['type'] for v in containers+doors}:continue
  r=Reader(b,129);name,focus,visual=r.s(),r.s(),r.s();r.skip(24);r.s();r.skip(2+4)
  for _ in range(4):r.s()
  lock=r.p;r.skip(1);r.s();r.s();end=r.p
  candidates.append(dict(path=n,b=b,pos=struct.unpack_from('<3f',b,49),visual=visual.decode('latin1').upper(),lock=lock,end=end,type=b[0]))
 used=set();matches=[]
 for v in containers+doors:
  possible=[c for c in candidates if c['path'] not in used and c['type']==v['type']]
  if not possible:raise ValueError('No native container/door candidate in '+key)
  c=min(possible,key=lambda c:sum((a-b)**2 for a,b in zip(c['pos'],v['pos'])))
  dist=math.dist(c['pos'],v['pos'])
  if dist>=1:raise ValueError('Native container/door candidate is too distant in '+key)
  used.add(c['path']);b=c['b'];r=Reader(b,c['lock']+1);oldkey=r.s();oldpick=r.s()
  keystr=v.get('key',oldkey.decode('latin1')).encode('latin1');pick=v.get('pick',oldpick.decode('latin1')).encode('latin1')
  files[c['path']]=b[:c['lock']]+bytes([v['locked']])+pack_s(keystr)+pack_s(pick)+b[c['end']:]
  if v.get('container'):
   inv=make_inventory(v['items']);inventory(inv);files[c['path'][:-4]+'inventory']=inv
  matches.append(dict(original=v['id'],native=c['path'],distance=dist))
 trigger_matches=[];trigger_skipped=[];trigger_used=set()
 for v in [v for v in state[key] if v.get('trigger') and not v.get('mover')]:
  possible=[]
  for n,b in files.items():
   if n.endswith('/data') and '/mobsi/' in n and len(b)>146 and b[0]==v['type'] and n not in trigger_used:
    pos=struct.unpack_from('<3f',b,49);dist=math.dist(pos,v['pos'])
    if dist<1:possible.append((dist,n,b))
  if len(possible)!=1:trigger_skipped.append(v['name']);continue
  dist,n,b=possible[0];trigger_used.add(n);r=Reader(b,129);r.skip(r.u()*4);emit=r.p
  b=bytearray(b)
  if v['maximum']>0:struct.pack_into('<I',b,emit,max(0,int(v['maximum'])-v['remaining']))
  b[emit+4]=int(not v['enabled']);files[n]=bytes(b);trigger_matches.append(v['name'])
 base=json.loads((ROOT/'base-world-state.json').read_text())[key]
 source_ids={v['id']:v for v in state[key]};mover_matches=[]
 def matrix(v):return [*v['rot'][0],0.,*v['rot'][1],0.,*v['rot'][2],0.,*v['pos'],1.]
 for v in [v for v in state[key] if v.get('mover')]:
  bs=[x for x in base if x.get('mover') and x['name']==v['name']]
  if len(bs)!=1:continue
  n=f"worlds/{key.lower()}.zen/mobsi/{bs[0]['id']}/data";b=bytearray(files[n])
  if len(b)<245:raise ValueError('Truncated native mover data')
  global_m=matrix(v);parent=source_ids.get(v.get('parent'))
  if parent:
   pr=parent['rot'];cr=v['rot'];delta=[a-b for a,b in zip(v['pos'],parent['pos'])]
   lr=[[sum(pr[row][j]*cr[col][j] for j in range(3)) for row in range(3)] for col in range(3)]
   lp=[sum(pr[col][j]*delta[j] for j in range(3)) for col in range(3)]
   local_m=matrix(dict(rot=lr,pos=lp))
  else:local_m=global_m
  struct.pack_into('<16f',b,1,*global_m);struct.pack_into('<16f',b,65,*local_m)
  original_state=v['moverState'];native_state=b[-17]
  if original_state in (0,2):native_state=0
  elif native_state!=1:native_state=2 if original_state==1 else 4
  tick=struct.unpack_from('<Q',entries['game/session'])[0]
  struct.pack_into('<BQII',b,len(b)-17,native_state,tick,v['frame'],v['frame'] if native_state==0 else max(0,v['nextFrame']))
  # AbstractTrigger's last byte records whether the mover is ticked.
  b[-82]=int(native_state!=0)
  files[n]=bytes(b);mover_matches.append(v['name'])
 loose=[v for v in state[key] if 'item' in v and v['amount']>0]
 records=[native_item(v['item'],v['amount'],v['pos'],v['rot']) for v in loose]
 path='worlds/'+key.lower()+'.zen/items';files[path]=struct.pack('<I',len(records))+b''.join(records)
 r=Reader(files[path])
 if r.u()!=len(loose):raise ValueError('Loose-item count mismatch')
 for _ in loose:item(r)
 r.end()
 report[key]=dict(loose_items=len(loose),containers=len(containers),doors=len(doors),container_stacks=sum(len(v['items']) for v in containers),matches=matches,triggers_restored=trigger_matches,triggers_unmatched=trigger_skipped,movers_restored=mover_matches)
 if key=='NEWWORLD':entries.update(files)
 else:
  entries['worlds/oldworld.zen.zip']=pack_visited_world(files)
# Restore the original guild relationship table without changing the extra engine guilds.
entries['game/quests']=restore_guild_table(entries['game/quests'],(ROOT/'guild-attitudes.bin').read_bytes())
h=entries['header'];r=Reader(h,len(b'OpenGothic/Save\0')+2);r.s();entries['header']=h[:len(b'OpenGothic/Save\0')+2]+pack_s(b'ORIGINAL SAVE IMPORT (EXPERIMENTAL)')+h[r.p:]
output=args.output
write_archive(entries,output)
(ROOT/'world-conversion-report.json').write_text(json.dumps(report,indent=2))
print('Written',output,output.stat().st_size)
for k,v in report.items():print(k,{n:x for n,x in v.items() if n not in ('matches','triggers_restored','movers_restored')})
