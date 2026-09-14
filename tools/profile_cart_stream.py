#!/usr/bin/env python3
"""Profile labelled renderer stages in PAL VICE, including finite scenes.

Elapsed emulated cycles include VIC stalls and IRQ work. Presentation waiting
is separate from rendering. Rebuild the cart for matching stage labels.
"""
from pathlib import Path
from c643d.cartpaths import menu_manifest_path
import argparse, hashlib, json, re, statistics, subprocess, tempfile
from verify_cart_stream import labels, startup_monitor

CLOCK = 985248


def profile(crt, vice, vice_data=None, menu_entry=None):
    crt = Path(crt).resolve()
    root = Path(__file__).resolve().parents[1]
    menu = None
    if menu_entry is None:
        manifest = json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
        sym = labels(crt.with_suffix('.lbl'))
    else:
        cart = json.loads(menu_manifest_path(crt).read_text())
        manifest = cart['streamed_entries'][menu_entry]
        sym = labels(root / manifest['work'] / 'runtime.lbl')
        menu = labels(root/'build'/f'{crt.stem}-cartridge-demo'/f'{crt.stem}-runtime-default.lbl')
    n = manifest['frames']
    finite = manifest.get('ending', False)
    warmup = 0 if finite else 3
    stages = []
    if 'profile_directory' in sym:
        stages.append(('directory', 'profile_directory'))
    if 'profile_lookup' in sym:
        stages.append(('picture_lookup_and_queue_wait', 'profile_lookup'))
    # V6 recycles before loading metadata directly into that slot's cache.
    load_stages = [('fetch', 'profile_fetch'), ('recycle_bitmap_and_colors', 'profile_recycle')]
    stages += sorted(load_stages, key=lambda item: sym[item[1]])
    if 'profile_cache' in sym:
        stages.append(('cache_metadata', 'profile_cache'))
    if manifest['colors']:
        stages.append(('apply_colors', 'profile_colors'))
    stages += [('draw_lines', 'profile_draw'), ('bookkeeping', 'frame_draw_complete'),
               ('publish_wait', 'profile_publish'), ('publish_commit', 'profile_publish_ready'),
               ('advance_and_final_hold', 'profile_published')]
    missing = [s for _, s in stages if s not in sym]
    if missing:
        raise ValueError(f'Rebuild this cartridge for explicit profiling labels: {missing}')
    count = n + warmup
    with tempfile.TemporaryDirectory(prefix='c643d-profile-') as td:
        td = Path(td)
        mon = ['delete']
        first_go = 'g'
        if menu is None:
            startup,first_go = startup_monitor(manifest,sym)
            mon += startup
        if menu is not None:
            mon += [f'break ${menu["menu_wait_key"]:04x}', 'g', 'delete',
                    f'> ${menu["selected_entry"]:04x} ${menu_entry:02x}']
            first_go = f'g ${menu["menu_launch_nowait"]:04x}'
        for fi in range(count):
            for j, (_, label) in enumerate(stages):
                mon += [f'break ${sym[label]:04x}', first_go if fi == j == 0 else 'g',
                        'stopwatch', 'delete']
        terminal = 'outro_start' if finite else 'frame_begin'
        mon += [f'break ${sym[terminal]:04x}', 'g', 'stopwatch', 'quit']
        (td/'run.mon').write_text('\n'.join(mon)+'\n')
        cmd = [str(vice), '-console', '+easyflashcrtwrite', '-pal', '+sound', '-warp', '-seed', '1',
               '-cartcrt', str(crt), '-initbreak', 'reset', '-moncommands', str(td/'run.mon'),
               '-monlogname', str(td/'monitor.log'), '-monlog',
               '-limitcycles', str(count*1000000+40000000)]
        if vice_data:
            cmd += ['-directory', str(vice_data)]
        with (td/'vice.log').open('w') as log:
            run = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        log = (td/'monitor.log').read_text() if (td/'monitor.log').exists() else ''
        ticks = [int(x) for x in re.findall(r'Stopwatch:\s*(\d+)', log)]
        k = len(stages)
        if run.returncode or len(ticks) != count*k+1:
            raise RuntimeError('VICE did not reach every stage boundary:\n'+log[-1600:]+'\n'+'\n'.join(line for line in (td/'vice.log').read_text().splitlines() if any(w in line.lower() for w in ('error','unknown','failed','cannot','unrecognized'))) )
    rows = []
    active_count = next(i for i, (name, _) in enumerate(stages) if name == 'bookkeeping')
    for i in range(warmup, count):
        deltas = [ticks[i*k+j+1]-ticks[i*k+j] for j in range(k)]
        row = dict(frame=i % n, cycles=dict(zip([s[0] for s in stages], deltas)))
        row['render_cycles'] = sum(deltas[:active_count])
        row['total_cycles'] = sum(deltas)
        rows.append(row)
    means = {name: round(statistics.mean(r['cycles'][name] for r in rows), 2) for name, _ in stages}
    render = [r['render_cycles'] for r in rows]
    totals = [r['total_cycles'] for r in rows]
    report = dict(cartridge=crt.name, sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
                  renderer=manifest['renderer'], menu_entry=menu_entry, frames=n, finite=finite,
                  warmup_frames=warmup, clock_hz=CLOCK,
                  accounting='PAL elapsed cycles include VIC stalls and IRQs; publish_wait includes call/ready tests; final advance includes final display hold.',
                  mean_cycles=means, mean_render_cycles=round(statistics.mean(render), 2),
                  worst_render_cycles=max(render), mean_total_cycles=round(statistics.mean(totals), 2),
                  worst_total_cycles=max(totals), measured_seconds=sum(totals)/CLOCK,
                  frames_per_second=CLOCK/statistics.mean(totals), samples=rows)
    if 'frame_ticks' in manifest:
        budget = manifest['frame_ticks']*19656
        report.update(render_budget_cycles=budget, frames_exceeding_render_budget=sum(v > budget for v in render))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('crt', type=Path)
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data')
    p.add_argument('--menu-entry', type=int)
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    result = profile(a.crt, a.vice, a.vice_data, a.menu_entry)
    print(json.dumps({k: v for k, v in result.items() if k != 'samples'}, indent=2))
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(json.dumps(result, indent=2)+'\n')
