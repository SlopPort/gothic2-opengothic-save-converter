"""Bounded Gothic DAT reader preserving original symbol records and indices."""
from pathlib import Path
import struct
from native_format import Reader


def parse_dat(path):
    return parse_dat_bytes(Path(path).read_bytes())


def parse_dat_bytes(data):
    r=Reader(data)
    r.skip(1)  # Keep the original version byte unchanged in generated files.
    count=r.u()
    r.skip(count*4)  # Original sorted lookup table; records stay in source order.
    records=[];symbols=[];byname={}
    def line():
        start=r.p
        while True:
            value=r.read(1)[0]
            if value in (0,10,13):return data[start:r.p-1]
    for index in range(count):
        start=r.p
        name=line() if r.u() else b''
        vary,props=r.u(),r.u()
        typ=(props>>12)&15;n=props&4095;flags=(props>>16)&63
        if typ>7:raise ValueError('Unsupported DAT symbol type: '+str(typ))
        r.skip(20)
        if not flags&4:
            if typ in (1,2):r.skip(n*4)
            elif typ==3:
                for _ in range(n):line()
            elif typ in (4,5,6,7):r.skip(4)
        parent=r.u()
        # Match the pinned ZenKit workaround while bounding every probe.
        if typ==3 and not flags&4 and flags&1 and parent&255 in b' \t\r\n\v\f':
            endpoint=r.p
            for shift in range(1,5):
                probe=endpoint+shift-4
                if probe>=0 and probe+4<=len(data) and struct.unpack_from('<i',data,probe)[0]==-1:
                    r.p=probe+4
                    break
            else:raise ValueError('Unsupported DAT constant-string boundary')
        name_text=name.upper().decode('latin1')
        symbol=dict(index=index,name=name_text,type=typ,count=n,flags=flags)
        symbols.append(symbol);byname[name_text]=symbol;records.append(data[start:r.p])
    code=r.read(r.u())
    r.end()
    if 'C_NPC.ATTRIBUTE' not in byname:raise ValueError('Missing Gothic II NPC attribute symbol')
    return dict(data=data,symbols=symbols,byname=byname,records=records,code=code,count=count)
