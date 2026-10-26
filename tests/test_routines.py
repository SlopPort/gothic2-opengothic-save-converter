import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from routines import routine_function

class RoutineTests(unittest.TestCase):
    def setUp(self):self.names={'RTN_START_1':dict(type=5,count=0,flags=1)}
    def test_internal_routine_is_resolved(self):self.assertEqual(routine_function('rtn_start_1',self.names),'RTN_START_1')
    def test_missing_and_archive_sentinel_have_no_callback(self):
        for value in ('','\xffINSTANCE_HELP'):self.assertIsNone(routine_function(value,self.names))
    def test_unknown_names_and_wrong_signatures_fail(self):
        for name in ('RTN_MISSING','ZS_ATTACK','\xffSOMETHING','RTN_A;CALL()'):
            with self.subTest(name=name),self.assertRaises(ValueError):routine_function(name,self.names)
        for key,value in (('type',2),('count',1),('flags',8),('flags',4)):
            self.names['RTN_START_1'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):routine_function('RTN_START_1',self.names)
            self.setUp()

if __name__=='__main__':unittest.main()
