"""Restore Gothic II spell-shortcut indices into the pinned native inventory.

The original archive stores 0..7 for keys 3..0. Native numslot[0..7]
uses the same ordering; Item.itSlot stores 3..10 instead.
"""
from collections import Counter
import struct
from native_format import inventory_layout

NULL=0xffffffff

def restore_spell_slots(data,shortcuts,byname):
    layout=inventory_layout(data);records=layout['records'];desired=[NULL]*8
    for name,slot in shortcuts:
        if not isinstance(slot,int) or not 0<=slot<8:raise ValueError('Unsupported source spell shortcut')
        if desired[slot]!=NULL:raise ValueError('Duplicate source spell shortcut')
        name=name.upper()
        if name not in byname:raise ValueError('Unknown source spell item')
        matches=[i for i,record in enumerate(records) if record['symbol']==byname[name]['index']]
        if len(matches)!=1:raise ValueError('Missing or ambiguous native spell stack')
        desired[slot]=matches[0]
    affected=set(layout['equipment'][8:]+desired)-{NULL}
    if affected&(set(layout['equipment'][:8])-{NULL}):
        raise ValueError('Spell stack is also referenced by a non-spell equipment slot')
    equipment=layout['equipment'][:8]+desired;counts=Counter(i for i in equipment if i!=NULL)
    result=bytearray(data)
    for slot,index in enumerate(desired,8):struct.pack_into('<I',result,layout['equipment_offset']+slot*4,index)
    start=4
    for index,record in enumerate(records):
        if index in affected:
            amount=struct.unpack_from('<I',record['raw'],record['amount'])[0]
            if counts[index]>amount:raise ValueError('Assigned spells exceed native stack amount')
            result[start+record['pos']+12]=counts[index]
            slots=[3+i for i,value in enumerate(desired) if value==index]
            result[start+record['pos']+13]=slots[-1] if slots else 255
        start+=len(record['raw'])
    active=layout['active']
    if 3<=active<=10 and layout['equipment'][active+5]!=equipment[active+5]:
        result[layout['equipment_offset']+16*4]=255
    inventory_layout(result)
    return bytes(result)
