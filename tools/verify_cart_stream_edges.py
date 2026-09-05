#!/usr/bin/env python3
"""Assemble and VICE-check cartridge run-count, metadata and directory boundaries.

Requires 64tass, cartconv and VICE. Outputs stay in build/<variant>-edge-checks/.
Run with --tass PATH --cartconv PATH --vice PATH --vice-data PATH as needed.
"""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
from c643d.cartstream import assemble_cartridge
from c643d.pipeline import FrameBuild
from verify_cart_stream import verify


def check(tass,cartconv,vice,vice_data=None,renderer="yunroll-cart-v3"):
    variant=renderer.rsplit("-",1)[1]
    root=Path(__file__).resolve().parents[1];out=root/f'build/{variant}-edge-checks';out.mkdir(parents=True,exist_ok=True)
    mesh=SimpleNamespace(name=variant.upper()+' BOUNDARIES',vertices=[None]*2,edges=[None],faces=[])
    cases=[(0,0,0),(1,1,1),(255,85,1),(256,86,1),(512,254,65),(257,255,63),(256,1,0)]
    reports=[]
    for colors in (True,False):
        frames=[]
        for i,(runs,clears,spans) in enumerate(cases):
            frames.append(FrameBuild([(0,0,2,0,0)]*runs,[(0,0,1)]*clears,2*runs,8 if runs else 0,[],[(0,0,1,((i+2)<<4))]*spans if colors else []))
        stem=variant+'-boundaries-'+('color' if colors else 'mono')
        crt,m=assemble_cartridge(root,frames,mesh,tass=tass,cartconv=cartconv,outdir=out,stem=stem,colors=colors,renderer=renderer)
        if colors:assert max(f['metadata_bytes'] for f in m['frame_data'])==1024
        reports.append(verify(crt,vice,vice_data))
    # Directory reaches $4ef9, immediately before V3's fixed $4f00 table.
    # Alternating empty/drawn frames also exercise blanking, all slots and wrap.
    fs=[FrameBuild([(0,0,2,0,0)] if i%2 else [],[(0,0,1)] if i%2 else [],2 if i%2 else 0,8 if i%2 else 0,[]) for i in range(255)]
    crt,m=assemble_cartridge(root,fs,mesh,tass=tass,cartconv=cartconv,outdir=out,stem=variant+'-directory-255',colors=False,renderer=renderer)
    assert m['directory_ram_bytes']==1785
    reports.append(verify(crt,vice,vice_data))
    return dict(renderer=renderer,run_counts=[c[0] for c in cases],max_clear_spans=255,max_metadata_bytes=1024,max_directory_frames=255,reports=reports)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv');p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data');p.add_argument('--report',type=Path)
    p.add_argument('--renderer',choices=('yunroll-cart-v3','yunroll-cart-v4'),default='yunroll-cart-v3')
    a=p.parse_args();r=check(a.tass,a.cartconv,a.vice,a.vice_data,a.renderer);text=json.dumps(r,indent=2);print(text)
    if a.report:a.report.write_text(text+'\n')
