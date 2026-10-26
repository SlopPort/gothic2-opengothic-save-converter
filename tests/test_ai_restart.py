import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from npc_ai import npc_ai_prefix,restart_saved_ai,verify_ai_restart,END_OF_TIME
from test_npc_ai import ai_record
from test_validation import string

def restart_record():
    data=ai_record();prefix=data[:npc_ai_prefix(data)['prefix_end']]
    action=struct.pack('<III',47,0xffffffff,0xffffffff)+string('POINT')+struct.pack('<Iii',17,1,2)+string('TEXT')+struct.pack('<i',3)+string('EXTRA')
    queues=struct.pack('<I',1)+action+struct.pack('<II',4,5)+bytes(12)
    tail=struct.pack('<IqqI',1,0,86400000,77)+string('ROUTINE_POINT')+string('FALLBACK')+b'opaque motion'+bytes(12)
    return prefix+queues+tail,tail

class AiRestartTests(unittest.TestCase):
    def setUp(self):
        self.names={name:dict(index=index,type=5,count=0,flags=1) for name,index in (('ZS_TEST',11),('ZS_TEST_LOOP',12),('ZS_TEST_END',13),('ZS_NEXT',14))}
        self.source=dict(ai=dict(currentValid=True,currentName='ZS_TEST',currentIndex=-3,currentIsRoutine=False,nextValid=True,nextName='ZS_NEXT'))
    def test_named_current_state_restarts_without_stale_queues_or_timers(self):
        data,tail=restart_record();result=restart_saved_ai(data,self.source,self.names,999)
        verify_ai_restart(result,self.source,self.names,999)
        state=npc_ai_prefix(result)
        self.assertEqual(state['functions'],[11,12,13]);self.assertEqual(state['calendar_end'],END_OF_TIME)
        self.assertEqual(result[state['prefix_end']+24:],tail)
        self.assertEqual(restart_saved_ai(result,self.source,self.names,999),result)
    def test_next_state_selected_only_without_a_current_state(self):
        data,_=restart_record();self.source['ai']['currentValid']=False
        result=restart_saved_ai(data,self.source,self.names,999)
        self.assertEqual(npc_ai_prefix(result)['functions'],[14,0xffffffff,0xffffffff])
    def test_no_state_preserves_native_fallback_scheduling(self):
        data,_=restart_record();self.source['ai'].update(currentValid=False,nextValid=False)
        result=restart_saved_ai(data,self.source,self.names,999)
        self.assertEqual(npc_ai_prefix(result)['functions'],[0xffffffff]*3)
    def test_routine_calendar_deadline_is_preserved(self):
        data,_=restart_record();self.source['ai']['currentIsRoutine']=True
        result=restart_saved_ai(data,self.source,self.names,999)
        self.assertEqual(npc_ai_prefix(result)['calendar_end'],1000)
    def test_unknown_or_external_callbacks_fail(self):
        data,_=restart_record()
        for key,value in (('type',2),('count',1),('flags',8)):
            self.names['ZS_TEST'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):restart_saved_ai(data,self.source,self.names,999)
            self.setUp()
        del self.names['ZS_TEST']
        with self.assertRaises(ValueError):restart_saved_ai(data,self.source,self.names,999)
    def test_truncated_or_oversized_queues_fail(self):
        data,_=restart_record();end=npc_ai_prefix(data)['prefix_end']
        for bad in (data[:end],data[:end]+struct.pack('<I',0xffffffff)):
            with self.assertRaises(ValueError):restart_saved_ai(bad,self.source,self.names,999)
    def test_verifier_detects_corrupted_state(self):
        data,_=restart_record();result=bytearray(restart_saved_ai(data,self.source,self.names,999))
        struct.pack_into('<I',result,npc_ai_prefix(result)['functions_offset'],100)
        with self.assertRaises(ValueError):verify_ai_restart(result,self.source,self.names,999)
    def test_dead_npc_initialization_is_not_run_twice(self):
        data,_=restart_record();self.source['attributes']=[0]
        self.assertEqual(restart_saved_ai(data,self.source,self.names,999),data)
        verify_ai_restart(data,self.source,self.names,999)

if __name__=='__main__':unittest.main()
