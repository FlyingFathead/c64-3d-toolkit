"""Output colour formats, geometry invariance and recycled-buffer metadata."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from tools.c643d.colors import c64_color_index, C64_PALETTE, configure_asm_colors
from tools.c643d.cli import make_parser, build_mesh, _scene_color_policy
from tools.c643d.toolchain import load_toolchain_settings
from tools.c643d.pipeline import Camera, build_frames, build_scene_frames
from tools.c643d.shapes import cube
from tools.c643d.sceneio import Projection, SceneFrame, SceneAnimation
from tools.c643d.optimize import picture_bytes, optimize_frames

ROOT=Path(__file__).resolve().parents[1]

class OutputColorTests(unittest.TestCase):
    def test_all_native_names_and_rgb_hex_roundtrip(self):
        for name,(index,rgb) in C64_PALETTE.items():
            for value in (name,name.upper(),name.replace('_',' '),name.replace('_','-'),index,str(index),f'0x{index:x}',f'${index:02x}',f'0b{index:04b}',f'%{index:04b}', '#'+''.join(f'{v:02x}' for v in rgb),f'rgb({rgb[0]},{rgb[1]},{rgb[2]})'):
                with self.subTest(value=value):
                    self.assertEqual(c64_color_index(value),index)
        self.assertEqual(c64_color_index('#fff'),1)
        self.assertEqual(c64_color_index('rgb(100%,100%,100%)'),1)
        self.assertEqual(c64_color_index('light grey'),15)
        self.assertEqual(c64_color_index('darkgrey'),11)

    def test_invalid_explicit_colors_fail(self):
        for value in ('16','0x10','$ff','%10000','-1','oops','#fgf','#ffff','#ffffff00','rgba(1,2,3,0.5)','transparent','rgb(256,0,0)','rgb(50%,0,0)'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                c64_color_index(value)

    def test_cli_aliases_black_is_not_treated_as_unset(self):
        parser=make_parser(load_toolchain_settings(None))
        for option in ('--color','--foreground-color','--fg-color','--foreground-colour'):
            args=parser.parse_args(['build','--shape','cube',option,'#000','--background-color','0x01','--border-color','light-blue','--no-color'])
            with contextlib.redirect_stdout(io.StringIO()):
                result=build_mesh(args)
                scene_policy=_scene_color_policy(cube(),args)
            self.assertEqual(result[6:9],('black',False,False))
            self.assertEqual(scene_policy,('black',False,False))
            self.assertEqual((args.background_color,args.border_color),('white','light_blue'))

    def test_config_defaults_and_cli_override(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'colors.ini'
            p.write_text('[render_defaults]\nforeground_color = #000\nbackground_color = #fff\nborder_color = $06\n')
            settings=load_toolchain_settings(p)
            parser=make_parser(settings)
            a=parser.parse_args(['build'])
            self.assertEqual((a.color,a.background_color,a.border_color),('black','white','blue'))
            a=parser.parse_args(['build','--color','red','--bg-color','black','--border-colour','%1111'])
            self.assertEqual((a.color,a.background_color,a.border_color),('red','black','light_gray'))

    def test_source_colors_keep_foreground_and_geometry_on_new_background(self):
        mesh=cube();mesh.face_colors=[2,3,5,6,7,14]
        old,_=build_frames(mesh,8,Camera(),enable_source_colors=True)
        new,_=build_frames(mesh,8,Camera(),enable_source_colors=True,background_color=1)
        for a,b in zip(old,new):
            self.assertEqual(a.records,b.records)
            self.assertEqual(a.clear_spans,b.clear_spans)
            self.assertTrue(b.color_spans)
            self.assertEqual([(lo,hi,n,c|1) for lo,hi,n,c in a.color_spans],b.color_spans)
            old_pic=picture_bytes(a,0x10);new_pic=picture_bytes(b,0x11)
            self.assertEqual(old_pic[:7680],new_pic[:7680])
            self.assertTrue(all(v&15==1 for v in new_pic[7680:]))
        optimized,_=optimize_frames(new,0x11)
        self.assertEqual([picture_bytes(f,0x11) for f in new],[picture_bytes(f,0x11) for f in optimized])

    def test_monochrome_inversion_needs_no_color_spans_or_extra_geometry(self):
        mesh=cube()
        white,_=build_frames(mesh,4,Camera())
        black,_=build_frames(mesh,4,Camera(),fallback_color=0,background_color=1)
        self.assertEqual(white,black)
        self.assertTrue(all(not f.color_spans for f in black))
        self.assertTrue(all(v==1 for v in picture_bytes(black[0],0x01)[7680:]))

    def test_authored_scene_background_propagation(self):
        mesh=cube();mesh.face_colors=[2,3,5,6,7,14]
        vertices=tuple((x,y,z+110) for x,y,z in mesh.vertices)
        scene=SceneAnimation('COLORS',mesh,(SceneFrame(1,vertices,Projection(180,180,128,96)),),25,1,Path('example.blend'))
        frames,_=build_scene_frames(scene,height=192,enable_source_colors=True,background_color=14)
        self.assertTrue(frames[0].color_spans)
        self.assertTrue(all(c&15==14 for _,_,_,c in frames[0].color_spans))

    def test_all_runtime_templates_preserve_defaults_and_accept_output_colors(self):
        paths=list((ROOT/'c64').glob('renderer-*.asm'))+list((ROOT/'c64/variants').glob('renderer-*.asm'))+list((ROOT/'c64/debug').glob('renderer-*.asm'))
        for p in paths:
            source=p.read_text()
            if 'SCREEN_COLOR = $10' not in source:continue
            with self.subTest(renderer=p.name):
                self.assertEqual(configure_asm_colors(source),source)
                selected=configure_asm_colors(source,0,1,6)
                self.assertIn('SCREEN_COLOR = $01',selected)
                self.assertIn('lda #6\n        sta $d020\n        lda #1\n        sta $d021',selected)

    def test_intro_handoff_restores_selected_border(self):
        source=(ROOT/'c64/renderer-yunroll-cart-v10-scene.asm').read_text()
        source=source.replace('        ; Per-build foreground','        jsr intro_start\n        ; Per-build foreground',1)
        selected=configure_asm_colors(source,0,1,6)
        self.assertIn('jsr intro_start\n        lda #6\n        sta $d020\n        lda #1\n        sta $d021',selected)

class ColorComboTests(unittest.TestCase):
    def test_showcase_uses_four_classics_and_preserves_every_geometry_sample(self):
        from tools.c643d.colorcombos import combo_sources, COMBOS
        from tools.c643d.cartframes import load_menu_reference
        refs={x.name:x for x in load_menu_reference(ROOT)}
        demos=combo_sources(ROOT)
        self.assertEqual([c[0] for c in COMBOS],['TORUS','TORUS DENSE','SPHERE','CUBE'])
        self.assertEqual(len({d.screen for d in demos}),4)
        for d,c in zip(demos,COMBOS):
            self.assertFalse(d.colors)
            self.assertEqual(d.border,d.screen&15)
            self.assertTrue(d.interactive_colors)
            self.assertEqual([f.records for f in d.frames],[f.records for f in refs[c[0]].frames])
            self.assertTrue(all(not f.color_spans for f in d.frames))
        self.assertEqual(demos[0].screen,0x01)

if __name__=='__main__':unittest.main()
