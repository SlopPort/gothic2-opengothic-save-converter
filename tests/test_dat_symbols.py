"""Small synthetic DAT files exercising record boundaries and append-only preservation."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from dat_symbols import parse_dat_bytes

def uint(value):return struct.pack('<I',value&0xffffffff)

def symbol(name,typ=2,count=1,flags=0,payload=b'',parent=-1):
    label=uint(1)+name.encode('ascii')+b'\n' if name is not None else uint(0)
    return label+uint(0)+uint(count|(typ<<12)|(flags<<16))+bytes(20)+payload+uint(parent)

def fixture(records=(),code=b'\x3c'):
    members=[symbol('C_NPC.ATTRIBUTE',2,8,4),*records]
    return b'\x32'+uint(len(members))+b''.join(uint(i) for i in reversed(range(len(members))))+b''.join(members)+uint(len(code))+code

class DatTests(unittest.TestCase):
    def test_numeric_string_function_and_member_records(self):
        records=[symbol('NUMBERS',2,2,payload=struct.pack('<ii',-7,99)),
                 symbol('FLOAT',1,1,payload=struct.pack('<f',1.25)),
                 symbol('TEXT',3,2,payload=b'first\nsecond\n'),
                 symbol('FUNCTION',5,0,1,uint(0)),symbol(None,0,0)]
        data=fixture(records)
        result=parse_dat_bytes(data)
        self.assertEqual(result['records'][1:],records)
        self.assertEqual(result['code'],b'\x3c')
        self.assertEqual(result['byname']['NUMBERS']['index'],1)
        self.assertEqual(result['byname']['C_NPC.ATTRIBUTE']['flags'],4)
        rebuilt=data[:1]+uint(result['count'])+data[5:5+result['count']*4]+b''.join(result['records'])+uint(len(result['code']))+result['code']
        self.assertEqual(rebuilt,data)
    def test_constant_string_extra_newlines(self):
        # ZenKit retries parent reads at endpoint-3, -2, -1, and endpoint.
        for extra in range(1,5):
            record=symbol('TEXT',3,1,1,b'line\n'+b'\n'*extra)
            result=parse_dat_bytes(fixture([record]))
            self.assertEqual(result['records'][1],record)
    def test_unterminated_name(self):
        data=b'\x32'+uint(1)+uint(0)+uint(1)+b'C_NPC.ATTRIBUTE'
        with self.assertRaises(ValueError):parse_dat_bytes(data)
    def test_every_truncated_prefix_rejected(self):
        data=fixture([symbol('INTEGER',2,1,payload=uint(4))])
        for end in range(len(data)):
            with self.subTest(end=end):
                with self.assertRaises(ValueError):parse_dat_bytes(data[:end])
    def test_trailing_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError,'Trailing'):parse_dat_bytes(fixture()+b'x')
    def test_excessive_count(self):
        with self.assertRaises(ValueError):parse_dat_bytes(b'\x32'+uint(0xffffffff))
    def test_missing_game_class(self):
        with self.assertRaisesRegex(ValueError,'NPC attribute'):parse_dat_bytes(b'\x32'+uint(0)+uint(0))
    def test_unsupported_type(self):
        with self.assertRaisesRegex(ValueError,'symbol type'):parse_dat_bytes(fixture([symbol('BAD',15,0)]))
    def test_unrecoverable_constant_boundary(self):
        record=symbol('TEXT',3,1,1,b'line\n',parent=32)
        with self.assertRaisesRegex(ValueError,'boundary'):parse_dat_bytes(fixture([record],b''))
    def test_truncated_constant_lookahead(self):
        record=symbol('TEXT',3,1,1,b'line\n',parent=32)
        data=fixture([record],b'')[:-4]
        with self.assertRaises(ValueError):parse_dat_bytes(data)

if __name__=='__main__':unittest.main()
