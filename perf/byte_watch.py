#!/usr/bin/env python3
"""Second-terminal viewer for byte_candidates.py; never starts VICE."""
import argparse,json,sys,time,re
from pathlib import Path
import pipeline,watch


def snapshot(logs, pref):
    records=[];states=[];errors=[]
    for p in sorted(logs.glob('*/candidate.json')):
        state=watch.read_json(p)
        if not state:continue
        states.append(state)
        work=Path(state['work']);stem='yunroll-cart-v9'+('-ram' if pref=='ram' else '')
        result=watch.read_json(work/'results'/(stem+'-play-all.json'))
        sizes=watch.read_json(work/'results'/(stem+'-sizes.json')) or {}
        if result:
            try:
                rows=pipeline.measurement_records(result,sizes,state['policy']+'-play-all.json')
                for row in rows:row['policy']=state['policy']
                records+=rows
            except (ValueError,KeyError,TypeError) as e:errors.append(str(e))
    experiment=watch.read_json(logs/'experiment.json') or {}
    terminal=bool(states) and len(states)==len(experiment.get('policies',[])) and all(s['status'] in ('completed','infeasible','failed','profile-failed') for s in states)
    # Timings shown before pixel/stage verification are explicitly provisional.
    provisional=not terminal or any(s['status'] not in ('completed','infeasible') for s in states)
    eligible=[r for r in records if not terminal or next(s['status'] for s in states if s['policy']==r['policy'])=='completed']
    try:ranking=pipeline.recommend(eligible,dict(status='completed',options={})) if not errors else {'status':'; '.join(errors)}
    except ValueError as e:ranking={'status':str(e)}
    tails=[]
    for state in states:
        path=logs/state['policy']/('stages.log' if (logs/state['policy']/'stages.log').exists() else 'run.log')
        try:
            with path.open('rb') as f:
                f.seek(0,2);n=f.tell();f.seek(max(0,n-1200));lines=f.read().decode(errors='replace').splitlines()
            last=lines[-1] if lines else ''
        except OSError:last=''
        tails.append(dict(worker=state['policy']+' ['+state['status']+']',last_line=last))
    return dict(status=('completed' if terminal else 'running')+' / '+pref,terminal=terminal,
                provisional=provisional,records=eligible,leaders=ranking.get('winners',[]),
                ranking_status=ranking['status'],reports=len(records),worker_tails=tails)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--id',required=True)
    p.add_argument('--ram',action='store_true');p.add_argument('--json',action='store_true');p.add_argument('--once',action='store_true')
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.id):p.error('invalid ID')
    try:
        while True:
            data=snapshot(pipeline.ROOT/'logs'/a.id,'ram' if a.ram else 'fps')
            if a.json:print(json.dumps(data),flush=True)
            else:
                if sys.stdout.isatty() and not a.once:print('\033[2J\033[H',end='')
                print(watch.render(data),flush=True)
            if a.once or data['terminal']:break
            time.sleep(2)
    except KeyboardInterrupt:pass

if __name__=='__main__':main()
