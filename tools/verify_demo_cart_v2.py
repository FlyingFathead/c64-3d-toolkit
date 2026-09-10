#!/usr/bin/env python3
"""Verify each preview menu entry, then measure three normal PLAY ALL visits."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import json


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('crt',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--vice',default='x64sc');ap.add_argument('--vice-data',required=True)
    ap.add_argument('--jobs',type=int,default=2)
    ap.add_argument('--capture',action='store_true')
    a=ap.parse_args()
    if a.jobs<1:ap.error('--jobs must be positive')
    from c643d.cartpaths import menu_manifest_path
    from verify_cart_stream import verify
    from benchmark_play_all import benchmark
    a.crt=a.crt.resolve();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=True)
    meta=json.loads(menu_manifest_path(a.crt).read_text())
    if not meta.get('preview',{}).get('new_dataset'):ap.error('Requires a matching Demo Cart 2.0 preview build')
    def entry(i):
        capture=a.out/f'entry-{i:02d}' if a.capture else None
        proof=verify(a.crt,a.vice,a.vice_data,cycles=2,menu_entry=i,capture=capture)
        (a.out/f'entry-{i:02d}.json').write_text(json.dumps(proof,indent=2)+'\n')
        print(meta['streamed_entries'][i]['name'],'bitmap/colour PASS',flush=True)
        return proof
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        proofs=list(pool.map(entry,range(len(meta['streamed_entries']))))
    result=benchmark(a.crt,a.vice,a.vice_data,loops=3)
    result['pixel_verification']=proofs
    result['scope']='New Demo Cart 2.0 material; not the frozen canonical 12-animation release comparison.'
    (a.out/'play-all.json').write_text(json.dumps(result,indent=2)+'\n')
    table=['| Animation | Samples | High FPS | Display FPS | Low FPS | Worst display ms |',
           '| --- | ---: | ---: | ---: | ---: | ---: |']
    for e in result['entries']:
        table.append(f"| {e['name']} | {e['frame_count']} | {e['high_fps']:.2f} | {e['display_fps']:.2f} | {e['low_fps']:.2f} | {e['worst_display_ms']:.2f} |")
    text='\n'.join(table)
    (a.out/'play-all.md').write_text('# Demo Cart 2.0 preview measurements\n\n'+result['scope']+'\n\n'+text+'\n\n'+result['method']+'\n')
    print(text,flush=True)


if __name__=='__main__':
    main()
