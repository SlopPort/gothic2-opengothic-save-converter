import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from source_validation import validate_source

class SourcePopulationTests(unittest.TestCase):
    def source(self):return dict(world='NEWWORLD',worlds={'NEWWORLD':[dict(player=True)],'OLDWORLD':[dict(player=False)]})
    def test_unique_current_player_is_returned(self):
        s=self.source();self.assertIs(validate_source(s),s['worlds']['NEWWORLD'][0])
    def test_missing_player_is_rejected(self):
        s=self.source();s['worlds']['NEWWORLD'][0]['player']=False
        with self.assertRaisesRegex(ValueError,'exactly one player'):validate_source(s)
    def test_duplicate_or_wrong_world_player_is_rejected(self):
        for current in (True,False):
            s=self.source();s['worlds']['NEWWORLD'][0]['player']=current;s['worlds']['OLDWORLD'][0]['player']=True
            with self.subTest(current=current),self.assertRaisesRegex(ValueError,'exactly one player'):validate_source(s)
    def test_unsupported_scope_is_rejected(self):
        for world in ('OLDWORLD','ADDONWORLD',None):
            s=self.source();s['world']=world
            with self.subTest(world=world),self.assertRaisesRegex(ValueError,'Supported scope'):validate_source(s)
        s=self.source();s['worlds']['ADDONWORLD']=[]
        with self.assertRaisesRegex(ValueError,'Supported scope'):validate_source(s)
    def test_empty_or_missing_world_table_is_rejected(self):
        for worlds in ({},None,[],{'OLDWORLD':[]}):
            with self.subTest(worlds=worlds),self.assertRaises(ValueError):validate_source(dict(world='NEWWORLD',worlds=worlds))
    def test_nonboolean_player_flags_are_not_guessed(self):
        for flag in (0,1,'false',None):
            s=self.source();s['worlds']['NEWWORLD'][0]['player']=flag
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,'boolean'):validate_source(s)
    def test_invalid_population_shape_is_rejected(self):
        for records in ({},None,[None]):
            s=self.source();s['worlds']['OLDWORLD']=records
            with self.subTest(records=records),self.assertRaises(ValueError):validate_source(s)

if __name__=='__main__':unittest.main()
