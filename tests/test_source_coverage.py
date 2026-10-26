import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from source_coverage import behavior_coverage

class CoverageTests(unittest.TestCase):
    def test_behavior_gaps_are_counted_without_claiming_complete_support(self):
        npc=dict(routine='RTN_START_1',ai=dict(currentValid=True,nextValid=True,respawn=True),news=[{},{}])
        report=behavior_coverage(dict(worlds={'NEWWORLD':[npc],'OLDWORLD':[dict(routine='')]}))
        self.assertEqual(report['npcs'],2);self.assertEqual(report['behaviorMetadataNPCs'],1)
        self.assertEqual(report['pendingExactReconstruction'],dict(currentAIStates=1,queuedNextAIStates=1,newsRecords=2,respawnFlags=1))
        self.assertFalse(report['completeBehaviorCompatibility'])
    def test_legacy_metadata_is_unknown_instead_of_a_full_support_claim(self):
        report=behavior_coverage(dict(worlds={'NEWWORLD':[{}]}))
        self.assertEqual(report['behaviorMetadataNPCs'],0);self.assertFalse(report['completeBehaviorCompatibility'])

if __name__=='__main__':unittest.main()
