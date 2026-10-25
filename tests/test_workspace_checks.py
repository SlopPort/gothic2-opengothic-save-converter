import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from workspace_checks import verify_original_scripts

class WorkspaceChecksTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)
        self.dat=self.root/'game/_work/Data/Scripts/_compiled/GOTHIC.DAT'
        self.dat.parent.mkdir(parents=True);self.dat.write_bytes(b'synthetic original scripts')
        self.report=self.root/'workspace/generated/build-report.json';self.report.parent.mkdir(parents=True)
        self.fingerprint=hashlib.sha256(self.dat.read_bytes()).hexdigest()
        self.report.write_text(json.dumps(dict(sourceSha256=self.fingerprint)))
    def check(self):verify_original_scripts(self.root/'game',self.root/'workspace')
    def test_matching_original(self):self.check()
    def test_changed_original_is_rejected(self):
        self.dat.write_bytes(b'synthetic modified scripts')
        with self.assertRaisesRegex(ValueError,'differ'):self.check()
    def test_missing_report(self):
        self.report.unlink()
        with self.assertRaisesRegex(ValueError,'build report'):self.check()
    def test_malformed_fingerprints(self):
        for value in (None,123,'', 'x'*64):
            self.report.write_text(json.dumps(dict(sourceSha256=value)))
            with self.assertRaises(ValueError):self.check()
    def test_uppercase_digest(self):
        self.report.write_text(json.dumps(dict(sourceSha256=self.fingerprint.upper())))
        self.check()

if __name__=='__main__':unittest.main()
