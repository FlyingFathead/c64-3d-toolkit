#!/usr/bin/env python3
"""Pixel-accurate compiler preview, not an emulator capture. Pillow required."""
from pathlib import Path
import sys,json,math,argparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
from c643d.objio import load_obj
from c643d.mesh import normalize_mesh,fix_winding_outward,transform_mesh
from c643d.pipeline import Camera,fit_scale,build_frames,decode_record_points
from c643d.colors import C64_PALETTE
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
PALETTE={v[0]:v[1] for v in C64_PALETTE.values()}
def load(name):
    meta=json.loads((ROOT/'objects'/f'{name}.json').read_text());m=load_obj(ROOT/'objects'/f'{name}.obj')
    m=fix_winding_outward(normalize_mesh(m))
    return transform_mesh(m,**dict(zip(('rx','ry','rz'),[math.radians(a) for a in meta['rotate']]))),meta

def frame_image(f,height=192):
    im=Image.new('RGB',(256,height));pix=im.load();cells={}
    for lo,hi,count,byte in f.color_spans:
        for off in range(lo+(hi<<8),lo+(hi<<8)+count):cells[(off%40,off//40)]=byte>>4
    for rec in f.records:
        for x,y in decode_record_points(rec):
            if 0<=x<256 and 0<=y<height:pix[x,y]=PALETTE[cells.get((x//8,y//8),1)]
    return im

def preview(name,frames=24):
    m,meta=load(name);cam=Camera(cy=96)
    m=transform_mesh(m,scale=fit_scale(m,frames,cam,max_scale=1.4,height=192))
    ff,_=build_frames(m,frames,cam,visibility_mode=meta['visibility'],z_tolerance=meta['z_tolerance'],enable_source_colors=True,height=192,max_visible_runs=65535)
    out=ROOT/'examples'/'hifi_showcase';out.mkdir(exist_ok=True,parents=True)
    ims=[frame_image(f) for f in ff]
    ims[0].resize((768,576),Image.Resampling.NEAREST).save(out/f'{name}_preview.png')
    ims[0].resize((512,384),Image.Resampling.NEAREST).save(out/f'{name}_turntable.gif',save_all=True,append_images=[im.resize((512,384),Image.Resampling.NEAREST) for im in ims[1:]],duration=130,loop=0)
    sheet=Image.new('RGB',(256*4,220*2),(12,12,18));d=ImageDraw.Draw(sheet)
    for k,i in enumerate([0,3,6,9,12,15,18,21]):
        sheet.paste(ims[i],((k%4)*256,(k//4)*220));d.text(((k%4)*256+8,(k//4)*220+197),f'{name}: view {i}/{frames}',fill=(200,190,210))
    sheet.save(out/f'{name}_views.png')
    print(name,'runs',min(len(f.records) for f in ff),max(len(f.records) for f in ff))
    return ims
if __name__=='__main__':
    for n in sys.argv[1:] or ['horse_head_hifi','sunflower_torus_hifi']:preview(n)
