"""Read the Gothic DAT symbol table while preserving original records and indices."""
from pathlib import Path
import struct

def parse_dat(path):
    data = Path(path).read_bytes()
    p = 1
    def uint():
        nonlocal p
        v = struct.unpack_from('<I', data, p)[0]; p += 4; return v
    def line():
        nonlocal p
        start = p
        while data[p] not in (0, 10, 13): p += 1
        v = data[start:p]; p += 1; return v
    count = uint(); p += count * 4
    records = []; symbols = []; byname = {}
    for i in range(count):
        start = p; name = line() if uint() else b''
        vary, props = uint(), uint(); typ = (props >> 12) & 15; n = props & 4095; flags = (props >> 16) & 63
        p += 20
        if not flags & 4:
            if typ in (1, 2): p += n * 4
            elif typ == 3:
                for _ in range(n): line()
            elif typ in (4, 5, 6, 7): p += 4
        parent = uint()
        # Mirror ZenKit's workaround for newline bytes in constant-string parent data.
        if typ == 3 and not flags & 4 and flags & 1 and parent & 255 in b' \t\r\n\v\f':
            endpoint = p
            for k in range(1, 5):
                if struct.unpack_from('<i', data, endpoint + k - 3)[0] == -1:
                    p = endpoint + k + 1; break
            else: raise ValueError('Unsupported string boundary')
        name_text = name.upper().decode('latin1')
        sym = dict(index=i, name=name_text, type=typ, count=n, flags=flags)
        symbols.append(sym); byname[name_text] = sym; records.append(data[start:p])
    code_len = uint(); oldcode = data[p:p+code_len]
    assert p + code_len == len(data), (p, code_len, len(data))
    assert len(symbols) == count and 'C_NPC.ATTRIBUTE' in byname
    return dict(data=data, symbols=symbols, byname=byname, records=records, code=oldcode, count=count)
