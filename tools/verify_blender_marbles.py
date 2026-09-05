"""Run inside the supplied baked Blender scene to audit visible tabletop marbles.

blender -b examples/blender_marbles/dont_lose_your_marbles.blend --python tools/verify_blender_marbles.py
Requires the matching cart build oracle.
"""
import bpy,json,sys,math
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path('tools').resolve()))
from c643d.pipeline import decode_record_points
s=bpy.context.scene;fs=json.load(open('build/dont_lose_your_marbles-yunroll-cart-v4-scene-stream-scene/oracle.json'))
checks=0;missing=[]
for i,f in enumerate(fs):
 frame=1+i*5
 if frame>=851:break
 s.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();pixels=set()
 for rec in f['records']:pixels.update(decode_record_points(rec))
 for o in s.objects:
  if not o.name.startswith('Marble'):continue
  center=o.matrix_world.translation
  if not(abs(center.x)<5.3 and abs(center.y)<3.7 and .3<center.z<2):continue
  direction=center-s.camera.location
  hit,loc,normal,face,obj,matrix=s.ray_cast(dg,s.camera.location,direction.normalized(),distance=direction.length)
  if not hit or obj.name!=o.name:continue # centre is obscured by another body
  uv=world_to_camera_view(s,s.camera,center);px=uv.x*256;py=(1-uv.y)*192
  bounds=[world_to_camera_view(s,s.camera,o.matrix_world@v.co) for v in o.data.vertices]
  x0=math.floor(min(v.x for v in bounds)*256)-1;x1=math.ceil(max(v.x for v in bounds)*256)+1
  y0=math.floor((1-max(v.y for v in bounds))*192)-1;y1=math.ceil((1-min(v.y for v in bounds))*192)+1
  checks+=1
  if not any(x0<=x<=x1 and y0<=y<=y1 for x,y in pixels):missing.append(dict(object=o.name,frame=frame,pixel=[px,py]))
r=dict(unobscured_table_marble_samples_checked=checks,empty_projected_regions=missing,method='Blender centre-ray visibility plus compiled bitmap within projected marble bounds; excludes the authored finale')
Path('examples/cart_marbles/marble-visibility-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(r)
assert not missing
