#!/usr/bin/env python3
"""Recover dense Marbles tests from saved compiled samples. Never invokes Blender."""
import argparse,hashlib,json,math,os,shutil,subprocess,sys,zipfile
from pathlib import Path
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1]

def indices(count,source_fps,target_fps):
    if not 1<=target_fps<=source_fps:raise ValueError('target must not exceed saved source sampling rate')
    return [min(count-1,math.floor(i*source_fps/target_fps+0.5)) for i in range(math.ceil(count*target_fps/source_fps))]

def timing_check(report, fps, duration=40):
    # Conservative admission: every render must fit even the shorter PAL hold.
    # Also reject aggregate slowdown; average FPS alone can hide heavy sections.
    budget=(50//fps)*19656
    over=sum(row['render_cycles']>budget for row in report['samples'])
    seconds=report['measured_seconds']
    return dict(passed=over==0 and abs(seconds-duration)<=0.25,
                measured_seconds=seconds, target_seconds=duration,
                tolerance_seconds=0.25, shortest_hold_budget_cycles=budget,
                renders_over_shortest_hold=over)

def worker(config):
    sys.path.insert(0,str(ROOT/'tools'))
    from c643d.sceneio import load_scene
    from c643d.pipeline import FrameBuild
    from c643d import cartscene,bytespan_v10,bytespan
    from verify_cart_stream import verify
    from profile_cart_stream import profile
    from unittest.mock import patch
    from scene_packing import pack_scene_frames, CapacityError
    a=json.loads(Path(config).read_text());out=Path(a['out']);work=Path(a['work'])
    scene=load_scene(a['export']);raw=json.loads(Path(a['oracle']).read_text())
    if len(raw)!=len(scene.frames) or len(raw)!=1000 or scene.source_fps!=25:raise ValueError('expected complete 1000-sample, 25 FPS Marbles checkpoint')
    frames=[FrameBuild(**f) for f in raw]
    force=bytespan_v10.frame_block
    def encoder(policy):
        if policy=='baseline':return bytespan.frame_block
        if policy=='force-bytes':return force
        n={'bytes125':125,'bytes150':150}[policy]
        def encode(frame,colors=True):
            direct,meta=force(frame,colors)
            from c643d.cartstream import frame_block
            vector,vmeta=frame_block(frame,colors)
            return (direct,meta) if len(direct)*100<=len(vector)*n else (vector,vmeta)
        return encode
    results=[]
    for fps in a['fps']:
        selected=indices(len(frames),25,fps)
        sampled=replace(scene,frames=tuple(scene.frames[i] for i in selected))
        for policy in ('force-bytes','bytes150','bytes125','baseline'):
            stem=f'marbles-hors-render-v1-{fps}fps-{policy}'
            record={'target_fps':fps,'policy':policy,'samples':len(selected),'source_duration_seconds':40,'status':'running'};results.append(record)
            print(f'{fps} FPS / {policy}: {len(selected)} integer-source samples; original 40-second timeline',flush=True)
            try:
                with patch.object(bytespan_v10,'frame_block',encoder(policy)), patch.object(cartscene,'pack_scene_frames',pack_scene_frames):
                    crt,manifest=cartscene.assemble_scene(ROOT,[frames[i] for i in selected],sampled,tass=a['tass'],cartconv=a['cartconv'],outdir=work/'carts',stem=stem,hud_text='DONT LOSE YOUR MARBLES',frame_ticks=50//fps,intro=True,ending=True,text_overlay=False,renderer='yunroll-cart-v10-scene',prefer='fps',output_fps=fps)
                record.update(crt_bytes=crt.stat().st_size,sha256=hashlib.sha256(crt.read_bytes()).hexdigest())
                record['pixels']=verify(crt,a['vice'],a['vice_data'])
                record['profile']=profile(crt,a['vice'],a['vice_data'])
                record['timing']=timing_check(record['profile'],fps)
                if not record['timing']['passed']:
                    record.update(status='rejected_timing',failure_kind='timing')
                    print(f'{stem}: REJECTED TIMING; {record["timing"]["measured_seconds"]:.2f}s versus 40s; {record["timing"]["renders_over_shortest_hold"]} renders exceed shortest hold',flush=True)
                else:
                    record['status']='passed'
                    selected_dir=work/'selected';selected_dir.mkdir(exist_ok=True)
                    for suffix in ('.crt','.lbl','-manifest.json'):
                        f=crt.with_name(crt.stem+suffix)
                        shutil.copy2(f,selected_dir/f.name)
                print(f'{stem}: {record["status"]}; {record["crt_bytes"]} bytes; profiler interval {record["profile"]["frames_per_second"]:.2f} FPS',flush=True)
            except Exception as e:
                record.update(status='failed',error=str(e),failure_kind='capacity' if isinstance(e,CapacityError) else 'build_or_verification');print(f'{stem}: FAILED: {e}',flush=True)
            (out/'results.json').write_text(json.dumps({'scope':'Capacity, pixel and conservative real-time timing checks; only timing-passing carts are included in the bundle. Original integer source samples reused; 20 FPS is nearest-sample resampling, not subframe interpolation. No Blender invocation, no music test. Fractional scalar budget counts use shorter interval.','results':results},indent=2)+'\n')

        if a.get('auto_fit'):
            current=[r for r in results if r['target_fps']==fps]
            if any(r['status']=='passed' for r in current):
                print(f'AUTO-FIT: selected {fps} FPS; verified candidates listed in results.json',flush=True)
                break
            if any(r.get('failure_kind') not in ('capacity','timing') for r in current):
                print('AUTO-FIT STOP: build or verification error; lowering FPS is not a remedy',flush=True)
                break
            print(f'AUTO-FIT: {fps} FPS fails capacity or real-time timing; trying next lower rate if above minimum',flush=True)
    passed=sum(r['status']=='passed' for r in results)
    print(f'RESULT: {passed}/{len(results)} candidates passed capacity, pixels and real-time timing',flush=True)
    return 0 if passed else 1

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id',default='marbles-realtime-01');p.add_argument('--from-run',default='marbles-blender-01')
    p.add_argument('--fps',type=int,nargs='+',default=[25,20,19,18,17,16,15]);p.add_argument('--vice-data')
    p.add_argument('--attempt-cart-auto-fit-fps',action='store_true',help='descend from highest --fps by one until capacity, pixel and real-time timing checks pass or minimum')
    p.add_argument('--min-fps',type=int,default=1)
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv');p.add_argument('--vice',default='x64sc')
    p.add_argument('--worker',help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.worker:return worker(a.worker)
    for name in (a.id,a.from_run):
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):p.error('invalid run ID')
    if not a.vice_data:p.error('--vice-data required')
    if any(not 1 <= f <= 25 for f in a.fps):p.error('target FPS must be between 1 and saved source rate 25')
    if not 1 <= a.min_fps <= max(a.fps):p.error('--min-fps must be between 1 and highest target FPS')
    rates=list(range(max(a.fps),a.min_fps-1,-1)) if a.attempt_cart_auto_fit_fps else list(dict.fromkeys(a.fps))
    prior=ROOT/'comparison-tests/blender-targets'/a.from_run/'source/build'
    export=prior/'marbles-v10-blender-25fps.c643dscene';oracle=prior/'marbles-v10-blender-25fps-stream-scene/oracle.json'
    for f in (export,oracle):
        if not f.is_file():p.error(f'missing saved checkpoint: {f}')
    binaries={}
    for key in ('tass','cartconv','vice'):
        binaries[key]=shutil.which(getattr(a,key))
        if not binaries[key]:p.error(f'{key} not found')
    work=ROOT/'comparison-tests/marbles-recovery'/a.id
    out=ROOT/'logs'/a.id
    if work.exists() or out.exists():p.error('use a new run ID')
    work.mkdir(parents=True);out.mkdir(parents=True)
    source=work/'source'
    shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('.git','build','logs','comparison-tests','__pycache__','monitor.log'))
    wrapper=work/'vice-default.py';wrapper.write_text('#!'+sys.executable+'\nimport os,sys\nos.execv('+repr(binaries['vice'])+',['+repr(binaries['vice'])+",'-console','-default','-pal',*sys.argv[1:]])\n");wrapper.chmod(0o755)
    config={**binaries,'vice':str(wrapper),'vice_data':str(Path(a.vice_data).expanduser().resolve()),'export':str(export),'oracle':str(oracle),'fps':rates,'auto_fit':a.attempt_cart_auto_fit_fps,'out':str(out),'work':str(work),'checkpoint_sha256':hashlib.sha256(oracle.read_bytes()).hexdigest()}
    cfg=out/'run.json';cfg.write_text(json.dumps(config,indent=2)+'\n')
    try:
        with (out/'run.log').open('w') as log:
            proc=subprocess.Popen([sys.executable,str(source/'perf/recover_marbles.py'),'--worker',str(cfg)],cwd=source,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            for line in proc.stdout:
                log.write(line);log.flush();print(line,end='',flush=True)
            code=proc.wait()
        print('Worker exit:',code,flush=True)
    finally:
        bundle=ROOT/'logs'/(a.id+'-results.zip')
        with zipfile.ZipFile(bundle,'x',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(out.rglob('*')):
                if f.is_file():z.write(f,f.relative_to(out.parent))
            for f in sorted((work/'selected').glob('*')):
                if f.is_file():z.write(f,'selected-carts/'+f.name)
        bundle.with_suffix('.zip.sha256').write_text(hashlib.sha256(bundle.read_bytes()).hexdigest()+'  '+bundle.name+'\n')
        print('SEND BACK:',bundle)
    return code
if __name__=='__main__':sys.exit(main())
