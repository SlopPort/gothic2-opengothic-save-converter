import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from npc_ai import npc_ai_prefix,rebase_npc_calendar,rebase_world_calendars,END_OF_TIME
from native_format import archive,pack_visited_world
from test_npc_pose import pose_record
from test_validation import npc_record,inventory_record,string

def ai_record(end=1000,transform=False):
    pose=pose_record()[:-len(b'opaque AI tail')-12]
    tr=(npc_record()+inventory_record()+bytes(44*4)+string('BODY')+string('HEAD')+bytes(16)+string('SKELETON')) if transform else b''
    return (pose+bytes(16+33*4+30)+bytes([transform])+tr+struct.pack('<4QB3IQqBQI',10,20,30,40,0,1,2,3,50,end,1,60,4)
            +b'opaque queues/routines/movement'+bytes(12))

class AiCalendarTests(unittest.TestCase):
    def test_changes_only_calendar_deadline(self):
        data=ai_record();state=npc_ai_prefix(data)
        result,changed=rebase_npc_calendar(data,86400000)
        self.assertTrue(changed);self.assertEqual(npc_ai_prefix(result)['calendar_end'],86401000)
        offset=state['calendar_offset']
        self.assertEqual(result[:offset],data[:offset]);self.assertEqual(result[offset+8:],data[offset+8:])
    def test_infinite_and_zero_shift_preserve_bytes(self):
        for data,delta in ((ai_record(END_OF_TIME),100),(ai_record(),0)):
            self.assertEqual(rebase_npc_calendar(data,delta),(data,False))
    def test_transformed_npc_embedded_state_is_skipped(self):
        data=ai_record(transform=True);result,changed=rebase_npc_calendar(data,-500)
        self.assertTrue(changed);self.assertEqual(npc_ai_prefix(result)['calendar_end'],500)
    def test_overflow_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'overflow'):rebase_npc_calendar(ai_record(END_OF_TIME-1),1)
        with self.assertRaisesRegex(ValueError,'overflow'):rebase_npc_calendar(ai_record(-(1<<63)),-1)
    def test_nested_and_invalid_npcs_are_rebased(self):
        path='worlds/newworld.zen/npc_invalid/0/data';old='worlds/oldworld.zen/npc/0/data'
        e={path:ai_record(), 'worlds/oldworld.zen.zip':pack_visited_world({old:ai_record()})}
        result,count=rebase_world_calendars(e,500)
        self.assertEqual(count,2);self.assertEqual(npc_ai_prefix(result[path])['calendar_end'],1500)
        self.assertEqual(npc_ai_prefix(archive(result['worlds/oldworld.zen.zip'])[old])['calendar_end'],1500)
    def test_truncated_prefixes_are_rejected(self):
        data=ai_record();end=npc_ai_prefix(data)['prefix_end']
        for size in range(end):
            with self.subTest(size=size),self.assertRaises(ValueError):npc_ai_prefix(data[:size])

if __name__=='__main__':unittest.main()
