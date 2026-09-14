#!/usr/bin/env python3
"""Build Demo Cart v3.1 interactive, or explicitly rebuild the preserved v3.0 benchmark."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from c643d.gmod3_catalog import inventory
from c643d.gmod3_collection import build


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--variant',choices=('interactive','benchmark','both'),default='interactive')
    p.add_argument('--refresh-inventory',action='store_true')
    a=p.parse_args()
    if a.refresh_inventory or not (ROOT/'build/gmod3-catalog/catalog.json').exists():inventory(ROOT)
    for interactive in (True,False):
        if a.variant=='interactive' and not interactive or a.variant=='benchmark' and interactive:continue
        build(ROOT,tass=a.tass,cartconv=a.cartconv,outdir=a.output_dir,interactive=interactive)

if __name__=='__main__':main()
