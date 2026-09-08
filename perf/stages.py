#!/usr/bin/env python3
"""Profile a saved candidate's stages. Diagnostic timing, not PLAY ALL FPS."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id',required=True)
    p.add_argument('--method',default='yunroll-cart-v9')
    p.add_argument('--ram',action='store_true')
    p.add_argument('--entry',type=int,nargs='+',help='zero-based menu entries; default all')
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.id) or not re.fullmatch(r'[A-Za-z0-9_-]+',a.method):p.error('invalid ID/method')
    run=ROOT/'logs'/a.id;state=json.loads((run/'run.json').read_text())
    if state['status']!='completed':p.error('wait for a completed run before profiling')
    if state['options'].get('max_fps') or state['options'].get('lock_to_min_fps'):p.error('use an uncapped run for stage diagnostics')
    work=Path(state['workspace']);cmd=state['command'];arg=lambda key:cmd[cmd.index(key)+1]
    name=a.method+('-ram' if a.ram else '');crt=work/'carts'/(name+'.crt')
    if not crt.exists():p.error('candidate not built in this run')
    sys.path.insert(0,str(work/'source/tools'))
    from profile_cart_stream import profile
    from verify_cart_stream import menu_manifest_path
    manifest=json.loads(menu_manifest_path(crt).read_text())
    entries=manifest['streamed_entries'];indices=a.entry if a.entry is not None else range(len(entries))
    if any(i<0 or i>=len(entries) for i in indices):p.error('entry index outside menu')
    out=run/'stages';out.mkdir(exist_ok=True)
    for i in indices:
        dest=out/f'{name}-{i:02d}.json'
        if dest.exists():p.error('profile exists: '+str(dest)+'; use a new run to repeat')
        print('Profiling',name,i,entries[i]['name'],flush=True)
        try: result=profile(crt,arg('--vice'),arg('--vice-data'),menu_entry=i)
        except (KeyError,ValueError) as e:
            if isinstance(e,ValueError) and 'profiling labels' not in str(e):raise
            result=dict(status='unsupported stage labels',reason=str(e))
        result.update(profiler_runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),diagnostic_only=True,animation=entries[i]['name'],candidate=name,
                      cartridge_sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
                      baseline_source_fingerprint=state['source_fingerprint'])
        dest.write_text(json.dumps(result,indent=2)+'\n')
        means=result.get('mean_cycles',{})
        if means:
            active={k:v for k,v in means.items() if 'wait' not in k and k not in ('publish_commit','advance_and_final_hold')}
            print('Stage cycles:',json.dumps(means),flush=True)
            print('Largest measured non-wait stage:',max(active,key=active.get) if active else 'unknown',flush=True)
        else:print(result['status'],flush=True)

if __name__=='__main__':main()
