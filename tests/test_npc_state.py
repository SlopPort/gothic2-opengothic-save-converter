import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from npc_state import npc_script_state
from test_validation import npc_record

class NpcStateTests(unittest.TestCase):
    def test_prefix_fields_and_opaque_tail(self):
        data=npc_record()
        report=npc_script_state(data+b'opaque movement/AI state')
        self.assertEqual(report['symbol'],7)
        self.assertEqual(report['attributes'],[40,80,10,20,15,12,0,0])
        self.assertEqual((report['guild'],report['level'],report['xp'],report['xpNext'],report['lp']),(2,14,100,200,8))
        self.assertEqual(report['prefix_size'],len(data))
    def test_every_truncated_prefix(self):
        data=npc_record()
        for end in range(len(data)):
            with self.subTest(end=end):
                with self.assertRaises(ValueError):npc_script_state(data[:end])

if __name__=='__main__':unittest.main()
