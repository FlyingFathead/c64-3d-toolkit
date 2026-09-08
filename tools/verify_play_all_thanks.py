#!/usr/bin/env python3
"""Exercise the PLAY ALL closing screen, native F1 and all three menu styles."""
import argparse
import hashlib
import json
from pathlib import Path
from c643d.cartpaths import menu_manifest_path
import re
import subprocess
import tempfile

from verify_cart_stream import labels
from verify_cart_ending import text_image
from c643d.buildscreen import screen_codes


def verify(crt, vice, vice_data, output):
    crt, vice_data, output = map(lambda p: Path(p).resolve(), (crt, vice_data, output))
    output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    meta = json.loads(menu_manifest_path(crt).read_text())
    work = root / 'build' / (crt.stem + '-cartridge-demo')
    styles = meta['menu_styles']
    menus = [labels(work / (crt.stem + '-runtime-' + s + '.lbl')) for s in styles]
    control = labels(work / (crt.stem + '-control.lbl'))
    last = len(meta['entries']) - 1
    last_runtime = labels(root / meta['streamed_entries'][last]['work'] / 'runtime.lbl')
    results = []
    for style, menu in enumerate(menus):
        for skip in (False, True):
            with tempfile.TemporaryDirectory(prefix='c643d-thanks-') as td:
                td = Path(td)
                commands = []
                def stop(address, start=None):
                    commands.extend(['delete', f'break ${address:04x}', 'g' if start is None else f'g ${start:04x}'])
                def dump(name):
                    commands.extend(['bank ram', f'bsave "{td / (name + ".ram")}" 0 $0000 $ffff',
                                     'bank cpu', f'bsave "{td / (name + ".io")}" 0 $d000 $dfff'])
                initial = styles.index(meta['menu_style'])
                stop(menus[initial]['menu_wait_key'])
                current = initial
                while current != style:
                    following = (current + 1) % len(styles)
                    stop(menus[following]['menu_wait_key'], menus[current]['menu_cycle_style'])
                    current = following
                commands.append(f'> ${menu["selected_entry"]:04x} ${last:02x}')
                stop(last_runtime['frame_draw_complete'], menu['menu_launch'])
                commands.extend(['> $02fd $02', '> $02fb $00'])
                stop(menu['play_all_thanks_visible'], control['control_next_nowait'])
                commands.append('stopwatch')
                dump('thanks')
                if skip:
                    commands.extend(['> $dc01 $00', '> $dc03 $10'])
                    stop(menu['play_all_thanks_exit'])
                    commands.append('stopwatch')
                    commands.append('> $dc03 $00')
                    stop(menu['menu_wait_key'])
                    dump('after')
                    stop(last_runtime['frame_draw_complete'], menu['menu_launch'])
                    dump('relaunch')
                else:
                    stop(menu['play_all_thanks_timeout'])
                    commands.append('stopwatch')
                    stop(menu['play_all_count'])
                    dump('after')
                commands.append('quit')
                (td / 'run.mon').write_text('\n'.join(commands) + '\n')
                cmd = [str(vice), '-console', '+easyflashcrtwrite', '-pal', '+sound', '-warp', '-seed', '1',
                       '-jamaction', '2', '-directory', str(vice_data), '-cartcrt', str(crt),
                       '-initbreak', 'reset', '-moncommands', str(td / 'run.mon'),
                       '-monlog', '-monlogname', str(td / 'monitor.log'), '-limitcycles', '35000000']
                with (td / 'vice.log').open('w') as log:
                    subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
                monitor = (td / 'monitor.log').read_text()
                ticks = [int(t) for t in re.findall(r'Stopwatch:\s*(\d+)', monitor)]
                assert len(ticks) == 2, monitor[-1800:]
                elapsed = (ticks[1] - ticks[0]) / 985248
                assert (elapsed < .02 if skip else 9.95 < elapsed < 10.02), elapsed
                ram = bytearray((td / 'thanks.ram').read_bytes())
                ram[0xd000:0xe000] = (td / 'thanks.io').read_bytes()
                for text in ['THANK YOU FOR WATCHING', 'c64-3d-toolkit v' + meta['version'],
                             'DEMO CART', 'github.com/flyingfathead/c64-3d-toolkit', 'F1 TO RETURN TO MENU']:
                    assert bytes(screen_codes(text)) in ram[0x400:0x7e8], text
                assert ram[0xd020] & 15 == ram[0xd021] & 15 == 0
                assert all(c & 15 == 1 for c in ram[0xd800:0xdbe8])
                assert ram[0xd018] & 0xfe == 0x16
                assert ram[0xd01a] & 15 == 0, 'Party IRQ must be disabled for the closing screen'
                after = (td / 'after.ram').read_bytes()
                assert after[0x02fc] == style, 'F1 must preserve the selected menu style'
                if skip:
                    assert after[0x02fd] == 0 and after[menu['selected_entry']] == last
                    relaunch = (td / 'relaunch.ram').read_bytes()
                    assert relaunch[0x02fa] == last and relaunch[0x02fd] == 0
                else:
                    assert after[0x02fa] == 0 and after[0x02fd:0x300] == bytes((2, 50, meta['play_all']['seconds']))
                if style == 0 and not skip:
                    from PIL import Image
                    charset = next((vice_data / 'C64').glob('chargen-901225*')).read_bytes()[0x800:]
                    text_image(ram, charset, 0).resize((960, 600), Image.Resampling.NEAREST).save(output / 'play-all-thank-you.png')
                results.append(dict(style=styles[style], action='F1' if skip else 'timeout',
                                    seconds=elapsed, correct_screen=True, style_preserved=True,
                                    following_demo_or_menu_reached=True))
    result = dict(cartridge=crt.name, sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
                  tests=results, input='Native CIA F1 column driven low through VICE monitor; not host keyboard injection.')
    (output / 'play-all-thanks-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('crt')
    parser.add_argument('--vice', default='x64sc')
    parser.add_argument('--vice-data', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.crt, args.vice, args.vice_data, args.output), indent=2))
