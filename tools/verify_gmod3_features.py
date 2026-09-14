#!/usr/bin/env python3
"""Exercise collection controls and SAKU pictures/sprites through real PAL VICE."""
import argparse
import hashlib
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

from verify_gmod3_collection import ROOT,labels,run_monitor,launch
from c643d.gmod3_catalog import frames_for


def controls(crt,meta,vice,data,out):
    entry=meta['entries'][0];sym=labels(crt.parent/entry['labels']);menu=labels(crt.parent/meta['collection_labels'])
    with tempfile.TemporaryDirectory(prefix='gmod3-controls-') as td:
        tmp=Path(td);cmd=['delete',f'break ${menu["menu_poll"]:04x}','g','delete','z 4000',
            f'scrsh "{out}/menu.png" 2','bank ram',f'bsave "{tmp}/menu.ram" 0 $0000 $ffff']
        def stop(addr):cmd.extend(['delete',f'break ${addr:04x}','g'])
        def sample(label,value):stop(sym[label]);cmd.append(f'r a=${value:02x}')
        def snap(name):cmd.extend(['bank ram',f'bsave "{tmp}/{name}.ram" 0 $0000 $ffff'])
        # SPACE is sampled by the actual menu scanner; normal release launches.
        stop(menu['menu_space_read']);cmd.append('r a=$ef');stop(menu['menu_space_release'])
        stop(sym['frame_begin']);snap('startup')
        checks=[]
        def release():
            stop(sym['fx_poll']);sample('v3_left_shift_read',255);sample('v3_right_shift_read',255)
            stop(sym['fx_poll_return'])
        def special(key,expected):
            release();stop(sym['fx_poll']);sample('v3_left_shift_read',127)
            sample('fx_row1_read',0xdf if key=='s' else 0xfd if key=='w' else 255)
            if key not in ('s','w'):sample('fx_row2_read',0xbf if key=='t' else 0xfd if key=='r' else 255)
            if key in ('g','b','o'):sample('fx_row3_read',0xfb if key=='g' else 0xef if key=='b' else 255)
            if key=='o':sample('fx_row4_read',0xbf)
            stop(sym['fx_poll_return']);name=f'key-{len(checks)}';snap(name);checks.append((name,expected))
        for key,expected in [('s',{'fx_enabled':1}),('s',{'fx_enabled':0}),
            ('t',{'fx_mode':0,'v3_background':1,'fx_enabled':0}),('r',{'fx_mode':2}),
            ('g',{'fx_mode':3,'fx_enabled':1}),('b',{'fx_mode':5}),('o',{'fx_mode':7}),
            ('r',{'fx_mode':6}),('w',{'fx_mode':0,'fx_enabled':0})]:special(key,expected)
        # F2 resets presentation and leaves stars OFF.
        sample('v3_row0_read',255);stop(sym['v3_poll_return'])
        sample('v3_row0_read',0xef);sample('v3_left_shift_read',127)
        stop(sym['v3_poll_return']);snap('reset')
        # Help opens through Shift+H, freezes all three pictures, then restores.
        release();stop(sym['fx_poll']);sample('v3_left_shift_read',127);sample('hp_h_read',0xdf)
        stop(sym['hp_save']);snap('before-help');stop(sym['hp_wait']);snap('help')
        cmd+=['delete','z 4000'];snap('paused-help');cmd.append(f'scrsh "{out}/help.png" 2')
        sample('hp_space_read',0xef);stop(sym['hp_restored']);snap('after-help')
        # F1 returns to the collection. Launch Dragon, use C, N and P handlers.
        sample('v3_row0_read',255);stop(sym['v3_poll_return'])
        sample('v3_row0_read',0xef);sample('v3_left_shift_read',255);sample('v3_right_shift_read',255)
        stop(menu['menu_poll']);snap('returned-menu')
        cmd+=['> $0330 01','delete',f'break ${menu["collection_poll"]:04x}',f'g ${menu["collection_start"]:04x}']
        for label,value,wanted in [('collection_c_read',0xef,2),('collection_n_read',0x7f,3),('collection_p_read',0xfd,2)]:
            # One idle native poll releases the shared key latch.
            stop(menu['collection_poll_done']);stop(menu['collection_poll_done'])
            stop(menu[label]);cmd.append(f'r a=${value:02x}')
            stop(menu['collection_poll']);snap(f'nav-{wanted}-{label}')
            checks.append((f'nav-{wanted}-{label}',{'selected':wanted}))
        # RUN/STOP returns to the menu both during playback and inside help.
        cmd+=['> $0330 00','delete',f'break ${sym["frame_begin"]:04x}',f'g ${menu["collection_start"]:04x}']
        sample('sd_row7_read',0x7f)
        stop(menu['menu_poll']);snap('stop-menu')
        cmd+=['delete',f'break ${sym["frame_begin"]:04x}',f'g ${menu["collection_start"]:04x}']
        release();stop(sym['fx_poll']);sample('v3_left_shift_read',127);sample('hp_h_read',0xdf)
        stop(sym['hp_wait']);sample('hp_space_read',0x7f)
        stop(menu['menu_poll']);snap('stop-help-menu')
        run_monitor(crt,vice,data,tmp,cmd,180_000_000)
        startup=(tmp/'startup.ram').read_bytes();assert startup[sym['fx_enabled']]==0
        assert (tmp/'reset.ram').read_bytes()[sym['fx_enabled']]==0
        for name,expected in checks:
            ram=(tmp/(name+'.ram')).read_bytes()
            for key,value in expected.items():assert ram[0x330 if key=='selected' else sym[key]]==value,(name,key,value)
        before=(tmp/'before-help.ram').read_bytes();after=(tmp/'after-help.ram').read_bytes();paused=(tmp/'paused-help.ram').read_bytes()
        for base,size in [(0x2000,8000),(0x6000,8000),(0xe000,8000),(0x400,1024),(0x4400,1024),(0xc800,1024)]:
            assert before[base:base+size]==after[base:base+size]==paused[base:base+size]
        from c643d.buildscreen import screen_codes
        menu_ram=(tmp/'menu.ram').read_bytes()
        for row,text in [(22,'cart type: GMod3'),(23,f'used: {meta["used_kib"]} KiB | free: {meta["free_kib"]} KiB')]:
            assert menu_ram[0x400+row*40:0x400+(row+1)*40]==bytes(screen_codes(text.center(40)))
        for name in ('returned-menu','stop-menu','stop-help-menu'):
            assert (tmp/(name+'.ram')).read_bytes()[0x400:0x450]==menu_ram[0x400:0x450]
    return dict(passed=True,space_start=True,stars_off_at_boot_and_reset=True,SAKU_modes=True,
        help_freezes_and_restores_three_buffers=True,F1_menu=True,RUN_STOP_menu=True,RUN_STOP_from_help_menu=True,Dragon_shading=True,next_previous=True,centered_capacity=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/benchmarks/gmod3-features')
    a=p.parse_args();crt=a.crt.resolve();a.output.mkdir(parents=True,exist_ok=True)
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text());entry=meta['entries'][0]
    results={'crt_sha256':hashlib.sha256(crt.read_bytes()).hexdigest(),
        'controls':controls(crt,meta,a.vice,a.vice_data,a.output)}
    # Reuse the existing independent SAKU oracle and sprite checks unchanged.
    spec=importlib.util.spec_from_file_location('saku_verification',ROOT/'examples/saku_2026/verify.py')
    saku=importlib.util.module_from_spec(spec);spec.loader.exec_module(saku)
    sym=labels(crt.parent/entry['labels']);menu=labels(crt.parent/meta['collection_labels'])
    def monitor(alias,vice,data,out,commands,limit,**unused):
        return run_monitor(crt,vice,data,out,launch(meta,menu,entry,sym)+commands,limit)
    saku.run_monitor=monitor
    with tempfile.TemporaryDirectory(prefix='gmod3-saku-reference-') as td:
        alias=Path(td)/'saku.crt';alias.symlink_to(crt)
        shutil.copyfile(crt.parent/entry['labels'],alias.with_suffix('.lbl'))
        reference=dict(entry['runtime'],name=entry['runtime'].get('hud_name',entry['name'][:10]))
        alias.with_name('saku-manifest.json').write_text(json.dumps(reference))
        shutil.copyfile(ROOT/'build/gmod3-catalog'/entry['oracle'],alias.with_name('saku-oracle.json.gz'))
        for name in ('pictures','hud_keys','speed_keys'):
            print('Checking',name,flush=True);results[name]=getattr(saku,name)(alias,a.vice,a.vice_data)
        for profile in ('light','full'):
            print('Checking',profile,'starfield',flush=True)
            results[profile]=saku.capture(alias,a.vice,a.vice_data,a.output/profile,refreshes=400,
                star_profile=profile,stars=True,gif=profile=='light')
        print('Checking exhibition',flush=True)
        results['exhibition']=saku.capture(alias,a.vice,a.vice_data,a.output/'exhibition',refreshes=900,
            star_profile='light',stars=False,hud=False,exhibition=True,exhibition_cycle=True)
    (a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS collection controls, SAKU modes, HUD, speed, sprites and exhibition',flush=True)

if __name__=='__main__':main()
