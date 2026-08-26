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
