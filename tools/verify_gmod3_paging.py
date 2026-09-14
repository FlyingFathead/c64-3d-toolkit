#!/usr/bin/env python3
"""Check all five Marbles pages in reverse and a standalone paced long scene."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from verify_gmod3_collection import ROOT, labels, launch, run_monitor, verify_entry
from verify_cart_stream import expected_frame, apply_interactive_overlay
from c643d.gmod3_catalog import frames_for, mesh_for
from c643d.gmod3_v3 import assemble_cartridge
from c643d.gmod3_paging import configure


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key,default in [('tass','64tass'),('cartconv','cartconv'),('vice','x64sc')]:p.add_argument('--'+key,default=default)
    p.add_argument('--vice-data',required=True)
    p.add_argument('--crt',type=Path,default=ROOT/'examples/gmod3_cart_demos/demo-cart-v3.1-gmod3-all-in-one.crt')
    p.add_argument('--output',type=Path,default=ROOT/'docs/benchmarks/gmod3-paging')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    crt=a.crt.resolve()
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    entry=next(r for r in meta['entries'] if r['frames']==640)
    sym=labels(crt.parent/entry['labels']);menu=labels(crt.parent/meta['collection_labels'])
    frames=frames_for(ROOT/'build/gmod3-catalog',entry);expected=[]
    for f in frames:
        bm,sc=expected_frame(f.__dict__,entry['screen_color'])
        expected.append(bytes(apply_interactive_overlay(bm,entry['runtime']))+sc)
    with tempfile.TemporaryDirectory(prefix='gmod3-reverse-') as td:
        tmp=Path(td);cmd=launch(meta,menu,entry,sym)
        # Change direction state at an ordinary frame boundary; keyboard direction
        # itself is covered separately by the shared controls tests.
        cmd += [f'> ${sym["v3_step"]:04x} ff']
        for i in range(643):
            cmd+=['delete',f'break ${sym["frame_draw_complete"]:04x}','g','bank ram',f'bsave "{tmp}/{i}.ram" 0 $0000 $ffff']
        run_monitor(crt,a.vice,a.vice_data,tmp,cmd)
        slots=set()
        for i in range(643):
            ram=(tmp/f'{i}.ram').read_bytes();slot=ram[sym['render_slot']]
            fi=ram[sym['frame_index']]+128*ram[sym['gp_page']]
            assert fi==(-i)%640,(i,fi)
            b=(0x2000,0x6000,0xe000)[slot];s=(0x400,0x4400,0xc800)[slot]
            assert ram[b:b+7680]+ram[s:s+960]==expected[fi],(i,fi,slot)
            slots.add(slot)
        assert slots=={0,1,2}
    out=ROOT/'build/gmod3-long-scene';out.mkdir(parents=True,exist_ok=True)
    def transform(src):return configure(src,pages=5,directory_bank=4,interactive=False,target_fps=16)
    auto,am=assemble_cartridge(ROOT,frames,mesh_for(entry),tass=a.tass,cartconv=a.cartconv,
        outdir=out,stem='long-scene-v4',size_mib=4,first_bank=5,directory_bank=4,page_frames=128,
        interactive=False,colors=entry['colors'],color_index=entry['screen_color']>>4,
        background_color=entry['screen_color']&15,border_color=entry['border_color'],
        source_transform=transform,renderer_name='hors-renderer-v4')
    row=dict(entry,labels=auto.with_suffix('.lbl').name,runtime=am,mode_frames=0,target_fps=16)
    result=verify_entry(auto,dict(standalone=True,interactive=False),row,a.vice,a.vice_data,a.output)
    result['crt_sha256']=hashlib.sha256(auto.read_bytes()).hexdigest()
    assert am['cartridge_capacity']['used_kib']==(5+len({f['bank'] for f in am['frame_data']}))*8
    report=dict(passed=True,collection_sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
        reverse_pictures_checked=643,reverse_all_three_buffers=True,reverse_wraps=True,
        standalone_paced_long_scene=result,standalone_capacity=am['cartridge_capacity'])
    (a.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS reverse pages, full wrap, standalone long scene and allocation accounting')

if __name__=='__main__':main()
