#!/usr/bin/env python3
"""Compare matched looping EasyFlash builds with PAL VICE and pixel oracles.

Keep private scenes and the output directory outside the checkout. This tool
reports regressions; it never substitutes a host estimate for a measurement.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import tempfile

from profile_cart_stream import profile, CLOCK
from verify_cart_stream import verify, labels, startup_monitor, expected_frame, apply_interactive_overlay, readonly_cartridge_flags

ROOT = Path(__file__).resolve().parents[1]


def load_case(crt, root):
    crt = Path(crt).resolve()
    meta = json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    if meta.get('ending') or meta.get('reel'):
        raise ValueError('Comparison currently requires standalone looping builds')
    if int.from_bytes(crt.read_bytes()[22:24], 'big') != 32:
        raise ValueError('Comparison currently measures EasyFlash CRTs')
    work = Path(root).resolve() / meta['runtime_work']
    oracle = work / 'oracle.json'
    frames = json.loads(oracle.read_text())
    if len(frames) != meta['frames'] or not frames:
        raise ValueError('Oracle frame count differs from the manifest')
    digest = hashlib.sha256()
    for frame in frames:
        bitmap, colors = expected_frame(frame, meta['screen_color'])
        digest.update(apply_interactive_overlay(bitmap, meta))
        digest.update(colors)
    return dict(crt=crt, meta=meta, work=work, oracle=oracle,
                pictures_sha256=digest.hexdigest())


def require_matched(a, b):
    if a['pictures_sha256'] != b['pictures_sha256']:
        raise ValueError('A/B picture bytes, colours or sample order differ')
    for key in ('frames', 'frame_ticks', 'screen_color', 'border_color', 'hud_text',
                'text_overlay', 'interactive_cart', 'background_effect', 'hud_visibility'):
        if a['meta'].get(key) != b['meta'].get(key):
            raise ValueError('A/B playback settings differ: '+key)


def measure_display(case, vice, data=None):
    """Count the actual display-slot store in the raster IRQ, over two loops."""
    crt, meta = case['crt'], case['meta']
    sym = labels(crt.with_suffix('.lbl'))
    prg = (case['work']/'runtime.prg').read_bytes()
    load, code = int.from_bytes(prg[:2], 'little'), prg[2:]
    operand = sym['display_slot']
    opcode = bytes([0x86, operand]) if operand < 256 else bytes([0x8e, operand & 255, operand >> 8])
    start, end = sym['raster_irq']-load, sym['irq_no_flip']-load
    region = code[start:end]
    if not 0 <= start < end <= len(code) or region.count(opcode) != 1:
        raise ValueError('Cannot identify the unique display publication store')
    flip = load + start + region.index(opcode)
    warm, count = meta['frames'], 2*meta['frames']
    startup, go = startup_monitor(meta, sym)
    commands = ['delete', *startup, f'break ${flip:04x}', go]
    commands += ['g']*(warm-1)
    for _ in range(count+1):
        commands += ['g', 'stopwatch']
    commands += ['quit']
    with tempfile.TemporaryDirectory(prefix='c643d-display-') as directory:
        tmp = Path(directory)
        (tmp/'run.mon').write_text('\n'.join(commands)+'\n')
        cmd = [str(vice), '-console', '-default', '+sound', '-pal', '-warp', '-seed', '1',
               '+easyflashcrtwrite', '-cartcrt', str(crt), '-initbreak', 'reset',
               '-moncommands', str(tmp/'run.mon'), '-monlogname', str(tmp/'monitor.log'),
               '-monlog', '-limitcycles', str((warm+count)*1000000+40000000)]
        cmd += readonly_cartridge_flags(crt)
        if data:
            cmd += ['-directory', str(data)]
        with (tmp/'vice.log').open('w') as output:
            subprocess.run(cmd, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=240)
        ticks = [int(v) for v in re.findall(r'Stopwatch:\s*(\d+)', (tmp/'monitor.log').read_text())]
    if len(ticks) != count+1:
        raise RuntimeError('VICE did not reach every display flip')
    intervals = [b-a for a, b in zip(ticks, ticks[1:])]
    if min(intervals) <= 0:
        raise RuntimeError('Invalid display interval')
    return dict(displayed_fps=count*CLOCK/(ticks[-1]-ticks[0]),
        high_fps=CLOCK/min(intervals), low_fps=CLOCK/max(intervals),
        mean_ms=statistics.mean(intervals)*1000/CLOCK,
        worst_ms=max(intervals)*1000/CLOCK,
        p95_ms=sorted(intervals)[int(count*.95)-1]*1000/CLOCK,
        warmup_pictures=warm, intervals=count, cycles=intervals, clock_hz=CLOCK,
        method='actual display_slot stores in raster IRQ; one warmup loop, two measured loops')


def compare(baseline, candidate, *, vice, data, out, capture=False, tolerance_percent=0.5):
    require_matched(baseline, candidate)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = dict(format='c643d-stream-comparison-v1', pictures_identical=True,
        pictures_sha256=baseline['pictures_sha256'], tolerance_percent=tolerance_percent,
        scope='PAL VICE; standalone default forward playback; physical hardware/NTSC unmeasured')
    version = subprocess.run([str(vice), '--version'], text=True, capture_output=True,
                             check=True, timeout=30)
    report['vice_version'] = (version.stdout or version.stderr).strip()
    for name, case in [('baseline', baseline), ('candidate', candidate)]:
        dest = out/name
        dest.mkdir()
        crt = case['crt']
        digest = hashlib.sha256(crt.read_bytes()).hexdigest()
        result = dict(cartridge=crt.name, sha256=digest, crt_bytes=crt.stat().st_size,
            renderer=case['meta']['renderer'], profile=profile(crt, vice, data),
            pixels=verify(crt, vice, data, cycles=2, oracle_path=case['oracle'],
                          capture=dest/'previews' if capture else None),
            display=measure_display(case, vice, data))
        if hashlib.sha256(crt.read_bytes()).hexdigest() != digest:
            raise AssertionError('Measurement modified the cartridge')
        for key in ('profile', 'pixels', 'display'):
            (dest/(key+'.json')).write_text(json.dumps(result[key], indent=2)+'\n')
        report[name] = result
        print(f'{name}: {result["display"]["displayed_fps"]:.5f} displayed FPS; pixels passed', flush=True)
    a, b = report['baseline'], report['candidate']
    change = 100*(b['display']['displayed_fps']/a['display']['displayed_fps']-1)
    worst = 100*(b['display']['worst_ms']/a['display']['worst_ms']-1)
    render = 100*(b['profile']['mean_render_cycles']/a['profile']['mean_render_cycles']-1)
    worst_render = 100*(b['profile']['worst_render_cycles']/a['profile']['worst_render_cycles']-1)
    report['change_percent'] = dict(displayed_fps=change, worst_display_hold=worst,
        mean_render_cycles=render, worst_render_cycles=worst_render)
    report['performance_gate_passed'] = (change >= -tolerance_percent and
        max(worst, render, worst_render) <= tolerance_percent)
    report['gate_note'] = 'Gate covers aggregate mean/worst metrics, not every individual frame or other workloads.'
    (out/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    rows = ['# Matched renderer comparison', '',
        '| Build | High FPS | Average FPS | Low FPS | Worst hold (ms) | Mean render cycles | Worst render cycles | CRT bytes |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name, r in [('Baseline', a), ('Candidate', b)]:
        d, p = r['display'], r['profile']
        rows.append(f'| {name} | {d["high_fps"]:.3f} | {d["displayed_fps"]:.3f} | {d["low_fps"]:.3f} | {d["worst_ms"]:.3f} | {p["mean_render_cycles"]:.2f} | {p["worst_render_cycles"]} | {r["crt_bytes"]} |')
    rows += ['', f'Displayed FPS change: {change:+.3f}%. Aggregate gate: {"PASS" if report["performance_gate_passed"] else "FAIL"} (tolerance {tolerance_percent:g}%).',
        '', 'Both builds passed the same picture, colour and HUD oracle over two loops and all three buffers.',
        'GIFs, when requested, show completed VICE pictures with approximate timing. FPS comes from actual display flips.',
        'High/low FPS are reciprocals of the shortest/longest observed display holds, not sustained rates.',
        report['gate_note'], report['scope'], '']
    (out/'comparison.md').write_text('\n'.join(rows))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--baseline-root', type=Path, default=ROOT)
    parser.add_argument('--candidate-root', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, required=True, help='new evidence directory')
    parser.add_argument('--vice', default='x64sc')
    parser.add_argument('--vice-data')
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--tolerance-percent', type=float, default=0.5)
    args = parser.parse_args()
    if not 0 <= args.tolerance_percent <= 100:
        parser.error('--tolerance-percent must be between 0 and 100')
    result = compare(load_case(args.baseline, args.baseline_root),
        load_case(args.candidate, args.candidate_root), vice=args.vice, data=args.vice_data,
        out=args.out, capture=args.capture, tolerance_percent=args.tolerance_percent)
    return 0 if result['performance_gate_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
