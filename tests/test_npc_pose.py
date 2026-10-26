import math,struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from npc_state import npc_pose_state,restore_npc_pose
from test_validation import npc_record,string

def pose_record():
    return (npc_record()+string('BODY')+string('HEAD')+bytes(16)
            +struct.pack('<8fBi',0,1,2,3,0,1,1,1,0,2)
            +bytes(44*4)+struct.pack('<Qii',0,1,2)+b'opaque AI tail'+bytes(12))

class PoseTests(unittest.TestCase):
    def test_restore_and_preserve_tail(self):
        original=pose_record()
        source=dict(position=[100,200,300],modelScale=[1,2,3],modelFatness=0.5,
                    rotation=[[0,0,1],[0,1,0],[-1,0,0]],guildTrue=4,
                    attitude=3,temporaryAttitude=0,talents=[[1,25,2],[21,8,1]])
        result=restore_npc_pose(original,source);state=npc_pose_state(result)
        self.assertEqual(state['position'],source['position'])
        self.assertEqual(state['angle'],-90)
        self.assertEqual(state['talentSkills'][1],2)
        self.assertEqual(state['talentValues'][21],8)
        self.assertEqual(struct.unpack('<3f',result[-12:]),(100,200,300))
        self.assertEqual(result[state['known_end']:-12],b'opaque AI tail')
        self.assertEqual(restore_npc_pose(result,source),result)
    def test_reject_invalid_vectors_and_talents(self):
        for source in (dict(position=[1,2]),dict(position=[1,math.inf,3]),
                       dict(modelFatness=math.nan),dict(talents=[[22,0,0]]),
                       dict(talents=[[1,0,0],[1,0,0]])):
            with self.subTest(source=source),self.assertRaises(ValueError):
                restore_npc_pose(pose_record(),source)
    def test_missing_physics_position(self):
        with self.assertRaises(ValueError):npc_pose_state(pose_record()[:npc_pose_state(pose_record())['known_end']])

if __name__=='__main__':unittest.main()
