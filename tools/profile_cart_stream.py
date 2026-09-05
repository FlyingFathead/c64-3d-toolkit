#!/usr/bin/env python3
"""Measure standalone streamed-cart stages in VICE, after three warm-up frames.

Elapsed emulated PAL cycles include display stalls and IRQs. Reports one full
rotation. Rebuild the cart first so its matching labels and manifest are present.
"""
from pathlib import Path
import argparse,json,re,subprocess,tempfile
from verify_cart_stream import labels


def profile(crt,vice,vice_data=None):
    crt=Path(crt).resolve();sym=labels(crt.with_suffix('.lbl'))
    manifest=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text());n=manifest['frames']
    names=['fetch','recycle_bitmap_and_colors','cache_metadata']
    if manifest['colors']:names+=['apply_colors']
    names+=['draw_lines','handoff_and_counters'];k=len(names)
    # The main loop begins with one JSR per stage. The last boundary is the
    # drawing-complete call site, avoiding repeated hits in publish_wait.
    with tempfile.TemporaryDirectory(prefix='c643d-profile-') as td:
        td=Path(td);mon=['delete']+[f'break ${sym["frame_begin"]+3*i:04x}' for i in range(k)]
        for _ in range((n+4)*k):mon+=['g','stopwatch']
        mon+=['quit'];(td/'run.mon').write_text('\n'.join(mon)+'\n')
        cmd=[vice,'-console','+sound','-warp','-seed','1','-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(td/'run.mon'),'-monlog','-monlogname',str(td/'monitor.log'),'-limitcycles',str((n+4)*1000000+2000000)]
        if vice_data:cmd+=['-directory',str(vice_data)]
        with (td/'vice.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
        ticks=[int(x) for x in re.findall(r'Stopwatch:\s*(\d+)',(td/'monitor.log').read_text())]
        if len(ticks)!=(n+4)*k:raise AssertionError('VICE did not reach every stage boundary')
        sums=[sum(ticks[i+1]-ticks[i] for i in range(3*k+j,3*k+k*n,k)) for j in range(k)]
    return dict(cartridge=crt.name,renderer=manifest['renderer'],orientations=n,mean_cycles=dict(zip(names,[round(x/n,2) for x in sums])),percent=dict(zip(names,[round(x/sum(sums)*100,2) for x in sums])))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path);p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data');p.add_argument('--report',type=Path);a=p.parse_args()
    text=json.dumps(profile(a.crt,a.vice,a.vice_data),indent=2);print(text)
    if a.report:a.report.write_text(text+'\n')
