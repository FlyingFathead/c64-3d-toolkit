#!/usr/bin/env python3
"""Verify Dragon carts, measure PAL display cadence, and capture timed GIFs."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from c643d.cartridge import inspect_easyflash_crt
from c643d.font import bitmap_text
from verify_cart_stream import expected_frame, labels, render_ram, verify

CLOCK = 985248
PAL_CYCLES = 19656
REFRESHES = 1504


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def combine_gifs(output, results):
    from PIL import Image
    images, durations, segments = [], [], []
    for name in ('wireframe', 'metallic', 'red', 'green', 'blue'):
        row = next(r for r in results if r['id'] == name)
        path = output / 'previews' / (Path(row['cartridge']).stem + '.gif')
        start = len(images)
        with Image.open(path) as source:
            for i in range(source.n_frames):
                source.seek(i)
                images.append(source.convert('RGB'))
                durations.append(source.info['duration'])
        segments.append(dict(variant=name,first_frame=start,frames=len(images)-start,
                             duration_ms=sum(durations[start:])))
    target = output / 'stanford_dragon-showcase.gif'
    images[0].save(target,save_all=True,append_images=images[1:],duration=durations,
                   loop=0,optimize=False,disposal=1)
    with Image.open(target) as check:
        total = 0
        if check.n_frames != 640:
            raise AssertionError('Showcase must contain five complete 128-picture turns')
        for i in range(check.n_frames):
            check.seek(i)
            total += check.info['duration']
        if total != sum(durations):
            raise AssertionError('Combined GIF changed the measured timing')
    return dict(frames=len(images),duration_ms=total,segments=segments,
                width=640,height=400,source='five individual verified PAL-timed GIFs')


def capture_display(cart, oracle, vice, data, output):
    """Sample actual VIC display buffers once per PAL IRQ after one warmup loop."""
    from PIL import Image
    meta = json.loads(cart.with_name(cart.stem + '-manifest.json').read_text())
    sym = labels(cart.with_suffix('.lbl'))
    frames = json.loads(oracle.read_text())
    known = {hashlib.sha256(b''.join(expected_frame(f, meta['screen_color']))).digest(): i
             for i, f in enumerate(frames)}
    if len(known) != len(frames):
        raise ValueError('This Dragon capture expects distinct orientation pictures')
    hud = bitmap_text(f"{meta['name']} V:{meta['vertices']:03d} E:{meta['edges']:03d}", 31)
    digest = sha(cart)
    transitions, ticks = [], []
    with tempfile.TemporaryDirectory(prefix='dragon-display-') as tmp:
        tmp = Path(tmp)
        from verify_cart_stream import startup_monitor
        startup,go = startup_monitor(meta,sym)
        commands = ['delete', *startup, f'break ${sym["profile_published"]:04x}',
                    go, *(['g'] * (len(frames) + 5)), 'delete',
                    f'break ${sym["irq_no_flip"]:04x}']
        for i in range(REFRESHES + 1):
            commands += ['g', 'stopwatch', 'bank ram',
                         f'bsave "{tmp / f"{i}.ram"}" 0 $0000 $ffff', 'bank cpu',
                         f'bsave "{tmp / f"{i}.io"}" 0 $d000 $dd03']
        (tmp / 'run.mon').write_text('\n'.join(commands + ['quit']) + '\n')
        command = [vice, '-default', '-console', '+easyflashcrtwrite', '+saveres',
                   '-pal', '+sound', '-warp', '-seed', '1', '-jamaction', '5',
                   '-directory', str(data), '-cartcrt', str(cart), '-initbreak', 'reset',
                   '-moncommands', str(tmp / 'run.mon'), '-monlogname', str(tmp / 'monitor.log'), '-monlog', '-limitcycles', '200000000']
        with (tmp / 'vice.txt').open('w') as log:
            proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=240)
        if proc.returncode:
            raise RuntimeError((tmp / 'vice.txt').read_text()[-2500:])
        ticks = [int(t) for t in re.findall(r'Stopwatch:\s*(\d+)', (tmp / 'monitor.log').read_text())]
        if len(ticks) != REFRESHES + 1:
            raise AssertionError('VICE did not complete the PAL observation window')
        seen, slots, previous = set(), set(), None
        for i in range(REFRESHES + 1):
            ram, io = (tmp / f'{i}.ram').read_bytes(), (tmp / f'{i}.io').read_bytes()
            slot = ram[sym['display_slot']]
            if slot not in (0, 1, 2):
                raise AssertionError('Invalid display slot')
            baddr, saddr = (0x2000, 0x6000, 0xe000)[slot], (0x400, 0x4400, 0xc800)[slot]
            picture = hashlib.sha256(ram[baddr:baddr+7680] + ram[saddr:saddr+960]).digest()
            if picture not in known or ram[baddr+7680:baddr+7680+len(hud)] != hud:
                raise AssertionError('Displayed Dragon picture or HUD differs from the oracle')
            if io[0xd00] & 3 != (3, 2, 0)[slot] or io[0x18] & 0xfe != (0x18, 0x18, 0x28)[slot]:
                raise AssertionError('VIC bank does not match the displayed buffer')
            if io[0x20] & 15 != 0 or io[0x21] & 15 != 0:
                raise AssertionError('Expected black border/background')
            seen.add(picture)
            slots.add(slot)
            if slot != previous:
                transitions.append((i, known[picture], render_ram(ram, slot)))
            previous = slot
    if seen != set(known) or slots != {0, 1, 2} or sha(cart) != digest:
        raise AssertionError('Incomplete display coverage or changed cartridge')
    elapsed = ticks[-1] - ticks[0]
    if abs(elapsed - REFRESHES * PAL_CYCLES) > PAL_CYCLES:
        raise AssertionError('PAL observation window has an unexpected duration')
    holds = [b[0]-a[0] for a, b in zip(transitions[1:], transitions[2:])]
    # Use a complete steady-state turn from orientation 0 to the following 0.
    zeros = [i for i, item in enumerate(transitions) if item[1] == 0]
    if len(zeros) < 2:
        raise AssertionError('Not enough displayed frames for a complete GIF loop')
    start, end = zeros[:2]
    loop = transitions[start:end]
    if [item[1] for item in loop] != list(range(len(frames))):
        raise AssertionError('GIF would skip or reorder a Dragon orientation')
    loop_holds = [transitions[i+1][0]-transitions[i][0] for i in range(start, end)]
    # Cumulative centisecond rounding avoids slowing down 30 ms/50 ms frames.
    boundaries = [0]
    total_ticks = 0
    for hold in loop_holds:
        total_ticks += hold
        boundaries.append(round(total_ticks * PAL_CYCLES / CLOCK * 100))
    durations = [(b-a)*10 for a, b in zip(boundaries, boundaries[1:])]
    if min(durations) < 20:
        raise AssertionError('GIF delay would trigger browser minimum-delay clamping')
    images = [item[2].resize((640, 400), Image.Resampling.NEAREST) for item in loop]
    output.mkdir(parents=True, exist_ok=True)
    gif = output / (cart.stem + '.gif')
    images[0].save(gif, save_all=True, append_images=images[1:], duration=durations,
                   loop=0, optimize=False, disposal=1)
    images[0].save(output / (cart.stem + '.png'))
    with Image.open(gif) as check:
        decoded_ms = 0
        for i in range(check.n_frames):
            check.seek(i)
            decoded_ms += check.info['duration']
        if check.n_frames != len(frames) or decoded_ms != sum(durations):
            raise AssertionError('Encoded GIF changed its frame count or duration')
    display = dict(sha256=digest, clock_hz=CLOCK, pal_cycles_per_refresh=PAL_CYCLES,
                   refreshes=REFRESHES, warmup_pictures=len(frames)+6,
                   elapsed_cycles=elapsed, display_flips=len(transitions)-1,
                   display_fps=(len(transitions)-1)*CLOCK/elapsed,
                   fastest_display_fps=CLOCK/(min(holds)*PAL_CYCLES),
                   slowest_display_fps=CLOCK/(max(holds)*PAL_CYCLES),
                   worst_display_ms=max(holds)*PAL_CYCLES/CLOCK*1000,
                   hold_ticks=dict(Counter(holds)), orientations_seen=len(seen),
                   pixel_match=True, color_match=True, hud_match=True, border_match=True,
                   all_three_buffers=True, cartridge_unchanged=True)
    timing = dict(frames=len(images), displayed_orientation_indices=[x[1] for x in loop],
                  pal_hold_ticks=loop_holds, gif_durations_ms=durations,
                  measured_loop_seconds=sum(loop_holds)*PAL_CYCLES/CLOCK,
                  gif_loop_seconds=sum(durations)/1000, width=640, height=400,
                  source='VICE actual display buffers; steady-state PAL refresh cadence')
    dump(output / (cart.stem + '-timing.json'), timing)
    return display, timing


def update_readme(results,showcase):
    from performance_tables import highlight_fps
    lines=['## Performance','',
        'PAL VICE 3.10, stock timing: 985,248 cycles/s and 19,656 cycles/refresh. Each cart uses 128 orientations and a 1,504-refresh observation window after warmup. Display FPS counts actual buffer flips. Bold marks the highest rate in each column; ties use the shown precision. These different surface appearances are not identical-picture optimization candidates.','',
        '| Surface | Average displayed FPS | High FPS | Low FPS | Longest hold (ms) | Frame ROM bytes | CRT bytes |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in results:
        d=row['display']
        lines.append(f"| {row['id']} | {d['display_fps']:.2f} | {d['fastest_display_fps']:.2f} | {d['slowest_display_fps']:.2f} | {d['worst_display_ms']:.2f} | {row['rom_frame_bytes']:,} | {row['crt_bytes']:,} |")
    lines+=['',f"All {len(results)} carts retain the complete source mesh. Each has an 896-byte frame directory, 8,192-byte staging buffer and 3,072-byte metadata cache, in addition to graphics, code and other state. The original five-way showcase remains {showcase['frames']} pictures and {showcase['duration_ms']/1000:.2f} seconds; the golden GIF is separate.", '',
        'The high/low rates describe individual display holds, not sustained throughput. GIF delays follow the actual PAL display sequence with cumulative centisecond rounding. All these carts start automatically and loop.','']
    path=HERE/'README.md';text=path.read_text();a=text.index('## Performance');b=text.index('## Validation',a)
    text=text[:a]+'\n'.join(highlight_fps(lines))+'\n'+text[b:]
    text=text.replace('Five standalone EasyFlash demos','Six standalone EasyFlash demos').replace('wireframe and the metallic (grey), red, green and blue shaded surfaces.', 'wireframe and metallic (grey), golden, red, green and blue shaded surfaces.')
    text=re.sub(r'259 completed pictures checked per cart:[^\n]+',f"259 completed pictures checked per cart: two full turns plus three buffer-reuse samples, **{sum(r['verification']['verified_frames'] for r in results):,} total**.",text)
    path.write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Run VICE, save fresh evidence and GIFs')
    parser.add_argument('--check', action='store_true', help='Check shipped files and saved evidence (default)')
    parser.add_argument('--vice', default='x64sc')
    parser.add_argument('--vice-data', type=Path)
    parser.add_argument('--cartridge-dir', type=Path, default=HERE / 'cartridges')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/stanford-dragon-verification')
    parser.add_argument('--install', action='store_true', help='Install fresh evidence/GIFs after all checks pass')
    args = parser.parse_args()
    if not args.run:
        record = json.loads((HERE / 'validation.json').read_text())
        for name, digest in record['sha256'].items():
            if sha(ROOT / name) != digest:
                raise SystemExit('Dragon evidence is stale: ' + name)
        for row in record['results']:
            inspect_easyflash_crt(HERE / 'cartridges' / row['cartridge'], require_metadata=True)
            assert row['verification']['pixel_match'] and row['verification']['color_match']
            assert row['display']['orientations_seen'] == 128 and row['display']['cartridge_unchanged']
            assert abs(row['gif']['gif_loop_seconds']-row['gif']['measured_loop_seconds']) < 0.01
        print(f"All {len(record['results'])} Stanford Dragon HORS-V3 carts, source, GIFs and saved PAL evidence match.")
        return
    if not args.vice_data:
        parser.error('--run requires --vice-data')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for row in json.loads((HERE / 'recipe.json').read_text())['variants']:
        cart = args.cartridge_dir.resolve() / (row['stem'] + '.crt')
        meta = json.loads(cart.with_name(cart.stem + '-manifest.json').read_text())
        if meta['renderer'] != 'hors-renderer-v3' or meta['frames'] != 128:
            raise AssertionError('Expected a 128-orientation HORS-V3 cartridge')
        container = inspect_easyflash_crt(cart, require_metadata=True)
        identity = sha(cart)
        with tempfile.TemporaryDirectory(prefix='dragon-oracle-') as tmp:
            oracle = Path(tmp) / 'oracle.json'
            oracle.write_bytes(gzip.decompress(cart.with_name(cart.stem + '-oracle.json.gz').read_bytes()))
            proof = verify(cart, args.vice, str(args.vice_data.resolve()), 2, oracle_path=oracle)
            display, timing = capture_display(cart, oracle, args.vice, args.vice_data.resolve(), output / 'previews')
        if sha(cart) != identity:
            raise AssertionError('VICE modified the cartridge')
        result = dict(id=row['id'], cartridge=cart.name, renderer=meta['renderer'],
                      vertices=meta['vertices'], edges=meta['edges'], triangles=meta['faces'],
                      frames=meta['frames'], crt_bytes=cart.stat().st_size,
                      rom_frame_bytes=meta['rom_frame_bytes'], highest_bank=meta['highest_bank'],
                      directory_ram_bytes=meta['directory_ram_bytes'],
                      frame_buffer_bytes=meta['frame_buffer_bytes'],
                      metadata_cache_bytes=meta['metadata_cache_bytes'],
                      container=container, verification=proof, display=display, gif=timing)
        dump(output / (row['id'] + '.json'), result)
        results.append(result)
        print(f"{row['id']}: {display['display_fps']:.2f} displayed FPS; {proof['verified_frames']} pictures checked; GIF {timing['gif_loop_seconds']:.2f}s", flush=True)
    showcase = combine_gifs(output, results)
    dump(output / 'results.json', dict(results=results, showcase=showcase,
         pal_vice=True, physical_hardware_tested=False))
    if args.install:
        if args.cartridge_dir.resolve() != (HERE / 'cartridges').resolve():
            parser.error('--install requires verification of the shipped cartridges')
        update_readme(results,showcase)
        shutil.copytree(output / 'previews', HERE / 'previews', dirs_exist_ok=True)
        shutil.copy2(output / 'stanford_dragon-showcase.gif', HERE / 'stanford_dragon-showcase.gif')
        (HERE / 'evidence').mkdir(exist_ok=True)
        for name in [r['id'] + '.json' for r in results] + ['results.json']:
            shutil.copy2(output / name, HERE / 'evidence' / name)
        files = [ROOT / 'VERSION']
        files += [p for p in HERE.rglob('*') if p.is_file() and p.suffix not in ('.md', '.pyc')
                  and p.name != 'validation.json' and '__pycache__' not in p.parts]
        for folder in ('tools', 'c64'):
            files += [p for p in (ROOT / folder).rglob('*') if p.is_file()
                      and p.suffix not in ('.md', '.pyc') and '__pycache__' not in p.parts]
        dump(HERE / 'validation.json', dict(toolkit_version=(ROOT / 'VERSION').read_text().strip(),
             results=results, showcase=showcase, pal_vice=True, physical_hardware_tested=False,
             sha256={p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(files))}))


if __name__ == '__main__':
    main()
