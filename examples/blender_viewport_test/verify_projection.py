"""Run inside either test .blend to compare every exported vertex to Blender."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import tempfile
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    root=Path(__file__).resolve().parents[2]
    original_argv=sys.argv[:]
    with tempfile.TemporaryDirectory() as td:
        output=Path(td)/'scene.c643dscene'
        sys.argv=['blender_export.py','--','--output',str(output),'--viewport-height','192']
        try:runpy.run_path(str(root/'tools/blender_export.py'),run_name='__main__')
        finally:sys.argv=original_argv
        data=json.loads(output.read_text())
    assert data['viewport']==dict(width=320,height=192)
    scene=bpy.context.scene
    objects=sorted([o for o in scene.objects if o.type=='MESH' and not o.hide_render],key=lambda o:o.name)
    maximum=0.;centre_error=0.;count=0
    for frame in data['frames']:
        scene.frame_set(frame['source_frame'])
        dg=bpy.context.evaluated_depsgraph_get()
        camera=scene.camera.evaluated_get(dg)
        centre=world_to_camera_view(scene,camera,Vector((0,0,0)))
        centre_error=max(centre_error,abs(centre.x-.5),abs(centre.y-.5))
        points=[]
        for original in objects:
            obj=original.evaluated_get(dg);mesh=obj.to_mesh()
            points.extend(world_to_camera_view(scene,camera,obj.matrix_world@v.co) for v in mesh.vertices)
            obj.to_mesh_clear()
        assert len(points)==len(frame['vertices'])
        proj=frame['projection']
        for (x,y,z),expected in zip(frame['vertices'],points):
            error=max(abs(proj['cx']+proj['fx']*x/z-expected.x*320),
                      abs(proj['cy']-proj['fy']*y/z-(1-expected.y)*192))
            maximum=max(maximum,error);count+=1
            assert error<.0002,(frame['source_frame'],error)
    assert centre_error<.000001,centre_error
    record=dict(passed=True,blender=bpy.app.version_string,frames=len(data['frames']),
                vertices_checked=count,maximum_projection_error_pixels=maximum,
                centre_error_normalized=centre_error,viewport=data['viewport'],
                source=Path(bpy.data.filepath).name)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2)+'\n');print(record)


if __name__=='__main__':main()
