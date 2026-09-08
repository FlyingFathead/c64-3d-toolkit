#!/usr/bin/env python3
"""Isolated V9 byte-span policy experiments; production renderers stay unchanged."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import pipeline

ROOT=pipeline.ROOT
POLICIES=('baseline','bytes125','bytes150','force-bytes')
ORIGINAL='return (bytes(data), meta) if len(data) < len(original) else (original, meta)'


def patch_encoder(source, policy):
    if source.count(ORIGINAL)!=1:raise ValueError('Unexpected encoder; review adapter')
    if policy=='baseline':return source
    choices={'bytes125':'len(data)*4 <= len(original)*5',
             'bytes150':'len(data)*2 <= len(original)*3',
             'force-bytes':'True'}
    if policy not in choices:raise ValueError('Unknown policy')
    return source.replace(ORIGINAL,
        'selected = bytes(data) if '+choices[policy]+' else original\n'
        '    if len(selected) > 8192:\n'
        '        raise ValueError("candidate picture exceeds 8192-byte bank window")\n'
        '    return selected, meta')


def profile_work(work, out, vice, data):
    sys.path.insert(0,str(work/'source/tools'))
    from profile_cart_stream import profile
    from c643d.cartpaths import menu_manifest_path
    out.mkdir(parents=True,exist_ok=True)
    for crt in sorted((work/'carts').glob('*.crt')):
        manifest=json.loads(menu_manifest_path(crt).read_text())
        for i,e in enumerate(manifest['streamed_entries']):
            dest=out/f'{crt.stem}-{i:02d}.json'
            if dest.exists():continue
            r=profile(crt,vice,data,menu_entry=i)
            r.update(animation=e['name'],diagnostic_only=True,
                     frame_encodings=[f.get('encoding','vectors') for f in e['frame_data']],
                     frame_bytes=[f['bytes'] for f in e['frame_data']])
            pipeline.save(dest,r)
            print(crt.stem,e['name'],'stage profile saved',flush=True)


def summarize(logs):
    rows=[];status=[];states=[]
    for file in sorted(logs.glob('*/candidate.json')):
        state=json.loads(file.read_text());states.append(state);status.append(dict(policy=state['policy'],status=state['status']))
        if state['status']!='completed':continue
        work=Path(state['work']);policy=state['policy']
        for p in sorted((work/'results').glob('*-play-all.json')):
            sizes=json.loads(p.with_name(p.name.replace('-play-all.json','-sizes.json')).read_text())
            result=json.loads(p.read_text())
            for row in pipeline.measurement_records(result,sizes,p.name):
                row.update(policy=policy,report=policy+'/'+p.name)
                rows.append(row)
    recommendations={}
    for pref in ('fps','ram'):
        group=[r for r in rows if r['preference']==pref]
        if group:recommendations[pref]=pipeline.recommend(group,dict(status='completed',options={}))
    report=dict(candidate_status=status,records=rows,recommendations=recommendations,
                complete=bool(states) and all(s['status'] in ('completed','infeasible') for s in states),
                note='Per-animation choices among verified completed candidates only. Not a mixed production renderer. '
                     'Profiles are diagnostics; only normal PLAY ALL supplies comparative FPS.')
    pipeline.save(logs/'summary.json',report)
    lines=['# V9 byte-span candidate experiment','','All measurements are normal PLAY ALL. Incomplete candidates are excluded.','',
           '| Policy | Status |','| --- | --- |']
    lines += [f"| {s['policy']} | {s['status']} |" for s in status]
    for pref in ('fps','ram'):
        lines+=['',f'## {pref.upper()} preference','',
                '| Animation | Policy | Average FPS | Low FPS | CRT bytes | Delta vs baseline |',
                '| --- | --- | ---: | ---: | ---: | ---: |']
        group=[r for r in rows if r['preference']==pref]
        base={r['animation']:r for r in group if r['policy']=='baseline'}
        for r in sorted(group,key=lambda r:(r['animation'],r['policy'])):
            b=base.get(r['animation']);delta=f"{100*(r['average_fps']/b['average_fps']-1):+.2f}%" if b else 'N/A'
            name=r['animation'].replace('|','/').replace('\n',' ')
            lines.append(f"| {name} | {r['policy']} | {r['average_fps']:.3f} | {r['low_fps']:.3f} | {r['cartridge_bytes']} | {delta} |")
    (logs/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    return report


def bundle(logs):
    summarize(logs)
    target=logs.parent/(logs.name+'-results.zip')
    if target.exists():raise SystemExit('Bundle exists; preserve it and choose a new output name manually')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in logs.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(logs))
        for s in logs.glob('*/candidate.json'):
            state=json.loads(s.read_text());work=Path(state['work']);prefix='raw/'+state['policy']+'/'
            for p in work.glob('results/*.json'):z.write(p,prefix+'results/'+p.name)
            for p in work.glob('*.log'):z.write(p,prefix+p.name)
            if (work/'provenance.json').exists():z.write(work/'provenance.json',prefix+'provenance.json')
    target.with_suffix('.zip.sha256').write_text(pipeline.digest(target)+'  '+target.name+'\n')
    print(target)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('run','resume','summary','bundle','profile-worker'))
    p.add_argument('--id',default='byte-policy-01')
    p.add_argument('--policies',nargs='+',choices=POLICIES,default=list(POLICIES))
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--loops',type=int,default=3)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv')
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',type=Path)
    p.add_argument('--reference-json',type=Path)
    p.add_argument('--workspace',type=Path,help=argparse.SUPPRESS)
    p.add_argument('--profile-output',type=Path,help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.action=='profile-worker':profile_work(a.workspace,a.profile_output,a.vice,a.vice_data);return
    if not a.id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a.id):p.error('invalid run ID')
    logs=ROOT/'logs'/a.id;build=ROOT/'comparison-tests'/'byte-candidates'/a.id
    if a.action in ('summary','bundle'):
        if not (logs/'experiment.json').exists():p.error('unknown experiment ID')
        if a.action=='bundle':bundle(logs)
        else:print(json.dumps(summarize(logs)['candidate_status'],indent=2));print(logs/'RESULTS.md')
        return
    if not 1<=a.loops<=20 or a.workers<1:p.error('loops 1..20; workers >=1')
    if a.vice_data is None:p.error('--vice-data required')
    for key in ('tass','cartconv','vice'):
        resolved=shutil.which(getattr(a,key))
        if not resolved:p.error('executable missing: '+getattr(a,key))
        setattr(a,key,resolved)
    a.vice_data=a.vice_data.resolve()
    if a.reference_json:a.reference_json=a.reference_json.resolve()
    signature=dict(source=pipeline.comparison.fingerprints(ROOT)[1],runner=pipeline.digest(__file__),
        analysis=pipeline.digest(ROOT/'perf/pipeline.py'),policies=a.policies,loops=a.loops,
        tools={k:pipeline.digest(getattr(a,k)) for k in ('tass','cartconv','vice')},
        vice_data=str(a.vice_data),reference=pipeline.digest(a.reference_json) if a.reference_json else None)
    if a.action=='resume':
        if json.loads((logs/'experiment.json').read_text())!=signature:p.error('experiment inputs/options changed; use a new ID')
    else:
        if logs.exists() or build.exists():p.error('ID exists; resume with same options or choose new ID')
        logs.mkdir(parents=True);build.mkdir(parents=True);pipeline.save(logs/'experiment.json',signature)
    def run(policy):
        root=build/policy;src=root/'input';work=root/'work';out=logs/policy;out.mkdir(exist_ok=True)
        statefile=out/'candidate.json'
        if statefile.exists() and json.loads(statefile.read_text())['status'] in ('completed','infeasible'):return
        if not src.exists():
            shutil.copytree(ROOT,src,ignore=shutil.ignore_patterns('.git','build','comparison-tests','logs','__pycache__'))
            encoder=src/'tools/c643d/bytespan.py';encoder.write_text(patch_encoder(encoder.read_text(),policy))
        state=dict(policy=policy,status='running',work=str(work),encoder_sha256=pipeline.digest(src/'tools/c643d/bytespan.py'))
        pipeline.save(statefile,state)
        cmd=[sys.executable,str(src/'tools/compare_renderers.py'),'--workspace',str(work),'--methods','yunroll-cart-v9','--workers','1','--loops',str(a.loops),
             '--tass',a.tass,'--cartconv',a.cartconv,'--vice',a.vice,'--vice-data',str(a.vice_data)]
        if a.reference_json:cmd+=['--reference-json',str(a.reference_json)]
        if (work/'provenance.json').exists():cmd+=['--resume']
        print(policy,'building / measuring',flush=True)
        with (out/'run.log').open('a') as log:code=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
        if code:
            detail='\n'.join(p.read_text(errors='replace') for p in work.glob('*.log'))
            state['status']='infeasible' if any(s in detail for s in ('exceed EasyFlash capacity','exceeds 8192-byte bank window')) else 'failed'
            state['exit_code']=code;pipeline.save(statefile,state);print(policy,state['status'],flush=True);return
        print(policy,'pixel checks and PLAY ALL passed; profiling stages',flush=True)
        cmd=[sys.executable,str(Path(__file__).resolve()),'profile-worker','--workspace',str(work),'--profile-output',str(out/'stages'),'--vice',a.vice,'--vice-data',str(a.vice_data)]
        with (out/'stages.log').open('a') as log:code=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
        state['status']='completed' if code==0 else 'profile-failed';pipeline.save(statefile,state);print(policy,state['status'],flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as pool:list(pool.map(run,a.policies))
    report=summarize(logs);print(logs/'RESULTS.md')
    if not report['complete']:raise SystemExit('Some candidates failed; inspect logs and resume with identical options')
    print('Ready to bundle. Per-demo leaders do not yet define a combined renderer.')

if __name__=='__main__':main()
