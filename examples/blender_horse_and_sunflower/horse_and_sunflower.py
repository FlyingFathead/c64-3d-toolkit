"""Author the horse_and_sunflower close-up using the original HiFi OBJ/MTL assets.

Run from any directory with Blender 4.0 or newer:
  blender --background --python examples/blender_horse_and_sunflower/horse_and_sunflower.py
Optional: -- --render /path/to/preview.png --preview-frame 112

Only Horse_motion is animated. The camera and sunflower remain stationary.
The original mesh topology/material indices are preserved; coloured CURVE
objects are desktop wire previews and are excluded from the C64 mesh exporter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.c643d.colors import C64_PALETTE

FPS = 25
END = 250
SAMPLE_STEP = 3


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_suffix('.blend'))
    parser.add_argument('--render', type=Path)
    parser.add_argument('--preview-frame', type=int, default=112)
    return parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])


def source_obj(slug):
    obj_path = ROOT / 'objects' / (slug + '.obj')
    vertices, faces, face_materials = [], [], []
    material = None
    for line in obj_path.read_text().splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == 'v':
            # Right-handed conversion from the source's Y-up to Blender Z-up.
            x, y, z = map(float, fields[1:4])
            vertices.append((x, -z, y))
        elif fields[0] == 'usemtl':
            material = fields[1]
        elif fields[0] == 'f':
            faces.append([int(v.split('/')[0]) - 1 for v in fields[1:]])
            face_materials.append(material)
    colours = {}
    mtl_path = obj_path.with_suffix('.mtl')
    for line in mtl_path.read_text().splitlines():
        fields = line.split()
        if fields and fields[0] == 'newmtl':
            material = fields[1]
        elif fields and fields[0] == 'Kd':
            colours[material] = tuple(map(float, fields[1:4]))
    return vertices, faces, face_materials, colours, {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (obj_path, mtl_path)
    }


def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def material(name, rgb, *, wire=False):
    mat = bpy.data.materials.new(('Wire ' if wire else 'C64 ') + name)
    mat.diffuse_color = (*rgb, 1)
    mat['c643d_color'] = C64_PALETTE[name][0]
    mat['source_Kd'] = list(rgb)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*map(linear, rgb), 1) if wire else (0, 0, 0, 1)
    emission.inputs['Strength'].default_value = 1
    mat.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
    return mat


def import_asset(slug, name, collection):
    verts, faces, face_materials, colours, hashes = source_obj(slug)
    mesh = bpy.data.meshes.new(name + '_original_mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    names = list(colours)
    for key in names:
        mesh.materials.append(material(key, colours[key]))
    for polygon, key in zip(mesh.polygons, face_materials):
        polygon.material_index = names.index(key)
    obj['c643d_export'] = True
    obj['source_asset'] = '//../../objects/' + slug + '.obj'
    obj['source_sha256'] = json.dumps(hashes, sort_keys=True)
    obj['description'] = 'Original HiFi vertices, polygons and native C64 face colours; no decimation.'
    return obj, colours


def add_wire_preview(obj, colours, collection, camera):
    """Draw source polygon edges, without introducing triangulation diagonals."""
    bpy.context.view_layer.update()
    toward_camera = (obj.matrix_world.inverted() @ camera.location).normalized()
    edge_material = {}
    edge_score = {}
    for polygon in obj.data.polygons:
        score = polygon.normal.dot(toward_camera)
        for a, b in polygon.edge_keys:
            key = tuple(sorted((a, b)))
            if key not in edge_score or score > edge_score[key]:
                edge_score[key] = score
                edge_material[key] = polygon.material_index
    for index, (name, rgb) in enumerate(colours.items()):
        curve = bpy.data.curves.new(obj.name + '_' + name + '_edges', 'CURVE')
        curve.dimensions = '3D'
        curve.resolution_u = 1
        curve.bevel_depth = .0055
        curve.bevel_resolution = 0
        curve.resolution_u = 1
        curve.materials.append(material(name, rgb, wire=True))
        for (a, b), mat_index in edge_material.items():
            if mat_index != index:
                continue
            spline = curve.splines.new('POLY')
            spline.points.add(1)
            spline.points[0].co = (*obj.data.vertices[a].co, 1)
            spline.points[1].co = (*obj.data.vertices[b].co, 1)
        wire = bpy.data.objects.new(obj.name + ' preview ' + name, curve)
        collection.objects.link(wire)
        wire.parent = obj
        wire['c643d_export'] = False
        wire['description'] = 'Blender wire preview only. Not exported to C64.'


def animate(rig):
    # Rest -> approach -> two small sniffing beats -> pause -> ease back.
    # Frame END+1 equals frame 1, so the loop has no duplicate endpoint sample.
    keys = [
        (1, 0, 0), (30, 0, 0), (83, 1, 0),
        (103, 1, .55), (115, 1, 0),
        (135, 1, 1), (150, 1, 0),
        (178, 1, 0), (231, 0, 0), (END + 1, 0, 0),
    ]
    for frame, lean, sniff in keys:
        rig.location = (-.74 + .40 * lean + .025 * sniff,
                        -.57 + .045 * lean + .014 * sniff,
                        -1.15 + .10 * lean + .018 * sniff)
        rig.rotation_euler = (0, math.radians(3.0 * lean - .65 * sniff), 0)
        rig.keyframe_insert(data_path='location', frame=frame)
        rig.keyframe_insert(data_path='rotation_euler', frame=frame)
    rig.animation_data.action.name = 'Lean in - sniff twice - ease back'
    for fcurve in rig.animation_data.action.fcurves:
        for key in fcurve.keyframe_points:
            key.interpolation = 'BEZIER'
            key.handle_left_type = key.handle_right_type = 'AUTO_CLAMPED'


def validate(scene, horse, flower, camera):
    expected = {horse.name: (135, 299, 178), flower.name: (243, 443, 238)}
    for obj in (horse, flower):
        actual = (len(obj.data.vertices), len(obj.data.edges), len(obj.data.polygons))
        assert actual == expected[obj.name], (obj.name, actual)
    frozen = None
    first = None
    horse_moved = False
    for frame in range(1, END + 2):
        scene.frame_set(frame)
        current = tuple(tuple(v for row in o.matrix_world for v in row) for o in (flower, camera))
        if frozen is None:
            frozen = current
            first = horse.matrix_world.copy()
        assert current == frozen, f'Camera or flower moved at {frame}'
        horse_moved |= horse.matrix_world != first
    assert horse_moved, 'Horse animation is static'
    assert horse.matrix_world == first, 'Loop endpoint must match opening pose'
    scene.frame_set(1)


def main():
    args = arguments()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = 'horse_and_sunflower'
    scene.frame_start = 1
    scene.frame_end = END
    scene.render.fps = FPS
    scene.render.resolution_x = 768
    scene.render.resolution_y = 576
    scene.render.resolution_percentage = 100
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    world = bpy.data.worlds.new('Black background')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)
    scene.world = world
    assets = bpy.data.collections.new('Original HiFi meshes - C64 export')
    preview = bpy.data.collections.new('Coloured wire preview - Blender only')
    scene.collection.children.link(assets)
    scene.collection.children.link(preview)
    horse, horse_colours = import_asset('horse_head_hifi', 'Horse_head_hifi', assets)
    flower, flower_colours = import_asset('sunflower_torus_hifi', 'Sunflower_torus_hifi', assets)
    rig = bpy.data.objects.new('Horse_motion', None)
    assets.objects.link(rig)
    rig.empty_display_type = 'PLAIN_AXES'
    rig.empty_display_size = .3
    horse.parent = rig
    horse.location = (.50, 0, 1.50)
    animate(rig)
    flower.location = (3.12, 0, 0)
    flower.scale = (.76,) * 3
    flower.rotation_euler.z = math.radians(148)
    flower['description'] = 'Stationary flower; brown/yellow front points partly toward the camera.'
    data = bpy.data.cameras.new('Close side view')
    camera = bpy.data.objects.new('Camera', data)
    assets.objects.link(camera)
    camera.location = (1.64, -11.80, 1.05)
    target = Vector((1.64, 0, 1.05))
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.type = 'PERSP'
    data.lens = 82
    data.sensor_width = 36
    data.clip_start = .1
    data.clip_end = 100
    scene.camera = camera
    scene.frame_set(1)
    add_wire_preview(horse, horse_colours, preview, camera)
    add_wire_preview(flower, flower_colours, preview, camera)
    scene['c643d_title'] = 'HORSE AND SUNFLOWER'
    scene['c643d_version'] = '0.6.7-rc5'
    scene['c643d_renderer'] = 'yunroll-cart-v7-scene'
    scene['c643d_prefer'] = 'fps'
    scene['c643d_sample_step'] = SAMPLE_STEP
    scene['c643d_frame_ticks'] = 6
    scene['description'] = 'Ten-second close side-view loop. Only the horse moves; two gentle sniffs, then withdrawal.'
    for frame, name in [(1, 'REST'), (83, 'CLOSE TO FLOWER'), (103, 'SNIFF 1'), (135, 'SNIFF 2'), (178, 'EASE BACK')]:
        scene.timeline_markers.new(name, frame=frame)
    validate(scene, horse, flower, camera)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.overlay.show_overlays = False
                area.spaces.active.shading.type = 'MATERIAL'
                area.spaces.active.shading.use_scene_world = True
                area.spaces.active.shading.use_scene_lights = True
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output), compress=True)
    print(f'Saved {args.output}: original 378 vertices / 416 faces; camera and flower verified static.', flush=True)
    if args.render:
        scene.frame_set(args.preview_frame)
        args.render = args.render.resolve()
        args.render.parent.mkdir(parents=True, exist_ok=True)
        scene.render.filepath = str(args.render)
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
