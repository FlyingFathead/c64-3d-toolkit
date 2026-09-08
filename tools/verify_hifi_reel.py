#!/usr/bin/env python3
"""Execute HiFi presentation transitions and PAL timers in production cartridges."""
import argparse,hashlib,json,re,subprocess,tempfile
from pathlib import Path
from c643d.cartpaths import menu_manifest_path
from verify_cart_stream import labels


def verify(crt,vice,vice_data):
    root=Path(__file__).resolve().parents[1];crt=Path(crt).resolve()
    meta=json.loads(menu_manifest_path(crt).read_text());style=meta['menu_style'];separate=bool(meta.get('reel'))
    work=root/'build'/f'{crt.stem}-cartridge-demo'
    m=labels(work/f'{crt.stem}-runtime-{style}.lbl');c=labels(work/f'{crt.stem}-control.lbl')
    with tempfile.TemporaryDirectory(prefix='c64-hifi-') as tmp:
        out=Path(tmp);commands=[];intervals=[]
        def stop(addr,start=None):
            commands.extend(['delete',f'break ${addr:04x}','g' if start is None else f'g ${start:04x}'])
        def dump(name):commands.extend(['bank ram',f'bsave "{out/name}.ram" 0 $0000 $ffff'])
        def clock():commands.append('stopwatch')
        stop(m['build_screen_visible']);dump('title')
        if separate:
            sym=labels(root/meta['streamed_entries'][0]['work']/'runtime.lbl')
            stop(sym['frame_begin'],m['build_screen_done']);clock()
            stop(sym['reel_scene_complete']);clock();dump('scene-end');intervals.append('complete-scene')
            order=[1,2]
        else:
            stop(m['menu_wait_key'],m['build_screen_done'])
            # F4 is SHIFT+F3: inject the sampled row and shift result, leaving
            # scanner, dispatch and release handling to real cartridge code.
            stop(m['scan_menu_row_read']);commands.append('r a=$df')
            stop(m['scan_shift_pressed'])
            stop(m['menu_hifi'],m['scan_shift_yes'])
            order=meta['hifi_reel']['entries']
        for i in order:
            stop(m['play_all_count']);clock();dump(f'start-{i}')
            stop(c['cart_control_auto_next']);clock();dump(f'end-{i}');intervals.append(f'entry-{i}')
        stop(m['play_all_thanks_visible']);clock();dump('thanks')
        stop(m['play_all_thanks_timeout']);clock();intervals.append('thanks')
        if not separate:
            stop(m['build_screen_visible']);clock()
            stop(m['build_screen_done']);clock();intervals.append('title')
            stop(m['play_all_count']);dump('loop')
            commands.append('> $02fb $00')
            stop(m['menu_wait_key'],c['control_menu_key']);dump('exit')
        else:
            stop(sym['frame_begin']);dump('loop')
        commands.append('quit');(out/'run.mon').write_text('\n'.join(commands)+'\n')
        cmd=[vice,'-console','-default','-pal','+sound','-warp','-seed','1','+easyflashcrtwrite',
             '-directory',str(vice_data),'-cartcrt',str(crt),'-initbreak','reset',
             '-moncommands',str(out/'run.mon'),'-monlog','-monlogname',str(out/'monitor.log'),
             '-limitcycles','100000000']
        with (out/'vice.log').open('w') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
        log=(out/'monitor.log').read_text();times=[int(x) for x in re.findall(r'Stopwatch:\s*(\d+)',log)]
        assert len(times)==2*len(intervals),log[-3000:]
        measured={name:times[i*2+1]-times[i*2] for i,name in enumerate(intervals)}
        for name,cycles in measured.items():
            if name!='complete-scene':assert abs(cycles-500*19656)<45000,(name,cycles)
        for i in order:
            ram=(out/f'start-{i}.ram').read_bytes()
            assert ram[0x02fa]==i and ram[0x02fd:0x300]==bytes((2,50,10)),(i,ram[0x2fa:0x300])
        loop=(out/'loop.ram').read_bytes()
        assert loop[0x02fa]==(0 if separate else order[0])
        if separate:
            last=(out/'scene-end.ram').read_bytes()
            assert last[sym['slot_frame']+last[sym['display_slot']]]==meta['reel']['scene_frames']-1
            assert last[sym['reel_hold']]==0
        else:
            assert loop[0x02f7]==2
            exit_ram=(out/'exit.ram').read_bytes();assert exit_ram[0x02f7]==exit_ram[0x02fd]==0
        from c643d.buildscreen import screen_codes
        thanks=(out/'thanks.ram').read_bytes()
        assert bytes(screen_codes('THANK YOU FOR WATCHING')) in thanks[0x400:0x800]
        assert bytes(screen_codes('0.7.1')) in thanks[0x400:0x800]
    return dict(cartridge=crt.name,sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),
                separate=separate,order=order,cycles=measured,loop=True,thanks=True,
                method='PAL VICE production code; monitor acknowledges initial SPACE and injects F4 scanner samples')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--report',type=Path);a=p.parse_args();result=verify(a.crt,a.vice,a.vice_data)
    text=json.dumps(result,indent=2)+'\n';print(text)
    if a.report:a.report.write_text(text)
