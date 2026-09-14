#!/usr/bin/env python3
"""Verify collection help and SAKU baseline through VICE host-keyboard events.

Uses the exported VICE keyboard API and its real symbolic/positional keymaps.
CPU registers and CIA samples are never injected. Monitor entry selection is
used only to launch each cartridge runtime reproducibly.
"""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
from c643d.gmod3_probe import labels, vice_command
from c643d.hors_v3_help import help_screen_codes
from c643d.interactive_cart_baseline import collection_help_pages
from c643d.gmod3_catalog import frames_for
from verify_cart_stream import expected_frame

ROOT=Path(__file__).resolve().parents[1]


def verify(crt, vice, data, output, entries=None):
    crt=Path(crt).resolve();data=Path(data).resolve();output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    menu=labels(crt.parent/meta['collection_labels'])
    rows=[e for e in meta['entries'] if entries is None or e['index'] in entries]
    shim=output/'hostkeys.so'
    subprocess.run(['cc','-shared','-fPIC','-o',str(shim),str(ROOT/'tools/vice_hostkeys.c'),'-ldl'],check=True)
    results=[]
    for mode,index in [('sym',2),('pos',3)]:
        out=output/mode;out.mkdir(exist_ok=True)
        commands=['delete',f'break ${menu["menu_poll"]:04x}','g','delete']
        checks=[];events=[];sym=None;entry=None
        def advance(amount='$20000'):commands.append('z '+amount)
        def key(k,down,mod=0):
            commands.append(f';hostkey {k} {mod} {int(down)}');events.append(f'HOSTKEY {k} {mod} {int(down)}')
        def tap(k):key(k,True);advance();key(k,False);advance()
        def shifted(ch):
            key(65505,True);key(ord(ch.upper()),True,1);advance()
            key(ord(ch.upper()),False,1);key(65505,False);advance()
        def fkey(n,ctrl=False):
            shift=n%2==0;odd=n-1 if shift else n
            modifier=65505 if shift else 65507 if ctrl else None
            mod=1 if shift else 4 if ctrl else 0
            if modifier:key(modifier,True)
            key(65469+odd,True,mod);advance();key(65469+odd,False,mod)
            if modifier:key(modifier,False)
            advance()
        def snap(name,**expected):
            prefix=f'{entry["index"]:02d}-' if entry is not None else 'menu-'
            name=prefix+name
            commands.extend(['bank ram',f'bsave "{out/name}.ram" 0 $0000 $ffff',
                'bank cpu',f'bsave "{out/name}.vic" 0 $d000 $d02e','bank ram'])
            if name.startswith(('menu-','00-')) and ('help' in name or name.endswith(('hud-off','stars-on'))):
                commands.append(f'scrsh "{out/name}.png" 2')
            checks.append((name,dict(sym or {}),dict(expected),entry))
        advance();snap('before',menu=True)
        shifted('h');snap('help1',help_page=0,main_help=True)
        tap(65363);snap('help2',help_page=1,main_help=True)
        tap(65361);snap('help1-return',help_page=0,main_help=True)
        tap(32);snap('after-space',menu=True)
        shifted('h');tap(65307);snap('after-esc',menu=True)
        shifted('h');shifted('h');snap('after-shift-h',menu=True)
        shifted('h');fkey(1);snap('after-f1',menu=True)
        entry=meta['entries'][0];sym=labels(crt.parent/entry['labels'])
        for launch_key,label in [(32,'space'),(65293,'enter')]:
            tap(launch_key);advance('$80000');snap('launch-'+label,fx_enabled=0,ui_info_visible=1)
            tap(65307);snap('exit-'+label,menu=True,selected=0)
        for entry in rows:
            sym=labels(crt.parent/entry['labels'])
            def launch():
                commands.extend(['delete',f'> $0330 {entry["index"]:02x}',
                    f'break ${sym["frame_begin"]:04x}',f'g ${menu["collection_start"]:04x}','delete'])
                advance('$80000')
            launch();snap('startup',fx_enabled=0,ui_info_visible=1,ui_perf_visible=1,ui_label_visible=1)
            shifted('i');snap('info-off',ui_info_visible=0,ui_perf_visible=1)
            shifted('i');shifted('f');snap('fps-off',ui_info_visible=1,ui_perf_visible=0)
            shifted('f');shifted('u');snap('hud-off',ui_info_visible=0,ui_perf_visible=0,ui_label_visible=0,hidden=True)
            for slot_test in range(3):
                commands.extend(['delete',f'break ${sym["frame_draw_complete"]:04x}','g','delete'])
                snap('hidden-picture-'+str(slot_test),hidden=True,picture=True)
                advance('$100')
            shifted('h');snap('help1',help_page=0)
            tap(65363);snap('help2',help_page=1)
            tap(32);snap('help-closed-hidden',hidden=True)
            shifted('u');snap('hud-restored',ui_info_visible=1,ui_perf_visible=1,ui_label_visible=1)
            shifted('s');snap('stars-on',fx_enabled=1)
            tap(65307);snap('exit-stars',menu=True,selected=entry['index'])
            launch();shifted('h');tap(65363);tap(65307);snap('exit-help2',menu=True,selected=entry['index'])
            if entry['index'] not in (0,1,31):continue
            launch()
            for ch,expected in [('3',{'sd_level':1}),('2',{'sd_level':2}),('1',{'sd_level':2}),
                ('4',{'sl_mode':0,'sd_level':3,'fx_enabled':0}),('3',{'sd_level':2}),
                ('4',{'sl_mode':1,'sd_level':2}),('4',{'sl_mode':0,'sd_level':2}),('1',{'sd_level':3})]:
                tap(ord(ch));snap('density-'+str(len(checks)),**expected)
            plus='+' if mode=='sym' else '-';minus='-' if mode=='sym' else '+'
            tap(ord(plus));snap('speed-up',sp_level=4);tap(ord(minus));snap('speed-down',sp_level=3)
            tap(48);snap('speed-reset',sp_level=3)
            # All native function-key colour/border controls.
            fkey(4);snap('background',v3_background=(entry['screen_color']+1)&15)
            fkey(5);snap('cycle-on',v3_cycle_enabled=1)
            fkey(6);snap('cycle-slower',v3_cycle_rate=1);fkey(7);snap('cycle-faster',v3_cycle_rate=2)
            fkey(8);snap('border-follow');fkey(7,ctrl=True);snap('border-colour')
            fkey(3);snap('foreground')
            fkey(2);snap('reset',fx_enabled=0,sp_level=3)
            tap(53);snap('exhibition',ex_enabled=1,fx_enabled=0,hidden=True)
            tap(54);snap('exhibition-random',ex_random=1)
            tap(56);snap('exhibition-longer',ex_interval=10)
            tap(55);snap('exhibition-shorter',ex_interval=5)
            shifted('s');snap('exhibition-stars',fx_enabled=1)
            tap(65307);snap('exit-exhibition',menu=True)
            launch();tap(ord(minus));tap(ord(minus));tap(ord(minus));snap('slowest',sp_level=0)
            key(ord(plus),True);advance();key(65307,True);advance();key(65307,False);key(ord(plus),False);advance()
            snap('exit-held-speed',menu=True)
            launch();shifted('u');shifted('h');fkey(1);snap('exit-f1-help-hidden',menu=True)
            # A short STOP event during an actual render is latched by the IRQ.
            launch();commands.extend(['delete',f'break ${sym["profile_recycle"]:04x}','g','delete'])
            key(65307,True);advance('$c000');key(65307,False);advance('$80000');snap('exit-short-stop',menu=True)
            if not entry['mode_frames']:continue
            launch()
            for ch,expected in [('t',{'fx_mode':0,'fx_enabled':0,'v3_background':1}),
                ('w',{'fx_mode':0,'fx_enabled':0}),('g',{'fx_mode':1,'fx_enabled':1}),
                ('r',{'fx_mode':3}),('b',{'fx_mode':5}),('o',{'fx_mode':7}),
                ('r',{'fx_mode':6}),('o',{'fx_mode':1})]:
                shifted(ch);snap('saku-'+ch+'-'+str(len(checks)),**expected)
            fkey(2);snap('saku-reset-stars-off',fx_enabled=0)
            tap(65307);snap('saku-exit',menu=True)
        commands.append('quit');(out/'run.mon').write_text('\n'.join(commands)+'\n')
        env=os.environ.copy();env['LD_PRELOAD']=str(shim)
        keymap=data/'C64'/f'gtk3_{mode}.vkm'
        cmd=vice_command(vice,crt,data)+['-keymap',str(index),f'-{mode}keymap',str(keymap),
            '-initbreak','reset','-moncommands',str(out/'run.mon'),'-limitcycles','1500000000']
        print(f'Checking {mode}: {len(rows)} entries, {len(checks)} states, {len(events)} host events',flush=True)
        with (out/'vice.log').open('w') as log:
            subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
        dispatched=re.findall(r'HOSTKEY \d+ \d+ [01]',(out/'vice.log').read_text())
        assert events==dispatched,'Missing host events'
        menu_screen=(out/'menu-before.ram').read_bytes()[0x400:0x7e8]
        frame_cache={}
        for name,symbols,expected,row in checks:
            ram=(out/(name+'.ram')).read_bytes();vic=(out/(name+'.vic')).read_bytes()
            for label,value in expected.items():
                if label=='main_help':continue
                if label=='help_page':
                    main=expected.get('main_help',False)
                    pages=collection_help_pages(modes=True if main else bool(row['mode_frames']))
                    base=0x400 if main else 0x8400
                    assert ram[base:base+1024]==bytes(help_screen_codes(pages[value])),(mode,name,'help text')
                elif label=='menu':
                    assert vic[0x11]&0x20==0 and ram[0x400:0x450]==menu_screen[:80],(mode,name,'not in menu')
                    if name.startswith('menu-after'):assert ram[0x400:0x7e8]==menu_screen,(mode,name,'selection changed')
                elif label=='selected':assert ram[0x330]==value,(mode,name,'selection')
                elif label=='picture':
                    if row['index'] not in frame_cache:
                        frame_cache[row['index']]=frames_for(ROOT/'build/gmod3-catalog',row)
                    fi=ram[symbols['frame_index']]+(ram[symbols['gp_page']]*128 if 'gp_page' in symbols else 0)
                    bm,_=expected_frame(frame_cache[row['index']][fi].__dict__,row['screen_color'])
                    base=(0x2000,0x6000,0xe000)[ram[symbols['render_slot']]]
                    assert ram[base:base+7680]==bytes(bm),(mode,name,'hidden artwork mismatch')
                elif label=='hidden':
                    for draw in ('v3_draw_label','render_fps_digits','sp_draw'):
                        assert ram[symbols[draw]]==0x60,(mode,name,draw,'HUD draw still active')
                    for base in (0x2000,0x6000,0xe000):
                        assert not any(ram[base+7680:base+8000]),(mode,name,'HUD pixels remain')
                else:assert ram[symbols[label]]==value,(mode,name,label,ram[symbols[label]],value)
        results.append(dict(keymap=mode,passed=True,entries=[e['index'] for e in rows],checks=len(checks),host_events=len(events),
            keymap_sha256=hashlib.sha256(keymap.read_bytes()).hexdigest()))
    result=dict(passed=True,version=(ROOT/'VERSION').read_text().strip(),cartridge=crt.name,
        crt_sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),results=results,
        method='VICE keyboard event API, real symbolic/positional keymap and unmodified CIA reads',gui_events_tested=False,
        startup_help=True,complete_help=True,hud_all_three_buffers=True,stars_off_startup_reset=True,
        held_key_exit=True,help_exit=True,exhibition_exit=True,short_stop_latched=True)
    (output/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',required=True);p.add_argument('--vice-data',required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/benchmarks/release-0.8.1/keyboard')
    p.add_argument('--entries',type=int,nargs='*');a=p.parse_args()
    print(json.dumps(verify(a.crt,a.vice,a.vice_data,a.output,a.entries),indent=2))
