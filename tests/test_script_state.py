"""Synthetic journal, guild-table, and script-variable records."""
import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from script_state import guild_table_offset,journal_tail_offset,restore_globals,restore_guild_table,restore_journal,string,uint
from native_format import Reader

def variable(typ,name,values):
    data=uint(typ)+string(name)+uint(len(values))
    if typ==3:return data+b''.join(string(value) for value in values)
    return data+b''.join(struct.pack('<i' if typ==2 else '<f',value) for value in values)

def variables(records):return uint(len(records))+b''.join(records)

def quests(native_size=3):
    journal=uint(1)+string('old')+bytes([1,2])+uint(1)+string('previous')
    tail=uint(1)+uint(12)+uint(34)+uint(native_size*native_size)+struct.pack('<'+str(native_size*native_size)+'i',*range(native_size*native_size))
    return journal+tail

class ScriptStateTests(unittest.TestCase):
    def test_integer_arrays_restore_and_other_records_preserved(self):
        others=[variable(1,'FLOAT',[1.25]),variable(3,'TEXT',['\x80\xff']),uint(0)]
        for cls in range(4):
            others.append(uint(7)+bytes([cls])+(string('INSTANCE')+uint(0xffffffff)+(uint(7) if cls==3 else b'') if cls else b''))
        data=variables([variable(2,'ARRAY',[1,2]),*others])
        result,report=restore_globals(data,[['ARRAY',[-2147483648,2147483647]]])
        self.assertEqual(result,variables([variable(2,'ARRAY',[-2147483648,2147483647]),*others]))
        self.assertEqual(report,dict(originalGlobalsVerified=1,globalsRestoredAfterWorldInitialization=1))
        self.assertEqual(restore_globals(result,[['ARRAY',[-2147483648,2147483647]]])[1]['globalsRestoredAfterWorldInitialization'],0)
    def test_global_array_length_mismatch(self):
        with self.assertRaisesRegex(ValueError,'array length'):restore_globals(variables([variable(2,'X',[1,2])]),[['X',[3]]])
    def test_missing_global(self):
        with self.assertRaisesRegex(ValueError,'missing'):restore_globals(variables([]),[['X',[3]]])
    def test_wrong_global_type(self):
        with self.assertRaisesRegex(ValueError,'incompatible'):restore_globals(variables([variable(1,'X',[1.0])]),[['X',[3]]])
    def test_duplicate_original_and_native_global(self):
        with self.assertRaisesRegex(ValueError,'Duplicate source'):restore_globals(variables([]),[['X',[1]],['X',[2]]])
        with self.assertRaisesRegex(ValueError,'Duplicate native'):restore_globals(variables([variable(2,'X',[1])]*2),[['X',[3]]])
    def test_unknown_record_type_or_instance_class(self):
        for record in (uint(9),uint(7)+bytes([4])):
            with self.assertRaises(ValueError):restore_globals(variables([record]),[])
    def test_all_truncated_variable_prefixes(self):
        data=variables([variable(3,'TEXT',['legacy bytes']),variable(2,'ARRAY',[4,5])])
        for end in range(len(data)):
            with self.subTest(end=end):
                with self.assertRaises(ValueError):restore_globals(data[:end],[])
        with self.assertRaises(ValueError):restore_globals(data+b'x',[])
    def test_journal_legacy_text_reverse_order_and_preserved_tail(self):
        data=quests();tail=data[journal_tail_offset(data):]
        original=[dict(title='\x80title',section=0,status=3,entries=['newest\xff','older'])]
        result=restore_journal(data,original)
        self.assertEqual(result,uint(1)+string('\x80title')+bytes([0,3])+uint(2)+string('older')+string('newest\xff')+tail)
    def test_truncated_journal_rejected(self):
        data=quests();offset=journal_tail_offset(data)
        for end in range(offset):
            with self.assertRaises(ValueError):restore_journal(data[:end],[])
    def test_guild_patch_preserves_extra_rows_columns_and_dialogs(self):
        data=quests();offset=guild_table_offset(data,3)
        result=restore_guild_table(data,bytes([11,12,21,22]),2,3)
        self.assertEqual(result[:offset],data[:offset])
        self.assertEqual(struct.unpack_from('<9i',result,offset),(11,12,2,21,22,5,6,7,8))
    def test_guild_shape_and_truncation(self):
        data=quests()
        for invalid in (data[:-1],data+b'x'):
            with self.assertRaises(ValueError):restore_guild_table(invalid,bytes(4),2,3)
        with self.assertRaisesRegex(ValueError,'native guild'):restore_guild_table(data,bytes(4),2,4)
        with self.assertRaisesRegex(ValueError,'source guild'):restore_guild_table(data,bytes(3),2,3)

if __name__=='__main__':unittest.main()
