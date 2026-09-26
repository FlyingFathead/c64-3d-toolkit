#!/usr/bin/env python3
"""Fresh PAL native checks for the release's defaults and explicit V5 candidates."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True)
    for key in ('tass','cartconv','vice'):
        import shutil
        value=shutil.which(getattr(a,key))
        if not value:raise ValueError('Missing executable: '+getattr(a,key))
        setattr(a,key,str(Path(value).resolve()))
    a.vice_data=str(Path(a.vice_data).resolve())
    common=[]
    for k in ('tass','cartconv','vice','vice_data'):common += ['--'+k.replace('_','-'),getattr(a,k)]
    subprocess.run([sys.executable,str(ROOT/'tools/verify_camera_crossing.py'),
                    '--output-dir',str(out/'camera'),*common],cwd=ROOT,check=True)
    from c643d import cli
    from verify_cart_stream import verify
    from verify_cart_build_screen import verify as verify_screen
    from benchmark_renderer_history import picture_hash
    objects=[]
    for renderer in (None,'hors-v5-c1','hors-v5-c2'):
        stem=renderer or 'default-v4-easyflash'
        opts=['build','--no-config','--shape','torus','--frames','12','--surface-fill','metallic',
              '--output',stem,'--output-dir',str(out),'--tass',a.tass,'--cartconv',a.cartconv]
        if renderer:opts += ['--renderer',renderer]
        if cli.main(opts):raise ValueError('Build failed: '+stem)
        crt=out/(stem+'.crt');before=hashlib.sha256(crt.read_bytes()).hexdigest()
        meta=json.loads((out/(stem+'-manifest.json')).read_text())
        if int.from_bytes(crt.read_bytes()[22:24],'big')!=32:raise ValueError('Expected EasyFlash')
        proof=verify(crt,a.vice,a.vice_data,cycles=2)
        if hashlib.sha256(crt.read_bytes()).hexdigest()!=before:raise ValueError('VICE changed cart')
        frames=json.loads((ROOT/meta['runtime_work']/'oracle.json').read_text())
        screen=None
        if renderer:
            if meta['build_screen']['version']!='0.8.2':raise ValueError('Build screen version mismatch')
            screen=verify_screen(crt,a.vice,a.vice_data,out/(stem+'-screen'))
        objects.append(dict(renderer=stem,crt_sha256=before,version='0.8.2',build_screen=screen,
                            picture_sha256=picture_hash(frames,meta['screen_color']),verification=proof))
    if len({r['picture_sha256'] for r in objects})!=1:raise ValueError('Candidate pictures differ')
    camera=json.loads((out/'camera/validation.json').read_text())
    result=dict(passed=True,version=(ROOT/'VERSION').read_text().strip(),camera=camera,objects=objects)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
