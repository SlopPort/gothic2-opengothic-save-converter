import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from npc_state import npc_script_state,restore_npc_script_state,verify_npc_script_state
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

class NpcRestoreTests(unittest.TestCase):
    def test_restore_fields_without_changing_opaque_tail(self):
        data=npc_record()+b'opaque AI and movement payload'
        source=dict(attributes=[1,2,3,4,5,6,7,8],protection=list(range(8)),hitChance=[11,22,33,44],
                    aiVars=list(range(100)),flags=5,guild=3,level=2,xp=8,xpNext=9,lp=10)
        result=restore_npc_script_state(data,source)
        verify_npc_script_state(result,source)
        self.assertEqual(result[len(npc_record()):],b'opaque AI and movement payload')
        self.assertEqual(npc_script_state(result)['hitChance'][0],0)
        self.assertEqual(restore_npc_script_state(result,source),result)
    def test_invalid_array_lengths_rejected(self):
        for field in ('attributes','protection','aiVars','hitChance'):
            with self.assertRaises(ValueError):restore_npc_script_state(npc_record(),{field:[]})
    def test_verifier_detects_field_mismatch(self):
        with self.assertRaisesRegex(ValueError,'xp'):verify_npc_script_state(npc_record(),dict(xp=999))

if __name__=='__main__':unittest.main()
