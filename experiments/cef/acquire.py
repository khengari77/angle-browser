#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Acquire an exact prebuilt CEF archive; verify before extracting local SDK files."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from urllib.parse import quote
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', choices=['client', 'minimal'])
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    lock = json.loads(Path(__file__).with_name('lock.json').read_text())
    dest = root / '.local-tools/cef'
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / (args.variant + '.tar.bz2')
    spec = lock['archives'][args.variant]
    name = f"cef_binary_{lock['cef']}_{lock['platform']}_{args.variant}"
    if not archive.exists():
        part = archive.with_suffix('.partial')
        with urlopen(lock['base_url'] + quote(name + '.tar.bz2', safe=''), timeout=60) as source, part.open('xb') as output:
            while block := source.read(1024 * 1024):
                output.write(block)
        part.rename(archive)
    if archive.stat().st_size != spec['size']:
        raise ValueError('Archive size mismatch')
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != spec['sha256']:
            raise ValueError('Archive SHA-256 mismatch; not extracted')
    target = dest / name
    if target.exists():
        raise FileExistsError('Destination exists; inspect it or select a clean checkout before extracting')
    with tarfile.open(archive) as bundle:
        bundle.extractall(dest, filter='data')
    print(target)


if __name__ == '__main__':
    main()
