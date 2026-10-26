import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from spell_slots import restore_spell_slots
from native_format import inventory_layout
from test_validation import NULL,inventory_record,item_record

class SpellSlotTests(unittest.TestCase):
    names={'RUNE_A':dict(index=17),'SCROLL_B':dict(index=18)}
    def test_first_and_last_spell_keys(self):
        data=inventory_record([item_record(17),item_record(18)])
        result=restore_spell_slots(data,[['RUNE_A',0],['SCROLL_B',7]],self.names)
        layout=inventory_layout(result)
        self.assertEqual(layout['equipment'][8:],[0]+[NULL]*6+[1])
        self.assertEqual([r['raw'][-66:-64] for r in layout['records']],[bytes([1,3]),bytes([1,10])])
        self.assertEqual(restore_spell_slots(result,[['RUNE_A',0],['SCROLL_B',7]],self.names),result)
    def test_stale_assignments_removed_and_active_slot_cleared(self):
        data=inventory_record([item_record(17)],equipment=[NULL]*8+[0]+[NULL]*7,active=3)
        result=restore_spell_slots(data,[],self.names);layout=inventory_layout(result)
        self.assertEqual(layout['equipment'][8:],[NULL]*8);self.assertEqual(layout['active'],255)
        self.assertEqual(layout['records'][0]['raw'][-66:-64],bytes([0,255]))
    def test_two_identical_scrolls_can_share_a_stack(self):
        data=inventory_record([item_record(17,2)])
        result=restore_spell_slots(data,[['RUNE_A',0],['RUNE_A',1]],self.names)
        self.assertEqual(inventory_layout(result)['records'][0]['raw'][-66],2)
    def test_insufficient_amount(self):
        with self.assertRaisesRegex(ValueError,'exceed'):
            restore_spell_slots(inventory_record([item_record(17)]),[['RUNE_A',0],['RUNE_A',1]],self.names)
    def test_invalid_or_duplicate_source_slot(self):
        for shortcuts in ([['RUNE_A',-1]],[['RUNE_A',8]],[['RUNE_A',0],['SCROLL_B',0]]):
            with self.assertRaises(ValueError):restore_spell_slots(inventory_record([item_record(17),item_record(18)]),shortcuts,self.names)
    def test_missing_or_ambiguous_stack(self):
        for data in (inventory_record(),inventory_record([item_record(17),item_record(17)])):
            with self.assertRaises(ValueError):restore_spell_slots(data,[['RUNE_A',0]],self.names)
    def test_equipment_conflict(self):
        with self.assertRaisesRegex(ValueError,'non-spell'):
            restore_spell_slots(inventory_record([item_record(17)],equipment=[0]+[NULL]*15),[['RUNE_A',0]],self.names)
    def test_non_spell_equipment_is_unchanged(self):
        gear=bytearray(item_record(99));gear[-66]=1
        data=inventory_record([bytes(gear),item_record(17)],equipment=[0]+[NULL]*15)
        result=restore_spell_slots(data,[['RUNE_A',2]],self.names)
        self.assertEqual(inventory_layout(result)['records'][0]['raw'],bytes(gear))

if __name__=='__main__':unittest.main()
