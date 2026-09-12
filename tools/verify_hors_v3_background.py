#!/usr/bin/env python3
"""Check black-only remapping, palette keys and actual PAL display performance."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile
from verify_cart_stream import labels, expected_frame, apply_interactive_overlay, render_ram
from verify_color_combos import run_monitor
from c643d.font import bitmap_text

CLOCK=985248
PAL_CYCLES=19656

def remap(value, background):
    return ((background if value >> 4 == 0 else value >> 4) << 4) | (background if value & 15 == 0 else value & 15)


def source_pictures(crt, oracle):
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    sym=labels(crt.with_suffix('.lbl'))
    pictures=[]
    for frame in json.loads(oracle.read_text()):
        bitmap, colors=expected_frame(frame,meta['screen_color'])
        apply_interactive_overlay(bitmap,meta)
        pictures.append((bytes(bitmap),bytes(colors)))
    return meta,sym,pictures


def verify_keys(crt, oracle, vice, data):
    meta,sym,pictures=source_pictures(crt,oracle)
    checks=[]
    state=dict(v3_background=0,v3_cycle_enabled=0,v3_cycle_rate=2,v3_cycle_interval=50,v3_border_mode=1)
    with tempfile.TemporaryDirectory(prefix='hors-v3-background-keys-') as td:
        td=Path(td);commands=[]
        def stop(label):commands.extend(['delete',f'break ${sym[label]:04x}','g'])
        def sample(label,value):stop(label);commands.append(f'r a=${value:02x}')
        def snapshot(name):
            stop('v3_poll_return')
            commands.extend(['bank ram',f'bsave "{td/str(len(checks))}.ram" 0 $0000 $ffff',
                'bank cpu',f'bsave "{td/str(len(checks))}.cia" 0 $dc02 $dc03','bank ram'])
            checks.append((name,dict(state)))
        def release():sample('v3_row0_read',255);snapshot('release')
        def key(row,shift=False,ctrl=False,name='',changes=None,held=False):
            sample('v3_row0_read',row)
            if not held:
                sample('v3_left_shift_read',0x7f if shift else 255)
                if not shift:sample('v3_right_shift_read',255)
                if row==0xf7 and not shift:sample('v3_ctrl_read',0xfb if ctrl else 255)
            state.update(changes or {});snapshot(name)
        key(0xdf,True,name='F4',changes={'v3_background':1})
        key(0xdf,True,name='held F4 is one event',held=True)
        release()
        key(0xdf,name='F3 leaves shades and background alone');release()
        key(0xdf,True,name='F4 again',changes={'v3_background':2});release()
        key(0xf7,True,name='F8 locks black',changes={'v3_border_mode':0});release()
        key(0xdf,True,name='F4 retains black lock',changes={'v3_background':3});release()
        key(0xf7,True,name='F8 resumes follow',changes={'v3_border_mode':1});release()
        key(0xf7,ctrl=True,name='Ctrl+F7 custom border',changes={'v3_border_mode':2});release()
        key(0xdf,True,name='F4 retains custom mode',changes={'v3_background':4});release()
        key(0xf7,True,name='F8 resumes follow from custom',changes={'v3_border_mode':1});release()
        for i in range(3):
            rate=max(0,state['v3_cycle_rate']-1)
            key(0xbf,True,name='F6 slower/clamp',changes={'v3_cycle_rate':rate,'v3_cycle_interval':[200,100,50][rate]});release()
        rates=[200,100,50,25,12,6,3,1]
        for i in range(8):
            rate=min(7,state['v3_cycle_rate']+1)
            key(0xf7,name='F7 faster/clamp',changes={'v3_cycle_rate':rate,'v3_cycle_interval':rates[rate]});release()
        # Reset to one-second timing before toggling, so no timer event can
        # interfere with these deliberately short key-state assertions.
        key(0xef,True,name='F2 reset',changes={'v3_background':0,'v3_cycle_enabled':0,'v3_cycle_rate':2,'v3_cycle_interval':50,'v3_border_mode':1});release()
        key(0xbf,name='F5 start',changes={'v3_cycle_enabled':1});release()
        key(0xbf,name='F5 stop',changes={'v3_cycle_enabled':0});release()
        run_monitor(str(crt),vice,data,td,commands,180_000_000)
        for i,(name,wanted) in enumerate(checks):
            ram=(td/f'{i}.ram').read_bytes()
            for label,value in wanted.items():assert ram[sym[label]]==value,(name,label,ram[sym[label]],value)
            assert (td/f'{i}.cia').read_bytes()==bytes([255,0]),('CIA restore',name)
    return dict(passed=True,input_checks=len(checks),f4_debounced=True,f3_unchanged=True,
                f5_start_stop=True,f6_f7_rates_and_clamps=True,f8_follow_black=True,
                ctrl_f7_custom=True,f2_reset=True)


def verify_palette(crt, oracle, vice, data):
    meta,sym,pictures=source_pictures(crt,oracle)
    # Every palette colour, changes each sample, reverse/forward wrap, all slots.
    sequence=[(i%16,1 if (i//16)%2 else 255,i%3,(i*3)%16) for i in range(len(pictures)*2+16)]
    with tempfile.TemporaryDirectory(prefix='hors-v3-palette-') as td:
        td=Path(td);commands=[]
        for i,(bg,step,mode,custom) in enumerate(sequence):
            commands.extend(['delete',f'break ${sym["frame_begin"]:04x}','g',
                f'> ${sym["v3_background"]:04x} ${bg:02x}',f'> ${sym["v3_step"]:04x} ${step:02x}',
                f'> ${sym["v3_border_mode"]:04x} ${mode:02x}',f'> ${sym["v3_custom_border"]:04x} ${custom:02x}',
                'delete',f'break ${sym["frame_draw_complete"]:04x}','g','bank ram',
                f'bsave "{td/str(i)}.ram" 0 $0000 $ffff',
                'delete',f'break ${sym["v3_display_colors_done"]:04x}','g','bank ram',
                f'bsave "{td/str(i)}-visible.ram" 0 $0000 $ffff',
                'bank cpu',f'bsave "{td/str(i)}-visible.io" 0 $d000 $d021','bank ram'])
        # F2 white flash does not recolour the object's stored surface.
        commands.extend([f'> ${sym["v3_flash_ticks"]:04x} $05','delete',f'break ${sym["v3_flash_done"]:04x}'])
        for i in range(5):
            commands.extend(['g','bank cpu',f'bsave "{td/f"flash-{i}.io"}" 0 $d000 $d021','bank ram'])
        commands.extend(['delete',f'break ${sym["v3_display_colors_done"]:04x}','g','bank cpu',f'bsave "{td/"restored.io"}" 0 $d000 $d021','bank ram'])
        run_monitor(str(crt),vice,data,td,commands,350_000_000)
        seen=set();slots=set()
        for i,(bg,step,mode,custom) in enumerate(sequence):
            ram=(td/f'{i}.ram').read_bytes();slot=ram[sym['render_slot']];index=ram[sym['frame_index']]
            baddr,saddr=(0x2000,0x6000,0xe000)[slot],(0x400,0x4400,0xc800)[slot]
            bitmap,colors=pictures[index]
            wanted=bytes(remap(v,bg) for v in colors)
            assert ram[baddr:baddr+7680]==bitmap,('bitmap',i,index,slot)
            assert ram[saddr:saddr+960]==wanted,('black-only remap',i,index,slot)
            assert ram[sym['v3_slot_background']+slot]==bg
            assert ram[sym['v3_slot_border']+slot]==(bg if mode==1 else custom if mode==2 else 0)
            assert ram[saddr+960:saddr+1000]==bytes([remap(meta['screen_color'],bg)])*40,('HUD background',i)
            assert ram[0x200:0x300]==bytes(remap(v,bg) for v in range(256)),('lookup',i)
            visible=(td/f'{i}-visible.ram').read_bytes();io=(td/f'{i}-visible.io').read_bytes()
            ds=visible[sym['display_slot']]
            assert (io[0x20]&15,io[0x21]&15)==(visible[sym['v3_slot_border']+ds],visible[sym['v3_slot_background']+ds]),('visible border lock/custom/follow',i)
            seen.add(bg);slots.add(slot)
        for i in range(5):
            io=(td/f'flash-{i}.io').read_bytes()
            assert (io[0x20]&15,io[0x21]&15)==(1,1) and not io[0x11]&16,('flash',i)
        assert (td/'restored.io').read_bytes()[0x11]&16,'display restored'
        assert seen==set(range(16)) and slots=={0,1,2}
    return dict(passed=True,pictures_checked=len(sequence),all_16_colors=True,all_three_buffers=True,
                nonblack_colors_preserved=True,bitmap_unchanged=True,hud_background=True,
                border_modes=True,visible_border_matches_buffer=True,all_256_lookup_values=True,f2_five_tick_white_flash=True)


def measure_background(crt, oracle, vice, data, background=6, cycle_ticks=None, refreshes=1504, capture=None):
    meta,sym,pictures=source_pictures(crt,oracle)
    digest=hashlib.sha256(crt.read_bytes()).hexdigest()
    hud=bitmap_text(f"{meta['name'].upper().replace('_',' ')} V:{meta['vertices']:03d} E:{meta['edges']:03d}",31)
    with tempfile.TemporaryDirectory(prefix='hors-v3-background-perf-') as td:
        td=Path(td);warmup=meta['frames']+6
        commands=['delete',f'break ${sym["profile_published"]:04x}','g',*(['g']*(warmup-1)),
                  f'> ${sym["v3_background"]:04x} ${background:02x}']
        if cycle_ticks:
            commands.extend([f'> ${sym["v3_cycle_enabled"]:04x} $01',f'> ${sym["v3_cycle_interval"]:04x} ${cycle_ticks:02x}'])
        commands.extend(['g']*5)
        commands.extend(['delete',f'break ${sym["v3_display_colors_done"]:04x}'])
        for i in range(refreshes+1):
            commands.extend(['g','stopwatch','bank ram',f'bsave "{td/f"{i}.ram"}" 0 $0000 $ffff',
                'bank cpu',f'bsave "{td/f"{i}.io"}" 0 $d000 $d021','bank ram'])
        run_monitor(str(crt),vice,data,td,commands,230_000_000)
        ticks=[int(v) for v in re.findall(r'Stopwatch:\s*(\d+)',(td/'monitor.log').read_text())]
        assert len(ticks)==refreshes+1
        previous=None;previous_bg=None;switches=[];changes=[];seen=set()
        for i in range(refreshes+1):
            ram=(td/f'{i}.ram').read_bytes();io=(td/f'{i}.io').read_bytes()
            slot=ram[sym['display_slot']];index=ram[sym['slot_frame']+slot]
            bg=ram[sym['v3_slot_background']+slot];border=ram[sym['v3_slot_border']+slot]
            baddr,saddr=(0x2000,0x6000,0xe000)[slot],(0x400,0x4400,0xc800)[slot]
            bitmap,colors=pictures[index]
            assert ram[baddr:baddr+7680]==bitmap,('visible bitmap',i)
            assert ram[saddr:saddr+960]==bytes(remap(v,bg) for v in colors),('visible colours',i)
            assert (io[0x20]&15,io[0x21]&15)==(border,bg)==(bg,bg),('border synchronization',i)
            assert ram[baddr+7680:baddr+7680+len(hud)]==hud,('HUD',i)
            if i and previous!=slot:switches.append((i,ticks[i]))
            if previous_bg is not None and previous_bg!=bg:changes.append(ticks[i])
            previous=slot;previous_bg=bg;seen.add(index)
            if capture and i==100:
                from PIL import Image,ImageOps
                from c643d.colors import C64_PALETTE
                rgb=next(rgb for code,rgb in C64_PALETTE.values() if code==border)
                image=ImageOps.expand(render_ram(ram,slot),border=16,fill=rgb)
                Path(capture).parent.mkdir(parents=True,exist_ok=True)
                image.resize((704,464),Image.Resampling.NEAREST).save(capture)
        elapsed=ticks[-1]-ticks[0]
        assert seen==set(range(len(pictures))),('orientation coverage',len(seen))
        assert abs(elapsed-refreshes*PAL_CYCLES)<PAL_CYCLES
        intervals=[b[1]-a[1] for a,b in zip(switches,switches[1:])]
        if cycle_ticks:assert len(changes)>10,'cycling not active'
        assert hashlib.sha256(crt.read_bytes()).hexdigest()==digest
    return dict(sha256=digest,clock_hz=CLOCK,refreshes=refreshes,display_flips=len(switches),
        elapsed_cycles=elapsed,display_fps=len(switches)*CLOCK/elapsed,
        worst_display_ms=max(intervals)*1000/CLOCK,
        hold_ticks=dict(Counter(b[0]-a[0] for a,b in zip(switches,switches[1:]))),
        cycle_period_pal_ticks=cycle_ticks,initial_background=background,observed_palette_changes=len(changes),
        unique_pictures_observed=len(seen),picture_coverage_complete=True,pixel_match=True,color_match=True,
        nonblack_colors_preserved=True,border_background_match=True,hud_match=True,
        cycle_mean_seconds=(changes[-1]-changes[0])/CLOCK/(len(changes)-1) if len(changes)>1 else None)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--crt',type=Path,required=True);p.add_argument('--oracle',type=Path,required=True)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--capture',type=Path)
    a=p.parse_args();crt=a.crt.resolve();oracle=a.oracle.resolve()
    result=dict(sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),keys=verify_keys(crt,oracle,a.vice,a.vice_data))
    print('Background keys passed',flush=True)
    result['palette']=verify_palette(crt,oracle,a.vice,a.vice_data)
    print('Palette and flash passed',flush=True)
    result['measurements']={}
    for name,cycle in [('steady',None),('auto-50',50),('auto-1',1)]:
        result['measurements'][name]=measure_background(crt,oracle,a.vice,a.vice_data,cycle_ticks=cycle,capture=a.capture if name=='steady' else None)
        print(name,result['measurements'][name]['display_fps'],flush=True)
    result['passed']=True;a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
