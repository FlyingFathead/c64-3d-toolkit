#!/usr/bin/env python3
"""Exercise V8 byte-span boundaries, mixed formats and resident reuse in VICE."""
import argparse
import json
from pathlib import Path
from c643d.pipeline import FrameBuild, oriented_dda, encode_run
from c643d.cartscene import assemble_scene
from verify_v5_kernels import scene
from verify_cart_stream import verify


def sparse(offsets, color=112):
    offsets = list(offsets)
    records = []
    cells = sorted({o//8 for o in offsets})
    for off in offsets:
        row, rem = divmod(off, 320)
        x, y = rem//8*8, row*8+rem%8
        records.append(encode_run(oriented_dda(x,y,x+1,y),0,1))
    return FrameBuild(records,[(c*8 & 255,c*8 >> 8,1) for c in cells],
        len(records)*2,len(records)*2,[],[(c & 255,c >> 8,1,color) for c in cells])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name, default in [('tass','64tass'),('cartconv','cartconv'),('vice','x64sc')]:
        p.add_argument('--'+name,default=default)
    p.add_argument('--vice-data',required=True)
    p.add_argument('--report',type=Path,default=Path('docs/benchmarks/v8/kernels.json'))
    a=p.parse_args()
    frames=[]
    for start in (0,249,256,7000):
        for length in (1,2,3,7,8,127,128,254,255,256,511):
            frames.append(sparse(range(start,start+length)))
    for count in (1,2,127,128,255,256,257):
        frames.append(sparse(i*4 for i in range(count)))
    # Every alignment of an indirect source/destination copy across pages.
    for start in range(248,264):
        frames.append(sparse(range(start,start+129)))
    plain=sparse([])
    plain.records=[encode_run(oriented_dda(0,20,126,20),0,126)]
    pts=[(x,20) for x in range(127)]
    cells=sorted({(y//8)*40+x//8 for x,y in pts})
    plain.clear_spans=[(c*8 & 255,c*8 >> 8,1) for c in cells]
    plain.color_spans=[(c & 255,c >> 8,1,16) for c in cells]
    a_byte=sparse(range(250,270));b_byte=sparse(range(900,940));color_only=sparse(range(250,270),32)
    pattern=[a_byte,b_byte,plain,a_byte,a_byte,color_only,sparse([]),b_byte,plain]
    frames += [pattern[i%len(pattern)] for i in range(270)]
    root=Path(__file__).resolve().parents[1]
    report={}
    for prefer in ('fps','ram'):
        crt,manifest=assemble_scene(root,frames,scene(frames,'V8 BYTE CHECK'),
            tass=a.tass,cartconv=a.cartconv,outdir=root/'build/v8-kernel-checks',
            stem='v8-byte-check-'+prefer,hud_text='V8 BYTE CHECK',frame_ticks=1,
            intro=False,ending=False,text_overlay=False,renderer='yunroll-cart-v8-scene',prefer=prefer)
        modes={d['encoding'] for d in manifest['frame_data']}
        assert modes=={'vectors','byte-spans'}, modes
        assert manifest['optimization']['duplicate_pictures']>0
        report[prefer]=dict(cases=len(frames),validation=verify(crt,a.vice,a.vice_data))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
