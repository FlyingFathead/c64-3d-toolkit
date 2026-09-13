#!/usr/bin/env python3
"""Build SAKU carts, including eight presentations in one interactive cartridge."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
VARIANTS={
    'solid':('saku_2026-solid',['--fill-style','solid','--background-color','white','--border-color','white']),
    'gradient':('saku_2026-gradient',['--fill-style','gradient']),
    'interactive':('saku_2026-interactive',['--fill-style','gradient','--interactive-cart','--svg-presentation-modes','--starfield-default','enabled','--starfield-profile','light',
        '--svg-background-card',str(HERE/'saku_2026-rounded-card.svg'),'--svg-outline-variant',str(HERE/'saku_2026-white-outline.svg')]),
}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--output-dir',type=Path,default=HERE/'cartridges')
    p.add_argument('--variants',nargs='+',choices=tuple(VARIANTS),default=list(VARIANTS))
    a=p.parse_args();out=a.output_dir.resolve()
    for key in a.variants:
        stem,extra=VARIANTS[key]
        svg='saku_2026-white-outline.svg' if key=='gradient' else 'saku_2026.svg'
        subprocess.run([sys.executable,str(ROOT/'c643d.py'),'build','--svg',str(HERE/svg),
            '--name','SAKU 2026','--svg-depth','3','--frames','30' if key=='interactive' else '48','--spin-axis','y',
            '--output',stem,'--output-dir',str(out),'--overwrite-policy','allow',
            '--tass',a.tass,'--cartconv',a.cartconv,*extra],cwd=ROOT,check=True)
        meta=json.loads((out/(stem+'-manifest.json')).read_text())
        assert meta['frames']==(240 if key=='interactive' else 48)
        oracle=out/(stem+'-oracle.json')
        oracle.with_suffix('.json.gz').write_bytes(gzip.compress(oracle.read_bytes(),mtime=0))
        oracle.unlink()
    print('SAKU cartridges:',out)

if __name__=='__main__':main()
