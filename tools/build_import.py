"""Generate a local import mod and append-only Daedalus helpers from your own files."""
import json, struct, pathlib, hashlib
u32 = lambda n: struct.pack('<I', n & 0xffffffff)
import argparse
from dat_symbols import parse_dat
from inventory_restore import source_inventory
from migration_identity import source_fingerprint
from routines import routine_function
from source_coverage import behavior_coverage
P=argparse.ArgumentParser(description=__doc__)
P.add_argument('--game-dir',type=pathlib.Path,required=True)
P.add_argument('--workspace',type=pathlib.Path,required=True)
P.add_argument('--encoding',default='cp1250')
args=P.parse_args()
ROOT=args.workspace.resolve();ROOT.mkdir(parents=True,exist_ok=True)
GAME=args.game_dir.resolve()
parsed=parse_dat(GAME/'_work/Data/Scripts/_compiled/GOTHIC.DAT')
data=parsed['data'];symbols=parsed['symbols'];byname=parsed['byname'];records=parsed['records'];oldcode=parsed['code'];count=parsed['count']
raw = json.loads((ROOT / 'source-save.json').read_text())
def fix(value):
    if isinstance(value, str): return value.encode('latin1').decode(args.encoding, errors='replace')
    if isinstance(value, list): return [fix(x) for x in value]
    if isinstance(value, dict): return {k:fix(v) for k,v in value.items()}
    return value
snapshot = fix(raw)
snapshot['migrationId']=source_fingerprint(data,(ROOT/'source-save.json').read_bytes())
extra_code = bytearray(); assignments = 0
def assign(name, value, index=0):
    global assignments
    s = byname.get(name.upper())
    if s is None or s['type'] != 2 or s['count'] <= index: raise ValueError((name,index,s))
    assignments += 1
    return bytes([64]) + u32(value) + bytes([245]) + u32(s['index']) + bytes([index,9])
def function(name, code, returns=False):
    index = len(records); address = len(oldcode) + len(extra_code)
    records.append(u32(1) + name.encode('ascii') + b'\n' + u32(2 if returns else 0) + u32((5 << 12) | ((3 if returns else 1) << 16)) + bytes(20) + u32(address) + u32(-1))
    symbols.append(dict(index=index,name=name,type=5,count=0,flags=1)); extra_code.extend(code + bytes([60])); return name
gcode = bytearray(); skipped=[]
for name, values in snapshot['symbols']:
    s = byname.get(name.upper())
    if s and s['type'] == 2 and not s['flags'] & (1|4) and len(values) <= s['count']:
        for i,v in enumerate(values): gcode.extend(assign(name,v,i))
    else: skipped.append(name)
function('OGI_IMPORT_GLOBALS',gcode)
for world, npcs in snapshot['worlds'].items():
    for index,n in enumerate(npcs):
        n['routineFunction']=routine_function(raw['worlds'][world][index].get('routine',''),byname)
        c = bytearray([80]); c.extend(u32(byname['SELF']['index']))
        for field,key in [('LEVEL','level'),('EXP','xp'),('EXP_NEXT','xpNext'),('LP','lp'),('GUILD','guild'),('AIVAR','aiVars'),('ATTRIBUTE','attributes'),('PROTECTION','protection'),('HITCHANCE','hitChance')]:
            values=n[key] if isinstance(n[key],list) else [n[key]]
            for i,v in enumerate(values): c.extend(assign('C_NPC.'+field,v,i + (1 if field=='HITCHANCE' else 0)))
        n['migrationKey']=f"OGI1:{snapshot['migrationId']}:{world}:{index}"
        n['helper']=function('OGI_IMPORT_'+world+'_'+str(index),c)
        n['inventory']=source_inventory(n)
        # Preserve raw game encoding in this JSON, because the game UI is not UTF-8.
for field in ['LP','EXP_NEXT','GUILD']:
    function('OGI_GET_'+field,bytes([80])+u32(byname['SELF']['index'])+bytes([65])+u32(byname['C_NPC.'+field]['index']),True)
# Saved by OpenGothic with the other integer globals; distinguishes migrated worlds after reload.
marker_name='OGI_IMPORT_MASK';marker_index=len(records)
records.append(u32(1)+marker_name.encode()+b'\n'+u32(0)+u32(1|(2<<12))+bytes(20)+u32(0)+u32(-1))
symbols.append(dict(index=marker_index,name=marker_name,type=2,count=1,flags=0))
snapshot['skippedSymbols']=skipped
output=ROOT/'generated';mod=output/'og-save-import';mod.mkdir(parents=True,exist_ok=True)
sort_order=sorted(range(len(symbols)),key=lambda i:symbols[i]['name'].encode('latin1'))
patched=data[:1]+u32(len(records))+b''.join(u32(i) for i in sort_order)+b''.join(records)+u32(len(oldcode)+len(extra_code))+oldcode+extra_code
(output/'GOTHIC.DAT').write_bytes(patched)
# The engine expects legacy bytes in strings, represented in JS by Latin-1 codepoints.
# Keep CP1250 only in the human-readable report; use the raw snapshot for game text.
for new,old in zip(snapshot['quests'],raw['quests']): new.update(old)
(mod/'snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=True,separators=(',',':')),encoding='utf8')
(mod/'manifest.json').write_text(json.dumps(dict(id='og-save-import',name='Original save import (experimental)',version='0.1.0',main='index.js',type='script',apiVersion=1,game=['G2']),ensure_ascii=True),encoding='utf8')
hero=next(n for n in snapshot['worlds'][snapshot['world']] if n['player'])
report=dict(sourceSha256=hashlib.sha256(data).hexdigest(),originalSymbols=count,patchedSymbols=len(records),originalBytecode=len(oldcode),addedBytecode=len(extra_code),assignments=assignments,globals=len(snapshot['symbols']),skippedSymbols=skipped,quests=len(snapshot['quests']),infos=len(snapshot['infos']),hero={k:hero[k] for k in ['level','xp','lp','guild','attributes','hitChance']},inventoryKinds=len(hero['inventory']),gold=hero['inventory'].get('ITMI_GOLD'),limitations=['World object, container and trigger state is not imported','NPC AI queues, news, routines and spawn scheduling are not reproduced exactly','World data, calendar, playtime, guild relations and accessory pointers are restored by the subsequent offline finalization stage'])
report['behaviorCoverage']=behavior_coverage(raw)
(output/'build-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
import shutil,secrets
shutil.copyfile(pathlib.Path(__file__).resolve().parents[1]/'mod/index.js',mod/'index.js')
config=mod/'config.json'
if not config.exists():config.write_text(json.dumps(dict(enableRemoteControl=False,remotePort=39843,remoteToken=secrets.token_hex(32)),indent=2))
print('Generated import files in',output)
print('This is an intermediate import; offline finalization is still required.')
