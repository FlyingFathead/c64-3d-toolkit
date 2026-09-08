#!/usr/bin/env python3
"""Rebuild V2-V8 with current and pristine v0.6.8 builders; compare all bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

BASE='5025172'


def probe(root,tass):
    sys.path.insert(0,str(root/'tools'))
    from c643d.cartuniform import prepare
    from c643d.cartframes import load_menu_reference
    sources=load_menu_reference(root);result={}
    for variant,preference in [(f'v{i}','fps') for i in range(2,9)]+[('v7','ram'),('v8','ram')]:
        entries,image,info,used,first=prepare(root,'yunroll-cart-'+variant,tass,sources=sources,prefer=preference)
        result[variant+'-'+preference]=dict(runtimes=[hashlib.sha256(p.read_bytes()).hexdigest() for _,p in entries],
                                          frame_image=hashlib.sha256(image).hexdigest())
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--tass',default='64tass')
    p.add_argument('--report',type=Path,default=Path('docs/benchmarks/v9/legacy-preservation.json'))
    p.add_argument('--probe',type=Path,help=argparse.SUPPRESS);a=p.parse_args()
    if a.probe:
        a.probe.write_text(json.dumps(probe(Path.cwd(),a.tass),indent=2)+'\n');return
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='c643d-v8-preservation-') as tmp:
        tmp=Path(tmp);baseline=tmp/'baseline';baseline.mkdir()
        archive=tmp/'base.tar'
        subprocess.run(['git','archive','--format=tar','--output',str(archive),BASE],cwd=root,check=True)
        with tarfile.open(archive) as tar:tar.extractall(baseline,filter='data')
        reports=[]
        for name,directory in [('baseline',baseline),('current',root)]:
            path=tmp/(name+'.json')
            with (tmp/(name+'.log')).open('w') as log:
                subprocess.run([sys.executable,str(Path(__file__).resolve()),'--tass',a.tass,'--probe',str(path)],
                               cwd=directory,stdout=log,stderr=subprocess.STDOUT,check=True)
            reports.append(json.loads(path.read_text()))
            print(name,'built',flush=True)
        assert reports[0]==reports[1],'Historical runtime or frame image changed'
    report=dict(base_commit=BASE,all_identical=True,runtimes_compared=sum(len(v['runtimes']) for v in reports[0].values()),
                frame_images_compared=len(reports[0]),variants=reports[0])
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print('All historical builds byte-identical',flush=True)


if __name__=='__main__':main()
