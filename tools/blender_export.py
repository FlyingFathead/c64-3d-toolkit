"""Blender-side exporter for c64-3d-toolkit.

Run through Blender, not ordinary Python:
    blender --background scene.blend --python tools/blender_export.py -- --output scene.c643dscene
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

# Reuse the exact host-side perceptual mapper. Blender runs this script with its
# own Python, so add the toolkit root containing the ``tools`` package.
TOOLKIT_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLKIT_ROOT))
from tools.c643d.colors import nearest_c64_color_index
from tools.c643d.blender import blender_frame_plan


WIDTH=256
HEIGHT=144
def _args():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser(description='Export evaluated Blender animation for c64-3d-toolkit')
    p.add_argument('--output',required=True)
    p.add_argument('--frame-start',type=int)
    p.add_argument('--frame-end',type=int)
    p.add_argument('--sample-step',type=int,default=1)
    return p.parse_args(argv)


def _nearest_c64(rgb):
    r,g,b=(max(0,min(255,round(float(v)*255))) for v in rgb[:3])
    return nearest_c64_color_index((r,g,b))


def _property_color(obj,material):
    for owner in (material,obj):
        if owner is not None and 'c643d_color' in owner:
            value=int(owner['c643d_color'])
            if not 0<=value<=15:
                raise RuntimeError(f'{owner.name}: c643d_color must be 0..15')
            return value
    if material is None:
        return None
    return _nearest_c64(material.diffuse_color)


def _export_objects():
    return sorted(
        (obj for obj in bpy.context.scene.objects
         if obj.type=='MESH' and not obj.hide_render and obj.get('c643d_export',True)),
        key=lambda obj:obj.name,
    )


def _evaluated_parts(objects,depsgraph):
    parts=[]
    for original in objects:
        obj=original.evaluated_get(depsgraph)
        mesh=obj.to_mesh(preserve_all_data_layers=True,depsgraph=depsgraph)
        if mesh is None:
            raise RuntimeError(f'{original.name}: could not evaluate mesh')
        parts.append((original,obj,mesh))
    return parts


def _release(parts):
    for _original,obj,_mesh in parts:
        obj.to_mesh_clear()


def main():
    args=_args()
    if args.sample_step<1:
        raise RuntimeError('--sample-step must be at least 1')
    scene=bpy.context.scene
    camera=scene.camera
    if camera is None:
        raise RuntimeError('scene has no active camera')
    if camera.data.type!='PERSP':
        raise RuntimeError('c64-3d-toolkit Blender v1 supports perspective cameras only')
    objects=_export_objects()
    if not objects:
        raise RuntimeError('scene has no exportable mesh objects')
    start=scene.frame_start if args.frame_start is None else args.frame_start
    end=scene.frame_end if args.frame_end is None else args.frame_end
    if start>end:
        raise RuntimeError(f'frame start {start} is after frame end {end}')
    rigidbody_world=getattr(scene,'rigidbody_world',None)
    point_cache=getattr(rigidbody_world,'point_cache',None)
    simulation_start=int(point_cache.frame_start) if point_cache is not None else None
    evaluation_frames,source_frames=blender_frame_plan(
        start,end,args.sample_step,scene_start=scene.frame_start,
        simulation_start=simulation_start,
    )
    if len(source_frames)>255:
        raise RuntimeError(f'{len(source_frames)} sampled frames exceed the C64 table limit of 255')
    capture_frames=set(source_frames)
    print(
        f'c643d: evaluating Blender frames {evaluation_frames.start}..{end} sequentially; '
        f'capturing {len(source_frames)} samples'
    )

    topology=None; expected=[]; out_frames=[]
    for evaluation_frame in evaluation_frames:
        scene.frame_set(evaluation_frame)
        depsgraph=bpy.context.evaluated_depsgraph_get()
        if evaluation_frame not in capture_frames:
            # Physics caches are stateful. Touch evaluated rigid-body matrices
            # on every intervening frame even though only sampled frames are
            # converted to C64 geometry.
            for original in objects:
                if original.rigid_body is not None:
                    original.evaluated_get(depsgraph).matrix_world.copy()
            continue
        source_frame=evaluation_frame
        parts=_evaluated_parts(objects,depsgraph)
        try:
            vertices=[]; faces=[]; face_colors=[]; counts=[]
            evaluated_camera=camera.evaluated_get(depsgraph)
            camera_inverse=evaluated_camera.matrix_world.inverted()
            for original,obj,mesh in parts:
                offset=len(vertices); counts.append((original.name,len(mesh.vertices),len(mesh.polygons)))
                for vertex in mesh.vertices:
                    p=camera_inverse @ obj.matrix_world @ vertex.co
                    vertices.append([float(p.x),float(p.y),float(-p.z)])
                for polygon in mesh.polygons:
                    faces.append([offset+i for i in polygon.vertices])
                    material=(obj.material_slots[polygon.material_index].material
                              if polygon.material_index<len(obj.material_slots) else None)
                    face_colors.append(_property_color(original,material))
            if topology is None:
                expected=counts
                topology={'faces':faces,'line_edges':[],'face_colors':face_colors,'line_colors':[]}
            elif counts!=expected or faces!=topology['faces']:
                raise RuntimeError(
                    f'topology changes at Blender frame {source_frame}; v1 requires stable vertex/polygon topology'
                )

            # calc_matrix_camera is an Object method in both Blender 4.x and
            # 5.x. Calling it on the Camera datablock fails on Blender 4.0.2.
            matrix=evaluated_camera.calc_matrix_camera(
                depsgraph,x=WIDTH,y=HEIGHT,scale_x=1.0,scale_y=1.0
            )
            fx=float(matrix[0][0])*WIDTH/2.0
            fy=float(matrix[1][1])*HEIGHT/2.0
            cx=WIDTH/2.0*(1.0-float(matrix[0][2]))
            cy=HEIGHT/2.0*(1.0+float(matrix[1][2]))
            out_frames.append({
                'source_frame':source_frame,
                'projection':{'fx':fx,'fy':fy,'cx':cx,'cy':cy},
                'vertices':vertices,
            })
        finally:
            _release(parts)

    changed_transitions=sum(
        previous['vertices']!=current['vertices'] or previous['projection']!=current['projection']
        for previous,current in zip(out_frames,out_frames[1:])
    )
    if len(out_frames)>1 and changed_transitions==0:
        print(
            'c643d: WARNING: all sampled frames are geometrically identical; '
            'the resulting C64 scene will be static',
            file=sys.stderr,
        )
    elif len(out_frames)>1:
        print(
            f'c643d: motion check: {changed_transitions}/{len(out_frames)-1} '
            'sampled transitions changed'
        )

    payload={
        'format':'c643dscene','version':1,
        'name':Path(bpy.data.filepath).stem.upper() or 'BLENDER SCENE',
        'source':{
            'kind':'blender','file':str(Path(bpy.data.filepath).resolve()),
            'fps':float(scene.render.fps)/float(scene.render.fps_base),
            'frame_start':start,'frame_end':end,'sample_step':args.sample_step,
        },
        'topology':topology,'frames':out_frames,
    }
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
    print(f'c643d: exported {len(objects)} objects, {len(out_frames)} frames, {len(out_frames[0]["vertices"])} vertices -> {output}')


if __name__=='__main__':
    main()
