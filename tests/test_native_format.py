import io,struct,sys,tempfile,unittest,zipfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from native_format import Reader,archive,inventory,pack_archive,pack_visited_world,publish_archive
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
class PublicationTests(unittest.TestCase):
 def setUp(self):
  self.directory=tempfile.TemporaryDirectory()
  self.addCleanup(self.directory.cleanup)
  self.root=Path(self.directory.name)
  self.candidate=self.root/'candidate.sav'
  self.output=self.root/'output.sav'
  self.candidate.write_bytes(pack_archive({'synthetic':b'test'}))
 def assert_no_temporary(self):
  self.assertEqual(list(self.root.glob('.save-converter-*')),[])
 def test_success_preserves_candidate(self):
  expected=self.candidate.read_bytes()
  publish_archive(self.candidate,self.output)
  self.assertEqual(self.output.read_bytes(),expected)
  self.assertEqual(self.candidate.read_bytes(),expected)
  self.assert_no_temporary()
 def test_existing_output_is_unchanged(self):
  self.output.write_bytes(b'existing')
  with self.assertRaises(FileExistsError):publish_archive(self.candidate,self.output)
  self.assertEqual(self.output.read_bytes(),b'existing')
  self.assert_no_temporary()
 def test_invalid_candidate_never_published(self):
  self.candidate.write_bytes(b'broken zip')
  with self.assertRaises(zipfile.BadZipFile):publish_archive(self.candidate,self.output)
  self.assertFalse(self.output.exists())
  self.assert_no_temporary()
 def test_invalid_nested_archive_never_published(self):
  self.candidate.write_bytes(pack_archive({'worlds/oldworld.zen.zip':struct.pack('<I',3)+b'bad'}))
  with self.assertRaises(zipfile.BadZipFile):publish_archive(self.candidate,self.output)
  self.assertFalse(self.output.exists())
 def test_wrong_nested_length_never_published(self):
  payload=pack_visited_world({'synthetic':b'test'})
  self.candidate.write_bytes(pack_archive({'worlds/oldworld.zen.zip':b'\0\0\0\0'+payload[4:]}))
  with self.assertRaises(ValueError):publish_archive(self.candidate,self.output)
  self.assertFalse(self.output.exists())
 def test_failed_flush_never_published(self):
  with patch('native_format.os.fsync',side_effect=OSError('simulated interrupted write')):
   with self.assertRaises(OSError):publish_archive(self.candidate,self.output)
  self.assertFalse(self.output.exists())
  self.assert_no_temporary()
 def test_competing_output_is_unchanged(self):
  import os
  link=os.link
  def competing(source,destination):
   Path(destination).write_bytes(b'competing output')
   return link(source,destination)
  with patch('native_format.os.link',side_effect=competing):
   with self.assertRaises(FileExistsError):publish_archive(self.candidate,self.output)
  self.assertEqual(self.output.read_bytes(),b'competing output')
  self.assert_no_temporary()
 def test_in_place_publication_rejected(self):
  with self.assertRaises(ValueError):publish_archive(self.candidate,self.candidate)
 def test_unsupported_filesystem_fails_safely(self):
  with patch('native_format.os.link',side_effect=OSError('hard links unavailable')):
   with self.assertRaises(OSError):publish_archive(self.candidate,self.output)
  self.assertFalse(self.output.exists())
  self.assert_no_temporary()
if __name__=='__main__':unittest.main()
