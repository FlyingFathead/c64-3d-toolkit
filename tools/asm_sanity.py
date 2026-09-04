#!/usr/bin/env python3
"""Approximate source-level sanity check for the toolkit's 6510 renderers.

64tass is authoritative. This catches the two mistakes that repeatedly hurt the
prototype: relative branches beyond +/-127 bytes, renderer+HUD growth into
the generated pointer arena, and pointer/LUT memory-map collisions.
"""
from __future__ import annotations
import re, sys
from pathlib import Path
BR={'bcc','bcs','beq','bne','bmi','bpl','bvc','bvs'}
IM={'rts','rti','sei','cli','cld','sec','clc','inx','iny','dex','dey','tax','tay','txa','tya','pha','pla','asl','lsr','rol','ror','nop'}
ZP={'STREAM_LO':0xf0,'STREAM_HI':0xf1,'PTR_LO':0xf2,'PTR_HI':0xf3,'STEP_BITS':0xf4,'LINE_MASK':0xf5,'CHUNK_COUNT':0xf6,'CHUNK_LEVELS':0xf7}
HUD_MAX_BYTES=31*8
PTR_BASE=0x1600
LUT_BASE=0x1700

def scan(path:Path, collect=False, labels=None):
    pc=0; branches=[]; const=dict(ZP)
    for no,raw in enumerate(path.read_text().splitlines(),1):
        s=raw.split(';',1)[0].strip()
        if not s or s.startswith('.include'):continue
        m=re.match(r'([A-Za-z_]\w*)\s*=\s*\$([0-9A-Fa-f]+)',s)
        if m:const[m.group(1)]=int(m.group(2),16);continue
        m=re.match(r'\*\s*=\s*\$([0-9A-Fa-f]+)',s)
        if m:pc=int(m.group(1),16);continue
        if s.endswith(':'):
            if labels is not None:labels[s[:-1]]=pc
            continue
        if s.startswith('.byte'):n=len([x for x in s[5:].split(',') if x.strip()])
        elif s.startswith('.word'):n=2*len([x for x in s[5:].split(',') if x.strip()])
        elif s.startswith('.text'):
            q=re.search(r'"(.*)"',s);n=len(q.group(1)) if q else 0
        elif s.startswith('.') or '=' in s:continue
        else:
            a=s.split(None,1);op=a[0].lower();operand=a[1].strip() if len(a)>1 else ''
            if op in BR:
                n=2
                if collect:branches.append((no,pc,op,operand))
            elif op in ('jmp','jsr'):n=3
            elif not operand or (op in IM and operand.lower()=='a'):n=1
            elif operand.startswith('#'):n=2
            elif operand.startswith('('):n=2 if '),y' in operand.lower() or ',x)' in operand.lower() else 3
            else:
                base=operand.split(',')[0].strip();v=const.get(base)
                if v is None and base.startswith('$'):
                    try:v=int(base[1:],16)
                    except ValueError:pass
                n=2 if v is not None and v<256 else 3
        pc+=n
    return branches,pc

def main(argv=None):
    path=Path((argv or sys.argv[1:])[0])
    labels={};scan(path,False,labels);branches,end=scan(path,True,labels)
    bad=[]
    for no,pc,op,target in branches:
        if target in labels:
            d=labels[target]-(pc+2)
            if not -128<=d<=127:bad.append((no,op,target,d))
    # The generated HUD is emitted directly after renderer code. Keep the
    # entire worst-case 31-cell source bitmap below the pointer arena at $1600.
    # v0.3.2 incorrectly used $1500 for pointers, which overwrote the tail of
    # longer HUD strings (e.g. sunflower E:142) in the assembled PRG.
    # Some colour-only cold helpers live in the free $4000-$43ff gap after the
    # HUD include. Use the explicit pre-HUD marker when present rather than the
    # numerically highest source segment.
    no_overlay='renderer_no_overlay_end' in labels
    code_end=labels.get('renderer_hud_start',labels.get('renderer_no_overlay_end',end))
    hud_end=code_end+(0 if no_overlay else HUD_MAX_BYTES)
    if hud_end>PTR_BASE:
        print(f'asm sanity: ERROR code end ${code_end:04x} + HUD would reach ${hud_end:04x}, overlapping pointer arena at ${PTR_BASE:04x}',file=sys.stderr);return 1
    if PTR_BASE+48*4>LUT_BASE:
        print(f'asm sanity: ERROR max frame pointer tables would overlap LUT at ${LUT_BASE:04x}',file=sys.stderr);return 1
    if bad:
        for b in bad:print(f'asm sanity: ERROR line {b[0]} {b[1]} {b[2]} offset {b[3]}',file=sys.stderr)
        return 1
    print(f'asm sanity: estimated code end ${code_end:04x}; {len(branches)} relative branches in range')
    return 0
if __name__=='__main__':raise SystemExit(main())
