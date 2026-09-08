#!/usr/bin/env python3
"""Run, resume and bundle isolated renderer experiments. No production mutations."""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import compare_renderers as comparison


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


PROTOCOL_KEYS = ('mode', 'exhibition', 'loops', 'seconds_setting', 'ticks_per_second',
                 'pal_clock_hz', 'vice_defaults', 'seed', 'harness')


def measurement_records(result, sizes, report):
    """Verify protocol and raw monitor windows; normalize by measured cycles."""
    if not result.get('entries'): return []
    if any(key not in result for key in PROTOCOL_KEYS):
        raise ValueError('Missing benchmark protocol metadata in '+report)
    protocol = {key: result[key] for key in PROTOCOL_KEYS}
    if protocol['mode'] != 'normal PLAY ALL ONLY' or protocol['exhibition']:
        raise ValueError('Only normal PLAY ALL may be ranked')
    loops=protocol['loops'];seconds=protocol['seconds_setting'];clock=protocol['pal_clock_hz']
    if not isinstance(loops,int) or not 1 <= loops <= 20 or seconds <= 0 or clock != 985248 or protocol['ticks_per_second'] != 50:
        raise ValueError('Unsupported timing protocol in '+report)
    expected=(seconds*50-1)*19656
    records=[];size_entries={e['name']:e for e in sizes.get('entries',[])}
    for e in result['entries']:
        samples=[r for r in result.get('samples',[]) if r['entry']==e['entry']]
        if len(samples)!=loops or {r['loop'] for r in samples} != set(range(loops)):
            raise ValueError('Missing or duplicate observation windows in '+report)
        if any(abs(r['window_cycles']-expected)>=4096 for r in samples):
            raise ValueError('Observation window outside benchmark cycle bound in '+report)
        cycles=sum(r['window_cycles'] for r in samples);flips=sum(r['display_flips'] for r in samples)
        if flips<0 or flips!=e['display_flips'] or not math.isclose(e['observation_seconds'],cycles/clock,rel_tol=0,abs_tol=1e-8):
            raise ValueError('Observation totals disagree with samples in '+report)
        fps=flips*clock/cycles
        if not math.isclose(e['display_fps'],fps,rel_tol=1e-9,abs_tol=1e-9):
            raise ValueError('FPS disagrees with raw cycles in '+report)
        records.append(dict(report=report,animation=e['name'],oracle_sha256=e.get('oracle_sha256'),
            frame_count=e['frame_count'],method=result.get('renderer'),preference=result.get('preference'),
            high_fps=e.get('high_fps'),average_fps=fps,low_fps=e.get('low_fps'),
            display_flips=flips,observation_seconds=cycles/clock,protocol=protocol,
            sizes=size_entries.get(e['name']),cartridge_bytes=sizes.get('crt_bytes')))
    return records


def collect(run):
    """Keep per-method data and honest failure status; do not rank partial runs."""
    state = json.loads((run / 'run.json').read_text())
    work = Path(state['workspace'])
    records = []
    for path in sorted((work / 'results').glob('*-play-all.json')):
        result = json.loads(path.read_text())
        if result.get('exhibition') or not result.get('mode', '').startswith('normal PLAY ALL'):
            continue
        sizes_path = path.with_name(path.name.replace('-play-all.json', '-sizes.json'))
        sizes = json.loads(sizes_path.read_text()) if sizes_path.exists() else {}
        records.extend(measurement_records(result, sizes, path.name))
    summary = dict(status=state['status'], scope=state['options'],
        note='Uncapped normal PLAY ALL measurements. Paced experiments, pixel checks, '
             'unsupported combinations and authored-scene diagnostics remain in raw reports. '
             'Do not rank a partial run or compare different oracle hashes/settings.',
        records=records)
    summary['analysis_sha256'] = digest(__file__)
    summary['recommendations'] = recommend(records, state)
    save(run / 'summary.json', summary)
    return summary


def recommend(records, state):
    if state['status'] != 'completed': return {'status': 'incomplete; no winners'}
    options = state['options']
    if options.get('max_fps') or options.get('lock_to_min_fps'):
        return {'status': 'paced experiment; no uncapped winner selection'}
    groups = {}
    rejected = []
    for row in records:
        if options.get('stream_only') and row['method'] in comparison.RESIDENT:
            rejected.append(dict(animation=row['animation'], report=row['report'], reason='resident backend excluded'))
            continue
        limit = options.get('max_cart_bytes')
        if limit is not None and (row['cartridge_bytes'] is None or row['cartridge_bytes'] > limit):
            rejected.append(dict(animation=row['animation'], report=row['report'], reason='whole comparison cartridge exceeds budget or size unknown'))
            continue
        groups.setdefault(row['animation'], []).append(row)
    winners = []
    for name, rows in groups.items():
        if None in {r['oracle_sha256'] for r in rows} or len({r['oracle_sha256'] for r in rows}) != 1:
            raise ValueError('Different or missing source oracle for '+name)
        protocols={json.dumps(r['protocol'],sort_keys=True) for r in rows}
        if len(protocols)!=1 or len({r['frame_count'] for r in rows})!=1:
            raise ValueError('Different benchmark settings or frame counts for '+name)
        for row in rows:
            protocol=row['protocol']
            expected=protocol['loops']*(protocol['seconds_setting']*50-1)*19656
            if not math.isfinite(row['observation_seconds']) or abs(row['observation_seconds']*protocol['pal_clock_hz']-expected)>=protocol['loops']*4096:
                raise ValueError('Observation duration outside benchmark cycle bound for '+name)
        best = max(r['average_fps'] for r in rows)
        winners.append(dict(animation=name,
            winners=[r['report'] for r in rows if math.isclose(r['average_fps'],best,rel_tol=0,abs_tol=1e-9)],
            average_fps=best,candidates=len(rows),
            ranking_metric='display_flips / measured observation_seconds',
            caution='Numerical leader; small differences need independent repeat runs.'))
    return dict(status='measured per-demo recommendations; not an assembled unified renderer',
                winners=winners, rejected=rejected)


def bundle(run):
    collect(run)
    work = Path(json.loads((run/'run.json').read_text())['workspace'])
    target = run.parent / (run.name + '-results.zip')
    if target.exists():
        raise SystemExit('Results bundle exists; choose another run ID instead of overwriting it.')
    paths = [run / n for n in ('run.json', 'summary.json', 'pipeline.log') if (run / n).exists()]
    paths += list((run/'stages').glob('*.json'))
    paths += list(run.glob('*.jsonl'))
    paths += list((work / 'results').glob('*.json'))
    paths += list(work.glob('*.log'))
    paths += [p for p in (work / 'provenance.json', work / 'PERFORMANCE_COMPARISON.md') if p.exists()]
    # Include the actual tool provenance even if the underlying filename changes.
    paths += list(work.glob('*provenance*.json'))
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(paths)):
            z.write(p, str(p.relative_to(run)) if p.is_relative_to(run) else 'work/'+str(p.relative_to(work)))
    target.with_suffix('.zip.sha256').write_text(digest(target) + '  ' + target.name + '\n')
    print(target)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['plan', 'run', 'resume', 'status', 'summarize', 'bundle'])
    p.add_argument('--id', default=None, help='unique run ID; required except for plan')
    p.add_argument('--profile', choices=['pilot', 'full'], default='pilot')
    p.add_argument('--methods', nargs='+')
    p.add_argument('--stream-only', action='store_true', help='exclude resident backends from recommendations')
    p.add_argument('--max-cart-bytes', type=int, help='whole comparison CRT size budget; not free RAM')
    p.add_argument('--workers', type=int, default=2)
    p.add_argument('--loops', type=int, default=3)
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', type=Path)
    source = p.add_mutually_exclusive_group()
    source.add_argument('--reference-json', type=Path)
    source.add_argument('--current-demos', action='store_true')
    pacing = p.add_mutually_exclusive_group()
    pacing.add_argument('--max-fps', type=int)
    pacing.add_argument('--lock-to-min-fps', action='store_true')
    a = p.parse_args()
    if a.id is None:
        if a.action != 'plan': p.error('--id is required')
        a.id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')
    if not a.id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a.id):
        p.error('run ID may contain only letters, digits, hyphens and underscores')
    run = ROOT / 'logs' / a.id
    work = ROOT / 'comparison-tests' / 'runs' / a.id
    if a.action in ('status', 'summarize', 'bundle'):
        if not (run / 'run.json').exists(): p.error('unknown run ID')
        if a.action == 'bundle': bundle(run)
        elif a.action == 'summarize':
            summary=collect(run)
            print('Recovered summary:', run/'summary.json')
            print('Ranked animations:',len(summary['recommendations'].get('winners',[])))
        else:
            state=json.loads((run/'run.json').read_text());print(json.dumps(state,indent=2))
            print('Completed JSON reports:', len(list((Path(state['workspace'])/'results').glob('*.json'))))
        return
    if a.action == 'resume':
        state = json.loads((run / 'run.json').read_text())
        if state['source_fingerprint'] != comparison.fingerprints(ROOT)[1] or state['pipeline_sha256'] != digest(__file__):
            p.error('inputs changed; use a new run ID')
        cmd = state['command'] + ['--resume']
    else:
        if a.workers < 1 or a.loops < 1: p.error('workers and loops must be positive')
        methods = a.methods or (['step', 'yunroll', 'yunroll-cart-v9'] if a.profile == 'pilot' else [])
        if any(m not in {m for m, _ in comparison.METHODS} for m in methods): p.error('unsupported method')
        cmd = [sys.executable, str(ROOT/'tools/compare_renderers.py'), '--workspace', str(work),
               '--workers', str(a.workers), '--loops', str(a.loops)]
        for name in ('tass', 'cartconv', 'vice'):
            value = getattr(a, name); resolved = shutil.which(value)
            if a.action == 'run' and not resolved: p.error('executable not found: '+value)
            cmd += ['--'+name, resolved or value]
        if a.vice_data: cmd += ['--vice-data', str(a.vice_data.resolve())]
        elif a.action == 'run': p.error('--vice-data is required')
        if methods: cmd += ['--methods'] + methods
        if a.reference_json: cmd += ['--reference-json', str(a.reference_json.resolve())]
        if a.current_demos: cmd += ['--current-demos']
        if a.max_fps is not None: cmd += ['--max-fps', str(a.max_fps)]
        if a.lock_to_min_fps: cmd += ['--lock-to-min-fps']
        state = dict(status='planned', workspace=str(work), source_fingerprint=comparison.fingerprints(ROOT)[1],
                     pipeline_sha256=digest(__file__), command=cmd,
                     options=dict(stream_only=a.stream_only, max_cart_bytes=a.max_cart_bytes, profile=a.profile, methods=methods, loops=a.loops,
                                  max_fps=a.max_fps, lock_to_min_fps=a.lock_to_min_fps,
                                  current_demos=a.current_demos, reference_json=str(a.reference_json) if a.reference_json else None))
        if a.action == 'plan': print(json.dumps(state, indent=2)); return
        if run.exists() or work.exists(): p.error('run ID exists; use resume or a new ID')
        run.mkdir(parents=True)
    state['status'] = 'running'; save(run/'run.json', state)
    try:
        with (run/'pipeline.log').open('a') as log:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                for line in proc.stdout:
                    print(line, end='', flush=True); log.write(line); log.flush()
                code = proc.wait()
            except KeyboardInterrupt:
                proc.wait(); raise
        state['status'] = 'completed' if code == 0 else 'failed'
        state['exit_code'] = code
    except KeyboardInterrupt:
        state['status'] = 'interrupted'; code = 130
    save(run/'run.json', state)
    collect(run)
    print('Results:', run)
    raise SystemExit(code)

if __name__ == '__main__': main()
