"""Accessory restoration fixtures contain no original game data."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from accessories import ACTIVE,AMULET,BELT,RING,restore_accessories
from native_format import inventory_layout
from test_validation import NULL,inventory_record,item_record

class AccessoryTests(unittest.TestCase):
    symbols={'RING_A':{'index':17},'RING_B':{'index':18},'BELT_A':{'index':19},'AMULET_A':{'index':20}}
    def original(self,name,flag):return dict(instance=name,flags=ACTIVE|flag,amount=1)
    def equipped_counts(self,data):
        return [record['raw'][record['pos']+12] for record in inventory_layout(data)['records']]
    def test_two_identical_rings_share_stack(self):
        data=inventory_record([item_record(17,2)])
        result,names=restore_accessories(data,[self.original('RING_A',RING)]*2,self.symbols)
        self.assertEqual(inventory_layout(result)['equipment'][1:5],[NULL,NULL,0,0])
        self.assertEqual(self.equipped_counts(result),[2])
        self.assertEqual(names,['RING_A','RING_A'])
    def test_insufficient_stack_rejected_without_mutation(self):
        data=bytearray(inventory_record([item_record(17,1)]));before=bytes(data)
        with self.assertRaisesRegex(ValueError,'exceeds'):
            restore_accessories(data,[self.original('RING_A',RING)]*2,self.symbols)
        self.assertEqual(bytes(data),before)
    def test_replaces_old_accessory_and_is_idempotent(self):
        old=bytearray(item_record(17));old[-66]=1
        data=inventory_record([bytes(old),item_record(18)],equipment=[NULL,NULL,NULL,0,NULL]+[NULL]*11)
        original=[self.original('ring_b',RING)]
        result,_=restore_accessories(data,original,self.symbols)
        self.assertEqual(inventory_layout(result)['equipment'][1:5],[NULL,NULL,1,NULL])
        self.assertEqual(self.equipped_counts(result),[0,1])
        self.assertEqual(restore_accessories(result,original,self.symbols)[0],result)
    def test_unequipped_accessories_clear_old_slots(self):
        data=inventory_record([item_record()],equipment=[NULL,NULL,NULL,0,NULL]+[NULL]*11)
        result,names=restore_accessories(data,[dict(instance='RING_A',flags=RING)],self.symbols)
        self.assertEqual(inventory_layout(result)['equipment'][1:5],[NULL]*4)
        self.assertEqual(self.equipped_counts(result),[0])
        self.assertEqual(names,[])
    def test_all_accessories_preserve_non_accessory_record(self):
        weapon=item_record(99)
        data=inventory_record([item_record(19),item_record(20),item_record(17),item_record(18),weapon],equipment=[NULL]*5+[4]+[NULL]*10)
        original=[self.original('BELT_A',BELT),self.original('AMULET_A',AMULET),self.original('RING_A',RING),self.original('RING_B',RING)]
        result,_=restore_accessories(data,original,self.symbols)
        layout=inventory_layout(result)
        self.assertEqual(layout['equipment'][1:6],[0,1,2,3,4])
        self.assertEqual(layout['records'][4]['raw'],weapon)
    def test_duplicate_belts_rejected(self):
        with self.assertRaisesRegex(ValueError,'Too many'):
            restore_accessories(inventory_record([item_record(19)]),[self.original('BELT_A',BELT)]*2,self.symbols)
    def test_third_ring_rejected(self):
        with self.assertRaisesRegex(ValueError,'Too many'):
            restore_accessories(inventory_record([item_record(17,3)]),[self.original('RING_A',RING)]*3,self.symbols)
    def test_missing_and_ambiguous_stacks(self):
        for items in ([],[item_record(),item_record()]):
            with self.assertRaisesRegex(ValueError,'Missing or ambiguous'):
                restore_accessories(inventory_record(items),[self.original('RING_A',RING)],self.symbols)
    def test_unknown_symbol(self):
        with self.assertRaisesRegex(ValueError,'Unknown'):
            restore_accessories(inventory_record(),[self.original('UNKNOWN',RING)],self.symbols)
    def test_ambiguous_source_category(self):
        with self.assertRaisesRegex(ValueError,'category'):
            restore_accessories(inventory_record(),[self.original('RING_A',RING|BELT)],self.symbols)
    def test_non_accessory_reference_conflict(self):
        with self.assertRaisesRegex(ValueError,'non-accessory'):
            restore_accessories(inventory_record([item_record()],equipment=[0]+[NULL]*15),[self.original('RING_A',RING)],self.symbols)

if __name__=='__main__':unittest.main()
