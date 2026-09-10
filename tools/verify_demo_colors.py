#!/usr/bin/env python3
"""Exercise demo-cart colour keys and measure the idle IRQ scan in PAL VICE."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile

from c643d.cartpaths import menu_manifest_path
from verify_cart_stream import labels, startup_monitor
from verify_color_combos import run_monitor

ROOT=Path(__file__).resolve().parents[1]


def check_entry(crt, meta, index, vice, data):
    entry=meta['streamed_entries'][index]
    sym=labels(ROOT/entry['work']/'runtime.lbl')
    work=ROOT/'build'/f'{crt.stem}-cartridge-demo'
    ctrl=labels(work/f'{crt.stem}-control.lbl')
    menu=labels(work/f'{crt.stem}-runtime-{meta["menu_style"]}.lbl')
    startup,go=startup_monitor(meta,menu)
    commands=['delete',*startup,f'break ${menu["menu_wait_key"]:04x}',go,
        'delete',f'> ${menu["selected_entry"]:04x} ${index:02x}',
        f'break ${sym["frame_draw_complete"]:04x}',f'g ${menu["menu_launch_nowait"]:04x}']
    checks=[]
    with tempfile.TemporaryDirectory(prefix='demo-color-keys-') as td:
        out=Path(td)
        def stop(addr):commands.extend(['delete',f'break ${addr:04x}','g'])
        def sample(addr,value):stop(addr);commands.append(f'r a=${value:02x}')
        def dump(name):commands.extend(['bank ram',f'bsave "{out/name}.ram" 0 $0000 $ffff',
            'bank cpu',f'bsave "{out/name}.vic" 0 $d020 $d021','bank ram'])
        stop(ctrl['cart_control_irq_impl']);commands.append('stopwatch')
        stop(ctrl['control_chain']);commands.append('stopwatch')
        screen=entry['screen_color'];border=entry['border_color']
        def press(kind, shift=False, right=False):
            nonlocal screen,border
            mono=not entry['colors'];row=0xdf if kind in ('fg','bg') else 0xf7
            name=f'key-{len(checks)}'
            sample(ctrl['control_row0_read'],row);dump(name+'-before')
            sample(sym['demo_color_row_read'],row)
            if mono or kind in ('border','reset'):
                sample(sym['demo_color_left_shift_read'],0x7f if shift and not right else 0xff)
                if not (shift and not right):sample(sym['demo_color_right_shift_read'],0xef if shift else 0xff)
            if kind=='fg' and mono:screen=(screen+16)&255
            if kind=='bg' and mono:screen=(screen&240)|((screen+1)&15)
            if kind=='border':border=(border+1)&15
            if kind=='reset':
                border=entry['border_color']
                if mono:screen=entry['screen_color']
            stop(ctrl['control_chain']);dump(name)
            checks.append((name,screen,border,not mono))
            # The held key must not advance again; release must re-arm it.
            sample(ctrl['control_row0_read'],row)
            stop(ctrl['control_chain']);dump(name+'-held')
            checks.append((name+'-held',screen,border,False))
            sample(ctrl['control_row0_read'],0xff)
            stop(ctrl['control_chain'])
        for n in range(16):press('fg')
        for n in range(16):press('bg',shift=True,right=bool(n%2))
        for n in range(16):press('border')
        press('fg');press('bg',shift=True);press('border');press('reset',shift=True)
        run_monitor(crt,vice,data,out,commands,15_000_000)
        ticks=[int(v) for v in re.findall(r'Stopwatch:\s*(\d+)',(out/'monitor.log').read_text())]
        assert len(ticks)==2,ticks
        for name,value,edge,preserve in checks:
            ram=(out/f'{name}.ram').read_bytes();vic=(out/f'{name}.vic').read_bytes()
            assert vic[0]&15==edge,(name,'border',vic[0]&15,edge)
            assert vic[1]&15==value&15,(name,'background',vic[1]&15,value&15)
            if not entry['colors']:
                for base in (0x400,0x4400,0xc800):
                    assert ram[base:base+1024]==bytes([value])*1024,(name,hex(base))
            elif preserve:
                before=(out/f'{name}-before.ram').read_bytes()
                for base in (0x400,0x4400,0xc800):
                    assert ram[base:base+1024]==before[base:base+1024],(name,'source palette changed')
        return dict(name=entry['name'],index=index,source_colors=entry['colors'],
            keyboard_checks=len(checks),monochrome_foreground_background_wrap=not entry['colors'],
            multicolor_foreground_background_ignored=entry['colors'],
            independent_border=True,source_palette_preserved=True,reset=True,
            held_key_debounce=True,both_shift_keys=True,idle_irq_scan_cycles=ticks[1]-ticks[0])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    crt=a.crt.resolve();meta=json.loads(menu_manifest_path(crt).read_text())
    assert all(e.get('color_controls') for e in meta['streamed_entries'])
    selected=[]
    for colors in (False,True):
        selected+=next(([i] for i,e in enumerate(meta['streamed_entries']) if e['colors']==colors),[])
    report=dict(cartridge=crt.name,sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
        entries=[check_entry(crt,meta,i,a.vice,a.vice_data) for i in selected],
        method='PAL VICE; sampled keyboard rows injected in the existing IRQ scanner')
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
