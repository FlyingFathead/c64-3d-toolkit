#!/usr/bin/env python3
"""Optional authored Marbles policy benchmark; leaves shipped artifacts intact."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import byte_candidates as candidates
import pipeline

ROOT = Path(__file__).resolve().parents[1]


def metrics(profiles):
    if not profiles:
        raise ValueError('No profiles')
    sha = profiles[0]['sha256']
    samples = []
    budget = profiles[0]['render_budget_cycles']
    for p in profiles:
        if p['sha256'] != sha or p['clock_hz'] != 985248 or p['render_budget_cycles'] != budget:
            raise ValueError('Mismatched measurement inputs')
        if len(p['samples']) != p['frames'] or [s['frame'] for s in p['samples']] != list(range(p['frames'])):
            raise ValueError('Incomplete frame coverage')
        samples += p['samples']
    costs = [s['render_cycles'] for s in samples]
    totals = [s['total_cycles'] for s in samples]
    if min(costs + totals) <= 0:
        raise ValueError('Non-positive timing')
    return dict(repeats=len(profiles), frames_per_repeat=profiles[0]['frames'],
                mean_render_cycles=sum(costs)/len(costs), worst_render_cycles=max(costs),
                render_over_budget=sum(c > budget for c in costs), measured_samples=len(costs),
                profile_interval_fps_high=985248/min(totals),
                profile_interval_fps_avg=985248*len(totals)/sum(totals),
                profile_interval_fps_low=985248/max(totals),
                mean_profile_seconds=sum(totals)/985248/len(profiles))


def worker(a):
    src = a.workspace/'source'
    sys.path.insert(0, str(src/'tools'))
    from c643d.cartframes import load_scene_source
    from c643d import cartscene
    from verify_cart_stream import verify
    from profile_cart_stream import profile
    from verify_cart_ending import verify as ending
    frames, scene, ref = load_scene_source(src/'../c64-3d-toolkit-history/examples/cart_marbles/history/dont_lose_your_marbles-yunroll-cart-v4-scene-clean.crt')
    oracle = a.workspace/'oracle.json'
    oracle.write_text(json.dumps([asdict(f) for f in frames]))
    for pref in a.preferences:
        for overlay in a.overlays:
            stem = f'marbles-{a.policy}-{pref}-{overlay}'
            result_path = a.output/(stem+'.json')
            out = a.workspace/'carts'
            out.mkdir(exist_ok=True)
            cartscene.assemble_scene(src, frames, scene, tass=a.tass, cartconv=a.cartconv,
                outdir=out, stem=stem, hud_text=ref['hud_text'], frame_ticks=ref['frame_ticks'],
                colors=ref['colors'], color_index=ref['screen_color']>>4,
                intro=True, ending=True, text_overlay=overlay=='hud',
                renderer='yunroll-cart-v9-scene', prefer=pref)
            crt=out/(stem+'.crt')
            pixels=verify(crt,a.vice,a.vice_data,oracle_path=oracle)
            profiles=[]
            for i in range(a.repeats):
                profiles.append(profile(crt,a.vice,a.vice_data))
                print(stem, f'profile {i+1}/{a.repeats}', flush=True)
            finish=ending(crt,a.vice,a.vice_data,a.workspace/'endings'/stem) if a.check_ending else None
            result=dict(policy=a.policy,preference=pref,overlay=overlay,status='passed',
                cartridge_bytes=crt.stat().st_size,cartridge_sha256=pipeline.digest(crt),
                oracle_sha256=pipeline.digest(oracle),pixels=pixels,profiles=profiles,
                ending=finish,metrics=metrics(profiles))
            pipeline.save(result_path,result)
            print(stem,'PASS',crt.stat().st_size,'bytes',flush=True)


def summary(logs):
    rows=[json.loads(p.read_text()) for p in sorted(logs.glob('results/*.json'))]
    config=json.loads((logs/'run.json').read_text())
    expected=len(config['policies'])*len(config['preferences'])*len(config['overlays'])
    for row in rows:
        row['metrics']=metrics(row['profiles'])
    if len({r['oracle_sha256'] for r in rows})>1:
        raise ValueError('Reference pictures differ')
    result=dict(complete=len(rows)==expected,expected=expected,completed=len(rows),records=rows)
    pipeline.save(logs/'summary.json',result)
    lines=['# Authored Marbles byte-policy comparison','',
        '*Measured seconds: scene-start-to-ending scene measurement with --check-ending; otherwise profiler interval duration including final hold.\n\nIndependent V9 scene builds. PAL, fixed seed, original 200 samples and authored pacing. Render cycles include VIC/IRQ interference. Interval FPS is derived from profiler boundaries, NOT menu display-flip FPS. Ending scene duration is measured separately.','',
        '| Policy | Preference | Overlay | CRT bytes | Mean render cycles | Worst render cycles | Over budget / samples | Interval FPS high / avg / low | Measured seconds* |',
        '| --- | --- | --- | ---: | ---: | ---: | --- | --- | ---: |']
    for r in rows:
        m=r['metrics']
        scene_seconds=r['ending']['scene_seconds'] if r['ending'] else m['mean_profile_seconds']
        lines.append(f"| {r['policy']} | {r['preference']} | {r['overlay']} | {r['cartridge_bytes']} | {m['mean_render_cycles']:.1f} | {m['worst_render_cycles']} | {m['render_over_budget']}/{m['measured_samples']} | {m['profile_interval_fps_high']:.3f} / {m['profile_interval_fps_avg']:.3f} / {m['profile_interval_fps_low']:.3f} | {scene_seconds:.3f} |")
    lines += ['',f"Completed {len(rows)}/{expected}. Missing jobs are not treated as passing.",'']
    (logs/'RESULTS.md').write_text('\n'.join(lines))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('run','summary','bundle','worker'))
    p.add_argument('--id',default='marbles-policy-01')
    p.add_argument('--policies',nargs='+',choices=candidates.POLICIES,default=list(candidates.POLICIES))
    p.add_argument('--preferences',nargs='+',choices=('fps','ram'),default=['fps','ram'])
    p.add_argument('--overlays',nargs='+',choices=('clean','hud'),default=['clean','hud'])
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--check-ending',action='store_true',help='also verify the full ending; excluded from render costs')
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--vice-data',type=Path)
    for k,default in [('tass','64tass'),('cartconv','cartconv'),('vice','x64sc')]:p.add_argument('--'+k,default=default)
    p.add_argument('--workspace',type=Path,help=argparse.SUPPRESS)
    p.add_argument('--output',type=Path,help=argparse.SUPPRESS)
    p.add_argument('--policy',choices=candidates.POLICIES,help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.action=='worker':worker(a);return
    if not a.id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a.id):p.error('invalid ID')
    logs=ROOT/'logs'/a.id;build=ROOT/'comparison-tests'/'marbles-candidates'/a.id
    if a.action in ('summary','bundle'):
        s=summary(logs)
        if a.action=='summary':print(logs/'RESULTS.md');return
        target=logs.parent/(a.id+'-results.zip')
        if target.exists():p.error('bundle already exists; preserve/rename it first')
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
            for f in logs.rglob('*'):
                if f.is_file():z.write(f,f.relative_to(logs))
        target.with_suffix('.zip.sha256').write_text(pipeline.digest(target)+'  '+target.name+'\n')
        print(target);return
    if not 1<=a.repeats<=20 or not 1<=a.workers<=4:p.error('repeats 1..20; workers 1..4')
    if not a.vice_data or not a.vice_data.is_dir():p.error('--vice-data directory required')
    if logs.exists() or build.exists():p.error('run ID exists; choose a new ID')
    for k in ('tass','cartconv','vice'):
        v=shutil.which(getattr(a,k))
        if not v:p.error('missing executable: '+getattr(a,k))
        setattr(a,k,str(Path(v).resolve()))
    a.vice_data=a.vice_data.resolve()
    logs.mkdir(parents=True);build.mkdir(parents=True);(logs/'results').mkdir()
    config=dict(policies=a.policies,preferences=a.preferences,overlays=a.overlays,repeats=a.repeats,
                source=pipeline.comparison.fingerprints(ROOT)[1],runner_sha256=pipeline.digest(__file__),
                tools={k:pipeline.digest(getattr(a,k)) for k in ('tass','cartconv','vice')},pal=True,seed=1,check_ending=a.check_ending)
    pipeline.save(logs/'run.json',config)
    # Force the same PAL/default settings even for the existing ending verifier.
    wrapper=build/'vice-pal'
    wrapper.write_text('#!'+sys.executable+'\nimport os,sys\nos.execv('+repr(a.vice)+', ['+repr(a.vice)+', "-console", "-default", "-pal"]+sys.argv[1:])\n')
    wrapper.chmod(0o755)
    def task(policy):
        work=build/policy;work.mkdir();src=work/'source'
        shutil.copytree(ROOT,src,ignore=shutil.ignore_patterns('.git','build','logs','comparison-tests','__pycache__'))
        encoder=src/'tools/c643d/bytespan.py';encoder.write_text(candidates.patch_encoder(encoder.read_text(),policy))
        command=[sys.executable,str(Path(__file__).resolve()),'worker','--workspace',str(work),
                 '--output',str(logs/'results'),'--policy',policy,'--preferences',*a.preferences,
                 '--overlays',*a.overlays,'--repeats',str(a.repeats),'--tass',a.tass,'--cartconv',a.cartconv,
                 '--vice',str(wrapper),'--vice-data',str(a.vice_data)]
        if a.check_ending:command.append('--check-ending')
        print(policy,'Marbles running; fps locking: original scene pacing',flush=True)
        with (logs/(policy+'.log')).open('w') as f:
            code=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT).returncode
        pipeline.save(logs/(policy+'-status.json'),dict(policy=policy,exit_code=code,status='passed' if code==0 else 'failed'))
        print(policy,'PASS' if code==0 else 'FAILED; see log',flush=True)
        return code
    with ThreadPoolExecutor(max_workers=a.workers) as pool:codes=list(pool.map(task,a.policies))
    s=summary(logs);print(logs/'RESULTS.md')
    if any(codes) or not s['complete']:raise SystemExit('Incomplete run; bundle logs for diagnosis')

if __name__=='__main__':main()
