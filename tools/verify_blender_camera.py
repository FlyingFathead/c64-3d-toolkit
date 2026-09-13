"""Blender integration check: camera framing, outward faces and material IDs.

blender --background --python tools/verify_blender_camera.py -- --output build/blender-camera-validation.json

Includes a reflected object, a rotated/shifted perspective camera and a moving
object. Runs the production exporter, then compares against Blender's evaluated
vertices, normals and world_to_camera_view projection.
"""
import argparse
import json
from pathlib import Path
import runpy
import sys
import tempfile

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector
from mathutils.geometry import normal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--viewport-width',type=int,choices=(256,320),default=320)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 2
    scene.render.resolution_x, scene.render.resolution_y = args.viewport_width * 3, 576
    scene.render.resolution_percentage = 100
    objects = []
    for index in range(2):
        bpy.ops.mesh.primitive_cube_add(size=1.5, location=(index * 2 - 1, 0, 0))
        obj = bpy.context.object
        obj.name = 'Cube_' + str(index)
        obj.scale = (-1.1 if index else 1.1, .7, 1.3)
        obj.rotation_euler = (.14, -.28, .21)
        for color in (3, 4, 5, 7, 9, 14):
            material = bpy.data.materials.new(str(color))
            material['c643d_color'] = color
            obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.material_index = polygon.index
        obj.keyframe_insert(data_path='location', frame=1)
        obj.location.z += .25
        obj.keyframe_insert(data_path='location', frame=2)
        objects.append(obj)
    camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.location = (3, -9, 4)
    camera.rotation_euler = (-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.lens = 46
    camera.data.shift_x = .08
    camera.data.shift_y = -.03
    camera.scale = (1.5, .8, 2.0)
    with tempfile.TemporaryDirectory(prefix='c643d-camera-') as td:
        output = Path(td) / 'camera.c643dscene'
        original_argv = sys.argv[:]
        sys.argv = ['blender_export.py', '--', '--output', str(output), '--viewport-width',str(args.viewport_width),'--viewport-height', '192']
        try:
            runpy.run_path(str(Path(__file__).with_name('blender_export.py')), run_name='__main__')
        finally:
            sys.argv = original_argv
        exported = json.loads(output.read_text())
    max_projection_error = 0
    min_normal_dot = 1
    for frame in exported['frames']:
        scene.frame_set(frame['source_frame'])
        dg = bpy.context.evaluated_depsgraph_get()
        vertex_offset, face_offset = 0, 0
        for original in objects:
            obj = original.evaluated_get(dg)
            transform = Matrix.Diagonal((1, 1, -1, 1)) @ camera.matrix_world.normalized().inverted() @ obj.matrix_world
            normal_transform = transform.inverted().transposed().to_3x3()
            for vertex in obj.data.vertices:
                p = frame['vertices'][vertex_offset + vertex.index]
                blender_view = world_to_camera_view(scene, camera, obj.matrix_world @ vertex.co)
                projection = frame['projection']
                pixel = (projection['cx'] + projection['fx'] * p[0] / p[2],
                         projection['cy'] - projection['fy'] * p[1] / p[2])
                error = max(abs(pixel[0] - blender_view.x * args.viewport_width), abs(pixel[1] - (1 - blender_view.y) * 192))
                max_projection_error = max(max_projection_error, error)
                assert error < .0001, (original.name, vertex.index, pixel, blender_view)
            for polygon in obj.data.polygons:
                fi = face_offset + polygon.index
                indices = exported['topology']['faces'][fi]
                actual_normal = normal([Vector(frame['vertices'][i]) for i in indices])
                expected_normal = (normal_transform @ polygon.normal).normalized()
                agreement = actual_normal.dot(expected_normal)
                min_normal_dot = min(min_normal_dot, agreement)
                assert agreement > .99999, (original.name, polygon.index, agreement)
                expected_color = obj.data.materials[polygon.material_index]['c643d_color']
                assert exported['topology']['face_colors'][fi] == expected_color
            vertex_offset += len(obj.data.vertices)
            face_offset += len(obj.data.polygons)
    result = dict(viewport_width=args.viewport_width,blender=bpy.app.version_string, frames=2, objects=2,
                  mirrored_object=True, shifted_rotated_camera=True, scaled_camera=True,
                  max_projection_error_pixels=max_projection_error,
                  min_outward_normal_dot=min_normal_dot, face_material_ids_preserved=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
