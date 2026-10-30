"""Read compiler-emitted Swift field descriptors in thin little-endian Mach-O64.

This recovers declarations, not JSON keys or runtime serialization behavior.
Layout: swiftlang/swift include/swift/RemoteInspection/Records.h and ABI/Mangling.rst.
"""
import argparse
import hashlib
from functools import lru_cache
import json
import struct
from pathlib import Path


class Image:
    def __init__(self, data):
        self.data = data
        if data[:4] != bytes.fromhex('cffaedfe'):
            raise ValueError('expected thin little-endian Mach-O64')
        count, total = self.unpack('<II', 16)
        end, pos = 32 + total, 32
        if end > len(data): raise ValueError('truncated load commands')
        self.sections = []
        self.segments = []
        self.fixups = None
        self.context_names = {}
        for _ in range(count):
            cmd, size = self.unpack('<II', pos)
            if size < 8 or pos + size > end: raise ValueError('invalid command')
            if cmd == 0x80000034:
                self.fixups = self.unpack('<II', pos+8)
            if cmd == 0x19:
                segname, vmaddr, vmsize = self.unpack('<16sQQ', pos+8)
                self.segments.append({'name':segname.rstrip(b'\0').decode(), 'address':vmaddr, 'size':vmsize})
                nsects, = self.unpack('<I', pos + 64)
                if 72 + nsects * 80 > size: raise ValueError('invalid sections')
                for i in range(nsects):
                    off = pos + 72 + i * 80
                    name, seg, addr, length, fileoff = self.unpack('<16s16sQQI', off)
                    flags, = self.unpack('<I', off+64)
                    self.sections.append({'name': name.rstrip(b'\0').decode(), 'segment': seg.rstrip(b'\0').decode(), 'address': addr, 'size': length, 'offset': fileoff, 'flags': flags})
            pos += size
        if pos != end: raise ValueError('load-command size mismatch')

    def unpack(self, fmt, offset):
        if offset < 0 or offset+struct.calcsize(fmt)>len(self.data): raise ValueError('out-of-file read')
        return struct.unpack_from(fmt, self.data, offset)

    @lru_cache(maxsize=65536)
    def file_offset(self, address):
        for s in self.sections:
            if s['flags'] & 0xff in (1, 0xc, 0x12): continue  # zero-fill
            if s['address'] <= address < s['address']+s['size']:
                off = s['offset']+address-s['address']
                if off >= len(self.data): raise ValueError('unbacked address')
                return off
        raise ValueError(f'address not in a file-backed section: {address:#x}')

    @lru_cache(maxsize=16384)
    def indirect_context(self, slot):
        if self.fixups is None: raise ValueError('no chained-fixup mapping')
        base = next(s['address'] for s in self.segments if s['name']=='__TEXT')
        offset, size = self.fixups
        if size < 28 or offset+size > len(self.data): raise ValueError('invalid chained fixups')
        version, startoff, _, _, _, _, _ = self.unpack('<7I', offset)
        if version != 0: raise ValueError('unsupported fixup version')
        start = offset+startoff
        count, = self.unpack('<I', start)
        if count>len(self.segments): raise ValueError('invalid fixup segment count')
        for i in range(count):
            rel, = self.unpack('<I', start+4+4*i)
            if not rel: continue
            record = start+rel
            length, page_size, form, segment_offset, _, pages = self.unpack('<IHHQIH', record)
            if record+length>offset+size or length<22+2*pages: raise ValueError('invalid fixup starts')
            segment = base+segment_offset
            if not segment <= slot < segment+pages*page_size: continue
            if form!=6: raise ValueError(f'unsupported indirect pointer format {form}')
            page=(slot-segment)//page_size
            entry, = self.unpack('<H',record+22+2*page)
            if entry==0xffff or entry & 0x8000: raise ValueError('absent or unsupported multi-start page')
            current=segment+page*page_size+entry
            page_end=segment+(page+1)*page_size
            while current+8<=page_end:
                raw, = self.unpack('<Q',self.file_offset(current))
                if current==slot:
                    if raw>>63: raise ValueError('external bound context remains unresolved')
                    if (raw>>44)&127: raise ValueError('nonzero reserved fixup bits')
                    target=base+((raw&((1<<36)-1))|(((raw>>36)&255)<<56))
                    return self.context(target)
                stride=((raw>>51)&4095)*4
                if not stride: break
                current+=stride
            raise ValueError('slot is not an observed chained fixup')
        raise ValueError('no fixup page for indirect context')

    def relative(self, address):
        delta, = self.unpack('<i', self.file_offset(address))
        return address+delta if delta else None

    def string(self, address, symbolic=False):
        start = self.file_offset(address)
        p = start
        refs = []
        while p-start < 4096:
            byte, = self.unpack('<B', p)
            if byte == 0:
                return {'file_offset': start, 'address': hex(address), 'bytes_hex': self.data[start:p].hex(), 'text': self.data[start:p].decode('utf8', 'backslashreplace') if not refs else None, 'symbolic_references': refs}
            if symbolic and 1 <= byte <= 31:
                width = 4 if byte <= 23 else 8
                delta, = self.unpack('<i' if width==4 else '<Q', p+1)
                target = address+(p-start)+1+delta if width==4 else delta
                ref = {'kind': byte, 'target': hex(target)}
                if byte in (1, 2):
                    try: ref['context'] = self.context(target) if byte==1 else self.indirect_context(target)
                    except ValueError as error: ref['unresolved'] = str(error)
                refs.append(ref)
                p += width+1
            else: p += 1
        raise ValueError('unterminated metadata string')

    def context(self, address, seen=None):
        if seen is None and address in self.context_names:
            return self.context_names[address]
        top_level = seen is None
        seen = set() if seen is None else seen
        if address in seen or len(seen)>32: raise ValueError('cyclic context')
        seen.add(address)
        flags, = self.unpack('<I', self.file_offset(address))
        kind = flags & 31
        if kind not in (0, 3, 16, 17, 18): raise ValueError(f'unresolved context kind {kind}')
        name_addr = self.relative(address+8)
        if name_addr is None: raise ValueError('null context name')
        name = self.string(name_addr)['text']
        parent = self.relative(address+4)
        if parent:
            # Context parents are RelativeIndirectablePointer: preserve unresolved indirect cases.
            if parent & 1: raise ValueError('indirect parent context not decoded')
            name = self.context(parent, seen)+'.'+name
        if top_level: self.context_names[address] = name
        return name

    def fields(self, pattern=''):
        section = next((s for s in self.sections if s['name']=='__swift5_fieldmd'), None)
        if section is None: raise ValueError('no Swift field descriptor section')
        rows, issues = [], []
        unresolved_names = 0
        p, end = section['offset'], section['offset']+section['size']
        if end > len(self.data): raise ValueError('truncated field descriptor section')
        count = 0
        while p < end:
            if p+16 > end: raise ValueError('truncated descriptor header')
            _, _, kind, stride, num = self.unpack('<iiHHI', p)
            if stride != 12 or p+16+num*stride>end: raise ValueError(f'unsupported descriptor layout at {p:#x}')
            address = section['address']+p-section['offset']
            try:
                type_address = self.relative(address)
                type_name = self.string(type_address, symbolic=True) if type_address else None
                name = None
                if type_name:
                    refs = type_name['symbolic_references']
                    if len(refs)==1: name = refs[0].get('context')
                    if name is None: name = type_name['text']
                if name is None: unresolved_names += 1
                if pattern and pattern not in (name or ''):
                    p += 16+num*stride; count += 1; continue
                fields = []
                for i in range(num):
                    pos = p+16+i*stride
                    faddr = section['address']+pos-section['offset']
                    flags, = self.unpack('<I', pos)
                    target = self.relative(faddr+4)
                    field_name = self.relative(faddr+8)
                    fields.append({'record_file_offset':pos, 'flags':flags, 'name':self.string(field_name)['text'] if field_name else None, 'mangled_type':self.string(target, symbolic=True) if target else None})
                rows.append({'descriptor_file_offset':p, 'descriptor_address':hex(address), 'kind':kind, 'context':name, 'type_name':type_name, 'fields':fields})
            except ValueError as error:
                issues.append({'descriptor_file_offset':p,'error':str(error)})
            p += 16+num*stride
            count += 1
        return {'descriptor_count':count, 'unresolved_names':unresolved_names, 'matches':rows, 'issues':issues, 'section':section}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary',type=Path); p.add_argument('--pattern',default='')
    a=p.parse_args(); data=a.binary.read_bytes()
    result=Image(data).fields(a.pattern)
    result.update(format='arcreverse-swift-fields-v1', sha256=hashlib.sha256(data).hexdigest(), pattern=a.pattern, limitations=['Compiler declarations do not establish Codable conformance, JSON keys, serialized representation, or runtime behavior.', 'Context kinds outside module/protocol/class/struct/enum and indirect parents remain unresolved.', 'Symbolic references are byte-preserved; direct context references and verified format-6 chained internal rebase contexts are named; bound imports remain unresolved.'])
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
