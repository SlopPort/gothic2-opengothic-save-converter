import io,struct,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_format import Reader,archive,inventory,pack_archive,pack_visited_world
class NativeFormatTests(unittest.TestCase):
 def test_preserves_explicit_npc_directories(self):
  entries={'worlds/':b'','worlds/newworld.zen/':b'','worlds/newworld.zen/npc/':b'',
   'worlds/newworld.zen/npc/0/':b'','worlds/newworld.zen/npc/0/data':b'synthetic NPC'}
  self.assertEqual(archive(pack_archive(entries)),entries)
  self.assertIn('worlds/newworld.zen/npc/0/',archive(pack_archive(entries)))
 def test_visited_world_length_prefix(self):
  entries={'worlds/oldworld.zen/npc/0/':b'','worlds/oldworld.zen/npc/0/data':b'synthetic'}
  payload=pack_visited_world(entries)
  self.assertEqual(struct.unpack_from('<I',payload)[0],len(payload)-4)
  self.assertEqual(archive(payload),entries)
 def test_rejects_truncated_string(self):
  with self.assertRaises(ValueError):Reader(struct.pack('<I',8)+b'ab').s()
 def test_empty_inventory_layout_and_truncation(self):
  data=struct.pack('<II',0,0)+struct.pack('<II',0,0xffffffff)*2+struct.pack('<16IBii',*([0xffffffff]*16),255,0,0)
  self.assertEqual(inventory(data),[])
  with self.assertRaises(ValueError):inventory(data[:-1])
 def test_rejects_duplicate_entries(self):
  import warnings
  out=io.BytesIO()
  with warnings.catch_warnings():
   warnings.simplefilter('ignore')
   with zipfile.ZipFile(out,'w') as z:z.writestr('same',b'a');z.writestr('same',b'b')
  with self.assertRaises(ValueError):archive(out.getvalue())
if __name__=='__main__':unittest.main()
