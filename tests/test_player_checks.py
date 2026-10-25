import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from player_checks import verify_player
from test_validation import NULL,npc_record,inventory_record,item_record

class PlayerChecksTests(unittest.TestCase):
    def setUp(self):
        self.hero=dict(player=True,attributes=[40,80,10,20,15,12,0,0],protection=[0]*8,aiVars=[0]*100,
                       level=14,xp=100,xpNext=200,lp=8,guild=2,hitChance=[0]*4,packed=['ITEM_A:2'],items=[])
        self.source=dict(worlds={'NEWWORLD':[self.hero]})
        self.entries={'worlds/newworld.zen/npc/0/data':npc_record(),
                      'worlds/newworld.zen/npc/0/inventory':inventory_record([item_record(17,2)])}
        self.byname={'PC_HERO':dict(index=7),'ITEM_A':dict(index=17)}
    def check(self):verify_player(self.entries,self.source,self.byname)
    def test_matching_player(self):self.check()
    def test_wrong_player_fields(self):
        self.hero['xp']=101
        with self.assertRaisesRegex(ValueError,'xp'):self.check()
    def test_extra_or_wrong_inventory_amounts(self):
        for records in ([item_record(17,3)],[item_record(17,2),item_record(18)]):
            self.entries['worlds/newworld.zen/npc/0/inventory']=inventory_record(records)
            with self.assertRaisesRegex(ValueError,'inventoryAmounts'):self.check()
    def test_stale_accessory_pointer(self):
        self.entries['worlds/newworld.zen/npc/0/inventory']=inventory_record([item_record(17,2)],equipment=[NULL,NULL,NULL,0,NULL]+[NULL]*11)
        with self.assertRaisesRegex(ValueError,'accessoryPointers'):self.check()
    def test_multiple_native_players_rejected(self):
        self.entries['worlds/newworld.zen/npc/1/data']=npc_record()
        with self.assertRaisesRegex(ValueError,'one native player'):self.check()
    def test_multiple_source_players_rejected(self):
        self.source['worlds']['NEWWORLD'].append(self.hero.copy())
        with self.assertRaisesRegex(ValueError,'one source player'):self.check()
    def test_unknown_source_inventory_symbol(self):
        del self.byname['ITEM_A']
        with self.assertRaisesRegex(ValueError,'absent'):self.check()

if __name__=='__main__':unittest.main()
