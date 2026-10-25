import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_format import inventory_layout
from inventory_restore import reconcile_inventory,source_inventory
from test_validation import NULL,inventory_record,item_record

def amounts(data):
    return {r['symbol']:struct.unpack_from('<I',r['raw'],r['amount'])[0] for r in inventory_layout(data)['records']}

class InventoryRestoreTests(unittest.TestCase):
    def test_remove_protected_duplicates_and_remap_equipment(self):
        equipment=[2]+[NULL]*15
        data=inventory_record([item_record(99),item_record(17,4),item_record(18,2)],equipment=equipment)
        result=reconcile_inventory(data,{17:2,18:1})
        self.assertEqual(amounts(result),{17:2,18:1})
        layout=inventory_layout(result)
        self.assertEqual(layout['equipment'][0],1)
        self.assertEqual(layout['records'][1]['raw'][-66],1)
    def test_model_attachment_and_active_slot_remapped(self):
        data=inventory_record([item_record(99),item_record(17)],models=[('HAND',1)],
                              attachments=[('AMMO',0),('STATE',1)],equipment=[NULL]*5+[0]+[NULL]*10,active=1)
        layout=inventory_layout(reconcile_inventory(data,{17:1}))
        self.assertEqual(layout['models'],[(b'HAND',0)])
        self.assertEqual(layout['attachments'],[(b'AMMO',NULL),(b'STATE',0)])
        self.assertEqual(layout['active'],255)
    def test_hotbar_active_slot_survives_remap(self):
        equipment=[NULL]*15+[1]
        data=inventory_record([item_record(99),item_record(17)],equipment=equipment,active=10)
        layout=inventory_layout(reconcile_inventory(data,{17:1}))
        self.assertEqual(layout['equipment'][15],0)
        self.assertEqual(layout['active'],10)
    def test_clear_accessories_before_repair(self):
        equipment=[NULL,NULL,NULL,0,0]+[NULL]*11
        data=inventory_record([item_record(17,2)],equipment=equipment)
        with self.assertRaisesRegex(ValueError,'Equipment references'):reconcile_inventory(data,{17:1})
        result=reconcile_inventory(data,{17:1},clear_accessories=True)
        self.assertEqual(inventory_layout(result)['equipment'][1:5],[NULL]*4)
        self.assertEqual(inventory_layout(result)['records'][0]['raw'][-66:],bytes([0,255])+bytes(64))
    def test_idempotent(self):
        data=inventory_record([item_record(17,5),item_record(18,3)])
        result=reconcile_inventory(data,{17:2,18:1})
        self.assertEqual(reconcile_inventory(result,{17:2,18:1}),result)
    def test_missing_or_duplicate_stack_rejected(self):
        for data in (inventory_record(),inventory_record([item_record(17),item_record(17)])):
            with self.assertRaises(ValueError):reconcile_inventory(data,{17:1})
    def test_invalid_amounts(self):
        for amount in (0,-1,0x100000000,1.5):
            with self.assertRaises(ValueError):reconcile_inventory(inventory_record([item_record(17)]),{17:amount})
    def test_empty_desired_inventory(self):
        result=reconcile_inventory(inventory_record([item_record()]),{})
        self.assertEqual(amounts(result),{})
    def test_input_unchanged(self):
        data=bytearray(inventory_record([item_record(17,4)]));before=bytes(data)
        reconcile_inventory(data,{17:1})
        self.assertEqual(data,before)
    def test_source_packed_and_explicit_amounts(self):
        npc=dict(packed=['item_a:2,ITEM_B:3','ITEM_A:4',''],
                 items=[dict(instance='ITEM_C',amount=0),dict(instance='item_a',amount=1)])
        self.assertEqual(source_inventory(npc),{'ITEM_A':7,'ITEM_B':3,'ITEM_C':1})
    def test_negative_packed_amount_rejected(self):
        with self.assertRaises(ValueError):source_inventory(dict(packed=['A:-1'],items=[]))

if __name__=='__main__':unittest.main()
