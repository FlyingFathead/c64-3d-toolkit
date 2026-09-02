"""Generate the falling-cubes Blender demo without manual scene editing.

Usage:
    blender --background --python examples/blender/falling_cubes_c64.py
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _args():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument('--output',help='output .blend path (default: beside this script)')
    return p.parse_args(argv)


def _material(name,color,c64_index):
    material=bpy.data.materials.new(name)
    material.diffuse_color=(*color,1.0)
    material['c643d_color']=c64_index
    return material


def _rigid_body(obj,kind):
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type=kind
    obj.select_set(False)


def main():
    args=_args()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.frame_start=1; scene.frame_end=72
    scene.render.fps=24
    scene.render.resolution_x=256; scene.render.resolution_y=144
    scene.render.resolution_percentage=100
    scene.gravity=(0.0,0.0,-9.81)

    colors=[
        _material('C64 Yellow',(0.93,0.93,0.47),7),
        _material('C64 Cyan',(0.67,1.0,0.93),3),
        _material('C64 Light Red',(1.0,0.47,0.47),10),
        _material('C64 Light Blue',(0.0,0.53,1.0),14),
    ]
    floor_material=_material('C64 Gray',(0.47,0.47,0.47),12)

    bpy.ops.mesh.primitive_cube_add(location=(0.0,0.0,-0.35),scale=(5.8,4.2,0.35))
    floor=bpy.context.object; floor.name='Floor'
    floor.data.materials.append(floor_material)
    _rigid_body(floor,'PASSIVE')

    positions=[(-1.6,0.2,8.8),(0.0,-0.4,10.8),(1.5,0.4,12.8),(-0.8,0.1,14.8),(0.9,-0.2,16.8),(0.0,0.4,18.8)]
    for i,position in enumerate(positions):
        bpy.ops.mesh.primitive_cube_add(location=position,scale=(0.72,0.72,0.72))
        cube=bpy.context.object; cube.name=f'FallingCube{i+1:02d}'
        cube.rotation_euler=(0.19*i,0.31*i,0.23*i)
        cube.data.materials.append(colors[i%len(colors)])
        _rigid_body(cube,'ACTIVE')
        cube.rigid_body.mass=1.0
        cube.rigid_body.restitution=0.32
        cube.rigid_body.friction=0.55
        cube.rigid_body.linear_damping=0.04
        cube.rigid_body.angular_damping=0.08

    bpy.ops.object.camera_add(location=(12.5,-18.0,10.0))
    camera=bpy.context.object; camera.name='Camera'
    target=Vector((0.0,0.0,4.2))
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.lens=48.0
    scene.camera=camera

    scene.frame_set(1)
    output=Path(args.output).resolve() if args.output else Path(__file__).with_suffix('.blend').resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f'c643d: wrote falling-cubes demo -> {output}')


if __name__=='__main__':
    main()
