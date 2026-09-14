#!/usr/bin/env python3
"""PAL VICE: timed PLAY ALL across every demo, wrap, skip, exit, manual launch.

ONLY use normal PLAY ALL for A/B comparisons between rendering methods and versions.
The optional F5 internal demo mode is exhibition-only, NOT a benchmark.
Uses the production menu/control handlers through the monitor. This verifies
C64 execution and keyboard handlers, not the host's Escape key mapping.
"""
import argparse
import hashlib
import json
from pathlib import Path
from c643d.cartpaths import menu_manifest_path
import re
import subprocess
import tempfile
from verify_cart_stream import labels


def verify(crt, vice, vice_data, *, exhibition=False):
    root = Path(__file__).resolve().parents[1]
    crt = Path(crt).resolve()
    meta = json.loads(menu_manifest_path(crt).read_text())
    seconds = meta['play_all']['seconds']
    count = len(meta['entries'])
    durations = meta['exhibition']['entry_seconds'] if exhibition else [seconds]*count
    work = root / 'build' / (crt.stem + '-cartridge-demo')
    menu = labels(work / (crt.stem + '-runtime-' + meta['menu_style'] + '.lbl'))
    control = labels(work / (crt.stem + '-control.lbl'))
    with tempfile.TemporaryDirectory(prefix='c643d-play-all-') as temp:
        out = Path(temp)
        commands = []
        def stop(address, start=None):
            commands.extend(['delete', f'break ${address:04x}',
                             'g' if start is None else f'g ${start:04x}'])
        def dump(name):
            commands.extend(['bank ram', f'bsave "{out / (name + ".ram")}" 0 $0000 $ffff'])
        if meta.get('build_screen', {}).get('wait_for_space'):
            stop(menu['build_screen_visible'])
            stop(menu['menu_wait_key'], menu['build_screen_done'])
        else:
            stop(menu['menu_wait_key'])
        dump('cold')
        if exhibition:
            # Inject the F5 matrix sample after the CIA read, then execute the
            # real scanner, menu dispatch and key-release path. No ROM patch.
            stop(menu['scan_menu_row_read'])
            commands.append('r a=$bf')
            stop(menu['menu_exhibition'])
        for index in range(count + 1):
            stop(menu['play_all_count'], menu['menu_launch'] if index == 0 and not exhibition else None)
            dump(f'{index}-start')
            commands.append('stopwatch')
            stop(control['cart_control_auto_next'])
            dump(f'{index}-end')
            commands.append('stopwatch')
        # Finish the automatic wrap, then exercise the SPACE handler mid-demo.
        stop(menu['play_all_count'])
        commands.append('> $02fb $00')
        stop(0x080d, control['control_next_key'])
        dump('skip-loaded')
        stop(menu['play_all_count'])
        dump('skip-running')
        # RUN/STOP/F1 handler stops autoplay and returns to the same selection.
        commands.append('> $02fb $00')
        stop(menu['menu_wait_key'], control['control_menu_key'])
        dump('returned')
        # Manually launched demos remain manual, even after PLAY ALL was used.
        commands.append(f'> ${menu["selected_entry"]:04x} $05')
        sym = labels(root / meta['streamed_entries'][5]['work'] / 'runtime.lbl')
        stop(sym['frame_draw_complete'], menu['menu_launch'])
        dump('manual')
        if exhibition:
            # A normal PLAY ALL launch after exiting must not inherit F5.
            stop(menu['menu_wait_key'], control['control_menu_key'])
            commands.append(f'> ${menu["selected_entry"]:04x} $ff')
            stop(menu['play_all_count'], menu['menu_launch'])
            dump('normal-restarted')
        commands.append('quit')
        (out / 'run.mon').write_text('\n'.join(commands) + '\n')
        cmd = [vice, '-console', '+easyflashcrtwrite', '-pal', '+sound', '-warp', '-seed', '1',
               '-jamaction', '2', '-directory', str(vice_data), '-cartcrt', str(crt),
               '-initbreak', 'reset', '-moncommands', str(out / 'run.mon'),
               '-monlogname', str(out / 'monitor.log'), '-monlog',
               '-limitcycles', str((count + 2) * (seconds + 3) * 1000000)]
        with (out / 'vice.log').open('w') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        ticks = [int(t) for t in re.findall(r'Stopwatch:\s*(\d+)', (out / 'monitor.log').read_text())]
        assert len(ticks) == 2 * (count + 1), (out / 'monitor.log').read_text()[-2000:]
        cold = (out / 'cold.ram').read_bytes()
        assert cold[menu['selected_entry']] == 255 and cold[0x02fd] == 0
        samples = []
        for index in range(count + 1):
            before = (out / f'{index}-start.ram').read_bytes()
            after = (out / f'{index}-end.ram').read_bytes()
            assert before[0x02fa] == after[0x02fa] == index % count
            assert before[0x02fd:0x0300] == bytes((2, 50, durations[index % count]))
            assert after[0x02fd:0x0300] == bytes((2, 50, 0))
            elapsed = ticks[2*index+1] - ticks[2*index]
            # First timer-count breakpoint is one raster after arming. The
            # final branch adds a handful of cycles to the last raster tick.
            expected = (durations[index % count] * 50 - 1) * 19656
            # Copy bursts can delay an IRQ by up to one bounded page copy.
            assert abs(elapsed - expected) < 4096, (index, elapsed, expected)
            samples.append(dict(entry=index % count, seconds=durations[index % count], count_interval_cycles=elapsed))
        skipped = (out / 'skip-loaded.ram').read_bytes()
        assert skipped[0x02fa] == 2 and skipped[0x02fd] == 1
        assert skipped[0x02fb] == 1, 'held SPACE must wait for release'
        assert (out / 'skip-running.ram').read_bytes()[0x02fd] == 2
        returned = (out / 'returned.ram').read_bytes()
        assert returned[0x02fd] == 0 and returned[menu['selected_entry']] == 2
        manual = (out / 'manual.ram').read_bytes()
        assert manual[0x02fa] == 5 and manual[0x02fd] == 0
        if 'exhibition' in meta:
            assert cold[0x02f7] == returned[0x02f7] == manual[0x02f7] == 0
            if exhibition:
                for index in range(count+1):
                    assert (out / f'{index}-start.ram').read_bytes()[0x02f7] == 1
                normal = (out/'normal-restarted.ram').read_bytes()
                assert normal[0x02f7] == 0 and normal[0x02ff] == seconds
    return dict(cartridge=crt.name, sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
                mode='internal-demo-F5' if exhibition else 'normal-play-all',
                menu_style=meta['menu_style'], entry_seconds=durations, seconds_per_demo=seconds, ticks_per_demo=50*seconds, all_entries=True,
                last_to_first_wrap=True, first_picture_before_timer=True,
                space_skips=True, held_space_latched=True, runstop_returns=True,
                manual_launch_disables_timer=True, samples=samples,
                method=('PAL VICE; injected F5 CIA row sample, real scanner/dispatch and production handlers; no host key injection.' if exhibition else 'PAL VICE; production handlers via monitor, no host key injection.'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('crt', type=Path)
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', type=Path, required=True)
    p.add_argument('--report', type=Path)
    p.add_argument('--exhibition', action='store_true', help='verify F5 internal demo mode (not a benchmark)')
    a = p.parse_args()
    result = verify(a.crt, a.vice, a.vice_data, exhibition=a.exhibition)
    text = json.dumps(result, indent=2) + '\n'
    print(text)
    if a.report:
        a.report.write_text(text)
