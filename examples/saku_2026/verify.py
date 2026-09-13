#!/usr/bin/env python3
"""Verify SAKU pixels and controls in PAL VICE; measure and capture the live VIC output."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_color_combos import run_monitor
from verify_cart_stream import labels, expected_frame, apply_interactive_overlay, verify
from c643d.hors_v3_effects import trajectories
CLOCK=985248
PAL=19656

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):p.write_text(json.dumps(data,indent=2)+'\n')

def help_keys(cart,vice,data,capture_dir):
    from c643d.hors_v3_help import help_lines, help_screen_codes
    from c643d.buildscreen import screen_codes
    sym=labels(cart.with_suffix('.lbl'))
    with tempfile.TemporaryDirectory(prefix='saku-help-') as tmp:
        out=Path(tmp);cmd=[]
        def stop(name):cmd.extend(['delete',f'break ${sym[name]:04x}','g'])
        def snap(name):
            cmd.extend(['bank ram',f'bsave "{out/name}.ram" 0 $0000 $ffff',
                        'bank cpu',f'bsave "{out/name}.vic" 0 $d000 $d02e',
                        f'bsave "{out/name}.cia" 0 $dd00 $dd00','bank ram'])
        stop('frame_begin');snap('startup')
        for i in range(2):
            stop('fx_poll');stop('v3_left_shift_read');cmd.append('r a=$7f')
            stop('hp_h_read');cmd.append('r a=$df')
            stop('hp_save');snap(f'before{i}')
            stop('hp_wait');snap(f'help{i}')
            # Spend real emulated time in the help loop: raster ticks, frame
            # counters, star phases and all buffered pictures must stay still.
            cmd.extend(['delete','z 20000']);snap(f'paused{i}')
            if i==0:cmd.append(f'scrsh "{capture_dir}/saku_2026-help.png" 2')
            if i==0:
                stop('hp_space_read');cmd.append('r a=$ef')
            else:
                stop('hp_space_read');cmd.append('r a=$ff')
                stop('v3_left_shift_read');cmd.append('r a=$7f')
                stop('hp_close_h_read');cmd.append('r a=$df')
            stop('hp_restored');snap(f'after{i}')
        run_monitor(cart,vice,data,out,cmd,40_000_000)
        meta=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text())
        lines=help_lines((ROOT/'VERSION').read_text().strip(),effects=True,modes=True,variants=meta['presentation_modes'].get('variants',()),hud=meta.get('hud_visibility',{}).get('toggle_allowed',True))
        text=bytes(help_screen_codes(lines))
        # Paged text is expanded on demand from the packed store.
        assert (out/'help0.ram').read_bytes()[0x8400:0x8800]==text
        states=['frame_index','tick_counter','display_slot','render_slot','free_slot','ready_slot',
                'fx_mode','fx_enabled','fx_foreground','v3_background','v3_step','sp_level']
        states += [name for name in ('ui_info_visible','ui_perf_visible','ui_label_visible','sl_mode','sd_level') if name in sym]
        for i in range(2):
            before=(out/f'before{i}.ram').read_bytes()
            help_ram=(out/f'help{i}.ram').read_bytes()
            paused=(out/f'paused{i}.ram').read_bytes()
            after=(out/f'after{i}.ram').read_bytes()
            for addr,length in [(0x2000,8000),(0x6000,8000),(0xe000,8000),(0x400,1024),(0x4400,1024),(0xc800,1024)]:
                assert before[addr:addr+length]==help_ram[addr:addr+length]==paused[addr:addr+length]==after[addr:addr+length]
            for label in states:
                assert before[sym[label]]==help_ram[sym[label]]==paused[sym[label]]==after[sym[label]],label
            initial=(out/f'before{i}.vic').read_bytes();final=(out/f'after{i}.vic').read_bytes()
            for addr in (0x11,0x16,0x18,0x20,0x21,0x15):
                mask=0x7f if addr==0x11 else 255
                assert initial[addr]&mask==final[addr]&mask,hex(addr)
            assert (out/f'before{i}.cia').read_bytes()==(out/f'after{i}.cia').read_bytes()
            shown=(out/f'help{i}.vic').read_bytes()
            assert shown[0x11]&0x7f==0x1b and shown[0x18]&0xfe==0x16 and shown[0x15]==0
    return dict(passed=True,versioned_help_text=True,open_with_shift_h=True,close_with_space_and_shift_h=True,
                paused_machine_instructions=20000,bitmap_buffers_preserved=3,presentation_state_preserved=True,vic_restored=True)

def keys(cart,vice,data):
    sym=labels(cart.with_suffix('.lbl'));checks=[]
    with tempfile.TemporaryDirectory(prefix='saku-keys-') as tmp:
        out=Path(tmp);cmd=[]
        def stop(name):cmd.extend(['delete',f'break ${sym[name]:04x}','g'])
        def sample(name,value):stop(name);cmd.append(f'r a=${value:02x}')
        def snapshot(name,expected,where='fx_poll_return'):
            stop(where);cmd.extend(['bank ram',f'bsave "{out/str(len(checks))}.ram" 0 $0000 $ffff'])
            checks.append((name,expected))
        def special(key,expected,held=False):
            stop('fx_poll');sample('v3_left_shift_read',0x7f)
            sample('fx_row1_read',0xdf if key=='s' else 0xfd if key=='w' else 255)
            if key not in ('s','w'):sample('fx_row2_read',0xbf if key=='t' else 0xfd if key=='r' else 255)
            if key in ('g','b','o'):sample('fx_row3_read',0xfb if key=='g' else 0xef if key=='b' else 255)
            if key=='o':sample('fx_row4_read',0xbf)
            snapshot(key,expected)
        def release():
            stop('fx_poll');sample('v3_left_shift_read',255);sample('v3_right_shift_read',255)
            snapshot('release',{'fx_key_held':0})
        special('s',{'fx_enabled':0});special('s',{'fx_enabled':0});release()
        special('s',{'fx_enabled':1});release()
        special('t',{'fx_enabled':0,'fx_mode':0,'v3_background':1,'v3_cycle_enabled':0});release()
        special('r',{'fx_mode':2});release()
        special('g',{'fx_enabled':1,'fx_mode':3,'v3_background':0});release()
        special('r',{'fx_mode':1});release()
        special('w',{'fx_enabled':0,'fx_mode':0,'v3_background':1});release()
        special('g',{'fx_enabled':1,'fx_mode':1,'v3_background':0});release()
        meta=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text())
        if meta['presentation_modes'].get('variants'):
            special('b',{'fx_mode':4,'v3_background':0,'fx_enabled':1});release()
            special('r',{'fx_mode':5});release()
            special('o',{'fx_mode':7});release()
            special('g',{'fx_mode':3});release()
            special('o',{'fx_mode':7});release()
            special('o',{'fx_mode':3});release()
            special('b',{'fx_mode':5});release()
            special('b',{'fx_mode':3});release()
            special('r',{'fx_mode':1});release()
            special('o',{'fx_mode':6});release()
            special('w',{'fx_mode':0,'fx_enabled':0,'v3_background':1});release()
            special('g',{'fx_mode':1,'fx_enabled':1,'v3_background':0});release()
        def fkey(row,expected,shift=False,ctrl=False):
            sample('v3_row0_read',255);stop('v3_poll_return')
            sample('v3_row0_read',row)
            sample('v3_left_shift_read',0x7f if shift else 255)
            if not shift:sample('v3_right_shift_read',255)
            if row==0xf7 and not shift:sample('v3_ctrl_read',0xfb if ctrl else 255)
            snapshot('function key',expected,'v3_poll_return')
        for i in range(1,18):fkey(0xdf,{'fx_foreground':i%17})
        fkey(0xdf,{'v3_background':1},shift=True)
        fkey(0xbf,{'v3_cycle_enabled':1});fkey(0xbf,{'v3_cycle_enabled':0})
        fkey(0xbf,{'v3_cycle_rate':1},shift=True)
        fkey(0xf7,{'v3_cycle_rate':2})
        fkey(0xf7,{'v3_border_mode':0},shift=True)
        fkey(0xf7,{'v3_border_mode':2},ctrl=True)
        fkey(0xef,{'fx_mode':1,'fx_enabled':1,'fx_foreground':0,'v3_background':0},shift=True)
        # Both joystick input paths and persistent left/right direction.
        sample('v3_joy1_read',0xfb);snapshot('joystick left',{'v3_step':255},'v3_poll_return')
        sample('v3_joy1_read',0xf7);snapshot('joystick right',{'v3_step':1},'v3_poll_return')
        run_monitor(cart,vice,data,out,cmd,100_000_000)
        for i,(name,expected) in enumerate(checks):
            ram=(out/f'{i}.ram').read_bytes()
            for key,wanted in expected.items():assert ram[sym[key]]==wanted,(name,key,ram[sym[key]],wanted)
    return dict(passed=True,checks=len(checks),method='VICE monitor injects sampled CIA row values; native scanners/handlers execute',shift_s_debounce=True,shift_t_g_r=True,foreground_hues=16,function_keys=True,joystick_directions=True)

def hud_keys(cart,vice,data):
    """Exercise key handlers and verify all HUD regions in all three buffers."""
    sym=labels(cart.with_suffix('.lbl'))
    meta=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text())
    config=meta.get('hud_visibility',meta.get('interactive_cart',{}).get('hud_visibility',{}))
    assert config.get('toggle_allowed','ui_poll' in sym)
    info=bool(config['initial_info']);perf=bool(config['initial_performance'])
    label=bool(config['initial_label'])
    checks=[]
    with tempfile.TemporaryDirectory(prefix='hud-keys-') as temp:
        out=Path(temp);cmd=[]
        start='fx_poll' if 'fx_poll' in sym else 'hp_poll'
        end='fx_poll_return' if 'fx_poll' in sym else 'sp_poll_return'
        def stop(label):cmd.extend(['delete',f'break ${sym[label]:04x}','g'])
        def sample(label,value):stop(label);cmd.append(f'r a=${value:02x}')
        def snap(name,i,p,wait=False):
            stop(end)
            if wait:
                stop('v3_display_colors_done');cmd.extend(['g']*120)
            cmd.extend(['bank ram',f'bsave "{out/str(len(checks))}.ram" 0 $0000 $ffff'])
            checks.append((name,i,p,label))
        def release():
            stop(start);sample('v3_left_shift_read',255);sample('v3_right_shift_read',255);stop(end)
        def key(key,i,p,wait=False):
            nonlocal label
            if key=='u':label=i
            stop(start);sample('v3_left_shift_read',0x7f)
            sample('ui_row4_read',0xfd if key=='i' else 255)
            if key!='i':sample('ui_row2_read',0xdf if key=='f' else 255)
            if key=='u':sample('ui_row3_read',0xbf)
            snap(key,i,p,wait)
        stop('frame_draw_complete');cmd.extend(['g']*3)
        snap('initial',info,perf)
        key('i',not info,perf);key('i',not info,perf);release()
        key('i',info,perf);release()
        key('f',info,not perf);key('f',info,not perf);release()
        key('f',info,perf);release()
        # Normalize to both hidden, irrespective of startup state.
        if info or perf:key('u',False,False,wait=True);release()
        else:key('u',True,True);release();key('u',False,False,wait=True);release()
        # Speed controls and measurement continue with all bottom ink hidden.
        sample('sp_row5_read',0xfe);stop('sp_poll_return')
        snap('hidden speed+',False,False,wait=True)
        key('u',True,True);release()
        sample('sp_row5_read',255);sample('sp_row4_read',0xf7);stop('sp_poll_return')
        snap('restored',True,True,wait=True)
        run_monitor(cart,vice,data,out,cmd,100_000_000)
        from c643d.font import bitmap_text
        original=bitmap_text(f"{meta['name'].upper().replace('_',' ')} V:{meta['vertices']:03d} E:{meta['edges']:03d}",31)
        for index,(name,i,p,label_visible) in enumerate(checks):
            ram=(out/f'{index}.ram').read_bytes()
            assert ram[sym['ui_info_visible']]==i,(name,'info flag')
            assert ram[sym['ui_perf_visible']]==p,(name,'perf flag')
            assert ram[sym['ui_label_visible']]==label_visible,(name,'INTERACTIVE flag')
            assert ram[sym['v3_draw_label']]==(0xae if label_visible else 0x60),(name,'INTERACTIVE draw gate')
            assert ram[sym['render_fps_digits']]==(0xad if p else 0x60),(name,'FPS draw gate')
            assert ram[sym['sp_draw']]==(0xae if p else 0x60),(name,'message draw gate')
            for base in (0x2000,0x6000,0xe000):
                expected=original if i else bytes(len(original))
                label_ink=bitmap_text('INTERACTIVE') if label_visible else bytes(88)
                assert ram[base+232:base+320]==label_ink,(name,'INTERACTIVE pixels')
                assert ram[base+7680:base+7680+len(original)]==expected,(name,'info pixels')
                fps=ram[base+7936:base+8000]
                if p:assert any(fps),(name,'FPS not restored')
                else:
                    assert not any(fps),(name,'FPS reappeared')
                    assert not any(ram[base+7616:base+7672]),(name,'speed message reappeared')
            if name=='hidden speed+':assert ram[sym['sp_level']]==4
            if name=='restored':assert ram[sym['sp_level']]==3
    return dict(passed=True,checks=len(checks),native_key_scan=True,held_key_debounce=True,
                all_three_buffers=True,hidden_stays_hidden=True,hidden_speed_controls_work=True,
                restored_name_counts_and_fps=True,hidden_and_restored_interactive_label=True)

def speed_keys(cart,vice,data):
    from c643d.hors_v3_speed import levels
    meta=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text())
    sym=labels(cart.with_suffix('.lbl'));rates=levels(meta['presentation_modes']['samples_per_mode'])
    checks=[]
    with tempfile.TemporaryDirectory(prefix='saku-speed-keys-') as tmp:
        out=Path(tmp);cmd=[]
        def stop(name):cmd.extend(['delete',f'break ${sym[name]:04x}','g'])
        def sample(name,value):stop(name);cmd.append(f'r a=${value:02x}')
        def snapshot(level,message):
            stop('sp_poll_return');cmd.extend(['bank ram',f'bsave "{out/str(len(checks))}.ram" 0 $0000 $ffff'])
            checks.append((level,message))
        def release():
            sample('sp_row5_read',255);sample('sp_row4_read',255);stop('sp_poll_return')
        def key(which,level,message):
            sample('sp_row5_read',0xfe if which=='+' else 0xf7 if which=='-' else 255)
            if which=='0':sample('sp_row4_read',0xf7)
            snapshot(level,message)
        for level in range(4,len(rates)):
            key('+',level,5 if level==len(rates)-1 else 0);release()
        key('+',len(rates)-1,3);key('+',len(rates)-1,3);release()
        key('0',3,2);release()
        for level in (2,1,0):key('-',level,1);release()
        key('-',0,4);release();key('0',3,2);release()
        # Capture native message rendering and its expiry in every buffer.
        for name,msg in [('inc',0),('max',3),('min',4),('wow',5)]:
            stop('frame_begin')
            for label,value in [('sp_message_id',msg),('sp_ttl',50),('sp_revision',20+msg)]:cmd.append(f'> ${sym[label]:04x} ${value:02x}')
            stop('frame_draw_complete');cmd.extend(['bank ram',f'bsave "{out/name}.ram" 0 $0000 $ffff'])
        stop('frame_begin');cmd.extend([f'> ${sym['sp_ttl']:04x} $01'])
        stop('profile_published');cmd+=['g','g','g','g','bank ram',f'bsave "{out}/expired.ram" 0 $0000 $ffff']
        run_monitor(cart,vice,data,out,cmd,160_000_000)
        for i,(level,message) in enumerate(checks):
            ram=(out/f'{i}.ram').read_bytes()
            assert ram[sym['sp_level']]==level,(i,'level')
            assert ram[sym['sp_message_id']]==message,(i,'message')
        for name,label in [('inc','inc'),('max','max_text'),('min','min_text'),('wow','wow')]:
            ram=(out/f'{name}.ram').read_bytes();slot=ram[sym['render_slot']]
            bm=(0x2000,0x6000,0xe000)[slot]+7616;sc=(0x400,0x4400,0xc800)[slot]+952
            assert ram[bm:bm+56]==ram[sym['sp_'+label]:sym['sp_'+label]+56],('message pixels',name)
            allowed=(2,) if name=='min' else (1,2) if name in ('max','wow') else (1,)
            assert all(v>>4 in allowed for v in ram[sc:sc+7]),('message colour',name)
        ram=(out/'expired.ram').read_bytes()
        assert ram[sym['sp_ttl']]==0
        for base in (0x2000,0x6000,0xe000):assert not any(ram[base+7616:base+7672]),'expired message remains'
    return dict(passed=True,checks=len(checks),all_levels=True,reset=True,limit_feedback=True,held_key_debounce=True,
                message_pixels=True,red_minimum=True,white_red_maximum=True,expiry_all_buffers=True)


def instruction_costs(cart,vice,data):
    sym=labels(cart.with_suffix('.lbl'));result={}
    default_profile=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text())['background_effect']['profiles']['default']
    for name,start,end,enabled in [('stars-on','fx_irq','fx_irq_return',1),
                                    ('stars-off','fx_irq','fx_irq_disabled_return',0),
                                    ('light-stars-on','sl_irq','sl_irq_return',1),
                                    ('light-stars-off','sl_irq','sl_irq_disabled_return',0),
                                    ('speed-poll-idle','sp_poll','ex_service_gate',0),
                                    ('effects-poll-idle','fx_poll','fx_poll_return',0)]:
        with tempfile.TemporaryDirectory(prefix='saku-cycle-cost-') as tmp:
            out=Path(tmp);cmd=['delete',f'break ${sym['frame_draw_complete']:04x}','g',f'> ${sym['fx_enabled']:04x} ${enabled:02x}']
            selected_profile='light' if name.startswith('light-') else 'full'
            if selected_profile!=default_profile:
                for label,value in [('sp_row5_read',255),('sp_row4_read',255),('sd_row7_read',255),('sd_row1_read',247)]:
                    cmd+=['delete',f'break ${sym[label]:04x}','g',f'r a=${value:02x}']
                cmd+=['delete',f'break ${sym["sp_poll_return"]:04x}','g']
            for i in range(32):
                cmd+=['delete',f'break ${sym[start]:04x}','g','stopwatch','delete',f'break ${sym[end]:04x}','g','stopwatch']
            run_monitor(cart,vice,data,out,cmd,80_000_000)
            stamps=[int(t) for t in re.findall(r'Stopwatch:\s*(\d+)',(out/'monitor.log').read_text())]
            assert len(stamps)==64
            cycles=[stamps[i+1]-stamps[i]+12 for i in range(0,64,2)] # JSR + final RTS
            result[name]=dict(min_cycles=min(cycles),max_cycles=max(cycles),mean_cycles=sum(cycles)/len(cycles),samples=32,
                method='VICE stopwatch between entry and final RTS, plus JSR/RTS; elapsed machine cycles')
    return result


def mapped(value,source_bg,bg,foreground,maps):
    def nibble(v):return bg if v==source_bg else maps[(foreground-1)*16+v] if foreground else v
    return nibble(value>>4)<<4|nibble(value&15)

def pictures(cart,vice,data):
    meta=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text());sym=labels(cart.with_suffix('.lbl'))
    frames=json.loads(gzip.decompress(cart.with_name(cart.stem+'-oracle.json.gz').read_bytes()))
    n=meta['presentation_modes']['samples_per_mode'];cases=[]
    with tempfile.TemporaryDirectory(prefix='saku-pixels-') as tmp:
        out=Path(tmp);cmd=[]
        def stop(name):cmd.extend(['delete',f'break ${sym[name]:04x}','g'])
        # All geometry samples in every mode and all three physical buffers.
        # Extra rows stress the hue/background LUT without changing the pictures.
        backgrounds=meta['presentation_modes'].get('source_backgrounds',[1,0,1,0])
        sequence=[(mode,i,bg,0) for mode,bg in enumerate(backgrounds) for i in range(n)]
        sequence += [(i%len(backgrounds),i%n,i%16,1+i%16) for i in range(48)]
        for mode,i,bg,fg in sequence:
            stop('frame_begin')
            for label,v in [('fx_mode',mode),('fx_position',i),('frame_index',mode*n+i),('v3_background',bg),('fx_foreground',fg)]:
                cmd.append(f'> ${sym[label]:04x} ${v:02x}')
            stop('frame_draw_complete');cmd.extend(['bank ram',f'bsave "{out/str(len(cases))}.ram" 0 $0000 $ffff'])
            cases.append((mode,i,bg,fg))
        run_monitor(cart,vice,data,out,cmd,220_000_000)
        slots=set()
        for k,(mode,i,bg,fg) in enumerate(cases):
            ram=(out/f'{k}.ram').read_bytes();slot=ram[sym['render_slot']];slots.add(slot)
            assert ram[sym['frame_index']]==mode*n+i
            bm,sc=expected_frame(frames[mode*n+i],meta['screen_color']);apply_interactive_overlay(bm,meta)
            maps=ram[sym['fx_foreground_maps']:sym['fx_foreground_maps']+256]
            wanted=bytes(mapped(v,backgrounds[mode],bg,fg,maps) for v in sc)
            baddr,saddr=(0x2000,0x6000,0xe000)[slot],(0x400,0x4400,0xc800)[slot]
            assert ram[baddr:baddr+7680]==bm,('bitmap',k,mode,i,slot)
            assert ram[saddr:saddr+960]==wanted,('colour',k,mode,i,slot)
        assert slots=={0,1,2}
    return dict(pixel_match=True,color_match=True,frames=len(cases),all_samples=True,all_three_buffers=True,hue_and_background_combinations=48)

def capture(cart,vice,data,out,*,mode=1,stars=True,cycle=False,foreground=0,refreshes=750,gif=False,speed_level=3,hud=True,density=None,star_profile='full',exhibition=False,exhibition_cycle=False):
    from PIL import Image
    meta=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text());sym=labels(cart.with_suffix('.lbl'))
    assert star_profile in ('full','light')
    identity=sha(cart);n=meta['presentation_modes']['samples_per_mode'];points=trajectories(interactive=star_profile=='full')
    source_bg=meta['presentation_modes'].get('source_backgrounds',[1,0,1,0])[mode]
    frames=json.loads(gzip.decompress(cart.with_name(cart.stem+'-oracle.json.gz').read_bytes()))
    oracles=[]
    for f in frames:
        bm,sc=expected_frame(f,meta['screen_color'])
        if hud:apply_interactive_overlay(bm,meta)
        oracles.append((bytes(bm),bytes(sc)))
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='saku-display-') as tmp:
        tmp=Path(tmp);cmd=['delete',f'break ${sym["frame_begin"]:04x}','g']
        if star_profile!=meta['background_effect']['profiles']['default']:
            # Exercise the actual event handler; detailed keymap/debounce checks
            # live in verify_vice_host_keys.py.
            for label,value in [('sp_row5_read',255),('sp_row4_read',255),('sd_row7_read',255),('sd_row1_read',247)]:
                cmd+=['delete',f'break ${sym[label]:04x}','g',f'r a=${value:02x}']
            cmd+=['delete',f'break ${sym["sp_poll_return"]:04x}','g']
        if density is not None:
            from verify_star_density import setup_commands
            cmd += setup_commands(sym, density)
        for key,val in [('fx_mode',mode),('fx_position',0),('frame_index',mode*n),('fx_enabled',int(stars)),
                        ('sp_level',speed_level),('fx_foreground',foreground),('v3_background',source_bg),('v3_cycle_enabled',int(cycle)),('v3_cycle_interval',12)]:
            cmd.append(f'> ${sym[key]:04x} ${val:02x}')
        if not hud:
            for name,value in [('fx_poll',None),('v3_left_shift_read',0x7f),('ui_row4_read',255),('ui_row2_read',255),('ui_row3_read',0xbf)]:
                cmd+=['delete',f'break ${sym[name]:04x}','g']
                if value is not None:cmd.append(f'r a=${value:02x}')
            cmd+=['delete',f'break ${sym['fx_poll_return']:04x}','g']
        if exhibition:
            # Hold one style for the measurement to isolate scheduler overhead.
            cmd += [f'> ${sym["ex_interval"]:04x} {5 if exhibition_cycle else 60:02x}', 'delete', f'break ${sym["ex_row2_read"]:04x}', 'g', 'r a=$fe',
                    'delete',f'break ${sym["ex_service_done"]:04x}','g']
        cmd+=['delete',f'break ${sym["profile_published"]:04x}',*(['g']*6),
              'delete',f'break ${sym["v3_display_colors_done"]:04x}']
        for i in range(refreshes+1):
            cmd+=['g','stopwatch','bank ram',f'bsave "{tmp/i.__str__()}.ram" 0 $0000 $ffff',
                  'bank cpu',f'bsave "{tmp/i.__str__()}.io" 0 $d000 $d02e','bank ram']
            if gif and i%2==0:cmd.append(f'scrsh "{tmp/i.__str__()}.png" 2')
        run_monitor(cart,vice,data,tmp,cmd,150_000_000)
        ticks=[int(t) for t in re.findall(r'Stopwatch:\s*(\d+)',(tmp/'monitor.log').read_text())]
        assert len(ticks)==refreshes+1
        previous=None;flips=[];seen=set();slots=set();stars_seen=0;star_pixels=0;images=[]
        for i in range(refreshes+1):
            ram=(tmp/f'{i}.ram').read_bytes();io=(tmp/f'{i}.io').read_bytes()
            slot=ram[sym['display_slot']];fi=ram[sym['slot_frame']+slot];bg=ram[sym['v3_slot_background']+slot]
            slots.add(slot);seen.add(fi)
            assert fi//n in ((1,4,6) if exhibition_cycle else (mode,)),('unexpected mode',i,fi,mode)
            if exhibition_cycle:source_bg=meta['presentation_modes']['source_backgrounds'][fi//n]
            baddr,saddr=(0x2000,0x6000,0xe000)[slot],(0x400,0x4400,0xc800)[slot]
            bm,sc=oracles[fi];maps=ram[sym['fx_foreground_maps']:sym['fx_foreground_maps']+256]
            assert ram[baddr:baddr+7680]==bm,('visible bitmap',i)
            assert ram[saddr:saddr+960]==bytes(mapped(v,source_bg,bg,foreground,maps) for v in sc),('visible colours',i)
            assert io[0x21]&15==bg,('background register',i,bg)
            if not hud:
                assert not any(ram[baddr+7680:baddr+8000]),('hidden bottom HUD',i)
                assert not any(ram[baddr+7616:baddr+7672]),('hidden speed feedback',i)
            if previous is not None and previous!=slot:flips.append((i,ticks[i]))
            previous=slot
            if not stars:assert io[0x15]==0
            else:
                assert io[0x1b]==255
                from c643d.hors_v3_density import LEVELS, POINTS, STAR_PERIODS
                active=min(8,LEVELS[ram[sym['sd_level']]])
                assert io[0x15] & ~((1 << active) - 1) == 0
                for j in range(active):
                    phase=ram[sym['fx_phase']+j];x,y=points[j][phase]
                    width=2 if star_profile=='full' and phase>=STAR_PERIODS[j]*3//4 else 1
                    assert ram[(0x7f8,0x47f8,0xcbf8)[slot]+j]==(253 if width==2 else 254)
                    assert (io[2*j]+(256 if io[0x10]&(1<<j) else 0),io[2*j+1])==(x+24,y+50)
                    if io[0x15]&(1<<j):
                        for dx,dy in POINTS[:ram[sym['sd_dot_count']]]:
                            visible_point=False
                            for w in range(width):
                                px,py=x+dx+w,y+dy
                                assert px<256 and py<192,('star outside model viewport',i,j)
                                point_cell=(py//8)*40+px//8
                                assert ram[saddr+point_cell]&15==bg,('extra star over a filled cell',i,j,px,py)
                                if not bm[point_cell*8+(py&7)]&(128>>(px&7)):
                                    star_pixels+=1;visible_point=True
                                bounds=meta['background_effect'].get('opaque_bounds',[None]*len(frames))[fi]
                                if bounds is not None:
                                    assert not(bounds[0]<=px<=bounds[1] and bounds[2]<=py<=bounds[3]),('extra star over opaque paint',i,j)
                            stars_seen+=int(visible_point)
                        box=meta['background_effect'].get('opaque_bounds',[None]*len(frames))[fi]
                        if box is not None:
                            assert not (box[0]<=x<=box[1] and box[2]<=y<=box[3]),('star over opaque paint',i,j,fi)
                        cell=(y//8)*40+x//8
                        assert ram[saddr+cell]&15==bg,('star over a fully filled cell',i,j)
                        # VIC priority hides set bitmap pixels; visible star pixels
                        # must therefore fall on the background-valued clear bits.
            if gif and i%2==0:
                with Image.open(tmp/f'{i}.png') as im:images.append(im.convert('RGB').resize((768,544),Image.Resampling.NEAREST))
        assert slots=={0,1,2}
        step=meta['interactive_cart']['speed']['levels'][speed_level]['skip']
        if exhibition_cycle:assert {fi//n for fi in seen}=={1,4,6}
        else:assert len(seen)==n//math.gcd(n,step),(len(seen),n,step)
        if stars:assert stars_seen>0
        elapsed=ticks[-1]-ticks[0];assert abs(elapsed-refreshes*PAL)<PAL
        if gif:
            # 2 PAL refreshes per image; actual VIC screenshot includes sprites.
            target=out/('saku_2026-exhibition.gif' if exhibition_cycle else 'saku_2026-gradient-starfield.gif')
            images[0].save(target,save_all=True,append_images=images[1:],duration=40,loop=0,disposal=1,optimize=False)
            from PIL import ImageChops
            with Image.open(target) as decoded:
                cursor=0
                for k in range(decoded.n_frames):
                    decoded.seek(k)
                    duration=decoded.info['duration']
                    assert duration%40==0
                    for _ in range(duration//40):
                        assert not ImageChops.difference(decoded.convert('RGB'),images[cursor]).getbbox(),('GIF pixel mismatch',k,cursor)
                        cursor+=1
                assert cursor==len(images)
    assert sha(cart)==identity
    spans=[b[1]-a[1] for a,b in zip(flips,flips[1:])]
    return dict(mode=mode,stars=stars,star_profile=star_profile,exhibition=exhibition,exhibition_cycle=exhibition_cycle,presentations_seen=sorted({fi//n for fi in seen}),auto_cycle=cycle,foreground=foreground,speed_level=speed_level,hud_visible=hud,gif_pixels_verified=bool(gif),display_fps=len(flips)*CLOCK/elapsed,
        elapsed_cycles=elapsed,refreshes=refreshes,display_flips=len(flips),worst_display_ms=max(spans)*1000/CLOCK,
        hold_ticks=dict(Counter(b[0]-a[0] for a,b in zip(flips,flips[1:]))),orientations_seen=len(seen),
        all_three_buffers=True,visible_pixel_and_colour_match=True,visible_star_samples=stars_seen,visible_star_pixel_samples=star_pixels,
        sprite_positions_match=True,sprite_occlusion=True,cartridge_unchanged=True,
        density=__import__('c643d.hors_v3_density',fromlist=['LEVELS']).LEVELS[density if density is not None else (2 if star_profile=='light' else 3)],
        gif_source='actual PAL VICE screenshots including hardware sprites' if gif else None)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--output-dir',type=Path,default=ROOT/'build/saku-verification')
    p.add_argument('--install',action='store_true');p.add_argument('--quick',action='store_true')
    p.add_argument('--cartridge-dir',type=Path,default=HERE/'cartridges')
    a=p.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    cart=a.cartridge_dir/'saku_2026-interactive.crt'
    meta=json.loads(cart.with_name(cart.stem+'-manifest.json').read_text())
    help_result=help_keys(cart,a.vice,a.vice_data,out);print('SAKU help and startup passed',flush=True)
    result={'keys':keys(cart,a.vice,a.vice_data)};print('SAKU keys passed',flush=True)
    result['help']=help_result
    from verify_star_density import verify as density_keys
    result['density_keys']=density_keys(cart,a.vice,a.vice_data,out);print('SAKU density keys passed',flush=True)
    result['hud_keys']=hud_keys(cart,a.vice,a.vice_data);print('SAKU HUD switches passed',flush=True)
    result['speed_keys']=speed_keys(cart,a.vice,a.vice_data);print('SAKU speed keys passed',flush=True)
    result['pictures']=pictures(cart,a.vice,a.vice_data);print('SAKU all-mode pictures passed',flush=True)
    result['instruction_costs']=instruction_costs(cart,a.vice,a.vice_data)
    result['measurements']={}
    cases=[('gradient-stars',1,True,False,0),('gradient-no-stars',1,False,False,0),
           ('solid-no-stars',0,False,False,0),('solid-stars',0,True,False,0),
           ('gradient-crawl-stars',3,True,False,0),('solid-crawl',2,False,False,0),
           ('gradient-stars-cycle',1,True,True,0),('gradient-stars-hue',1,True,False,8)]
    cases += [(name,mode,True,False,0) for mode,name in enumerate(meta['presentation_modes']['modes']) if mode>=4]
    for name,mode,stars,cycle,fg in cases[:1] if a.quick else cases:
        row=capture(cart,a.vice,a.vice_data,out,mode=mode,stars=stars,cycle=cycle,foreground=fg,
                    gif=name=='gradient-stars',refreshes=750)
        result['measurements'][name]=row;print(name,row['display_fps'],flush=True)
    if not a.quick:
        for name,mode in [('gradient-light-stars',1),('card-light-stars',4),('crawl-light-stars',3),('outline-light-stars',6),('outline-crawl-light-stars',7)]:
            result['measurements'][name]=capture(cart,a.vice,a.vice_data,out/name,mode=mode,
                star_profile='light',gif=mode==1)
            print(name,result['measurements'][name]['display_fps'],flush=True)
        from c643d.hors_v3_speed import levels
        for name,level in [('slowest',0),('fastest',len(levels(meta['presentation_modes']['samples_per_mode']))-1)]:
            result['measurements'][name]=capture(cart,a.vice,a.vice_data,out,speed_level=level,refreshes=2500 if level==0 else 750)
            print(name,result['measurements'][name]['display_fps'],flush=True)
        for name,stars in [('gradient-stars-hud-hidden',True),('gradient-no-stars-hud-hidden',False)]:
            result['measurements'][name]=capture(cart,a.vice,a.vice_data,out,stars=stars,hud=False)
            print(name,result['measurements'][name]['display_fps'],flush=True)
        result['measurements']['gradient-exhibition-active']=capture(cart,a.vice,a.vice_data,out,stars=False,hud=False,exhibition=True)
        print('gradient-exhibition-active',result['measurements']['gradient-exhibition-active']['display_fps'],flush=True)
        result['measurements']['exhibition-tour']=capture(cart,a.vice,a.vice_data,out,stars=False,hud=False,exhibition=True,exhibition_cycle=True,gif=True,refreshes=800)
        print('exhibition-tour',result['measurements']['exhibition-tour']['display_fps'],flush=True)
        for level in (0,2,5):
            result['measurements']['gradient-stars-density-'+str((2,4,8,16,24,32)[level])]=capture(cart,a.vice,a.vice_data,out,density=level)
        result['plain']={} 
        for style in ('solid','gradient'):
            plain=a.cartridge_dir/f'saku_2026-{style}.crt'
            with tempfile.TemporaryDirectory() as tmp:
                oracle=Path(tmp)/'oracle.json';oracle.write_bytes(gzip.decompress(plain.with_name(plain.stem+'-oracle.json.gz').read_bytes()))
                result['plain'][style]=verify(plain,a.vice,a.vice_data,oracle_path=oracle)
    result.update(default_star_profile=meta['background_effect']['profiles']['default'],presentation_modes=meta['presentation_modes'],passed=True,pal_vice=True,physical_hardware_tested=False,cartridge_sha256=sha(cart))
    dump(out/'results.json',result)
    if a.install:
        if a.quick:p.error('--install requires the full measurements')
        (HERE/'previews').mkdir(exist_ok=True);(HERE/'evidence').mkdir(exist_ok=True)
        shutil.copy2(out/'saku_2026-gradient-starfield.gif',HERE/'previews/saku_2026-gradient-starfield.gif')
        shutil.copy2(out/'gradient-light-stars/saku_2026-gradient-starfield.gif',HERE/'previews/saku_2026-light-starfield.gif')
        shutil.copy2(out/'saku_2026-exhibition.gif',HERE/'previews/saku_2026-exhibition.gif')
        shutil.copy2(out/'saku_2026-help.png',HERE/'previews/saku_2026-help.png')
        shutil.copy2(out/'results.json',HERE/'evidence/results.json')
        files=[ROOT/'VERSION',*HERE.rglob('*'),*(ROOT/'tools').rglob('*'),*(ROOT/'c64').rglob('*')]
        hashes={p.relative_to(ROOT).as_posix():sha(p) for p in files if p.is_file() and p.suffix not in ('.md','.pyc') and p.name!='validation.json' and '__pycache__' not in p.parts}
        dump(HERE/'validation.json',dict(version=(ROOT/'VERSION').read_text().strip(),passed=True,sha256=hashes))

if __name__=='__main__':main()
