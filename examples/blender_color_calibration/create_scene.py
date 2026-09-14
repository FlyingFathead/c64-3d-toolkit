"""Create an editable palette-index calibration card and inspect real materials.

Run with Blender: blender -b --factory-startup --python create_scene.py
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import bpy

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))
from tools.c643d.colors import c64_color_name, nearest_c64_color_index


def linear(channel):
    v=channel/255
    return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene['c643d_title']='PALETTE CALIBRATION'
    scene.frame_start=1;scene.frame_end=1
    scene.render.resolution_x=960;scene.render.resolution_y=576;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    scene.view_settings.exposure=0;scene.view_settings.gamma=1
    spec=importlib.util.spec_from_file_location('exporter',ROOT/'tools/blender_export.py')
    exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
    palettes=json.loads((HERE/'palettes.json').read_text());records=[];row=0
    for palette in palettes:
        for pinned in (False,True):
            for index,rgb in enumerate(palette['rgb']):
                name=f'{row:02d}-{index:02d}-{palette["name"]}-'+('index' if pinned else 'auto')
                mat=bpy.data.materials.new(name);mat.use_nodes=True
                rgba=tuple(linear(c) for c in rgb)+(1,)
                mat.diffuse_color=rgba
                mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=rgba
                if pinned:mat['c643d_color']=index
                x=-7.5+index;y=2.5-row
                mesh=bpy.data.meshes.new(name)
                mesh.from_pydata([(x-.42,y-.36,0),(x+.42,y-.36,0),(x+.42,y+.36,0),(x-.42,y+.36,0)],[],[(0,1,2,3)])
                mesh.update();obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj.data.materials.append(mat)
                mapped=exporter._property_color(obj,mat)
                records.append(dict(object=name,palette=palette['name'],source_rgb=rgb,expected_index=index,
                    source_linear=list(rgba[:3]),pinned=pinned,mapped_index=mapped,mapped_name=c64_color_name(mapped),matches=mapped==index))
            row+=1
    camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(camera)
    camera.location=(0,0,18);camera.data.lens=36;camera.data.sensor_width=36;camera.data.sensor_fit='HORIZONTAL';scene.camera=camera
    # Isolate the two documented exporter changes without guessing v0.7.2 code.
    mat=bpy.data.materials.new('node-vs-viewport-diagnostic');mat.use_nodes=True
    mat.diffuse_color=(0,0,1,1);mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(1,0,0,1)
    diagnostic=dict(diffuse_rgb=[0,0,255],principled_rgb=[255,0,0],mapped_index=exporter._property_color({},mat))
    assert diagnostic['mapped_index']==2
    assert all(r['matches'] for r in records if r['pinned'] or r['palette']=='toolkit')
    scene['calibration_readme']='Six rows: toolkit auto/index, Pepto PAL auto/index, Colodore auto/index; columns VIC-II 0..15.'
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'color-calibration.blend'))
    report=dict(blender_version=bpy.app.version_string,records=records,node_vs_diffuse=diagnostic,
        mapper_sha256=hashlib.sha256((ROOT/'tools/c643d/colors.py').read_bytes()).hexdigest(),
        exporter_sha256=hashlib.sha256((ROOT/'tools/blender_export.py').read_bytes()).hexdigest(),
        native_index_rows_passed=True,reference_palette_rows_passed=True)
    (HERE/'material-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Calibration: 96 materials, toolkit palette and all 48 explicit indices passed')


if __name__=='__main__':main()
