"""Read-only Mach-O load-command inventory; no target execution."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def inspect(path):
    data = Path(path).read_bytes()
    def unpack(fmt, offset):
        if offset < 0 or offset + struct.calcsize(fmt) > len(data):
            raise ValueError('truncated header')
        return struct.unpack_from(fmt, data, offset)
    magic = data[:4]
    if magic == bytes.fromhex('cafebabe'):
        count, = unpack('>I', 4)
        if count > 32:
            raise ValueError('excessive architecture count')
        slices = [unpack('>IIIII', 8 + 20*i)[2:4] for i in range(count)]
    else:
        slices = [(0, len(data))]
    result = {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data), 'slices': []}
    for start, size in slices:
        if start + size > len(data) or data[start:start+4] != bytes.fromhex('cffaedfe'):
            raise ValueError('unsupported or truncated Mach-O slice')
        _, cpu, subtype, filetype, count, cmdsize, flags, _ = unpack('<8I', start)
        end = start + 32 + cmdsize
        if end > start + size:
            raise ValueError('load commands exceed slice')
        pos = start + 32
        commands = []
        for _ in range(count):
            cmd, length = unpack('<II', pos)
            if length < 8 or pos + length > end:
                raise ValueError('invalid load command size')
            item = {'command': hex(cmd), 'file_offset': pos, 'size': length}
            if cmd in (0xc, 0xd, 0x80000018, 0x8000001f, 0x8000001c, 0x20):
                offset, = unpack('<I', pos+8)
                if not 8 <= offset < length:
                    raise ValueError('invalid string offset')
                item['name'] = data[pos+offset:pos+length].split(b'\0')[0].decode('utf8', 'replace')
            if cmd == 0x1d:
                item['signature_offset'], item['signature_size'] = unpack('<II', pos+8)
            commands.append(item)
            pos += length
        if pos != end:
            raise ValueError('load command count mismatch')
        result['slices'].append({'architecture': {0x1000007:'x86_64', 0x100000c:'arm64'}.get(cpu, hex(cpu)), 'offset': start, 'size': size, 'commands': commands})
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary')
    print(json.dumps(inspect(parser.parse_args().binary), indent=2))
