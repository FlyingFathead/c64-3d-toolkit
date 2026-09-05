import tempfile, unittest
from pathlib import Path
from tools.c643d.shapes import (
    torus,cube,sphere,choose_torus_segments_by_vertices,
    choose_sphere_segments_by_vertices,
)
from tools.c643d.objio import load_obj, load_mtl
from tools.c643d.assets import load_object_preset, import_obj_asset, import_svg_asset
from tools.c643d.mesh import (
    normalize_mesh,fix_winding_outward,transform_mesh,face_center,face_normal,dot,
    mesh_diagnostics,
)
from tools.c643d.pipeline import Camera,fit_scale,build_frames,classify_feature_edges,decode_record_points
from tools.c643d.svgio import load_svg
from tools.c643d.colors import c64_color_name

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
            self.assertTrue(q.use_colors)

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

    def test_default_colored_output_name_gets_color_suffix(self):
        from tools.c643d.cli import default_output_basename
        self.assertEqual(default_output_basename('SUNFLOWER TORUS','yunroll',True),'sunflower_torus_color-yunroll')
        self.assertEqual(default_output_basename('SUNFLOWER TORUS','yunroll',False),'sunflower_torus-yunroll')

    def test_build_notice_announces_missing_obj_color_layer(self):
        from tools.c643d.cli import color_build_notice
        mesh=load_obj(ROOT/'objects'/'horse_head.obj')
        notice=color_build_notice(mesh,ROOT/'objects'/'horse_head.obj','white',False,False)
        self.assertEqual(
            notice,
            'color: no usable MTL color layer found for horse_head.obj; using white monochrome default pipeline',
        )


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

    def test_sunflower_mtl_maps_all_materials_to_native_c64_codes(self):
        colors=load_mtl(ROOT/'objects'/'sunflower_torus.mtl')
        self.assertEqual(
            {name:c64_color_name(index) for name,index in colors.items()},
            {'center':'brown','petals':'yellow','stem':'green','leaves':'green'},
        )
        mesh=load_obj(ROOT/'objects'/'sunflower_torus.obj')
        self.assertEqual([c64_color_name(c) for c in mesh.face_colors[:48]],['brown']*48)
        self.assertEqual([c64_color_name(c) for c in mesh.face_colors[48:60]],['yellow']*12)
        self.assertEqual([c64_color_name(c) for c in mesh.face_colors[60:]],['green']*10)

    def test_obj_without_material_colors_keeps_monochrome_path(self):
        from tools.c643d.cli import build_mesh, make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        mesh=load_obj(ROOT/'objects'/'horse_head.obj')
        self.assertFalse(mesh.has_source_colors)
        with tempfile.TemporaryDirectory() as td:
            parser=make_parser(load_toolchain_settings(Path(td)/'missing.ini'))
        built=build_mesh(parser.parse_args(['inspect','--object','horse_head']))
        self.assertEqual(built[6],'white')
        self.assertFalse(built[7])
        self.assertFalse(built[8])

    def test_ignoring_material_colors_is_geometry_table_neutral(self):
        from tools.c643d.emit import emit_tables
        mesh=fix_winding_outward(normalize_mesh(load_obj(ROOT/'objects'/'sunflower_torus.obj'),46.0))
        plain=mesh.copy(); plain.face_colors=[]
        cam=Camera(); scale=fit_scale(mesh,8,cam); mesh=transform_mesh(mesh,scale=scale); plain=transform_mesh(plain,scale=scale)
        with_colors,edges=build_frames(mesh,8,cam,visibility_mode='surface_features',enable_source_colors=False)
        without_colors,_=build_frames(plain,8,cam,visibility_mode='surface_features')
        self.assertEqual(with_colors,without_colors)
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'a.inc'; b=Path(td)/'b.inc'
            sa=emit_tables(a,with_colors,'yunroll',edges)
            sb=emit_tables(b,without_colors,'yunroll',edges)
            self.assertEqual(a.read_bytes(),b.read_bytes())
        self.assertFalse(sa['colors_enabled']); self.assertEqual(sa,sb)

    def test_sunflower_build_generates_per_cell_color_spans(self):
        from tools.c643d.emit import emit_tables
        mesh=fix_winding_outward(normalize_mesh(load_obj(ROOT/'objects'/'sunflower_torus.obj'),46.0))
        cam=Camera(); scale=fit_scale(mesh,8,cam); mesh=transform_mesh(mesh,scale=scale)
        frames,edges=build_frames(mesh,8,cam,visibility_mode='surface_features',enable_source_colors=True)
        self.assertTrue(all(frame.color_spans for frame in frames))
        palette={color for frame in frames for color in frame.color_palette}
        self.assertEqual({c64_color_name(color) for color in palette},{'brown','yellow','green'})
        with tempfile.TemporaryDirectory() as td:
            stats=emit_tables(Path(td)/'color.inc',frames,'yunroll',edges)
        self.assertTrue(stats['colors_enabled'])
        self.assertGreater(stats['color_table_bytes'],0)

    def test_import_obj_preserves_mtllib(self):
        with tempfile.TemporaryDirectory() as td:
            objects=Path(td)
            p=import_obj_asset(ROOT/'objects'/'sunflower_torus.obj',objects,slug='flower',up_axis='z')
            self.assertTrue((objects/'flower.obj').exists())
            self.assertTrue((objects/'sunflower_torus.mtl').exists())
            text=(objects/'flower.obj').read_text(encoding='utf-8')
            self.assertIn('mtllib sunflower_torus.mtl',text)
            self.assertIn('sunflower_torus.mtl',p.materials)

    def test_import_obj_can_persist_source_color_opt_out(self):
        with tempfile.TemporaryDirectory() as td:
            p=import_obj_asset(ROOT/'objects'/'sunflower_torus.obj',Path(td),slug='plain_flower',use_colors=False)
        self.assertFalse(p.use_colors)

    def test_example_manifest_includes_sunflower(self):
        import json
        data=json.loads((ROOT/'examples'/'examples.json').read_text())
        names={x['name'] for x in data}
        self.assertIn('sunflower_torus',names)
        self.assertIn('sunflower_torus_color',names)

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
        m,label,axis,vis,ztol,feature_angle,*_=build_mesh(a)
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
        m,label,axis,vis,ztol,fa,*_=build_mesh(a)
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
        m,label,axis,vis,ztol,fa,*_=build_mesh(a)
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
        m,label,axis,vis,ztol,fa,*_=build_mesh(a); cam=Camera(); scale=fit_scale(m,36,cam,spin_axis=axis); m=transform_mesh(m,scale=scale)
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
        m,label,axis,vis,ztol,fa,*_=build_mesh(a)
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
            labels={}
            _,end=scan(ROOT/'c64'/name,labels=labels)
            code_end=labels.get('renderer_hud_start',end)
            self.assertLessEqual(code_end+HUD_MAX_BYTES,PTR_BASE,name)
        self.assertLessEqual(PTR_BASE+48*4,PTR_LIMIT)


class TestSvgPipeline(unittest.TestCase):
    def test_space_horse_svg_imports_and_maps_yellow(self):
        info=load_svg(ROOT/'objects'/'space_horse.svg','SPACE HORSE',tolerance=20.0,curve_step=12.0,depth=0.0)
        self.assertEqual(info.c64_color,'yellow')
        self.assertEqual(info.contours,14)
        self.assertGreaterEqual(len(info.mesh.edges),100)
        self.assertEqual(len(info.mesh.faces),0)
        self.assertEqual(mesh_diagnostics(info.mesh)['isolated_vertices'],0)

    def test_space_horse_presets(self):
        spin=load_object_preset(ROOT/'objects','space_horse')
        crawl=load_object_preset(ROOT/'objects','space_horse_crawl')
        self.assertEqual(spin.obj_path.name,'space_horse.svg')
        self.assertEqual(spin.color,'yellow')
        self.assertEqual(spin.animation,'spin')
        self.assertEqual(crawl.animation,'crawl')
        self.assertEqual(crawl.color,'yellow')

    def test_single_source_color_uses_zero_overhead_global_hires_path(self):
        from tools.c643d.cli import build_mesh, make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        with tempfile.TemporaryDirectory() as td:
            parser=make_parser(load_toolchain_settings(Path(td)/'missing.ini'))
        colored=build_mesh(parser.parse_args(['inspect','--object','space_horse']))
        plain=build_mesh(parser.parse_args(['inspect','--object','space_horse','--no-colors']))
        self.assertEqual(colored[6],'yellow')
        self.assertTrue(colored[7])
        self.assertFalse(colored[8])
        self.assertEqual(plain[6],'white')
        self.assertFalse(plain[7])
        self.assertFalse(plain[8])

    def test_import_svg_asset_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            objects=Path(td)
            p=import_svg_asset(ROOT/'objects'/'space_horse.svg',objects,slug='logo',svg_tolerance=20.0,svg_depth=0.0)
            self.assertTrue((objects/'logo.svg').exists())
            self.assertTrue((objects/'logo.json').exists())
            self.assertEqual(p.color,'yellow')
            self.assertEqual(p.obj_path.name,'logo.svg')
            self.assertTrue(p.use_colors)

    def test_import_svg_can_persist_source_color_opt_out(self):
        with tempfile.TemporaryDirectory() as td:
            p=import_svg_asset(ROOT/'objects'/'space_horse.svg',Path(td),slug='plain_logo',svg_tolerance=20.0,svg_depth=0.0,use_colors=False)
        self.assertFalse(p.use_colors)

    def test_svg_keeps_distinct_source_colors_on_contour_edges(self):
        with tempfile.TemporaryDirectory() as td:
            svg=Path(td)/'two-colors.svg'
            svg.write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<path d="M 5 20 L 95 20" fill="none" stroke="#ff0000"/>
<path d="M 5 80 L 95 80" fill="none" stroke="#0000ff"/>
</svg>''')
            info=load_svg(svg,tolerance=0.0,depth=0.0)
        self.assertEqual({c64_color_name(color) for color in info.mesh.line_colors},{'red','blue'})
        self.assertEqual(set(info.c64_colors),{'red','blue'})

    def test_svg_without_explicit_colors_keeps_monochrome_path(self):
        with tempfile.TemporaryDirectory() as td:
            svg=Path(td)/'plain.svg'
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L20 0 L20 20 Z"/></svg>')
            info=load_svg(svg,tolerance=0.0,depth=0.0)
        self.assertFalse(info.mesh.has_source_colors)
        self.assertEqual(info.c64_color,'white')

    def test_crawl_animation_builds_frames(self):
        info=load_svg(ROOT/'objects'/'space_horse.svg','SPACE HORSE',tolerance=40.0,curve_step=14.0,depth=0.0)
        m=normalize_mesh(info.mesh,46.0); cam=Camera()
        scale=fit_scale(m,8,cam,animation='crawl',animation_tilt=62.0,animation_travel=105.0,animation_rise=42.0)
        m=transform_mesh(m,scale=scale)
        frames,edges=build_frames(m,8,cam,animation='crawl',animation_tilt=62.0,animation_travel=105.0,animation_rise=42.0)
        self.assertEqual(len(frames),8)
        self.assertEqual(edges,len(m.edges))
        self.assertTrue(all(f.records for f in frames))

    def test_example_manifest_includes_svg_demos(self):
        import json
        names={x['name'] for x in json.loads((ROOT/'examples'/'examples.json').read_text())}
        self.assertIn('space_horse_spin_color',names)
        self.assertIn('space_horse_crawl_color',names)

    def test_renderer_colour_is_patched_for_svg_demo(self):
        from tools.c643d.cli import prepare_asm
        asm=prepare_asm('yunroll',8,7,True).read_text()
        self.assertIn('SCREEN_COLOR = $70',asm)
        self.assertIn('COLORS_ENABLED = 1',asm)

    def test_colored_renderers_restore_recycled_screen_cells(self):
        from tools.c643d.cli import prepare_asm
        for renderer in ('step','bytechunk','yunroll'):
            asm=prepare_asm(renderer,8,1,True).read_text()
            self.assertIn('jsr reset_old_frame_colors',asm,renderer)
            self.assertIn('* = $4000\nreset_old_frame_colors:',asm,renderer)
            self.assertIn('lda #SCREEN_COLOR\nrofc_store:',asm,renderer)

class TestToolchainConfig(unittest.TestCase):
    def test_builtin_defaults_keep_vice_windowed(self):
        from tools.c643d.toolchain import load_toolchain_settings
        with tempfile.TemporaryDirectory() as td:
            cfg=load_toolchain_settings(Path(td)/'missing.ini',system='Linux')
        self.assertEqual(cfg.tass,'64tass')
        self.assertEqual(cfg.vice,'x64sc')
        self.assertEqual(cfg.blender,'blender')
        self.assertEqual(cfg.vice_args,('+VICIIfull',))
        self.assertIsNone(cfg.config_path)

    def test_platform_section_overrides_generic_toolchain(self):
        from tools.c643d.toolchain import load_toolchain_settings
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'c643d.ini'
            path.write_text('''[toolchain]\ntass = generic-tass\nvice = generic-vice\nvice_args = +VICIIfull\n\n[macos]\ntass = /opt/homebrew/bin/64tass\nvice = /Applications/VICE.app\nvice_args = +VICIIfull -confirmexit\n''')
            cfg=load_toolchain_settings(path,system='Darwin',require=True)
        self.assertEqual(cfg.tass,'/opt/homebrew/bin/64tass')
        self.assertEqual(cfg.vice,'/Applications/VICE.app')
        self.assertEqual(cfg.vice_args,('+VICIIfull','-confirmexit'))
        self.assertEqual(cfg.platform_key,'macos')

    def test_explicit_executable_path_resolves(self):
        import os
        from tools.c643d.toolchain import resolve_executable
        with tempfile.TemporaryDirectory() as td:
            exe=Path(td)/'my-x64sc'
            exe.write_text('#!/bin/sh\nexit 0\n')
            exe.chmod(0o755)
            self.assertEqual(Path(resolve_executable(str(exe),'vice')),exe.resolve())

    def test_macos_x64sc_app_prefers_real_sibling_cli_binary(self):
        from tools.c643d.toolchain import resolve_executable
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            wrapper=root/'x64sc.app'/'Contents'/'MacOS'/'x64sc'
            real=root/'VICE.app'/'Contents'/'Resources'/'bin'/'x64sc'
            wrapper.parent.mkdir(parents=True); real.parent.mkdir(parents=True)
            wrapper.write_text('#!/bin/sh\nexit 0\n'); wrapper.chmod(0o755)
            real.write_text('#!/bin/sh\nexit 0\n'); real.chmod(0o755)
            self.assertEqual(Path(resolve_executable(str(root/'x64sc.app'),'vice')),real.resolve())

    def test_macos_downloaded_distribution_prefers_bin_x64sc(self):
        from tools.c643d.toolchain import resolve_executable
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'vice-arm64-gtk3-3.8'
            cli=root/'bin'/'x64sc'
            launcher=root/'tools'/'x64sc'
            cli.parent.mkdir(parents=True); launcher.parent.mkdir(parents=True)
            cli.write_text('#!/bin/sh\nexit 0\n'); cli.chmod(0o755)
            launcher.write_text('#!/bin/sh\nexit 0\n'); launcher.chmod(0o755)
            self.assertEqual(Path(resolve_executable(str(root),'vice')),cli.resolve())

    def test_macos_distribution_directory_finds_tools_launcher(self):
        from tools.c643d.toolchain import resolve_executable
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'vice-arm64-gtk3-3.10'
            launcher=root/'tools'/'x64sc'
            launcher.parent.mkdir(parents=True)
            launcher.write_text('#!/bin/sh\nexit 0\n')
            launcher.chmod(0o755)
            self.assertEqual(Path(resolve_executable(str(root),'vice')),launcher.resolve())

    def test_tool_command_places_default_args_before_prg(self):
        from tools.c643d.toolchain import command
        self.assertEqual(command('/usr/bin/x64sc',['+VICIIfull'],['demo.prg']),
                         ['/usr/bin/x64sc','+VICIIfull','demo.prg'])

    def test_blender_path_is_configurable_per_platform(self):
        from tools.c643d.toolchain import load_toolchain_settings
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'c643d.ini'
            path.write_text('[toolchain]\nblender = generic-blender\n\n[linux]\nblender = /opt/blender/blender\n')
            cfg=load_toolchain_settings(path,system='Linux',require=True)
        self.assertEqual(cfg.blender,'/opt/blender/blender')

    def test_preflight_version_probe_reads_first_output_line(self):
        from tools.c643d.cli import _executable_version
        with tempfile.TemporaryDirectory() as td:
            fake=Path(td)/'tool'
            fake.write_text('#!/bin/sh\nprintf "Example Tool 1.2.3\\nmore detail\\n"\n')
            fake.chmod(0o755)
            self.assertEqual(_executable_version(str(fake)),'Example Tool 1.2.3')


class TestBlenderScenePipeline(unittest.TestCase):
    def _scene_file(self,root:Path):
        import json
        base=normalize_mesh(cube(),18.0)
        frames=[]
        for source_frame,dx in ((1,-4.0),(4,5.0)):
            frames.append({
                'source_frame':source_frame,
                'projection':{'fx':180.0,'fy':176.0,'cx':128.0,'cy':72.0},
                'vertices':[[x+dx,y,z+110.0] for x,y,z in base.vertices],
            })
        path=root/'moving_cube.c643dscene'
        path.write_text(json.dumps({
            'format':'c643dscene','version':1,'name':'MOVING CUBE',
            'source':{'kind':'blender','fps':24.0,'sample_step':3},
            'topology':{
                'faces':[list(f) for f in base.faces],'line_edges':[],
                'face_colors':[7]*len(base.faces),'line_colors':[],
            },
            'frames':frames,
        }))
        return path

    def test_scene_loader_and_renderer_accept_authored_frames(self):
        from tools.c643d.sceneio import load_scene
        from tools.c643d.pipeline import build_scene_frames
        with tempfile.TemporaryDirectory() as td:
            scene=load_scene(self._scene_file(Path(td)))
        self.assertEqual(scene.name,'MOVING CUBE')
        self.assertEqual([f.source_frame for f in scene.frames],[1,4])
        self.assertEqual(scene.sample_step,3)
        built,edges=build_scene_frames(scene,enable_source_colors=False)
        self.assertEqual(len(built),2)
        self.assertEqual(edges,12)
        self.assertTrue(all(frame.records for frame in built))

    def test_blender_sampling_evaluates_intervening_physics_frames(self):
        from tools.c643d.blender import blender_frame_plan
        evaluation,captures=blender_frame_plan(
            1,72,3,scene_start=1,simulation_start=1,
        )
        self.assertEqual(list(evaluation),list(range(1,73)))
        self.assertEqual(captures[:4],(1,4,7,10))
        self.assertEqual(captures[-1],70)
        self.assertEqual(len(captures),24)

    def test_blender_exporter_warns_if_sampled_scene_is_static(self):
        text=(ROOT/'tools'/'blender_export.py').read_text(encoding='utf-8')
        self.assertIn('for evaluation_frame in evaluation_frames:',text)
        self.assertIn('if evaluation_frame not in capture_frames:',text)
        self.assertIn('all sampled frames are geometrically identical',text)
        self.assertNotIn('for source_frame in source_frames:',text)

    def test_scene_renderer_clips_authored_edges_to_viewport(self):
        import json
        from tools.c643d.sceneio import load_scene
        from tools.c643d.pipeline import build_scene_frames, decode_record_points
        with tempfile.TemporaryDirectory() as td:
            path=self._scene_file(Path(td))
            data=json.loads(path.read_text())
            for frame in data['frames']:
                for vertex in frame['vertices']:
                    vertex[1]+=45.0
            path.write_text(json.dumps(data))
            scene=load_scene(path)
            built,_=build_scene_frames(scene,enable_source_colors=False)
        points=[point for record in built[0].records for point in decode_record_points(record)]
        self.assertTrue(points)
        self.assertTrue(all(0<=x<256 and 0<=y<144 for x,y in points))

    def test_viewport_clipper_handles_reported_falling_cube_edge(self):
        from tools.c643d.pipeline import clip_line_to_viewport
        clipped=clip_line_to_viewport(95.0,12.0,94.0,-11.0)
        self.assertIsNotNone(clipped)
        self.assertAlmostEqual(clipped[3],0.0)
        self.assertTrue(all((0<=x<256 and 0<=y<144)
                            for x,y in ((clipped[0],clipped[1]),(clipped[2],clipped[3]))))

    def test_legacy_renderer_retains_outside_viewport_guard(self):
        from tools.c643d.mesh import Mesh
        mesh=normalize_mesh(cube(),18.0)
        shifted=Mesh(
            mesh.name,[(x,y+60.0,z) for x,y,z in mesh.vertices],
            list(mesh.faces),list(mesh.line_edges),
            list(mesh.face_colors),list(mesh.line_colors),
        )
        with self.assertRaisesRegex(RuntimeError,'projected edge outside viewport'):
            build_frames(shifted,1,Camera(distance=110.0,focal=180.0))

    def test_scene_loader_rejects_topology_changes(self):
        import json
        from tools.c643d.sceneio import load_scene
        with tempfile.TemporaryDirectory() as td:
            path=self._scene_file(Path(td))
            data=json.loads(path.read_text())
            data['frames'][1]['vertices'].pop()
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'topology changed'):
                load_scene(path)

    def test_missing_blender_gives_ubuntu_install_command(self):
        from tools.c643d.blender import require_blender
        with self.assertRaisesRegex(RuntimeError,'sudo apt install blender'):
            require_blender('definitely-not-a-real-blender-command',system='Linux')

    def test_bpy_probe_reports_blender_version(self):
        from tools.c643d.blender import probe_blender
        with tempfile.TemporaryDirectory() as td:
            fake=Path(td)/'blender'
            fake.write_text(
                '#!/bin/sh\n'
                'case "$*" in *hasattr*|*bpy.types*) exit 9;; esac\n'
                'printf "C6433D ignored\\nC643D_BPY_OK:4.0.2\\n"\n'
            )
            fake.chmod(0o755)
            self.assertEqual(probe_blender(str(fake)),'4.0.2')

    def test_bpy_probe_does_not_introspect_blender_rna_types(self):
        text=(ROOT/'tools'/'c643d'/'blender.py').read_text(encoding='utf-8')
        self.assertIn('import bpy; print',text)
        self.assertNotIn('hasattr(',text)
        self.assertNotIn('bpy.types.',text)
        self.assertIn("'--python-exit-code','1'",text)
        self.assertIn("'--disable-autoexec'",text)

    def test_bpy_probe_disables_autoexec(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from tools.c643d.blender import probe_blender

        def fake_run(command,**kwargs):
            self.assertIn('--disable-autoexec',command)
            self.assertLess(command.index('--disable-autoexec'),command.index('--python-expr'))
            return SimpleNamespace(returncode=0,stdout='C643D_BPY_OK:4.0.2\n',stderr='')

        with patch('tools.c643d.blender.subprocess.run',side_effect=fake_run):
            self.assertEqual(probe_blender('/fake/blender'),'4.0.2')

    def test_bpy_probe_preserves_useful_failure_tail(self):
        from tools.c643d.blender import probe_blender
        with tempfile.TemporaryDirectory() as td:
            fake=Path(td)/'blender'
            fake.write_text(
                '#!/bin/sh\n'
                'printf "Traceback (most recent call last):\\n" >&2\n'
                'printf "ImportError: bpy failed to import\\n" >&2\n'
                'printf "Error: script failed, exiting.\\n" >&2\n'
                'exit 1\n'
            )
            fake.chmod(0o755)
            with self.assertRaisesRegex(RuntimeError,'ImportError: bpy failed to import'):
                probe_blender(str(fake))

    def test_blender_export_uses_camera_object_api(self):
        text=(ROOT/'tools'/'blender_export.py').read_text(encoding='utf-8')
        self.assertIn('evaluated_camera.calc_matrix_camera(',text)
        self.assertNotIn('evaluated_camera.data.calc_matrix_camera(',text)

    def test_blender_export_turns_python_tracebacks_into_failure(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from tools.c643d.blender import export_blend_scene
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/'scene.blend'
            output=root/'scene.c643dscene'
            source.write_bytes(b'BLENDER')
            (root/'tools').mkdir()
            (root/'tools'/'blender_export.py').write_text('# test exporter\n')

            def fake_run(command,**kwargs):
                output.write_text('{}')
                self.assertIn('--disable-autoexec',command)
                self.assertLess(command.index('--disable-autoexec'),command.index(str(source.resolve())))
                self.assertLess(command.index('--python-exit-code'),command.index('--python'))
                self.assertEqual(command[command.index('--python-exit-code')+1],'1')
                return SimpleNamespace(returncode=0)

            with patch('tools.c643d.blender.subprocess.run',side_effect=fake_run):
                self.assertEqual(
                    export_blend_scene(
                        source,output,blender='/fake/blender',root=root,
                        blender_is_verified=True,
                    ),
                    output.resolve(),
                )

    def test_falling_cubes_examples_are_packaged_under_examples(self):
        directory=ROOT/'examples'/'blender_falling_cubes'
        self.assertTrue((directory/'falling_cubes_c64.py').is_file())
        self.assertTrue((directory/'falling_cubes_full.py').is_file())
        blend=directory/'falling_cubes_full.blend'
        self.assertTrue(blend.is_file())
        self.assertEqual(blend.read_bytes()[:7],b'BLENDER')

    def test_windows_setup_offers_exact_optional_blender_package(self):
        text=(ROOT/'setup-windows.ps1').read_text(encoding='utf-8')
        self.assertIn("WingetId = 'BlenderFoundation.Blender'",text)
        self.assertIn('Request-BlenderInstall',text)
        self.assertIn('64tass is REQUIRED to assemble a runnable .prg',text)

class TestRc062RenderAndChecksumControls(unittest.TestCase):
    def test_render_defaults_config(self):
        from tools.c643d.toolchain import load_toolchain_settings
        with tempfile.TemporaryDirectory() as td:
            cfg=Path(td)/'c643d.ini'
            cfg.write_text(
                '[render_defaults]\n'
                'text_overlay = false\n'
                'viewport_height = auto\n'
                'overwrite_policy = error\n'
                'rastertime_profiler = false\n',
                encoding='utf-8',
            )
            settings=load_toolchain_settings(cfg)
        self.assertFalse(settings.text_overlay)
        self.assertIsNone(settings.viewport_height)
        self.assertEqual(settings.overwrite_policy,'error')
        self.assertFalse(settings.rastertime_profiler)

    def test_auto_viewport_height_reserves_only_hud_row(self):
        from argparse import Namespace
        from tools.c643d.cli import _viewport_height
        self.assertEqual(_viewport_height(Namespace(viewport_height=None,text_overlay=True)),192)
        self.assertEqual(_viewport_height(Namespace(viewport_height=None,text_overlay=False)),200)
        self.assertEqual(_viewport_height(Namespace(viewport_height=144,text_overlay=False)),144)

    def test_variant_output_suffixes(self):
        from tools.c643d.cli import default_output_basename
        self.assertEqual(
            default_output_basename('CUBE','yunroll',False,text_overlay=False),
            'cube-yunroll_no_overlay',
        )
        self.assertEqual(
            default_output_basename('CUBE','yunroll',False,rastertime_profiler=True),
            'cube-yunroll_rastertime_profiler',
        )

    def test_variant_sources_are_separate_from_production(self):
        from tools.c643d.cli import C64, NO_OVERLAY_RENDERERS, RASTERTIME_RENDERERS, RENDERERS
        production=(C64/RENDERERS['yunroll']).read_text(encoding='utf-8')
        no_overlay=(C64/NO_OVERLAY_RENDERERS['yunroll']).read_text(encoding='utf-8')
        profiler=(C64/RASTERTIME_RENDERERS['yunroll']).read_text(encoding='utf-8')
        self.assertNotIn('RASTERTIME PROFILER DEBUG VARIANT',production)
        self.assertNotIn('NO TEXT OVERLAY VARIANT',production)
        self.assertIn('NO TEXT OVERLAY VARIANT',no_overlay)
        self.assertIn('RASTERTIME PROFILER DEBUG VARIANT',profiler)

    def test_checksum_comparison_states(self):
        import hashlib
        from tools.c643d.checksums import compare_prg
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'demo.prg'; p.write_bytes(b'abc')
            sha=hashlib.sha256(b'abc').hexdigest()
            good={'files':{'demo.prg':{'sha256':sha,'size':3}}}
            changed={'files':{'demo.prg':{'sha256':'0'*64,'size':3}}}
            self.assertEqual(compare_prg(p,good)['status'],'MATCHING')
            self.assertEqual(compare_prg(p,changed)['status'],'CHANGED')
            self.assertEqual(compare_prg(p,{'files':{}})['status'],'ABSENT')

    def test_generate_examples_defaults_to_all_variants(self):
        from tools.c643d.cli import make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        parser=make_parser(load_toolchain_settings(Path('/definitely/missing/c643d.ini')))
        args=parser.parse_args(['generate-examples'])
        self.assertEqual(args.variants,'all')

    def test_legacy144_variant_parses(self):
        from tools.c643d.cli import make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        parser=make_parser(load_toolchain_settings(Path('/definitely/missing/c643d.ini')))
        args=parser.parse_args(['test-examples','--variants','legacy144'])
        self.assertEqual(args.variants,'legacy144')

    def test_example_manifest_records_per_example_directories(self):
        import json
        specs=json.loads((ROOT/'examples'/'examples.json').read_text(encoding='utf-8'))
        self.assertTrue(all(spec.get('directory') for spec in specs))
        self.assertEqual({x['name']:x['directory'] for x in specs}['sunflower_torus_color'],'sunflower_torus')

    def test_blender_only_selector_parses(self):
        from tools.c643d.cli import make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        parser=make_parser(load_toolchain_settings(Path('/definitely/missing/c643d.ini')))
        args=parser.parse_args(['test-examples','--blender-only'])
        self.assertTrue(args.blender_only)

    def test_blender_example_manifest_has_color_and_monochrome_falling_cubes(self):
        import json
        manifest=ROOT/'examples'/'blender_falling_cubes'/'examples.json'
        specs=json.loads(manifest.read_text(encoding='utf-8'))
        self.assertEqual(
            [spec['name'] for spec in specs],
            ['falling_cubes_c64_color-yunroll','falling_cubes_c64-yunroll'],
        )
        color,mono=specs
        for spec in (color,mono):
            self.assertIn('--blend',spec['args'])
            self.assertIn('examples/blender_falling_cubes/falling_cubes_c64.blend',spec['args'])
            self.assertEqual(spec['args'][spec['args'].index('--sample-step')+1],'4')
            self.assertEqual(spec['args'][spec['args'].index('--renderer')+1],'yunroll')
        self.assertNotIn('--no-colors',color['args'])
        self.assertIn('--no-colors',mono['args'])
        self.assertEqual(color['directory'],'blender_falling_cubes')
        self.assertEqual(mono['directory'],'blender_falling_cubes')
        self.assertEqual(color['variant_args']['_legacy144'],['--sample-step','3'])
        self.assertNotIn('_legacy144',mono['variants'])


    def test_manifest_variant_override_replaces_duplicate_option(self):
        from tools.c643d.cli import _merge_manifest_variant_args
        merged=_merge_manifest_variant_args(
            ['--sample-step','4','--renderer','yunroll'],
            ['--sample-step','3'],
        )
        self.assertEqual(merged.count('--sample-step'),1)
        self.assertEqual(merged[merged.index('--sample-step')+1],'3')
        self.assertEqual(merged[merged.index('--renderer')+1],'yunroll')

    def test_development_version_is_064(self):
        from tools.c643d import __version__
        self.assertEqual(__version__,'0.6.4')
        self.assertEqual((ROOT/'VERSION').read_text(encoding='utf-8').strip(),'0.6.4')

    def test_blender_only_selector_uses_blender_manifest(self):
        from argparse import Namespace
        from tools.c643d.cli import _example_specs
        specs=_example_specs(Namespace(blender_only=True,only=None))
        self.assertEqual(len(specs),2)
        self.assertTrue(all('--blend' in spec['args'] for spec in specs))

class TestReferenceReproductionMode(unittest.TestCase):
    def test_legacy_manifest_records_144_line_reproduction_override(self):
        import json
        data=json.loads((ROOT/'tests'/'data'/'golden_prg_checksums.json').read_text(encoding='utf-8'))
        ref=data['reference_sets']['legacy-v0.6.0-v0.6.1']
        self.assertEqual(ref['build_overrides'],['--viewport-height','144'])

    def test_reproduce_reference_flag_parses(self):
        from tools.c643d.cli import make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        parser=make_parser(load_toolchain_settings(Path('/definitely/missing/c643d.ini')))
        args=parser.parse_args(['test-examples','--variants','normal','--reproduce-reference'])
        self.assertTrue(args.reproduce_reference)

class TestCartridgeStageOne(unittest.TestCase):
    def test_toolchain_defaults_include_optional_cartconv(self):
        from tools.c643d.toolchain import load_toolchain_settings
        with tempfile.TemporaryDirectory() as td:
            cfg=load_toolchain_settings(Path(td)/'missing.ini',system='Linux')
        self.assertEqual(cfg.cartconv,'cartconv')

    def test_cartconv_platform_override_is_loaded(self):
        from tools.c643d.toolchain import load_toolchain_settings
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'c643d.ini'
            path.write_text(
                '[toolchain]\ncartconv = generic-cartconv\n\n'
                '[windows]\ncartconv = C:\\Tools\\VICE\\bin\\cartconv.exe\n',
                encoding='utf-8',
            )
            cfg=load_toolchain_settings(path,system='Windows',require=True)
        self.assertEqual(cfg.cartconv,r'C:\Tools\VICE\bin\cartconv.exe')

    def test_cartconv_distribution_directory_resolves(self):
        from tools.c643d.toolchain import resolve_executable
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'vice-3.10'
            exe=root/'bin'/'cartconv'
            exe.parent.mkdir(parents=True)
            exe.write_text('#!/bin/sh\nexit 0\n',encoding='utf-8')
            exe.chmod(0o755)
            self.assertEqual(Path(resolve_executable(str(root),'cartconv')),exe.resolve())

    def test_easyflash_smoke_raw_layout(self):
        from tools.c643d.cartridge import (
            EASYFLASH_CHIP_SIZE,EASYFLASH_RAW_SIZE,build_smoke_raw,easyflash_offset,
        )
        romh=bytes([0x5a])*EASYFLASH_CHIP_SIZE
        raw,manifest=build_smoke_raw(romh)
        self.assertEqual(len(raw),EASYFLASH_RAW_SIZE)
        self.assertEqual(raw[easyflash_offset(0,'romh'):easyflash_offset(0,'romh')+EASYFLASH_CHIP_SIZE],romh)
        self.assertTrue(raw[easyflash_offset(1,'roml'):].startswith(b'C643D EASYFLASH BANK 1 OK\x00'))
        self.assertTrue(raw[easyflash_offset(2,'roml'):].startswith(b'C643D EASYFLASH BANK 2 OK\x00'))
        self.assertTrue(raw[easyflash_offset(3,'roml'):].startswith(b'C643D EASYFLASH BANK 3 OK\x00'))
        self.assertEqual(raw[easyflash_offset(1,'roml',0x100)],1)
        self.assertEqual(raw[easyflash_offset(2,'roml',0x100)],2)
        self.assertEqual(raw[easyflash_offset(3,'roml',0x100)],3)
        self.assertEqual(manifest['bank_count'],64)

    def test_easyflash_info_validation(self):
        from tools.c643d.cartridge import validate_easyflash_info
        validate_easyflash_info(
            'Hardware ID: 32 (EasyFlash)\n'
            'Mode: exrom: 1 game: 0 (ultimax)\n'
            'total banks: 4 size: $008000\n'
        )
        with self.assertRaises(RuntimeError):
            validate_easyflash_info('Hardware ID: 0 (generic)\nMode: exrom: 0 game: 0\n')

    def test_cartridge_smoke_cli_and_cartconv_override_parse(self):
        from tools.c643d.cli import make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        parser=make_parser(load_toolchain_settings(Path('/definitely/missing/c643d.ini')))
        args=parser.parse_args(['cartridge-smoke','--cartconv','/opt/vice/bin/cartconv','--run'])
        self.assertEqual(args.command,'cartridge-smoke')
        self.assertEqual(args.cartconv,'/opt/vice/bin/cartconv')
        self.assertTrue(args.run)

    def test_yunroll_cart_is_separate_source_not_normal_renderer_choice(self):
        from tools.c643d.cli import CARTRIDGE_RENDERERS,RENDERERS
        self.assertEqual(CARTRIDGE_RENDERERS['yunroll-cart'],'renderer-yunroll-cart.asm')
        self.assertNotIn('yunroll-cart',RENDERERS)
        self.assertTrue((ROOT/'c64'/'renderer-yunroll-cart.asm').is_file())

class TestCartridgeDemoControlPatch(unittest.TestCase):
    def test_demo_packer_patches_only_cartridge_copy_irq(self):
        from tools.c643d.cli import CARTRIDGE_DEMO_ENTRIES,ROOT
        from tools.c643d.cartridge import easyflash_offset,pack_demo_prgs
        originals={path:path.read_bytes() for _,path in CARTRIDGE_DEMO_ENTRIES}
        image,plans,_=pack_demo_prgs(CARTRIDGE_DEMO_ENTRIES,source_root=ROOT)
        self.assertEqual(len(plans),len(CARTRIDGE_DEMO_ENTRIES))
        for (_,path),plan in zip(CARTRIDGE_DEMO_ENTRIES,plans):
            self.assertEqual(path.read_bytes(),originals[path])
            stored=image[easyflash_offset(plan.bank,'roml'):easyflash_offset(plan.bank,'roml')+plan.length]
            self.assertIn(plan.irq_address,(0x0917,0x091a))
            self.assertNotEqual(stored,originals[path][2:])

class TestCartridgeFailureMessages(unittest.TestCase):
    def test_missing_cartconv_is_targeted_and_prg_safe(self):
        import contextlib, io
        from tools.c643d.cli import require_cartconv
        err=io.StringIO()
        with contextlib.redirect_stderr(err):
            resolved=require_cartconv('/definitely/missing/cartconv',verbose=False)
        self.assertIsNone(resolved)
        text=err.getvalue()
        self.assertIn('EasyFlash cartridge output requires cartconv',text)
        self.assertIn('--cartconv PATH',text)
        self.assertIn('Normal .prg builds do not require cartconv.',text)

class TestCartridgeDemoStageTwo(unittest.TestCase):
    def test_cartridge_demo_cli_parses(self):
        from tools.c643d.cli import make_parser
        from tools.c643d.toolchain import load_toolchain_settings
        parser=make_parser(load_toolchain_settings(Path('/definitely/missing/c643d.ini')))
        args=parser.parse_args(['cart-demos','--run','--cartconv','/opt/vice/cartconv','--menu-style','demoscene'])
        self.assertEqual(args.command,'cart-demos')
        self.assertTrue(args.run)
        self.assertEqual(args.cartconv,'/opt/vice/cartconv')
        self.assertEqual(args.menu_style,'demoscene')
        compat=parser.parse_args(['cartridge-demo','--menu-style','decorative'])
        self.assertEqual(compat.command,'cartridge-demo')
        self.assertEqual(compat.menu_style,'decorative')
        plain=parser.parse_args(['cart-demos'])
        self.assertEqual(plain.menu_style,'default')

    def test_demo_pack_fits_canonical_examples(self):
        from tools.c643d.cli import CARTRIDGE_DEMO_ENTRIES
        from tools.c643d.cartridge import (
            DEMO_RUNTIME_LOAD,EASYFLASH_RAW_SIZE,easyflash_offset,pack_demo_prgs,
        )
        from tools.c643d.cli import ROOT
        image,plans,manifest=pack_demo_prgs(CARTRIDGE_DEMO_ENTRIES,source_root=ROOT)
        self.assertEqual(len(image),EASYFLASH_RAW_SIZE)
        self.assertEqual(len(plans),10)
        self.assertLessEqual(manifest['highest_bank_used'],63)
        self.assertEqual(manifest['data_banks_used'],57)
        self.assertEqual(plans[0].name,'TORUS')
        self.assertEqual(manifest['entries'][0]['source'],'examples/torus/torus.prg')
        self.assertFalse(Path(manifest['entries'][0]['source']).is_absolute())
        first_payload=bytearray(CARTRIDGE_DEMO_ENTRIES[0][1].read_bytes()[2:])
        # Cartridge copies redirect only the generated raster IRQ target to the
        # low-RAM cart-control shim; canonical PRGs on disk remain untouched.
        patch=next(i for i in range(len(first_payload)-9)
                   if first_payload[i]==0xa9 and first_payload[i+2:i+5]==bytes((0x8d,0xfe,0xff))
                   and first_payload[i+5]==0xa9 and first_payload[i+7:i+10]==bytes((0x8d,0xff,0xff)))
        original_irq=first_payload[patch+1] | (first_payload[patch+6]<<8)
        first_payload[patch+1]=0x00
        first_payload[patch+6]=0x02
        stored=bytearray()
        remaining=len(first_payload)
        bank=plans[0].bank
        while remaining:
            n=min(0x2000,remaining)
            start=easyflash_offset(bank,'roml')
            stored.extend(image[start:start+n])
            remaining-=n
            bank+=1
        self.assertEqual(bytes(stored),bytes(first_payload))
        self.assertEqual(plans[0].irq_address,original_irq)
        self.assertEqual(manifest['entries'][0]['cart_irq'],'$0200')
        for plan in plans:
            self.assertLessEqual(plan.load_address+plan.length,DEMO_RUNTIME_LOAD)

    def test_demo_runtime_and_boot_install_use_both_bank0_chips(self):
        from tools.c643d.cartridge import (
            DEMO_CONTROL_ROM_OFFSET,DEMO_CONTROL_SIZE,DEMO_MENU_FONT_ROM_OFFSET,DEMO_MENU_FONT_SIZE,
            DEMO_RUNTIME_SIZE,EASYFLASH_CHIP_SIZE,build_menu_charset,easyflash_offset,
            install_demo_boot,new_easyflash_image,
        )
        image=new_easyflash_image()
        boot=bytes([0x55])*EASYFLASH_CHIP_SIZE
        runtime=bytes([0xaa])*DEMO_RUNTIME_SIZE
        control=bytes([0x33])*DEMO_CONTROL_SIZE
        menu_font=build_menu_charset()
        self.assertEqual(len(menu_font),DEMO_MENU_FONT_SIZE)
        styles=[bytes([0x10+i])*DEMO_RUNTIME_SIZE for i in range(3)]
        install_demo_boot(image,boot,runtime,control,menu_font,styles)
        romh=easyflash_offset(0,'romh')
        roml=easyflash_offset(0,'roml')
        self.assertEqual(bytes(image[romh:romh+EASYFLASH_CHIP_SIZE]),boot)
        self.assertEqual(bytes(image[roml:roml+DEMO_RUNTIME_SIZE]),runtime)
        self.assertEqual(bytes(image[roml+DEMO_CONTROL_ROM_OFFSET:roml+DEMO_CONTROL_ROM_OFFSET+DEMO_CONTROL_SIZE]),control)
        self.assertEqual(image[roml+DEMO_CONTROL_ROM_OFFSET+DEMO_CONTROL_SIZE],0xff)
        self.assertEqual(bytes(image[roml+DEMO_MENU_FONT_ROM_OFFSET:roml+DEMO_MENU_FONT_ROM_OFFSET+DEMO_MENU_FONT_SIZE]),menu_font)
        style_romh=easyflash_offset(1,'romh')
        for i,payload in enumerate(styles):
            start=style_romh+i*DEMO_RUNTIME_SIZE
            self.assertEqual(bytes(image[start:start+DEMO_RUNTIME_SIZE]),payload)
        self.assertNotEqual(menu_font[1*8:2*8],menu_font[0x41*8:0x42*8])

    def test_demo_menu_footer_and_style_source_are_cartridge_only(self):
        runtime=(ROOT/'c64'/'cart'/'easyflash-demo-runtime.asm').read_text(encoding='utf-8')
        self.assertIn('by FlyingFathead, 2026',runtime)
        self.assertIn('github: flyingfathead/c64-3d-toolkit',runtime)
        self.assertIn('MENU_STYLE_DEMOSCENE',runtime)
        self.assertIn('CONTROL_CYCLE     = $0203',runtime)
        self.assertIn('F1 STYLE',runtime)
        # $02F8-$02FF is persistent state. Reinstalling the executable shim
        # must stop before that tail or F1 style cycling collapses back to 0.
        self.assertIn('cpx #$f8',runtime.lower())
        self.assertIn('$02F8-$02FF is persistent control state',runtime)
        control=(ROOT/'c64'/'cart'/'easyflash-demo-control.asm').read_text(encoding='utf-8')
        self.assertIn('default -> decorative -> demoscene -> default',control)
        self.assertIn('STYLE_ROMH      = $a000',control)
        self.assertNotIn('github: flyingfathead/c64-3d-toolkit',(ROOT/'c64'/'renderer-yunroll.asm').read_text(encoding='utf-8'))

    def test_demo_include_contains_generated_metadata(self):
        from tools.c643d.cartridge import DemoEntryPlan,write_demo_include
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'cart-demo-data.inc'
            plans=[DemoEntryPlan(
                name='TEST DEMO',path=Path('demo.prg'),bank=3,banks=2,
                load_address=0x0801,entry_address=0x080d,length=0x2345,
                checksum16=0xabcd,irq_address=0x0917,
            )]
            write_demo_include(out,plans)
            text=out.read_text(encoding='utf-8')
        self.assertIn('DEMO_ENTRY_COUNT = 1',text)
        self.assertIn('demo_bank:',text)
        self.assertIn('$03',text)
        self.assertIn('demo_irq_lo:',text)
        self.assertIn('$17',text)
        self.assertIn('demo_name_0:',text)
        self.assertIn('TEST DEMO',text)
