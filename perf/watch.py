#!/usr/bin/env python3
"""Read-only live viewer. JSON results appear when each measurement completes."""
import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import textwrap
import sys
import time
import pipeline


def read_json(path):
    try: return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError): return None


def snapshot(run):
    state=read_json(run/'run.json')
    if state is None: return dict(status='waiting for run manifest',records=[],leaders=[])
    work=Path(state['workspace']);records=[];unsupported=[];errors=[]
    for path in sorted((work/'results').glob('*-play-all.json')):
        result=read_json(path)
        if not result or result.get('exhibition') or not result.get('mode','').startswith('normal PLAY ALL'):continue
        sizes=read_json(path.with_name(path.name.replace('-play-all.json','-sizes.json'))) or {}
        try: records.extend(pipeline.measurement_records(result,sizes,path.name))
        except (ValueError,KeyError,TypeError) as e: errors.append(path.name+': '+str(e))
    for path in sorted((work/'results').glob('*-unsupported.json')):
        data=read_json(path)
        if isinstance(data,list):unsupported.extend(dict(method=path.stem,**row) for row in data)
    # Display partial leaders, explicitly provisional until all workers verify.
    provisional=dict(state,status='completed')
    try: ranking=pipeline.recommend(records,provisional) if not errors else {'status':'Invalid measurement reports: '+'; '.join(errors)}
    except ValueError as e: ranking={'status':str(e)}
    tails=[]
    for path in sorted(work.glob('*.log')):
        try:
            with path.open('rb') as f:
                f.seek(0,2);size=f.tell();f.seek(max(0,size-2048));text=f.read().decode(errors='replace')
            lines=text.splitlines()
            if lines:tails.append(dict(worker=path.name,last_line=lines[-1]))
        except OSError:pass
    return dict(timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),status=state['status'],
        provisional=state['status']!='completed',records=records,
        leaders=ranking.get('winners',[]),ranking_status=ranking['status'],
        unsupported=unsupported,worker_tails=tails,
        reports=len(list((work/'results').glob('*.json'))))


def clean(value):
    # Worker output and custom names must not inject terminal controls.
    return ''.join(c if c.isprintable() else ' ' for c in str(value))


def render(data, width=None):
    width = max(20, (width or shutil.get_terminal_size((100,24)).columns)-1)
    lines=['C64 candidate measurements | '+clean(data['status']),
           'PROVISIONAL: available measurements only; correctness/jobs may still be pending.' if data.get('provisional',True)
           else 'Completed run. Leaders are per-demo candidates, not a unified cartridge.',
           'FPS updates when a method benchmark finishes. Host wall time is not C64 FPS.',
           'Reports: '+str(data.get('reports',0)), '']
    rows={ (r['animation'],r['report']):r for r in data['records'] }
    lines.append(f"{'Animation':22} {'Leader':12} {'High':>7} {'Avg':>7} {'Low':>7} {'CRT B':>9}")
    def number(v):return 'N/A' if v is None else f'{v:.2f}'
    for leader in data.get('leaders',[]):
        for winner in leader['winners']:
            r=rows[(leader['animation'],winner)]
            label=winner.removesuffix('-play-all.json').replace('yunroll-cart-v','V').replace('-ram',' RAM')
            lines.append(f"{clean(r['animation'])[:22]:22} {clean(label)[:12]:12} {number(r['high_fps']):>7} {number(r['average_fps']):>7} {number(r['low_fps']):>7} {str(r['cartridge_bytes'] or 'N/A'):>9}")
    if not data.get('leaders'):lines.append(clean(data.get('ranking_status','Waiting for completed measurements.')))
    lines+=['', 'Unsupported combinations: '+str(len(data.get('unsupported',[]))), 'Latest worker messages:']
    for row in data.get('worker_tails',[]):lines.append(clean(row['worker']+': '+row['last_line'])[:180])
    return '\n'.join(part for line in lines for part in (textwrap.wrap(line,width=width,replace_whitespace=False) or ['']))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id',required=True)
    p.add_argument('--interval',type=float,default=2)
    p.add_argument('--json',action='store_true',help='emit newline-delimited JSON snapshots to stdout')
    p.add_argument('--once',action='store_true')
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.id) or a.interval<0.2:p.error('invalid ID or interval below 0.2 seconds')
    run=pipeline.ROOT/'logs'/a.id
    try:
        while True:
            data=snapshot(run)
            if a.json:print(json.dumps(data),flush=True)
            else:
                if sys.stdout.isatty() and not a.once:print('\033[2J\033[H',end='')
                print(render(data),flush=True)
            if a.once or data['status'] in ('completed','failed','interrupted'):break
            time.sleep(a.interval)
    except KeyboardInterrupt:pass

if __name__=='__main__':main()
