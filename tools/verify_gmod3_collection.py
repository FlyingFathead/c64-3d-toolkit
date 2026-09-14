#!/usr/bin/env python3
"""Verify every collection entry and measure actual PAL display throughput."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from c643d.gmod3_probe import labels,vice_command
from c643d.gmod3_catalog import frames_for
from verify_cart_stream import expected_frame,apply_interactive_overlay,render_ram,startup_monitor

ROOT=Path(__file__).resolve().parents[1]
CLOCK=985248
PAL=19656


def run_monitor(crt,vice,data,tmp,commands,limit=600_000_000):
    (tmp/'run.mon').write_text('\n'.join(commands+['quit'])+'\n')
    with (tmp/'vice.log').open('w') as log:
        p=subprocess.run(vice_command(vice,crt,data)+['-initbreak','reset','-moncommands',str(tmp/'run.mon'),
            '-monlogname', str(tmp/'monitor.log'), '-monlog','-limitcycles',str(limit)],
            stdout=log,stderr=subprocess.STDOUT,timeout=240)
    if p.returncode:raise RuntimeError((tmp/'monitor.log').read_text()[-1800:]+'\n'+(tmp/'vice.log').read_text()[-800:])
    return [int(x) for x in re.findall(r'Stopwatch:\s*(\d+)',(tmp/'monitor.log').read_text())]


def launch(meta,menu,entry,sym):
    if meta.get('standalone'):
        setup,go=startup_monitor(entry['runtime'],sym)
        return ['delete',*setup,f'break ${sym["frame_begin"]:04x}',go]
    return ['delete',f'break ${menu["menu_poll"]:04x}','g','delete',
        f'> $0330 {entry["index"]:02x}',f'break ${sym["frame_begin"]:04x}',f'g ${menu["collection_start"]:04x}']


def verify_entry(crt,meta,entry,vice,data,out,refreshes=2400):
    sym=labels(crt.parent/entry['labels']);menu={} if meta.get('standalone') else labels(crt.parent/meta['collection_labels'])
    frames=frames_for(ROOT/'build/gmod3-catalog',entry)
    if 'slice' in entry:frames=frames[slice(*entry['slice'])]
    n=entry['mode_frames'] or len(frames);begin=entry['mode_frames'] if entry['mode_frames'] else 0
    expected=[]
    for f in frames:
        bm,sc=expected_frame(f.__dict__,entry['screen_color'])
        expected.append(bytes(apply_interactive_overlay(bm,entry['runtime']))+sc)
    count=n*2+3
    with tempfile.TemporaryDirectory(prefix='gmod3-entry-') as td:
        tmp=Path(td);cmd=launch(meta,menu,entry,sym)
        cmd+=['bank ram',f'bsave "{tmp}/startup.ram" 0 $0000 $ffff','delete']
        # Completion breakpoints verify every produced picture. The following
        # IRQ observation independently measures what reached the display.
        for i in range(count):
            cmd+=['stopwatch','delete',f'break ${sym["frame_draw_complete"]:04x}','g','stopwatch','bank ram',
                f'bsave "{tmp}/frame-{i}.ram" 0 $0000 $ffff','delete',f'break ${sym["frame_begin"]:04x}','g']
        cmd+=['delete',f'break ${sym["irq_no_flip"]:04x}']
        for i in range(refreshes+1):
            cmd+=['g','stopwatch','bank ram',f'bsave "{tmp}/irq-{i}.ram" 0 $0000 $1fff']
        try:
            ticks=run_monitor(crt,vice,data,tmp,cmd)
            if len(ticks)!=count*2+refreshes+1:raise AssertionError('Incomplete observation')
            startup=(tmp/'startup.ram').read_bytes()
            if meta['interactive']:
                assert startup[sym['fx_enabled']]==0,'Stars must start off'
            slots=Counter();indices=[]
            for i in range(count):
                ram=(tmp/f'frame-{i}.ram').read_bytes();fi=ram[sym['frame_index']];slot=ram[sym['render_slot']]
                if 'gp_page' in sym:fi+=ram[sym['gp_page']]*128
                wanted=begin+i%n
                if fi!=wanted:raise AssertionError(f'Frame order: {fi}, expected {wanted}')
                baddr=(0x2000,0x6000,0xe000)[slot];saddr=(0x400,0x4400,0xc800)[slot]
                got=ram[baddr:baddr+7680]+ram[saddr:saddr+960]
                if got!=expected[fi]:
                    mismatches=[j for j,(a,b) in enumerate(zip(got,expected[fi])) if a!=b]
                    raise AssertionError(f'{entry["name"]} picture {fi}, slot {slot}: {len(mismatches)} mismatches; first {mismatches[:12]}')
                slots[slot]+=1;indices.append(fi)
                if i==n:render_ram(ram,slot).resize((640,400)).save(out/f'{entry["index"]:02d}.png')
            transitions=[];last=None
            for i in range(refreshes+1):
                ram=(tmp/f'irq-{i}.ram').read_bytes();slot=ram[sym['display_slot']];fi=ram[sym['slot_frame']+slot]
                if slot!=last:
                    if transitions:
                        active=128 if entry['frames']>255 else n
                        wanted=begin+(transitions[-1][1]-begin+1)%active
                        if fi!=wanted:raise AssertionError(f'Display skipped/reordered: {fi}, expected {wanted}')
                    transitions.append((i,fi))
                last=slot
            holds=[b[0]-a[0] for a,b in zip(transitions,transitions[1:])]
            cycles=[ticks[i*2+1]-ticks[i*2] for i in range(n,count)]
            elapsed=ticks[-1]-ticks[count*2]
            assert abs(elapsed-refreshes*PAL)<PAL,'Unexpected PAL observation duration'
            assert set(slots)=={0,1,2}
            return dict(index=entry['index'],name=entry['name'],passed=True,frames=n,stored_frames=len(frames),
                pictures_checked=count,all_three_buffers=True,stars_off=meta['interactive'],
                display_frames=len(transitions)-1,observed_refreshes=refreshes,
                average_fps=(len(transitions)-1)/(refreshes*PAL/CLOCK),
                high_fps=CLOCK/(min(holds)*PAL),low_fps=CLOCK/(max(holds)*PAL),
                mean_render_cycles=sum(cycles)/len(cycles),max_render_cycles=max(cycles),
                picture_sha256=entry['picture_sha256'],allocated_kib=entry['allocated_kib'],
                bank_range=[entry['runtime_bank'],entry['last_bank']],target_fps=entry.get('target_fps'))
        except Exception:
            failure=out/f'failure-{entry["index"]:02d}';failure.mkdir(exist_ok=True)
            for p in tmp.glob('*'):
                if p.name in ('run.mon','monitor.log','vice.log','startup.ram') or p.name.startswith('frame-'):
                    shutil.copyfile(p,failure/p.name)
            raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('crt',type=Path)
    p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True)
    p.add_argument('--output',type=Path,default=ROOT/'docs/benchmarks/gmod3-collection')
    p.add_argument('--entries',type=int,nargs='*');p.add_argument('--refreshes',type=int,default=2400)
    p.add_argument('--resume',action='store_true');a=p.parse_args();crt=a.crt.resolve();a.output.mkdir(parents=True,exist_ok=True)
    meta=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text());results=[];digest=hashlib.sha256(crt.read_bytes()).hexdigest()
    for entry in meta['entries']:
        if a.entries is not None and entry['index'] not in a.entries:continue
        path=a.output/f'{entry["index"]:02d}.json'
        if a.resume and path.exists():
            row=json.loads(path.read_text())
            if row.get('crt_sha256')==digest:results.append(row);continue
        print('Verify',entry['index'],entry['name'],flush=True)
        row=verify_entry(crt,meta,entry,a.vice,a.vice_data,a.output,a.refreshes);row['crt_sha256']=digest
        path.write_text(json.dumps(row,indent=2)+'\n');results.append(row)
        print(f'PASS {row["name"]}: {row["average_fps"]:.4f} displayed FPS, {row["pictures_checked"]} pictures',flush=True)
    (a.output/'results.json').write_text(json.dumps(dict(cartridge=crt.name,crt_sha256=digest,entries=results,
        clock_hz=CLOCK,pal_cycles=PAL,protocol='Full picture loops then actual IRQ display-slot transitions; stars off; warmup excluded'),indent=2)+'\n')

if __name__=='__main__':main()
