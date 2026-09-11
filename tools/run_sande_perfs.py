#!/usr/bin/env python3
"""Rebuild and measure the separate Sande test kit in stock-speed PAL VICE."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from build_sande_examples import MODELS, RENDERERS, ROOT, SOURCES, SET_ID, build, sha
from c643d.cartridge import inspect_easyflash_crt
from c643d.font import bitmap_text
from verify_cart_stream import expected_frame, apply_interactive_overlay, labels, startup_monitor, verify

CLOCK = 985248
PAL_CYCLES = 19656
REPORT = 'docs/benchmarks/sande/summary.json'
COLOR_REPORT = 'docs/benchmarks/sande/summary-color.json'


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def measure(crt, oracle, vice, vice_data, refreshes, cycle_ticks=None):
    """Observe actual VIC display slots after each IRQ, checking every picture."""
    manifest = json.loads(crt.with_name(crt.stem + '-manifest.json').read_text())
    sym = labels(crt.with_suffix('.lbl'))
    wanted = set()
    for frame in json.loads(oracle.read_text()):
        bitmap, colors = expected_frame(frame, manifest['screen_color'])
        apply_interactive_overlay(bitmap, manifest)
        wanted.add(hashlib.sha256(bitmap if cycle_ticks else bitmap + colors).digest())
    hud = bitmap_text(f"{manifest['name'].upper().replace('_', ' ')} "
                      f"V:{manifest['vertices']:03d} E:{manifest['edges']:03d}", 31)
    identity = sha(crt)
    with tempfile.TemporaryDirectory(prefix='c643d-sande-display-') as tmp:
        tmp = Path(tmp)
        startup, go = startup_monitor(manifest, sym)
        warmup = manifest['frames'] + 6
        commands = ['delete', *startup, f'break ${sym["profile_published"]:04x}',
                    go, *(['g'] * (warmup - 1)), 'delete']
        if cycle_ticks:
            commands += [f'> ${sym["sande_cycle_enabled"]:04x} $01',
                         f'> ${sym["sande_cycle_interval"]:04x} ${cycle_ticks:02x}']
        commands += [f'break ${sym["irq_no_flip"]:04x}']
        for i in range(refreshes + 1):
            commands += ['g', 'stopwatch', 'bank ram',
                         f'bsave "{tmp / f"{i}.ram"}" 0 $0000 $ffff', 'bank cpu',
                         f'bsave "{tmp / f"{i}.io"}" 0 $d000 $dd03']
        commands.append('quit')
        (tmp / 'run.mon').write_text('\n'.join(commands) + '\n')
        command = [str(vice), '-default', '-console', '+easyflashcrtwrite', '+saveres',
                   '-pal', '+sound', '-warp', '-seed', '1', '-jamaction', '5',
                   '-cartcrt', str(crt), '-initbreak', 'reset',
                   '-moncommands', str(tmp / 'run.mon'), '-monlog',
                   '-monlogname', str(tmp / 'monitor.log'), '-limitcycles',
                   str(warmup * 1000000 + (refreshes + 1) * PAL_CYCLES + 20000000)]
        if vice_data:
            command += ['-directory', str(vice_data)]
        with (tmp / 'vice.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=240)
        ticks = [int(v) for v in re.findall(r'Stopwatch:\s*(\d+)',
                                           (tmp / 'monitor.log').read_text())]
        if len(ticks) != refreshes + 1:
            raise RuntimeError('VICE did not reach every Sande display observation: ' +
                               (tmp / 'vice.log').read_text()[-1200:])
        seen, switches = set(), []
        palette_changes, previous_color = 0, None
        previous = None
        for i in range(refreshes + 1):
            ram = (tmp / f'{i}.ram').read_bytes()
            io = (tmp / f'{i}.io').read_bytes()
            slot = ram[sym['display_slot']]
            if slot not in (0, 1, 2):
                raise AssertionError(f'Invalid display slot: {slot}')
            baddr, saddr = (0x2000, 0x6000, 0xe000)[slot], (0x400, 0x4400, 0xc800)[slot]
            bitmap, colors = ram[baddr:baddr + 7680], ram[saddr:saddr + 960]
            if cycle_ticks:
                color = colors[0]
                if colors != bytes([color]) * 960 or color >> 4 == color & 15:
                    raise AssertionError('Automatic palette is inconsistent or invisible')
                if io[0x20] & 15 != color & 15 or io[0x21] & 15 != color & 15:
                    raise AssertionError('Automatic border/background mismatch')
                palette_changes += int(previous_color is not None and previous_color != color)
                previous_color = color
            picture = hashlib.sha256(bitmap if cycle_ticks else bitmap + colors).digest()
            if picture not in wanted:
                raise AssertionError(f'{crt.name}: displayed picture mismatch at refresh {i}')
            if ram[baddr + 7680:baddr + 7680 + len(hud)] != hud:
                raise AssertionError(f'{crt.name}: Sande HUD mismatch at refresh {i}')
            if io[0xd00] & 3 != (3, 2, 0)[slot] or io[0x18] & 0xfe != (0x18, 0x18, 0x28)[slot]:
                raise AssertionError('VIC bank/display-slot mismatch')
            seen.add(picture)
            if i and slot != previous:
                switches.append((i, ticks[i]))
            previous = slot
    if sha(crt) != identity:
        raise AssertionError('VICE modified the cartridge')
    intervals = [b[1] - a[1] for a, b in zip(switches, switches[1:])]
    if not intervals or not wanted.issubset(seen):
        raise AssertionError('Incomplete visible-picture coverage; increase --seconds')
    elapsed = ticks[-1] - ticks[0]
    # Cartridge mapping defers IRQ entry; allow one refresh at the two window
    # boundaries, while computing FPS from actual stopwatch cycles throughout.
    if abs(elapsed - refreshes * PAL_CYCLES) > PAL_CYCLES:
        raise AssertionError(f'Display window differs by more than one PAL refresh: {elapsed} vs {refreshes * PAL_CYCLES}')
    return dict(sha256=identity, clock_hz=CLOCK, refreshes=refreshes,
                warmup_samples=warmup, display_flips=len(switches), elapsed_cycles=elapsed,
                display_fps=len(switches) * CLOCK / elapsed,
                high_fps=CLOCK / min(intervals), low_fps=CLOCK / max(intervals),
                worst_display_ms=max(intervals) * 1000 / CLOCK,
                hold_ticks=dict(Counter(b[0] - a[0] for a, b in zip(switches, switches[1:]))),
                unique_pictures_expected=len(wanted), unique_pictures_observed=len(seen),
                picture_coverage_complete=True, pixel_match=True, color_match=True, hud_match=True,
                interactive_label_match=bool(manifest.get('interactive_overlay')),
                cycle_period_pal_ticks=cycle_ticks, observed_palette_changes=palette_changes)


def validate_report(root, report):
    if report.get('version') != (root / 'VERSION').read_text().strip():
        raise ValueError('Sande report version is stale; rerun tools/run_sande_perfs.py')
    for name, digest in report['source_sha256'].items():
        if sha(root / 'examples/demos_sande' / name) != digest:
            raise ValueError('Sande source or recipe changed: ' + name)
    rows = report['results']
    cases = {(r['model'], r['renderer'], r['preference']) for r in rows}
    expected = {(m, r, p) for m in MODELS for r in RENDERERS for p in ('fps', 'ram')}
    if cases != expected or len(rows) != len(expected):
        raise ValueError('The published Sande comparison requires both models, v1/v2 and FPS/RAM')
    for model in MODELS:
        group = [r for r in rows if r['model'] == model]
        if len({r['oracle_sha256'] for r in group}) != 1:
            raise ValueError('Sande A/B source pictures differ')
    for row in rows:
        display, proof = row['display'], row['verification']
        if not all(display[k] for k in ('pixel_match', 'color_match', 'hud_match', 'picture_coverage_complete')):
            raise ValueError('Sande display verification is incomplete')
        if not proof['pixel_match'] or not proof['color_match'] or proof['orientations'] != 192:
            raise ValueError('Sande source verification is incomplete')
        if display['clock_hz'] != CLOCK or display['refreshes'] != report['refreshes']:
            raise ValueError('Sande measurement protocols differ')
        if not math.isclose(display['display_fps'], display['display_flips'] * CLOCK / display['elapsed_cycles']):
            raise ValueError('Sande FPS does not match raw display count and elapsed cycles')
        if row['renderer'] == 'hors-render-v2' and row['preference'] == 'fps':
            crt = root / 'examples/demos_sande' / row['cartridge']
            if sha(crt) != display['sha256']:
                raise ValueError('Sande results do not match the shipped cartridge: ' + crt.name)
    interactive = report.get('interactive', [])
    if report.get('source_colors'):
        if interactive:
            raise ValueError('Source-material report cannot use monochrome interactive carts')
        return
    if {r['model'] for r in interactive} != set(MODELS) or len(interactive) != len(MODELS):
        raise ValueError('Missing Sande interactive idle measurements')
    for row in interactive:
        d = row['display']
        if not d.get('interactive_label_match') or not row['verification'].get('interactive_label_match'):
            raise ValueError('Interactive label verification is missing')
        if d['refreshes'] != report['refreshes'] or not d['picture_coverage_complete']:
            raise ValueError('Interactive measurement window/coverage differs')
        if sha(root / 'examples/demos_sande' / row['cartridge']) != d['sha256']:
            raise ValueError('Interactive report does not match shipped cart')
        baseline = next(r for r in rows if r['model'] == row['model'] and r['renderer'] == 'hors-render-v2' and r['preference'] == 'fps')
        if row['oracle_sha256'] != baseline['oracle_sha256']:
            raise ValueError('Interactive and automatic source pictures differ')
        for ticks in (50, 1):
            cycle = row.get('cycling', {}).get(str(ticks), {})
            if cycle.get('sha256') != d['sha256'] or cycle.get('refreshes') != report['refreshes']:
                raise ValueError('Interactive cycling measurements are missing or stale')
            if not all(cycle.get(k) for k in ('pixel_match', 'color_match', 'hud_match', 'picture_coverage_complete', 'interactive_label_match')):
                raise ValueError('Interactive cycling validation failed')
            if cycle.get('cycle_period_pal_ticks') != ticks or cycle.get('observed_palette_changes', 0) < 10:
                raise ValueError('Interactive cycling was not exercised')


def comparison_section(root, source_colors=False):
    root = Path(root)
    report = json.loads((root / (COLOR_REPORT if source_colors else REPORT)).read_text())
    if bool(report.get('source_colors')) != source_colors:
        raise ValueError('Sande report colour mode differs')
    validate_report(root, report)
    if source_colors:
        lines = ['', '### Standalone material-colour variants', '',
                 'These separate `-color` carts use the original MTL diffuse colours with the same 192 Y-axis orientations, '
                 'visibility and gap-6 encoding recipe as the bw defaults. Pretzel maps to dark grey; TAC-2 retains red, white and greys. '
                 'The measurements use the same PAL display-slot and complete-picture checks as the bw table.', '',
                 '| Model | Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Frame data ROM bytes |',
                 '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |']
        for row in report['results']:
            d = row['display']
            lines.append(f"| {row['title']} | {row['renderer']} | {row['preference']} | {d['high_fps']:.2f} | "
                         f"{d['display_fps']:.2f} | {d['low_fps']:.2f} | {row['crt_bytes']:,} | {row['rom_frame_bytes']:,} |")
        lines += ['', f"Shared colour-test window: {report['refreshes']:,} PAL refresh intervals; high/low are interval extrema, not sustained rates.", '',
                  '[Raw material-colour measurements](benchmarks/sande/summary-color.json)', '',
                  '```bash', 'python tools/run_sande_perfs.py --source-colors --workspace ../c64-sande-color-perfs --vice-data /usr/local/share/vice', '```', '']
        return lines
    lines = ['', "## Sande's Models", '',
             "Models contributed by **Sande**: **Sande's Pretzel** and **Sande's TAC-2 joystick**. "
             'This is a separate workload from the original twelve animations and Demo Cart 2.0.', '',
             'Each standalone cart uses the complete OBJ topology, white-on-black output, 192 Y-axis orientations, '
             'automatic surface visibility, the normal HUD and uncapped playback. V1/V2 and FPS/RAM builds use '
             'identical picture oracles. PAL VICE measures actual display-slot changes after each raster IRQ; '
             'every observed bitmap, colour matrix and Sande HUD is checked. The initial full-loop warmup is excluded.', '',
             '| Model | V / E | Renderer | Preference | High FPS | Average FPS | Low FPS | CRT bytes | Frame data ROM bytes |',
             '| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for row in report['results']:
        d = row['display']
        lines.append(f"| {row['title']} | {row['vertices']} / {row['edges']} | {row['renderer']} | "
                     f"{row['preference']} | {d['high_fps']:.2f} | {d['display_fps']:.2f} | "
                     f"{d['low_fps']:.2f} | {row['crt_bytes']:,} | {row['rom_frame_bytes']:,} |")
    lines += ['', '### Interactive path, no input', '',
              'The separate interactive v2/FPS builds poll the keyboard and both joystick ports once per produced sample. '
              'These rows include the top-right INTERACTIVE label and measure their cost with no control held, '
              'using the same source pictures and observation window. The label is checked separately over the model oracle.', '',
              '| Model | Automatic FPS | Interactive idle FPS | Change |',
              '| --- | ---: | ---: | ---: |']
    for row in report['interactive']:
        base = next(r for r in report['results'] if r['model'] == row['model'] and r['renderer'] == 'hors-render-v2' and r['preference'] == 'fps')
        before, after = base['display']['display_fps'], row['display']['display_fps']
        lines.append(f"| {row['title']} | {before:.2f} | {after:.2f} | {(after / before - 1) * 100:+.2f}% |")
    lines += ['', '### Interactive palette cycling', '',
              'F5 toggles sequential colour changes, alternating foreground and background. F6 slows the rate; F7 speeds it up. '
              'F8 toggles a persistent black border or background-follow mode (the default); Ctrl+F7 selects an independent border colour. F2 flashes white briefly and resets. '
              'Cycling uses the existing PAL tick counter; palette writes run only on a change event. '
              'The fastest setting requests one change per PAL tick but is limited to one event per produced frame.', '',
              '| Model | Cycle setting | High FPS | Average FPS | Low FPS | Change versus interactive idle |',
              '| --- | --- | ---: | ---: | ---: | ---: |']
    for row in report['interactive']:
        for ticks, label in ((50, 'Default: about 1 s per change'), (1, 'Fastest: at most once per produced frame')):
            d = row['cycling'][str(ticks)]
            lines.append(f"| {row['title']} | {label} | {d['high_fps']:.2f} | {d['display_fps']:.2f} | {d['low_fps']:.2f} | "
                         f"{(d['display_fps'] / row['display']['display_fps'] - 1) * 100:+.2f}% |")
    lines += ['', f"All cases use {report['refreshes']:,} PAL refresh intervals per observation window "
              f"(approximately {report['refreshes'] * PAL_CYCLES / CLOCK:.2f} seconds). "
              'Average FPS is displayed frames divided by emulated elapsed time. High/low are interval extrema, '
              'not sustained rates. A difference below one flip per window is within measurement granularity.', '',
              '**V/E are source-mesh totals, not runtime transformations or a count of visible lines drawn each frame.** '
              'Projection and visibility are computed offline; hors-render-v2 draws precomputed bitmap spans. '
              'No mesh simplification or orientation reduction is used. These are emulator measurements, not physical-hardware results.', '',
              '[Sande models, carts and reproduction](../examples/demos_sande/README.md) · '
              '[Raw Sande measurements](benchmarks/sande/summary.json)', '',
              '```bash', 'python tools/run_sande_perfs.py --workspace ../c64-sande-perfs --vice-data /usr/local/share/vice',
              '```', '',
              'The Sande benchmark is also part of `RUN-CHECKS.sh`. Its checked report, source hashes and '
              'shipped cart hashes are verified when this page is generated and by `--check`.']
    return lines


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--tass', default='64tass')
    p.add_argument('--cartconv', default='cartconv')
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', type=Path, default=Path('/usr/local/share/vice'))
    p.add_argument('--seconds', type=float, default=30)
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--capture', action='store_true', help='Also save VICE PNG/GIF previews (requires Pillow)')
    p.add_argument('--source-colors', action='store_true', help='Measure separate material-colour variants instead of the bw set')
    a = p.parse_args()
    work = a.workspace.expanduser().resolve()
    if work.exists():
        p.error('--workspace must be a new directory')
    if not math.isfinite(a.seconds) or a.seconds <= 0 or not 1 <= a.jobs <= 4:
        p.error('--seconds must be positive and finite; --jobs must be 1..4')
    if work == ROOT or ROOT in work.parents:
        p.error('--workspace must be outside the checkout')
    for key in ('tass', 'cartconv', 'vice'):
        tool = shutil.which(str(getattr(a, key)))
        if not tool:
            p.error('Executable not found: ' + str(getattr(a, key)))
        setattr(a, key, str(Path(tool).resolve()))
    work.mkdir(parents=True)
    carts = work / 'carts'
    # The existing verifier also gets clean VICE defaults and JAM detection.
    os.environ['C64_VICE_REAL'] = a.vice
    os.environ['C64_VICE_LOG_DIR'] = str(work / 'vice-logs')
    wrapper = str(ROOT / 'VICE-BATCH.sh') if os.name != 'nt' else a.vice
    tasks = []
    for renderer in RENDERERS:
        for prefer in ('fps', 'ram'):
            results = build(carts, renderer=renderer, prefer=prefer, tass=a.tass, cartconv=a.cartconv, source_colors=a.source_colors)
            tasks.extend((row, renderer, prefer) for row in results)
    interactive_tasks = [] if a.source_colors else [(row, 'hors-render-v2', 'fps') for row in
                         build(carts, interactive=True, tass=a.tass, cartconv=a.cartconv)]
    def check(task):
        row, renderer, prefer = task
        crt = carts / row['cartridge']
        proof = verify(crt, wrapper, a.vice_data, cycles=2,
                       capture=work / 'previews' if a.capture and renderer == 'hors-render-v2' and prefer == 'fps' else None)
        dump(work / (crt.stem + '-verification.json'), proof)
        manifest = json.loads(crt.with_name(crt.stem + '-manifest.json').read_text())
        oracle = ROOT / manifest['runtime_work'] / 'oracle.json'
        return dict(model=row['model'], title=json.loads((SOURCES / 'recipe.json').read_text())['models'][row['model']]['title'],
                    renderer=renderer, preference=prefer, cartridge=crt.name,
                    vertices=manifest['vertices'], edges=manifest['edges'], frames=manifest['frames'],
                    crt_bytes=crt.stat().st_size, rom_frame_bytes=manifest['rom_frame_bytes'],
                    oracle_sha256=sha(oracle), verification=proof,
                    metadata=inspect_easyflash_crt(crt, require_metadata=True))
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        all_rows = list(pool.map(check, tasks + interactive_tasks))
    # Common window across all cases; at least two complete slowest rotations.
    seconds = max(a.seconds, max(2.2 * r['frames'] / r['verification']['average_fps'] for r in all_rows))
    refreshes = math.ceil(seconds * CLOCK / PAL_CYCLES)
    def timed(row):
        crt = carts / row['cartridge']
        manifest = json.loads(crt.with_name(crt.stem + '-manifest.json').read_text())
        row['display'] = measure(crt, ROOT / manifest['runtime_work'] / 'oracle.json', a.vice, a.vice_data, refreshes)
        if manifest.get('interactive_cart'):
            row['cycling'] = {str(ticks): measure(crt, ROOT / manifest['runtime_work'] / 'oracle.json',
                                                a.vice, a.vice_data, refreshes, cycle_ticks=ticks) for ticks in (50, 1)}
        dump(work / (crt.stem + '-display.json'), row['display'])
        print(f"{crt.name}: {row['display']['display_fps']:.3f} display FPS; pixels, colours and HUD PASS", flush=True)
        return row
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        all_rows = list(pool.map(timed, all_rows))
    report = dict(set_id=SET_ID, version=(ROOT / 'VERSION').read_text().strip(), author='Sande',
                  protocol='standalone looping objects; normal uncapped playback; PAL; seed 1; factory defaults; sound off',
                  refreshes=refreshes,
                  source_sha256={p.name: sha(p) for p in sorted(SOURCES.iterdir()) if p.suffix in ('.obj', '.mtl') or p.name == 'recipe.json'},
                  tool_sha256={key: sha(getattr(a, key)) for key in ('tass', 'cartconv', 'vice')},
                  results=all_rows[:len(tasks)], interactive=all_rows[len(tasks):])
    if a.source_colors:
        report['source_colors'] = True
    validate_report(ROOT, report)
    dump(work / ('summary-color.json' if a.source_colors else 'summary.json'), report)
    print('Sande test kit PASS:', work, flush=True)


if __name__ == '__main__':
    main()
