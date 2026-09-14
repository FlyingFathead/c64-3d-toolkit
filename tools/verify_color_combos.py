#!/usr/bin/env python3
"""Verify colour-combo pixels, automatic PAL timing and F3/F4 scanner handling."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from c643d.cartpaths import menu_manifest_path
from verify_cart_stream import labels, verify as verify_frames, render_ram

ROOT=Path(__file__).resolve().parents[1]


def run_monitor(crt,vice,vice_data,out,commands,limit,*,acknowledge_startup=True):
    if acknowledge_startup:
        from verify_cart_stream import startup_monitor
        meta_path=Path(crt).with_name(Path(crt).stem+'-manifest.json')
        label_path=Path(crt).with_suffix('.lbl')
        if meta_path.exists() and label_path.exists():
            startup,go=startup_monitor(json.loads(meta_path.read_text()),labels(label_path))
            if startup and 'build_screen_return' in labels(label_path):
                commands=[*startup,f'break ${labels(label_path)["build_screen_return"]:04x}',go,'delete',*commands]

    (out/'run.mon').write_text('\n'.join(commands+['quit'])+'\n')
    with (out/'vice.log').open('w') as log:
        p=subprocess.run([vice,'-console','-default','-pal','+sound','-warp','-seed','1',
            '+easyflashcrtwrite','-directory',str(vice_data),'-cartcrt',str(crt),
            '-initbreak','reset','-moncommands',str(out/'run.mon'),'-monlogname', str(out/'monitor.log'), '-monlog','-limitcycles',str(limit)],
            stdout=log,stderr=subprocess.STDOUT,timeout=120)
    if p.returncode:raise RuntimeError((out/'vice.log').read_text()[-2500:])


def verify_controls(crt,vice,vice_data,capture=None):
    crt=Path(crt).resolve();meta=json.loads(menu_manifest_path(crt).read_text())
    assert len(meta['streamed_entries'])==4 and meta['color_combo_test']['automatic_start']
    menu=labels(ROOT/'build'/f'{crt.stem}-cartridge-demo'/f'{crt.stem}-runtime-default.lbl')
    ctrl=labels(ROOT/'build'/f'{crt.stem}-cartridge-demo'/f'{crt.stem}-control.lbl')
    intervals=[]
    with tempfile.TemporaryDirectory(prefix='color-combo-timing-') as td:
        out=Path(td);commands=[]
        def stop(addr):commands.extend(['delete',f'break ${addr:04x}','g'])
        def dump(name):commands.extend(['bank ram',f'bsave "{out/name}.ram" 0 $0000 $ffff','bank cpu',f'bsave "{out/name}.vic" 0 $d020 $d021','bank ram'])
        # No cold-start jump or memory patch: title times out and PLAY ALL starts.
        for i in range(8):
            stop(menu['play_all_count']);commands.append('stopwatch');dump(f'start-{i}')
            stop(ctrl['cart_control_auto_next']);commands.append('stopwatch');dump(f'end-{i}')
        stop(menu['play_all_count']);dump('loop')
        # Existing F1 exit and SPACE skip use the unchanged control shim. Enter
        # their handlers as the real matrix scanner does, then verify the state.
        commands.append('> $02fb $00')
        commands.extend(['delete',f'break ${menu["menu_wait_key"]:04x}',f'g ${ctrl["control_menu_key"]:04x}'])
        dump('menu-exit')
        run_monitor(crt,vice,vice_data,out,commands,120_000_000)
        times=[int(x) for x in re.findall(r'Stopwatch:\s*(\d+)',(out/'monitor.log').read_text())]
        assert len(times)==16
        for i in range(8):
            ram=(out/f'start-{i}.ram').read_bytes();entry=meta['streamed_entries'][i%4]
            assert ram[0x02fa]==i%4 and ram[0x02fd]==2,(i,ram[0x02fa:0x300])
            duration=times[2*i+1]-times[2*i]
            # Cartridge mapping can defer the IRQ handler; allow one PAL refresh.
            assert abs(duration-(meta['play_all']['seconds']*50-1)*19656)<19656,(i,duration)
            intervals.append(duration/985248)
            vic=(out/f'start-{i}.vic').read_bytes()
            assert vic[0]&15==entry['border_color']==entry['screen_color']&15
            if capture and i<4:
                capture=Path(capture);capture.mkdir(parents=True,exist_ok=True)
                sym=labels(ROOT/entry['work']/'runtime.lbl')
                from PIL import Image, ImageOps
                im=render_ram(ram,ram[sym['display_slot']])
                from c643d.colors import C64_PALETTE
                rgb=next(v[1] for v in C64_PALETTE.values() if v[0]==entry['border_color'])
                ImageOps.expand(im,border=16,fill=rgb).resize((704,464),Image.Resampling.NEAREST).save(capture/f'combo-{i+1}.png')
        assert (out/'loop.ram').read_bytes()[0x02fa]==0
        assert (out/'menu-exit.ram').read_bytes()[0x02fd]==0
    entry=meta['streamed_entries'][0];sym=labels(ROOT/entry['work']/'runtime.lbl')
    checks=[]
    with tempfile.TemporaryDirectory(prefix='color-combo-keys-') as td:
        out=Path(td);commands=[];screen=entry['screen_color']
        def stop(addr):commands.extend(['delete',f'break ${addr:04x}','g'])
        def sample(addr,value):stop(addr);commands.append(f'r a=${value:02x}')
        def snapshot(expected):
            stop(sym['combo_keys_done']);name=f'key-{len(checks)}'
            commands.extend(['bank ram',f'bsave "{out/name}.ram" 0 $0000 $ffff','bank cpu',f'bsave "{out/name}.vic" 0 $d020 $d021','bank ram'])
            checks.append((name,expected))
        stop(sym['frame_draw_complete'])
        for kind in ('foreground','background'):
            for n in range(16):
                sample(sym['combo_f3_read'],0xdf)
                left=kind=='background' and n%2==0
                right=kind=='background' and n%2==1
                sample(sym['combo_left_shift_read'],0x7f if left else 0xff)
                if not left:sample(sym['combo_right_shift_read'],0xef if right else 0xff)
                screen=((screen+16)&255) if kind=='foreground' else (screen&0xf0)|((screen+1)&15)
                snapshot(screen)
                # Still held: no repeat. Then release to arm the next press.
                sample(sym['combo_f3_read'],0xdf);snapshot(screen)
                sample(sym['combo_f3_read'],0xff);snapshot(screen)
        # Check SPACE's existing next-demo path and preset reset on entry.
        commands.append('> $02fb $00')
        second=labels(ROOT/meta['streamed_entries'][1]['work']/'runtime.lbl')
        commands.extend(['delete',f'break ${second["frame_draw_complete"]:04x}',f'g ${ctrl["control_next_key"]:04x}',
                         'bank ram',f'bsave "{out/"next.ram"}" 0 $0000 $ffff'])
        run_monitor(crt,vice,vice_data,out,commands,15_000_000)
        for name,value in checks:
            ram=(out/f'{name}.ram').read_bytes()
            assert ram[sym['combo_screen_color']]==value,(name,value)
            for base in (0x400,0x4400,0xc800):
                assert ram[base:base+1024]==bytes([value])*1024,(name,hex(base),value)
            vic=(out/f'{name}.vic').read_bytes()
            assert vic[0]&15==value&15 and vic[1]&15==value&15,(name,vic,value)
        ram=(out/'next.ram').read_bytes()
        assert ram[0x02fa]==1 and ram[second['combo_screen_color']]==meta['streamed_entries'][1]['screen_color']
    return dict(cartridge=crt.name,sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
        automatic_start=True,loops_verified=2,order=[0,1,2,3]*2,
        measured_timer_seconds=intervals,foreground_wrap=True,background_wrap=True,
        both_shift_keys=True,held_key_debounce=True,all_three_screen_buffers=True,
        border_follows_background=True,reset_on_next_entry=True,menu_exit=True,
        keyboard_checks=len(checks),method='PAL VICE; real automatic playback; F3/F4 sampled keyboard rows injected by monitor')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--report',type=Path);p.add_argument('--capture',type=Path)
    a=p.parse_args()
    pictures=[verify_frames(a.crt,a.vice,a.vice_data,menu_entry=i) for i in range(4)]
    result=verify_controls(a.crt,a.vice,a.vice_data,a.capture);result['picture_checks']=pictures
    text=json.dumps(result,indent=2)+'\n';print(text)
    if a.report:a.report.write_text(text)

if __name__=='__main__':main()
