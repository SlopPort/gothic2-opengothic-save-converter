"""Restore accessory slots without running scripts or applying attribute bonuses."""
from collections import Counter
import struct
from native_format import inventory_layout

NULL=0xffffffff
ACTIVE=0x80000000
BELT=1<<24
AMULET=1<<22
RING=1<<11

def restore_accessories(data,original_items,byname):
    layout=inventory_layout(data)
    records=layout['records']
    desired=[NULL]*4
    restored=[]
    ring=2
    for original in original_items:
        flags=original['flags']&0xffffffff
        if not flags&ACTIVE:continue
        categories=[bool(flags&bit) for bit in (BELT,AMULET,RING)]
        if not any(categories):continue
        if sum(categories)!=1:raise ValueError('Ambiguous source accessory category')
        if flags&BELT:slot=0
        elif flags&AMULET:slot=1
        else:slot=ring;ring+=1
        if slot>=4 or desired[slot]!=NULL:raise ValueError('Too many equipped accessories for a slot')
        name=original['instance'].upper()
        if name not in byname:raise ValueError('Unknown accessory symbol: '+name)
        symbol=byname[name]['index']
        matches=[i for i,record in enumerate(records) if record['symbol']==symbol]
        if len(matches)!=1:raise ValueError('Missing or ambiguous native accessory stack: '+name)
        desired[slot]=matches[0]
        restored.append(name)
    previous=layout['equipment'][1:5]
    affected=set(previous+desired)-{NULL}
    counts=Counter(index for index in desired if index!=NULL)
    other=set(layout['equipment'][:1]+layout['equipment'][5:])-{NULL}
    if affected&other:raise ValueError('Accessory stack is also referenced by a non-accessory equipment slot')
    # A shared stack can back both ring slots; equipped is a count, not a boolean.
    for index in affected:
        amount=struct.unpack_from('<I',records[index]['raw'],records[index]['amount'])[0]
        if counts[index]>amount:raise ValueError('Equipped accessory count exceeds stack amount')
    result=bytearray(data)
    for slot,index in enumerate(desired,1):
        struct.pack_into('<I',result,layout['equipment_offset']+slot*4,index)
    start=4
    for index,record in enumerate(records):
        if index in affected:
            result[start+record['pos']+12]=counts[index]
            result[start+record['pos']+13]=255
        start+=len(record['raw'])
    inventory_layout(result)
    return bytes(result),restored
