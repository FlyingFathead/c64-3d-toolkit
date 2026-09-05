"""Build a 40-second orbiting cubes/marbles Blender example from falling_cubes.

blender --background --python examples/blender_marbles/dont_lose_your_marbles.py

Rigid-body motion is evaluated sequentially and baked to ordinary transform
keyframes before saving, so the delivered .blend scrubs/exports reproducibly.
Re-run this script to change the pours or physics. The original stays intact.
"""
from __future__ import annotations
import argparse
import math
import random
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Quaternion

FPS=25
END=1000


def args():
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,default=Path(__file__).with_suffix('.blend'))
    p.add_argument('--seed',type=int,default=6502)
    return p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])


def rigid(obj,kind):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    if obj.rigid_body is None:bpy.ops.rigidbody.object_add()
    obj.rigid_body.type=kind
    return obj.rigid_body


def add_finale(scene,floor,objects,poses,rng):
    """Authored fracture: physics gives way to drifting, star-like fragments."""
    burst=END-149
    floor_mat=floor.data.materials[0]
    corners=[(-5.8,-4.2),(5.8,-4.2),(5.8,4.2),(-5.8,4.2)]
    perimeter=[]
    for a,b in zip(corners,corners[1:]+corners[:1]):
        perimeter.extend([(a[0]+(b[0]-a[0])*j/8,a[1]+(b[1]-a[1])*j/8) for j in range(8)])
    center=(.25,-.15)
    def drift(loc,rot,scale,axis,speed,spin,target,frame):
        t=(frame-burst)/FPS;p=(frame-burst)/(END-burst)
        direction=Vector((loc.x,loc.y,1.5)).normalized()
        ballistic=loc+direction*speed*t+Vector((0,0,1.8*t))
        # Gradually remove gravity and let the camera follow the new constellation.
        scene.frame_set(frame)
        destination=scene.camera.matrix_world@target
        u=max(0,min(1,(p-.22)/.78));u=u*u*(3-2*u)
        position=ballistic.lerp(destination,u)
        size=1-.965*u
        return Matrix.LocRotScale(position,Quaternion(axis,spin*t)@rot,scale*size)
    shards=[]
    for i,(a,b) in enumerate(zip(perimeter,perimeter[1:]+perimeter[:1])):
        triangle=[center,a,b];cx=sum(v[0] for v in triangle)/3;cy=sum(v[1] for v in triangle)/3
        verts=[(x-cx,y-cy,z) for z in (0,-.7) for x,y in triangle]
        mesh=bpy.data.meshes.new(f'TableShardMesh{i+1}')
        mesh.from_pydata(verts,[],[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)]);mesh.update()
        shard=bpy.data.objects.new(f'TableShard{i+1:02d}',mesh);scene.collection.objects.link(shard)
        shard.data.materials.append(floor_mat);shard.rotation_mode='QUATERNION'
        shard['c643d_visible_start']=burst
        for frame in (1,burst-1):
            shard.location=(cx,cy,-45);shard.keyframe_insert(data_path='location',frame=frame)
            shard.rotation_quaternion=(1,0,0,0);shard.keyframe_insert(data_path='rotation_quaternion',frame=frame)
            shard.scale=(1,1,1);shard.keyframe_insert(data_path='scale',frame=frame)
        axis=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1))).normalized()
        target=Vector((rng.uniform(-9,9),rng.uniform(-6.3,6.3),-28))
        speed=rng.uniform(1.1,2.0);spin=rng.uniform(.7,1.6)
        for frame in range(burst,END+1):
            m=drift(Vector((cx,cy,0)),Quaternion(),Vector((1,1,1)),axis,speed,spin,target,frame)
            shard.location,shard.rotation_quaternion,shard.scale=m.decompose()
            for key in ('location','rotation_quaternion','scale'):shard.keyframe_insert(data_path=key,frame=frame)
        for fc in shard.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='CONSTANT' if k.co.x<burst else 'LINEAR'
        shards.append(shard)
    bpy.ops.object.select_all(action='DESELECT');floor.select_set(True);bpy.context.view_layer.objects.active=floor
    bpy.ops.rigidbody.object_remove();floor.animation_data_clear()
    for frame,z in ((1,-.35),(burst-1,-.35),(burst,-45),(END,-45)):
        floor.location.z=z;floor.keyframe_insert(data_path='location',frame=frame)
    floor['c643d_visible_end']=burst-1
    for fc in floor.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='CONSTANT'
    scattered=0
    for o in objects:
        loc,rot,scale=poses[o.name][burst-1].decompose()
        if loc.z < -4 or abs(loc.x)>8 or abs(loc.y)>6:continue
        scattered+=1;axis=Vector((rng.random(),rng.random(),rng.random())).normalized()
        target=Vector((rng.uniform(-9,9),rng.uniform(-6.3,6.3),-28))
        for frame in range(burst,END+1):
            poses[o.name][frame-1]=drift(loc,rot,scale,axis,1.5,1.5,target,frame)
    scene['c643d_blast_frame']=burst
    return dict(frame=burst,seconds=(burst-1)/FPS,table_shards=len(shards),scattered_objects=scattered,method='authored drifting fracture to constellation after rigid-body simulation')


def main():
    a=args();rng=random.Random(a.seed)
    source=Path(__file__).resolve().parents[1]/'blender_falling_cubes/falling_cubes_c64.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=END;scene.render.fps=FPS
    scene.render.resolution_x=256;scene.render.resolution_y=192;scene.render.resolution_percentage=100
    scene.gravity=(0,0,-9.81)
    floor=bpy.data.objects['Floor'];floor.rotation_euler=(0,0,0)
    floor.rigid_body.friction=0.55;floor.rigid_body.restitution=0.38
    floor['description']='Level original tabletop; objects spill after physical impacts.'
    materials=[bpy.data.materials[n] for n in ('C64 Yellow','C64 Cyan','C64 Light Red','C64 Light Blue')]
    cubes=sorted([o for o in scene.objects if o.name.startswith('FallingCube')],key=lambda o:o.name)
    objects=[];schedule=[]
    # Cubes establish the pile, then alternating marble and cube waves.
    waves=[('cube',6,0.2,0.45),('marble',10,4.0,0.28),('cube',5,10.5,0.34),('marble',10,14.0,0.28),('cube',4,22.0,0.34),('marble',10,26.0,0.28)]
    serial=0
    for wave,(kind,count,start,spacing) in enumerate(waves):
        for i in range(count):
            if wave==0:obj=cubes[i]
            elif kind=='cube':
                bpy.ops.mesh.primitive_cube_add(size=1.44)
                obj=bpy.context.object
            else:
                bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=0.57)
                obj=bpy.context.object
            obj.animation_data_clear()
            serial+=1;obj.name=f'{kind.title()}_{serial:02d}'
            obj.data.materials.clear();obj.data.materials.append(materials[(i+wave)%4])
            # Keep each release well inside the table, aimed through the cube pile.
            if kind=='cube':
                x,y=[(-1.7,-1.1),(1.7,1.1),(-1.7,1.1),(1.7,-1.1),(0,0),(0,0)][i%6]
            else:
                theta=[0,math.pi,math.pi/2,3*math.pi/2][i%4]+.12*wave
                x=1.4*math.cos(theta);y=1.1*math.sin(theta)
            x+=rng.uniform(-.12,.12);y+=rng.uniform(-.12,.12)
            release=1+round((start+i*spacing)*FPS)
            z=11.8+rng.uniform(-0.3,0.3)
            dx=0.0
            dy=0.0
            rb=rigid(obj,'ACTIVE');rb.mass=2.2 if kind=='marble' else 0.9
            rb.collision_shape='SPHERE' if kind=='marble' else 'BOX'
            rb.use_margin=True;rb.collision_margin=0.015
            rb.restitution=0.62 if kind=='marble' else 0.28
            rb.friction=0.20 if kind=='marble' else 0.42
            rb.linear_damping=0.015;rb.angular_damping=0.035
            obj.rotation_euler=(rng.random()*.25,rng.random()*.25,rng.random()*.25)
            # Isolate queued emitters from live bodies until their release.
            rb.collision_collections=[False]*19+[True]
            rb.keyframe_insert(data_path='collision_collections',frame=1)
            rb.keyframe_insert(data_path='collision_collections',frame=release-1)
            rb.collision_collections=[True]+[False]*19
            rb.keyframe_insert(data_path='collision_collections',frame=release)
            rb.kinematic=True;rb.keyframe_insert(data_path='kinematic',frame=1)
            rb.keyframe_insert(data_path='kinematic',frame=release-1)
            rb.kinematic=False;rb.keyframe_insert(data_path='kinematic',frame=release)
            # Waiting bodies sit above the scene in distinct parking slots. They
            # never sweep upward through the existing pile during activation.
            # Export visibility starts only once the object reaches its inlet.
            obj['c643d_visible_start']=release-2
            park=25+serial*3
            for f,pos in [(1,(x,y,park)),(max(1,release-3),(x,y,park)),(release-2,(x,y,z)),(release-1,(x,y,z))]:
                obj.location=pos;obj.keyframe_insert(data_path='location',frame=f)
            for fc in obj.animation_data.action.fcurves:
                for k in fc.keyframe_points:k.interpolation='CONSTANT'
            objects.append(obj);schedule.append(dict(object=obj.name,kind=kind,release_frame=release,release_seconds=(release-1)/FPS,color=int(obj.data.materials[0]['c643d_color']),release_xy=[x,y]))
    world=scene.rigidbody_world;world.substeps_per_frame=6;world.solver_iterations=20
    world.point_cache.frame_start=1;world.point_cache.frame_end=END
    camera=scene.camera;camera.data.lens=42;camera.data.clip_end=1000
    # One continuous 360-degree tracking shot; endpoint at 1001 avoids duplicating
    # the opening camera pose in the exported samples.
    target=Vector((0,0,2.4));radius=22.0;angle0=math.atan2(-18,12.5)
    camera.animation_data_clear()
    for f in range(1,END+2):
        phase=(f-1)/END;angle=angle0+math.tau*phase
        camera.location=(radius*math.cos(angle),radius*math.sin(angle),11.0+0.7*math.sin(math.tau*phase))
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.keyframe_insert(data_path='location',frame=f);camera.keyframe_insert(data_path='rotation_euler',frame=f)
    scene['c643d_title']="DON'T LOSE YOUR MARBLES"
    scene['c643d_sample_step']=5;scene['c643d_frame_ticks']=7
    scene['description']='40 seconds: cubes, marbles, cubes, marbles, cubes; full orbit; source C64 palette.'
    a.output=a.output.resolve();a.output.parent.mkdir(parents=True,exist_ok=True)
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.output.with_name(a.output.stem+'_physics.blend')),compress=True)
    print('Evaluating rigid-body simulation...',flush=True)
    poses={o.name:[] for o in objects}
    for f in range(1,END+1):
        scene.frame_set(f);dg=bpy.context.evaluated_depsgraph_get()
        for o in objects:poses[o.name].append(o.evaluated_get(dg).matrix_world.copy())
        if f%125==0:print(f'physics {f}/{END}',flush=True)
    finale=add_finale(scene,floor,objects,poses,rng)
    # Keep all physics settings in the reproducible generator; bake the example.
    for o in objects:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
        bpy.ops.rigidbody.object_remove();o.animation_data_clear();o.rotation_mode='QUATERNION'
        for f,matrix in enumerate(poses[o.name],1):
            loc,rot,scale=matrix.decompose();o.location=loc;o.rotation_quaternion=rot;o.scale=scale
            o.keyframe_insert(data_path='location',frame=f);o.keyframe_insert(data_path='rotation_quaternion',frame=f);o.keyframe_insert(data_path='scale',frame=f)
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'
    for fc in camera.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='LINEAR'
    scene.frame_set(1)
    a.output=a.output.resolve();a.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.output),compress=True)
    import json
    impacts=[]
    for o,entry in zip(objects,schedule):
        positions=[m.translation for m in poses[o.name]]
        near=[(i+1,v) for i,v in enumerate(positions) if i+1>=entry['release_frame'] and -0.2<=v.z<=3.0 and abs(v.x)<5.8 and abs(v.y)<4.2]
        rebounds=sum(1 for i in range(max(1,entry['release_frame']),END-1) if positions[i].z<4 and positions[i].z-positions[i-1].z<-.02 and positions[i+1].z-positions[i].z>.02)
        impacts.append(dict(object=o.name,entered_table_pile_volume=bool(near),first_table_volume_frame=near[0][0] if near else None,rebounds=rebounds))
    report={'source':source.name,'fps':FPS,'frames':END,'duration_seconds':END/FPS,'camera_orbit_degrees':360,'objects':len(objects),'pours':schedule,'fallen_below_table':sum(poses[o.name][-1].translation.z < -2 for o in objects),'baked_transform_animation':True,'table_pile_entries':sum(x['entered_table_pile_volume'] for x in impacts),'impact_checks':impacts,'finale':finale}
    a.output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
