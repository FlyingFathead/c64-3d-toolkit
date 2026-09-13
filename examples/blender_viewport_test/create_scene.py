"""Blender test card: readable directions, centre cross, zoom through four edges.

blender -b --python examples/blender_viewport_test/create_scene.py -- --output build/viewport-test.blend
"""
import argparse
from pathlib import Path
import sys
import math
import bpy


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--variant',choices=('zoom','tracking'),default='zoom')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.edit.keyframe_new_interpolation_type='LINEAR'
    scene=bpy.context.scene
    scene['c643d_title']='BLENDER VIEWPORT TEST' if args.variant=='zoom' else 'BLENDER TRACKING TEST'
    scene.frame_start=1;scene.frame_end=16
    scene.render.resolution_x=960;scene.render.resolution_y=576
    scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
    scene.render.fps=25
    materials={}
    for name,color,rgb in [('white',1,(1,1,1,1)),('red',2,(1,0,0,1)),
                           ('green',5,(0,1,0,1)),('cyan',3,(0,1,1,1)),('yellow',7,(1,1,0,1)),('grey',12,(.3,.3,.3,1))]:
        mat=bpy.data.materials.new(name);mat['c643d_color']=color;mat.diffuse_color=rgb
        materials[name]=mat
    def line(name,a,b,color,width=.012,z=0):
        dx,dy=b[0]-a[0],b[1]-a[1];length=(dx*dx+dy*dy)**.5
        nx,ny=-dy/length*width/2,dx/length*width/2
        verts=[(a[0]+nx,a[1]+ny,z),(a[0]-nx,a[1]-ny,z),
               (b[0]-nx,b[1]-ny,z),(b[0]+nx,b[1]+ny,z)]
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.update()
        obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.data.materials.append(materials[color])
    def label(text,position,color,size=.38):
        curve=bpy.data.curves.new(text,'FONT');curve.body=text;curve.size=size;curve.align_x='CENTER';curve.resolution_u=2
        obj=bpy.data.objects.new(text,curve);scene.collection.objects.link(obj);obj.location=(*position,.02)
        obj.data.materials.append(materials[color]);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
        bpy.ops.object.convert(target='MESH');obj.select_set(False)
    for x in (-3,-2,-1,1,2,3):line('grid-x'+str(x),(x,-2.4),(x,2.4),'white')
    for y in (-2,-1,1,2):line('grid-y'+str(y),(-4,y),(4,y),'white')
    line('left',(-4,-2.4),(-4,2.4),'red',.035)
    line('right',(4,-2.4),(4,2.4),'green',.035)
    line('top',(-4,2.4),(4,2.4),'cyan',.035)
    line('bottom',(-4,-2.4),(4,-2.4),'yellow',.035)
    line('centre-x',(-.42,0),(.42,0),'white',.035,.04)
    line('centre-y',(0,-.42),(0,.42),'white',.035,.04)
    line('right-arrow',(1.1,-.3),(2.0,-.3),'green',.035,.04)
    line('arrow-upper',(1.75,-.05),(2.0,-.3),'green',.035,.04)
    line('arrow-lower',(1.75,-.55),(2.0,-.3),'green',.035,.04)
    label('LEFT',(-2.4,.25),'red')
    label('RIGHT',(2.4,.25),'green')
    label('TOP',(0,1.5),'cyan')
    label('BOTTOM',(0,-1.8),'yellow')
    camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(camera)
    camera.location=(0,0,10);camera.data.lens=36;camera.data.sensor_width=36
    camera.data.sensor_fit='HORIZONTAL';scene.camera=camera
    if args.variant=='zoom':
        camera.data.keyframe_insert('lens',frame=1)
        camera.data.lens=72;camera.data.keyframe_insert('lens',frame=16)
    else:
        target=bpy.data.objects.new('Card centre tracking target',None)
        scene.collection.objects.link(target)
        target.rotation_euler.x=-math.pi/2  # target Z supplies the card's +Y up
        track=camera.constraints.new('TRACK_TO');track.target=target
        track.track_axis='TRACK_NEGATIVE_Z';track.up_axis='UP_Y';track.use_target_z=True
        for frame,position in [(1,(-3,-1.4,10)),(8,(0,1.0,10)),(16,(3,-1.4,10))]:
            camera.location=position;camera.keyframe_insert('location',frame=frame)
    scene.frame_set(1)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()))


if __name__=='__main__':main()
