"""Behaviour checks for experimental solid surfaces; runtime checked in VICE."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c643d import cli
from c643d.mesh import Mesh
from c643d.pipeline import Camera
from c643d.surface_fill import raster, quantize, frame_from_pixels, cmd_build, build_frames
from c643d.optimize import picture_bytes

class SurfaceFillTests(unittest.TestCase):
    def parser(self, *args):
        return cli.make_parser(cli.load_toolchain_settings(None)).parse_args(['build', *args])

    def test_opt_in_and_spelling_alias(self):
        self.assertIsNone(self.parser().surface_fill)  # source-specific default resolves at build dispatch
        self.assertEqual(self.parser('--surface-fill').surface_fill, 'material')
        self.assertEqual(self.parser('--surface-fills', 'metallic').surface_fill, 'metallic')
        self.assertEqual(self.parser('--compact-color-dictionary').v3_color_encoding, 'indexed4')
        self.assertEqual(self.parser().v3_color_encoding,'literal')

    def test_long_renderer_name_and_preview_alias_dispatch_identically(self):
        for name in ('hors-renderer-v3', 'hors-render-v3'):
            args=self.parser('--renderer',name,'--surface-fill','metallic')
            with patch('c643d.surface_fill.cmd_build',return_value=0) as build:
                self.assertEqual(cli.cmd_build(args),0)
                build.assert_called_once_with(args)
                self.assertEqual(args.renderer,'hors-renderer-v3')

    def test_depth_wins_over_face_order_and_mtl_colors_survive(self):
        points = [(-12,-12,0),(12,-12,0),(0,12,0),(-12,-12,-5),(12,-12,-5),(0,12,-5)]
        for faces, colors in [([(0,1,2),(3,4,5)],[2,6]), ([(3,4,5),(0,1,2)],[6,2])]:
            mesh = Mesh('overlap', points, faces, face_colors=colors)
            pic = raster(mesh, Camera(cy=96), 0, 1, 'material')
            self.assertEqual(pic[96,128], 6)
            bits, screen, native = quantize(pic, 'native', 'material')
            self.assertEqual(native[96,128], 6)
            self.assertEqual(native[0,0], 0)

    def test_missing_material_uses_foreground_fallback(self):
        mesh=Mesh('triangle',[(-12,-12,0),(12,-12,0),(0,12,0)],[(0,1,2)])
        pic=raster(mesh,Camera(cy=96),0,1,'material',fallback=7)
        self.assertEqual(pic[96,128],7)

    def test_native_cell_limit_black_silhouette_and_packed_bytes(self):
        pic=np.zeros((192,256),dtype=np.uint8)
        pic[8:16,8:16]=np.tile([0,11,12,15,1,11,12,15],(8,1))
        pic[32:40,32:40]=np.tile([11,11,12,12,15,15,1,1],(8,1))
        bit,screen,native=quantize(pic)
        self.assertLessEqual(len(np.unique(native[8:16,8:16])),2)
        self.assertEqual(native[8,8],0)
        self.assertGreater(screen[4,4]&15,0)
        blob=picture_bytes(frame_from_pixels(bit,screen))
        decoded=np.zeros((192,320),dtype=np.uint8)
        for y in range(192):
            for x in range(320):
                cell=(y//8)*40+x//8
                mask=blob[cell*8+(y&7)] & (128>>(x&7))
                colors=blob[7680+cell]
                decoded[y,x]=colors>>4 if mask else colors&15
        np.testing.assert_array_equal(decoded,native)

    def test_dither_uses_only_black_white_and_keeps_shade_order(self):
        pic=np.zeros((192,256),dtype=np.uint8)
        for i,c in enumerate([11,12,15,1]):pic[8:24,i*16:(i+1)*16]=c
        bit,screen,native=quantize(pic,'dither')
        self.assertEqual(set(np.unique(native)),{0,1})
        self.assertTrue(np.all(screen==0x10))
        fills=[int(bit[8:24,i*16:(i+1)*16].sum()) for i in range(4)]
        self.assertEqual(fills,sorted(set(fills)))

    def test_single_material_fast_path_has_no_color_updates(self):
        mesh=Mesh('triangle',[(-12,-12,0),(12,-12,0),(0,12,0)],[(0,1,2)],face_colors=[11])
        frame=build_frames(mesh,1,Camera(cy=96),preset='material',uniform_foreground=11)[0]
        self.assertEqual(frame.color_spans,[])
        self.assertEqual(picture_bytes(frame,0xb0)[7680:],bytes([0xb0])*960)
        self.assertGreater(frame.unique_pixels,0)

    def test_rejects_interactive_uniform_color_controls(self):
        args=self.parser('--renderer','hors-render-v2','--surface-fill','metallic','--interactive-cart')
        with self.assertRaisesRegex(ValueError,'interactive'):
            cmd_build(args)

    def test_new_fill_flags_cannot_change_old_renderer_behavior(self):
        args=self.parser('--renderer','hors-render-v2','--surface-fill','metallic')
        with self.assertRaisesRegex(ValueError,'new HORS-V3'):
            cli.cmd_build(args)
        args=self.parser('--renderer','hors-render-v2','--compact-color-dictionary')
        with self.assertRaisesRegex(ValueError,'requires --renderer hors-renderer-v3'):
            cli.cmd_build(args)

    def test_default_dispatch_does_not_call_surface_builder(self):
        args=self.parser('--renderer','hors-render-v2')
        with patch('c643d.hors_v2_stable.cmd_build_object',return_value=0) as wire:
            self.assertEqual(cli.cmd_build(args),0)
            wire.assert_called_once()

if __name__=='__main__':unittest.main()
