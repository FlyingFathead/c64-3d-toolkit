"""Blender-side exporter for c64-3d-toolkit.

Run through Blender, not ordinary Python:
    blender --background scene.blend --python tools/blender_export.py -- --output scene.c643dscene
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy

# Reuse the exact host-side perceptual mapper. Blender runs this script with its
# own Python, so add the toolkit root containing the ``tools`` package.
TOOLKIT_ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(TOOLKIT_ROOT))
from tools.c643d.colors import nearest_c64_color_index, c64_color_index
from tools.c643d.blender_colors import material_color_index
from tools.c643d.blender import blender_frame_plan, output_frame_plan


def _args():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser(description='Export evaluated Blender animation for c64-3d-toolkit')
    p.add_argument('--output',required=True)
    p.add_argument('--blender-color-space',choices=('linear','srgb'),default='linear')
    p.add_argument('--ignore-warnings',action='store_true')
    p.add_argument('--frame-start',type=int)
    p.add_argument('--frame-end',type=int)
    p.add_argument('--output-fps',type=int)
    p.add_argument('--sample-step',type=int,default=1)
    p.add_argument('--viewport-width',type=int,choices=(256,320),default=320)
    p.add_argument('--viewport-height',type=int,default=144)
    p.add_argument('--max-frames',type=int,default=255,help='explicit host export limit; legacy PRG default 255')
    return p.parse_args(argv)


def _nearest_c64(rgb):
    r,g,b=(max(0,min(255,round(float(v)*255))) for v in rgb[:3])
    return nearest_c64_color_index((r,g,b))


def _property_color(obj,material,color_space='linear'):
    for owner in (material,obj):
        if owner is not None and 'c643d_color' in owner:
            try:
                return c64_color_index(owner['c643d_color'])
            except ValueError as exc:
                raise RuntimeError(f'{owner.name}: invalid c643d_color: {exc}') from exc
    if material is None:
        return None
    rgb = material.diffuse_color
    if material.use_nodes and material.node_tree:
        output = next((node for node in material.node_tree.nodes
                       if node.type == 'OUTPUT_MATERIAL' and node.is_active_output), None)
        socket = output.inputs.get('Surface') if output else None
        shader = socket.links[0].from_node if socket and socket.is_linked else None
        if shader and shader.type == 'BSDF_PRINCIPLED':
            base = shader.inputs.get('Base Color')
            if base and not base.is_linked:
                rgb = base.default_value
    return material_color_index(rgb,color_space)


def _export_objects():
    return sorted(
        (obj for obj in bpy.context.scene.objects
         if obj.type=='MESH' and not obj.hide_render and obj.get('c643d_export',True)),
        key=lambda obj:obj.name,
    )


def _validate_mesh_caches(objects, *, ignore_warnings=False):
    """Fail clearly on unavailable external caches before exporting a static mesh."""
    for original in objects:
        for modifier in original.modifiers:
            if modifier.type not in ('MESH_SEQUENCE_CACHE', 'MESH_CACHE'):
                continue
            if not modifier.show_viewport:
                if not ignore_warnings:print(f'WARNING: {original.name}: cache modifier {modifier.name} is disabled in the viewport; evaluated export will omit it', flush=True)
                continue
            cache = getattr(modifier, 'cache_file', None)
            if modifier.type == 'MESH_SEQUENCE_CACHE' and cache is None:
                raise RuntimeError(f'{original.name}: Mesh Sequence Cache has no cache file')
            owner = cache if cache is not None else original
            ref = cache.filepath if cache is not None else modifier.filepath
            path = Path(bpy.path.abspath(ref, library=getattr(owner, 'library', None)))
            if path.suffix.lower() == '.abc' and not bpy.app.build_options.alembic:
                raise RuntimeError(f'{original.name}: this Blender build has no Alembic support; select an Alembic-enabled Blender with --blender')
            if not ref or not path.is_file():
                raise RuntimeError(f'{original.name}: external vertex cache is missing: {path}. Keep the .abc/.mdd/.pc2 file accessible to headless Blender and repair its modifier path')
            print(f'c643d: {original.name}: evaluating {modifier.type} cache {path.name}', flush=True)


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
    if args.viewport_height<8 or args.viewport_height>200 or args.viewport_height%8:
        raise RuntimeError('--viewport-height must be a multiple of 8 from 8..200')
    width=args.viewport_width
    height=args.viewport_height
    scene=bpy.context.scene
    camera=scene.camera
    if camera is None:
        raise RuntimeError('scene has no active camera')
    if camera.data.type!='PERSP':
        raise RuntimeError('c64-3d-toolkit Blender v1 supports perspective cameras only')
    objects=_export_objects()
    if not objects:
        raise RuntimeError('scene has no exportable mesh objects')
    _validate_mesh_caches(objects,ignore_warnings=args.ignore_warnings)
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
    if args.output_fps is not None:
        if args.sample_step != 1:
            raise RuntimeError('--output-fps and --sample-step other than 1 conflict')
        if rigidbody_world is not None and any(o.rigid_body is not None for o in objects):
            raise RuntimeError('--output-fps requires baked transforms; use the baked .blend, not live rigid-body physics')
        evaluation_frames,source_frames=output_frame_plan(start,end,float(scene.render.fps)/scene.render.fps_base,args.output_fps,evaluation_frames.start)
        print(f'Blender output FPS: {args.output_fps}; source FPS: {scene.render.fps/scene.render.fps_base:g}; source timing preserved')
        source_rate=float(scene.render.fps)/scene.render.fps_base
        rounded=sum(abs((start+i*source_rate/args.output_fps)-f)>1e-8 for i,f in enumerate(source_frames))
        repeated=len(source_frames)-len(set(source_frames))
        if (rounded or repeated) and not args.ignore_warnings:
            print(f'WARNING: {rounded} requested sample times rounded/clamped to nearest integer Blender frame; {repeated} repeated samples retained. No fractional geometry evaluation; requested playback duration retained.',flush=True)

    if not 1<=len(source_frames)<=args.max_frames:
        raise RuntimeError(f'{len(source_frames)} sampled frames exceed the requested limit of {args.max_frames}')
    capture_frames=set(source_frames)
    print(
        f'c643d: evaluating Blender frames {evaluation_frames[0]}..{end} sequentially; '
        f'capturing {len(source_frames)} samples'
    )

    topology=None; expected=[]; out_frames=[]
    for evaluation_frame in evaluation_frames:
        scene.frame_set(int(evaluation_frame), subframe=float(evaluation_frame)%1)
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
            # Blender's camera projection ignores camera object scale (as does
            # world_to_camera_view). Match it for scaled camera parents too.
            camera_inverse=evaluated_camera.matrix_world.normalized().inverted()
            for original,obj,mesh in parts:
                offset=len(vertices); counts.append((original.name,len(mesh.vertices),len(mesh.polygons)))
                # Camera-space export negates Z to make forward positive. That
                # reflection reverses handedness. Preserve outward normals by
                # reversing polygon order, accounting for mirrored objects too.
                # Surface-only Z buffering hid this in earlier scene exports;
                # front-face feature culling and material selection need it.
                reverse_winding=(camera_inverse @ obj.matrix_world).to_3x3().determinant() > 0
                for vertex in mesh.vertices:
                    if not int(original.get('c643d_visible_start',start)) <= source_frame <= int(original.get('c643d_visible_end',end)):
                        # Preserve topology while parking scheduled emitters safely
                        # outside the viewport and in front of the projection plane.
                        vertices.append([float(vertex.co.x),-10000.0+float(vertex.co.y),100.0+float(vertex.co.z)])
                    else:
                        p=camera_inverse @ obj.matrix_world @ vertex.co
                        vertices.append([float(p.x),float(p.y),float(-p.z)])
                for polygon in mesh.polygons:
                    indices=list(polygon.vertices)
                    if reverse_winding:
                        indices.reverse()
                    faces.append([offset+i for i in indices])
                    material=(obj.material_slots[polygon.material_index].material
                              if polygon.material_index<len(obj.material_slots) else None)
                    face_colors.append(_property_color(original,material,args.blender_color_space))
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
                depsgraph,x=width,y=height,scale_x=1.0,scale_y=1.0
            )
            fx=float(matrix[0][0])*width/2.0
            fy=float(matrix[1][1])*height/2.0
            cx=width/2.0*(1.0-float(matrix[0][2]))
            cy=height/2.0*(1.0+float(matrix[1][2]))
            out_frames.append({
                'source_frame':int(source_frame),
                'source_frame_time':source_frame,
                'projection':{'fx':fx,'fy':fy,'cx':cx,'cy':cy},
                'vertices':vertices,
            })
        finally:
            _release(parts)

    if args.output_fps is not None:
        captured={f['source_frame']:f for f in out_frames}
        out_frames=[captured[f] for f in source_frames]
    changed_transitions=sum(
        previous['vertices']!=current['vertices'] or previous['projection']!=current['projection']
        for previous,current in zip(out_frames,out_frames[1:])
    )
    if len(out_frames)>1 and changed_transitions==0 and not args.ignore_warnings:
        print(
            'c643d: WARNING: all sampled frames are geometrically identical; '
            'the resulting C64 scene will be static',
            file=sys.stderr,
        )
    elif len(out_frames)>1 and changed_transitions:
        print(
            f'c643d: motion check: {changed_transitions}/{len(out_frames)-1} '
            'sampled transitions changed'
        )

    payload={
        'format':'c643dscene','version':1,
        'viewport':{'width':width,'height':height},
        'name':str(scene.get('c643d_title') or Path(bpy.data.filepath).stem.upper() or 'BLENDER SCENE'),
        'source':{
            'blender_color_space':args.blender_color_space,
            'output_fps':args.output_fps,
            'resampling':'nearest-integer-source-frame' if args.output_fps is not None else 'sample-step',
            'kind':'blender','file':Path(bpy.data.filepath).name,
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
