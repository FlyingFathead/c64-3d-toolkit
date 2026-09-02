"""Generate Harry's deterministic 40-cube Blender rigid-body scene.

This is the fuller Blender authoring/stress example. The much smaller
``falling_cubes_c64.py`` variant is intended for C64 table compilation.

Usage:
    blender --background --python examples/blender/falling_cubes_full.py
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _args():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',help='output .blend path (default: beside this script)')
    return parser.parse_args(argv)


def make_cube_cluster(cx,cy,cz,size=0.6):
    for x in (-0.5,0.5):
        for y in (-0.5,0.5):
            for z in (-0.5,0.5):
                bpy.ops.mesh.primitive_cube_add(
                    location=(cx+x*size,cy+y*size,cz+z*size),
                    scale=(size/2,size/2,size/2),
                )
                obj=bpy.context.object
                obj.rotation_euler=(
                    random.uniform(-0.05,0.05),
                    random.uniform(-0.05,0.05),
                    random.uniform(-0.05,0.05),
                )
                bpy.ops.rigidbody.object_add()
                obj.rigid_body.type='ACTIVE'
                obj.rigid_body.mass=0.25
                obj.rigid_body.friction=0.6
                obj.rigid_body.restitution=0.3


def main():
    args=_args()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    random.seed(1337)

    bpy.ops.mesh.primitive_cube_add(location=(0,0,-0.25),scale=(6,6,0.25))
    floor=bpy.context.object
    floor.name='Floor'
    bpy.ops.rigidbody.object_add()
    floor.rigid_body.type='PASSIVE'
    floor.rigid_body.friction=0.8

    make_cube_cluster(-1.5,0.0,5.0)
    make_cube_cluster(0.0,0.2,7.0)
    make_cube_cluster(1.5,-0.3,9.0)
    make_cube_cluster(-0.7,-1.0,11.0)
    make_cube_cluster(1.0,1.0,13.0)

    bpy.ops.object.camera_add(location=(12,-16,9))
    camera=bpy.context.object
    bpy.context.scene.camera=camera
    direction=Vector((0,0,3))-camera.location
    camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

    scene=bpy.context.scene
    scene.frame_start=1
    scene.frame_end=180
    scene.render.fps=30
    scene.gravity=(0,0,-9.81)

    output=Path(args.output).resolve() if args.output else Path(__file__).with_suffix('.blend').resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print(f'Created {output}')


if __name__=='__main__':
    main()
