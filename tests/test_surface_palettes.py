"""Native colour-ramp output and preservation of existing metallic behaviour."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from c643d import cli
from c643d.mesh import Mesh
from c643d.pipeline import Camera
from c643d.surface_fill import raster, quantize, build_frames, SHADE_PALETTES
from c643d.optimize import picture_bytes


class SurfacePaletteTests(unittest.TestCase):
    def args(self, *extra):
        return cli.make_parser(cli.load_toolchain_settings(None)).parse_args(['build', *extra])

    def test_grey_and_metallic_aliases(self):
        for alias in ('grey', 'gray', 'metallic'):
            self.assertEqual(self.args('--surface-fill', alias).surface_fill, 'metallic')
            self.assertEqual(self.args('--surface-palette', alias).surface_palette, 'grey')

    def test_default_and_explicit_grey_have_identical_pictures(self):
        mesh = Mesh('face', [(-14,-12,0), (0,14,0), (14,-12,0)], [(0,1,2)])
        a = build_frames(mesh, 4, Camera(cy=96))
        b = build_frames(mesh, 4, Camera(cy=96), shade_palette='grey')
        self.assertEqual([picture_bytes(f) for f in a], [picture_bytes(f) for f in b])

    def test_coloured_raster_keeps_silhouette_and_shading_levels(self):
        mesh = Mesh('face', [(-14,-12,0), (0,14,0), (14,-12,0)], [(0,1,2)])
        grey = raster(mesh, Camera(cy=96), 0, 4)
        for name in ('blue', 'red', 'green'):
            pic = raster(mesh, Camera(cy=96), 0, 4, shade_palette=name)
            np.testing.assert_array_equal(pic != 0, grey != 0)
            for old, new in zip(SHADE_PALETTES['grey'], SHADE_PALETTES[name]):
                self.assertTrue(np.all(pic[grey == old] == new))

    def test_native_cell_limit_and_black_boundary_for_every_ramp(self):
        for name, ramp in SHADE_PALETTES.items():
            pic = np.zeros((192,256), dtype=np.uint8)
            pic[8:16,8:16] = np.tile([0, *ramp[1:], *ramp[1:4]], (8,1))
            pic[24:32,24:32] = np.tile(list(ramp[1:])*2, (8,1))
            _, _, native = quantize(pic, shade_palette=name)
            self.assertLessEqual(len(np.unique(native[8:16,8:16])), 2)
            self.assertLessEqual(len(np.unique(native[24:32,24:32])), 2)
            self.assertEqual(native[8,8], 0)
            self.assertTrue(set(np.unique(native)).issubset(set(ramp)))

    def test_old_renderers_and_unrelated_surface_modes_reject_coloured_ramps(self):
        for extra in ([], ['--surface-fill','material'], ['--surface-fill','textured'],
                      ['--surface-fill','metallic','--surface-encoding','dither']):
            args = self.args('--renderer','hors-renderer-v3','--surface-palette','blue',*extra)
            with self.assertRaisesRegex(ValueError,'require'):
                cli.cmd_build(args)
        with self.assertRaisesRegex(ValueError,'requires --renderer hors-renderer-v3'):
            cli.cmd_build(self.args('--surface-palette','red'))


if __name__ == '__main__':
    unittest.main()
