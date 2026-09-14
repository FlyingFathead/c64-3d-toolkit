#!/usr/bin/env python3
"""Rebuild and check the original crossing scene on GMod3, EasyFlash and PRG."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from c643d import cli
from c643d.pipeline import build_scene_frames
from c643d.sceneio import load_scene
from c643d.gmod3_validation import display_capture
from verify_cart_stream import verify, labels, expected_frame

ROOT=Path(__file__).resolve().parents[1]


def verify_resident(prg, frames, *, vice, vice_data):
    sym=labels(prg.with_suffix('.lbl'));count=len(frames)*3+3;slots=set()
    with tempfile.TemporaryDirectory(prefix='c643d-resident-') as td:
        temp=Path(td)
        commands=['delete',f'load "{prg}" 0',f'break ${sym["frame_begin"]+9:04x}']
        for i in range(count):
            commands+=[f'g ${sym["start"]:04x}' if i==0 else 'g','bank ram',
                       f'bsave "{temp}/{i}.ram" 0 $0000 $ffff']
        commands+=['quit']
        (temp/'run.mon').write_text('\n'.join(commands)+'\n')
        with (temp/'vice.log').open('w') as log:
            result=subprocess.run([vice,'-console','-pal','+sound','-warp','-seed','1',
                '-directory',vice_data,'-monlogname',str(temp/'monitor.log'),'-initbreak','ready','-moncommands',str(temp/'run.mon'),
                '-limitcycles',str(count*1000000+2000000)],stdout=log,stderr=subprocess.STDOUT,timeout=120)
        if result.returncode:raise RuntimeError((temp/'vice.log').read_text()[-2000:])
        for i in range(count):
            ram=(temp/f'{i}.ram').read_bytes();fi=ram[sym['frame_index']];slot=ram[sym['render_slot']]
            assert fi==i%len(frames),(i,fi)
            slots.add(slot)
            bm,sc=expected_frame(asdict(frames[fi]),0x10)
            baddr=(0x2000,0x6000,0xe000)[slot];saddr=(0x400,0x4400,0xc800)[slot]
            assert ram[baddr:baddr+7680]==bm,('resident bitmap',i,slot)
            assert ram[saddr:saddr+960]==sc,('resident colours',i,slot)
    assert slots=={0,1,2}
    return dict(passed=True,verified_frames=count,all_three_buffers=True,bitmap_match=True,color_match=True,
                prg_sha256=hashlib.sha256(prg.read_bytes()).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    a=p.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    source=ROOT/'examples/camera_crossing/camera-crossing.c643dscene'
    scene=load_scene(source);stats={}
    frames,_=build_scene_frames(scene,height=192,enable_source_colors=True,ignore_warnings=True,clipping_stats=stats)
    assert len(frames)==17 and stats['empty_frames']==9
    assert frames[0]==frames[-1] and frames[0].unique_pixels
    results=dict(passed=True,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),clipping=stats)
    for name,renderer in (('gmod3','hors-v4'),('easyflash','hors-v4-ef'),('resident','yunroll')):
        stem='camera-crossing-'+name
        args=['build','--scene',str(source),'--renderer',renderer,'--output-dir',str(out),'--output',stem,
              '--tass',a.tass,'--cartconv',a.cartconv,'--vice',a.vice,'--overwrite-policy','allow','--ignore-warnings']
        args+=['--viewport-width','256'] if name=='resident' else ['--frame-ticks','2']
        if cli.main(args):raise RuntimeError(name+' build failed')
        if name=='resident':
            resident,_=build_scene_frames(scene,width=256,height=192,enable_source_colors=True,ignore_warnings=True)
            results[name]=verify_resident(out/(stem+'.prg'),resident,vice=a.vice,vice_data=a.vice_data)
        else:
            results[name]=verify(out/(stem+'.crt'),a.vice,a.vice_data,cycles=3)
            if name=='gmod3':
                meta=json.loads((out/(stem+'-manifest.json')).read_text())
                results['gmod3_display']=display_capture(out/(stem+'.crt'),ROOT/meta['runtime_work']/'oracle.json',
                    vice=a.vice,vice_data=a.vice_data,out=out/'display',refreshes=300)
    (out/'validation.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
