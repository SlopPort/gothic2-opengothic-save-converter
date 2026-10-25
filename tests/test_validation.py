"""Synthetic format-56 fixtures; no game or playthrough data."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_format import inventory_layout,pack_archive,pack_visited_world
from native_validation import MAGIC,validate_save

NULL=0xffffffff

def string(value):
    data=value.encode('ascii')
    return struct.pack('<I',len(data))+data

def item_record(symbol=17,amount=1):
    # Empty script strings and zero script attributes; independent fixed-layout fixture.
    script=struct.pack('<Ii',symbol,0)+string('')+string('')
    script+=bytes(48*4)  # hp/hp_max/main_flag and numeric item fields through disguise_guild
    script+=string('')*3+bytes(4)+string('')+bytes(20)
    script+=string('')*7+bytes(44)
    return script+struct.pack('<I3fBB16f',amount,0,0,0,0,255,*([0.0]*16))

def inventory_record(items=(),models=(),attachments=None,equipment=None,active=255):
    result=struct.pack('<I',len(items))+b''.join(items)+struct.pack('<I',len(models))
    for name,index in models:result+=string(name)+struct.pack('<I',index)
    for name,index in attachments or [('',NULL),('',NULL)]:result+=string(name)+struct.pack('<I',index)
    return result+struct.pack('<16IBii',*(equipment or [NULL]*16),active,-1,0)

def npc_record(symbol=7):
    data=struct.pack('<Ii',symbol,99)+string('')*7+struct.pack('<ii',0,0)
    data+=struct.pack('<8i',40,80,10,20,15,12,0,0)+bytes((5+8+8)*4)
    data+=struct.pack('<3i',0,2,14)+bytes((5+5+2)*4)+string('')+bytes((3+100)*4)
    return data+string('')+struct.pack('<5i',100,200,8,0,0)

def world(name):
    prefix='worlds/'+name+'/'
    return {prefix+'version':struct.pack('<H',56),prefix+'npc/0/':b'',
            prefix+'npc/0/data':npc_record(),prefix+'npc/0/visual':b'',
            prefix+'npc/0/inventory':inventory_record(),prefix+'items':struct.pack('<I',0)}

def save(visited=True):
    current='newworld.zen';old='oldworld.zen'
    entries=world(current)
    entries['header']=MAGIC+struct.pack('<H',56)+string('synthetic')+string(current)+bytes(36)+struct.pack('<qQBH',900,123,2,int(visited))
    entries['game/session']=struct.pack('<QqQ',123,900,0)+string(current)
    entries['game/quests']=struct.pack('<III',0,0,66*66)+bytes(66*66*4);entries['game/daedalus']=bytes(4)
    if visited:
        entries['header']+=string(old)
        entries['worlds/'+old+'.zip']=pack_visited_world(world(old))
    return entries

class InventoryValidationTests(unittest.TestCase):
    def test_full_layout(self):
        layout=inventory_layout(inventory_record([item_record()],models=[('HAND',0)],
                                attachments=[('AMMO',0),('',NULL)],equipment=[0]+[NULL]*15,active=10))
        self.assertEqual(layout['records'][0]['symbol'],17)
        self.assertEqual(layout['models'],[(b'HAND',0)])
        self.assertEqual(layout['equipment'],[0]+[NULL]*15)
        self.assertEqual(layout['active'],10)
    def test_invalid_equipment_index(self):
        with self.assertRaisesRegex(ValueError,'pointer'):
            inventory_layout(inventory_record([item_record()],equipment=[1]+[NULL]*15))
    def test_invalid_model_pointer(self):
        with self.assertRaisesRegex(ValueError,'pointer'):
            inventory_layout(inventory_record(models=[('HAND',0)]))
    def test_invalid_attachment_pointer(self):
        with self.assertRaisesRegex(ValueError,'pointer'):
            inventory_layout(inventory_record(attachments=[('AMMO',0),('',NULL)]))
    def test_invalid_active_slot(self):
        with self.assertRaisesRegex(ValueError,'active'):
            inventory_layout(inventory_record(active=11))
    def test_truncated_and_trailing_records(self):
        data=inventory_record([item_record()])
        for invalid in (data[:-1],data+b'x'):
            with self.assertRaises(ValueError):inventory_layout(invalid)
    def test_excessive_count(self):
        with self.assertRaisesRegex(ValueError,'count'):inventory_layout(struct.pack('<I',10000))

class SaveValidationTests(unittest.TestCase):
    def test_two_worlds(self):
        report=validate_save(pack_archive(save()))
        self.assertEqual(set(report['worlds']),{'newworld.zen','oldworld.zen'})
        self.assertNotIn('synthetic',str(report))
    def test_empty_npc_inventory_may_be_omitted(self):
        entries=save(False);del entries['worlds/newworld.zen/npc/0/inventory']
        self.assertEqual(validate_save(pack_archive(entries))['worlds']['newworld.zen']['inventories'],0)
    def test_missing_explicit_npc_directory(self):
        entries=save();del entries['worlds/newworld.zen/npc/0/']
        with self.assertRaisesRegex(ValueError,'Missing save entry'):validate_save(pack_archive(entries))
    def test_noncontiguous_npc_ids(self):
        entries=save(False)
        entries={key.replace('/npc/0/','/npc/2/'):value for key,value in entries.items()}
        with self.assertRaisesRegex(ValueError,'Non-contiguous'):validate_save(pack_archive(entries))
    def test_missing_visual(self):
        entries=save();del entries['worlds/newworld.zen/npc/0/visual']
        with self.assertRaisesRegex(ValueError,'visual'):validate_save(pack_archive(entries))
    def test_header_session_world_mismatch(self):
        entries=save();entries['game/session']=struct.pack('<QqQ',123,900,0)+string('oldworld.zen')
        with self.assertRaisesRegex(ValueError,'world mismatch'):validate_save(pack_archive(entries))
    def test_header_session_calendar_mismatch(self):
        entries=save();entries['game/session']=struct.pack('<QqQ',123,901,0)+string('newworld.zen')
        with self.assertRaisesRegex(ValueError,'calendar mismatch'):validate_save(pack_archive(entries))
    def test_undeclared_visited_payload(self):
        entries=save(False);entries['worlds/oldworld.zen.zip']=pack_visited_world(world('oldworld.zen'))
        with self.assertRaisesRegex(ValueError,'list/payload'):validate_save(pack_archive(entries))
    def test_nested_bad_inventory(self):
        entries=save();nested=world('oldworld.zen')
        nested['worlds/oldworld.zen/npc/0/inventory']=inventory_record(equipment=[0]+[NULL]*15)
        entries['worlds/oldworld.zen.zip']=pack_visited_world(nested)
        with self.assertRaisesRegex(ValueError,'oldworld.*pointer'):validate_save(pack_archive(entries))
    def test_unsupported_version(self):
        entries=save();header=bytearray(entries['header']);struct.pack_into('<H',header,len(MAGIC),57);entries['header']=header
        with self.assertRaisesRegex(ValueError,'format 56'):validate_save(pack_archive(entries))
    def test_truncated_header_and_items(self):
        for key in ('header','worlds/newworld.zen/items'):
            entries=save();entries[key]=b'bad'
            with self.assertRaises(ValueError):validate_save(pack_archive(entries))
    def test_wrong_world_version(self):
        entries=save();entries['worlds/newworld.zen/version']=struct.pack('<H',55)
        with self.assertRaisesRegex(ValueError,'world version'):validate_save(pack_archive(entries))

if __name__=='__main__':unittest.main()
