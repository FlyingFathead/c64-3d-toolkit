#!/usr/bin/env python3
"""Opt-in measured multi-pass search for looping .c643dscene EasyFlash builds."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import argparse, csv, hashlib, itertools, json, math, os, shutil, statistics, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=Path(__file__).resolve()

def dump(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def worker(config_path):
    from c643d.sceneio import load_scene
    from c643d.pipeline import FrameBuild
    from c643d.cartscene import assemble_scene
    from c643d.hors_v2 import assemble_scene as assemble_v2
    from c643d.autotune_metrics import measure_display, CLOCK, PAL_TICKS
    from verify_cart_stream import verify,labels
    from profile_cart_stream import profile
    cfg=json.loads(Path(config_path).read_text());case=Path(cfg['directory']);stage=case/'stage';artifacts=case/'artifacts'
    artifacts.mkdir();shutil.copytree(ROOT/'c64',stage/'c64')
    scene=load_scene(cfg['scene']);frames=[FrameBuild(**f) for f in json.loads(Path(cfg['frames']).read_text())]
    beta=cfg['renderer'] in ('hors-render-v2-beta1','hors-render-v2')
    if cfg['renderer']=='hors-render-v2':
        from c643d.hors_v2_stable import assemble_scene as assemble_v2
    options=dict(tass=cfg['tass'],cartconv=cfg['cartconv'],outdir=artifacts,stem='candidate',hud_text='AUTOTUNE',
        frame_ticks=cfg['ticks'],colors=not cfg['mono'],color_index=cfg['color_index'],intro=False,ending=False,text_overlay=False,
        renderer=cfg['renderer'],prefer=cfg['preference'],optimize=cfg['plan']=='optimized')
    if beta:options.update(draw_gap=cfg['gap'],batch_budget=cfg['batch'])
    crt,manifest=(assemble_v2 if beta else assemble_scene)(stage,frames,scene,**options)
    build=stage/'build/candidate-stream-scene';oracle=build/'oracle.json'
    proof=verify(crt,cfg['vice'],cfg['vice_data'],cycles=2,oracle_path=oracle);dump(case/'verification.json',proof)
    timing=None
    if not manifest.get('optimization',{}).get('duplicate_pictures'):
        timing=profile(crt,cfg['vice'],cfg['vice_data']);dump(case/'producer-profile.json',timing)
    else:
        dump(case/'producer-profile.json',{'unavailable':'Existing stage profiler does not account for skipped duplicate-picture stages; display measurement and full oracle verification still run.'})
    producer_fps=timing['frames_per_second'] if timing else proof['average_fps']
    refreshes=max(round(cfg['seconds']*CLOCK/PAL_TICKS),math.ceil(2*len(frames)*CLOCK/(max(producer_fps,.001)*PAL_TICKS)))
    if refreshes>cfg['max_refreshes']:raise ValueError('Full-loop display window exceeds --max-refreshes; increase it explicitly')
    display=measure_display(crt,oracle,cfg['vice'],cfg['vice_data'],refreshes);dump(case/'display.json',display)
    if not display['picture_coverage_complete']:raise AssertionError('Display window did not cover every visible picture; increase --seconds')
    symbols=labels(crt.with_suffix('.lbl'))
    row={k:cfg[k] for k in ['candidate','renderer','preference','ticks','plan','gap','batch']}
    row.update(status='passed',**{k:display[k] for k in ['sha256','display_fps','display_interval_worst_ms','display_interval_p95_ms','display_changes','elapsed_cycles','fixed_cadence','picture_coverage_complete']},
        requested_hold_histogram=display['observed_hold_ticks'],
        prep_mean_ms=timing['mean_render_cycles']/985.248 if timing else None,
        prep_worst_ms=timing['worst_render_cycles']/985.248 if timing else None,
        ROM_payload_bytes=manifest['rom_frame_bytes'],ROM_data_capacity_bytes=manifest['data_bank_capacity_bytes'],
        ROM_bank_slots=len({(r['chip'],r['bank']) for r in manifest['frame_data']}),
        runtime_PRG_bytes=(build/'runtime.prg').stat().st_size,
        bitmap_reserved_bytes=3*8000,screen_reserved_bytes=3*1000,metadata_reserved_bytes=3*1024,
        directory_reserved_bytes=1792,staging_reserved_bytes=8192,
        beta_extra_reserved_RAM_bytes=0,beta_reclaimed_dispatch_bytes=256 if beta else 0,
        beta_helper_code_and_state_bytes=symbols.get('hors_v2_extension_end',0)-symbols.get('hors_v2_extension_start',0),
        verified_producer_frames=proof['verified_frames'],verified_display_observations=display['refresh_observations'],
        palette_and_bitmap_pass=True,
        memory_note='Allocation components, not a disjoint total. PRG size includes gaps. Beta reuses a vector-only page after requiring all frames to be direct spans.')
    dump(case/'result.json',row)


def resolve_tool(value):
    result=shutil.which(value)
    if result:return str(Path(result).resolve())
    path=Path(value).expanduser().resolve()
    if path.is_file():return str(path)
    raise ValueError('Cannot find executable '+value)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scene',nargs='?',type=Path)
    ap.add_argument('--out',type=Path)
    ap.add_argument('--renderers',nargs='+',choices=['hors-render-v2','hors-render-v1-scene','hors-render-v2-beta1','yunroll-cart-v9-scene'],default=['hors-render-v1-scene','hors-render-v2'])
    ap.add_argument('--preferences',nargs='+',choices=['fps','ram'],default=['fps'])
    ap.add_argument('--ticks',nargs='+',type=int,default=[1,2,3,4])
    ap.add_argument('--plans',nargs='+',choices=['optimized','raw'],default=['optimized','raw'])
    ap.add_argument('--gaps',nargs='+',type=int,default=[6])
    ap.add_argument('--batches',nargs='+',type=int,default=[2048])
    ap.add_argument('--objective',choices=['fps','steady'],default='fps')
    ap.add_argument('--seconds',type=float,default=10,help='Minimum display measurement window; expanded to at least two source loops')
    ap.add_argument('--max-refreshes',type=int,default=10000)
    ap.add_argument('--jobs',type=int,default=2)
    ap.add_argument('--mono',action='store_true')
    ap.add_argument('--color-index',type=int,default=1)
    ap.add_argument('--width',type=int,choices=[256,320],default=256,help='Projection viewport width; preserve the source export framing')
    ap.add_argument('--visibility',choices=['surface','surface_features','surface_creases','frontface'],default='surface')
    ap.add_argument('--tass',default='64tass');ap.add_argument('--cartconv',default='cartconv');ap.add_argument('--vice',default='x64sc');ap.add_argument('--vice-data')
    ap.add_argument('--worker',type=Path,help=argparse.SUPPRESS)
    args=ap.parse_args()
    if args.worker:worker(args.worker);return
    if args.scene is None or args.out is None:ap.error('scene and --out are required')
    if args.jobs<1 or args.seconds<=0 or args.max_refreshes<2 or not 0<=args.color_index<=15 or any(not 1<=n<=255 for n in args.ticks) or any(n<1 for n in args.gaps+args.batches):ap.error('Invalid search limits')
    args.out=args.out.expanduser().resolve();args.scene=args.scene.expanduser().resolve()
    if args.out.exists():ap.error('--out must name a new directory')
    from c643d.sceneio import load_scene
    from c643d.pipeline import build_scene_frames
    from c643d.autotune_metrics import select
    from c643d import __version__
    tass=resolve_tool(args.tass);cartconv=resolve_tool(args.cartconv);vice=resolve_tool(args.vice)
    data=str(Path(args.vice_data).expanduser().resolve()) if args.vice_data else None
    scene=load_scene(args.scene)
    print(f'Analysis pass: {len(scene.frames)} authored frames, {len(scene.mesh.vertices)} vertices',flush=True)
    frames,_=build_scene_frames(scene,visibility_mode=args.visibility,z_tolerance=.0008,feature_angle=40,
        enable_source_colors=not args.mono,fallback_color=args.color_index,width=args.width,height=192,max_frames=2048,max_visible_runs=65535)
    # Full-width sources can emit clears wider than the existing 32-cell kernel.
    for frame in frames:
        spans=[]
        for lo,hi,count in frame.clear_spans:
            offset=lo+(hi<<8)
            while count:
                n=min(32,count);spans.append((offset&255,offset>>8,n));offset+=8*n;count-=n
        frame.clear_spans=spans
    args.out.mkdir(parents=True);frame_file=args.out/'compiled-frames.json';dump(frame_file,[asdict(f) for f in frames])
    dump(args.out/'analysis.json',{'scene_sha256':hashlib.sha256(args.scene.read_bytes()).hexdigest(),'toolkit_version':__version__,
        'source_frames':len(frames),'vertices':len(scene.mesh.vertices),'source_fps':scene.source_fps,'sample_step':scene.sample_step,
        'per_frame':[{'frame':i,'drawing_records':len(f.records),'clear_spans':len(f.clear_spans),'colour_spans':len(f.color_spans),'unique_pixels':f.unique_pixels} for i,f in enumerate(frames)],
        'timing_policy':'All candidates use the same authored samples. Different holds may change animation speed; no implicit resampling.',
        'test_environment':{'PAL':True,'seed':1,'sound':False,'tass':tass,'cartconv':cartconv,'vice':vice,'vice_data':data},
        'search_configuration':{k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items() if k!='worker'}})
    cases=[]
    for renderer,preference,ticks,plan in itertools.product(dict.fromkeys(args.renderers),dict.fromkeys(args.preferences),dict.fromkeys(args.ticks),dict.fromkeys(args.plans)):
        extra=list(itertools.product(dict.fromkeys(args.gaps),dict.fromkeys(args.batches))) if renderer in ('hors-render-v2-beta1','hors-render-v2') else [(None,None)]
        for gap,batch in extra:
            name=f'{renderer}-{preference}-{plan}-t{ticks}'+(f'-g{gap}-b{batch}' if gap is not None else '')
            case=args.out/name;case.mkdir()
            cfg=dict(candidate=name,directory=str(case),scene=str(args.scene),frames=str(frame_file),renderer=renderer,preference=preference,ticks=ticks,plan=plan,gap=gap,batch=batch,
                mono=args.mono,color_index=args.color_index,tass=tass,cartconv=cartconv,vice=vice,vice_data=data,seconds=args.seconds,max_refreshes=args.max_refreshes)
            dump(case/'configuration.json',cfg);cases.append(cfg)
    print(f'Build/verify/measure passes: {len(cases)} candidates; {args.jobs} independent workers',flush=True)
    def run(cfg):
        case=Path(cfg['directory'])
        try:
            with (case/'run.log').open('w') as log:
                proc=subprocess.run([sys.executable,str(SCRIPT),'--worker',str(case/'configuration.json')],stdout=log,stderr=log,timeout=720)
            if proc.returncode:raise RuntimeError(f'Worker exited {proc.returncode}')
            return json.loads((case/'result.json').read_text())
        except (RuntimeError,subprocess.SubprocessError) as exc:
            row={k:cfg[k] for k in ['candidate','renderer','preference','ticks','plan','gap','batch']};row.update(status='failed',reason=str(exc),log_tail=(case/'run.log').read_text()[-2400:]);dump(case/'result.json',row);return row
    rows=[]
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        tasks=[executor.submit(run,cfg) for cfg in cases]
        for future in as_completed(tasks):
            row=future.result();rows.append(row);print(row['candidate']+': '+row['status']+(f"; {row['display_fps']:.3f} display FPS" if row['status']=='passed' else ''),flush=True);dump(args.out/'results.json',rows)
    selection=select(rows,args.objective);dump(args.out/'selection.json',selection)
    header='| Candidate | Display FPS | Worst display ms | Active stages ms | ROM B | Runtime PRG B | Fixed cadence | Verified |\n| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |'
    lines=[header]
    def number(value):return '-' if value is None else f'{value:.3f}'
    for row in sorted(rows,key=lambda r:(r['status']!='passed',-r.get('display_fps',0))):
        if row['status']=='passed':lines.append(f"| {row['candidate']} | {number(row['display_fps'])} | {number(row['display_interval_worst_ms'])} | {number(row['prep_mean_ms'])} | {row['ROM_payload_bytes']} | {row['runtime_PRG_bytes']} | {row['fixed_cadence']} | yes |")
        else:lines.append(f"| {row['candidate']} | - | - | - | - | - | - | FAILED; see log |")
    text='\n'.join(lines);print('\n'+text+'\n\nSelection: '+str(selection.get('winner')),flush=True)
    (args.out/'comparison.md').write_text('# Measured scene optimization search\n\n'+text+'\n\nSelection: '+str(selection.get('winner'))+'\n\nActual display changes per emulated PAL time. PRG length is not total used RAM; allocation categories are in results.json. Preparation can be unavailable when the legacy stage profiler cannot follow duplicate-picture shortcuts. Timing ties are recorded in selection.json. Different minimum holds can change authored animation speed. All selected candidates must pass completed-frame and displayed-picture checks; no build is automatically promoted.\n')
    fields=sorted({k for row in rows for k in row})
    with (args.out/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    if not selection.get('winner'):raise SystemExit('No candidate met the requested constraints; inspect results and logs')

if __name__=='__main__':main()
