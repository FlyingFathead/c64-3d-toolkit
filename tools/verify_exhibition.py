#!/usr/bin/env python3
"""Native host-key exhibition/paged-help checks in both VICE keymaps."""
import argparse,hashlib,json,os,subprocess,re
from pathlib import Path
from verify_cart_stream import labels
from c643d.hors_v3_help import help_screen_codes
from c643d.font import bitmap_text


def verify(crt,vice,data,out):
    crt=Path(crt).resolve();data=Path(data).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text());sym=labels(crt.with_suffix('.lbl'))
    shim=out/'hostkeys.so'
    subprocess.run(['cc','-shared','-fPIC','-o',str(shim),str(Path(__file__).with_name('vice_hostkeys.c')),'-ldl'],check=True)
    results={}
    for mode,index in [('sym',2),('pos',3)]:
        dest=out/mode;dest.mkdir(exist_ok=True)
        cmd=['delete',f'break ${sym["build_screen_visible"]:04x}','g','delete'];checks=[];events=[]
        def key(k,down,mod=0):cmd.append(f';hostkey {k} {mod} {int(down)}');events.append((k,mod,int(down)))
        def advance():cmd.append('z $20000')
        def snap(name,**expected):
            cmd.extend(['bank ram',f'bsave "{dest/name}.ram" 0 $0000 $ffff', 'bank cpu',f'bsave "{dest/name}.vic" 0 $d000 $d02e','bank ram'])
            if 'page' in name or 'notice' in name:cmd.append(f'scrsh "{dest/name}.png" 2')
            checks.append((name,expected))
        def tap(k,name=None,**expected):
            key(ord(k) if isinstance(k,str) else k,True);advance()
            if name:snap(name,**expected)
            key(ord(k) if isinstance(k,str) else k,False);advance()
        def shifted(c):
            key(65505,True);key(ord(c.upper()),True,1);advance()
            key(ord(c.upper()),False,1);key(65505,False);advance()
        def next_scene(name,**expected):
            cmd.extend(['delete',f'break ${sym["ex_choose"]:04x}','g','delete',f'break ${sym["ex_service_done"]:04x}','g','delete'])
            cmd.append('stopwatch')
            snap(name,**expected)
        advance();snap('intro-idle')
        tap(65307,'intro-page0',hp_page=0)
        key(65363,True);advance();snap('intro-page1',hp_page=1)
        advance();snap('intro-page1-held',hp_page=1)
        key(65363,False);advance()
        tap(65361,'intro-page0-back',hp_page=0)
        tap(65307);snap('intro-return')
        tap(32);snap('started',ex_enabled=0,ex_interval=5,ex_random=0,fx_mode=1,fx_enabled=1)
        key(56,True);advance();snap('notice-increased',ex_interval=10)
        advance();snap('notice-held',ex_interval=10)
        key(56,False);advance()
        tap('7','notice-decreased',ex_interval=5);tap('7','interval-min',ex_interval=5)
        tap('5','exhibition-on',ex_enabled=1,fx_enabled=0,ui_info_visible=0,ui_perf_visible=0,ui_label_visible=0)
        next_scene('ordered-card',fx_mode=4,fx_enabled=0)
        next_scene('ordered-solid',fx_mode=6,fx_enabled=0)
        next_scene('ordered-gradient',fx_mode=1,fx_enabled=0)
        shifted('s');tap('4');tap('3')
        next_scene('star-choice-retained',fx_enabled=1,sl_mode=0,sd_level=2)
        shifted('r')
        next_scene('crawl-retained',fx_mode=7,fx_enabled=1,sl_mode=0,sd_level=2)
        tap('6','random-selected',ex_random=1)
        for i in range(12):next_scene('random-'+str(i),fx_enabled=1,sl_mode=0,sd_level=2)
        tap(65307,'running-page0',hp_page=0)
        tap(65363,'running-page1',hp_page=1)
        snap('paused-before');cmd.append('z $400000');snap('paused-after')
        tap(65307)
        tap('5','exhibition-off',ex_enabled=0,fx_enabled=1,ui_info_visible=1,ui_perf_visible=1,ui_label_visible=1)
        # Reset timed notice/maximum/minimum, including autorepeat suppression.
        for i in range(11):tap('8',f'interval-up-{i}',ex_interval=min(60,10+i*5))
        tap('8','interval-max',ex_interval=60)
        # Let the final notice clear while inactive. No idle timer remains.
        cmd.append('z $100000');snap('notice-expired',ex_notice_ticks=0,ex_notice_dirty=0)
        tap('5');tap(65307,'long-pause-page0')
        cmd.append('z $400000');tap(65307);snap('long-resumed',ex_enabled=1,ex_interval=60)
        shifted('u');snap('hud-manual',ui_info_visible=1)
        # F2 stops exhibition and returns presentation defaults.
        key(65505,True);key(65470,True,1);advance();key(65470,False,1);key(65505,False);advance()
        snap('f2-stopped',ex_enabled=0,fx_mode=1,sl_mode=1,fx_enabled=1,ex_interval=5,ex_random=0)
        shifted('t');tap('8');cmd.append('z $100000');snap('white-notice-expired',ex_notice_dirty=0)
        cmd.append('quit');(dest/'run.mon').write_text('\n'.join(cmd)+'\n')
        env=os.environ.copy();env['LD_PRELOAD']=str(shim)
        with (dest/'vice.log').open('w') as log:
            subprocess.run([str(vice),'-console','-default','-pal','+sound','-warp','-seed','1','+easyflashcrtwrite',
                '-directory',str(data),'-keymap',str(index),f'-{mode}keymap',str(data/'C64'/f'gtk3_{mode}.vkm'),
                '-monlogname', str(dest/'monitor.log'), '-monlog','-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(dest/'run.mon'),'-limitcycles','800000000'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
        actual=[x for x in (dest/'vice.log').read_text().splitlines() if x.startswith('HOSTKEY ')]
        assert actual==[f'HOSTKEY {k} {m} {d}' for k,m,d in events],(mode,'host events')
        for name,expected in checks:
            ram=(dest/(name+'.ram')).read_bytes()
            for label,value in expected.items():assert ram[sym[label]]==value,(mode,name,label,ram[sym[label]],value)
            if 'page' in name and 'held' not in name:
                page=ram[sym['hp_page']]
                assert ram[0x8400:0x8800]==bytes(help_screen_codes(meta['interactive_cart']['help']['pages'][page])),(mode,name,'page contents')
            if name in ('notice-increased','notice-decreased'):
                wanted=bitmap_text('AUTO TIME '+('INCREASED TO 10 SECS' if name=='notice-increased' else 'DECREASED TO 05 SECS'))
                for base in (0x2000,0x6000,0xe000):assert ram[base+0x1cc0:base+0x1cc0+240]==wanted,(mode,name,'notification')
            if expected.get('fx_enabled')==0:assert (dest/(name+'.vic')).read_bytes()[0x15]==0
        before=(dest/'paused-before.ram').read_bytes();after=(dest/'paused-after.ram').read_bytes()
        for label in ('tick_counter','ex_seconds','ex_subsecond','fx_mode','sl_mode','sd_level'):assert before[sym[label]]==after[sym[label]],(mode,'pause',label)
        values=[(dest/f'random-{i}.ram').read_bytes()[sym['fx_mode']] for i in range(12)]
        assert all(x in (7,3,5) for x in values) and all(x!=y for x,y in zip(values,values[1:])),values
        expired=(dest/'notice-expired.ram').read_bytes()
        assert expired[sym['ex_tick_gate']]==0x60 and expired[sym['ex_service_gate']]==0x60
        for base in (0x2000,0x6000,0xe000):assert not any(expired[base+0x1cc0:base+0x1cc0+240]),'notice trail'
        white=(dest/'white-notice-expired.ram').read_bytes()
        for slot,screen in enumerate((0x400,0x4400,0xc800)):
            bg=white[sym['v3_slot_background']+slot]
            assert bg==1
            assert all((v&15)==bg for v in white[screen+920:screen+950]),'notice background not restored'
        assert (dest/'intro-idle.ram').read_bytes()[0x400:0x7e8]==(dest/'intro-return.ram').read_bytes()[0x400:0x7e8]
        stamps=[int(v) for v in re.findall(r'Stopwatch:\s*(\d+)',(dest/'monitor.log').read_text())]
        intervals=[stamps[i+1]-stamps[i] for i in range(2)]
        assert all(abs(v-250*19656)<200000 for v in intervals),(mode,'five-second timer',intervals)
        results[mode]=dict(passed=True,checks=len(checks),random_modes=values,host_events=len(events),ordered_interval_cycles=intervals)
    result=dict(passed=True,cartridge_sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),results=results,
        gui_events_tested=False,method='VICE host keysym API -> symbolic/positional matrix, native 6510 code',
        page_headers_verified=True,space_intro_preserved=True,random_no_repeats=True,star_choices_retained=True)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt');p.add_argument('--vice',required=True);p.add_argument('--vice-data',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();print(json.dumps(verify(a.crt,a.vice,a.vice_data,a.out),indent=2))
