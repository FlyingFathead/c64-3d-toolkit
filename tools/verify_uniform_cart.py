#!/usr/bin/env python3
"""Check every entry of a uniform-renderer cart in VICE; write per-demo FPS."""
import argparse,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from verify_cart_stream import verify

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path);p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data');p.add_argument('--workers',type=int,default=2);p.add_argument('--report',type=Path);a=p.parse_args()
    m=json.loads(a.crt.with_name(a.crt.stem+'-cart-manifest.json').read_text())
    if not m.get('uniform_renderer'):p.error('requires a uniform-renderer cart')
    def check(i):
        r=verify(a.crt,a.vice,a.vice_data,menu_entry=i);r['name']=m['entries'][i]['name'];print(r['name'],round(r['average_fps'],3),'FPS, pixel/colour match',flush=True);return r
    with ThreadPoolExecutor(max_workers=max(1,min(4,a.workers))) as pool:rows=list(pool.map(check,range(len(m['entries']))))
    out=dict(renderer=m['stream_renderer'],all_entries_verified=True,entries=rows)
    if a.report:a.report.write_text(json.dumps(out,indent=2)+'\n')
