#!/usr/bin/env python3
"""VICE regression: launch every uniform-cart demo from every menu style.

Build the cart first for matching symbols, runtime PRGs and frame oracles.
Exercises the real F1/RETURN/control handlers via the monitor; it does not
inject host keyboard events. The demoscene raster IRQ is allowed to run.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from c643d.cartridge import _patch_demo_irq
from verify_cart_stream import expected_frame, labels


def verify(crt, vice='x64sc', vice_data=None):
    root = Path(__file__).resolve().parents[1]
    crt = Path(crt).resolve()
    manifest = json.loads(crt.with_name(crt.stem + '-cart-manifest.json').read_text())
    if not manifest.get('uniform_renderer') or manifest['menu_style'] != 'default':
        raise ValueError('requires a uniform cart with default startup style')
    entries = manifest['streamed_entries']
    work = root / 'build' / (crt.stem + '-cartridge-demo')
    styles = ('default', 'decorative', 'demoscene')
    menus = {s: labels(work / f'{crt.stem}-runtime-{s}.lbl') for s in styles}
    control = labels(work / f'{crt.stem}-control.lbl')
    symbols = [labels(root / e['work'] / 'runtime.lbl') for e in entries]
    payloads = [_patch_demo_irq((root / e['work'] / 'runtime.prg').read_bytes()[2:])[0]
                for e in entries]
    frames = [json.loads((root / e['work'] / 'oracle.json').read_text()) for e in entries]
    checks = []
    with tempfile.TemporaryDirectory(prefix='c643d-menu-launch-') as temp:
        out = Path(temp)
        commands = ['delete', f'break ${menus["default"]["menu_wait_key"]:04x}', 'g']

        def stop_at(address, start=None, idle=0):
            commands.extend(['delete', f'break ${address:04x}'])
            if idle:
                commands.append(f'ignore 1 {idle}')
            commands.append('g' if start is None else f'g ${start:04x}')

        def dump(name, bank='ram', start=0, end=0xffff):
            commands.extend([f'bank {bank}',
                             f'bsave "{out / name}" 0 ${start:04x} ${end:04x}'])

        def animation(index, tag, start):
            stop_at(0x080d, start)
            dump(tag + '-loaded.ram')
            dump(tag + '-port.bin', 'cpu', 0, 1)
            dump(tag + '-vic.bin', 'cpu', 0xd019, 0xd01a)
            for f in range(3):
                stop_at(symbols[index]['frame_draw_complete'])
                dump(tag + f'-frame-{f}.ram')
            checks.append((index, tag))

        # A second style cycle catches state that survives launching/returning.
        for pass_index in range(2):
            for style_index, style in enumerate(styles):
                menu = menus[style]
                if pass_index or style_index:
                    previous = menus[styles[(style_index - 1) % 3]]
                    stop_at(menu['menu_wait_key'], previous['menu_cycle_style'])
                tag = f'{pass_index}-{style}'
                dump(tag + '-before-idle.ram')
                stop_at(menu['menu_wait_key'], idle=3000)
                dump(tag + '-idle.ram')
                dump(tag + '-idle-port.bin', 'cpu', 0, 1)
                for index in range(len(entries)):
                    item = tag + f'-{index:02d}'
                    commands.append(f'> ${menu["selected_entry"]:04x} ${index:02x}')
                    animation(index, item, menu['menu_launch'])
                    if index in (len(entries) - 2, len(entries) - 1):
                        commands.append('> $02fb $00')
                        animation((index + 1) % len(entries), item + '-next',
                                  control['control_next_key'])
                    commands.append('> $02fb $00')
                    stop_at(menu['menu_wait_key'], control['control_menu_key'])
                    dump(item + '-returned.ram')
        commands.append('quit')
        (out / 'run.mon').write_text('\n'.join(commands) + '\n')
        cmd = [vice, '-console', '+sound', '-warp', '-seed', '1', '-jamaction', '2',
               '-cartcrt', str(crt), '-initbreak', 'reset', '-moncommands',
               str(out / 'run.mon'), '-limitcycles', '180000000']
        if vice_data:
            cmd.extend(['-directory', str(vice_data)])
        with (out / 'vice.log').open('w') as log:
            result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        if result.returncode or 'Main CPU: JAM' in (out / 'vice.log').read_text():
            raise AssertionError('VICE launch regression failed:\n' +
                                 (out / 'vice.log').read_text()[-6000:])
        for pass_index in range(2):
            for style_index, style in enumerate(styles):
                tag = f'{pass_index}-{style}'
                menu = menus[style]
                ram = (out / (tag + '-idle.ram')).read_bytes()
                assert ram[0x02fc] == style_index, (tag, 'style')
                assert manifest['version'].encode() in ram[0x0400:0x07e8], (tag, 'version text')
                port = (out / (tag + '-idle-port.bin')).read_bytes()[1] & 7
                assert port == (5 if style == 'demoscene' else 7), (tag, 'menu mapping', port)
                if style == 'demoscene':
                    before = (out / (tag + '-before-idle.ram')).read_bytes()
                    assert ram[menu['gradient_divider']] != before[menu['gradient_divider']], (tag, 'IRQ did not run')
                for index in range(len(entries)):
                    returned = (out / (tag + f'-{index:02d}-returned.ram')).read_bytes()
                    expected = (index + 1) % len(entries) if index >= len(entries)-2 else index
                    assert returned[0x02fc] == style_index
                    assert returned[menu['selected_entry']] == expected
                    assert returned[menu['top_entry']] <= expected < returned[menu['top_entry']] + 10
        shim = (work / f'{crt.stem}-control.bin').read_bytes()[:0xf8]
        for index, tag in checks:
            ram = (out / (tag + '-loaded.ram')).read_bytes()
            assert ram[0x0801:0x0801 + len(payloads[index])] == payloads[index], (tag, 'payload')
            assert ram[0x0200:0x02f8] == shim, (tag, 'control shim')
            assert ram[0x02fa] == index, (tag, 'current entry')
            assert (out / (tag + '-port.bin')).read_bytes()[1] & 7 == 7, (tag, 'loader mapping')
            assert (out / (tag + '-vic.bin')).read_bytes()[1] & 15 == 0, (tag, 'menu IRQ still enabled')
            slots = set()
            for f in range(3):
                ram = (out / (tag + f'-frame-{f}.ram')).read_bytes()
                sym = symbols[index]
                assert ram[sym['frame_index']] == f
                slot = ram[sym['render_slot']]
                slots.add(slot)
                bitmap, colors = expected_frame(frames[index][f], entries[index]['screen_color'])
                baddr, caddr = (0x2000, 0x6000, 0xe000)[slot], (0x0400, 0x4400, 0xc800)[slot]
                assert ram[baddr:baddr+7680] == bitmap, (tag, f, 'bitmap')
                assert ram[caddr:caddr+960] == colors, (tag, f, 'colors')
            assert slots == {0, 1, 2}, (tag, 'buffer slots')
    return dict(version=manifest['version'], version_text_all_styles=True, cartridge=crt.name, sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
                renderer=manifest['stream_renderer'], styles=list(styles), style_cycles=2,
                demos_per_style=len(entries), menu_launches=6*len(entries),
                next_launches=len(checks)-6*len(entries), frames_checked=3*len(checks),
                exact_payloads=True, exact_control_shim=True, pixel_and_color_match=True,
                flashing_irq_exercised=True, loader_mapping_verified=True,
                menu_irq_disabled_at_handoff=True, menu_return_and_wrap=True,
                method='Real menu/control handlers entered through the VICE monitor; host key injection not used.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('crt', type=Path)
    parser.add_argument('--vice', default='x64sc')
    parser.add_argument('--vice-data')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    result = verify(args.crt, args.vice, args.vice_data)
    text = json.dumps(result, indent=2) + '\n'
    print(text)
    if args.report:
        args.report.write_text(text)
