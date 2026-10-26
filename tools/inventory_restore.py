"""Reconcile native inventory amounts and indices without running item scripts."""
from collections import Counter
import struct
from native_format import inventory_layout,Reader,item

NULL=0xffffffff

def source_inventory(npc):
    counts=Counter()
    for packed in npc['packed']:
        for part in packed.split(','):
            if ':' not in part:continue
            name,amount=part.rsplit(':',1)
            count=int(amount)
            if count<0:raise ValueError('Negative packed inventory amount')
            if count:counts[name.upper()]+=count
    for item in npc['items']:
        counts[item['instance'].upper()]+=max(1,item['amount'])
    return dict(counts)

def reconcile_inventory(data,counts,clear_accessories=False,templates=None):
    layout=inventory_layout(data)
    for symbol,amount in counts.items():
        if not isinstance(symbol,int) or not isinstance(amount,int) or not 0<amount<=0xffffffff:
            raise ValueError('Invalid desired inventory amount or symbol')
    symbols={};mapping={};records=[]
    for old,record in enumerate(layout['records']):
        symbol=record['symbol']
        if symbol not in counts:continue
        if symbol in symbols:raise ValueError('Ambiguous duplicate native inventory stack')
        symbols[symbol]=len(records);mapping[old]=len(records);records.append(record)
    for symbol in counts:
        if symbol in symbols:continue
        if templates is None or symbol not in templates:raise ValueError('Source inventory item is missing from native templates')
        raw=templates[symbol]
        r=Reader(raw);record=item(r);r.end()
        if record['symbol']!=symbol:raise ValueError('Native item template symbol mismatch')
        symbols[symbol]=len(records);records.append(record)
    def remap(index):return mapping.get(index,NULL)
    equipment=[remap(index) for index in layout['equipment']]
    if clear_accessories:equipment[1:5]=[NULL]*4
    equipped=Counter(index for index in equipment if index!=NULL)
    output=[]
    for index,record in enumerate(records):
        amount=counts[record['symbol']]
        if equipped[index]>amount:raise ValueError('Equipment references exceed desired inventory amount')
        raw=bytearray(record['raw']);struct.pack_into('<I',raw,record['amount'],amount)
        raw[record['pos']+12]=equipped[index]
        if not equipped[index]:raw[record['pos']+13]=255
        output.append(raw)
    def string(value):return struct.pack('<I',len(value))+value
    result=bytearray(struct.pack('<I',len(output))+b''.join(output)+struct.pack('<I',len(layout['models'])))
    for name,index in layout['models']+layout['attachments']:
        result+=string(name)+struct.pack('<I',remap(index))
    active=layout['active']
    slot=5 if active==1 else 6 if active==2 else active+5 if 3<=active<=10 else None
    if slot is not None and equipment[slot]==NULL:active=255
    current=layout['current'] if layout['current'] in counts else 0
    state=layout['state'] if layout['state'] in counts else 0
    result+=struct.pack('<16IBii',*equipment,active,current,state)
    inventory_layout(result)
    return bytes(result)


def empty_inventory():
    return struct.pack('<II',0,0)+struct.pack('<II',0,NULL)*2+struct.pack('<16IBii',*([NULL]*16),255,0,0)
