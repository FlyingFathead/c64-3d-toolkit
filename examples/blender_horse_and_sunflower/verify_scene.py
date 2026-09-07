"""Reopen the saved .blend through Blender and check its source assets and motion."""
from pathlib import Path
import bpy, json, runpy, hashlib
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[2]
gen=runpy.run_path(str(root/'examples/blender_horse_and_sunflower/horse_and_sunflower.py'),run_name='scene_functions')
scene=bpy.context.scene
horse=bpy.data.objects['Horse_head_hifi']; flower=bpy.data.objects['Sunflower_torus_hifi']
gen['validate'](scene,horse,flower,scene.camera)
for slug,obj in [('horse_head_hifi',horse),('sunflower_torus_hifi',flower)]:
 verts,faces,colors,mtls,hashes=gen['source_obj'](slug)
 assert json.loads(obj['source_sha256'])==hashes
 for v,p in zip(obj.data.vertices,verts):assert max(abs(a-b) for a,b in zip(v.co,p))<1e-6
 assert [tuple(p.vertices) for p in obj.data.polygons]==[tuple(f) for f in faces]
 for polygon,name in zip(obj.data.polygons,colors):
  mat=obj.data.materials[polygon.material_index]
  assert mat['c643d_color']==gen['C64_PALETTE'][name][0]
  assert max(abs(a-b) for a,b in zip(mat.diffuse_color[:3],mtls[name]))<1e-6
animated=[o.name for o in scene.objects if o.animation_data and o.animation_data.action]
assert animated==['Horse_motion']
checked_frames=(1,40,65,83,103,115,135,150,178,200,231,250)
intersections=[]
for frame in checked_frames:
 scene.frame_set(frame)
 def bvh(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])
 overlap=bvh(horse).overlap(bvh(flower))
 if overlap:intersections.append([frame,len(overlap)])
result=dict(blender=bpy.app.version_string,vertices=378,faces=416,original_topology_and_materials=True,animated_objects=animated,stationary_camera=True,stationary_sunflower=True,loop_endpoint_matches=True,mesh_intersections=intersections,intersection_checked_frames=checked_frames)
assert not intersections, intersections
print(json.dumps(result,indent=2))
(root/'examples/blender_horse_and_sunflower/scene-validation.json').write_text(json.dumps(result,indent=2)+'\n')
