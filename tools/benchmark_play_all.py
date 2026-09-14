#!/usr/bin/env python3
"""A/B throughput measurement using ONLY normal PLAY ALL, never F5.

Traces the unmodified production cartridge. Counts actual VIC buffer flips and
logical sample publications during matching normal PLAY ALL observation windows.
Requires symbols/oracles from a matching build. Emulator wall time is irrelevant.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess
import tempfile
from c643d.cartpaths import menu_manifest_path
from verify_cart_stream import labels, startup_monitor

CLOCK = 985248


def benchmark(crt, vice, vice_data, loops=3):
    if not 1 <= loops <= 20:
        raise ValueError('loops must be 1..20')
    root=Path(__file__).resolve().parents[1];crt=Path(crt).resolve()
    meta=json.loads(menu_manifest_path(crt).read_text())
    if 'play_all' not in meta or not meta.get('uniform_renderer'):
        raise ValueError('requires a uniform cartridge with normal PLAY ALL')
    seconds=meta['play_all']['seconds'];entries=meta['streamed_entries']
    work=root/'build'/f'{crt.stem}-cartridge-demo'
    menu=labels(work/f'{crt.stem}-runtime-{meta["menu_style"]}.lbl')
    syms=[labels(root/e['work']/'runtime.lbl') for e in entries]
    for e,s in zip(entries,syms):
        # The five bytes preceding irq_no_flip clear ready_slot only after an
        # actual display-bank flip. This assertion also supports older runtimes.
        prg=(root/e['work']/'runtime.prg').read_bytes();load=int.from_bytes(prg[:2],'little')
        i=s['irq_no_flip']-5-load+2
        assert prg[i:i+5] == bytes((0xa9,255,0x8d,s['ready_slot']&255,s['ready_slot']>>8))
    with tempfile.TemporaryDirectory(prefix='c643d-play-all-benchmark-') as tmp:
        tmp=Path(tmp)
        startup,first_go=startup_monitor(meta,menu)
        commands=['delete',*startup,f'break ${menu["menu_wait_key"]:04x}',first_go]
        for i in range(len(entries)*loops):
            s=syms[i%len(entries)]
            commands+=['delete',f'break ${menu["play_all_count"]:04x}',f'g ${menu["menu_launch"]:04x}' if i==0 else 'g',
                       'bank ram',f'bsave "{tmp/f"state-{i}.bin"}" 0 $02f7 $02ff','bank cpu','delete']
            for key in ('profile_recycle','frame_draw_complete','profile_published'):
                commands.append(f'trace exec ${s[key]:04x}')
            commands += [f'trace exec ${s["irq_no_flip"]-5:04x}','break $0206','g']
        commands+=['quit'];(tmp/'run.mon').write_text('\n'.join(commands)+'\n')
        cmd=[vice,'-default','-console','+easyflashcrtwrite','-pal','+sound','-warp','-seed','1','-jamaction','2',
             '-directory',str(vice_data),'-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(tmp/'run.mon'),
             # Keep the per-entry load/startup margin. Even a one-entry cart
             # also needs the ten-second thank-you screen between loops.
             '-monlogname', str(tmp/'monitor.log'), '-monlog','-limitcycles',str((((seconds+6)*len(entries)+12)*loops+5)*1000000)]
        with (tmp/'vice.log').open('w') as log:
            subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=max(120,loops*90))
        events=[(int(m[0],16),int(m[1])) for m in re.findall(r'^\.C:([0-9a-fA-F]{4})\s.*?\s(\d+)\s*$',(tmp/'monitor.log').read_text(),re.M)]
        windows=[];current=None
        for addr,clock in events:
            if addr==menu['play_all_count']:
                current=dict(start=clock,events=[])
            elif addr==0x0206 and current is not None:
                current['end']=clock;windows.append(current);current=None
            elif current is not None:
                current['events'].append((addr,clock))
        assert len(windows)==len(entries)*loops, len(windows)
        samples=[]
        for i,w in enumerate(windows):
            state=(tmp/f'state-{i}.bin').read_bytes();idx=i%len(entries);s=syms[idx]
            assert state[3]==idx and state[6:9]==bytes((2,50,seconds)), (i,state)
            if 'exhibition' in meta:assert state[0]==0,'F5 mode invalidates comparison'
            elapsed=w['end']-w['start'];expected=(seconds*50-1)*19656
            assert abs(elapsed-expected)<4096,(i,elapsed,expected)
            flips=sum(a==s['irq_no_flip']-5 for a,c in w['events'])
            flip_clocks=[c for a,c in w['events'] if a==s['irq_no_flip']-5]
            intervals=[b-a for a,b in zip(flip_clocks,flip_clocks[1:])]
            published=sum(a==s['profile_published'] for a,c in w['events'])
            costs=[];begin=None
            for a,c in w['events']:
                if a==s['profile_recycle']:begin=c
                elif a==s['frame_draw_complete'] and begin is not None:
                    costs.append(c-begin);begin=None
            samples.append(dict(loop=i//len(entries),entry=idx,window_cycles=elapsed,display_flips=flips,
                                published_samples=published,completed_render_cycles=costs,
                                display_interval_cycles=intervals))
    results=[]
    for i,e in enumerate(entries):
        rows=[x for x in samples if x['entry']==i];cycles=sum(x['window_cycles'] for x in rows)
        flips=sum(x['display_flips'] for x in rows);published=sum(x['published_samples'] for x in rows)
        costs=[n for x in rows for n in x['completed_render_cycles']]
        intervals=[n for x in rows for n in x['display_interval_cycles']]
        results.append(dict(name=e['name'],entry=i,frame_count=e['frames'],
                            oracle_sha256=hashlib.sha256((root/e['work']/'oracle.json').read_bytes()).hexdigest(),display_flips=flips,published_samples=published,
                            observation_seconds=cycles/CLOCK,display_fps=flips*CLOCK/cycles,
                            published_samples_per_second=published*CLOCK/cycles,
                            mean_render_cycles=statistics.mean(costs),worst_render_cycles=max(costs),
                            high_fps=CLOCK/min(intervals) if intervals else None,
                            low_fps=CLOCK/max(intervals) if intervals else None,
                            worst_display_ms=max(intervals)/985.248 if intervals else None,
                            p95_display_ms=sorted(intervals)[int(.95*(len(intervals)-1))]/985.248 if intervals else None))
    return dict(cartridge=crt.name,sha256=hashlib.sha256(crt.read_bytes()).hexdigest(),renderer=meta['stream_renderer'],
                preference=meta.get('preference','fps'),mode='normal PLAY ALL ONLY',exhibition=False,loops=loops,
                seconds_setting=seconds,ticks_per_second=50,pal_clock_hz=CLOCK,vice_defaults=True,seed=1,
                method='Unmodified CRT; monitor traces of production normal PLAY ALL. First count IRQ to automatic-next handler; 499 PAL ticks at the default 10-second setting. Initial visible picture is outside the observation window. Actual VIC flips and logical publications counted separately; no wall-clock timing.',
                entries=results,samples=samples)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--loops',type=int,default=3);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();r=benchmark(a.crt,a.vice,a.vice_data,a.loops)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n')
    for e in r['entries']:print(e['name'],round(e['display_fps'],3),round(e['mean_render_cycles'],1))


if __name__=='__main__':main()
