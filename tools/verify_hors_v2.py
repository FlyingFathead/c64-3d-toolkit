#!/usr/bin/env python3
"""Exercise beta ROMH payloads, 16-bit frame paging, blank pictures and size rejection."""
from pathlib import Path
from dataclasses import replace
import argparse, json, shutil
from c643d.sceneio import load_scene
from c643d.pipeline import build_scene_frames, FrameBuild
from c643d import cartscene
from c643d.cartridge import easyflash_offset
from c643d.hors_v2 import assemble_scene, encoder
from verify_cart_stream import verify


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--tass',default='64tass');p.add_argument('--cartconv',default='cartconv');p.add_argument('--vice',default='x64sc');p.add_argument('--vice-data')
 a=p.parse_args();root=Path(__file__).resolve().parents[1];a.out=a.out.resolve()
 if a.out.exists():p.error('--out must be a new directory')
 a.out.mkdir(parents=True);stage=a.out/'stage';shutil.copytree(root/'c64',stage/'c64')
 scene=load_scene(root/'examples/autotune/colour-cube.c643dscene')
 raw,_=build_scene_frames(scene,enable_source_colors=True,height=192,max_frames=2048,max_visible_runs=65535)
 frames=raw*11;scene=replace(scene,frames=scene.frames*11)
 frames[25]=FrameBuild([],[],0,0,[])
 # Deliberately scatter enough bytes that a gap-1 literal stream cannot fit.
 records=[]
 for y in range(0,192,2):
  for cell in range(40):
   offset=(y//8)*320+cell*8
   records.append((offset&255,offset>>8,1,(y&7)<<3,0))
 oversized=FrameBuild(records,[],len(records),len(records),[])
 try:encoder(1,2048)(oversized)
 except ValueError as e:rejection=str(e)
 else:raise AssertionError('Oversized literal picture was not rejected')
 original_pack=cartscene.pack_scene_frames
 def force_romh(items,colors=True,**options):
  image,directory=original_pack(items,colors,**options)
  assert all(d['chip']=='roml' for d in directory)
  for bank in {d['bank'] for d in directory}:
   source=easyflash_offset(bank,'roml',0);target=easyflash_offset(bank,'romh',0)
   image[target:target+8192]=image[source:source+8192]
  for i,d in enumerate(directory):
   d['chip']='romh';d['address']+=0x2000
   page,j=divmod(i,256)
   address=easyflash_offset(1+page//4,'romh',(page%4)*1792+2*256+j)
   image[address]=d['address']>>8
  return image,directory
 cartscene.pack_scene_frames=force_romh
 try:
  crt,manifest=assemble_scene(stage,frames,scene,tass=str(Path(a.tass).resolve()) if '/' in a.tass else a.tass,
      cartconv=str(Path(a.cartconv).resolve()) if '/' in a.cartconv else a.cartconv,outdir=a.out,stem='beta-boundaries',
      hud_text='BETA BOUNDARIES',frame_ticks=1,colors=True,color_index=1,intro=False,ending=False,text_overlay=False,
      optimize=False,prefer='fps',draw_gap=6,batch_budget=2048)
 finally:cartscene.pack_scene_frames=original_pack
 result=verify(crt,a.vice,a.vice_data,cycles=2,oracle_path=stage/'build/beta-boundaries-stream-scene/oracle.json')
 report={'passed':True,'frames':len(frames),'all_payloads_ROMH':all(d['chip']=='romh' for d in manifest['frame_data']),
         'crossed_frame_255':True,'blank_frame_index':25,'oversize_rejected':rejection,'verification':result,
         'scope':'Synthetic compiler-level edge case; the normal geometry compiler still rejects wholly invisible scene samples.'}
 (a.out/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
