#!/usr/bin/env python3
"""Rebuild, verify and compare stable v2 with at most --jobs VICE workers."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--workspace',type=Path,required=True)
    ap.add_argument('--jobs',type=int,default=3)
    ap.add_argument('--tass',default='64tass');ap.add_argument('--cartconv',default='cartconv')
    ap.add_argument('--vice',default='x64sc');ap.add_argument('--vice-data',required=True)
    ap.add_argument('--extended-search',action='store_true',help='Also search raw plans and minimum holds 2, 3 and 4 (56 candidates total)')
    a=ap.parse_args();a.workspace=a.workspace.expanduser().resolve()
    if a.jobs<1:ap.error('--jobs must be positive')
    if a.workspace.exists():ap.error('--workspace must be a new directory')
    a.workspace.mkdir(parents=True)
    def run(name,command):
        print('\n'+name,flush=True)
        with (a.workspace/(name+'.log')).open('w') as log:
            proc=subprocess.Popen([sys.executable,*command],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in proc.stdout:
                print(line,end='',flush=True);log.write(line)
            if proc.wait():raise RuntimeError(name+' failed; see its log')
    carts=a.workspace/'carts'
    for renderer,short in [('hors-render-v1','v1'),('hors-render-v2','v2')]:
        run('build-'+short,['tools/build_demo_cart_v2.py','--renderer',renderer,'--output-dir',str(carts),
            '--tass',a.tass,'--cartconv',a.cartconv])
        run('measure-'+short,['tools/verify_demo_cart_v2.py',str(carts/f'demo-cart-2-preview-hors-{short}.crt'),
            '--out',str(a.workspace/short),'--jobs',str(a.jobs),'--vice',a.vice,'--vice-data',a.vice_data])
    run('ripples-search',['tools/autotune_scene.py','examples/cart_demos_v2/scenes/ripples_lite.c643dscene',
        '--out',str(a.workspace/'ripples-search'),'--mono','--width','320','--jobs',str(a.jobs),
        '--ticks',*(['1','2','3','4'] if a.extended_search else ['1']),
        '--plans',*(['optimized','raw'] if a.extended_search else ['optimized']),
        '--gaps','3','6','10','--batches','1024','2048','--tass',a.tass,'--cartconv',a.cartconv,
        '--vice',a.vice,'--vice-data',a.vice_data])
    left=json.loads((a.workspace/'v1/play-all.json').read_text())
    right=json.loads((a.workspace/'v2/play-all.json').read_text())
    table=['| New menu scene | v1 FPS | v2 FPS | Change |','| --- | ---: | ---: | ---: |']
    for x,y in zip(left['entries'],right['entries'],strict=True):
        if x['oracle_sha256']!=y['oracle_sha256']:raise AssertionError('A/B source oracle mismatch')
        table.append(f"| {x['name']} | {x['display_fps']:.2f} | {y['display_fps']:.2f} | {(y['display_flips']/x['display_flips']-1)*100:+.2f}% |")
    text='\n'.join(table)
    (a.workspace/'COMPARISON.md').write_text('# Local hors-render-v2 check\n\n'+text+'\n\nNormal PLAY ALL, three visits at ten seconds each. New Demo Cart 2.0 material; not the original release matrix. Change uses display counts to avoid ranking timer-phase noise.\n')
    files=[p for p in a.workspace.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt']
    (a.workspace/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(a.workspace).as_posix()+'\n' for p in sorted(files)))
    print('\n'+text+'\n\nResults:',a.workspace,flush=True)


if __name__=='__main__':
    main()
