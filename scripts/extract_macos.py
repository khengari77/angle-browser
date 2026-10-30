"""Decode Arc's zlib/raw UDIF HFS partition, then extract with 7z.

Usage: python3 scripts/extract_macos.py image.dmg output_directory
The output directory must not exist. The source is never modified.
"""
import argparse
import plistlib
import struct
import subprocess
import zlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('image',type=Path); p.add_argument('output',type=Path)
a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=False)
with a.image.open('rb') as source:
    source.seek(-512,2); trailer=source.read(512)
    if trailer[:4]!=b'koly': raise ValueError('not a UDIF disk image')
    offset,length=struct.unpack_from('>QQ',trailer,216)
    if length>16*1024*1024: raise ValueError('oversized partition metadata')
    source.seek(offset); meta=plistlib.loads(source.read(length))
    partitions=[x['Data'] for x in meta['resource-fork']['blkx'] if 'Apple_HFS' in x['Name']]
    if len(partitions)!=1: raise ValueError('expected one HFS partition')
    b=partitions[0]; _,sectors,data_offset=struct.unpack_from('>QQQ',b,8)
    count=struct.unpack_from('>I',b,200)[0]
    if sectors*512>2*1024**3 or 204+count*40>len(b): raise ValueError('unsupported partition size')
    partition=a.output/'partition.hfs'
    with partition.open('xb') as out:
        out.truncate(sectors*512)
        for i in range(count):
            kind,_,sector,nsectors,coff,clen=struct.unpack_from('>IIQQQQ',b,204+40*i)
            if kind in (0,2,0xffffffff): continue
            if kind not in (1,0x80000005) or sector+nsectors>sectors or clen>16*1024**2:
                raise ValueError('unsupported or malformed partition run')
            source.seek(data_offset+coff); raw=source.read(clen)
            if kind==0x80000005:
                decoder=zlib.decompressobj(); raw=decoder.decompress(raw,nsectors*512+1)
                if not decoder.eof or decoder.unconsumed_tail: raise ValueError('invalid compressed run')
            if len(raw)!=nsectors*512: raise ValueError('run length mismatch')
            out.seek(sector*512); out.write(raw)
subprocess.run(['7z','x','-y','-o'+str(a.output/'bundle'),str(partition),'Arc/Arc.app/*'],check=True)
