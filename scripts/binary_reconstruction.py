#!/usr/bin/env python3
"""Produce sanitized static declarations from hash-bound cached research and MSIX.

No application is executed. Output contains factual names/coordinates, not code.
"""
# SPDX-License-Identifier: MPL-2.0
import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path

SELECTED = {
    'StorableSidebar.StorableSidebar', 'BaseModels.SidebarItem',
    'BaseModels.SidebarItemData', 'BaseModels.SidebarItemDictionaryCoding',
    'BaseModels.SidebarItemContainer', 'BaseModels.SidebarItemContainer.ContainerType',
    'BaseModels.SidebarContainer', 'BaseModels.SidebarContainerType',
    'BaseModels.SpaceModel', 'BaseModels.SpaceModel.CodingKeys',
    'BaseModels.SpaceModel.CustomInfo', 'BaseModels.SpaceModel.ContainerType',
    'BaseModels.SpaceModel.ContainerType.UnpinnedContainerType',
    'SidebarDataStore.AppSidebarReducerState',
    'CommandBar.CommandBarState', 'CommandBar.CommandBar.Action',
    'CommandBar.CommandBarSelectionOptions.Action',
    'CommandBar.TypeLetterInCommandBarStateMachine.State',
    'CommandBar.TypeLetterInCommandBarStateMachine.Event',
    'CommandBar.TypeLetterInCommandBarStateMachine.Transition',
    'CommandBar.CommandBarPresentation', 'CommandBar.CommandBarSelectionFlags',
    'CommandBar.CommandBarDelegateAction', 'CommandBar.CommandBarViewState',
    'SharedWindowFeature.SidebarItemHoveredState',
}
SEEDS = ('StorableSidebar.json', 'savedURL', 'currentURL', 'childrenIds',
         'parentID', 'newContainerIDs', 'containerIDs', 'topAppsContainerIDs')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inspect_pe(data):
    """Read bounded PE header/section declarations, without loading the image."""
    def read(fmt, pos):
        if pos < 0 or pos + struct.calcsize(fmt) > len(data):
            raise ValueError('PE structure outside member')
        return struct.unpack_from(fmt, data, pos)
    if data[:2] != b'MZ':
        raise ValueError('missing DOS header')
    pe, = read('<I', 0x3c)
    if data[pe:pe+4] != b'PE\0\0':
        raise ValueError('missing PE signature')
    machine, count, timestamp, _, _, optional_size, flags = read('<HHIIIHH', pe+4)
    if count > 96:
        raise ValueError('section count exceeds bounded inventory')
    magic, = read('<H', pe+24)
    sections = []
    for index in range(count):
        pos = pe+24+optional_size+40*index
        name, virtual_size, rva, size, offset = read('<8sIIII', pos)
        if size and offset + size > len(data):
            raise ValueError('section exceeds member')
        sections.append(dict(name=name.rstrip(b'\0').decode('ascii', errors='replace'),
                             rva=hex(rva), virtual_size=virtual_size,
                             file_offset=offset, file_size=size))
    return dict(machine=hex(machine), optional_magic=hex(magic),
                coff_timestamp=timestamp, characteristics=hex(flags), sections=sections)


def function_start_ownership(data, sites):
    """Identify exact LC_FUNCTION_STARTS records at supplied Ghidra source VAs."""
    def read(fmt, pos):
        if pos < 0 or pos + struct.calcsize(fmt) > len(data):
            raise ValueError('Mach-O structure outside file')
        return struct.unpack_from(fmt, data, pos)
    if data[:4] != bytes.fromhex('cffaedfe'):
        raise ValueError('expected thin little-endian Mach-O64')
    count, command_size = read('<II', 16)
    pos, command_end = 32, 32+command_size
    segments, starts, base = [], None, None
    for _ in range(count):
        cmd, size = read('<II', pos)
        if size < 8 or pos+size > command_end:
            raise ValueError('invalid Mach-O command size')
        if cmd == 0x19:
            name, address, virtual_size, offset, file_size = read('<16sQQQQ', pos+8)
            name = name.rstrip(b'\0').decode('ascii')
            segments.append(dict(name=name, address=address, offset=offset, file_size=file_size))
            if name == '__TEXT':
                base = address
        elif cmd == 0x26:
            starts = read('<II', pos+8)
        pos += size
    if pos != command_end or base is None or starts is None:
        raise ValueError('missing or inconsistent function-start mapping')
    offset, size = starts
    end = offset+size
    if end > len(data):
        raise ValueError('function-start table exceeds file')
    rows = []
    for site in sites:
        owner = next((x for x in segments if x['address'] <= site < x['address']+x['file_size']), None)
        if owner is None:
            raise ValueError('reference source is not file-backed')
        file_offset = owner['offset']+site-owner['address']
        rows.append(dict(source_address=hex(site), segment=owner['name'],
                         source_file_offset=file_offset,
                         in_function_starts=offset <= file_offset < end))
    pos, address = offset, base
    while pos < end:
        record = pos
        delta, shift = 0, 0
        while True:
            if pos >= end or shift >= 64:
                raise ValueError('invalid function-start ULEB128')
            value = data[pos]
            pos += 1
            delta |= (value & 127) << shift
            if not value & 128:
                break
            shift += 7
        if not delta:
            break
        address += delta
        for row in rows:
            if row['source_file_offset'] == record:
                row['record_target'] = hex(address)
                row['record_size'] = pos-record
    return dict(load_command='LC_FUNCTION_STARTS', table_file_offset=offset,
                table_size=size, sites=rows,
                interpretation='Importer DATA references point from function-start declarations; they are not code callers or dispatch entries.')


def build(macho, metadata_path, msix):
    actual = digest(macho)
    metadata = json.loads(Path(metadata_path).read_text())
    ownership = function_start_ownership(Path(macho).read_bytes(), (0x10534064d, 0x105371f36))
    if metadata.get('sha256') != actual:
        raise ValueError('cached Swift report does not match supplied executable hash')
    models = [dict(context=r['context'], descriptor_address=r['descriptor_address'],
                   kind=r['kind'], fields=[f['name'] for f in r['fields']])
              for r in metadata['matches'] if r.get('context') in SELECTED]
    report = dict(format='angle-binary-reconstruction-v1',
                  macos=dict(sha256=actual, function_start_reference_ownership=ownership, metadata_report_sha256=digest(metadata_path),
                             descriptor_count=metadata['descriptor_count'],
                             unresolved_names=metadata['unresolved_names'],
                             models=models, missing_selected_contexts=sorted(SELECTED-{r['context'] for r in models})),
                  limitations=['Compiler field declarations do not establish encoded JSON keys, values, defaults, emitted cases or runtime behavior.',
                               'Cached parser coverage remains incomplete; metadata names are not recovered function implementations.',
                               'PE section declarations and exact string presence do not establish code paths or shared serialization.',
                               'Package hashes identify the inspected artifacts, not their signature authenticity.'])
    with zipfile.ZipFile(msix) as archive:
        binaries = []
        for name in ('Arc.exe', 'Arc.dll'):
            member = archive.getinfo(name)
            if member.file_size > 128*1024*1024:
                raise ValueError('selected PE member exceeds analysis memory budget')
            image = archive.read(member)
            hits = []
            for seed in SEEDS:
                for encoding in ('utf-8', 'utf-16le'):
                    needle = seed.encode(encoding)
                    first = image.find(needle)
                    hits.append(dict(seed=seed, encoding=encoding, count=image.count(needle),
                                     first_file_offset=first if first >= 0 else None))
            binaries.append(dict(member=name, sha256=hashlib.sha256(image).hexdigest(),
                                 size=len(image), pe=inspect_pe(image), string_seed_presence=hits))
        report['windows'] = dict(package_sha256=digest(msix), member_count=len(archive.infolist()),
                                 inspected_binaries=binaries,
                                 selected_resource_members=[n for n in archive.namelist() if n in ('AppxManifest.xml','resources.pri')])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--macho', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--msix', required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.macho, args.metadata, args.msix), indent=2))


if __name__ == '__main__':
    main()
