#!/usr/bin/env python3
"""Matched PAL cartridge comparisons using every released picture.

Both builders receive identical HORS-V3 picture payloads, HUD and settings.
Authored pacing is disabled to expose throughput. The 640-picture Marbles
sequence is measured as five equal 128-picture segments on both backends;
the collection verifier separately exercises its uninterrupted paged playback.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import copy
import hashlib
import json
from pathlib import Path
import shutil

from c643d.gmod3_catalog import read_json, frames_for, mesh_for
from c643d.gmod3_collection import layout
from c643d.gmod3_v3 import assemble_cartridge as gmod3
from c643d.hors_v3 import assemble_cartridge as easyflash
from verify_gmod3_collection import ROOT, verify_entry, CLOCK, PAL


def cases():
    rows=read_json(ROOT/'examples/gmod3_cart_demos/demo-cart-v3.0-gmod3-all-in-one-benchmark-manifest.json')['entries']
    result=[]
    for row in rows:
        if row['frames']>255:
            for start in range(0,row['frames'],128):
                item=copy.deepcopy(row)
                item.update(name=row['name']+f' [{start+1}..{start+128}]',slice=[start,start+128],frames=128)
                result.append(item)
        else:result.append(row)
    for i,row in enumerate(result):row['case']=i
    return result


def measure(args):
    row,tass,conv,vice,data,out,refreshes=args
    out=Path(out);number=row['case'];path=out/f'{number:02d}.json'
    # Rebuild/re-measure on each invocation. A previous JSON is evidence for
    # its recorded binary, not a cache valid after renderer/settings changes.
    frames=frames_for(ROOT/'build/gmod3-catalog',row)
    if 'slice' in row:frames=frames[slice(*row['slice'])]
    mesh=mesh_for(row);mesh.name=mesh.name[:10];mesh.faces=[]
    # The released 192-picture metallic Pretzel uses the explicit indexed4
    # policy to fit the preserved EasyFlash ROML allocator. Match that policy
    # on both backends; retain all pictures and identify it in the report.
    encoding='indexed4' if number==56 else 'literal'
    work=ROOT/'build/gmod3-matched'/f'{number:02d}';work.mkdir(parents=True,exist_ok=True)
    builds={};result=dict(case=number,name=row['name'],source_id=row['id'],frames=len(frames),slice=row.get('slice'),color_encoding=encoding)
    for kind,builder in [('easyflash',easyflash),('gmod3',gmod3)]:
        stem=f'matched-{number:02d}-{kind}'
        opts=dict(tass=tass,cartconv=conv,outdir=work,stem=stem,colors=row['colors'],
            color_index=row['screen_color']>>4,background_color=row['screen_color']&15,
            border_color=row['border_color'],interactive=False,include_starfield=False,hud_visible=True,color_encoding=encoding)
        if kind=='gmod3':opts['renderer_name']='hors-renderer-v4'
        crt,meta=builder(ROOT,frames,mesh,**opts)
        builds[kind]=[f['sha256'] for f in meta['frame_data']]
        entry=dict(row,index=number,labels=crt.with_suffix('.lbl').name,runtime=meta,
            mode_frames=0,frames=len(frames),target_fps=None)
        folder=out/kind;folder.mkdir(exist_ok=True)
        metrics=verify_entry(crt,dict(standalone=True,interactive=False),entry,vice,data,folder,refreshes)
        metrics['crt_sha256']=hashlib.sha256(crt.read_bytes()).hexdigest()
        metrics['renderer']=meta['renderer'];metrics['toolkit_version']=meta['build_screen']['version']
        result[kind]=metrics
    assert builds['easyflash']==builds['gmod3'],'Cartridge comparison changed encoded picture bytes'
    result.update(encoded_payloads_identical=True,
        difference_fps=result['gmod3']['average_fps']-result['easyflash']['average_fps'])
    path.write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name,default in [('tass','64tass'),('cartconv','cartconv'),('vice','x64sc')]:p.add_argument('--'+name,default=default)
    p.add_argument('--vice-data',required=True);p.add_argument('--jobs',type=int,default=3)
    p.add_argument('--output',type=Path,default=ROOT/'docs/benchmarks/hors-v4-matched')
    p.add_argument('--refreshes',type=int,default=4800);p.add_argument('--cases',type=int,nargs='*')
    a=p.parse_args()
    if a.refreshes<2 or a.jobs<1:p.error('refreshes must be >=2 and jobs >=1')
    a.output.mkdir(parents=True,exist_ok=True)
    rows=[r for r in cases() if a.cases is None or r['case'] in a.cases]
    tasks=[(r,str(Path(shutil.which(a.tass)).resolve()),str(Path(shutil.which(a.cartconv)).resolve()),
        str(Path(shutil.which(a.vice)).resolve()),a.vice_data,str(a.output.resolve()),a.refreshes) for r in rows]
    results=[]
    with ProcessPoolExecutor(max_workers=a.jobs) as executor:
        for future in as_completed([executor.submit(measure,t) for t in tasks]):
            r=future.result();results.append(r)
            print(f'PASS {r["case"]:02d} {r["name"]}: EF {r["easyflash"]["average_fps"]:.5f}, GMod3 {r["gmod3"]["average_fps"]:.5f} FPS',flush=True)
    results.sort(key=lambda r:r['case'])
    (a.output/'results.json').write_text(json.dumps(dict(protocol='Identical HORS-V3 payloads, non-interactive, HUD on, no authored pacing or stars; two picture loops plus warm-up, then actual displayed slots',
        clock_hz=CLOCK,pal_cycles=PAL,observation_refreshes=a.refreshes,entries=results),indent=2)+'\n')

if __name__=='__main__':main()
