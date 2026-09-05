#!/usr/bin/env python3
"""Verify the finite Marbles story in real PAL VICE, including text and timing."""
import argparse,json,re,subprocess,tempfile
from pathlib import Path
from verify_cart_stream import labels,render_ram
from c643d.colors import C64_PALETTE

MESSAGE="HEY... DON'T LOSE YOUR MARBLES. :-)"
GREETING='GREETINGS TO ALL OLD DEMOSCENE WANDERERS'
def screen(text):return bytes(ord(c)-64 if 64<=ord(c)<=95 else ord(c) for c in text)
def text_image(ram,chargen,bg=6):
    from PIL import Image
    pal={v[0]:v[1] for v in C64_PALETTE.values()};im=Image.new('RGB',(320,200));pix=im.load()
    for y in range(200):
        for x in range(320):
            cell=y//8*40+x//8;bits=chargen[ram[0x400+cell]*8+(y&7)]
            pix[x,y]=pal[ram[0xd800+cell]&15 if bits&(128>>(x&7)) else bg]
    return im

def verify(crt,vice,data,out):
    crt=Path(crt).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    syms=labels(crt.with_suffix('.lbl'));manifest=json.loads(crt.with_name(crt.stem+'-manifest.json').read_text())
    assert manifest.get('ending')
    stages=['intro_start','frame_begin','outro_start','greeting_oops','greeting_done','outro_credits_visible','fake_basic_ready','ghost_message_done','ghost_idle','ghost_idle']
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);mon=['delete']
        for i,name in enumerate(stages):
            mon += [f'break ${syms[name]:04x}','g','bank ram',f'bsave "{tmp/i.__str__()}.ram" 0 $0000 $ffff','bank cpu',f'bsave "{tmp/i.__str__()}.io" 0 $d000 $dbff','stopwatch','delete']
        mon += ['quit'];(tmp/'run.mon').write_text('\n'.join(mon)+'\n')
        cmd=[vice,'-console','+sound','-warp','-seed','1','-cartcrt',str(crt),'-initbreak','reset','-moncommands',str(tmp/'run.mon'),'-monlog','-monlogname',str(tmp/'monitor.log'),'-limitcycles','160000000']
        if data:cmd+=['-directory',str(data)]
        with (out/'vice-ending.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=180)
        log=(tmp/'monitor.log').read_text();ticks=[int(t) for t in re.findall(r'Stopwatch:\s*(\d+)',log)]
        assert len(ticks)==len(stages),log[-2000:]
        rams=[]
        for i in range(len(stages)):
            r=bytearray((tmp/f'{i}.ram').read_bytes());r[0xd000:0xdc00]=(tmp/f'{i}.io').read_bytes();rams.append(r)
        for i,r in enumerate(rams):(out/f'{i}.ram').write_bytes(r)
        (out/'monitor.log').write_text(log)
        assert rams[3][0x590:0x590+len('GREETINGS TO ALL OLD DEMOSCENE WANKE')]==screen('GREETINGS TO ALL OLD DEMOSCENE WANKE'),repr(rams[3][0x590:0x590+40])
        assert rams[4][0x590:0x590+len(GREETING)]==screen(GREETING)
        for i in (6,7,8,9):
            r=rams[i]
            assert r[0xd011]&0x7f==0x1b and r[0xd018]&0xfe==0x14
            assert r[0xd020]&15==14 and r[0xd021]&15==6
            assert r[0x428:0x428+40]==screen('    **** COMMODORE 64 BASIC V2 ****'.ljust(40))
            assert r[0x478:0x478+40]==screen(' 64K RAM SYSTEM  38911 BASIC BYTES FREE'.ljust(40))
            assert r[0x4c8:0x4ce]==screen('READY.')
        for i in (7,8,9):assert rams[i][0x518:0x518+len(MESSAGE)]==screen(MESSAGE)
        assert ticks[9]-ticks[8]>980000,'cursor idle loop was not held for one second'
        charpaths=list(Path(data).glob('C64/chargen*')) if data else []
        assert charpaths,'VICE C64 chargen is required for verified text previews'
        chargen=charpaths[0].read_bytes()
        images=[]
        for i in range(2,10):
            if i==2:im=render_ram(rams[i],rams[i][syms['display_slot']])
            elif i==5:im=render_ram(rams[i],0)
            else:im=text_image(rams[i],chargen,0 if i in (3,4) else 6)
            im.resize((960,600)).save(out/f'{i:02d}-{stages[i]}.png');images.append(im)
        from PIL import Image,ImageDraw
        sheet=Image.new('RGB',(640,880),'#25242b');draw=ImageDraw.Draw(sheet)
        for j,im in enumerate(images):
            x=j%2*320;y=j//2*220;sheet.paste(im,(x,y+20));draw.text((x+4,y+4),stages[j+2],fill='white')
        sheet.save(out/'ending-storyboard.png')
        result=dict(cartridge=crt.name,finite_ending=True,greeting_correction_verified=True,basic_banner_verified=True,ghost_message_verified=True,idle_cursor_verified=True,seconds_from_reset={f'{i}-{s}':t/985248 for i,(s,t) in enumerate(zip(stages,ticks))},scene_seconds=(ticks[2]-ticks[1])/985248,total_to_ghost_seconds=ticks[7]/985248)
        (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('crt');p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    print(json.dumps(verify(a.crt,a.vice,a.vice_data,a.output),indent=2))
