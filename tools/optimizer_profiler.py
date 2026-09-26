#!/usr/bin/env python3
"""Measure all renderer families; rank lossless native EasyFlash scene candidates."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

from benchmark_renderer_history import ROOT, SCENE_METHODS, freeze_scene, native_one, core_matrix, selector_coverage, save, sha

METHODS = tuple(SCENE_METHODS)
TUNABLE = ('hors-render-v2-beta1-scene','hors-v2-scene','hors-v3','hors-v4-ef','hors-v5-c1','hors-v5-c2')
BASELINE = ('hors-v4-ef', 6, 2048)


def candidate_id(method, gap, budget):
    return f'{method}-g{gap}-b{budget}'


def select(rows, baseline_id, tolerance_percent=0.5):
    """Highest verified average FPS wins; tail regressions remain explicit."""
    baseline = next((r for r in rows if r['candidate'] == baseline_id and r['status'] == 'passed'), None)
    if baseline is None:
        return dict(winner=None, reason='The V4 reference did not pass; no recommendation', automatically_promoted=False)
    passed = [r for r in rows if r['status'] == 'passed' and r.get('cartridge','easyflash')=='easyflash']
    factor = 1 + tolerance_percent/100
    for row in passed:
        row['tail_gate_passed'] = all(row['display'][key] <= baseline['display'][key]*factor
                                      for key in ('p95_ms', 'worst_ms'))
    best = max(r['display']['displayed_fps'] for r in passed)
    tied = [r for r in passed if r['display']['displayed_fps'] == best]
    winner = min(tied, key=lambda r: (r['crt_bytes'], r['profile']['mean_render_cycles'], r['candidate']))
    return dict(winner=winner['candidate'], throughput_ties=[r['candidate'] for r in tied],
        baseline=baseline_id, tolerance_percent=tolerance_percent,
        rule='Require exact pictures and passing VICE checks; highest measured average FPS wins. Exact FPS ties prefer smaller CRT then less active work. Tail regressions are reported, not hidden or used to relabel a slower candidate as the FPS winner.',
        near_ties=[r['candidate'] for r in passed if r['display']['displayed_fps']>=best/factor],
        fastest_measured=max(passed, key=lambda r:r['display']['displayed_fps'])['candidate'],
        automatically_promoted=False)


def console_table(rows, *, core=False, color=False):
    """Terminal table with an explicit text marker even without ANSI support."""
    def metrics(row):
        return row.get('timing',{}) if core else row.get('display',{})
    key='display_fps' if core else 'displayed_fps'
    passed=[r for r in rows if r['status']=='passed' and (core or r.get('cartridge','easyflash')=='easyflash')]
    best=max((metrics(r)[key] for r in passed),default=None)
    header=('Renderer / setting','Pref','Avg FPS','P95 ms','Worst ms','CRT bytes','Result')
    data=[]
    for row in sorted(rows,key=lambda r:(r['status']!='passed',-metrics(r).get(key,0))):
        name=row['method'] if core else row['candidate']
        if row['status']!='passed':
            cells=(name,row.get('preference','fps'),'N/A' if row['status']=='capacity' else 'FAIL','-','-','-',row['reason'])
            data.append((cells,False));continue
        m=metrics(row)
        win=(core or row.get('cartridge','easyflash')=='easyflash') and m[key]==best
        note='WINNER' if win else 'passed'
        if not core and row.get('cartridge')=='gmod3':note='GMod3 reference'
        elif not core and row.get('tail_gate_passed') is False:note+='; tail regression'
        cells=(name,row.get('preference','fps'),f'{m[key]:.5f}',
            (f"{m['p95_display_ms']:.3f}" if 'p95_display_ms' in m else '-') if core else f"{m['p95_ms']:.3f}",
            f"{1000/m['low_fps']:.3f}" if core else f"{m['worst_ms']:.3f}",f"{row['crt_bytes']:,}",note)
        data.append((cells,win))
    widths=[max(len(str(cells[i])) for cells,_ in [(header,False)]+data) for i in range(len(header))]
    def line(cells):return ' | '.join(str(v).ljust(widths[i]) if i in (0,1,6) else str(v).rjust(widths[i]) for i,v in enumerate(cells))
    lines=[line(header),'-+-'.join('-'*w for w in widths)]
    for cells,win in data:
        rendered=line(cells)
        lines.append('\033[1;32m'+rendered+'\033[0m' if win and color else rendered)
    return '\n'.join(lines)


def markdown(report):
    lines = ['# Scene optimizer-profiler', '',
        'PAL VICE; identical pictures, colours, order and four-refresh minimum hold. '
        'One warmup loop and two measured loops. N/A is a capacity limit; FAIL is an error. '
        'GMod3 retains its own HUD/controller and is listed for reference, not eligible for the EasyFlash winner.', '',
        '| Candidate | Average FPS | P95 hold ms | Worst hold ms | Active cycles | CRT bytes | Result |',
        '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for row in sorted(report['rows'],key=lambda r:(r['status']!='passed',-r.get('display',{}).get('displayed_fps',0))):
        if row['status'] != 'passed':
            status = 'N/A' if row['status']=='capacity' else 'FAIL'
            lines.append(f"| {row['candidate']} | {status} | — | — | — | — | {row['reason'].replace('|','/')} |")
            continue
        d=row['display']; p=row['profile']
        gate=('passed; separate hardware' if row.get('cartridge')=='gmod3' else
              'passed; tail within tolerance' if row.get('tail_gate_passed') else 'passed; tail regression')
        label=row['candidate']+(' **WINNER**' if row['candidate']==report['selection'].get('winner') and report['passed'] else '')
        lines.append(f"| {label} | {d['displayed_fps']:.5f} | {d['p95_ms']:.3f} | {d['worst_ms']:.3f} | {p['mean_render_cycles']:,.2f} | {row['crt_bytes']:,} | {gate} |")
    choice=report['selection']
    lines += ['', 'Recommendation: **'+str(choice.get('winner'))+'**. No settings or source files were changed.', '',
        choice.get('rule',choice.get('reason','')), '',
        '## Where the time goes', '',
        '| Candidate | Clear/reset | Fetch | Apply colours | Draw |',
        '| --- | ---: | ---: | ---: | ---: |']
    for row in report['rows']:
        if row['status']=='passed':
            stages=row['profile']['mean_cycles']
            lines.append('| '+row['candidate']+' | '+' | '.join(f'{stages.get(k,0):,.2f}' for k in (
                'recycle_bitmap_and_colors','fetch','apply_colors','draw_lines'))+' |')
    c=report['colour_conflicts']
    mapping=report['colour_mapping']
    lines += ['', 'Stage values are elapsed emulated PAL cycles, including VIC stalls and IRQ work. '
        'Presentation waiting is excluded from active rendering.', '',
        '## Colour diagnosis', '',
        'Recorded Blender colour interpretation: **'+str(mapping['blender_color_space'])+'**. '
        'Exported face-colour counts (C64 indices): `'+str(mapping['face_colour_counts'])+'`.', '',
        'A .c643dscene already contains palette indices. Changing blender_color_space cannot '
        'reinterpret these; re-export the .blend to compare linear/sRGB. Original material RGB '
        'and shader-node values are not present in this interchange format.', '',
        f"Source colour conflicts: {c['mean_cells']:.2f} cells/frame on average; maximum {c['max_cells']}. "
        'These are 8×8 cells containing more than one requested foreground colour. '
        'Exact-picture verification preserves the current colour choices; it is not a visual-quality approval.', '',
        'The search is finite, not a global optimum. It does not vary geometry, colours, source samples, '
        'minimum hold, hardware, RAM layout, or video standard. Colour/depth changes require a separate '
        'visual comparison and their own reference pictures. Physical hardware and NTSC are unmeasured.', '']
    if 'history' in report:
        lines += ['## Original cores: common PLAY ALL comparison', '',
            'All original cores are retained here, including capacity N/As. '
            'These runs use an uncapped common V9 controller, three ten-second visits; '
            'their rates are not mixed into the native scene winner ranking.', '',
            '| Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Result |',
            '| --- | --- | ---: | ---: | ---: | ---: | --- |']
        for row in report['history']['rows']:
            if row['status']=='passed':
                t=row['timing']
                lines.append(f"| {row['method']} | {row['preference']} | {t['high_fps']:.3f} | {t['display_fps']:.3f} | {t['low_fps']:.3f} | {row['crt_bytes']:,} | passed |")
            else:
                status='N/A' if row['status']=='capacity' else 'FAIL'
                lines.append(f"| {row['method']} | {row['preference']} | {status} | {status} | {status} | — | {row['reason'].replace('|','/')} |")
        lines += ['', 'Accepted spelling aliases and their core/native routes are in selectors.json. '
            'Historical core CRTs remain under history/core/carts/.', '']
    return '\n'.join(lines)


def worker(path):
    job=json.loads(Path(path).read_text())
    result=native_one(job['case'], Path(job['reference']), Path(job['out']),
        SimpleNamespace(**job['args']), job['method'], draw_gap=job['gap'], batch_budget=job['budget'])['rows'][0]
    result['candidate']=job['candidate']
    save(Path(job['out'])/'result.json',result)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scene',type=Path)
    parser.add_argument('--out',type=Path,required=True,help='new directory outside the checkout')
    parser.add_argument('--renderers',nargs='+',choices=METHODS,default=list(METHODS),
                        type=lambda value: 'hors-v5-c1' if value=='hors-v5-ef' else value)
    parser.add_argument('--gaps',nargs='+',type=int,default=[3,6,12])
    parser.add_argument('--budgets',nargs='+',type=int,default=[2048])
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--tolerance-percent',type=float,default=0.5)
    parser.add_argument('--capture',action='store_true',help='capture every verified candidate')
    parser.add_argument('--tass',default='64tass');parser.add_argument('--cartconv',default='cartconv')
    parser.add_argument('--vice',default='x64sc');parser.add_argument('--vice-data',type=Path)
    args=parser.parse_args(argv)
    out=args.out.expanduser().resolve();scene=args.scene.expanduser().resolve()
    if out==ROOT or ROOT in out.parents:parser.error('--out must be outside the checkout')
    if out.exists():parser.error('--out must be new; previous evidence is preserved')
    if not scene.is_file() or scene.suffix.lower()!='.c643dscene':parser.error('scene must be an existing .c643dscene export')
    if not 1<=args.workers<=4:parser.error('--workers must be 1..4')
    if not 0<=args.tolerance_percent<=10:parser.error('--tolerance-percent must be 0..10')
    if any(not 1<=n<=255 for n in args.gaps) or any(n<1 for n in args.budgets):parser.error('gaps must be 1..255; budgets must be positive')
    for key in ('tass','cartconv','vice'):
        value=shutil.which(getattr(args,key))
        if not value:parser.error('Executable not found: '+getattr(args,key))
        setattr(args,key,str(Path(value).resolve()))
    args.vice_data=str(args.vice_data.expanduser().resolve()) if args.vice_data else None
    from compare_renderers import fingerprints
    source_hash=fingerprints(ROOT)[1]
    out.mkdir(parents=True)
    # Copy the input as well as frozen pictures. Workers cannot silently load a
    # newly edited source while sharing the old projection/picture reference.
    source_hash_before=sha(scene);snapshot=out/'input.c643dscene';shutil.copy2(scene,snapshot)
    if sha(snapshot)!=source_hash_before:raise RuntimeError('Input changed while taking snapshot')
    reference=out/'reference.json';case=freeze_scene(snapshot,reference)
    frames=json.loads(reference.read_text())['demos'][0]['frames']
    raw_scene=json.loads(snapshot.read_text())
    conflicts=[f['color_conflicts'] for f in frames]
    configs=[BASELINE]
    for method in args.renderers:
        configs.extend((method,gap,budget) for gap,budget in (
            itertools.product(args.gaps,args.budgets) if method in TUNABLE else [(6,2048)]))
    configs=list(dict.fromkeys(configs))
    report=dict(format='c643d-optimizer-profiler-v1',version=(ROOT/'VERSION').read_text().strip(),
        source_sha256=source_hash,input_sha256=source_hash_before,pictures_sha256=case['pictures_sha256'],
        frames=case['frames'],frame_ticks=4,rows=[],selection={},passed=False,
        colour_conflicts=dict(mean_cells=sum(conflicts)/len(conflicts),max_cells=max(conflicts)),
        colour_mapping=dict(blender_color_space=raw_scene.get('source',{}).get('blender_color_space','not recorded'),
            face_colour_counts=dict(Counter(str(c) for c in raw_scene['topology'].get('face_colors',[]))),
            material_rgb_available=False),
        tools={key:dict(sha256=sha(getattr(args,key))) for key in ('tass','cartconv','vice')})
    def run(config):
        method,gap,budget=config;name=candidate_id(*config);folder=out/name;folder.mkdir()
        job=dict(case=case,reference=str(reference),out=str(folder),method=method,gap=gap,budget=budget,candidate=name,
            args={key:getattr(args,key) for key in ('tass','cartconv','vice','vice_data','capture')})
        save(folder/'job.json',job)
        with (folder/'run.log').open('w') as log:
            try:
                done=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(folder/'job.json')],
                    stdout=log,stderr=subprocess.STDOUT,timeout=900)
                if done.returncode:raise RuntimeError('Worker exited '+str(done.returncode))
                row=json.loads((folder/'result.json').read_text())
            except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
                row=dict(candidate=name,method=method,draw_gap=gap,batch_budget=budget,status='failed',reason=str(error)+'; see '+name+'/run.log')
                save(folder/'result.json',row)
        print(name+': '+row['status']+(f"; {row['display']['displayed_fps']:.5f} FPS" if row['status']=='passed' else ''),flush=True)
        return row
    print(f'{len(configs)} fixed-picture candidates; {args.workers} independent processes',flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(run,configs):
            report['rows'].append(row);save(out/'results.json',report)
    print('Original cores: full common-controller comparison',flush=True)
    history_out=out/'history';history_out.mkdir()
    args.loops=3
    report['history']=core_matrix(case,reference,history_out,args)
    save(out/'selectors.json',selector_coverage())
    if sha(scene)!=source_hash_before or sha(snapshot)!=source_hash_before:raise RuntimeError('Input scene changed during measurement')
    if fingerprints(ROOT)[1]!=source_hash:raise RuntimeError('Source code changed during measurement')
    report['selection']=select(report['rows'],candidate_id(*BASELINE),args.tolerance_percent)
    if report['selection']['winner']:
        chosen=next(r for r in report['rows'] if r['candidate']==report['selection']['winner'])
        report['selection']['cartridge']=f"{chosen['candidate']}/native/{chosen['method']}/scene.crt"
        report['selection']['build_flags']=['--renderer',chosen['method'],'--v2-draw-gap',str(chosen['draw_gap']),
            '--v2-batch-budget',str(chosen['batch_budget']),'--frame-ticks','4']
    report['passed']=(bool(report['selection']['winner']) and report['history']['subprocess_returncode']==0
        and all(r['status']!='failed' for r in report['rows']+report['history']['rows']))
    if report['passed']:
        chosen=next(r for r in report['rows'] if r['candidate']==report['selection']['winner'])
        source_cart=out/report['selection']['cartridge']
        folder=out/'winner';folder.mkdir()
        slug=re.sub(r'[^A-Za-z0-9_-]+','-',scene.stem).strip('-') or 'scene'
        stem=slug+'-WINNER-'+chosen['candidate']
        winner_cart=folder/(stem+'.crt')
        shutil.copy2(source_cart,winner_cart)
        shutil.copy2(source_cart.with_suffix('.lbl'),winner_cart.with_suffix('.lbl'))
        meta=json.loads(source_cart.with_name('scene-manifest.json').read_text())
        candidate_root=out/chosen['candidate']/'native'
        meta['runtime_work']=str((candidate_root/meta['runtime_work']).relative_to(out))
        save(folder/(stem+'-manifest.json'),meta)
        assert sha(winner_cart)==chosen['crt_sha256'],'Winner copy differs from measured cartridge'
        report['selection']['cartridge']=str(winner_cart.relative_to(out))
    save(out/'results.json',report);save(out/'selection.json',report['selection'])
    (out/'comparison.md').write_text(markdown(report))
    ansi=sys.stdout.isatty() and 'NO_COLOR' not in os.environ and os.environ.get('TERM')!='dumb'
    native_table=console_table(report['rows'],color=ansi)
    core_table=console_table(report['history']['rows'],core=True,color=ansi)
    print('\nNATIVE SCENES: fixed four-refresh hold; EasyFlash FPS winner\n'+native_table)
    print('\nORIGINAL CORES: uncapped common PLAY ALL; separate FPS winner\n'+core_table)
    (out/'comparison.txt').write_text('NATIVE SCENES\n'+console_table(report['rows'])+'\n\nORIGINAL CORES (different protocol)\n'+console_table(report['history']['rows'],core=True)+'\n')
    print('Recommendation' if report['passed'] else 'Provisional recommendation (search failed)',':',report['selection']['winner']);print(out/'comparison.md')
    if report['selection']['winner']:
        print('Selected cartridge:',out/report['selection']['cartridge'])
        print('Reuse with:',' '.join(report['selection']['build_flags']))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker':worker(sys.argv[2])
    else:raise SystemExit(main())
