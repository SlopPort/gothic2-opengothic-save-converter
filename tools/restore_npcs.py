"""Restore source NPC inventory quantities using stable migration identities."""
import argparse,json,struct
from collections import Counter
from pathlib import Path
from accessories import restore_accessories
from dat_symbols import parse_dat
from inventory_restore import empty_inventory,reconcile_inventory,source_inventory
from migration_identity import map_npcs,source_fingerprint
from native_format import Reader,archive,inventory,item,pack_visited_world,write_archive
from npc_state import restore_npc_script_state,verify_npc_script_state,restore_npc_pose
from spell_slots import restore_spell_slots
from npc_ai import restart_saved_ai,verify_ai_restart


def restore_npcs(entries,source,fingerprint,byname,extra_templates=None,restart_ai=False):
    if restart_ai and any('ai' not in npc for records in source['worlds'].values() for npc in records):
        raise ValueError('Saved AI restart requires a fresh source export containing AI metadata')
    worlds={}
    for world in source['worlds']:
        name=world.lower()+'.zen'
        worlds[world]=archive(entries['worlds/'+name+'.zip']) if world!='NEWWORLD' else {
            path:data for path,data in entries.items() if path.startswith('worlds/'+name+'/')}
    mappings={world:map_npcs(files,world,source,fingerprint,byname) for world,files in worlds.items()}
    templates=dict(extra_templates or {})
    for files in worlds.values():
        for path,data in files.items():
            if path.endswith('/inventory') and data:
                for record in inventory(data):templates.setdefault(record['symbol'],record['raw'])
            elif path.endswith('/items'):
                r=Reader(data)
                for _ in range(r.u()):
                    record=item(r);templates.setdefault(record['symbol'],record['raw'])
                r.end()
    missing=set()
    for records in mappings.values():
        for _,npc in records:
            for name in source_inventory(npc):
                if name not in byname or byname[name]['index'] not in templates:missing.add(name)
    if missing:return None,dict(missing=sorted(missing))
    result=dict(entries);report={}
    ticks=struct.unpack_from('<Q',entries['game/session'])[0] if restart_ai else None
    for world,files in worlds.items():
        changed=0
        for node,npc in mappings[world]:
            files[node+'data']=restore_npc_script_state(files[node+'data'],npc,byname)
            if any(name in npc for name in ('position','guildTrue','talents')):
                files[node+'data']=restore_npc_pose(files[node+'data'],npc)
            if restart_ai and 'ai' in npc:files[node+'data']=restart_saved_ai(files[node+'data'],npc,byname,ticks)
            wanted={byname[name]['index']:amount for name,amount in source_inventory(npc).items()}
            before=files.get(node+'inventory') or empty_inventory()
            restored=reconcile_inventory(before,wanted,clear_accessories=True,templates=templates)
            restored,_=restore_accessories(restored,npc['items'],byname)
            if 'spellHotkeys' in npc:restored=restore_spell_slots(restored,npc['spellHotkeys'],byname)
            changed+=before!=restored
            files[node+'inventory']=restored
        report[world]=dict(source_npcs=len(source['worlds'][world]),mapped_records=len(mappings[world]),inventories_changed=changed)
        if world=='NEWWORLD':result.update(files)
        else:result['worlds/'+world.lower()+'.zen.zip']=pack_visited_world(files)
    return result,dict(missing=[],worlds=report)


def verify_npcs(entries,source,fingerprint,byname,restart_ai=False):
    if restart_ai and any('ai' not in npc for records in source['worlds'].values() for npc in records):
        raise ValueError('Saved AI restart requires source AI metadata for every NPC')
    ticks=struct.unpack_from('<Q',entries['game/session'])[0] if restart_ai else None
    for world in source['worlds']:
        files=entries if world=='NEWWORLD' else archive(entries['worlds/'+world.lower()+'.zen.zip'])
        for node,npc in map_npcs(files,world,source,fingerprint,byname):
            verify_npc_script_state(files[node+'data'],npc,byname)
            if restart_ai and 'ai' in npc:verify_ai_restart(files[node+'data'],npc,byname,ticks)
            if any(name in npc for name in ('position','guildTrue','talents')) and restore_npc_pose(files[node+'data'],npc)!=files[node+'data']:
                raise ValueError('NPC pose, attitudes, or talents differ from source')
            data=files.get(node+'inventory') or empty_inventory();actual=Counter()
            for record in inventory(data):
                actual[record['symbol']]+=struct.unpack_from('<I',record['raw'],record['amount'])[0]
            desired=Counter({byname[name]['index']:amount for name,amount in source_inventory(npc).items()})
            if actual!=desired:raise ValueError('NPC inventory quantities differ from source')
            restored,_=restore_accessories(data,npc['items'],byname)
            if restored!=data:raise ValueError('NPC accessory pointers differ from source')
            if 'spellHotkeys' in npc and restore_spell_slots(data,npc['spellHotkeys'],byname)!=data:
                raise ValueError('NPC spell shortcuts differ from source')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('game-dir','workspace','input','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--restart-saved-ai',action='store_true',help='Experimental restart of saved AI entrypoints; does not resume original queues')
    args=parser.parse_args()
    if args.input.resolve()==args.output.resolve():raise ValueError('Input and output must differ')
    original_dat=(args.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT').read_bytes()
    source_bytes=(args.workspace/'source-save.json').read_bytes();source=json.loads(source_bytes)
    byname=parse_dat(args.game_dir/'_work/Data/Scripts/_compiled/GOTHIC.DAT')['byname']
    templates={}
    for path in (args.workspace/'item-templates').glob('*.item'):
        raw=path.read_bytes();r=Reader(raw);record=item(r);r.end();templates[record['symbol']]=raw
    result,report=restore_npcs(archive(args.input.read_bytes()),source,source_fingerprint(original_dat,source_bytes),byname,templates,args.restart_saved_ai)
    (args.workspace/'npc-item-coverage.json').write_text(json.dumps(report,indent=2))
    if result is None:raise ValueError('Missing NPC inventory item templates; see npc-item-coverage.json')
    write_archive(result,args.output)
    print('Restored source inventory quantities for all identified NPC records')

if __name__=='__main__':main()
