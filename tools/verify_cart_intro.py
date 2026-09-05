#!/usr/bin/env python3
"""Capture native intro milestones in VICE; no display server required."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from verify_cart_stream import labels,render_ram

def capture(crt,vice,vice_data,out):
    crt=Path(crt).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    syms=labels(crt.with_suffix('.lbl'))
    stages=[(2,'brand'),(3,'presents'),(5,'dont'),(6,'lose'),(7,'your'),(8,'marbles'),(10,'subtitle'),(11,'white')]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);mon=['delete']
        for stage,name in stages:
            mon += [f'break ${syms[f"intro_stage_{stage}"]:04x}','g','bank ram',f'bsave "{td/name}.ram" 0 $0000 $ffff','delete']
        mon+=['quit'];(td/'intro.mon').write_text('\n'.join(mon)+'\n')
        cmd=[vice,'-console','+sound','-warp','-seed','1','-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(td/'intro.mon'),'-limitcycles','30000000']
        if vice_data:cmd+=['-directory',vice_data]
        with (td/'vice.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=90)
        from PIL import Image,ImageDraw
        sheet=Image.new('RGB',(960,880),'#24212d');d=ImageDraw.Draw(sheet)
        for i,(stage,name) in enumerate(stages):
            ram=(td/f'{name}.ram').read_bytes();im=render_ram(ram,0)
            im.resize((960,600),Image.Resampling.NEAREST).save(out/f'intro-{name}.png')
            x=(i%2)*480;y=(i//2)*220
            sheet.paste(im,(x+80,y+20));d.text((x+12,y+5),name,fill='white')
            if name=='white':assert all(lo==hi==255 for lo,hi in im.getextrema()), 'final flash is not solid white'
        sheet.save(out/'intro-storyboard.png')
    return {'cartridge':crt.name,'intro_milestones':len(stages),'white_flash_verified':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('crt',type=Path);p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(capture(a.crt,a.vice,a.vice_data,a.output),indent=2))
