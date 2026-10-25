"""Check that offline finalization uses the original scripts recorded by prepare."""
import hashlib,json
from pathlib import Path


def verify_original_scripts(game_dir,workspace):
    report_path=Path(workspace)/'generated/build-report.json'
    if not report_path.is_file():
        raise ValueError('Workspace build report is missing; run prepare in a fresh workspace')
    report=json.loads(report_path.read_text(encoding='utf8'))
    expected=report.get('sourceSha256')
    if not isinstance(expected,str) or len(expected)!=64:
        raise ValueError('Workspace has no valid original-script fingerprint')
    try:bytes.fromhex(expected)
    except ValueError:raise ValueError('Invalid original-script fingerprint') from None
    original=Path(game_dir)/'_work/Data/Scripts/_compiled/GOTHIC.DAT'
    actual=hashlib.sha256(original.read_bytes()).hexdigest()
    if actual!=expected.lower():
        raise ValueError('Game scripts differ from preparation; use the same unmodified original game installation')
