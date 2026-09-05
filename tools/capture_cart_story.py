#!/usr/bin/env python3
"""Capture native intro/outro raster ticks and completed vector frames in VICE.

Produces a timestamped GIF from emulated RAM, including the real text charset.
The vector portion uses completed buffers, as in verify_cart_stream.py.
"""
import argparse,json,re,subprocess,tempfile
from pathlib import Path
from verify_cart_stream import labels,render_ram
from verify_cart_ending import text_image

def capture(crt,vice,data,out):
    crt=Path(crt).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    syms=labels(crt.with_suffix('.lbl'));tick=syms['intro_wait_line']+7
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        mon=['delete',f'break ${tick:04x}',f'break ${syms["frame_draw_complete"]:04x}',f'break ${syms["ghost_idle"]:04x}','command 3 "quit"']
        for i in range(2000):
            mon+=['g','bank ram',f'bsave "{tmp}/{i}.ram" 0 $0000 $ffff','bank cpu',f'bsave "{tmp}/{i}.io" 0 $d000 $ddff','stopwatch']
        mon+=['quit'];(tmp/'run.mon').write_text('\n'.join(mon)+'\n')
        cmd=[vice,'-console','+sound','-warp','-seed','1','-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(tmp/'run.mon'),'-monlog','-monlogname',str(tmp/'monitor.log'),'-limitcycles','100000000','-directory',str(data)]
        with (tmp/'vice.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
        log=(tmp/'monitor.log').read_text();events=[];pc=None
        for line in log.splitlines():
            m=re.search(r'Stop on\s+exec ([0-9a-f]+)',line)
            if m:pc=int(m[1],16)
            m=re.search(r'Stopwatch:\s*(\d+)',line)
            if m:events.append((pc,int(m[1])))
        assert events and pc==syms['ghost_idle'],log[-2000:]
        char=next(Path(data).glob('C64/chargen*')).read_bytes();images=[]
        from PIL import Image
        for i,(pc,t) in enumerate(events):
            ram=bytearray((tmp/f'{i}.ram').read_bytes());ram[0xd000:0xde00]=(tmp/f'{i}.io').read_bytes()
            if not ram[0xd011]&16:im=Image.new('RGB',(320,200),'black')
            elif ram[0xd011]&32:
                if pc==syms['frame_draw_complete']:slot=ram[syms['render_slot']]
                else:slot={0:0,1:1,3:2}[(~ram[0xdd00])&3]
                im=render_ram(ram,slot)
            else:im=text_image(ram,char,ram[0xd021]&15)
            images.append(im.resize((640,400),Image.Resampling.NEAREST))
        dt=[max(10,round((b[1]-a[1])/985248*100)*10) for a,b in zip(events,events[1:])]+[2000]
        images[0].save(out/'marbles-complete-story.gif',save_all=True,append_images=images[1:],duration=dt,loop=0)
        report=dict(captures=len(events),last_capture_seconds=events[-1][1]/985248,preview_seconds=sum(dt)/1000,method='PAL VICE RAM captures: intro/outro raster ticks and completed scene buffers')
        (out/'story-capture.json').write_text(json.dumps(report,indent=2)+'\n');return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('crt');p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(capture(a.crt,a.vice,a.vice_data,a.output),indent=2))
