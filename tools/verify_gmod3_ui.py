#!/usr/bin/env python3
"""GMod3 cold-boot UI: capacity, indefinite SPACE wait and interactive help."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

from c643d.buildscreen import screen_codes
from verify_cart_stream import labels, verify as verify_frames
from verify_color_combos import run_monitor


def verify(crt, vice, data, output):
    crt = Path(crt).resolve()
    meta = json.loads(crt.with_name(crt.stem + '-manifest.json').read_text())
    sym = labels(crt.with_suffix('.lbl'))
    interactive = bool(meta.get('interactive_cart'))
    expected = bytearray([32] * 1000)
    rows = [('c64-3d-toolkit', 7), ('v. ' + meta['build_screen']['version'], 10),
            (meta['build_screen']['renderer'], 12), ('github.com/FlyingFathead/c64-3d-toolkit', 16),
            ('SPACE to start', 20)]
    if interactive:
        rows += [('press SHIFT+H for help', 19)]
    rows += [(line['text'], line['row']) for line in meta.get('cartridge_capacity',{}).get('lines',[])]
    for text, row in rows:
        start = row * 40 + (40 - len(text)) // 2
        expected[start:start+len(text)] = bytes(screen_codes(text))
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='v3-intro-') as tmp:
        tmp = Path(tmp)
        commands = []
        def stop(label):
            commands.extend(['delete', f'break ${sym[label]:04x}', 'g'])
        def snap(name):
            commands.extend(['bank ram', f'bsave "{tmp/name}.ram" 0 $0000 $ffff',
                             'bank cpu', f'bsave "{tmp/name}.vic" 0 $d000 $d02e', 'bank ram'])
        def sample(label, value):
            stop(label)
            commands.append(f'r a=${value:02x}')
        stop('build_screen_visible')
        commands.append('stopwatch')
        snap('initial')
        # Actual unmodified cold-boot execution, far beyond the old 3s timeout.
        commands.extend(['delete', 'z $200000', 'stopwatch'])
        snap('idle')
        commands.append(f'scrsh "{output/crt.stem}.png" 2')
        if interactive:
            for index, close in enumerate(('space', 'shift-h', 'run-stop')):
                if close=='run-stop':sample('hp_stop_read',0x7f)
                else:
                    sample('v3_left_shift_read', 0x7f)
                    sample('v3_intro_h_read', 0xdf)
                stop('hp_wait')
                snap('help-' + str(index))
                if close in ('space','run-stop'):
                    sample('hp_space_read', 0xef if close=='space' else 0x7f)
                else:
                    sample('hp_space_read', 0xff)
                    sample('v3_left_shift_read', 0x7f)
                    sample('hp_close_h_read', 0xdf)
                stop('build_screen_leave')
                snap('returned-' + str(index))
                commands.extend(['delete', 'z 10000'])
                snap('still-waiting-' + str(index))
        sample('build_screen_space_read', 0xef)
        stop('build_screen_done')
        stop('frame_begin')
        snap('started')
        for _ in range(4):
            stop('frame_draw_complete')
        snap('playing')
        try:
            run_monitor(crt, vice, data, tmp, commands, 60_000_000, acknowledge_startup=False)
        except Exception:
            import shutil
            shutil.copytree(tmp, output/'failure', dirs_exist_ok=True)
            raise
        ticks = [int(x) for x in re.findall(r'Stopwatch:\s*(\d+)', (tmp/'monitor.log').read_text())]
        assert len(ticks) == 2 and ticks[1]-ticks[0] > 5*985248, ticks
        for name in ['initial', 'idle'] + ([f'{kind}-{i}' for i in range(3)
                      for kind in ('returned', 'still-waiting')] if interactive else []):
            ram = (tmp/(name+'.ram')).read_bytes()
            vic = (tmp/(name+'.vic')).read_bytes()
            assert ram[0x400:0x7e8] == expected, (crt.name, name, 'title layout')
            assert vic[0x11]&0x7f == 0x1b and vic[0x18]&0xfe == 0x16, name
            assert vic[0x15] == 0 and vic[0x20]&15 == 0 and vic[0x21]&15 == 0, name
        if interactive:
            from c643d.hors_v3_help import help_screen_codes
            help_text = help_screen_codes(meta['interactive_cart']['help']['lines'])
            for i in range(3):
                ram = (tmp/f'help-{i}.ram').read_bytes()
                assert ram[0x8400:0x8800] == bytes(help_text)
        playing = (tmp/'playing.ram').read_bytes()
        assert playing[sym['frame_index']] != (tmp/'started.ram').read_bytes()[sym['frame_index']]
    result = dict(passed=True, cartridge=crt.name, sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
                  layout=meta['build_screen']['renderer']+' centered startup text',
                  capacity=meta.get('cartridge_capacity'),
                  no_key_wait_seconds=(ticks[1]-ticks[0])/985248,
                  timeout=False, explicit_space_starts=True, playback_reached=True,
                  startup_help_open_and_both_exit_keys=interactive,
                  run_stop_help=interactive,
                  closing_help_returns_to_space_wait=interactive,
                  input_method='PAL VICE cold boot; CIA read results injected only for deliberate key presses')
    (output/(crt.stem+'.json')).write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('crt', type=Path, nargs='+')
    p.add_argument('--vice', default='x64sc')
    p.add_argument('--vice-data', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    for crt in a.crt:
        print(json.dumps(verify(crt, a.vice, a.vice_data, a.output), indent=2), flush=True)
