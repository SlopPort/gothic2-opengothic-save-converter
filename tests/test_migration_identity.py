import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from migration_identity import decode_key,map_npcs,source_fingerprint,strip_migration_keys
from native_format import archive,pack_visited_world
from test_validation import string

FINGERPRINT='a'*64

def key(world='NEWWORLD',index=0,fingerprint=FINGERPRINT):
    return struct.pack('<I',1)+string('OGI1:'+fingerprint+':'+world+':'+str(index))

class MigrationIdentityTests(unittest.TestCase):
    def setUp(self):
        self.source={'worlds':{'NEWWORLD':[dict(instance='NPC_A',player=False)]}}
        self.names={'NPC_A':dict(index=7)}
        self.node='worlds/newworld.zen/npc/0/'
        self.entries={self.node+'migration-key':key(),self.node+'data':struct.pack('<I',7)}
    def mapping(self):return map_npcs(self.entries,'NEWWORLD',self.source,FINGERPRINT,self.names)
    def test_identity_is_independent_of_native_index(self):
        self.entries={name.replace('/npc/0/','/npc/21/'):data for name,data in self.entries.items()}
        self.assertEqual(self.mapping()[0][0],'worlds/newworld.zen/npc/21/')
    def test_fingerprint_binds_both_original_inputs(self):
        self.assertNotEqual(source_fingerprint(b'dat',b'source'),source_fingerprint(b'dat2',b'source'))
        self.assertNotEqual(source_fingerprint(b'dat',b'source'),source_fingerprint(b'dat',b'source2'))
    def test_wrong_source_rejected(self):
        self.entries[self.node+'migration-key']=key(fingerprint='b'*64)
        with self.assertRaisesRegex(ValueError,'different source'):self.mapping()
    def test_missing_identity_rejected(self):
        del self.entries[self.node+'migration-key']
        with self.assertRaisesRegex(ValueError,'Missing stable'):self.mapping()
    def test_duplicate_identity_rejected(self):
        self.entries.update({name.replace('/npc/0/','/npc/1/'):data for name,data in list(self.entries.items())})
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.mapping()
    def test_wrong_instance_or_index_rejected(self):
        self.entries[self.node+'data']=struct.pack('<I',8)
        with self.assertRaisesRegex(ValueError,'instance symbol'):self.mapping()
        self.entries[self.node+'data']=struct.pack('<I',7);self.entries[self.node+'migration-key']=key(index=1)
        with self.assertRaisesRegex(ValueError,'outside source'):self.mapping()
    def test_invalid_and_truncated_key(self):
        for data in (b'',struct.pack('<I',2),key()[:-1],key()+b'x',struct.pack('<I',1)+string('invalid')):
            with self.assertRaises(ValueError):decode_key(data)
    def test_player_alias_allowed_in_visited_world(self):
        self.source['worlds']['OLDWORLD']=[];self.source['worlds']['NEWWORLD'][0]['player']=True
        entries={name.replace('newworld.zen','oldworld.zen'):data for name,data in self.entries.items()}
        self.assertEqual(len(map_npcs(entries,'OLDWORLD',self.source,FINGERPRINT,self.names)),1)
        self.source['worlds']['NEWWORLD'][0]['player']=False
        with self.assertRaisesRegex(ValueError,'another world'):map_npcs(entries,'OLDWORLD',self.source,FINGERPRINT,self.names)
    def test_final_output_removes_active_and_nested_markers(self):
        nested={'worlds/oldworld.zen/npc/0/':b'','worlds/oldworld.zen/npc/0/migration-key':key(),
                'worlds/oldworld.zen/npc/0/data':b'preserve'}
        entries={**self.entries,'worlds/oldworld.zen.zip':pack_visited_world(nested)}
        result=strip_migration_keys(entries)
        self.assertNotIn(self.node+'migration-key',result)
        self.assertEqual(archive(result['worlds/oldworld.zen.zip']),{name:data for name,data in nested.items() if not name.endswith('/migration-key')})
        self.assertEqual(result[self.node+'data'],self.entries[self.node+'data'])

if __name__=='__main__':unittest.main()
