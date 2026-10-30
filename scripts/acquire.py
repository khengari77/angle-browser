"""Acquire pinned official reference packages, verifying SHA-256 before publication."""
import hashlib
import json
import subprocess
from pathlib import Path
REFERENCES = [
 ('macos/Arc-1.170.0-89123.dmg','https://releases.arc.net/release/Arc-1.170.0-89123.dmg','5cf6d057e8944f847dac83d89b4d30d7a49c8974d02d29b35d2cf5afce9e36c1'),
 ('windows/ArcReverse-Arc-1.129.0.288-x64.msix','https://releases.arc.net/windows/prod/1.129.0.288/Arc.x64.msix','b45d110aad915c82a042782b0f3dae126787107727bb44e86ad733d2479196b5')]
records=[]
for name,url,expected in REFERENCES:
    path=Path('artifacts')/name; path.parent.mkdir(parents=True,exist_ok=True)
    candidate=path if path.exists() else path.with_suffix(path.suffix+'.part')
    if not path.exists(): subprocess.run(['curl','-fL','--max-time','300','-o',str(candidate),url],check=True)
    h=hashlib.sha256()
    with candidate.open('rb') as f:
        for block in iter(lambda:f.read(1024**2),b''): h.update(block)
    if h.hexdigest()!=expected: raise ValueError(f'hash mismatch: {candidate}')
    if candidate!=path: candidate.rename(path)
    records.append({'path':name,'source':url,'sha256':expected,'size':path.stat().st_size})
print(json.dumps(records,indent=2))
