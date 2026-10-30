"""Inventory a copied app bundle without following symbolic links."""
import argparse
import hashlib
import json
import plistlib
from pathlib import Path
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('bundle', type=Path)
a = p.parse_args()
rows = []
for path in sorted(a.bundle.rglob('*')):
    row = {'path': str(path.relative_to(a.bundle))}
    if path.is_symlink():
        row.update(kind='symlink', target=str(path.readlink()))
    elif path.is_file():
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
        row.update(kind='file', size=path.stat().st_size, sha256=digest.hexdigest())
        if path.name == 'Info.plist':
            try:
                info = plistlib.loads(path.read_bytes())
                row['metadata'] = {k:info[k] for k in ('CFBundleIdentifier','CFBundleExecutable','CFBundleShortVersionString','CFBundleVersion','LSMinimumSystemVersion') if k in info}
            except (ValueError, plistlib.InvalidFileException) as error:
                row['error'] = str(error)
    else:
        continue
    rows.append(row)
print(json.dumps({'format':'arcreverse-inventory-v1', 'entries':rows}, indent=2))
