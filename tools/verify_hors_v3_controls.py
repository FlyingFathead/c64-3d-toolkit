#!/usr/bin/env python3
"""Verify HORS-V3 inputs and arbitrary reverse traversal in PAL VICE."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from verify_cart_stream import labels, expected_frame, apply_interactive_overlay
from verify_color_combos import run_monitor


def verify_controls(crt, oracle, vice, data):
    crt, oracle = Path(crt).resolve(), Path(oracle).resolve()
    digest = hashlib.sha256(crt.read_bytes()).hexdigest()
    meta = json.loads(crt.with_name(crt.stem + '-manifest.json').read_text())
    assert meta['interactive_cart']['source_surface_colors_preserved']
    sym = labels(crt.with_suffix('.lbl'))
    frames = json.loads(oracle.read_text())
    directions = [1] * 12 + [-1] * (2*len(frames)+7) + [1] * (2*len(frames)+7) + [-1, 1] * 12
    expected, index, slots = [], 0, set()
    with tempfile.TemporaryDirectory(prefix='hors-v3-reverse-') as td:
        td = Path(td)
        commands = []
        for i, direction in enumerate(directions):
            commands += ['delete', f'break ${sym["frame_begin"]:04x}', 'g',
                         f'> ${sym["v3_step"]:04x} ${direction & 255:02x}',
                         'delete', f'break ${sym["frame_draw_complete"]:04x}', 'g',
                         'bank ram', f'bsave "{td / f"{i}.ram"}" 0 $0000 $ffff']
            expected.append(index)
            index = (index + direction) % len(frames)
        run_monitor(crt, vice, data, td, commands, len(directions)*1000000+2000000)
        for i, index in enumerate(expected):
            ram = (td / f'{i}.ram').read_bytes()
            assert ram[sym['frame_index']] == index, ('direction index', i, index)
            slot = ram[sym['render_slot']]
            slots.add(slot)
            bitmap, colors = expected_frame(frames[index], meta['screen_color'])
            apply_interactive_overlay(bitmap, meta)
            baddr, saddr = (0x2000, 0x6000, 0xe000)[slot], (0x400, 0x4400, 0xc800)[slot]
            assert ram[baddr:baddr+7680] == bitmap, ('reverse bitmap', i, index, slot)
            assert ram[saddr:saddr+960] == colors, ('reverse colours', i, index, slot)
    assert set(expected) == set(range(len(frames))) and slots == {0, 1, 2}

    checks, direction = [], 1
    with tempfile.TemporaryDirectory(prefix='hors-v3-keys-') as td:
        td = Path(td)
        commands = []
        def stop(label):
            commands.extend(['delete', f'break ${sym[label]:04x}', 'g'])
        def sample(label, value):
            stop(label)
            commands.append(f'r a=${value:02x}')
        def snapshot(name):
            stop('v3_poll_return')
            commands.extend(['bank ram', f'bsave "{td / f"{len(checks)}.ram"}" 0 $0000 $ffff',
                             'bank cpu', f'bsave "{td / f"{len(checks)}.cia"}" 0 $dc02 $dc03', 'bank ram'])
            checks.append((name, direction))
        for row, shift, name in [(0xfb,'none','cursor right'), (0xfb,'left','left Shift+cursor'),
                                 (0xff,'none','release holds direction'), (0xfb,'right','right Shift+cursor'),
                                 (0xfb,'none','cursor right again'), (0xdf,'none','F3 preserves direction')]:
            sample('v3_row0_read', row)
            if row == 0xfb:
                sample('v3_left_shift_read', 0x7f if shift == 'left' else 0xff)
                if shift != 'left':
                    sample('v3_right_shift_read', 0xef if shift == 'right' else 0xff)
                direction = 1 if shift == 'none' else 255
            snapshot(name)
        for port in ('v3_joy1_read','v3_joy2_read'):
            for value, name in [(0xfb,'left'),(0xf3,'opposed'),(0xfe,'up'),(0xfd,'down'),
                                (0xef,'fire'),(0xf7,'right'),(0xf3,'opposed again')]:
                sample(port,value)
                if value in (0xfb,0xf7):direction=255 if value==0xfb else 1
                snapshot(port+' '+name)
        run_monitor(crt,vice,data,td,commands,150000000)
        for i,(name,wanted) in enumerate(checks):
            ram=(td/f'{i}.ram').read_bytes()
            assert ram[sym['v3_step']]==wanted,(name,ram[sym['v3_step']],wanted)
            assert (td/f'{i}.cia').read_bytes()==bytes([255,0]),('CIA restore',name)
    assert hashlib.sha256(crt.read_bytes()).hexdigest()==digest
    return dict(passed=True,sha256=digest,reverse_pictures_checked=len(directions),
                all_orientations=True,all_three_buffers=True,forward_reverse_wrap=True,
                repeated_direction_changes=True,pixel_match=True,color_match=True,interactive_label_match=True,
                input_checks=len(checks),both_shift_keys=True,both_joystick_ports=True,
                direction_persists=True,opposing_directions_ignored=True,cia_directions_restored=True,
                uniform_palette_controls=False,
                input_method='VICE monitor injects CIA read results at labelled scan boundaries; host mappings and physical controllers are not tested')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--crt',type=Path,required=True)
    p.add_argument('--oracle',type=Path,required=True)
    p.add_argument('--vice',default='x64sc')
    p.add_argument('--vice-data',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    result=verify_controls(a.crt,a.oracle,a.vice,a.vice_data)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(f"HORS-V3 controls: {result['reverse_pictures_checked']} reverse/forward pictures and {result['input_checks']} inputs passed.")


if __name__=='__main__':main()
