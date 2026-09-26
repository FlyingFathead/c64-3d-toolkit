#!/usr/bin/env python3
"""Compare the original renderer families and native scene variants outside the checkout.

Every complete input is frozen once. Capacity failures are N/A with a reason;
other build failures and pixel mismatches are FAIL, never omitted or simplified.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
CORE_METHODS = ['step', 'bytechunk', 'yunroll'] + [f'yunroll-cart-v{i}' for i in range(2,11)] + [
    'hors-render-v2-beta1', 'hors-render-v2', 'hors-renderer-v3', 'hors-v4-ef', 'hors-v5-c1', 'hors-v5-c2']
SCENE_METHODS = [f'yunroll-cart-v{i}-scene' for i in range(4,11)] + [
    'hors-render-v2-beta1-scene', 'hors-v2-scene', 'hors-v3', 'hors-v4-ef', 'hors-v4-gmod3', 'hors-v5-c1', 'hors-v5-c2']
CAPACITY_MESSAGES = ('resident record count exceeds 255', 'frame pointer tables reach',
    'line tables reach', 'line tables need', 'clear tables reach', 'clear/colour tables reach',
    'staging buffer', 'per-slot cache', 'frame arena', 'capacity exceeded',
    'exceed EasyFlash capacity', 'stream pool exhausted', 'frame-data chips',
    '8 KiB bank', '8-bit (maximum 255 each)', 'metadata span count exceeds one byte',
    'metadata exceeds its 1 KiB cache', 'exceeds its 1 KiB cache per frame',
    'C2 runs colour span count exceeds 255')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2)+'\n')


def picture_hash(frames, screen):
    from verify_cart_stream import expected_frame
    digest = hashlib.sha256()
    for frame in frames:
        for data in expected_frame(asdict(frame) if not isinstance(frame, dict) else frame, screen):
            digest.update(data)
    return digest.hexdigest()


def capacity_reason(text):
    return next((line.strip() for line in text.splitlines()
                 if any(message in line for message in CAPACITY_MESSAGES)), None)


def selector_coverage():
    """Account for every accepted spelling without counting aliases as wins."""
    from c643d.cli import make_parser
    from c643d.renderer_names import canonical_selector
    from c643d.toolchain import load_toolchain_settings
    parser=make_parser(load_toolchain_settings(ROOT/'config/c643d.ini'))
    build=next(a for a in parser._actions if isinstance(a,argparse._SubParsersAction)).choices['build']
    choices=next(a.choices for a in build._actions if a.dest=='renderer')
    routes={}
    for selector in dict.fromkeys(choices):
        key=canonical_selector(selector)
        if selector=='hors-v4-gmod3':core=None;native='hors-v4-gmod3'
        elif key=='hors-renderer-v4':core=native='hors-v4-ef'
        elif key=='hors-renderer-v5':core=native='hors-v5-c1'
        elif key=='hors-renderer-v5-c2':core=native='hors-v5-c2'
        elif key=='hors-renderer-v3':core='hors-renderer-v3';native='hors-v3'
        elif key.startswith('hors-render-v2-beta1'):
            core='hors-render-v2-beta1';native='hors-render-v2-beta1-scene'
        elif key.startswith('hors-render-v2'):
            core='hors-render-v2';native='hors-v2-scene'
        elif key.startswith('hors-render-v1'):
            core='yunroll-cart-v10';native='yunroll-cart-v10-scene'
        elif key.endswith('-scene'):core=key.removesuffix('-scene');native=key
        elif key in CORE_METHODS:
            core=key;native=key+'-scene' if key+'-scene' in SCENE_METHODS else None
        else:raise ValueError('Renderer missing from history matrix: '+selector)
        if core is not None and core not in CORE_METHODS:raise ValueError(core)
        if native is not None and native not in SCENE_METHODS:raise ValueError(native)
        routes[selector]=dict(core=core,native=native)
    return routes


def freeze_scene(path, out):
    from c643d.sceneio import load_scene
    from c643d.pipeline import build_scene_frames
    from c643d.cartuniform import Demo
    from c643d.font import bitmap_text
    scene = load_scene(path)
    colors = scene.mesh.source_colors
    foreground = colors[0] if colors else 1
    percell = len(colors) > 1
    frames, _ = build_scene_frames(scene, visibility_mode='surface', z_tolerance=.0008,
        feature_angle=40, enable_source_colors=percell, fallback_color=foreground,
        background_color=0, height=192, width=scene.viewport_width,
        max_frames=65535, max_visible_runs=65535)
    demo = Demo(scene.name, frames, percell, foreground << 4,
        bitmap_text(scene.name[:31],31), path.name, sha(path))
    row = asdict(demo); row['hud'] = demo.hud.hex()
    save(out, dict(format='c643d-vector-reference-v1', demos=[row]))
    return dict(name=scene.name, frames=len(frames), source_sha256=sha(path),
        pictures_sha256=picture_hash(frames, demo.screen), reference=out.name,
        private=True, viewport_width=scene.viewport_width, scene=str(path))


def core_matrix(case, reference, out, args):
    from compare_renderers import METHODS, EXTRA_METHODS
    work = out/'core'
    command = [sys.executable, str(ROOT/'tools/compare_renderers.py'), '--workspace',str(work),
        '--reference-json',str(reference), '--methods',*CORE_METHODS, '--loops',str(args.loops),
        '--workers',str(args.workers), '--tass',args.tass, '--cartconv',args.cartconv,
        '--vice',args.vice, '--vice-data',str(args.vice_data)]
    with (out/'core.log').open('w') as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    rows = []
    for method, preference in METHODS+EXTRA_METHODS:
        if method not in CORE_METHODS:continue
        key = method+('-ram' if preference=='ram' else '')
        result = work/'results'/(key+'-play-all.json')
        row = dict(method=method, preference=preference)
        if not result.exists():
            row.update(status='failed', reason='Build/measurement failed; see core/menu-'+method+'-'+preference+'.log')
        else:
            timing=json.loads(result.read_text())
            if timing.get('unsupported'):
                reasons=json.loads((work/'results'/(key+'-unsupported.json')).read_text())
                row.update(status='capacity', reason='; '.join(r['reason'] for r in reasons))
            else:
                try:
                    proof=json.loads((work/'results'/(key+'-pixels-00.json')).read_text())
                    assert proof['pixel_match'] and proof['color_match'] and proof['orientations']==case['frames']
                    assert len(timing['entries'])==1 and timing['entries'][0]['frame_count']==case['frames']
                    from c643d.cartpaths import menu_manifest_path
                    metadata=json.loads(menu_manifest_path(work/'carts'/(key+'.crt')).read_text())
                    entry=metadata['streamed_entries'][0]
                    oracle=json.loads((work/'source'/entry['work']/'oracle.json').read_text())
                    assert picture_hash(oracle,entry['screen_color'])==case['pictures_sha256'],'Core picture bytes/colours/order differ'
                    row.update(status='passed', timing=timing['entries'][0], verification=proof,
                        size=json.loads((work/'results'/(key+'-sizes.json')).read_text())['entries'][0],
                        crt_bytes=(work/'carts'/(key+'.crt')).stat().st_size,
                        crt_sha256=sha(work/'carts'/(key+'.crt')))
                except (OSError, AssertionError, KeyError) as error:
                    row.update(status='failed', reason='Incomplete/mismatched verification: '+str(error))
        rows.append(row)
    hashes={r['timing']['oracle_sha256'] for r in rows if r['status']=='passed'}
    if len(hashes)!=1:raise RuntimeError('Core matrix does not share one complete input oracle')
    return dict(protocol='Normal PLAY ALL; three ten-second visits by default; no FPS cap; common V9 controller',
        loops=args.loops, rows=rows, command=command, subprocess_returncode=completed.returncode)


def native_one(case, reference, out, args, method, *, draw_gap=6, batch_budget=2048, color_plan="auto"):
    from c643d import cli, pipeline
    from c643d.pipeline import FrameBuild
    from compare_cart_stream import measure_display
    from verify_cart_stream import verify
    from profile_cart_stream import profile
    root=out/'native';root.mkdir()
    shutil.copytree(ROOT/'c64',root/'c64');shutil.copy2(ROOT/'VERSION',root/'VERSION')
    frozen=json.loads(reference.read_text())['demos'][0]
    frames=[FrameBuild(**f) for f in frozen['frames']]
    old={name:getattr(cli,name) for name in ('ROOT','C64','BUILD','GENERATED')}
    old_builder=pipeline.build_scene_frames
    rows=[]
    try:
        cli.ROOT,cli.C64,cli.BUILD,cli.GENERATED=root,root/'c64',root/'build',root/'generated'
        pipeline.build_scene_frames=lambda *a,**k:(deepcopy(frames),0)
        for method in (method,):
            print(case['name'],method,'native scene',flush=True)
            row=dict(method=method,preference='fps',draw_gap=draw_gap,batch_budget=batch_budget)
            folder=root/method;folder.mkdir()
            cart_type='gmod3' if method.endswith('gmod3') else 'easyflash'
            argv=['build','--no-config','--scene',case['scene'],'--renderer',method,
                '--cart-type',cart_type,'--frame-ticks','4','--output','scene',
                '--output-dir',str(folder),'--tass',args.tass,'--cartconv',args.cartconv,
                '--v2-draw-gap',str(draw_gap),'--v2-batch-budget',str(batch_budget)]
            if method=='hors-v5-c2':argv+=['--v5-color-plan',color_plan]
            log_path=folder/'build.log'
            with log_path.open('w') as log,redirect_stdout(log),redirect_stderr(log):
                try:
                    code=cli.main(argv)
                except Exception:
                    traceback.print_exc();code=1
            if code:
                reason=capacity_reason(log_path.read_text())
                row.update(status='capacity' if reason else 'failed',reason=reason or 'Build failed; see native/'+method+'/build.log')
                rows.append(row);save(folder/'result.json',row);continue
            crt=folder/'scene.crt';meta=json.loads((folder/'scene-manifest.json').read_text())
            work=root/meta.get('runtime_work','build/scene-stream-scene')
            oracle=work/'oracle.json'
            # Each older scene backend uses the same stem/work path; preserve
            # the just-built runtime before the next method uses that path.
            snapshot=folder/'runtime';shutil.copytree(work,snapshot)
            meta['runtime_work']=str(snapshot.relative_to(root))
            save(folder/'scene-manifest.json',meta)
            digest=picture_hash(json.loads(oracle.read_text()),meta['screen_color'])
            try:
                assert digest==case['pictures_sha256'],'Native picture bytes/colours/order differ'
                initial=sha(crt)
                check=verify(crt,args.vice,args.vice_data,cycles=2,oracle_path=oracle,
                    capture=folder/'previews' if args.capture else None)
                display=measure_display(dict(crt=crt,meta=meta,work=work),args.vice,args.vice_data)
                stages=profile(crt,args.vice,args.vice_data)
                assert sha(crt)==initial,'Measurement changed cartridge bytes'
                row.update(status='passed',display=display,profile=stages,verification=check,
                    pictures_sha256=digest,crt_sha256=initial,crt_bytes=crt.stat().st_size,
                    rom_frame_bytes=meta.get('rom_frame_bytes'),cartridge=cart_type,
                    color_plan=meta.get('color_policy',{}).get('c2_color_plan'),
                    hud_text=meta.get('hud_text'),source_frames=meta.get('source_frames'))
            except Exception as error:
                (folder/'measurement-error.log').write_text(traceback.format_exc())
                row.update(status='failed',reason=str(error))
            rows.append(row);save(folder/'result.json',row)
    finally:
        pipeline.build_scene_frames=old_builder
        for name,value in old.items():setattr(cli,name,value)
    return dict(protocol='Native automatic scene playback; four PAL refresh minimum hold; one warmup loop and two measured loops; GMod3 retains its own HUD',rows=rows)



def native_matrix(case, reference, out, args):
    native=out/'native-methods';native.mkdir()
    def run(method):
        folder=native/method;folder.mkdir()
        config=folder/'job.json'
        save(config,dict(case=case,reference=str(reference),out=str(folder),method=method,
            args={key:getattr(args,key) for key in ('tass','cartconv','vice','capture')}|
                 dict(vice_data=str(args.vice_data))))
        with (folder/'run.log').open('w') as log:
            result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--_native-one',str(config)],
                stdout=log,stderr=subprocess.STDOUT)
        path=folder/'result.json'
        row=json.loads(path.read_text()) if path.exists() else dict(method=method,preference='fps',
            status='failed',reason='Worker failed; see native-methods/'+method+'/run.log')
        print(case['name'],method,row['status'],flush=True)
        return row
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows=list(pool.map(run,SCENE_METHODS))
    return dict(protocol='Native automatic scene playback; four PAL refresh minimum hold; one warmup loop and two measured loops; GMod3 retains its own HUD',rows=rows)


def markdown(report):
    lines=['# Renderer history comparison','',
        'PAL VICE, default machine settings, sound disabled, seed 1. No source samples are removed. '
        'N/A means a confirmed capacity limit; FAIL means a build or verification error. '
        'Compare FPS within each table: the core harness is uncapped, native scenes retain four-refresh pacing.','']
    for case in report['cases']:
        lines += ['## '+case['name'], '',f"{case['frames']} pictures; input picture SHA-256 `{case['pictures_sha256']}`.",'']
        for group in ('core','native'):
            if group not in case:continue
            lines += ['### '+('Original cores / common PLAY ALL' if group=='core' else 'Native scene backends'),'',case[group]['protocol']+'.','',
                '| Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Result / reason |',
                '| --- | --- | ---: | ---: | ---: | ---: | --- |']
            for row in case[group]['rows']:
                start=f"| {row['method']} | {row['preference']} |"
                if row['status']!='passed':
                    score='N/A' if row['status']=='capacity' else 'FAIL'
                    lines.append(start+f" {score} | {score} | {score} | — | "+row['reason'].replace('|','/')+' |')
                else:
                    d=row['timing'] if group=='core' else row['display']
                    avg=d['display_fps'] if group=='core' else d['displayed_fps']
                    lines.append(start+f" {d['high_fps']:.3f} | {avg:.3f} | {d['low_fps']:.3f} | {row['crt_bytes']:,} | pixels and colours passed |")
            lines.append('')
    lines += ['## Selector coverage','','Spelling aliases are grouped; distinct implementations are measured separately. '
        'HORS-V1 is yunroll-cart-v10; HORS-V2 uses a different encoder/mapping path despite sharing that assembly base. '
        'HORS-V4 EasyFlash preserves the V3 core. Scene-suffixed runtimes have their own paced table. '
        'GMod3 appears only in the native table because the common controller is EasyFlash-specific. '
        'GMod4 remains roadmap work.','',
        '`hors-vN`, `hors-render-vN` and accepted `hors-renderer-vN` spellings follow the CLI aliases. '
        '`hors-v4` defaults to EasyFlash; `hors-v4-gmod3` is measured separately. '
        '`hors-v1-scene` / `hors-render-v1-scene` select v10-scene; V2 scene aliases select the stable V2 scene path.','',
        'This is a comparison across implementations, not an old-release versus new-release regression claim. '
        'High/low FPS describe observed display intervals, not sustained rates. Physical hardware and NTSC are unmeasured.','']
    lines += ['| Accepted selector | Core table | Native scene table |',
              '| --- | --- | --- |']
    for selector, route in report.get('selectors', {}).items():
        lines.append(f"| `{selector}` | {route['core'] or '—'} | {route['native'] or '—'} |")
    lines += ['', 'The native column identifies the corresponding scene backend; it does not imply '
              'that every unsuffixed historical selector automatically switches to it.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',type=Path,action='append',default=[])
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--name',default='Nightdrive Test')
    p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv');p.add_argument('--vice',default='x64sc')
    p.add_argument('--vice-data',type=Path,default=Path('/usr/local/share/vice'))
    p.add_argument('--workers',type=int,default=3);p.add_argument('--loops',type=int,default=3)
    p.add_argument('--capture',action='store_true')
    p.add_argument('--core-only',action='store_true',help='diagnostic subset: omit the native scene table')
    a=p.parse_args();out=a.out.expanduser().resolve()
    if out.exists() or out==ROOT or ROOT in out.parents or out in ROOT.parents:p.error('--out must be a new directory outside the checkout')
    if not 1<=a.workers<=4 or not 1<=a.loops<=20:p.error('workers 1..4; loops 1..20')
    for key in ('tass','cartconv','vice'):
        value=shutil.which(getattr(a,key))
        if not value:p.error('Executable not found: '+getattr(a,key))
        setattr(a,key,str(Path(value).resolve()))
    a.vice_data=a.vice_data.expanduser().resolve()
    scenes=[x.expanduser().resolve() for x in a.scene]
    if any(not x.is_file() or x.suffix.lower()!='.c643dscene' for x in scenes):p.error('--scene requires existing .c643dscene exports')
    if len({x.stem for x in scenes})!=len(scenes):p.error('scene basenames must be unique')
    out.mkdir(parents=True)
    from c643d.cartframes import load_menu_reference
    control=next(d for d in load_menu_reference(ROOT) if d.name=='CUBE')
    row=asdict(control);row['hud']=control.hud.hex()
    reference=out/'public-cube.json';save(reference,dict(format='c643d-vector-reference-v1',demos=[row]))
    cases=[dict(name='Public original CUBE control',frames=len(control.frames),private=False,
        pictures_sha256=picture_hash(control.frames,control.screen),reference=reference.name)]
    for scene in scenes:
        print('Freezing',scene.name,flush=True)
        case=freeze_scene(scene,out/(scene.stem+'-reference.json'))
        case['name']=a.name+': '+scene.stem
        cases.append(case)
    from compare_renderers import fingerprints
    _,source_hash=fingerprints(ROOT)
    report=dict(format='c643d-renderer-history-v1',version=(ROOT/'VERSION').read_text().strip(),
        selectors=selector_coverage(),source_sha256=source_hash,
        tools={key:dict(sha256=sha(getattr(a,key)),version=subprocess.run(
            [getattr(a,key),'--version'],text=True,capture_output=True,check=False).stdout.splitlines()[0])
            for key in ('tass','cartconv','vice')},cases=cases,passed=False)
    for i,case in enumerate(cases):
        destination=out/f'case-{i:02d}';destination.mkdir()
        print(case['name'],'full core matrix',flush=True)
        case['core']=core_matrix(case,out/case['reference'],destination,a)
        save(out/'comparison.json',report)
        if case['private'] and not a.core_only:
            case['native']=native_matrix(case,out/case['reference'],destination,a)
        save(out/'comparison.json',report);(out/'comparison.md').write_text(markdown(report))
    report['passed']=all(case['core']['subprocess_returncode']==0 for case in cases) and all(row['status']!='failed' for case in cases for group in ('core','native') if group in case for row in case[group]['rows'])
    for case in cases:
        if case.get('scene') and sha(case['scene'])!=case['source_sha256']:raise RuntimeError('Input scene changed during measurement')
    if fingerprints(ROOT)[1]!=source_hash:raise RuntimeError('Source inputs changed during measurement')
    save(out/'comparison.json',report);(out/'comparison.md').write_text(markdown(report))
    print(out/'comparison.md',flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--_native-one':
        from types import SimpleNamespace
        job=json.loads(Path(sys.argv[2]).read_text())
        result=native_one(job['case'],Path(job['reference']),Path(job['out']),SimpleNamespace(**job['args']),job['method'])
        save(Path(job['out'])/'result.json',result['rows'][0])
    else:
        raise SystemExit(main())
