#!/usr/bin/env python3
"""Exercise V5 Y blocks/partial paths and resident reuse in real PAL VICE."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
from c643d.pipeline import FrameBuild,decode_record_points,oriented_dda,encode_run
from c643d.cartscene import assemble_scene
from verify_cart_stream import verify


def frame(record,color=16):
    points=decode_record_points(record)
    cells=sorted({(y//8)*320+(x//8)*8 for x,y in points})
    clear=[(off&255,off>>8,1) for off in cells]
    colors=[((off//8)&255,(off//8)>>8,1,color) for off in cells]
    return FrameBuild([record],clear,len(points),len(points),[],colors)


def scene(frames,name):
    return SimpleNamespace(name=name,mesh=SimpleNamespace(vertices=[],edges=[],faces=[]),
        source_fps=50,sample_step=1,frames=[SimpleNamespace(source_frame=i+1) for i in range(len(frames))])


def check(tass,cartconv,vice,vice_data):
    root=Path(__file__).resolve().parents[1];out=root/'build/v5-kernel-checks'
    frames=[]
    # All eight Y entry phases, both X directions, boundary lengths, and four
    # representative bit patterns. Optimization is disabled to execute every
    # original record even when two masks happen to produce the same picture.
    for phase in range(8):
        for neg in (False,True):
            for count in (2,7,8,9,15,16,17,126,127):
                for mask in (0,255,85,170):
                    x=192 if neg else 64;y=16+phase
                    off=(y//8)*320+(x//8)*8
                    ctl=(x&7)|((y&7)<<3)|64|(128 if neg else 0)
                    rec=(off&255,off>>8,count,ctl,*([mask]*((phase+count+7)//8)))
                    frames.append(frame(rec))
    crt,_=assemble_scene(root,frames,scene(frames,'Y KERNEL CHECK'),tass=tass,cartconv=cartconv,
        outdir=out,stem='v5-y-kernels',hud_text='Y KERNEL CHECK',frame_ticks=1,
        intro=False,ending=False,text_overlay=False,renderer='yunroll-cart-v5-scene',optimize=False)
    kernels=verify(crt,vice,vice_data)
    def line(coords,color):
        dda=oriented_dda(*coords)
        return frame(encode_run(dda,0,len(dda['points'])-1),color)
    A=line((25,50,72,50),16);B=line((50,20,50,70),32)
    C=line((20,20,62,62),112);D=line((25,50,72,50),32)
    pattern=[A,B,C,A,B,A,A,A,D,D,A,B,A,C,A]
    fs=[pattern[i%len(pattern)] for i in range(270)]
    crt,_=assemble_scene(root,fs,scene(fs,'REUSE CHECK'),tass=tass,cartconv=cartconv,
        outdir=out,stem='v5-reuse',hud_text='REUSE CHECK',frame_ticks=3,
        intro=True,ending=True,text_overlay=False,renderer='yunroll-cart-v5-scene')
    reuse=verify(crt,vice,vice_data)
    assert reuse['reused_samples']>150,reuse
    from profile_cart_stream import profile
    timing=profile(crt,vice,vice_data)
    # Every logical sample retains its three PAL ticks, including duplicates.
    ideal=len(fs)*3*19656/985248
    assert abs(timing['measured_seconds']-ideal)<0.10,(timing['measured_seconds'],ideal)
    result=dict(kernel_cases=len(frames),kernels=kernels,reuse=reuse,
                hold_seconds=timing['measured_seconds'],ideal_hold_seconds=ideal)
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tass',default='64tass')
    p.add_argument('--cartconv',default='cartconv');p.add_argument('--vice',default='x64sc')
    p.add_argument('--vice-data',required=True);a=p.parse_args()
    print(json.dumps(check(a.tass,a.cartconv,a.vice,a.vice_data),indent=2))
