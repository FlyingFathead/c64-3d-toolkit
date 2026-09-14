"""Create an original road/camera-crossing diagnostic in Blender.

blender -b --factory-startup --python tools/create_camera_crossing.py -- --output scene.blend
"""
import argparse
from pathlib import Path
import sys
import bpy


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.frame_start=1;scene.frame_end=17;scene.render.fps=25
    scene.render.resolution_x=960;scene.render.resolution_y=576
    scene.render.resolution_percentage=100
    scene['c643d_title']='CAMERA CROSSING ROAD'
    parent=bpy.data.objects.new('Road animation',None)
    scene.collection.objects.link(parent)
    def box(name,location,scale,color):
        bpy.ops.mesh.primitive_cube_add(size=2,location=location)
        obj=bpy.context.object;obj.name=name;obj.scale=scale;obj.parent=parent
        mat=bpy.data.materials.new(name+' material');mat['c643d_color']=color
        obj.data.materials.append(mat)
        return obj
    box('Road',(0,-1.2,-5),(2,.04,4),12)
    for z in (-2,-4,-6,-8):
        box('Lane mark',(0,-1.14,z),(.07,.025,.38),1)
    box('Left marker',(-1.6,-.6,-4),(.12,.6,.12),2)
    box('Right marker',(1.6,-.6,-6),(.12,.6,.12),5)
    for frame,z in ((1,0),(9,12),(17,0)):
        parent.location.z=z;parent.keyframe_insert(data_path='location',frame=frame)
    for curve in parent.animation_data.action.fcurves:
        for key in curve.keyframe_points:key.interpolation='LINEAR'
    camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(camera);scene.camera=camera
    camera.data.lens=28;camera.data.clip_start=.01
    scene.frame_set(1)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()))

if __name__=='__main__':main()
