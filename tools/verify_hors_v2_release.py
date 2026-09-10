#!/usr/bin/env python3
"""Verify every stable v2 example, including native finite scene endings."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from c643d.cartpaths import menu_manifest_path
from c643d.released_examples import is_current_v2_example
from verify_cart_stream import verify
from verify_cart_ending import verify as verify_ending
from verify_hifi_reel import verify as verify_reel

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--jobs',type=int,default=3)
    a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    if a.jobs<1:p.error('--jobs must be positive')
    carts=sorted(p for p in (ROOT/'examples').rglob('*.crt') if
        is_current_v2_example(p,(ROOT/'VERSION').read_text().strip()))
    if len(carts)<19:raise ValueError('Release is missing stable v2 examples')
    jobs=[]
    for crt in carts:
        menu=menu_manifest_path(crt)
        if menu.exists():
            meta=json.loads(menu.read_text())
            jobs.extend((crt,i) for i in range(len(meta['streamed_entries'])))
        else:jobs.append((crt,None))
    def check(job):
        crt,i=job
        result=verify(crt,a.vice,a.vice_data,menu_entry=i)
        result.update(path=crt.relative_to(ROOT).as_posix(),entry=i,
            sha256=hashlib.sha256(crt.read_bytes()).hexdigest())
        (a.out/(crt.stem+('' if i is None else f'-{i:02d}')+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(crt.name,i,'PASS',flush=True)
        return result
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:results=list(pool.map(check,jobs))
    marbles=next(p for p in carts if p.parent.name=='cart_marbles')
    ending=verify_ending(marbles,a.vice,a.vice_data,a.out/'marbles-ending')
    (a.out/'marbles-ending.json').write_text(json.dumps(ending,indent=2)+'\n')
    for crt in carts:
        if crt.parent.name=='cart_demos':
            subprocess.run([sys.executable,str(ROOT/'tools/verify_cart_menu.py'),str(crt),
                '--vice',a.vice,'--vice-data',a.vice_data,'--report',str(a.out/(crt.stem+'-menu.json'))],check=True)
        if crt.parent.name in ('cart_demos','cart_hifi'):
            result=verify_reel(crt,a.vice,a.vice_data)
            (a.out/(crt.stem+'-reel.json')).write_text(json.dumps(result,indent=2)+'\n')
    summary=dict(passed=True,cartridges=len(carts),checks=len(results),
        verified_pictures=sum(x['verified_frames'] for x in results),native_ending=ending,
        carts=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in carts])
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Release example verification PASS:',len(carts),'cartridges',flush=True)


if __name__=='__main__':main()
