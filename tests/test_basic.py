import tempfile, unittest
from pathlib import Path
from tools.c643d.shapes import (
    torus,cube,sphere,choose_torus_segments_by_vertices,
    choose_sphere_segments_by_vertices,
)
from tools.c643d.objio import load_obj
from tools.c643d.assets import load_object_preset, import_obj_asset
from tools.c643d.mesh import (
    normalize_mesh,fix_winding_outward,transform_mesh,face_center,face_normal,dot,
    mesh_diagnostics,
)
from tools.c643d.pipeline import Camera,fit_scale,build_frames,classify_feature_edges,decode_record_points

ROOT=Path(__file__).resolve().parents[1]

class ToolkitSmokeTests(unittest.TestCase):
    def test_torus_topology(self):
        m=torus(10,5)
        self.assertEqual(len(m.vertices),50)
        self.assertEqual(len(m.faces),50)
        self.assertEqual(len(m.edges),100)

    def test_torus_72_vertex_target(self):
        major,minor=choose_torus_segments_by_vertices(72)
        m=torus(major,minor)
        self.assertEqual((major,minor),(12,6))
        self.assertEqual(len(m.vertices),72)
        self.assertEqual(len(m.faces),72)
        self.assertEqual(len(m.edges),144)

    def test_torus_winding_preserves_concave_inner_wall(self):
        import math
        m=fix_winding_outward(torus(10,5))
        for face in m.faces:
            c=face_center(m,face)
            u=math.atan2(c[2],c[0])
            tube_center=(34.0*math.cos(u),0.0,34.0*math.sin(u))
            expected=(c[0]-tube_center[0],c[1],c[2]-tube_center[2])
            self.assertGreater(dot(face_normal(m,face),expected),0.0)

    def test_cube_topology(self):
        m=cube()
        self.assertEqual((len(m.vertices),len(m.faces),len(m.edges)),(8,6,12))

    def test_sphere_vertex_target_exists(self):
        lat,lon=choose_sphere_segments_by_vertices(64)
        m=sphere(lat,lon)
        self.assertLessEqual(abs(len(m.vertices)-64),8)

    def test_canonical_horse_imports(self):
        m=load_obj(ROOT/'objects'/'horse_head.obj')
        self.assertEqual((len(m.vertices),len(m.faces),len(m.edges)),(64,65,124))
        d=mesh_diagnostics(m)
        self.assertEqual(d['isolated_vertices'],0)

    def test_horse_preset_metadata(self):
        p=load_object_preset(ROOT/'objects','horse_head')
        self.assertEqual(p.up_axis,'z')
        self.assertEqual(p.spin_axis,'y')
        self.assertEqual(p.obj_path.name,'horse_head.obj')

    def test_import_obj_asset_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            objects=Path(td)
            p=import_obj_asset(ROOT/'objects'/'horse_head.obj',objects,slug='pony',up_axis='z')
            self.assertTrue((objects/'pony.obj').exists())
            self.assertTrue((objects/'pony.json').exists())
            q=load_object_preset(objects,'pony')
            self.assertEqual(q.up_axis,'z')
            self.assertEqual(q.obj_path.name,'pony.obj')

    def test_small_cube_pipeline_all_spin_axes(self):
        m=fix_winding_outward(normalize_mesh(cube(),46))
        cam=Camera()
        for axis in ('x','y','z'):
            s=fit_scale(m,8,cam,spin_axis=axis)
            mm=transform_mesh(m,scale=s)
            frames,edges=build_frames(mm,8,cam,spin_axis=axis)
            self.assertEqual(len(frames),8)
            self.assertEqual(edges,12)
            self.assertTrue(all(f.records for f in frames))

if __name__=='__main__':unittest.main()

class TestProjectFeatures(unittest.TestCase):
    def test_example_manifest_includes_horse(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/'examples'/'examples.json').read_text())
        names={x['name'] for x in data}
        self.assertIn('horse_head',names)
        self.assertIn('torus_dense',names)


class TestObjVisibilityAndMaterials(unittest.TestCase):
    def test_horse_preset_uses_full_surface_visibility(self):
        p=load_object_preset(ROOT/'objects','horse_head')
        self.assertEqual(p.visibility,'surface')
        self.assertGreaterEqual(p.z_tolerance,0.001)

    def test_sunflower_asset_and_preset(self):
        m=load_obj(ROOT/'objects'/'sunflower_torus.obj')
        self.assertEqual((len(m.vertices),len(m.faces),len(m.edges)),(76,70,142))
        p=load_object_preset(ROOT/'objects','sunflower_torus')
        self.assertEqual(p.up_axis,'z')
        self.assertEqual(p.visibility,'surface_features')
        self.assertIn('sunflower_torus.mtl',p.materials)
        self.assertTrue((ROOT/'objects'/'sunflower_torus.mtl').exists())

    def test_import_obj_preserves_mtllib(self):
        with tempfile.TemporaryDirectory() as td:
            objects=Path(td)
            p=import_obj_asset(ROOT/'objects'/'sunflower_torus.obj',objects,slug='flower',up_axis='z')
            self.assertTrue((objects/'flower.obj').exists())
            self.assertTrue((objects/'sunflower_torus.mtl').exists())
            text=(objects/'flower.obj').read_text(encoding='utf-8')
            self.assertIn('mtllib sunflower_torus.mtl',text)
            self.assertIn('sunflower_torus.mtl',p.materials)

    def test_example_manifest_includes_sunflower(self):
        import json
        data=json.loads((ROOT/'examples'/'examples.json').read_text())
        names={x['name'] for x in data}
        self.assertIn('sunflower_torus',names)

    def test_horse_owner_aware_visibility_pipeline(self):
        # Smoke/regression check for the muzzle self-occlusion fix. The robust
        # preset should generate all 36 sampled orientations with a healthy
        # number of visible runs and no empty/dropout frame.
        from argparse import Namespace
        from tools.c643d.cli import build_mesh
        a=Namespace(obj=None,object='horse_head',shape='torus',name=None,obj_up='y',
                    polycount=None,vertices=None,major_segments=10,minor_segments=5,
                    lat_segments=6,lon_segments=10,rotate_x=0.0,rotate_y=0.0,rotate_z=0.0,
                    scale=1.0,spin_axis=None,keep_winding=False,visibility='auto',z_tolerance=None)
        m,label,axis,vis,ztol,feature_angle=build_mesh(a)
        cam=Camera(); s=fit_scale(m,36,cam,spin_axis=axis); m=transform_mesh(m,scale=s)
        frames,_=build_frames(m,36,cam,spin_axis=axis,visibility_mode=vis,z_tolerance=ztol,feature_angle=feature_angle)
        self.assertEqual(len(frames),36)
        self.assertGreaterEqual(min(len(f.records) for f in frames),60)


class TestCreaseAwareFeatures(unittest.TestCase):
    def test_horse_sharp_muzzle_edges_are_features(self):
        import math
        from argparse import Namespace
        from tools.c643d.cli import build_mesh
        a=Namespace(obj=None,object='horse_head',shape='torus',name=None,obj_up='y',
                    polycount=None,vertices=None,major_segments=10,minor_segments=5,
                    lat_segments=6,lon_segments=10,rotate_x=0.0,rotate_y=0.0,rotate_z=0.0,
                    scale=1.0,spin_axis=None,keep_winding=False,visibility='auto',z_tolerance=None,feature_angle=None)
        m,label,axis,vis,ztol,fa=build_mesh(a)
        features,stats=classify_feature_edges(m,fa)
        # OBJ 1-based edges (4,10), (5,11), (2,8) are sharp structural
        # muzzle edges that the old surface_features pre-cull could drop.
        for a1,b1 in ((4,10),(5,11),(2,8)):
            e=tuple(sorted((a1-1,b1-1)))
            self.assertTrue(features[e],e)
        self.assertGreater(stats['crease'],0)


class TestSegmentedTablePacking(unittest.TestCase):
    def test_horse_full_surface_fits_36_orientations(self):
        from argparse import Namespace
        from tools.c643d.cli import build_mesh
        from tools.c643d.emit import emit_tables
        a=Namespace(obj=None,object='horse_head',shape='torus',name=None,obj_up='y',
                    polycount=None,vertices=None,major_segments=10,minor_segments=5,
                    lat_segments=6,lon_segments=10,rotate_x=0.0,rotate_y=0.0,rotate_z=0.0,
                    scale=1.0,spin_axis=None,keep_winding=False,visibility='auto',z_tolerance=None,feature_angle=None)
        m,label,axis,vis,ztol,fa=build_mesh(a)
        self.assertEqual(vis,'surface')
        cam=Camera(); scale=fit_scale(m,48,cam,spin_axis=axis); m=transform_mesh(m,scale=scale)
        frames,edges=build_frames(m,36,cam,spin_axis=axis,visibility_mode=vis,z_tolerance=ztol,feature_angle=fa)
        with tempfile.TemporaryDirectory() as td:
            stats=emit_tables(Path(td)/'tables.inc',frames,'yunroll',edges)
        self.assertEqual(stats['frames'],36)
        self.assertGreater(stats['line_overflow_bytes'],0)
        self.assertLessEqual(stats['line_primary_bytes'],0xC800-0x8000)

    def test_surface_mode_contains_pixels_surface_features_preculled(self):
        from argparse import Namespace
        from tools.c643d.cli import build_mesh
        base=dict(obj=None,object='horse_head',shape='torus',name=None,obj_up='y',
                  polycount=None,vertices=None,major_segments=10,minor_segments=5,
                  lat_segments=6,lon_segments=10,rotate_x=0.0,rotate_y=0.0,rotate_z=0.0,
                  scale=1.0,spin_axis=None,keep_winding=False,z_tolerance=None,feature_angle=None)
        a=Namespace(**base,visibility='surface')
        m,label,axis,vis,ztol,fa=build_mesh(a); cam=Camera(); scale=fit_scale(m,36,cam,spin_axis=axis); m=transform_mesh(m,scale=scale)
        surf,_=build_frames(m,36,cam,spin_axis=axis,visibility_mode='surface',z_tolerance=ztol,feature_angle=fa)
        feat,_=build_frames(m,36,cam,spin_axis=axis,visibility_mode='surface_features',z_tolerance=ztol,feature_angle=40.0)
        # The old mode really did drop visible horse pixels; this regression
        # test makes that design difference explicit instead of hiding it.
        found=False
        for sf,ff in zip(surf,feat):
            sp=set(); fp=set()
            for r in sf.records: sp.update(decode_record_points(r))
            for r in ff.records: fp.update(decode_record_points(r))
            if sp-fp:
                found=True; break
        self.assertTrue(found)


class TestVisibilityRegressionSemantics(unittest.TestCase):
    def _sunflower_frames(self, visibility, count=24):
        from argparse import Namespace
        from tools.c643d.cli import build_mesh
        a=Namespace(obj=None,object='sunflower_torus',shape='torus',name=None,obj_up='y',
                    polycount=None,vertices=None,major_segments=10,minor_segments=5,
                    lat_segments=6,lon_segments=10,rotate_x=0.0,rotate_y=0.0,rotate_z=0.0,
                    scale=1.0,spin_axis=None,keep_winding=False,visibility=visibility,
                    z_tolerance=None,feature_angle=None)
        m,label,axis,vis,ztol,fa=build_mesh(a)
        cam=Camera(); scale=fit_scale(m,48,cam,spin_axis=axis); m=transform_mesh(m,scale=scale)
        frames,_=build_frames(m,count,cam,spin_axis=axis,visibility_mode=vis,z_tolerance=ztol,feature_angle=fa)
        return frames

    def test_sunflower_surface_features_matches_v031_workload(self):
        frames=self._sunflower_frames('surface_features',24)
        counts=[len(f.records) for f in frames]
        self.assertEqual((min(counts),max(counts),sum(counts)),(87,109,2447))
        self.assertEqual(sum(f.raw_pixels for f in frames),29785)

    def test_surface_creases_keeps_v032_behavior_separate(self):
        cheap=self._sunflower_frames('surface_features',24)
        creases=self._sunflower_frames('surface_creases',24)
        self.assertGreater(sum(len(f.records) for f in creases),sum(len(f.records) for f in cheap))
        self.assertGreater(sum(f.raw_pixels for f in creases),sum(f.raw_pixels for f in cheap))


class TestGeneratedMemoryMap(unittest.TestCase):
    def test_renderer_hud_cannot_overlap_frame_pointer_arena(self):
        from tools.asm_sanity import scan, HUD_MAX_BYTES
        from tools.c643d.emit import PTR_BASE, PTR_LIMIT
        for name in ('renderer-step.asm','renderer-bytechunk.asm','renderer-yunroll.asm'):
            _,end=scan(ROOT/'c64'/name)
            self.assertLessEqual(end+HUD_MAX_BYTES,PTR_BASE,name)
        self.assertLessEqual(PTR_BASE+48*4,PTR_LIMIT)
