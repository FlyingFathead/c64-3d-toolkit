#!/usr/bin/env python3
from pathlib import Path
import sys,subprocess,json
import argparse
from PIL import Image
p=argparse.ArgumentParser(description='Verify scrolling menu in all styles with real VICE; requires the matching cart build.')
p.add_argument('crt',type=Path);p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data',type=Path,required=True);p.add_argument('--report',type=Path)
a=p.parse_args()
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'tools'))
from verify_cart_stream import labels
from c643d.colors import C64_PALETTE
stem=a.crt.stem;wd=r/'build'/f'{stem}-cartridge-demo';out=r/'build'/f'{stem}-scroll-check';out.mkdir(exist_ok=True)
styles=['default','decorative','demoscene'];syms={s:labels(wd/f'{stem}-runtime-{s}.lbl') for s in styles};m=json.loads((a.crt.with_name(stem+'-cart-manifest.json')).read_text())
mon=['delete',f'break ${syms["default"]["menu_wait_key"]:04x}','g'];checks=[]
def dump(style,tag):
 name=style+'-'+tag;checks.append((style,name))
 mon.extend(['bank ram',f'bsave "{out/(name+".ram")}" 0 $0000 $ffff','bank cpu',f'bsave "{out/(name+".color")}" 0 $d800 $dbe7'])
for style in styles:
 s=syms[style]
 if style!='default':mon+=['delete',f'break ${s["menu_wait_key"]:04x}','g $0203']
 mon += [f'> ${s["selected_entry"]:04x} $00',f'g ${s["menu_redraw"]:04x}'];dump(style,'start')
 # A clear-screen breakpoint would stop an accidental full redraw prematurely.
 mon += [f'break ${s["clear_screen"]:04x}']
 for i in range(12):mon += [f'g ${s["menu_down"]:04x}'];dump(style,f'down-{i}')
 for i in range(12):mon += [f'g ${s["menu_up"]:04x}'];dump(style,f'up-{i}')
mon+=['quit'];(out/'run.mon').write_text('\n'.join(mon)+'\n')
cmd=[a.vice,'-console','+sound','-warp','-seed','1','-directory',str(a.vice_data),'-cartcrt',str(a.crt.resolve()),'-initbreak','reset','-moncommands',str(out/'run.mon'),'-limitcycles','12000000']
with (out/'vice.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
rom=(a.vice_data/'C64/chargen-901225-01.bin').read_bytes();pal={v[0]:v[1] for v in C64_PALETTE.values()};reports=[]
for style,name in checks:
 s=syms[style];ram=(out/(name+'.ram')).read_bytes();color=(out/(name+'.color')).read_bytes();screen=ram[0x400:0x7e8]
 expected=0 if name.endswith('start') else ((int(name.rsplit('-',1)[1])+1)%12 if '-down-' in name else (11-int(name.rsplit('-',1)[1]))%12)
 sel=ram[s['selected_entry']];top=ram[s['top_entry']];assert sel==expected,(name,sel,expected)
 assert top<=sel<top+10,(name,top,sel)
 row=2 if style=='default' else 5;col=2 if style=='default' else 5
 text=bytes(v+64 if style!='default' and v<32 else v for v in screen)
 for i in range(min(10,12-top)):
  label=m['entries'][top+i]['name'].encode();pos=(row+i)*40+col
  assert text[pos:pos+len(label)]==label,(name,i,text[pos:pos+len(label)],label)
 assert screen[(row+sel-top)*40+col-2]==ord('>'),name
 assert color[(row+sel-top)*40+col-2]&15==7,(name,'marker color')
 assert b'CURSORS' in text[(row+12)*40:(row+13)*40],name
 assert b'IN DEMO:' in text[(row+13)*40:(row+14)*40],name
 initial=(out/(style+'-start.ram')).read_bytes()[0x400:0x7e8]
 for y in range(25):
  if row-1<=y<=row+10:continue
  assert screen[y*40:(y+1)*40]==initial[y*40:(y+1)*40],(name,'static row changed',y)
 if name.endswith(('start','down-10')):
  chars=rom[2048:] if style=='default' else ram[0x2000:0x2800];im=Image.new('RGB',(352,232),pal[0 if style=='default' else 6]);pix=im.load()
  for cy in range(25):
   for cx in range(40):
    glyph=screen[cy*40+cx];fg=pal[color[cy*40+cx]&15]
    for y in range(8):
     bits=chars[glyph*8+y]
     for x in range(8):pix[16+cx*8+x,16+cy*8+y]=fg if bits&(128>>x) else pal[0]
  im.resize((704,464),Image.Resampling.NEAREST).save(out/(name+'.png'))
 reports.append(dict(style=style,action=name,selected=sel,top=top))
(a.report or out/'validation.json').write_text(json.dumps(dict(all_styles=True,up_down_wrap=True,stable_header_footer=True,no_clear_screen_on_navigation=True,checks=reports),indent=2)+'\n')
print('Passed 75 menu states: all styles, both directions, scroll, wrap, marker colours, fixed header/footer, no full clears.')
