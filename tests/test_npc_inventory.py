import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from restore_npcs import restore_npcs,verify_npcs
from native_format import archive,inventory_layout,pack_visited_world
from test_migration_identity import FINGERPRINT,key
from test_validation import world,npc_record,inventory_record,item_record

class NpcInventoryTests(unittest.TestCase):
    def setUp(self):
        self.node='worlds/newworld.zen/npc/0/'
        self.source={'worlds':{'NEWWORLD':[dict(instance='NPC_A',player=False,packed=['ITEM_A:2'],items=[])]}}
        self.names={'NPC_A':dict(index=7),'ITEM_A':dict(index=17),'ITEM_B':dict(index=18)}
        self.entries=world('newworld.zen');self.entries[self.node+'migration-key']=key()
        self.entries[self.node+'inventory']=inventory_record([item_record(17,5),item_record(18)])
    def restore(self,templates=None):return restore_npcs(self.entries,self.source,FINGERPRINT,self.names,templates)
    def test_exact_counts_and_extras_removed(self):
        result,report=self.restore()
        records=inventory_layout(result[self.node+'inventory'])['records']
        self.assertEqual(len(records),1)
        self.assertEqual(struct.unpack_from('<I',records[0]['raw'],records[0]['amount'])[0],2)
        verify_npcs(result,self.source,FINGERPRINT,self.names)
        self.assertEqual(report['worlds']['NEWWORLD']['mapped_records'],1)
    def test_missing_template_discovery_then_retry(self):
        self.source['worlds']['NEWWORLD'][0]['packed']=['ITEM_B:3']
        self.entries[self.node+'inventory']=inventory_record([item_record(17)])
        result,report=self.restore();self.assertIsNone(result);self.assertEqual(report['missing'],['ITEM_B'])
        result,report=self.restore({18:item_record(18)})
        verify_npcs(result,self.source,FINGERPRINT,self.names)
    def test_omitted_empty_inventory_is_supported(self):
        del self.entries[self.node+'inventory'];self.source['worlds']['NEWWORLD'][0]['packed']=[]
        result,report=self.restore();verify_npcs(result,self.source,FINGERPRINT,self.names)
    def test_engine_empty_inventory_entry_is_supported(self):
        self.entries[self.node+'inventory']=b'';self.source['worlds']['NEWWORLD'][0]['packed']=[]
        result,report=self.restore();verify_npcs(result,self.source,FINGERPRINT,self.names)
    def test_duplicate_instance_names_still_map_exact_source_indices(self):
        second=dict(instance='NPC_A',player=False,packed=['ITEM_A:4'],items=[])
        self.source['worlds']['NEWWORLD'].append(second)
        self.entries.update({name.replace('/npc/0/','/npc/1/'):data for name,data in list(self.entries.items()) if '/npc/0/' in name})
        self.entries['worlds/newworld.zen/npc/1/migration-key']=key(index=1)
        result,report=self.restore();verify_npcs(result,self.source,FINGERPRINT,self.names)
        self.assertEqual(report['worlds']['NEWWORLD']['mapped_records'],2)
    def test_verifier_rejects_wrong_amount(self):
        with self.assertRaisesRegex(ValueError,'quantities'):verify_npcs(self.entries,self.source,FINGERPRINT,self.names)
    def test_bad_template_symbol_rejected(self):
        self.source['worlds']['NEWWORLD'][0]['packed']=['ITEM_B:3'];self.entries[self.node+'inventory']=inventory_record()
        with self.assertRaisesRegex(ValueError,'symbol mismatch'):self.restore({18:item_record(17)})

if __name__=='__main__':unittest.main()
