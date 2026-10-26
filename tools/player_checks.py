"""Compare final player fields and inventory against the decoded source before publication."""
from collections import Counter
import struct
from accessories import restore_accessories
from inventory_restore import source_inventory
from native_format import inventory_layout
from npc_state import npc_script_state
from spell_slots import restore_spell_slots


def verify_player(entries,source,byname):
    heroes=[npc for npc in source['worlds']['NEWWORLD'] if npc['player']]
    if len(heroes)!=1:raise ValueError('Expected exactly one source player')
    hero=heroes[0];symbol=byname['PC_HERO']['index']
    paths=[name for name,data in entries.items() if name.startswith('worlds/newworld.zen/npc/')
           and name.endswith('/data') and len(data)>=4 and struct.unpack_from('<I',data)[0]==symbol]
    if len(paths)!=1:raise ValueError('Expected exactly one native player')
    native=npc_script_state(entries[paths[0]])
    fields=('attributes','protection','aiVars','level','xp','xpNext','lp','guild')
    mismatches=[key for key in fields if native[key]!=hero[key]]
    if native['hitChance'][1:]!=hero['hitChance']:mismatches.append('hitChance')
    inventory=entries[paths[0][:-4]+'inventory'];counts=Counter()
    for record in inventory_layout(inventory)['records']:
        counts[record['symbol']]+=struct.unpack_from('<I',record['raw'],record['amount'])[0]
    expected=Counter()
    for name,amount in source_inventory(hero).items():
        if name not in byname:raise ValueError('Source inventory symbol is absent from original scripts')
        expected[byname[name]['index']]+=amount
    if counts!=expected:mismatches.append('inventoryAmounts')
    restored,_=restore_accessories(inventory,hero['items'],byname)
    if restored!=inventory:mismatches.append('accessoryPointers')
    if 'spellHotkeys' in hero and restore_spell_slots(inventory,hero['spellHotkeys'],byname)!=inventory:
        mismatches.append('spellShortcuts')
    if mismatches:raise ValueError('Final player differs from source: '+', '.join(mismatches))
