"""Blender-side regression: native MDD and Alembic evaluated geometry export.

blender --background --factory-startup --python-exit-code 1 \
  --python tools/verify_blender_vertex_caches.py -- --output-dir build/cache-check
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import struct
import sys
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import blender_export as exporter
from tools.c643d.colors import nearest_c64_color_index


def export_scene(out, name):
    target = out/(name+'.c643dscene')
    old = sys.argv
    try:
        sys.argv = ['blender', '--', '--output', str(target), '--frame-start','1',
                    '--frame-end','4','--viewport-height','192']
        exporter.main()
    finally:
        sys.argv = old
    data = json.loads(target.read_text())
    assert len(data['frames']) == 4
    assert len({json.dumps(f['vertices']) for f in data['frames']}) == 4
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    out = a.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = 1; scene.frame_end = 4; scene.render.fps = 25
    camera_data = bpy.data.cameras.new('Camera')
    camera = bpy.data.objects.new('Camera',camera_data)
    scene.collection.objects.link(camera); camera.location = (0,0,8); scene.camera = camera
    vertices = [(-1,-1,0),(1,-1,0),(0,1,0),(0,0,1)]
    mesh = bpy.data.meshes.new('CacheMesh')
    mesh.from_pydata(vertices, [], [(0,1,2),(0,3,1),(1,3,2),(2,3,0)])
    obj = bpy.data.objects.new('CACHE TEST',mesh); scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj; obj.select_set(True)
    cache = out/'deformation.mdd'
    blob = bytearray(struct.pack('>ii',4,len(vertices)))
    blob.extend(struct.pack('>4f',0.,.04,.08,.12))
    for frame in range(4):
        for i,(x,y,z) in enumerate(vertices):
            blob.extend(struct.pack('>3f',x+frame*.2*(i+1),y+frame*.1,z))
    cache.write_bytes(blob)
    mod = obj.modifiers.new('Native MDD','MESH_CACHE')
    mod.cache_format = 'MDD'; mod.filepath = str(cache); mod.frame_start = 1
    mat = bpy.data.materials.new('Linear swatch')
    mat.diffuse_color = (.18,.18,.18,1.)
    mesh.materials.append(mat)
    assert exporter._property_color(obj,mat) == nearest_c64_color_index((118,118,118))
    mat.use_nodes = True
    mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (0.,1.,0.,1.)
    assert exporter._property_color(obj,mat) == nearest_c64_color_index((0,255,0))
    mat['c643d_color'] = 'purple'; assert exporter._property_color(obj,mat) == 4
    del mat['c643d_color']
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'mdd.blend'))
    mdd = export_scene(out,'mdd')
    saved = mod.filepath; mod.filepath = str(out/'missing.mdd')
    try:
        exporter._validate_mesh_caches([obj])
    except RuntimeError as exc:
        assert 'external vertex cache is missing' in str(exc)
    else: raise AssertionError('Missing MDD path was not rejected')
    mod.filepath = saved
    mod.show_viewport = False
    log = io.StringIO()
    with contextlib.redirect_stdout(log): exporter._validate_mesh_caches([obj])
    assert 'disabled in the viewport' in log.getvalue()
    mod.show_viewport = True
    report = dict(passed=True,blender=bpy.app.version_string,mdd_evaluated=True,
        alembic_evaluated=False,samples_each=4,all_samples_deform=True,
        missing_cache_rejected=True,disabled_cache_warning=True,
        scene_linear_and_principled_mapping=True,explicit_override=True,
        caveat='Synthetic stable-topology caches; the reported LightWave project was not supplied')
    if not bpy.app.build_options.alembic:
        report['alembic_skipped'] = 'This Blender binary was compiled without Alembic support'
        (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
        return
    abc = out/'deformation.abc'
    bpy.ops.wm.alembic_export(filepath=str(abc),start=1,end=4,selected=True,as_background_job=False)
    bpy.data.objects.remove(obj,do_unlink=True)
    bpy.ops.wm.alembic_import(filepath=str(abc),as_background_job=False,set_frame_range=False)
    assert any(m.type=='MESH_SEQUENCE_CACHE' for o in scene.objects for m in o.modifiers)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'alembic.blend'))
    alembic = export_scene(out,'alembic')
    assert len(mdd['frames'][0]['vertices']) == len(alembic['frames'][0]['vertices'])
    report['alembic_evaluated'] = True
    (out/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
