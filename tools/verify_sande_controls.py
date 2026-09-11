#!/usr/bin/env python3
"""Verify reverse traversal, both joystick/shift paths and Sande palette controls."""
import argparse
import json
from pathlib import Path
import tempfile

from build_sande_examples import ROOT, SOURCES, MODELS, sha
from verify_cart_stream import labels, expected_frame, apply_interactive_overlay
from verify_color_combos import run_monitor


def reverse_check(crt, vice, data):
    meta = json.loads(crt.with_name(crt.stem + '-manifest.json').read_text())
    assert meta.get('interactive_overlay'), 'Interactive HUD label is missing'
    sym = labels(crt.with_suffix('.lbl'))
    frames = json.loads((ROOT / meta['runtime_work'] / 'oracle.json').read_text())
    directions = [1] * 12 + [-1] * 207 + [1] * 207 + [-1, 1] * 12
    expected, index = [], 0
    with tempfile.TemporaryDirectory(prefix='sande-reverse-') as tmp:
        tmp = Path(tmp)
        commands = []
        for i, direction in enumerate(directions):
            commands += ['delete', f'break ${sym["frame_begin"]:04x}', 'g',
                         f'> ${sym["sande_step"]:04x} ${direction & 255:02x}',
                         'delete', f'break ${sym["frame_draw_complete"]:04x}', 'g',
                         'bank ram', f'bsave "{tmp / f"{i}.ram"}" 0 $0000 $ffff']
            expected.append(index)
            index = (index + direction) % len(frames)
        run_monitor(crt, vice, data, tmp, commands, len(directions) * 1000000 + 2000000)
        for i, index in enumerate(expected):
            ram = (tmp / f'{i}.ram').read_bytes()
            if ram[sym['frame_index']] != index:
                raise AssertionError(('reverse index mismatch', i, index, ram[sym['frame_index']]))
            slot = ram[sym['render_slot']]
            bitmap, colors = expected_frame(frames[index], meta['screen_color'])
            apply_interactive_overlay(bitmap, meta)
            baddr, saddr = (0x2000, 0x6000, 0xe000)[slot], (0x400, 0x4400, 0xc800)[slot]
            if ram[baddr:baddr + 7680] != bitmap or ram[saddr:saddr + 960] != colors:
                raise AssertionError(('reverse buffer mismatch', i, index, slot))
    return dict(verified_frames=len(directions), all_orientations=set(expected) == set(range(len(frames))),
                forward_reverse_wrap=True, repeated_direction_changes=True, pixel_match=True, color_match=True,
                interactive_label_match=bool(meta.get('interactive_overlay')))


def key_check(crt, vice, data):
    sym = labels(crt.with_suffix('.lbl'))
    checks = []
    state = dict(screen=0x10, border=0, sande_step=1, sande_cycle_enabled=0,
                 sande_cycle_rate=2, sande_border_follow=1)
    flash_pairs = []
    with tempfile.TemporaryDirectory(prefix='sande-keys-') as tmp:
        tmp = Path(tmp)
        commands = []
        def stop(label):
            commands.extend(['delete', f'break ${sym[label]:04x}', 'g'])
        def sample(label, value):
            stop(label)
            commands.append(f'r a=${value:02x}')
        def dump():
            name = str(len(checks))
            commands.extend(['bank ram', f'bsave "{tmp / name}.ram" 0 $0000 $ffff',
                             'bank cpu', f'bsave "{tmp / name}.vic" 0 $d020 $d021', 'bank ram'])
            checks.append((name, dict(state)))
            return name
        def shift(down, right=False):
            sample('demo_color_left_shift_read', 0x7f if down and not right else 0xff)
            if not down or right:
                sample('demo_color_right_shift_read', 0xef if down else 0xff)
        stop('frame_draw_complete')
        dump()
        def press(kind, right_shift=False):
            row = dict(fg=0xdf, bg=0xdf, faster=0xf7, border=0xf7,
                       toggle=0xbf, slower=0xbf, reset=0xef, f1=0xef, custom=0xf7)[kind]
            sample('sande_row0_read', row)
            if kind in ('fg', 'bg', 'faster', 'border', 'custom'):
                sample('demo_color_row_read', row)
            shift(kind in ('bg', 'slower', 'border', 'reset'), right_shift)
            if kind in ('faster', 'custom'):
                sample('sande_ctrl_read', 0xfb if kind == 'custom' else 0xff)
            if kind == 'fg':
                state['screen'] = (state['screen'] + 16) & 255
            elif kind == 'bg':
                state['screen'] = (state['screen'] & 240) | ((state['screen'] + 1) & 15)
                if state['sande_border_follow'] == 1:state['border'] = state['screen'] & 15
                elif state['sande_border_follow'] == 0:state['border'] = 0
            elif kind == 'border':
                state['sande_border_follow'] = 0 if state['sande_border_follow'] == 1 else 1
                if state['sande_border_follow'] == 1:state['border'] = state['screen'] & 15
                elif state['sande_border_follow'] == 0:state['border'] = 0
            elif kind == 'custom':
                state['sande_border_follow'] = 2
                state['border'] = (state['border'] + 1) & 15
            elif kind == 'toggle':
                state['sande_cycle_enabled'] ^= 1
            elif kind == 'slower':
                state['sande_cycle_rate'] = max(0, state['sande_cycle_rate'] - 1)
            elif kind == 'faster':
                state['sande_cycle_rate'] = min(7, state['sande_cycle_rate'] + 1)
            elif kind == 'reset':
                stop('sande_flash_visible')
                state.update(screen=0x11, border=1)
                flash_start = dump()
                state.update(screen=0x10, border=0, sande_cycle_enabled=0,
                             sande_cycle_rate=2, sande_border_follow=1)
            stop('sande_done')
            name = dump()
            if kind == 'reset':
                flash_pairs.append((flash_start, name))
            # A held key has one effect; release re-arms the next press.
            sample('sande_row0_read', row)
            stop('sande_done')
            dump()
            sample('sande_row0_read', 0xff)
            stop('sande_done')
        for kind in ('fg', 'bg'):
            for i in range(16):
                press(kind, right_shift=bool(i % 2))
        for kind in ('bg', 'border', 'fg', 'bg', 'border', 'reset', 'f1'):
            press(kind)
        for i in range(16):press('custom', right_shift=bool(i % 2))
        for kind in ('fg', 'bg', 'custom', 'bg', 'border', 'border', 'bg', 'reset'):
            press(kind)
        for kind in ('faster', 'slower'):
            for i in range(10):
                press(kind, right_shift=bool(i % 2))
        press('reset', right_shift=True)
        press('toggle')
        press('toggle')
        press('toggle')
        press('reset')
        for left, right_shift in ((True, False), (False, False), (True, True)):
            sample('sande_row0_read', 0xfb)
            shift(left, right_shift)
            state['sande_step'] = 255 if left else 1
            stop('sande_done')
            dump()
            sample('sande_row0_read', 0xff)
            stop('sande_done')
            dump()
        for port in ('sande_joy2_read', 'sande_joy1_read'):
            for value in (0xfb, 0xf7, 0xf3):
                sample(port, value)
                if value != 0xf3:
                    state['sande_step'] = 255 if value == 0xfb else 1
                stop('sande_done')
                dump()
        run_monitor(crt, vice, data, tmp, commands, 150000000)
        for name, expected in checks:
            ram = (tmp / (name + '.ram')).read_bytes()
            vic = (tmp / (name + '.vic')).read_bytes()
            color = expected['screen']
            if vic[0] & 15 != expected['border'] or vic[1] & 15 != color & 15:
                raise AssertionError(('VIC colours', name, vic.hex(), expected))
            for base in (0x400, 0x4400, 0xc800):
                if ram[base:base + 1024] != bytes([color]) * 1024:
                    raise AssertionError(('palette buffer', name, base))
            for key in ('sande_step', 'sande_cycle_enabled', 'sande_cycle_rate', 'sande_border_follow'):
                if ram[sym[key]] != expected[key]:
                    raise AssertionError((key, name, ram[sym[key]], expected[key]))
        for first, last in flash_pairs:
            a, b = ((tmp / (name + '.ram')).read_bytes() for name in (first, last))
            assert 5 <= (b[sym['tick_counter']] - a[sym['tick_counter']]) % 256 <= 7
    return dict(checks=len(checks), palette_wrap=True, f8_black_or_follow=True,
                f4_links_background_and_border=True, f3_preserves_border=True, ctrl_f7_custom_border=True,
                f5_toggle=True, f6_f7_rate_limits=True, f2_white_flash=True,
                key_debounce=True, reset_defaults=True, both_shift_keys=True,
                both_joystick_ports=True, opposing_directions_ignored=True,
                input_method='VICE monitor injects CIA read results at labelled scan boundaries; host key mappings and physical controllers are not tested')


def cycle_check(crt, vice, data):
    sym = labels(crt.with_suffix('.lbl'))
    results = []
    for interval, follow in ((200, 1), (50, 1), (1, 1), (1, 0), (1, 2)):
        with tempfile.TemporaryDirectory(prefix='sande-cycle-') as tmp:
            tmp = Path(tmp)
            commands = ['delete', f'break ${sym["frame_begin"]:04x}', 'g',
                        f'> ${sym["sande_cycle_interval"]:04x} ${interval:02x}',
                        f'> ${sym["sande_border_follow"]:04x} ${follow:02x}']
            if follow == 2:commands += ['bank cpu', '> $d020 $06', 'bank ram']
            def stop(label):
                commands.extend(['delete', f'break ${sym[label]:04x}', 'g'])
            def toggle():
                stop('sande_row0_read')
                commands.append('r a=$bf')
                for label in ('demo_color_left_shift_read', 'demo_color_right_shift_read'):
                    stop(label)
                    commands.append('r a=$ff')
                stop('sande_done')
            def dump(name):
                commands.extend(['bank ram', f'bsave "{tmp / name}.ram" 0 $0000 $ffff',
                                 'bank cpu', f'bsave "{tmp / name}.vic" 0 $d020 $d021', 'bank ram'])
            toggle()
            dump('start')
            # Let normal no-key polling re-arm F5; observe natural timer events.
            for i in range(36):
                stop('sande_cycle_commit')
                stop('sande_cycle_done')
                dump(str(i))
            toggle()
            dump('stopped')
            for i in range(100):
                stop('frame_draw_complete')
                dump('off-' + str(i))
            run_monitor(crt, vice, data, tmp, commands, 250000000)
            color, last_tick, gaps = 0x10, (tmp / 'start.ram').read_bytes()[sym['sande_cycle_last']], []
            for i in range(36):
                ram = (tmp / f'{i}.ram').read_bytes()
                vic = (tmp / f'{i}.vic').read_bytes()
                fg, bg = color >> 4, color & 15
                if i % 2 == 0:
                    fg = (fg + 1) & 15
                    if fg == bg:fg = (fg + 1) & 15
                else:
                    bg = (bg + 1) & 15
                    if bg == fg:bg = (bg + 1) & 15
                color = (fg << 4) | bg
                assert ram[sym['demo_color_screen']] == color, (i, color)
                assert vic[0] & 15 == (bg if follow == 1 else 6 if follow == 2 else 0) and vic[1] & 15 == bg
                for base in (0x400, 0x4400, 0xc800):
                    assert ram[base:base + 1024] == bytes([color]) * 1024
                tick = ram[sym['sande_cycle_last']]
                gap = (tick - last_tick) % 256
                assert interval <= gap <= interval + 10, (interval, gap)
                gaps.append(gap)
                last_tick = tick
            stopped = (tmp / 'stopped.ram').read_bytes()
            assert stopped[sym['sande_cycle_enabled']] == 0
            for i in range(100):
                ram = (tmp / f'off-{i}.ram').read_bytes()
                assert ram[sym['demo_color_screen']] == stopped[sym['demo_color_screen']]
            results.append(dict(interval_pal_ticks=interval, border_mode=('black', 'follow', 'custom')[follow],
                                updates=36, min_tick_gap=min(gaps), max_tick_gap=max(gaps),
                                alternation=True, palette_wrap=True, distinct_colours=True,
                                stopped_frames_checked=100))
    return dict(passed=True, cases=results)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', type=Path, default=Path('/usr/local/share/vice'))
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for model in MODELS:
        crt = SOURCES / (model + '-hors-render-v2-interactive.crt')
        digest = sha(crt)
        row = dict(cartridge=crt.name, sha256=digest,
                   reverse=reverse_check(crt, a.vice, a.vice_data),
                   keys=key_check(crt, a.vice, a.vice_data),
                   cycle=cycle_check(crt, a.vice, a.vice_data))
        if sha(crt) != digest:
            raise AssertionError('VICE modified the interactive cartridge')
        rows.append(row)
        print(crt.name, 'reverse/palette/input PASS', flush=True)
    (a.out / 'summary.json').write_text(json.dumps(dict(passed=True, results=rows), indent=2) + '\n')


if __name__ == '__main__':
    main()
