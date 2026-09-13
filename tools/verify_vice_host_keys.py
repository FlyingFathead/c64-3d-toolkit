#!/usr/bin/env python3
"""Exercise VICE's host-keysym/keymap/CIA path, without injecting CPU registers.

Linux test-only LD_PRELOAD helper calls the exported VICE keyboard event API
from monitor input on the emulator thread. This covers keymap translation and
emulated matrix scanning; it does not synthesize operating-system GUI events.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from verify_cart_stream import labels
from c643d.hors_v3_help import help_screen_codes
from PIL import Image


def verify(crt, vice, data, out, compiler='cc'):
    crt=Path(crt).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    data=Path(data).resolve();sym=labels(crt.with_suffix('.lbl'))
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    profile=meta['background_effect']['profiles']['default']
    initial_mode=int(profile=='light');initial_level=2 if initial_mode else 3
    shim=out/'hostkeys.so'
    subprocess.run([compiler,'-shared','-fPIC','-o',str(shim),str(Path(__file__).with_name('vice_hostkeys.c')),'-ldl'],check=True)
    results={}
    for mode,index in [('sym',2),('pos',3)]:
        dest=out/mode;dest.mkdir(exist_ok=True)
        keymap=data/'C64'/f'gtk3_{mode}.vkm'
        commands=['delete',f'break ${sym["build_screen_visible"]:04x}','g','delete']
        checks=[];events=[]
        def key(keysym,down,mod=0):
            commands.append(f';hostkey {keysym} {mod} {int(down)}');events.append((keysym,mod,int(down)))
        def advance():commands.extend(['z $40000'])
        def snap(name,**expected):
            commands.extend(['bank ram',f'bsave "{dest/name}.ram" 0 $0000 $ffff'])
            if expected.get('fx_enabled')==0 or 'help_visible' in expected or 'outline' in name or 'card' in name:
                commands.extend(['bank cpu',f'bsave "{dest/name}.vic" 0 $d000 $d02e',
                                 f'scrsh "{dest/name}.png" 2','bank ram'])
            checks.append((name,expected))
        advance();snap('intro-idle')
        # Native Escape mapping, held-key release, and return to SPACE intro.
        key(65307,True);advance();snap('intro-esc-help',help_visible=True)
        advance();snap('intro-esc-held',help_visible=True)
        key(65307,False);advance()
        key(65307,True);advance();key(65307,False);advance()
        snap('intro-after-esc',help_visible=False)
        advance();snap('intro-still-waiting',help_visible=False)
        key(32,True);advance();key(32,False);advance()
        snap('started',sl_mode=initial_mode,sd_level=initial_level,sp_level=3,ui_label_visible=1,fx_enabled=1)
        def tap(char,name,**expected):
            key(ord(char),True);advance();snap(name,**expected)
            key(ord(char),False);advance()
        if initial_mode:tap('4','select-full',sl_mode=0,sd_level=3)
        key(50,True);advance();snap('more',sd_level=4,sp_level=3)
        advance();snap('held-more',sd_level=4,sp_level=3)
        key(50,False);advance()
        tap('2','maximum',sd_level=5);tap('2','clamped-max',sd_level=5)
        tap('1','reset',sd_level=3)
        for n,level in enumerate((2,1,0,0)):tap('3',f'less-{n}',sd_level=level)
        tap('1','reset-again',sd_level=3)
        key(52,True);advance();snap('light',sl_mode=1,sd_level=2,sd_dot_count=1)
        advance();snap('held-mode',sl_mode=1,sd_level=2)
        key(52,False);advance()
        tap('2','light-limit',sl_mode=1,sd_level=2)
        tap('3','light-less',sl_mode=1,sd_level=1)
        tap('4','full-restored',sl_mode=0,sd_level=3,sd_dot_count=2)
        tap('4','light-density-restored',sl_mode=1,sd_level=1)
        tap('1','light-reset',sl_mode=1,sd_level=2)
        tap('4','full-again',sl_mode=0,sd_level=3)
        # A literal plus is positional '-' on the US host keymap.
        plus='+' if mode=='sym' else '-'
        minus='-' if mode=='sym' else '+'
        tap(plus,'speed-up',sd_level=3,sp_level=4)
        tap(minus,'speed-down',sd_level=3,sp_level=3)
        tap('0','speed-reset',sd_level=3,sp_level=3)
        def shifted(char):
            key(65505,True);key(ord(char.upper()),True,1);advance()
            key(ord(char.upper()),False,1);key(65505,False);advance()
        shifted('s');snap('stars-off',fx_enabled=0)
        shifted('o');snap('outline-stays-off',fx_enabled=0,fx_mode=6)
        shifted('o');snap('gradient-stays-off',fx_enabled=0,fx_mode=1)
        shifted('b');snap('card-stays-off',fx_enabled=0,fx_mode=4)
        shifted('b');snap('card-back-stays-off',fx_enabled=0,fx_mode=1)
        tap('4','light-while-off',sl_mode=1,fx_enabled=0)
        advance();snap('light-still-off',sl_mode=1,fx_enabled=0)
        shifted('o');snap('light-outline-stays-off',sl_mode=1,fx_enabled=0,fx_mode=6)
        shifted('o');snap('light-gradient-stays-off',sl_mode=1,fx_enabled=0,fx_mode=1)
        shifted('h');snap('help-stars-off',fx_enabled=0)
        key(32,True);advance();key(32,False);advance()
        snap('help-closed-stars-off',fx_enabled=0)
        key(65307,True);advance();snap('esc-help-stars-off',fx_enabled=0,help_visible=True)
        key(65307,False);advance()
        key(65307,True);advance();key(65307,False);advance()
        snap('esc-closed-stars-off',sl_mode=1,fx_enabled=0,help_visible=False)
        shifted('s');snap('light-on',sl_mode=1,fx_enabled=1)
        shifted('s');snap('light-off',sl_mode=1,fx_enabled=0)
        tap('4','full-while-off',sl_mode=0,fx_enabled=0)
        shifted('s');snap('full-on',sl_mode=0,fx_enabled=1)
        shifted('o');snap('full-outline-on',sl_mode=0,fx_enabled=1,fx_mode=6)
        tap('4','light-outline-on',sl_mode=1,fx_enabled=1,fx_mode=6)
        shifted('o');snap('light-gradient-on',sl_mode=1,fx_enabled=1,fx_mode=1)
        tap('4','full-gradient-on',sl_mode=0,fx_enabled=1,fx_mode=1)
        shifted('u');snap('all-hidden',ui_info_visible=0,ui_perf_visible=0,ui_label_visible=0)
        shifted('h');snap('help')
        commands.extend(['bank cpu',f'bsave "{dest}/help.colors" 0 $d800 $dbff',f'scrsh "{dest}/help.png" 2'])
        key(32,True);advance();key(32,False);advance()
        snap('after-help',ui_info_visible=0,ui_perf_visible=0,ui_label_visible=0)
        key(65307,True);advance();snap('esc-hidden-help',help_visible=True)
        key(65307,False);advance()
        key(65307,True);advance();key(65307,False);advance()
        snap('after-esc',help_visible=False,sl_mode=0,ui_info_visible=0,ui_perf_visible=0,ui_label_visible=0)
        shifted('u');snap('all-restored',ui_info_visible=1,ui_perf_visible=1,ui_label_visible=1)
        key(65505,True);key(65470,True,1);advance()
        key(65470,False,1);key(65505,False);advance()
        snap('f2-default-profile',sl_mode=initial_mode,sd_level=initial_level)
        commands.append('quit');(dest/'run.mon').write_text('\n'.join(commands)+'\n')
        env=os.environ.copy();env['LD_PRELOAD']=str(shim)
        with (dest/'vice.log').open('w') as log:
            subprocess.run([str(vice),'-console','-default','-pal','+sound','-warp','-seed','1',
                '+easyflashcrtwrite','-directory',str(data),'-keymap',str(index),f'-{mode}keymap',str(keymap),
                '-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(dest/'run.mon'),
                '-limitcycles','180000000'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        actual=[line for line in (dest/'vice.log').read_text().splitlines() if line.startswith('HOSTKEY ')]
        assert actual==[f'HOSTKEY {k} {m} {d}' for k,m,d in events], 'Host events were not all dispatched'
        for name,expected in checks:
            ram=(dest/(name+'.ram')).read_bytes()
            for label,value in expected.items():
                if label=='help_visible':
                    vic=(dest/(name+'.vic')).read_bytes()
                    assert (vic[0x18]&0xfe==0x16 and vic[0x11]&0x20==0)==(value or name.startswith('intro-')), (mode,name,'help display')
                    if name.startswith('intro-') and not value:
                        assert ram[0x400:0x7e8]==(dest/'intro-idle.ram').read_bytes()[0x400:0x7e8],(mode,name,'intro changed')
                else:assert ram[sym[label]]==value,(mode,name,label,ram[sym[label]],value)
            if 'sl_mode' in expected:
                target=sym['sl_irq' if expected['sl_mode'] else 'fx_irq']
                assert int.from_bytes(ram[sym['sl_dispatch']+1:sym['sl_dispatch']+3],'little')==target
            if expected.get('fx_enabled')==0:
                assert (dest/(name+'.vic')).read_bytes()[0x15]==0,(mode,name,'sprites still enabled')
                # Both the sprite register and rendered border must be clean.
                # An unchanged $d020/$d021 write caused grey dots on MOS8565
                # even with sprites disabled; a register-only test missed it.
                picture=Image.open(dest/(name+'.png')).convert('RGB')
                assert picture.size==(384,272),picture.size
                assert len(set(picture.crop((0,235,384,272)).getdata()))==1,(mode,name,'border dots remain')
            if name=='intro-idle':assert ram[0x400:0x408]==bytes([32])*8
            if name in ('all-hidden','after-help','after-esc'):
                assert ram[sym['v3_draw_label']]==0x60
                for base in (0x2000,0x6000,0xe000):
                    assert not any(ram[base+232:base+320]),(mode,name,'INTERACTIVE remains')
                    assert not any(ram[base+7680:base+8000]),(mode,name,'bottom HUD remains')
            if name=='help':assert ram[0x8400:0x8800]==bytes(help_screen_codes(meta['interactive_cart']['help']['lines']))
        colors=(dest/'help.colors').read_bytes()
        assert [v&15 for v in colors[:80]]==[14]*40+[3]*40
        assert all(v&15==1 for v in colors[80:1000])
        results[mode]=dict(passed=True,checks=len(checks),host_events=len(events),keymap_sha256=hashlib.sha256(keymap.read_bytes()).hexdigest())
    result=dict(passed=True,cartridge=crt.name,sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
        method='VICE exported host keyboard event API; symbolic and positional keymap translation; unmodified emulated CIA reads',
        gui_events_tested=False,number_keys={'1':'reset','2':'more','3':'less','4':'light/full'},shift_u_all_hud=True,
        escape_help=True,escape_intro_preserves_space_wait=True,initial_profile=profile,f2_restores_initial_profile=True,
        outline_and_card_preserve_starfield_state=True,help_header_stripes=True,stars_off_border_pixels_clean=True,results=results)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('crt',type=Path);p.add_argument('--vice',required=True)
    p.add_argument('--vice-data',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(verify(a.crt,a.vice,a.vice_data,a.out),indent=2))
