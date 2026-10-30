"""Find candidate RIP-relative LEA references to a literal in thin x86_64 Mach-O.

Search is deliberately bounded to REX.W LEA; it is not a complete xref engine.
Candidate decoding uses GNU objdump and declared LC_FUNCTION_STARTS boundaries.
"""
import argparse
import bisect
import hashlib
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path
from inspect_macho import inspect
from swift_fields import Image


def lea_candidates(data, section, targets):
    begin, end = section['offset'], section['offset']+section['size']
    if end>len(data): raise ValueError('truncated code section')
    matches=[]
    for rex in range(0x48,0x50):
        pos=begin
        while True:
            pos=data.find(bytes([rex,0x8d]),pos,end)
            if pos<0: break
            if pos+7<=end and data[pos+2]&0xc7==5:
                address=section['address']+pos-begin
                target=address+7+struct.unpack_from('<i',data,pos+3)[0]
                if target in targets:
                    matches.append({'instruction_address':hex(address),'file_offset':pos,'target':hex(target),'bytes_hex':data[pos:pos+7].hex()})
            pos+=1
    return sorted(matches,key=lambda row:row['file_offset'])


def function_starts(data, command, base):
    offset,size=struct.unpack_from('<II',data,command['file_offset']+8)
    end=offset+size
    if end>len(data): raise ValueError('truncated function starts')
    result=[];address=base
    while offset<end:
        value=shift=0
        while True:
            if offset>=end or shift>63: raise ValueError('invalid function-start ULEB')
            byte=data[offset];offset+=1
            value|=(byte&127)<<shift
            if not byte&128: break
            shift+=7
        if not value: return result
        address+=value
        if address>=1<<64: raise ValueError('function address overflow')
        result.append(address)
    raise ValueError('unterminated function-start stream')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary',type=Path);parser.add_argument('literal')
    parser.add_argument('--function-assembly-dir',type=Path,help='New local directory for bounded complete function-span disassembly')
    args=parser.parse_args();data=args.binary.read_bytes();image=Image(data)
    meta=inspect(args.binary)
    if meta['slices'][0]['architecture']!='x86_64': raise ValueError('expected x86_64')
    text=next(s for s in image.sections if s['name']=='__text')
    base=next(s['address'] for s in image.segments if s['name']=='__TEXT')
    commands=meta['slices'][0]['commands'];command=next((c for c in commands if c['command']=='0x26'),None)
    starts=function_starts(data,command,base) if command else []
    needle=args.literal.encode();targets=[];pos=0
    if not needle: raise ValueError('empty literal')
    while True:
        pos=data.find(needle,pos)
        if pos<0: break
        for section in image.sections:
            if section['offset']<=pos<section['offset']+section['size']:
                targets.append(section['address']+pos-section['offset'])
        pos+=len(needle)
    refs=lea_candidates(data,text,set(targets))
    if args.function_assembly_dir: args.function_assembly_dir.mkdir(parents=True,exist_ok=False)
    for ref in refs:
        address=int(ref['instruction_address'],16);i=bisect.bisect_right(starts,address)-1
        ref['preceding_declared_function_start']=hex(starts[i]) if i>=0 else None
        ref['next_declared_function_start']=hex(starts[i+1]) if 0<=i<len(starts)-1 else None
        with tempfile.NamedTemporaryFile() as stream:
            stream.write(bytes.fromhex(ref['bytes_hex']));stream.flush()
            decoded=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','--adjust-vma='+ref['instruction_address'],stream.name],capture_output=True,text=True,check=True)
        ref['objdump_instruction']=[line.strip() for line in decoded.stdout.splitlines() if '\t' in line]
        if args.function_assembly_dir and 0<=i<len(starts)-1:
            begin, end = starts[i], starts[i+1]
            if 0<end-begin<=65536:
                offset=image.file_offset(begin)
                if offset+end-begin>len(data): raise ValueError('truncated declared function span')
                code=data[offset:offset+end-begin]
                with tempfile.NamedTemporaryFile() as stream:
                    stream.write(code);stream.flush()
                    disasm=subprocess.run(['objdump','-D','-b','binary','-m','i386:x86-64','--adjust-vma='+hex(begin),stream.name],capture_output=True,text=True,check=True).stdout
                target_file=args.function_assembly_dir/(hex(begin)+'.asm')
                target_file.write_text(disasm)
                line=next((line for line in disasm.splitlines() if re.match(r'^\s*'+format(address,'x')+r':',line)),None)
                ref['linear_disassembly_has_candidate_instruction_boundary']=line is not None
                ref['declared_function_span_sha256']=hashlib.sha256(code).hexdigest()
                ref['local_disassembly_filename']=target_file.name
                ref['declared_function_span_size']=len(code)
            else:
                ref['linear_disassembly_skipped']='declared span exceeds 64 KiB or is empty'

    print(json.dumps({'format':'arcreverse-x86-literal-refs-v1','sha256':meta['sha256'],'literal':args.literal,'targets':[hex(x) for x in targets],'function_starts_count':len(starts),'candidates':refs,'limitations':['Only REX.W RIP-relative LEA encodings in __text are searched.', 'A preceding declared function start and isolated decoding alone do not validate instruction boundaries. Optional full-span linear disassembly checks boundaries, not control-flow reachability.', 'No target execution or complete function analysis occurred.']},indent=2))

if __name__=='__main__': main()
